# Phase 1 — Repository Inventory

This is a working document for the public-release reorganization of
`maryland-soybean-stress`. It is **read-only** at this stage: nothing is moved,
renamed, or deleted yet. It captures one author's-eye view of every tracked
and untracked file in the repository so you (the human owner) can confirm or
override the categorization before we move to Phase 2.

Categories used:

- **KEEP AS-IS** — canonical analysis, used in the paper, well-named and well-placed.
- **KEEP / RENAME** — canonical, but poorly named or in the wrong directory.
- **REWRITE** — canonical or near-canonical, but undocumented, duplicative, or
  uses inconsistent paths/idioms. (Phase 3 only adds a docstring + relative
  paths — no numerical changes.)
- **ARCHIVE** — exploratory or scratch; preserved under `archive/` for
  provenance, not part of the figure-generating pipeline.
- **DELETE** — empty/dead; safe to remove.

A separate file is **OUT-OF-SCOPE** (the manuscript PDF, the abstract DOCX,
the CSV outputs that aren't input to anything else, etc.). Those are
addressed in the directory-level summary at the end.

---

## A. Top-level files

| Path | Best inference of purpose | Category |
|---|---|---|
| `README.md` | 2-line placeholder README. | REWRITE (full paper README in Phase 4) |
| `LICENSE` | MIT, owner = `ananthsriram1`, year = 2025. | KEEP AS-IS (Phase 4 may update copyright line) |
| `.gitignore` | Standard Python + .DS_Store + `data/` ignored. Reasonable. | REWRITE in Phase 4 (add `outputs/` for large CSVs, add `.env`, `.venv`, `.ipynb_checkpoints` already there). |
| `requirements.txt` | Pins matplotlib/numpy/pandas/pillow/etc + `python-docx` + `geopandas`. **Missing: `seaborn`, `scipy`, `statsmodels`, `ipython` (used by many scripts).** | REWRITE (add missing deps with version pins) |
| `analysis.txt` | Author's notes on which `outputs/` figures show what insights. Not code. | ARCHIVE (move to `archive/notes/analysis.txt`) |
| `irrigation_speaker_notes.md` | Long narrative for an irrigation talk; per-census-year speaker notes. Not code. | ARCHIVE (move to `archive/notes/`) |
| `abstract` (no extension) | Python script that builds `Abstract_Submission.docx` via `python-docx`. | ARCHIVE (`archive/abstract_builder.py`) |
| `Abstract_Submission.docx` | Generated abstract. | OUT-OF-SCOPE for code reorg; can stay or move to `archive/manuscript/`. |
| `Manuscript_Sriram_Kumar_IB_HK.docx - Google Docs.pdf` | Manuscript PDF. | OUT-OF-SCOPE; suggest moving to `archive/manuscript/` and adding to `.gitignore` if you don't want it in the public repo. |
| `venv/` | Local venv. | DELETE from tracking (already in `.gitignore`). |
| `.DS_Store` (root and several subfolders) | macOS metadata. | DELETE; `.gitignore` already covers them but a few exist and should be untracked / removed. |

---

## B. `scripts/GEE_Scripts/` — Google Earth Engine source (canonical)

These are JavaScript files (no `.js` extension) copied verbatim from the GEE
code editor. Per your constraint: keep syntactically intact, can rename and
add headers but not rewrite logic.

| Path | Purpose | Category |
|---|---|---|
| `scripts/GEE_Scripts/NDWI_Extraction` | Sentinel-2 SR_HARMONIZED → monthly mean NDWI per Maryland county, masked to USDA CDL soybean pixels. Currently hard-codes July 2023; user changes the date and re-runs per month. Exports CSV to Drive. | KEEP / RENAME → `GEE_Scripts/01_NDWI_Monthly_Sentinel2.js`. Add `.js` extension and a header comment block. |
| `scripts/GEE_Scripts/10_Day_NDVI_Reduction` | Sentinel-2 only, 10-day median composites May–Oct of a single year (currently 2024). NDVI + NDWI per county, with Sentinel-2 cloud-probability mask (35% threshold). Exports `MD_Soybean_10Day_TimeSeries_2024.csv`. | KEEP / RENAME → `GEE_Scripts/02_S2_10Day_NDVI_NDWI_2017plus.js` |
| `scripts/GEE_Scripts/10_Day_NDVI_Reduction_PRE2017` | Same 10-day pipeline but with a Sentinel-2 / Landsat-8 fallback for years before S2 coverage. Year hard-coded (currently 2011). | KEEP / RENAME → `GEE_Scripts/03_S2_or_L8_10Day_NDVI_NDWI_PreS2.js` |

There is also one stray `.js` file outside this folder:

| Path | Purpose | Category |
|---|---|---|
| `scripts/CreateNDVI/Monthly_NDVI_Soybean.js` | Same shape as `NDWI_Extraction` but for monthly NDVI (B8/B4). Currently hard-codes Nov 2024. | KEEP / RENAME → `GEE_Scripts/04_NDVI_Monthly_Sentinel2.js` |

After move, `GEE_Scripts/` will contain 4 `.js` files plus a README.md (Phase 4).

---

## C. `scripts/CreateNDVI/` — Colab notebook for combining NDVI exports

| Path | Purpose | Category |
|---|---|---|
| `scripts/CreateNDVI/Export_MD_Monthly_NDVI.ipynb` | Google Colab notebook. Mounts Google Drive, reads the per-month NDVI CSVs exported by the GEE script, pivots to wide, filters to MD counties, writes `maryland_only_soybean_ndvi_timeseries_FINAL.csv`. Functionally identical to `scripts/CreateNDRE/CombineNDRE.py + PreprocessNDRE.py` but for NDVI. | ARCHIVE (`archive/notebooks/Export_MD_Monthly_NDVI.ipynb`). The same logic for NDVI is missing from the Python pipeline — see "Gaps" at end. |

---

## D. `scripts/` (top-level Python files, mostly preprocessing)

| Path | Purpose | Category |
|---|---|---|
| `scripts/Preprocess_MD_Soybean_10Day.py` | Concatenates `data/MD_SOYBEAN_10DAY/MD_Soybean_10Day_TimeSeries_YYYY.csv`, filters to 24 MD counties, dedup, attach Ag district, ffill/bfill impute, write long + wide + wide-imputed. **The single most important preprocessing script for the paper.** | KEEP / RENAME → `analysis/preprocessing/preprocess_10day_indices.py` (or similar — see Phase 2). Already well-documented. |
| `scripts/PreprocessYieldData.py` | Reads `data/nass/YieldBu:Acre97to25.csv`, cleans, splits into 11 derivative CSVs under `data/processed_yield/`. Canonical for soybean yield. | KEEP / RENAME → `analysis/preprocessing/preprocess_soybean_yield.py`. |
| `scripts/PreprocessCornYieldData.py` | Mirror of the above but for corn (`data/Corn_Yield_1997to2024.csv` → `data/processed_corn_yield/`). Used for context but **corn does not appear in the paper figures**. Suggest keeping anyway because it's tidy and supports any reviewer follow-up. | KEEP / RENAME → `analysis/preprocessing/preprocess_corn_yield.py` (optional pipeline, document in README as auxiliary). |
| `scripts/PreprocessDroughtData.py` | Reads NCEI county PDSI/PHDI/PMDI from `data/drought_data_1997-2025/`, normalizes county names, builds `drought_monthly_county.csv`, county-year aggregates, and district-year aggregates. Drives every downstream drought analysis. | KEEP / RENAME → `analysis/preprocessing/preprocess_palmer_indices.py`. |
| `scripts/PreprocessSoilData.py` | Reads `data/soybeanSoilCompositionPerCounty.csv` (full CDL soybean values 5/26/239/240/241/254) → 5 CSV outputs in `data/processed/`. | KEEP / RENAME → `analysis/preprocessing/preprocess_soil_composition.py`. |
| `scripts/PreprocessSoilData_Band5.py` | Same script as above except (a) tab-indented instead of 4-space, (b) reads band-5-only CDL inputs (`*band5.csv`), (c) writes to `data/processed_band5/`. **The Band-5 outputs are what's used in the paper soil-composition figures.** Differs from the non-Band5 script only in input/output paths and indentation. | REWRITE — merge into a single `analysis/preprocessing/preprocess_soil_composition.py` with a `--band5/--all-soybean` flag (or two output directories). Numerical behavior preserved. |
| `scripts/BuildCensusIrrigationDataset.py` | Reads `data/nass/IrrigationvsNonirrigated.csv` → `data/census_nass_irrigation_all.csv`. Already well-documented (header + module docstring). | KEEP / RENAME → `analysis/preprocessing/preprocess_irrigation_census.py`. |
| `scripts/PreprocessBusinessPatterns.py` | Reads district-level "Business Patterns" CSVs (NAICS counts) → cleaned wide CSV. **Business Patterns appears in `outputs/BusinessPatterns/` which is NOT part of the manuscript figures (you can confirm).** | ARCHIVE (`archive/economic_context/`) unless the BP figure ends up in supplementary. |
| `scripts/CombineETData.py` | Combines monthly ET CSVs (`data/et/`) → MD-only ET wide CSV. **ET is not in the paper figures; ET outputs are exploratory.** Uses `IPython.display`. | ARCHIVE (`archive/exploratory/`). |
| `scripts/PlotNDWIByDistrict.py` | Top-level script: simple line plot of NDWI by district from `data/maryland_ndwi_combined_wide.csv` (a legacy file not produced by any script in the repo). Superseded by `PlotNDWI/PreprocessNDWI.py` + `PlotNDWI/PlotMonthlyNDWI.py`. | ARCHIVE. |
| `scripts/PlotSoilandNDWI.py` | Top-level early scatter of soil water capacity vs NDWI by district. Reads legacy `maryland_ndwi_combined_wide.csv`. Superseded by `Differential_Stress_Analysis.py` and `Longitudinal_10Day_Index_Analysis.py`. | ARCHIVE. |
| `scripts/SoilData.py` | 32-line scratch: bar chart of avg soil water content by district. Comment header: "filter the soil data". Pure exploration. | ARCHIVE. |

---

## E. `scripts/Analysis/` — The paper's main statistical / figure pipeline

These are the analytical engines for the manuscript. Most have proper module
docstrings.

| Path | Purpose | Category |
|---|---|---|
| `scripts/Analysis/Differential_Stress_Analysis.py` | Five analyses (NDVI plateau, leading-indicator/cross-correlation, 2012 soil tipping point, detrended-anomaly heatmaps, AUC yield model). 33 KB, well-documented. **Major paper engine.** | KEEP AS-IS. |
| `scripts/Analysis/Longitudinal_10Day_Index_Analysis.py` | Six analyses (R4–R6 sensitivity, drought correlations, soil resilience, 2012 NDWI signature, district stress heatmaps, critical phenological window). 32 KB. **Major paper engine.** | KEEP AS-IS. |
| `scripts/Analysis/AnalyzeDroughtResistance.py` | Yield-by-drought-class boxplot + per-county drought-resistance scatter. Output dir `outputs/DroughtEffect/`. Documented. | KEEP AS-IS. |
| `scripts/Analysis/AnalyzeIrrigationDroughtYield.py` | Compares yield in drought between irrigated and non-irrigated counties (using census irrigation status carried forward). Documented. | KEEP AS-IS. |
| `scripts/Analysis/AnalyzeYieldVsDrought.py` | District-level Pearson correlations between Palmer indices and yield, scatter plots. Documented. | KEEP AS-IS. |
| `scripts/Analysis/DetectFlashDroughts.py` | "Flash drought" proxy from monthly Palmer indices (acknowledged limitation in docstring: weekly definitions not possible without USDM/EDDI). Outputs counts and event tables. | KEEP AS-IS. |
| `scripts/Analysis/District_DroughtPrecip_Impact_On_Indices.py` | District-by-district precip + drought vs late-season NDVI/NDWI anomalies. Documented. Outputs `outputs/StressDrivers/`. | KEEP AS-IS. |
| `scripts/Analysis/District_Yield_vs_R4R6_Indices.py` | District yield vs R4–R6 NDVI/NDWI relationships (uses `District_DroughtPrecip_Impact_On_Indices.py` table as input). Documented. | KEEP AS-IS. |
| `scripts/Analysis/DroughtEffectFigureOptions.py` | Generates 5 figure variants (A–E) for the drought-vs-yield boxplot decision. **OptionD (small multiples) is the published figure; OptionA/B/C/E are exploratory.** | KEEP AS-IS code but document this prominently in the docstring. The non-final option PNGs in `outputs/DroughtEffect/Options/` should stay (they document the figure choice). |
| `scripts/Analysis/NDWI_R4R6_TwoSample_TTests.py` | Welch t-tests + chi-square + ANOVA on R4–R6 NDWI by district. Documented including caveats. | KEEP AS-IS. |
| `scripts/Analysis/PairedTTest_CountyYield_EarlyVsLate.py` | Paired t-test 1997–2006 vs 2019–2025 county-mean yields. Documented. | KEEP AS-IS. |

---

## F. `scripts/Plotting/` — Figure scripts

Mixed: a number are canonical figure-generators for the manuscript; many are
older "options" / "variations" / pre-Band5 versions that the paper does not
use.

### F.1 Likely canonical (paper figures or directly cited tables)

| Path | Purpose | Category |
|---|---|---|
| `scripts/Plotting/MapMarylandDistricts.py` | Choropleth of MD counties colored by ag district. Likely Figure 1 study-area map. Documented. | KEEP AS-IS. |
| `scripts/Plotting/MapSoilCompositionBand5.py` | Choropleth maps for each soil type (band-5 soybean only). Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotNDVI_NDWI_Scissors.py` | Single-county "scissors" plot (NDVI plateau / NDWI decline). Documented + CLI. | KEEP AS-IS. |
| `scripts/Plotting/PlotNDVI_NDWI_Scissors_DualAxis.py` | Two-county dual-axis scissors plot for 2012 + 2024 (Southern vs Eastern). Likely a paper figure. Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotNDWI_R4R6_ByDistrict_Boxplot.py` | R4–R6 NDWI boxplot across districts (single panel + 4-period grid). Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotIrrigatedAcres.py` | Comprehensive irrigation visualizations (county-year). | KEEP AS-IS. |
| `scripts/Plotting/PlotIrrigatedAcresDistrictHeatmap.py` | District×census-year irrigated-acres heatmap (acres → ha SI). Documented. | KEEP AS-IS. |
| `scripts/Plotting/AnalyzeIrrigationSoilComposition.py` | Irrigation × soil composition (band5) correlations & scatter. Documented. | KEEP AS-IS. |
| `scripts/Plotting/Plot_SaLo_Counties.py` | Acres planted + yield for SaLo > 8% counties. Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotPDSIVsYield.py` | PDSI × yield scatters per district. Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotPrecipVsYield.py` | Precip × yield scatters per district. Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotDistrictPrecipitationClimatology.py` | District-level precip climatology (boxplots / mean±SD). Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotDistrictPrecipitationDecadeOverlay.py` | Decade-binned precip overlays. Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotDistrictPrecipitationTrends.py` | District precip trends small multiples (Option A figure). Documented. | KEEP AS-IS. |
| `scripts/Plotting/PlotPrecipitationTrends.py` | Older comprehensive precip plotting (24KB, Jan 16). Some overlap with the District_Precipitation* scripts. | REWRITE (just docstring + path tidy). |
| `scripts/Plotting/PlotSoilComposition_Band5.py` | Band-5-only soil composition plots (the variant matching the paper). Tab-indented. | KEEP AS-IS. |
| `scripts/Plotting/SoilCompositionBand5_CountyDistrictHeatmap.py` | Single-figure soil composition summary heatmap (district + county). Documented. | KEEP AS-IS. |
| `scripts/Plotting/SoilDistrictHeatmap_Variants.py` | Variants of the district soil heatmap. Useful for figure-choice provenance. | KEEP AS-IS or ARCHIVE (your call — they're intentional variants, not exploratory junk). |
| `scripts/Plotting/StudyArea_Option2_Enhanced.py` | "Final" study-area Option 2 figure (4 time-blocks with reference lines). | KEEP AS-IS (likely Figure 2). |
| `scripts/Plotting/StudyArea_Options3_4.py` | Decade-binned dot+whisker yield/yield-gap (Option 3); irrigated acres by district (Option 4). | KEEP AS-IS. |
| `scripts/Plotting/CompareNationalVsMaryland_AcreageYield.py` | National vs MD soybean acreage and yield. Newer script (Nov 7). | KEEP AS-IS. |
| `scripts/Plotting/CompareCountyAndDistrictVsNational.py` | County-and-district small-multiples vs US/MD. Newer (Nov 7). | KEEP AS-IS. |
| `scripts/Plotting/CountyDistrict_Yield_Heatmaps.py` | County/district yield heatmaps and difference-vs-MD/US heatmaps. Newer (Nov 7). | KEEP AS-IS. |

### F.2 Older / superseded plotting scripts

| Path | Purpose | Category |
|---|---|---|
| `scripts/Plotting/PlotSoilComposition.py` | Pre-Band5 version of soil composition plotting. Superseded by `_Band5` variant. | ARCHIVE. |
| `scripts/Plotting/CompareNationalVsMaryland.py` | Older (Oct 23) version of `CompareNationalVsMaryland_AcreageYield.py`. Big overlap. | ARCHIVE. |
| `scripts/Plotting/AnalyzeIrrigation.py` | Comprehensive irrigation analysis (Oct 23). Possibly superseded by the newer (Nov 7 / Apr 24) `PlotIrrigatedAcres*.py` family + `AnalyzeIrrigationSoilComposition.py`. Without the paper figure list it's hard to tell. | KEEP AS-IS pending your call (possibly REWRITE if used for an SI figure, otherwise ARCHIVE). |
| `scripts/Plotting/ComprehensiveYieldPlots.py` | 41 KB Oct-23 yield-plot kitchen sink. Likely partially superseded by the newer `StudyArea_*` and `CountyDistrict_Yield_Heatmaps.py`. | ARCHIVE unless individual figures here are still in the paper. |
| `scripts/Plotting/StudyArea_YieldOptions.py` | 6 visualization options for district yield by time blocks — the precursor to `Option2_Enhanced`. | ARCHIVE. |
| `scripts/Plotting/StudyArea_YieldGapFigures.py` | Earlier yield-gap figures (Options 1–2 only, w/o time blocks). | ARCHIVE. |
| `scripts/Plotting/StudyArea_Option2_Variations.py` | Variants of Option 2. | ARCHIVE. |
| `scripts/Plotting/PlotNassData.py` | 50-line older NASS plotter using `IPython.display`. Reads `data/maryland_nass_data_cleaned_with_district.csv`. Plotting routine for early figures. | ARCHIVE. |
| `scripts/Plotting/PlotPDSIScatter.py` | Older (Sep 30) PDSI scatter — separate from `PlotPDSIVsYield.py`. | ARCHIVE unless used. |
| `scripts/Plotting/PlotDroughtIndicesPerDistrict.py` | Aug-22 PDSI/PHDI/PMDI line plots per district. Uses legacy `maryland_nass_data_cleaned_with_district.csv`. | ARCHIVE. |
| `scripts/Plotting/PlotPrecipitationPerDistrict.py` | Aug-22 precip per district. Superseded by `PlotDistrictPrecipitation*.py` family. | ARCHIVE. |
| `scripts/Plotting/PlotETData.py` | ET visualizations. ET is not in the paper. | ARCHIVE. |
| `scripts/Plotting/Regional_NDRE_Analysis.py` | NDRE per district. NDRE is not in the paper (paper uses NDVI + NDWI). | ARCHIVE. |
| `scripts/Plotting/Regional_NDVI_Analysis.py` | Older NDVI per district (uses legacy `maryland_only_soybean_ndvi_timeseries_FINAL.csv`). Superseded by `Longitudinal_10Day_Index_Analysis.py`. | ARCHIVE. |
| `scripts/Plotting/Statewide_Drought_Analysis.py` | Granger causality + cross-correlation between precip and Palmer indices, statewide. Documented partially. | KEEP AS-IS or REWRITE (depending on whether any of its outputs appear in the paper SI). |
| `scripts/Plotting/MapSoilCompositionBand5.py` | (Already listed above as canonical.) | — |
| `scripts/Plotting/__pycache__/` | Build artifact. | DELETE. |

---

## G. `scripts/PlotNDWI/` — Specialized NDWI scripts

| Path | Purpose | Category |
|---|---|---|
| `scripts/PlotNDWI/PreprocessNDWI.py` | Combines per-decade NDWI CSVs from `data/ndwi_ten_day_interval/` into `data/maryland_ndwi_10day_final_imputed.csv`. **Predecessor to `Preprocess_MD_Soybean_10Day.py`**, which includes both NDVI+NDWI and is now the canonical 10-day file. The `PlotIntervalNDWI.py` figures still depend on `maryland_ndwi_10day_final_imputed.csv`. | KEEP / RENAME → `analysis/preprocessing/preprocess_ndwi_10day_legacy.py`. Or merge with the canonical 10-day preprocessor (REWRITE). My recommendation: **REWRITE** to point at the canonical 10-day file produced by the merged GEE pipeline. |
| `scripts/PlotNDWI/PlotIntervalNDWI.py` | 106 KB NDWI water-stress vs yield analysis. Documented at top with research-derived 0.1325 stress threshold. | KEEP / RENAME → `analysis/figures/`. Possibly **REWRITE** because it relies on `data/maryland_ndwi_10day_final_imputed.csv` (legacy NDWI-only file) instead of the canonical NDVI+NDWI long file. Verify scientific equivalence before relocating. |
| `scripts/PlotNDWI/PlotBusinessPatterns.py` | 70 KB business-patterns + NDWI integration. BP not in paper. | ARCHIVE. |
| `scripts/PlotNDWI/PlotMonthlyNDWI.py` | Monthly NDWI by district plots. | KEEP AS-IS or ARCHIVE depending on whether any paper figure derives from it. The newer Apr-24 `Plotting/` pipeline supersedes most of this. | 
| `scripts/PlotNDWI/PlotNDWIWaterStatistics.py` | NDWI vs PDSI / precip correlations. Likely superseded by `Longitudinal_10Day_Index_Analysis.py` (which does the same correlations, plus more, with documentation). | ARCHIVE. |
| `scripts/PlotNDWI/PlotYieldNDWITimeSeries.py` | Yield + NDWI time-series by district. Likely superseded by newer scripts. | ARCHIVE. |
| `scripts/PlotNDWI/__pycache__/` | Build artifact. | DELETE. |

---

## H. `scripts/CombineDroughtPrecipitationData/` — drought/precip CSV stitching

| Path | Purpose | Category |
|---|---|---|
| `scripts/CombineDroughtPrecipitationData/CombinePDSIData.py` | Reads `data/pdsi/*.csv`, pivots to wide, writes `data/maryland_pdsi_combined_wide.csv`. | REWRITE. See note below. |
| `scripts/CombineDroughtPrecipitationData/CombinePHDIData.py` | Same script with `pdsi`→`phdi` and `PDSI_`→`PHDI_`. **Diff is 3 lines.** | REWRITE — collapse into one. |
| `scripts/CombineDroughtPrecipitationData/CombinePMDIData.py` | Same script with `pdsi`→`pmdi`. **Diff is 3 lines.** | REWRITE — collapse into one. |
| `scripts/CombineDroughtPrecipitationData/CombinePrecipitationData.py` | Different (slightly): handles file-name → county-name mapping and skips 3 rows of NCEI header. | REWRITE — keep separate from PDSI/PHDI/PMDI but unify with shared helper. |

Recommendation: rewrite into a single `analysis/preprocessing/combine_climate_wide.py` with `--index pdsi|phdi|pmdi|precip` flag. Numerical behavior preserved (3 PDSI/PHDI/PMDI scripts are arithmetic-identical except for names; the precip variant has a different reader that we keep). **Note:** this duplicates work that `PreprocessDroughtData.py` does for monthly+aggregated PDSI/PHDI/PMDI — but the wide-format outputs feed many downstream scripts, so we keep both pipelines.

---

## I. `scripts/CreateNDRE/` — NDRE preprocessing

| Path | Purpose | Category |
|---|---|---|
| `scripts/CreateNDRE/CombineNDRE.py` | Reads `data/ndre/*.csv` → `data/maryland_soybean_ndre_timeseries_combined_wide.csv`. | ARCHIVE — NDRE not in paper. |
| `scripts/CreateNDRE/PreprocessNDRE.py` | Filters combined NDRE to MD-only counties → `data/maryland_only_ndre_timeseries_FINAL.csv`. | ARCHIVE. |

---

## J. `scripts/NASSPlotting/`

| Path | Purpose | Category |
|---|---|---|
| `scripts/NASSPlotting/CombineNassData.py` | Joins yield/planted/harvested/production/irrigated NASS CSVs into `data/maryland_nass_data_cleaned_with_district.csv`. **Canonical legacy file** — many other scripts read it. | KEEP / RENAME → `analysis/preprocessing/combine_nass_metrics.py`. May want REWRITE: the script reads files directly from `data/`, not `data/nass/`, which is inconsistent with how the rest of the repo organizes NASS data. |
| `scripts/NASSPlotting/DeriveNassInsights.py` | Plots from the cleaned NASS file (acres planted vs harvested over time, etc.). Generates several figures in `outputs/NASSData/`. | KEEP AS-IS (lightly REWRITE for path consistency). |

---

## K. `scripts/YieldAnalysis/`

| Path | Purpose | Category |
|---|---|---|
| `scripts/YieldAnalysis/PlotYieldTimeSeries.py` | 26 KB. Time-series yield plots by county within district (2014–2024). Sep-28 timestamp. Possibly superseded by newer `StudyArea_*` and `CountyDistrict_Yield_Heatmaps.py`. | KEEP AS-IS or ARCHIVE depending on use. |

---

## L. `outputs/`

The user's manuscript's final 10 figures live in
`outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure01.png` … `Figure10.png`.
Everything else under `outputs/` is intermediate / exploratory artifacts or
non-final figures.

For Phase 2 / 3 I propose:

- Keep `outputs/` outside the source tree as you have it.
- Add `outputs/` to `.gitignore` for the public release **except** for
  `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/` (which we'd rename to
  `figures/` or `outputs/manuscript_figures/`).
- Add a `MANIFEST.md` that maps each script → which output paths it writes.

Concrete `outputs/` subfolders by relevance:

| Subdir | Status |
|---|---|
| `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure01..10.png` | KEEP AS-IS — final figures. |
| `outputs/StressDrivers/` | KEEP AS-IS — Differential / Longitudinal analyses + scissors plots write here. |
| `outputs/IndexStressAnalysis/`, `outputs/DifferentialStressAnalysis/` | KEEP AS-IS — primary analytical outputs. |
| `outputs/DroughtEffect/`, `outputs/IrrigationVsDroughtYield/`, `outputs/FlashDrought/` | KEEP AS-IS — paper-supporting analytics. |
| `outputs/YieldAnalysis/StudyArea/`, `outputs/Irrigation/`, `outputs/SoilCompositionBand5/`, `outputs/NationalVsMaryland/` | KEEP AS-IS. |
| `outputs/BusinessPatterns/`, `outputs/ET/`, `outputs/NDRE/`, `outputs/IntervalNDWI/`, `outputs/MonthlyNDWI/`, `outputs/NDVI/`, `outputs/NDWI/`, `outputs/NDWIByAgriculturalDistrict/`, `outputs/NDWIWaterStatistics/`, `outputs/DroughtIndices/`, `outputs/Precipitation/`, `outputs/SoilComposition/`, `outputs/NASSData/`, `outputs/YieldNDWITimeSeries/`, `outputs/IrrigationVsDroughtYield/` | Outputs of pipelines — keep PNGs that document figure-choice provenance, but don't track all of them in git. |

---

## M. `data/`

Currently `data/` is git-ignored (good). The local working copy contains:

- Raw inputs (NASS CSVs, NCEI county PDSI/PHDI/PMDI, NOAA precip,
  GEE-exported NDWI/NDVI/NDRE/ET CSVs, business patterns CSVs, raw 10-day
  GEE export CSVs in `data/MD_SOYBEAN_10DAY/`, soil composition CSVs).
- Processed outputs from the preprocessing scripts.
- A few `.DS_Store` files and miscellaneous files like `CENSUS_NASS_IRRIGATION.md` (a useful inventory of the NASS irrigation files — keep with the data, or move to `docs/`).

Recommendation:

- Keep `data/` git-ignored.
- Document in the README how a user obtains each raw dataset and where to put it. The `CENSUS_NASS_IRRIGATION.md` is good prior art for that.
- We can add a `data/README.md` that lists expected directory tree + dataset sources (which is half of what Phase 4 README will cover anyway).

---

## N. Duplicates and near-duplicates (to consolidate in Phase 3)

1. **`CombinePDSIData.py` ≈ `CombinePHDIData.py` ≈ `CombinePMDIData.py`**
   — 3-line difference each (folder name + output file name + column prefix).
   Merge into one parameterized script.

2. **`PreprocessSoilData.py` vs `PreprocessSoilData_Band5.py`**
   — same logic, different input file paths and tab-vs-space indentation.
   Merge into one script with a CLI flag.

3. **`PlotSoilComposition.py` vs `PlotSoilComposition_Band5.py`**
   — older (full-soybean) and newer (band-5) plotting variants. The Band-5 one is canonical (paper). Archive the old.

4. **`CompareNationalVsMaryland.py` vs `CompareNationalVsMaryland_AcreageYield.py`**
   — older 24 KB version and newer 5 KB tighter version. Archive the old.

5. **`StudyArea_*` family** — `StudyArea_YieldOptions.py`, `StudyArea_YieldGapFigures.py`, `StudyArea_Option2_Variations.py`, `StudyArea_Option2_Enhanced.py`, `StudyArea_Options3_4.py`. Per filename, only the "Enhanced" + "Options3_4" appear to be the published variants. Archive the precursors.

6. **`Preprocess_MD_Soybean_10Day.py` (NDVI+NDWI long+wide+wide-imputed) vs `PlotNDWI/PreprocessNDWI.py` (NDWI-only, different decade-naming source data, also writes a similar wide-imputed file)**
   — these read different source folders (`data/MD_SOYBEAN_10DAY/` vs `data/ndwi_ten_day_interval/`). Both produce a "10-day NDWI" canonical file. They may not be redundant if they were used at different stages of the project, but the current repo only needs the unified one. Confirmed: `PlotIntervalNDWI.py` (one of the canonical figure scripts) reads the OLD one (`maryland_ndwi_10day_final_imputed.csv`). **Confirm with the author whether Figure-X uses the NDWI-only file or the NDVI+NDWI canonical.**

7. **`CreateNDVI/Export_MD_Monthly_NDVI.ipynb` vs `CreateNDRE/CombineNDRE.py + PreprocessNDRE.py`**
   — same shape, NDRE has a Python pipeline; NDVI only has the Colab notebook. Either replicate the NDVI pipeline in Python (small, ~30 lines), or archive the notebook + acknowledge that the canonical 10-day pipeline (Sentinel-2 GEE → 10-day CSV → `Preprocess_MD_Soybean_10Day.py`) is the actual NDVI source for the paper.

---

## O. Inter-file Python dependency graph

I checked every `.py` in `scripts/` for `from scripts.*` / `import scripts.*` /
relative imports. **No script imports any other script** — they all read CSVs
from `data/` and write CSVs / PNGs to `outputs/`. This makes the reorg easy:
no Python import paths to update; just file moves + path-string updates inside
each script.

There is, however, a strong **data-file dependency graph**. Summarized:

```
GEE_Scripts (.js, manual)
       │  (per-month, per-year CSVs exported to Drive)
       ▼
data/MD_SOYBEAN_10DAY/MD_Soybean_10Day_TimeSeries_YYYY.csv
       ▼
Preprocess_MD_Soybean_10Day.py
       ▼
data/maryland_soybean_10day_timeseries_long.csv  (and wide, wide_imputed)
       │
       ├── Differential_Stress_Analysis.py
       ├── Longitudinal_10Day_Index_Analysis.py
       ├── District_DroughtPrecip_Impact_On_Indices.py
       ├── PlotNDVI_NDWI_Scissors.py / _DualAxis.py
       ├── PlotNDWI_R4R6_ByDistrict_Boxplot.py
       └── NDWI_R4R6_TwoSample_TTests.py

data/Precipitation_Data_NOAA_97-25/*.csv
       ▼ CombinePrecipitationData.py
data/maryland_precipitation_combined_wide.csv
       ├── PlotDistrictPrecipitationTrends.py
       ├── PlotDistrictPrecipitationDecadeOverlay.py
       ├── PlotDistrictPrecipitationClimatology.py
       ├── PlotPrecipVsYield.py
       └── (Differential / Longitudinal / DroughtPrecip indirectly)

data/drought_data_1997-2025/{pdsi_county,phdi_county,pmdi_county}/*.csv
       ▼ PreprocessDroughtData.py            ▼ Combine{PDSI,PHDI,PMDI}Data.py
data/processed_drought/*.csv                  data/maryland_{pdsi,phdi,pmdi}_combined_wide.csv
       ├── DetectFlashDroughts.py             ├── Differential_Stress_Analysis.py
       ├── AnalyzeDroughtResistance.py        ├── Longitudinal_10Day_Index_Analysis.py
       ├── AnalyzeIrrigationDroughtYield.py   ├── District_DroughtPrecip_Impact_On_Indices.py
       └── AnalyzeYieldVsDrought.py           ├── PlotPDSIVsYield.py / PlotPDSIScatter.py
                                              └── Statewide_Drought_Analysis.py

data/nass/YieldBu:Acre97to25.csv
       ▼ PreprocessYieldData.py
data/processed_yield/*.csv
       ├── (nearly every analysis + plot script)
       └── …

data/nass/IrrigatedAcresHarvestedByCounty.csv + IrrigationvsNonirrigated.csv
       ▼ BuildCensusIrrigationDataset.py
data/census_nass_irrigation_all.csv
       ├── PlotIrrigatedAcres*.py
       ├── AnalyzeIrrigation*.py
       └── AnalyzeIrrigationDroughtYield.py

data/soybeanSoilCompositionPerCounty(2018|2020)band5.csv
       ▼ PreprocessSoilData_Band5.py
data/processed_band5/*.csv
       ├── PlotSoilComposition_Band5.py
       ├── SoilCompositionBand5_CountyDistrictHeatmap.py
       ├── MapSoilCompositionBand5.py
       └── AnalyzeIrrigationSoilComposition.py
```

---

## P. Python dependency requirements gaps (to fix in Phase 4)

`requirements.txt` is missing direct dependencies actually imported by tracked scripts:

- `seaborn` (used in 30+ scripts)
- `scipy` (`scipy.stats` used in 14 scripts)
- `statsmodels` (used in `Statewide_Drought_Analysis.py`)
- `ipython` / `IPython.display` (used in 16 scripts; we can drop most of these as dead imports during REWRITE since `display(...)` only matters in notebooks)

Also: nothing pins a Python version. Phase 4 README should specify a version.

---

## Q. Per-phase TODO / flags raised in Phase 1

Things I noticed but did **not** change. To be addressed (or explicitly punted) in Phase 3 or by you.

1. **Path inconsistency in `scripts/NASSPlotting/CombineNassData.py`**: it reads NASS files from `data/`, not `data/nass/`. Other scripts use `data/nass/`. Likely an artifact of an older repo layout. Phase 3 path-tidy will fix this.
2. **Legacy `data/maryland_ndwi_combined_wide.csv` is referenced** by `PlotNDWIByDistrict.py` and `PlotSoilandNDWI.py`, but no script in the repo writes that file. It looks like it was hand-built from a Colab pipeline parallel to `Export_MD_Monthly_NDVI.ipynb` that wasn't checked in. Both readers are slated for ARCHIVE so this dangling reference becomes harmless.
3. **`Preprocess_MD_Soybean_10Day.py` says it writes "20" canonical years (2008–2024)** but the `Preprocess_MD_Soybean_10Day.py` script header says it imputes via `ffill().bfill()` along the time axis per county. That imputation is non-trivial scientifically (fills missing decadal observations with neighboring values). Already disclosed in the docstring; no action.
4. **`PlotIntervalNDWI.py` (PlotNDWI/) hard-codes a stress threshold of 0.1325** (mean of 0.121 and 0.144 from a Braga et al. reference). The same threshold appears as 0.121 lower bound in `NDWI_R4R6_TwoSample_TTests.py` and as 0.12 in the dual-axis scissors plot. **Inconsistent representation of the same scientific threshold.** Flagging — not changing — per your "do not silently change a numerical constant" rule.
5. **`Differential_Stress_Analysis.py`** uses 20th and 60th percentile thresholds for the NDVI plateau definition. Documented; not changed.
6. **`DroughtEffectFigureOptions.py`** generates 5 alternative figures (A–E) — only OptionD seems to make it into the manuscript per `outputs/Manuscript_Figures_Sriram_Kumar_IB_HK/Figure07.png`-ish. Confirm before archiving non-final variants.
7. **Empty / synthetic outputs** to clean up under `outputs/`: I see several PNGs that are 15 KB and have identical sizes (`outputs/DroughtIndices/County_Heatmaps_Precip_PDSI.png`, `District_*` etc. all 15127 bytes) — these may be empty/blank figures. Worth a quick look to confirm.
8. **`scripts/Plotting/Statewide_Drought_Analysis.py`** uses `from statsmodels.tsa.stattools import grangercausalitytests` and `ccf`. Whether the Granger output ends up in the paper drives whether we ARCHIVE or KEEP. You'll want to flag.

---

## Summary counts

- Total tracked Python files: **57**
- KEEP AS-IS: ~25
- KEEP / RENAME (move + add header): ~10
- REWRITE (clean up paths, add docstring, dedupe): ~9
- ARCHIVE: ~14
- DELETE (build artifacts only): the `__pycache__` folders and `.DS_Store` files; no Python source files marked DELETE.

I'm ready to discuss any of the above before drafting Phase 2.
