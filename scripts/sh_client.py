"""
Copernicus Data Space Ecosystem (CDSE) Sentinel Hub client.

Reads OAuth credentials from $SH_CREDS_FILE (default: /etc/morimieru/sentinel-hub.env)
or from environment variables SH_CLIENT_ID / SH_CLIENT_SECRET.

Caches the access token to ~/.cache/morimieru/sh_token.json (expires 30 min from issue).

Endpoints:
- Token:      https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
- Process:    https://sh.dataspace.copernicus.eu/api/v1/process
- Statistical: https://sh.dataspace.copernicus.eu/api/v1/statistics
"""
import json
import os
import time
from pathlib import Path
from typing import Optional

import requests

CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
CDSE_STAT_URL = "https://sh.dataspace.copernicus.eu/api/v1/statistics"

DEFAULT_CREDS_FILE = "/etc/morimieru/sentinel-hub.env"
TOKEN_CACHE_PATH = Path.home() / ".cache" / "morimieru" / "sh_token.json"

# Round-robin index for multi-account rotation
_current_account_idx = 0
_token_cache_by_account = {}


def _load_all_creds() -> list[tuple[str, str]]:
    """Returns list of (client_id, client_secret) pairs from env + env file.
    Supports SH_CLIENT_ID / SH_CLIENT_ID_2 / SH_CLIENT_ID_3 ... patterns."""
    sources = {}
    # From env vars
    for k, v in os.environ.items():
        if k.startswith("SH_CLIENT_ID"):
            suffix = k[len("SH_CLIENT_ID"):]
            sec_key = f"SH_CLIENT_SECRET{suffix}"
            sec = os.environ.get(sec_key)
            if sec:
                sources[suffix or "_1"] = (v, sec)
    # From file
    path = Path(os.environ.get("SH_CREDS_FILE", DEFAULT_CREDS_FILE))
    if path.is_file():
        file_data = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            file_data[k] = v.strip().strip('"').strip("'")
        for k, v in file_data.items():
            if k.startswith("SH_CLIENT_ID"):
                suffix = k[len("SH_CLIENT_ID"):]
                sec = file_data.get(f"SH_CLIENT_SECRET{suffix}")
                if sec and (suffix or "_1") not in sources:
                    sources[suffix or "_1"] = (v, sec)
    if not sources:
        raise RuntimeError(
            f"Sentinel Hub credentials not found. Set SH_CLIENT_ID/SH_CLIENT_SECRET "
            f"or readable {DEFAULT_CREDS_FILE}"
        )
    return list(sources.values())


def _load_creds() -> tuple[str, str]:
    """Returns first account (back-compat)."""
    return _load_all_creds()[0]


def _read_token_cache() -> Optional[str]:
    try:
        if TOKEN_CACHE_PATH.is_file():
            data = json.loads(TOKEN_CACHE_PATH.read_text())
            if data.get("expires_at", 0) > time.time() + 60:  # 60s buffer
                return data["access_token"]
    except Exception:
        return None
    return None


def _write_token_cache(token: str, expires_in: int):
    TOKEN_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE_PATH.write_text(json.dumps({
        "access_token": token,
        "expires_at": time.time() + expires_in,
    }))
    TOKEN_CACHE_PATH.chmod(0o600)


def get_token(force: bool = False, account_idx: int = None) -> str:
    """Get an access token, rotating across accounts. force=True forces refresh."""
    global _current_account_idx
    accounts = _load_all_creds()
    if account_idx is None:
        account_idx = _current_account_idx % len(accounts)
    cid, sec = accounts[account_idx]
    if not force and account_idx in _token_cache_by_account:
        cached = _token_cache_by_account[account_idx]
        if cached["expires_at"] > time.time() + 60:
            return cached["access_token"]
    # Try fallback cache file for single-account legacy
    if not force and account_idx == 0:
        cached = _read_token_cache()
        if cached:
            _token_cache_by_account[0] = {"access_token": cached, "expires_at": time.time() + 1500}
            return cached
    r = requests.post(
        CDSE_TOKEN_URL,
        data={"grant_type": "client_credentials", "client_id": cid, "client_secret": sec},
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    _token_cache_by_account[account_idx] = {
        "access_token": j["access_token"],
        "expires_at": time.time() + j.get("expires_in", 1800),
    }
    if account_idx == 0:
        _write_token_cache(j["access_token"], j.get("expires_in", 1800))
    return j["access_token"]


def rotate_account():
    """Move to next account in round-robin."""
    global _current_account_idx
    accounts = _load_all_creds()
    _current_account_idx = (_current_account_idx + 1) % len(accounts)
    return _current_account_idx


def _call_with_rotation(url: str, payload: dict, accept: str, return_bytes: bool = False):
    """Generic API call with multi-account rotation on rate limits / 401."""
    accounts = _load_all_creds()
    last_err = None
    for attempt in range(len(accounts) * 2 + 2):
        try:
            token = get_token()
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}", "Accept": accept},
                json=payload,
                timeout=120,
            )
            if r.status_code == 401:
                token = get_token(force=True)
                r = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {token}", "Accept": accept},
                    json=payload,
                    timeout=120,
                )
            if r.status_code == 429:
                # Rate limited — rotate to next account and retry
                rotate_account()
                time.sleep(1.5)
                last_err = f"429 rate-limited, rotated to account {_current_account_idx}"
                continue
            if not r.ok:
                raise RuntimeError(f"API failed: {r.status_code} {r.text[:400]}")
            return r.content if return_bytes else r.json()
        except requests.exceptions.RequestException as e:
            last_err = str(e)
            time.sleep(1)
            continue
    raise RuntimeError(f"All retries failed: {last_err}")


def process(payload: dict, accept: str = "image/png") -> bytes:
    return _call_with_rotation(CDSE_PROCESS_URL, payload, accept, return_bytes=True)


def statistics(payload: dict) -> dict:
    return _call_with_rotation(CDSE_STAT_URL, payload, "application/json", return_bytes=False)


# ----- Evalscripts -----

# Returns NDVI as 4-band RGBA PNG with mori-mieru brand palette + cloud masking
EVALSCRIPT_NDVI_COLORED = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "SCL", "dataMask"] }],
    output: { bands: 4, sampleType: "UINT8" }
  };
}
function evaluatePixel(s) {
  // SCL classes to mask: 3=cloud shadow, 8=mid prob cloud, 9=high prob cloud, 10=thin cirrus, 11=snow
  const cloud = (s.SCL === 3 || s.SCL === 8 || s.SCL === 9 || s.SCL === 10 || s.SCL === 11);
  if (!s.dataMask || cloud) return [0, 0, 0, 0];

  const ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + 1e-7);

  // Brand palette: earth → sage → green → deep-forest
  if (ndvi < 0.15)       return [230, 200, 160, 220];
  else if (ndvi < 0.40)  return [167, 196, 152, 230];
  else if (ndvi < 0.65)  return [ 90, 138,  58, 240];
  else                   return [ 45,  90,  61, 250];
}
"""

# Returns raw NDVI as 32-bit float TIFF (for downstream CO2 model)
EVALSCRIPT_NDVI_RAW = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "SCL", "dataMask"] }],
    output: { bands: 2, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(s) {
  const cloud = (s.SCL === 3 || s.SCL === 8 || s.SCL === 9 || s.SCL === 10 || s.SCL === 11);
  const valid = (s.dataMask && !cloud) ? 1.0 : 0.0;
  const ndvi = valid > 0 ? (s.B08 - s.B04) / (s.B08 + s.B04 + 1e-7) : 0.0;
  return [ndvi, valid];
}
"""

# Statistical API evalscript: NDVI mean only on valid (non-cloud) forest-like pixels
EVALSCRIPT_NDVI_STATS = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "SCL", "dataMask"] }],
    output: [
      { id: "ndvi", bands: 1, sampleType: "FLOAT32" },
      { id: "dataMask", bands: 1 }
    ]
  };
}
function evaluatePixel(s) {
  const cloud = (s.SCL === 3 || s.SCL === 8 || s.SCL === 9 || s.SCL === 10 || s.SCL === 11);
  const valid = (s.dataMask && !cloud) ? 1 : 0;
  const ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + 1e-7);
  return { ndvi: [ndvi], dataMask: [valid] };
}
"""


def build_process_payload_png(
    bbox_wgs84: tuple,
    date_from: str,
    date_to: str,
    width: int = 1024,
    height: int = 1024,
    evalscript: str = EVALSCRIPT_NDVI_COLORED,
    mosaicking_order: str = "leastCC",
):
    """Helper that builds a Process API payload returning colored NDVI as PNG."""
    return {
        "input": {
            "bounds": {
                "bbox": list(bbox_wgs84),
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": f"{date_from}T00:00:00Z",
                        "to": f"{date_to}T23:59:59Z",
                    },
                    "mosaickingOrder": mosaicking_order,
                    "maxCloudCoverage": 30,
                },
            }],
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [{
                "identifier": "default",
                "format": {"type": "image/png"},
            }],
        },
        "evalscript": evalscript,
    }


def build_statistics_payload(
    bbox_wgs84: tuple,
    date_from: str,
    date_to: str,
    aggregation_interval_days: int = 5,
    width: int = 200,   # ~80m/pixel for the typical Himi AOI - keeps PU usage low
    height: int = 200,
    evalscript: str = EVALSCRIPT_NDVI_STATS,
):
    """Helper for Statistical API: time series of NDVI over an AOI."""
    return {
        "input": {
            "bounds": {
                "bbox": list(bbox_wgs84),
                "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {"maxCloudCoverage": 30},
            }],
        },
        "aggregation": {
            "timeRange": {
                "from": f"{date_from}T00:00:00Z",
                "to": f"{date_to}T23:59:59Z",
            },
            "aggregationInterval": {"of": f"P{aggregation_interval_days}D"},
            "evalscript": evalscript,
            "width": width,
            "height": height,
        },
        "calculations": {
            "ndvi": {
                "histograms": {
                    "default": {"nBins": 10, "lowEdge": -0.5, "highEdge": 1.0},
                },
                "statistics": {
                    "default": {"percentiles": {"k": [5, 50, 95]}},
                },
            },
        },
    }


if __name__ == "__main__":
    # Quick smoke test
    tok = get_token()
    print(f"Token OK ({len(tok)} chars)")
