# Phase 2 — Proposed Structure

Companion to `REORG_PHASE1_INVENTORY.md`.
Status: **proposal — awaiting sign-off before any moves**.

This phase is read-only: nothing is moved, renamed, deleted, or rewritten until
you approve the moves and TODOs below. Phase 3 will execute exactly the moves
listed in §3, with diffs shown for any refactor longer than ~10 lines, no
silent changes to numerical constants, and bugs flagged rather than fixed.

---

## 0. Resolved figure-to-script mapping (locked, used throughout this proposal)

After cross-checking the byte-level evidence against `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure01..10.png`, you confirmed the canonical mapping below. **Five figures changed source-script versus the assignment given in your Phase 1 reply.** Everything in §1–§5 is built on this resolved mapping.

| Figure | Description | Canonical script |
|---|---|---|
| 01 | MD counties by NASS reporting district (study-area map) | `scripts/Plotting/MapMarylandDistricts.py` |
| 02 | Soil composition heatmap by district | `scripts/Plotting/SoilDistrictHeatmap_Variants.py` |
| 03 | Annual + Jul–Sep precipitation by district (10-year blocks) | `scripts/Plotting/PlotDistrictPrecipitationDecadeOverlay.py` |
| 04 | Historical yield trends by district (4 time periods) | `scripts/Plotting/StudyArea_Option2_Enhanced.py` |
| 05 | Flash-drought proxy events per year (PDSI/PHDI/PMDI panels) | `scripts/Analysis/DetectFlashDroughts.py` |
| 06 | County-year yield by PDSI drought class boxplots | `scripts/Analysis/DroughtEffectFigureOptions.py` (OptionD) |
| 07 | Irrigated soybean area heatmap (district × census year) | `scripts/Plotting/PlotIrrigatedAcresDistrictHeatmap.py` |
| 08 | NDWI distribution by district and census period (R4–R6) | `scripts/Plotting/PlotNDWI_R4R6_ByDistrict_Boxplot.py` |
| 09 | NDVI/NDWI dual-axis "Invisible Stress Window" | `scripts/Plotting/PlotNDVI_NDWI_Scissors_DualAxis.py` |
| 10 | Production + yield variability for >8% sandy loam counties | `scripts/Plotting/Plot_SaLo_Counties.py` |

Demoted to ARCHIVE (no longer claimed as canonical): `ComprehensiveYieldPlots.py`, `AnalyzeIrrigation.py`, `Statewide_Drought_Analysis.py`, `PlotIntervalNDWI.py`, `PlotSoilComposition_Band5.py`, `SoilCompositionBand5_CountyDistrictHeatmap.py`, `PlotDistrictPrecipitationClimatology.py`. Phase 1 inventory rows for these are revised in §3.

The Colab-pipeline reconstruction TODO is **dropped** (see §6.A): the only consumers of `maryland_ndwi_combined_wide.csv` are themselves archived scripts, and no in-paper figure depends on that file.

---

## 1. Proposed target directory tree

```
maryland-soybean-stress/
├── README.md                                    # Phase 4 (rewrite from placeholder)
├── LICENSE                                      # KEEP AS-IS (MIT, copyright line refresh in Phase 4)
├── CITATION.cff                                 # Phase 4 (new)
├── requirements.txt                             # Phase 4 (rewrite, pin from `pip freeze`)
├── .gitignore                                   # Phase 4 (rewrite, see §5.E)
├── REORG_PHASE1_INVENTORY.md                    # internal reorg log; deleted after Phase 5
├── REORG_PHASE2_PROPOSAL.md                     # this file; deleted after Phase 5
│
├── GEE_Scripts/                                 # JavaScript only — pasted into the GEE code editor
│   ├── README.md                                # Phase 4 (new)
│   ├── 01_NDWI_Monthly_Sentinel2.js             # was scripts/GEE_Scripts/NDWI_Extraction
│   ├── 02_NDVI_Monthly_Sentinel2.js             # was scripts/CreateNDVI/Monthly_NDVI_Soybean.js
│   ├── 03_S2_10Day_NDVI_NDWI_2017plus.js        # was scripts/GEE_Scripts/10_Day_NDVI_Reduction
│   └── 04_S2_or_L8_10Day_NDVI_NDWI_PreS2.js     # was scripts/GEE_Scripts/10_Day_NDVI_Reduction_PRE2017
│
├── analysis/                                    # All locally-executed Python (proposed name; alts in §1.A below)
│   ├── __init__.py                              # empty, lets us run `python -m analysis.preprocessing.*`
│   ├── preprocessing/                           # Build canonical CSVs from GEE / NASS / NCEI exports
│   │   ├── __init__.py
│   │   ├── preprocess_10day_indices.py          # was scripts/Preprocess_MD_Soybean_10Day.py
│   │   ├── preprocess_soybean_yield.py          # was scripts/PreprocessYieldData.py
│   │   ├── preprocess_corn_yield.py             # was scripts/PreprocessCornYieldData.py
│   │   ├── preprocess_palmer_indices.py         # was scripts/PreprocessDroughtData.py
│   │   ├── preprocess_soil_composition.py       # consolidates _Band5 + non-Band5 (Band5 logic kept)
│   │   ├── preprocess_irrigation_census.py      # was scripts/BuildCensusIrrigationDataset.py
│   │   ├── combine_palmer_index.py              # consolidates Combine{PDSI,PHDI,PMDI}Data.py (CLI, see §2)
│   │   ├── combine_precipitation.py             # was CombinePrecipitationData.py (kept separate)
│   │   └── combine_nass_metrics.py              # was scripts/NASSPlotting/CombineNassData.py (input path → data/nass/)
│   │
│   ├── stress_analysis/                         # Statistical analyses that produce paper tables
│   │   ├── __init__.py
│   │   ├── differential_stress_analysis.py      # was scripts/Analysis/Differential_Stress_Analysis.py
│   │   ├── longitudinal_10day_indices.py        # was scripts/Analysis/Longitudinal_10Day_Index_Analysis.py
│   │   ├── district_drought_precip_impact.py    # was scripts/Analysis/District_DroughtPrecip_Impact_On_Indices.py
│   │   ├── district_yield_vs_r4r6.py            # was scripts/Analysis/District_Yield_vs_R4R6_Indices.py
│   │   ├── ndwi_r4r6_two_sample_ttests.py       # was scripts/Analysis/NDWI_R4R6_TwoSample_TTests.py
│   │   ├── paired_ttest_county_yield.py         # was scripts/Analysis/PairedTTest_CountyYield_EarlyVsLate.py
│   │   ├── analyze_yield_vs_drought.py          # was scripts/Analysis/AnalyzeYieldVsDrought.py
│   │   ├── analyze_drought_resistance.py        # was scripts/Analysis/AnalyzeDroughtResistance.py
│   │   └── analyze_irrigation_drought_yield.py  # was scripts/Analysis/AnalyzeIrrigationDroughtYield.py
│   │
│   └── figures/                                 # Plotting scripts that produce the 10 paper figures + supporting
│       ├── __init__.py
│       ├── figure01_md_districts_map.py         # was MapMarylandDistricts.py
│       ├── figure02_soil_district_heatmap.py    # was SoilDistrictHeatmap_Variants.py
│       ├── figure03_district_precip_decade_overlay.py  # was PlotDistrictPrecipitationDecadeOverlay.py
│       ├── figure04_yield_4block.py             # was StudyArea_Option2_Enhanced.py
│       ├── figure05_flash_drought_summary.py    # was scripts/Analysis/DetectFlashDroughts.py (also stays under stress_analysis/)
│       ├── figure06_drought_class_yield_boxplots.py  # was DroughtEffectFigureOptions.py (only OptionD path retained)
│       ├── figure07_irrigated_district_heatmap.py  # was PlotIrrigatedAcresDistrictHeatmap.py
│       ├── figure08_ndwi_r4r6_boxplot.py        # was PlotNDWI_R4R6_ByDistrict_Boxplot.py
│       ├── figure09_ndvi_ndwi_scissors_dualaxis.py  # was PlotNDVI_NDWI_Scissors_DualAxis.py
│       ├── figure10_salo_counties_yield.py      # was Plot_SaLo_Counties.py
│       │
│       ├── supporting/                          # Per your earlier sign-off these were KEEP AS-IS as paper supporting figs
│       │   ├── __init__.py
│       │   ├── ndvi_ndwi_scissors.py            # was PlotNDVI_NDWI_Scissors.py
│       │   ├── plot_pdsi_vs_yield.py            # was PlotPDSIVsYield.py
│       │   ├── plot_precip_vs_yield.py          # was PlotPrecipVsYield.py
│       │   ├── compare_national_vs_md_acreage.py  # was CompareNationalVsMaryland_AcreageYield.py
│       │   ├── compare_county_district_vs_national.py  # was CompareCountyAndDistrictVsNational.py
│       │   ├── countydistrict_yield_heatmaps.py # was CountyDistrict_Yield_Heatmaps.py
│       │   ├── studyarea_options_3_4.py         # was StudyArea_Options3_4.py
│       │   ├── plot_irrigated_acres.py          # was PlotIrrigatedAcres.py
│       │   ├── analyze_irrigation_soil.py       # was AnalyzeIrrigationSoilComposition.py
│       │   ├── derive_nass_insights.py          # was DeriveNassInsights.py
│       │   ├── plot_soil_composition.py         # was PlotSoilComposition_Band5.py — see §6.D
│       │   └── plot_district_precipitation_trends.py  # was PlotDistrictPrecipitationTrends.py
│       │
│       └── maps/
│           └── map_soil_composition.py          # was MapSoilCompositionBand5.py
│
├── docs/
│   ├── figure_manifest.md                       # §2 of this proposal materialized
│   ├── data_sources.md                          # Phase 4 (full source table; lives also in README)
│   └── census_nass_irrigation.md                # was data/CENSUS_NASS_IRRIGATION.md
│
├── data/                                        # ENTIRELY .gitignored except for data/README.md
│   └── README.md                                # Phase 4 (explains expected inputs and where to obtain)
│
├── outputs/                                     # ENTIRELY .gitignored except for manuscript figures
│   └── manuscript_figures/                      # was outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/
│       ├── Figure01.png
│       ├── Figure02.png
│       ├── Figure03.png
│       ├── Figure04.png
│       ├── Figure05.png
│       ├── Figure06.png
│       ├── Figure07.png
│       ├── Figure08.png
│       ├── Figure09.png
│       └── Figure10.png
│
└── archive/                                     # Everything historical / off the figure path
    ├── README.md                                # Phase 4 — explains every subfolder and its provenance
    │
    ├── notes/
    │   ├── analysis.txt                         # was /analysis.txt (author commentary on outputs)
    │   └── irrigation_speaker_notes.md          # was /irrigation_speaker_notes.md
    │
    ├── manuscript/                              # Out of code-reorg scope; staged here for tidiness
    │   ├── Abstract_Submission.docx
    │   └── Manuscript_Sriram_Kumar_IB_HK.docx-Google-Docs.pdf
    │
    ├── notebooks/
    │   └── Export_MD_Monthly_NDVI.ipynb         # was scripts/CreateNDVI/Export_MD_Monthly_NDVI.ipynb
    │
    ├── abstract_builder.py                      # was /abstract (top-level Python file with no extension)
    │
    ├── plotnd​wi_legacy/                         # whole scripts/PlotNDWI/ folder; depends on legacy NDWI-only CSV
    │   ├── README.md                            # explains the legacy NDWI-only pipeline & its CSVs
    │   ├── PreprocessNDWI.py
    │   ├── PlotIntervalNDWI.py                  # interactive (zero savefig); demoted from "Figure 8"
    │   ├── PlotMonthlyNDWI.py
    │   ├── PlotNDWIWaterStatistics.py
    │   ├── PlotYieldNDWITimeSeries.py
    │   └── PlotBusinessPatterns.py
    │
    ├── exploratory/                             # Scratch scripts not in the figure path
    │   ├── CombineETData.py
    │   ├── PlotETData.py
    │   ├── Regional_NDRE_Analysis.py
    │   ├── Regional_NDVI_Analysis.py
    │   ├── PlotNDWIByDistrict.py                # consumes maryland_ndwi_combined_wide.csv
    │   ├── PlotSoilandNDWI.py                   # consumes maryland_ndwi_combined_wide.csv
    │   └── SoilData.py
    │
    ├── ndre_pipeline/                           # NDRE not in paper
    │   ├── CombineNDRE.py
    │   └── PreprocessNDRE.py
    │
    ├── economic_context/
    │   └── PreprocessBusinessPatterns.py
    │
    ├── figure_drafts/                           # Variants & precursors of paper figures
    │   ├── README.md                            # Phase 4 — names each script + why archived
    │   ├── DroughtEffectFigureOptions.py        # full A–E generator preserved for provenance
    │   ├── StudyArea_YieldOptions.py
    │   ├── StudyArea_YieldGapFigures.py
    │   ├── StudyArea_Option2_Variations.py
    │   ├── ComprehensiveYieldPlots.py           # demoted from "Figure 4"
    │   ├── AnalyzeIrrigation.py                 # demoted from "Figure 7"
    │   ├── Statewide_Drought_Analysis.py        # demoted from "Figure 5"
    │   ├── PlotSoilComposition.py               # pre-Band5
    │   ├── SoilCompositionBand5_CountyDistrictHeatmap.py  # demoted from "Figure 2"
    │   ├── PlotDistrictPrecipitationClimatology.py  # demoted from "Figure 3"
    │   ├── PlotPrecipitationTrends.py
    │   ├── PlotNassData.py
    │   ├── PlotPDSIScatter.py
    │   ├── PlotDroughtIndicesPerDistrict.py
    │   ├── PlotPrecipitationPerDistrict.py
    │   ├── CompareNationalVsMaryland.py         # superseded by _AcreageYield
    │   └── PlotYieldTimeSeries.py               # was scripts/YieldAnalysis/
    │
    ├── combine_drought_legacy/                  # Original three Combine*Data.py kept for traceability
    │   ├── CombinePDSIData.py
    │   ├── CombinePHDIData.py
    │   └── CombinePMDIData.py
    │
    ├── soil_legacy/
    │   └── PreprocessSoilData.py                # superseded by Band5 consolidation
    │
    └── outputs_archive/
        ├── README.md                            # Phase 4 — what each subfolder is and why it's preserved
        └── DroughtIndices_15kb_errors/          # the four 15,127-byte error PNGs (do NOT regenerate)
            ├── County_Heatmaps_Precip_PDSI.png
            ├── County_Precip_PDSI_Analysis_Fixed_Axes.png
            ├── District_Heatmaps_Precip_PDSI.png
            └── District_Precip_PDSI_Analysis_Fixed_Axes.png
```

### 1.A — On the name `analysis/`

You asked me to propose a name for the Python package. I propose `analysis/` because it accurately describes what's inside (statistical analysis + figure generation), is short, and avoids confusion with the existing `scripts/Analysis/` (which goes away). Two alternatives if you prefer:

- `src/` — most common Python convention but the least descriptive (this isn't a library)
- `pipeline/` — accurate but slightly oversells the level of orchestration

**Default: `analysis/`. Tell me if you prefer a different name.**

### 1.B — `__init__.py` files

I'm proposing empty `__init__.py` files inside `analysis/`, `analysis/preprocessing/`, `analysis/stress_analysis/`, `analysis/figures/`, and `analysis/figures/supporting/` so that scripts can be invoked as `python -m analysis.preprocessing.preprocess_10day_indices` from the repo root, which is friendlier than `python scripts/Preprocess_MD_Soybean_10Day.py` (no path issues, no working-directory issues). All scripts will continue to work as plain `python path/to/script.py` too. Confirm if this is OK; if you'd rather skip the package structure, say so and I'll keep them as plain scripts.

### 1.C — Why `figures/figure05_flash_drought_summary.py` is dual-listed

`scripts/Analysis/DetectFlashDroughts.py` does both the analysis (writes `flash_drought_events_proxy.csv`, `flash_drought_counts_by_year_index.csv`, `flash_drought_descriptive_by_year_index.csv`) and the figure (`flash_drought_descriptive_summary.png` = Figure 5). Two clean options:

- **Option A (proposed):** copy of script lives at `analysis/figures/figure05_flash_drought_summary.py` and at `analysis/stress_analysis/detect_flash_droughts.py`. The figure path is a thin wrapper that imports from the analysis path. Avoids ambiguity in the figure manifest.
- **Option B:** keep only `analysis/stress_analysis/detect_flash_droughts.py` and reference it directly in the manifest. Skip the wrapper.

**Default: Option B (no duplication). Manifest will point to `analysis/stress_analysis/detect_flash_droughts.py` for Figure 5.**

### 1.D — Why `figures/figure06_drought_class_yield_boxplots.py` strips Options A/B/C/E

`scripts/Analysis/DroughtEffectFigureOptions.py` generates 5 design variants (A–E); only OptionD is published. Per your Phase 1 reply, I proposed `archive/figure_drafts/DroughtEffectFigureOptions.py` for the full generator and a slimmed `figures/figure06_drought_class_yield_boxplots.py` containing only the OptionD code path. Confirm or override.

---

## 2. Figure-to-script manifest

Will be materialized at `docs/figure_manifest.md` in Phase 3. Preview below.

| # | Title | Generating script (post-Phase 3 path) | Input CSV(s) | Output PNG (post-Phase 3) | Source PNG today |
|---|---|---|---|---|---|
| 1 | Maryland counties by NASS reporting district | `analysis/figures/figure01_md_districts_map.py` | None (uses `cb_2018_us_county_500k` shapefile + hard-coded district list) | `outputs/manuscript_figures/Figure01.png` | `outputs/Maps/Maryland_Counties_By_District.png` (303,903 B, byte-exact) |
| 2 | Soil composition heatmap by district | `analysis/figures/figure02_soil_district_heatmap.py` | `data/maryland_soil_composition_band5_2020.csv` | `outputs/manuscript_figures/Figure02.png` | `outputs/SoilCompositionBand5/variants/Variant_*.png` (no byte-exact match — figure was re-rendered) |
| 3 | Annual + Jul–Sep precipitation by district (10-yr blocks) | `analysis/figures/figure03_district_precip_decade_overlay.py` | `data/maryland_precipitation_combined_wide.csv` + `data/maryland_nass_data_cleaned_with_district.csv` | `outputs/manuscript_figures/Figure03.png` | output written by `PlotDistrictPrecipitationDecadeOverlay.py` |
| 4 | Historical yield trends by district (4 time periods) | `analysis/figures/figure04_yield_4block.py` | `data/maryland_nass_data_cleaned_with_district.csv` | `outputs/manuscript_figures/Figure04.png` | `outputs/YieldAnalysis/StudyArea/Options/Option2_FourBlocks_Enhanced.png` (re-rendered, not byte-exact) |
| 5 | Flash-drought proxy events per year (PDSI/PHDI/PMDI) | `analysis/stress_analysis/detect_flash_droughts.py` | `data/maryland_pdsi_combined_wide.csv` + `_phdi_` + `_pmdi_` | `outputs/manuscript_figures/Figure05.png` | `outputs/FlashDrought/flash_drought_descriptive_summary.png` (310,943 B, byte-exact) |
| 6 | County-year yield by PDSI drought class boxplots | `analysis/figures/figure06_drought_class_yield_boxplots.py` | `data/maryland_nass_data_cleaned_with_district.csv` + `data/maryland_pdsi_combined_wide.csv` | `outputs/manuscript_figures/Figure06.png` | `outputs/DroughtEffect/Options/OptionD_ByDistrict_SmallMultiples_v3_largerAxisLabels_2col_3rows.png` (1,023,081 B, byte-exact) |
| 7 | Irrigated soybean area heatmap (district × census year) | `analysis/figures/figure07_irrigated_district_heatmap.py` | NASS Census irrigation CSVs (Phase 3 will resolve exact path) | `outputs/manuscript_figures/Figure07.png` | output written by `PlotIrrigatedAcresDistrictHeatmap.py` (re-rendered, not byte-exact) |
| 8 | NDWI distribution by district and census period (R4–R6) | `analysis/figures/figure08_ndwi_r4r6_boxplot.py` | `data/maryland_soybean_10day_timeseries_wide_imputed.csv` (canonical 10-day pipeline output) | `outputs/manuscript_figures/Figure08.png` | `outputs/StressDrivers/figures/NDWI_R4R6_ByDistrict_Boxplot_ByCensusPeriod.png` (142,192 B, byte-exact) |
| 9 | NDVI/NDWI dual-axis "Invisible Stress Window" | `analysis/figures/figure09_ndvi_ndwi_scissors_dualaxis.py` | `data/maryland_soybean_10day_timeseries_wide_imputed.csv` | `outputs/manuscript_figures/Figure09.png` | `outputs/StressDrivers/figures/NDVI_NDWI_Scissors_DualAxis_2012_2024_LowerEastern.png` (212,501 B, byte-exact) |
| 10 | Production + yield variability for >8% sandy loam counties | `analysis/figures/figure10_salo_counties_yield.py` | `data/maryland_nass_data_cleaned_with_district.csv` + `data/maryland_soil_composition_band5_2020.csv` | `outputs/manuscript_figures/Figure10.png` | `outputs/Irrigation/SaLoCounties/SaLo_Counties_Acres_and_Yield_Bars.png` (169,140 B, byte-exact) |

Phase 3 will verify the **exact** input CSV paths by re-reading each script and writing them into the docstring + the manifest table. Any input I'm uncertain about today (Figs 2, 3, 7) gets a confirmation pass before relocation.

---

## 3. CLI parameterization for `combine_palmer_index.py`

The three legacy scripts (`CombinePDSIData.py`, `CombinePHDIData.py`, `CombinePMDIData.py`) are byte-identical except for three lines:

```text
data_folder    = 'data/pdsi'        | 'data/phdi'        | 'data/pmdi'
output_file    = 'data/maryland_pdsi_combined_wide.csv'
                                    | '..._phdi_...csv'  | '..._pmdi_...csv'
column_prefix  = 'PDSI_'            | 'PHDI_'            | 'PMDI_'
```

Proposed consolidated invocation:

```bash
python -m analysis.preprocessing.combine_palmer_index --index PDSI
python -m analysis.preprocessing.combine_palmer_index --index PHDI
python -m analysis.preprocessing.combine_palmer_index --index PMDI
```

Proposed implementation skeleton (will be the actual Phase 3 file modulo cosmetics):

```python
"""Combine NCEI county-level Palmer index CSVs into a wide pivot.

Usage:
  python -m analysis.preprocessing.combine_palmer_index --index PDSI
  python -m analysis.preprocessing.combine_palmer_index --index PHDI
  python -m analysis.preprocessing.combine_palmer_index --index PMDI

Inputs:  data/{pdsi|phdi|pmdi}/<County>.csv     (NCEI per-county exports)
Output:  data/maryland_{pdsi|phdi|pmdi}_combined_wide.csv

Behavior is bit-identical to the legacy Combine{PDSI,PHDI,PMDI}Data.py scripts
preserved in archive/combine_drought_legacy/. The only differences are the
input folder, output filename, and column prefix; all parsing, pivoting,
column renaming, and pivot aggfunc are unchanged.
"""

import argparse
import os
import pandas as pd

INDEX_CONFIG = {
    "PDSI": {
        "data_folder": "data/pdsi",
        "output_file": "data/maryland_pdsi_combined_wide.csv",
        "column_prefix": "PDSI_",
    },
    "PHDI": {
        "data_folder": "data/phdi",
        "output_file": "data/maryland_phdi_combined_wide.csv",
        "column_prefix": "PHDI_",
    },
    "PMDI": {
        "data_folder": "data/pmdi",
        "output_file": "data/maryland_pmdi_combined_wide.csv",
        "column_prefix": "PMDI_",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index",
        required=True,
        choices=sorted(INDEX_CONFIG),
        help="Which Palmer drought index to combine (PDSI, PHDI, or PMDI).",
    )
    args = parser.parse_args()
    cfg = INDEX_CONFIG[args.index]

    data_folder   = cfg["data_folder"]
    output_file   = cfg["output_file"]
    column_prefix = cfg["column_prefix"]

    # ---- Below this line: copied verbatim from legacy CombinePDSIData.py ----
    try:
        all_files = os.listdir(data_folder)
        csv_files = [f for f in all_files if f.endswith(".csv")]
        print(f"Found {len(csv_files)} files in '{data_folder}' to process.")
    except FileNotFoundError:
        print(f"Error: The folder '{data_folder}' was not found.")
        return

    if not csv_files:
        return

    all_data_list = []
    for filename in csv_files:
        file_path = os.path.join(data_folder, filename)
        df = pd.read_csv(file_path, skiprows=1)
        county_name = filename.replace(".csv", "")
        df["County"] = county_name
        df["Date"] = pd.to_datetime(df["Date"], format="%Y%m").dt.strftime("%Y-%m")
        all_data_list.append(df)

    long_df = pd.concat(all_data_list, ignore_index=True)
    print("Successfully combined all files into a single long-format table.")

    print(f"Pivoting the {column_prefix.strip('_')} table to a wide format...")
    wide_df = long_df.pivot_table(index="County", columns="Date", values="Value", aggfunc="mean")
    wide_df.columns = [column_prefix + str(col) for col in wide_df.columns]

    wide_df.to_csv(output_file)
    print(f"\n✅ Success! The combined data has been saved to: '{output_file}'")


if __name__ == "__main__":
    main()
```

Notes:
- The `from IPython.display import display` line and the `display(wide_df.head())` call are dropped during consolidation (dead code outside notebook context — per your Phase 1 reply: "These can be dropped as dead imports during the REWRITE phase if the `display(...)` calls are only relevant to notebooks").
- The three legacy `Combine{PDSI,PHDI,PMDI}Data.py` files are preserved verbatim under `archive/combine_drought_legacy/` for traceability.
- `CombinePrecipitationData.py` is **not** consolidated into this script: it has different `skiprows` (3 vs 1), different column-name handling (`names=['Date','Value']`), and a county-name remap dictionary. It moves to `analysis/preprocessing/combine_precipitation.py` as a separate REWRITE (relative paths + docstring only).

---

## 4. Complete file move list

Grouped by category. Each row is **`source path → target path`**, plus a short note.

### 4.A — KEEP / RENAME (paper pipeline; content unchanged, file relocated and renamed)

JavaScript (GEE editor scripts — **only headers added in Phase 3, no logic changes**):

| Source | Target |
|---|---|
| `scripts/GEE_Scripts/NDWI_Extraction` | `GEE_Scripts/01_NDWI_Monthly_Sentinel2.js` |
| `scripts/CreateNDVI/Monthly_NDVI_Soybean.js` | `GEE_Scripts/02_NDVI_Monthly_Sentinel2.js` |
| `scripts/GEE_Scripts/10_Day_NDVI_Reduction` | `GEE_Scripts/03_S2_10Day_NDVI_NDWI_2017plus.js` |
| `scripts/GEE_Scripts/10_Day_NDVI_Reduction_PRE2017` | `GEE_Scripts/04_S2_or_L8_10Day_NDVI_NDWI_PreS2.js` |

Manuscript figures (canonical PNGs — relocated to a sane folder name):

| Source | Target |
|---|---|
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure01.png` | `outputs/manuscript_figures/Figure01.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure02.png` | `outputs/manuscript_figures/Figure02.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure03.png` | `outputs/manuscript_figures/Figure03.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure04.png` | `outputs/manuscript_figures/Figure04.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure05.png` | `outputs/manuscript_figures/Figure05.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure06.png` | `outputs/manuscript_figures/Figure06.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure07.png` | `outputs/manuscript_figures/Figure07.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure08.png` | `outputs/manuscript_figures/Figure08.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure09.png` | `outputs/manuscript_figures/Figure09.png` |
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure10.png` | `outputs/manuscript_figures/Figure10.png` |

Documentation:

| Source | Target |
|---|---|
| `data/CENSUS_NASS_IRRIGATION.md` | `docs/census_nass_irrigation.md` |
| `LICENSE` | `LICENSE` (in place; copyright line updated in Phase 4) |

### 4.B — REWRITE (paper pipeline; minor changes: docstring + relative paths + dead-import cleanup; **diffs shown for any change >~10 lines**)

Preprocessing:

| Source | Target | Notable changes (Phase 3) |
|---|---|---|
| `scripts/Preprocess_MD_Soybean_10Day.py` | `analysis/preprocessing/preprocess_10day_indices.py` | Add docstring; verify all paths are relative; drop `from IPython.display import display` if unused |
| `scripts/PreprocessYieldData.py` | `analysis/preprocessing/preprocess_soybean_yield.py` | Same |
| `scripts/PreprocessCornYieldData.py` | `analysis/preprocessing/preprocess_corn_yield.py` | Same |
| `scripts/PreprocessDroughtData.py` | `analysis/preprocessing/preprocess_palmer_indices.py` | Same |
| `scripts/PreprocessSoilData_Band5.py` | `analysis/preprocessing/preprocess_soil_composition.py` | Same; non-Band5 logic from `PreprocessSoilData.py` is **NOT** ported (per your call: "Band5 is canonical"). The old `PreprocessSoilData.py` is archived under `archive/soil_legacy/`. |
| `scripts/BuildCensusIrrigationDataset.py` | `analysis/preprocessing/preprocess_irrigation_census.py` | Same |
| `scripts/CombineDroughtPrecipitationData/CombinePrecipitationData.py` | `analysis/preprocessing/combine_precipitation.py` | Same |
| `scripts/NASSPlotting/CombineNassData.py` | `analysis/preprocessing/combine_nass_metrics.py` | **Plus** input path correction `data/` → `data/nass/` (your call). Diff shown before applying. |

Stress analysis:

| Source | Target | Notable changes |
|---|---|---|
| `scripts/Analysis/Differential_Stress_Analysis.py` | `analysis/stress_analysis/differential_stress_analysis.py` | Docstring + relative paths; threshold drift flagged in §6, **not** changed |
| `scripts/Analysis/Longitudinal_10Day_Index_Analysis.py` | `analysis/stress_analysis/longitudinal_10day_indices.py` | Same |
| `scripts/Analysis/District_DroughtPrecip_Impact_On_Indices.py` | `analysis/stress_analysis/district_drought_precip_impact.py` | Same |
| `scripts/Analysis/District_Yield_vs_R4R6_Indices.py` | `analysis/stress_analysis/district_yield_vs_r4r6.py` | Same |
| `scripts/Analysis/NDWI_R4R6_TwoSample_TTests.py` | `analysis/stress_analysis/ndwi_r4r6_two_sample_ttests.py` | Same |
| `scripts/Analysis/PairedTTest_CountyYield_EarlyVsLate.py` | `analysis/stress_analysis/paired_ttest_county_yield.py` | Same |
| `scripts/Analysis/AnalyzeYieldVsDrought.py` | `analysis/stress_analysis/analyze_yield_vs_drought.py` | Same |
| `scripts/Analysis/AnalyzeDroughtResistance.py` | `analysis/stress_analysis/analyze_drought_resistance.py` | Same |
| `scripts/Analysis/AnalyzeIrrigationDroughtYield.py` | `analysis/stress_analysis/analyze_irrigation_drought_yield.py` | Same |
| `scripts/Analysis/DetectFlashDroughts.py` | `analysis/stress_analysis/detect_flash_droughts.py` | Same; produces Figure 5 |

Paper-figure scripts:

| Source | Target | Figure | Notable changes |
|---|---|---|---|
| `scripts/Plotting/MapMarylandDistricts.py` | `analysis/figures/figure01_md_districts_map.py` | 1 | Docstring + paths |
| `scripts/Plotting/SoilDistrictHeatmap_Variants.py` | `analysis/figures/figure02_soil_district_heatmap.py` | 2 | Docstring + paths; if it produces multiple variants, Phase 3 will narrow the canonical-output filename to one and document the rest as supplementary |
| `scripts/Plotting/PlotDistrictPrecipitationDecadeOverlay.py` | `analysis/figures/figure03_district_precip_decade_overlay.py` | 3 | Docstring + paths |
| `scripts/Plotting/StudyArea_Option2_Enhanced.py` | `analysis/figures/figure04_yield_4block.py` | 4 | Docstring + paths |
| `scripts/Analysis/DroughtEffectFigureOptions.py` | `analysis/figures/figure06_drought_class_yield_boxplots.py` | 6 | **Trim to OptionD only** (the published variant). Full A–E generator preserved at `archive/figure_drafts/DroughtEffectFigureOptions.py`. Diff shown. |
| `scripts/Plotting/PlotIrrigatedAcresDistrictHeatmap.py` | `analysis/figures/figure07_irrigated_district_heatmap.py` | 7 | Docstring + paths |
| `scripts/Plotting/PlotNDWI_R4R6_ByDistrict_Boxplot.py` | `analysis/figures/figure08_ndwi_r4r6_boxplot.py` | 8 | Docstring + paths |
| `scripts/Plotting/PlotNDVI_NDWI_Scissors_DualAxis.py` | `analysis/figures/figure09_ndvi_ndwi_scissors_dualaxis.py` | 9 | Docstring + paths |
| `scripts/Plotting/Plot_SaLo_Counties.py` | `analysis/figures/figure10_salo_counties_yield.py` | 10 | Docstring + paths |

Supporting figure scripts (per your Phase 1 reply: KEEP AS-IS but renamed for clarity):

| Source | Target |
|---|---|
| `scripts/Plotting/PlotNDVI_NDWI_Scissors.py` | `analysis/figures/supporting/ndvi_ndwi_scissors.py` |
| `scripts/Plotting/PlotPDSIVsYield.py` | `analysis/figures/supporting/plot_pdsi_vs_yield.py` |
| `scripts/Plotting/PlotPrecipVsYield.py` | `analysis/figures/supporting/plot_precip_vs_yield.py` |
| `scripts/Plotting/CompareNationalVsMaryland_AcreageYield.py` | `analysis/figures/supporting/compare_national_vs_md_acreage.py` |
| `scripts/Plotting/CompareCountyAndDistrictVsNational.py` | `analysis/figures/supporting/compare_county_district_vs_national.py` |
| `scripts/Plotting/CountyDistrict_Yield_Heatmaps.py` | `analysis/figures/supporting/countydistrict_yield_heatmaps.py` |
| `scripts/Plotting/StudyArea_Options3_4.py` | `analysis/figures/supporting/studyarea_options_3_4.py` |
| `scripts/Plotting/PlotIrrigatedAcres.py` | `analysis/figures/supporting/plot_irrigated_acres.py` |
| `scripts/Plotting/AnalyzeIrrigationSoilComposition.py` | `analysis/figures/supporting/analyze_irrigation_soil.py` |
| `scripts/NASSPlotting/DeriveNassInsights.py` | `analysis/figures/supporting/derive_nass_insights.py` |
| `scripts/Plotting/PlotDistrictPrecipitationTrends.py` | `analysis/figures/supporting/plot_district_precipitation_trends.py` |
| `scripts/Plotting/MapSoilCompositionBand5.py` | `analysis/figures/maps/map_soil_composition.py` |

§6.D contains an open question on whether `PlotSoilComposition_Band5.py` should be supporting (`figures/supporting/plot_soil_composition.py`) or archived.

### 4.C — CONSOLIDATE (multiple sources → one target)

| Sources | Target | Notes |
|---|---|---|
| `scripts/CombineDroughtPrecipitationData/CombinePDSIData.py` + `CombinePHDIData.py` + `CombinePMDIData.py` | `analysis/preprocessing/combine_palmer_index.py` | CLI in §3. Originals → `archive/combine_drought_legacy/` verbatim. |
| `scripts/PreprocessSoilData.py` + `scripts/PreprocessSoilData_Band5.py` | `analysis/preprocessing/preprocess_soil_composition.py` | Band5 logic only. Non-Band5 source → `archive/soil_legacy/PreprocessSoilData.py`. |

### 4.D — ARCHIVE (move to `archive/`, keep verbatim)

Notes / docs:

| Source | Target |
|---|---|
| `analysis.txt` | `archive/notes/analysis.txt` |
| `irrigation_speaker_notes.md` | `archive/notes/irrigation_speaker_notes.md` |
| `Abstract_Submission.docx` | `archive/manuscript/Abstract_Submission.docx` |
| `Manuscript_Sriram_Kumar_IB_HK.docx - Google Docs.pdf` | `archive/manuscript/Manuscript_Sriram_Kumar_IB_HK.pdf` (with rename to drop spaces) |
| `abstract` (top-level Python file) | `archive/abstract_builder.py` |

Notebooks:

| Source | Target |
|---|---|
| `scripts/CreateNDVI/Export_MD_Monthly_NDVI.ipynb` | `archive/notebooks/Export_MD_Monthly_NDVI.ipynb` |

Demoted / superseded plotting scripts (you confirmed all of these are not in the paper):

| Source | Target |
|---|---|
| `scripts/Plotting/ComprehensiveYieldPlots.py` | `archive/figure_drafts/ComprehensiveYieldPlots.py` |
| `scripts/Plotting/AnalyzeIrrigation.py` | `archive/figure_drafts/AnalyzeIrrigation.py` |
| `scripts/Plotting/Statewide_Drought_Analysis.py` | `archive/figure_drafts/Statewide_Drought_Analysis.py` |
| `scripts/Plotting/SoilCompositionBand5_CountyDistrictHeatmap.py` | `archive/figure_drafts/SoilCompositionBand5_CountyDistrictHeatmap.py` |
| `scripts/Plotting/PlotDistrictPrecipitationClimatology.py` | `archive/figure_drafts/PlotDistrictPrecipitationClimatology.py` |
| `scripts/Plotting/PlotSoilComposition.py` (pre-Band5) | `archive/figure_drafts/PlotSoilComposition.py` |
| `scripts/Plotting/StudyArea_YieldOptions.py` | `archive/figure_drafts/StudyArea_YieldOptions.py` |
| `scripts/Plotting/StudyArea_YieldGapFigures.py` | `archive/figure_drafts/StudyArea_YieldGapFigures.py` |
| `scripts/Plotting/StudyArea_Option2_Variations.py` | `archive/figure_drafts/StudyArea_Option2_Variations.py` |
| `scripts/Plotting/CompareNationalVsMaryland.py` | `archive/figure_drafts/CompareNationalVsMaryland.py` |
| `scripts/Plotting/PlotPrecipitationTrends.py` | `archive/figure_drafts/PlotPrecipitationTrends.py` |
| `scripts/Plotting/PlotNassData.py` | `archive/figure_drafts/PlotNassData.py` |
| `scripts/Plotting/PlotPDSIScatter.py` | `archive/figure_drafts/PlotPDSIScatter.py` |
| `scripts/Plotting/PlotDroughtIndicesPerDistrict.py` | `archive/figure_drafts/PlotDroughtIndicesPerDistrict.py` |
| `scripts/Plotting/PlotPrecipitationPerDistrict.py` | `archive/figure_drafts/PlotPrecipitationPerDistrict.py` |
| `scripts/Plotting/Regional_NDRE_Analysis.py` | `archive/figure_drafts/Regional_NDRE_Analysis.py` |
| `scripts/Plotting/Regional_NDVI_Analysis.py` | `archive/figure_drafts/Regional_NDVI_Analysis.py` |
| `scripts/Plotting/PlotETData.py` | `archive/figure_drafts/PlotETData.py` |
| `scripts/YieldAnalysis/PlotYieldTimeSeries.py` | `archive/figure_drafts/PlotYieldTimeSeries.py` |
| `scripts/Analysis/DroughtEffectFigureOptions.py` | `archive/figure_drafts/DroughtEffectFigureOptions.py` (full A–E generator preserved) |

Whole `scripts/PlotNDWI/` directory:

| Source | Target |
|---|---|
| `scripts/PlotNDWI/PreprocessNDWI.py` | `archive/plotndwi_legacy/PreprocessNDWI.py` |
| `scripts/PlotNDWI/PlotIntervalNDWI.py` | `archive/plotndwi_legacy/PlotIntervalNDWI.py` |
| `scripts/PlotNDWI/PlotMonthlyNDWI.py` | `archive/plotndwi_legacy/PlotMonthlyNDWI.py` |
| `scripts/PlotNDWI/PlotNDWIWaterStatistics.py` | `archive/plotndwi_legacy/PlotNDWIWaterStatistics.py` |
| `scripts/PlotNDWI/PlotYieldNDWITimeSeries.py` | `archive/plotndwi_legacy/PlotYieldNDWITimeSeries.py` |
| `scripts/PlotNDWI/PlotBusinessPatterns.py` | `archive/plotndwi_legacy/PlotBusinessPatterns.py` |

Top-level scratch scripts:

| Source | Target |
|---|---|
| `scripts/PlotNDWIByDistrict.py` | `archive/exploratory/PlotNDWIByDistrict.py` |
| `scripts/PlotSoilandNDWI.py` | `archive/exploratory/PlotSoilandNDWI.py` |
| `scripts/SoilData.py` | `archive/exploratory/SoilData.py` |
| `scripts/CombineETData.py` | `archive/exploratory/CombineETData.py` |
| `scripts/PreprocessBusinessPatterns.py` | `archive/economic_context/PreprocessBusinessPatterns.py` |
| `scripts/CreateNDRE/CombineNDRE.py` | `archive/ndre_pipeline/CombineNDRE.py` |
| `scripts/CreateNDRE/PreprocessNDRE.py` | `archive/ndre_pipeline/PreprocessNDRE.py` |

Outputs:

| Source | Target |
|---|---|
| `outputs/DroughtIndices/County_Heatmaps_Precip_PDSI.png` (15,127 B) | `archive/outputs_archive/DroughtIndices_15kb_errors/` |
| `outputs/DroughtIndices/County_Precip_PDSI_Analysis_Fixed_Axes.png` (15,127 B) | `archive/outputs_archive/DroughtIndices_15kb_errors/` |
| `outputs/DroughtIndices/District_Heatmaps_Precip_PDSI.png` (15,127 B) | `archive/outputs_archive/DroughtIndices_15kb_errors/` |
| `outputs/DroughtIndices/District_Precip_PDSI_Analysis_Fixed_Axes.png` (15,127 B) | `archive/outputs_archive/DroughtIndices_15kb_errors/` |

Everything else under `outputs/` (the dozens of intermediate/exploratory tables and PNGs) is **not moved**; instead it is **excluded from version control via the new `.gitignore`** in Phase 4. Git history for those files is preserved (we don't `git rm` history-bearing tracked outputs unless you say so). Practically that means:

- Locally: the files stay on disk (everything under `outputs/` minus `outputs/manuscript_figures/`) but won't appear in `git status`.
- For Zenodo: the published archive is built from the cleaned tree, so these files don't ship.

If you'd rather *physically delete* the bulk of `outputs/` from disk too, say so and I'll add explicit deletes in Phase 3. Default is "leave on local disk, gitignore for the public release."

### 4.E — DELETE (true cruft; no provenance value)

| Source | Reason |
|---|---|
| `.DS_Store` (root + every subfolder) | macOS metadata, no value, will be `.gitignore`d going forward |
| `venv/` | Local virtualenv; not tracked anyway, but ensure `.gitignore` covers it |
| `__pycache__/`, `*.pyc` | Already ignored; double-check Phase 4 `.gitignore` covers them |

No script files are in this category.

---

## 5. Top-level structure

| File | Status | Phase |
|---|---|---|
| `README.md` | currently 118-byte placeholder; full rewrite | Phase 4 |
| `LICENSE` | KEEP AS-IS (MIT). Refresh the copyright line text only (`Copyright (c) 2025 Ananth Sriram` → year + your preferred name). | Phase 4 |
| `CITATION.cff` | NEW. CFF v1.2.0 with author list, paper title placeholder, repo URL, license: MIT, Zenodo DOI placeholder. | Phase 4 |
| `requirements.txt` | currently 18 lines, missing `seaborn`/`scipy`/`statsmodels`/`ipython`. Rewrite, pin from `pip freeze`. | Phase 4 |
| `.gitignore` | currently 576 bytes; rewrite (see §5.E) | Phase 4 |
| `REORG_PHASE1_INVENTORY.md` and `REORG_PHASE2_PROPOSAL.md` | internal reorg logs; kept until Phase 5 then deleted | Phase 5 |

### 5.E — Proposed `.gitignore` (full content for Phase 4)

```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg
*.egg-info/
build/
dist/

# Virtual envs
venv/
.venv/
env/
.env

# Jupyter
.ipynb_checkpoints/

# OS / editor
.DS_Store
.idea/
.vscode/
*.swp

# Project-specific
data/                        # all input data; users obtain themselves
data/!README.md              # but do track the data/README that explains where to obtain inputs
outputs/                     # all generated output by default
!outputs/manuscript_figures/ # except the 10 published manuscript figures
!outputs/manuscript_figures/*.png

# Reorg logs (deleted at Phase 5)
REORG_PHASE1_INVENTORY.md
REORG_PHASE2_PROPOSAL.md
```

Note on the `!data/README.md` exception: standard `.gitignore` syntax requires un-ignoring the file directly under the ignored directory. Phase 4 will tune the exact pattern based on what's tracked at that point.

---

## 6. New TODOs surfaced during Phase 2 design

These are flags only. Nothing here is fixed in this phase or in Phase 3 unless you explicitly opt in.

### 6.A — `maryland_ndwi_combined_wide.csv` Colab pipeline TODO — **DROPPED**

Per your sign-off in this exchange. Reason: only consumers (`PlotNDWIByDistrict.py`, `PlotSoilandNDWI.py`) are archived as exploratory. No paper figure depends on the file.

### 6.B — `maryland_ndwi_10day_final_imputed.csv` legacy CSV (separate from 6.A)

This file is consumed by every script in `scripts/PlotNDWI/` and is produced in-repo by `scripts/PlotNDWI/PreprocessNDWI.py`. Under this proposal, all consumers move to `archive/plotndwi_legacy/`. Two options:

- **6.B.1 (default):** mark `archive/plotndwi_legacy/README.md` as the documentation home for this entire legacy NDWI-only pipeline. The README will state: input = `data/ndwi_ten_day_interval/<County>.csv`, output = `data/maryland_ndwi_10day_final_imputed.csv`, consumers = the five archived scripts. No further action needed for paper reproducibility.
- **6.B.2:** preserve `PreprocessNDWI.py` as a non-archived utility under `analysis/preprocessing/preprocess_ndwi_10day_legacy.py` in case a reviewer wants to re-run the legacy NDWI-only path. **Not recommended** since the canonical 10-day pipeline (`Preprocess_MD_Soybean_10Day.py`) supersedes it.

**Default: 6.B.1.**

### 6.C — Threshold-value drift (PRESERVED, not changed)

Per your policy. Phase 3 will produce a TODO list at the end with the file/line of every occurrence of `0.121`, `0.144`, `0.12`, `0.1325` so you can reconcile by hand. No silent changes. Quick scan I've already done:

```
scripts/PlotNDWI/PlotIntervalNDWI.py:8     "NDWI < 0.1325 indicates water stress (average of 0.121 and 0.144 from research)"
scripts/PlotNDWI/PlotIntervalNDWI.py:9     "0.121-0.144"
... (full enumeration coming in Phase 3 TODO list)
```

After the move to `archive/plotndwi_legacy/`, the in-paper-pipeline scripts that touch this threshold will be a much smaller set, narrowing your reconciliation surface.

### 6.D — `PlotSoilComposition_Band5.py` placement

You said "PlotSoilComposition.py vs PlotSoilComposition_Band5.py: Same as above — _Band5 is canonical." That was an instruction for the **preprocessor pair** (PreprocessSoilData[_Band5].py), but the same naming exists for the **plotter pair**. The plotter `PlotSoilComposition_Band5.py` writes 7 panels, none of which is byte-exact for Figure 2. It's currently:

- a precursor to the canonical Figure 2 generator (`SoilDistrictHeatmap_Variants.py`) — likely ARCHIVE
- OR a useful supporting figure script — likely `analysis/figures/supporting/plot_soil_composition.py`

**My default: classify as supporting (KEEP/RENAME to `analysis/figures/supporting/plot_soil_composition.py`)**, since you previously asked me to keep the _Band5 version. Override to ARCHIVE if you want it strictly off the figure path.

### 6.E — `Statewide_Drought_Analysis.py` writes 4 of the 15,127-byte error PNGs

Three of the four `15,127 B` "error" PNGs you flagged are written by `Statewide_Drought_Analysis.py`'s savefig calls (`District_Precip_PDSI_Analysis_Fixed_Axes.png`, `District_Heatmaps_Precip_PDSI.png`). The script itself is being archived. After archiving the script, future runs cannot regenerate these tiny PNGs (which is what we want). Just flagging that the cause is now traceable.

### 6.F — `figure02_soil_district_heatmap.py` writes "variants" in its current form

`SoilDistrictHeatmap_Variants.py` writes multiple `Variant_*.png` panels to `outputs/SoilCompositionBand5/variants/`. None is a 250,034-byte byte-exact match for Figure 2; the published figure was almost certainly one of these variants, re-rendered. Phase 3 needs you to confirm **which Variant_*.png is the published Figure 2** so I can write the exact output filename into the figure manifest. I'll surface this as a question during Phase 3 — does NOT block Phase 2 sign-off.

### 6.G — Manuscript PDF/DOCX in `archive/manuscript/`

`Manuscript_Sriram_Kumar_IB_HK.docx - Google Docs.pdf` is 1.9 MB. I'm proposing to track it under `archive/manuscript/` for provenance (Zenodo will see a snapshot of the manuscript alongside the code). If you'd rather **not** publish the manuscript draft on Zenodo, add it to `.gitignore` in Phase 4 instead. Default: track it.

### 6.H — `data/` README + dataset inventory

A new `data/README.md` is proposed for Phase 4 listing every CSV/folder the scripts read, the source URL, and how a stranger obtains it. This is a Phase 4 deliverable, not Phase 3. Just flagging that it's the right home for the GEE-export inventory + NCEI download instructions.

### 6.I — Banner / shebang on legacy scripts

I propose **not** adding shebangs (`#!/usr/bin/env python`) to anything. Existing scripts don't have them and Cursor will treat any addition as a noisy diff. Override if you want them.

### 6.J — Deferred to Phase 3, not blocking sign-off

- Verifying every script's actual `read_csv` paths (Phase 3 must read each source file once to confirm path strings before relocation).
- Running `pip freeze` for `requirements.txt` (Phase 4).
- The `from IPython.display import display` removal pass — 16 scripts; none of those calls is reachable outside notebooks.

---

## 7. Sign-off checklist

Approve any subset; I'll only execute the approved items.

- [ ] Directory tree (§1) including the `analysis/` package name and `__init__.py` files (§1.A, §1.B)
- [ ] Figure 5 dual-listing strategy (§1.C — default Option B, no wrapper)
- [ ] Figure 6 trimmed to OptionD only (§1.D)
- [ ] CLI design for `combine_palmer_index.py` (§3)
- [ ] Full file move list (§4.A through §4.E)
- [ ] Top-level layout & `.gitignore` policy (§5)
- [ ] TODO 6.B.1 (default for legacy NDWI documentation)
- [ ] TODO 6.D (`plot_soil_composition.py` → supporting, default)
- [ ] TODO 6.G (track manuscript PDF/DOCX in archive/manuscript/, default)
- [ ] Outputs not in `outputs/manuscript_figures/` — gitignore them but leave on local disk (§4.D last paragraph, default)
- [ ] Anything to override

Once this is signed off, Phase 3 will:

1. Apply the moves in §4 in dependency order (preprocessing first, analysis next, figures last).
2. For each REWRITE, show a diff before applying when the diff exceeds ~10 lines.
3. Produce a TODO list at the end of Phase 3 with: every threshold-value drift occurrence, every `IPython.display` removal, and the Figure 2 variant question (§6.F).

Stop here. Awaiting sign-off.
