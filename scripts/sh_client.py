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


def _load_creds() -> tuple[str, str]:
    cid = os.environ.get("SH_CLIENT_ID")
    sec = os.environ.get("SH_CLIENT_SECRET")
    if cid and sec:
        return cid, sec
    path = Path(os.environ.get("SH_CREDS_FILE", DEFAULT_CREDS_FILE))
    if path.is_file():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k == "SH_CLIENT_ID":
                cid = v.strip().strip('"').strip("'")
            elif k == "SH_CLIENT_SECRET":
                sec = v.strip().strip('"').strip("'")
    if not (cid and sec):
        raise RuntimeError(
            f"Sentinel Hub credentials not found. Set SH_CLIENT_ID/SH_CLIENT_SECRET "
            f"or readable {DEFAULT_CREDS_FILE}"
        )
    return cid, sec


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


def get_token(force: bool = False) -> str:
    if not force:
        cached = _read_token_cache()
        if cached:
            return cached
    cid, sec = _load_creds()
    r = requests.post(
        CDSE_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": sec,
        },
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    _write_token_cache(j["access_token"], j.get("expires_in", 1800))
    return j["access_token"]


def process(payload: dict, accept: str = "image/png") -> bytes:
    """Call the Process API. Returns raw response body (bytes for PNG/TIFF, JSON for stats)."""
    token = get_token()
    r = requests.post(
        CDSE_PROCESS_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
        },
        json=payload,
        timeout=120,
    )
    if r.status_code == 401:
        # refresh token once
        token = get_token(force=True)
        r = requests.post(
            CDSE_PROCESS_URL,
            headers={"Authorization": f"Bearer {token}", "Accept": accept},
            json=payload,
            timeout=120,
        )
    if not r.ok:
        raise RuntimeError(f"Process API failed: {r.status_code} {r.text[:400]}")
    return r.content


def statistics(payload: dict) -> dict:
    """Call the Statistical API. Returns parsed JSON."""
    token = get_token()
    r = requests.post(
        CDSE_STAT_URL,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        json=payload,
        timeout=120,
    )
    if r.status_code == 401:
        token = get_token(force=True)
        r = requests.post(
            CDSE_STAT_URL,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            json=payload,
            timeout=120,
        )
    if not r.ok:
        raise RuntimeError(f"Statistical API failed: {r.status_code} {r.text[:400]}")
    return r.json()


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
