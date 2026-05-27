# morimieru — project overview

Last updated: 2026-05-26
Live URL: **https://mori-mieru.jp/en/**
Japanese version: [OVERVIEW.md](OVERVIEW.md)

---

## 1. One-line summary

> **A public-good infrastructure that turns free satellite data and open government data into transparent, verifiable measurements of forest value — water yield, CO₂ absorption, watershed connections, biodiversity — usable by anyone, free.**

Demonstrated in Japan since 2026. Adapting for India (Western Ghats focus) from 2026.

---

## 2. The problem we solve

Forests carry public-good functions that markets don't price:

- Storing water (water yield / groundwater recharge)
- Absorbing and fixing CO₂
- Preventing landslides and floods
- Supporting biodiversity
- Supplying timber

These functions get measured in academic papers or in expensive consulting deliverables, but they are **not available in a form anyone can pull for any municipality, watershed, or forest stand**. Result: TNFD disclosure, carbon-credit purchasing, watershed-based supply-chain decisions, and even citizen forest literacy all run on opaque, custom estimates.

morimieru fills that gap with **free, transparent, country-scale** data.

---

## 3. Strategic positioning

| Axis | Large SI / consultancies | morimieru |
|---|---|---|
| Customer | Large companies & ministries (paid engagements) | Anyone (free web) |
| Precision | Custom-tuned per project · high | Standard data · medium (±10–30%) |
| Coverage | Per engagement | **Country-scale pre-integrated** |
| Transparency | Report deliverable | **Every formula, every input, every source published** |
| Edge | Precision + support | **Verifiability × accessibility** |

> We don't compete on precision; we compete on verifiability × accessibility.
> An open public-good layer for the audiences large SI cannot serve cheaply: small forest cooperatives, local governments, educators, and watershed-aligned companies.

---

## 4. What's running today

### 4.1 Watershed matching v1
Address → catchment → upstream forests, end-to-end automatic.
- HydroBASINS Lvl 10 (CC-BY, commercial OK)
- Geocoding: GSI Japan
- Mean basin area ≈ 100 km²

### 4.2 Water-yield estimation
Aligned with the Forestry Agency of Japan's simplified evaluation method Ver.1.0 (released March 2026).
- Water-balance approach: precipitation − evapotranspiration − direct runoff
- Inputs: NASA POWER climate · AIST seamless geology · forest-cover from open data
- Pilot: Himi City, Toyama — **~1.19 hundred-million tonnes/yr** (equivalent to ~1.6 M households)

### 4.3 CO₂ absorption estimation
IPCC AFOLU **Tier 2**.
- Sentinel-2 NDVI → forest mask (10 m grid)
- Aggregated per forest stand (median ≈ 100 ha)
- Pilot: Shizuoka Prefecture, 1,102 stands / 161,182 ha → **~1.3 M t-CO₂/yr**

### 4.4 Satellite NDVI time series
- Copernicus Sentinel-2 L2A, 5-year history
- 71 observation points on a 10 m grid (Himi pilot)
- Before/after forest-management differencing for cheap MRV

### 4.5 J-Credit project map (Japan, 264 projects)
Every forest-management project registered with Japan's J-Credit programme, geocoded and mapped.
2026 market context: price crossed ¥10,000/t-CO₂ in mid-2025 and is heading toward ¥20,000.

### 4.6 3D hydrology simulator (PoC)
- Engine: **ParFlow 3.15.0** (LLNL / Univ. of Bonn, LGPL, 3D Richards + Shallow Water + CLM coupling)
- Validated on the same server: Little Washita (US, 12 days, CLM-coupled) — 18 s; Himi (Japan, 6 hours, SRTM DEM) — 5 s
- Roadmap: [SIMULATOR_ROADMAP.md](SIMULATOR_ROADMAP.md)

### 4.7 Cryptographically tamper-proof monitoring
- TPM 2.0 attestation + Merkle hash chain + RFC 3161 timestamps
- Every monitoring report carries an independently verifiable signature

---

## 5. Data sources (all free, all public)

| Layer | Source | License |
|---|---|---|
| Sentinel-1 / Sentinel-2 L2A | Copernicus / CDSE | Free, commercial OK |
| Landsat 8/9 | NASA / USGS | Free, commercial OK |
| NASA POWER (climate) | NASA | Free |
| AMeDAS (Japan climate) | Japan Met Agency | Free, no auth |
| AIST Seamless Geological Map V2 | AIST (Japan) | CC-BY |
| HydroBASINS Lvl 10 | WWF HydroSHEDS | CC-BY |
| Japan KSJ A13 / W05 / W07 | GSI Japan | Non-commercial (verify per use) |
| Shizuoka Pref. forest clouds (1,102 stands) | Shizuoka Pref. | Open data |
| Forestry Agency of Japan LiDAR (Tochigi · Hyogo · Kochi) | Forestry Agency / G-Spatial Info Center | "Rashinban" (MIERUNE × JAFTA), commercial OK |
| Forest Ecosystem Survey | Forestry Agency of Japan | Open |
| Natural Environment Survey (vegetation) | Japan Ministry of Environment | Open |
| Natural Park polygons A10 | KSJ | CC-BY |
| J-Credit project list (264) | J-Credit Secretariat | Open |

For India deployment, this layer swaps to: **FSI inventory · IMD climate · ISRO Bhuvan / CartoSat · India-WRIS · CCTS afforestation methodology · CAMPA project registry**. The satellite, watershed, and IPCC layers stay identical.

---

## 6. Tech stack

### Frontend
- Plain HTML / CSS / JavaScript — no build step
- Mapping: Leaflet + Esri World Imagery tiles
- 3D watershed: Mapbox GL JS
- Fonts: Noto Sans JP / M PLUS Rounded 1c / Josefin Sans

### Backend / data processing
- Python: rasterio · pystac-client · numpy · pandas · Pillow · scipy
- Numerical hydrology: ParFlow (C/Fortran/MPI, Hypre PFMG preconditioner)

### Infrastructure
- AWS EC2 (ap-northeast-1)
- Ubuntu 24.04 / nginx / Let's Encrypt
- 19 GB EBS volume (1 host)

### i18n
- `__MM_LANG = window.location.pathname.startsWith('/en/') ? 'en' : 'ja'`
- ~90 translation keys in `app.js`
- 47 prefecture names mapped JP ↔ EN

---

## 7. Repository layout

```
/var/www/morimieru/
├── README.md                          # Public README (JP)
├── OVERVIEW.md                        # Project overview (JP)
├── OVERVIEW_EN.md                     # ← this file
├── ROADMAP.md                         # Feature roadmap
├── SIMULATOR_ROADMAP.md               # 3D simulator plan
├── COMPETITORS.md                     # Competitive matrix
├── NAGANO_MTG_*.md / pdf / docx       # Business-plan documents
│
├── index.html                         # JP top
├── map.html / watershed.html
├── reports.html
├── style.css / app.js / config.js
│
├── en/                                # ← English site
│   ├── index.html                     # EN top
│   ├── map.html · watershed.html
│   ├── reports.html
│   ├── report/                        # Detailed reports (EN, 3)
│   │   ├── himi-water.html
│   │   ├── himi-monitoring.html
│   │   ├── shizuoka-forests.html
│   │   └── report.css
│   └── article/                       # Explainers (EN, 7)
│       ├── index.html                 # EN article hub
│       ├── india-pilot.html           # India case study (CCTS / Western Ghats / FSI)
│       ├── karnataka-coffee-supply-chain.html  # EUDR / CCTS / TNFD playbook
│       ├── india-campa-monitoring.html         # CAMPA transparency layer
│       ├── india-semiconductor-water.html      # Fabs × TNFD / BRSR / CDP Water
│       ├── tnfd-forest-disclosure.html         # TNFD LEAP (translation + India notes)
│       ├── satellite-co2-tier2.html            # Tier 2 walkthrough (translation + India)
│       └── water-yield-guide.html              # Simplified water yield (translation + India)
│
├── report/                            # Detailed reports (JP, 3)
│   ├── himi-water.html
│   ├── himi-monitoring.html
│   └── shizuoka-forests.html
│
├── article/                           # Explainers (JP, 5)
│   ├── index.html
│   ├── water-yield-guide.html
│   ├── tnfd-forest-disclosure.html
│   ├── jcredit-forest-map-2026.html
│   ├── satellite-co2-tier2.html
│   ├── gx-ets-forest-credit-2026.html
│   └── img/                           # ~20 article figures
│
├── data/                              # Datasets
│   ├── candidates.js
│   ├── jcredit_projects.json
│   ├── reports.json
│   ├── sentinel/ · co2/ · watersheds/ · rinpan/ · mountains/
│
├── scripts/                           # ~20 Python data-prep scripts
└── assets/                            # Logos, OG images
```

---

## 8. URL structure

### Japanese
| URL | Page |
|---|---|
| `/` | Top, 4-step flow |
| `/map.html` | National data map (per-municipality scores) |
| `/watershed.html` | 3D watershed map (HydroBASINS Lvl 10) |
| `/reports.html` | Reports hub |
| `/article/` | Article hub |
| `/article/<slug>.html` | Article body (5 articles) |
| `/report/<slug>.html` | Report body (3 reports) |

### English (live)
| URL | Page |
|---|---|
| `/en/` | English landing |
| `/en/map.html` | Data map (EN UI, JP data) |
| `/en/watershed.html` | 3D watershed (EN UI) |
| `/en/reports.html` | Reports list (EN, with EN report cards) |
| `/en/article/` | Article hub (EN) |
| `/en/article/india-pilot.html` | India case study (CCTS / Western Ghats / FSI) |
| `/en/article/karnataka-coffee-supply-chain.html` | EUDR / CCTS / TNFD playbook for coffee |
| `/en/article/india-campa-monitoring.html` | CAMPA satellite transparency layer |
| `/en/article/tnfd-forest-disclosure.html` | TNFD LEAP playbook (translation) |
| `/en/article/satellite-co2-tier2.html` | IPCC Tier 2 walkthrough (translation) |
| `/en/article/water-yield-guide.html` | Simplified water yield (translation) |
| `/en/report/himi-water.html` | Himi water yield report (translation) |
| `/en/report/himi-monitoring.html` | Himi 5-yr monitoring report (translation) |
| `/en/report/shizuoka-forests.html` | Shizuoka 1,102 stands report (translation) |

### Sitemap
`/sitemap.xml` — 26 URLs with `hreflang` cross-references (JP ↔ EN where bilingual).

---

## 9. Articles (Japanese)

| # | Title | Cluster |
|---|---|---|
| 1 | Water yield: complete guide to the simplified evaluation method | Water yield, simplified evaluation |
| 2 | TNFD forest disclosure: practical playbook | TNFD, LEAP |
| 3 | All 264 forest J-Credit projects mapped, 2026 edition | J-Credit price, purchase, selection |
| 4 | Satellite × forest CO₂: IPCC AFOLU Tier 2 walkthrough | IPCC AFOLU, Sentinel-2, NDVI |
| 5 | Japan's GX-ETS and forest J-Credits, 2026 | GX-ETS, carbon pricing |

Each ~4,000–6,000 chars, with Schema.org `Article` markup, FAQ, references.

## 10. Articles (English)

| # | Title | Type |
|---|---|---|
| 1 | India forest valuation pilot: CCTS, Western Ghats & FSI | India-native |
| 2 | Karnataka coffee × EUDR / CCTS / TNFD playbook | India-native |
| 3 | CAMPA monitoring: satellite transparency for compensatory afforestation | India-native |
| 4 | India semiconductor fabs × water exposure (TNFD / BRSR / CDP Water) | India-native |
| 5 | TNFD forest disclosure: LEAP playbook (+ India BRSR / IFSCA notes) | Translation + India |
| 6 | Satellite × forest CO₂: IPCC AFOLU Tier 2 walkthrough (+ Western Ghats Tier 2 numbers) | Translation + India |
| 7 | Forest water yield: simplified evaluation method (+ India IMD / Bhuvan / FSI substitutions) | Translation + India |

Each ~5,000–9,000 English words, with Schema.org `Article` markup, FAQ, and references.

## 10b. Reports (English translations)

| # | Title | Source |
|---|---|---|
| 1 | Himi forest water yield report (~119 M t/yr) | Translation of JP |
| 2 | Himi management-effect monitoring (5-year NDVI + Sentinel-1 SAR) | Translation of JP |
| 3 | Shizuoka 1,102 stands forest public-function | Translation of JP |

---

## 11. Stakeholders

### Core
- **ryuji**: development (front + back + data + writing)
- **M-square Lab Inc.** (CEO Yuriko Kato): publisher; brings satellite × open-data heritage (Nochi-Navi+)

### Partner candidates
- **Moriage Inc.** (CEO Asako Nagano, ex-Forestry Agency of Japan Wood Utilization Division chief): sales network · regulatory knowledge · "One Company, One Mountain" concept
- **Satoshi Imai**: introducer / co-promoter
- **Yoshihiko Haruyama** (YAMAP CEO): potential watershed-map licensing collaboration

### Intended paying users
- ✗ Forest owners, forest cooperatives, local governments (insufficient credit / budget — per Moriage's framing)
- ✓ Consumers, lumber processors, lumber traders, housing makers, financial institutions, water-intensive companies (beverage, semiconductor, food, paper)

### Competitors (Japan, consulting / SI segment)
Morikachi (Sumitomo Forestry × NTT) · woodinfo · Hitachi FSDX · Asia Air Survey · DeepForest Tech · PreFore · Yamaha UMS · mapry · Chiken Environmental Technology (GETFLOWS). See [COMPETITORS.md](COMPETITORS.md).

---

## 12. Active projects

### 12.1 Michibiki (QZSS) demonstration grant — Japan
- Window: 2026-04-01 to 2026-05-28
- Lead applicant: M-square Lab Inc.
- Co-applicant: Moriage Inc.
- Technical contributor: morimieru
- Cooperation: forest cooperatives, lumber primary-industry partners
- 5 candidate business plans on file → [NAGANO_MTG_BUSINESS_PLANS.md](NAGANO_MTG_BUSINESS_PLANS.md)

### 12.2 3D hydrology simulator — Phase 0 complete
- ParFlow 3.15.0 built and validated on the production server
- Little Washita (US, 12 days, CLM-coupled): 18 s
- Himi (Japan, 6 h, SRTM DEM): 5 s
- Full plan: [SIMULATOR_ROADMAP.md](SIMULATOR_ROADMAP.md)

### 12.3 India deployment scoping
- English UI live (5 pages) — `/en/`
- India case study article live — `/en/article/india-pilot.html`
- Target: Western Ghats pilot polygon (Kodagu / Wayanad), 90-day delivery once a pilot partner is in
- Stack swaps documented (FSI, IMD, CartoSat, CCTS) — architecture stays the same

### 12.4 SEO ramp-up
- Google Analytics shows ~17 unique users in the trailing 30 days (early stage)
- 5 JP articles + 1 EN article live
- sitemap.xml 19 URLs with hreflang
- Waiting on Google Search Console reindex (typical lag 1–4 weeks)

---

## 13. Short-term roadmap

| Priority | Item |
|---|---|
| ⭐⭐⭐ | Submit Michibiki grant application (Japan, deadline 2026-05-28) |
| ⭐⭐⭐ | Stand × ledger × management-plan integration (start with Shizuoka) |
| ⭐⭐⭐ | Year-over-year NDVI differencing as management-effect monitoring |
| ⭐⭐ | ParFlow Phase 1 — AMeDAS-driven 1-year Himi simulation |
| ⭐⭐ | Forestry Agency LiDAR ingestion for Tochigi / Hyogo / Kochi (20 m mesh) |
| ⭐⭐ | India pilot site selection (Western Ghats) |
| ⭐⭐ | English translations of the 4 remaining Japanese explainer articles |
| ⭐⭐ | MoE biodiversity layer integration |
| ⭐⭐ | Google Search Console reindex request, traffic measurement |
| ⭐ | YAMAP watershed-map license conversation |
| ⭐ | Open-source release on GitHub |

Full list: [ROADMAP.md](ROADMAP.md)

---

## 14. Messaging axes (for outreach)

- ✅ "Not a precision race — verifiability × accessibility"
- ✅ "Built entirely on free public data"
- ✅ "Connect people who want to steward forests, not 'land-as-liability'" (after Asako Nagano)
- ✅ "Built on top of 20+ years of national inventories, with new layers added"
- ✅ "A country-scale forest infrastructure, always pre-computed, always free"

---

## 15. Deployment

```bash
ssh ubuntu@mori-mieru.jp 'cd /var/www/morimieru && sudo git pull && sudo chown -R www-data:www-data .'
```

Data refresh:

```bash
.venv/bin/python scripts/parse_jcredit.py        # Refresh J-credit list
.venv/bin/python scripts/fetch_sentinel2_himi.py # Refresh Sentinel-2 imagery
```

---

## 16. Contact & related resources

- Public site: https://mori-mieru.jp/ (JP) / https://mori-mieru.jp/en/ (EN)
- Publisher: M-square Lab Inc. — https://m2-labo.jp/
- Partner: Moriage Inc. — https://mori-age.jp/

---

Last updated 2026-05-26. This file mirrors `OVERVIEW.md` (Japanese) and is the canonical English single-file project briefing.
