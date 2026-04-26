# Maryland soybean stress — analysis code & figure reproduction

<!--
  Phase 4 — Round 1 DRAFT (README.md)
  Review this file before asking the assistant to commit it.
-->

This repository contains the **Python analysis pipeline and figure generators** for a study of **drought-related stress in Maryland soybean**, combining USDA yield and irrigation records, NOAA/NCEI climate and Palmer drought indices, county-level precipitation, soil composition (CDL band-5 soybean mask), and **Sentinel-2 / Landsat-based 10-day NDVI and NDWI** composites derived in Google Earth Engine.

**Publication context (JAG resubmission).** The manuscript was **desk-rejected**; the resubmission requires a working **Code Availability** statement with a **Zenodo DOI** before the manuscript returns to the editor. Treat this repo as **deposit-ready** when Phase 4 closes: (1) finalize and tag the GitHub release, (2) obtain the Zenodo DOI, (3) paste that DOI into the manuscript’s Code Availability section and into `README.md` / `CITATION.cff` where placeholders appear below.

## Citation (placeholders — update after acceptance & Zenodo)

- **Journal article (International Journal of Applied Earth Observation and Geoinformation — placeholder):**  
  Sriram, A., Borzi, I., & Kumar, H. (*year*). *Title as accepted.* *International Journal of Applied Earth Observation and Geoinformation*. `https://doi.org/10.xxxx/xxxx` *(replace with the real DOI when assigned).*

- **This code repository (Zenodo — placeholder):**  
  Sriram, A., Borzi, I., & Kumar, H. (*year*). *Same title as manuscript.* Zenodo. `https://doi.org/10.5281/zenodo.xxxxxxx` *(replace with the Zenodo DOI after you publish the GitHub release archive).*

## Quickstart (reproduce manuscript Figures 1–10)

**Prerequisites:** Python 3.10+ recommended, `git`, and enough disk space for inputs (NASS / NCEI / GEE exports — see **Data sources**). The `data/` tree is **not** included in git; you must populate it locally.

```bash
git clone <YOUR_GITHUB_REPO_URL> maryland-soybean-stress
cd maryland-soybean-stress
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # pins supplied in Round 2 of Phase 4

# After populating `data/` per `data/README.md`, regenerate figures:
python -m analysis.figures.regenerate_manuscript_figures
```

**Outputs:** Generators write descriptive PNG paths under `outputs/` (ignored by git except the paper-facing bundle). The orchestrator copies the canonical figures to `outputs/manuscript_figures/Figure01.png` … `Figure10.png`. **Figure 2** is currently a **documented placeholder** (soil heatmap variant selection pending); stderr warns when the stand-in is copied.

**Baseline / drift tracking:** `docs/manuscript_figures_baseline.json` records SHA256 hashes for the originally submitted manuscript figures (see “Manuscript baselines rename” note below) and for the last successful regeneration. Optional review tiles under `outputs/manuscript_figures/_comparison/` are **gitignored** (local visual QA only).

## Repository structure (high level)

```text
maryland-soybean-stress/
├── analysis/                 # All shipped Python (package import path: analysis.*)
│   ├── preprocessing/      # Build / combine canonical CSVs from raw inputs
│   ├── stress_analysis/    # Statistical engines (flash drought, differential stress, …)
│   └── figures/            # Manuscript figure scripts + regenerate_manuscript_figures.py
├── archive/                # Demoted / legacy scripts (not part of the figure path)
├── docs/                   # Baseline JSON, reorg notes, Phase 4+ documentation
├── scripts/                # Residual GEE JS + helpers (will be migrated/removed in Round 3)
├── data/                   # Ignored: local inputs (NASS, Palmer, GEE exports, …)
└── outputs/                # Mostly ignored; tracked exceptions under outputs/manuscript_figures/
```

Google Earth Engine **JavaScript** sources currently live under `scripts/GEE_Scripts/` and `scripts/CreateNDVI/*.js`. In **Round 3**, canonical GEE JS sources will be moved to a top-level `GEE_Scripts/` folder, and duplicates under `scripts/` will be removed.

## Data sources (summary)

| Source | Role in this project |
|--------|----------------------|
| **USDA NASS** | Soybean (and auxiliary corn) yield, acreage, district assignments; Census of Agriculture irrigation tables. |
| **NOAA / NCEI** | County precipitation; Palmer **PDSI**, **PHDI**, **PMDI** monthly series. |
| **USDA Cropland Data Layer (CDL)** | Soybean mask for GEE zonal stats; band-5 soil composition inputs (via preprocessed county tables). |
| **Google Earth Engine (Sentinel-2; Landsat 8/9 pre-2017)** | Monthly / 10-day **NDVI** and **NDWI** composites for Maryland soybean pixels; exported county CSVs merged by `analysis/preprocessing/preprocess_10day_indices.py`. |
| **U.S. Census TIGER/Line** | County boundaries (e.g. `cb_2018_us_county_500k`) for mapping scripts. |
| **Maryland Geological Survey / soil tabular products** | County-level soil attributes as used in the soil composition preprocessing (see preprocessing docstrings). |
| **Klopp & Bly (2024)** | Soil water-holding capacity reference values used in soil composition preprocessing. SDSU Extension. |

Exact filenames and download steps are in **`data/README.md`**.

## Figures ↔ code (manifest)

The authoritative mapping is:

1. **Orchestrator manifest** — list `FIGURE_MANIFEST` in  
   `analysis/figures/regenerate_manuscript_figures.py`  
   (each entry: `generator_module`, descriptive PNG path, `outputs/manuscript_figures/FigureNN.png`).

2. **Baseline / hash record** —  
   `docs/manuscript_figures_baseline.json`  
   (`manuscript_baseline_sha256` vs `current_regeneration_sha256`).

Run `python -m analysis.figures.regenerate_manuscript_figures --help` for flags (`--figure`, `--no-copy`, `--verify-only`, `--update-current-baseline`).

## License

This repository is released under the **MIT License** — see [`LICENSE`](LICENSE).
Round 2 will update `LICENSE` to use the full author list: **“Copyright (c) 2026 Ananth Sriram, Iolanda Borzi, Hemendra Kumar.”**

## Known limitations & outstanding items

- **Figure 2:** Canonical `Variant_*.png` identification still pending; orchestrator uses a labeled **placeholder** copy and prints warnings.
- **Threshold literals:** NDWI stress-band constants (`0.121`–`0.144` family) appear in multiple modules; a reconciliation table is a carry-forward from Phase 3 (no silent scientific changes).
- **Archived legacy paths:** Some figure wrappers load provenance code from `archive/figure_drafts/` (e.g. precipitation climatology, study-area yield facets); see `REORG_PHASE3_REPORT.md`.
- **`scripts/` residual:** plotting helpers and GEE JS may still live under `scripts/` until Round 3 migration; not required for `python -m analysis.*` once migration completes.

## Manuscript baselines

The originally submitted manuscript figure baselines live under `outputs/manuscript_baselines/` and are used for hash comparisons and side-by-side review tiles.

## Contact

Corresponding / lead author: **Ananth Sriram** — update with institutional email and ORCID in `CITATION.cff` when you finalize Round 2.
