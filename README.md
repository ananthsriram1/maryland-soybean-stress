# Maryland Soybean Stress

Analysis pipeline and figure generators for a study of drought-related
stress and irrigation effects on soybean yield disparity across Maryland's
five USDA NASS reporting districts (1997–2024).

The analysis combines USDA NASS yield and irrigation records, NOAA/NCEI
climate and Palmer drought indices, USDA Cropland Data Layer soil
composition, and Sentinel-2 / Landsat-derived 10-day NDVI and NDWI
composites computed in Google Earth Engine. The repository regenerates
all 10 manuscript figures from raw inputs through a single orchestrator
script.

## Citation

If you use this code, please cite both the manuscript and the archived
software release:

**Manuscript:** Sriram, A., Kumar, H., & Borzì, I. (in review).
*Quantifying Agricultural Resilience: A Geospatial Analysis of Drought,
Soil, and the Mitigating Effect of Irrigation on Soybean Yield Disparity
in Maryland.* International Journal of Applied Earth Observation and
Geoinformation.

**Software:** Sriram, A., Kumar, H., & Borzì, I. (2026). *Maryland
Soybean Stress* (Version 1.0.1) [Software]. Zenodo.
https://doi.org/10.5281/zenodo.19799371

## Quickstart (reproduce manuscript Figures 1–10)

**Prerequisites:** Python 3.10+, `git`, and enough disk space for inputs
(NASS / NCEI / GEE exports — see **Data sources**). The `data/` tree is
**not** included in git; you must populate it locally per
[`data/README.md`](data/README.md).

```bash
git clone https://github.com/ananthsriram1/maryland-soybean-stress.git
cd maryland-soybean-stress
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# After populating data/ per data/README.md, regenerate figures:
python -m analysis.figures.regenerate_manuscript_figures
```

**Outputs.** Each figure script writes to a descriptive path under
`outputs/`. The orchestrator then copies the canonical version to
`outputs/manuscript_figures/Figure01.png` … `Figure10.png`. Run
`python -m analysis.figures.regenerate_manuscript_figures --help` for
flags (`--figure`, `--no-copy`, `--verify-only`).

**Baseline tracking.** `docs/manuscript_figures_baseline.json` records
SHA256 hashes for the originally submitted manuscript figures (under
`outputs/manuscript_baselines/`) and for the last successful local
regeneration.

## Repository structure

```text
maryland-soybean-stress/
├── analysis/              # Python analysis pipeline (import path: analysis.*)
│   ├── preprocessing/     # Build canonical CSVs from raw inputs
│   ├── stress_analysis/   # Statistical engines (flash drought, differential stress)
│   └── figures/           # Figure generators + regenerate_manuscript_figures.py
├── archive/               # Legacy and exploratory scripts (not in figure pipeline)
├── data/                  # Local inputs (gitignored; see data/README.md)
├── docs/                  # Baseline JSON, manifest, supporting documentation
├── outputs/               # Generated outputs (mostly gitignored)
└── scripts/               # Google Earth Engine JavaScript sources
```

## Data sources

| Source | Role in this project |
|--------|----------------------|
| **USDA NASS** | County-level soybean yield, acreage, and Census of Agriculture irrigation tables. |
| **NOAA NCEI** | County precipitation; Palmer PDSI, PHDI, and PMDI monthly series. |
| **USDA Cropland Data Layer (CDL)** | Soybean field mask for GEE zonal statistics; soil composition inputs. |
| **Sentinel-2 (via Google Earth Engine)** | Surface reflectance for 10-day NDVI and NDWI composites (2017–2024). |
| **Landsat 8/9 (via Google Earth Engine)** | Surface reflectance for 10-day NDVI and NDWI composites (2008–2016). |
| **U.S. Census TIGER/Line** | Maryland county boundaries for mapping scripts. |
| **Maryland Geological Survey** | County-level soil attributes for soil composition preprocessing. |
| **Klopp & Bly (2024)** | Soil water-holding capacity reference values. SDSU Extension. |

Exact filenames, query parameters, and download steps are in
[`data/README.md`](data/README.md).

## Figures ↔ code

The authoritative mapping lives in two places:

1. The `FIGURE_MANIFEST` list in
   `analysis/figures/regenerate_manuscript_figures.py`
2. The hash record in `docs/manuscript_figures_baseline.json`

## License

This repository is released under the MIT License — see
[`LICENSE`](LICENSE).
