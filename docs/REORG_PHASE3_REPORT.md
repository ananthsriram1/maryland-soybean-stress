# Phase 3 reorg — progress report (checkpoint: preprocessing tier complete)

## Preprocessing tier — status: **handed off**

**Scope (this checkpoint):** `analysis/preprocessing/` — combine + preprocess scripts, docstrings, NASS path fix, `__main__` guards, soil docstring accuracy.

**Policy note (reframed, 2026-04-25):** Public repo targets reproducibility and clear pipelines for a researcher audience, not bit-for-bit audits unless explicitly requested. Logic-preserving refactors are acceptable even when outputs are not byte-identical to a prior run.

---

## What landed

- **File moves (8):** See Phase 2 proposal; sources under `scripts/` are now in `analysis/preprocessing/` with the agreed names (`preprocess_10day_indices`, `preprocess_soybean_yield`, `preprocess_corn_yield`, `preprocess_palmer_indices`, `preprocess_soil_composition`, `preprocess_irrigation_census`, `combine_precipitation`, `combine_nass_metrics`), plus `combine_palmer_index` consolidation and Palmer legacy scripts in `archive/combine_drought_legacy/`, non-Band5 soil preprocessor in `archive/soil_legacy/`.
- **Canonical data at `data/`:** `maryland_precipitation_combined_wide.csv` and `maryland_nass_data_cleaned_with_district.csv` are accepted as the current canonical outputs (regenerated during an import smoke test before guards existed). A defensive snapshot of the post-regeneration state remains under `/tmp/reorg_backup/post_overwrite_2130/` for the author’s use only, not a rollback target.
- **`if __name__ == "__main__":` execution-on-import fix:**
  - **`combine_precipitation.py`** — top-level execution moved into `main()`; module keeps `precip_folder_path` and `output_file` constants.
  - **`combine_nass_metrics.py`** — top-level execution moved into `main()`; `clean_nass_csv` and path constants remain at module level.
- **`preprocess_soil_composition.py` docstring** — inputs now name the files the code actually reads (`data/soybeanSoilCompositionPerCounty2018band5.csv`, `data/soybeanSoilCompositionPerCounty2020band5.csv`); GEE export / not-in-repo note and Phase 4 README TODO embedded in the docstring.

---

## Audit: unguarded execution on import (item 1.7)

| Module | Pattern |
|--------|---------|
| `combine_palmer_index.py` | **Already** `if __name__ == "__main__": main()` |
| `preprocess_10day_indices.py` | **Already** guarded |
| `preprocess_soybean_yield.py` | **Already** guarded |
| `preprocess_corn_yield.py` | **Already** guarded |
| `preprocess_palmer_indices.py` | **Already** guarded |
| `preprocess_soil_composition.py` | **Already** guarded |
| `preprocess_irrigation_census.py` | **Already** guarded |
| `combine_precipitation.py` | **Fixed in this checkpoint** (was unguarded) |
| `combine_nass_metrics.py` | **Fixed in this checkpoint** (was unguarded) |

**Summary:** Only **two** of the 11 preprocessing modules ran pipeline code at import time; both are now guarded. The other **nine** already used `if __name__ == "__main__"`.

**Going forward:** Before import-based smoke checks in `stress_analysis` and `figures` tiers, snapshot `shasum -a 256` (or at least `ls -la`) for any on-disk outputs a module might write if it were unguarded — so we have a pre-import baseline even for untracked data files.

---

## Smoke check (post-guard)

- `python3 -c "import importlib; importlib.import_module('analysis.preprocessing.<mod>')"` for all 11 modules: **no I/O on import** (no accidental CSV rewrite).

---

## Phase 3 final TODO list (rolling — will grow through figures/archive tiers)

### A. Threshold drift (0.121 / 0.1325 / 0.12 family)

Reconcile by hand; do not silently normalize. **Sample of current occurrences** (repo-wide `*.py` grep; not exhaustive of every literal):

| Path | Note |
|------|------|
| `scripts/Plotting/PlotNDVI_NDWI_Scissors.py` | `NDWI_STRESS = 0.12` (vs 0.121/0.144 band elsewhere) |
| `scripts/Plotting/PlotNDVI_NDWI_Scissors_DualAxis.py` | `NDWI_STRESS_LO, NDWI_STRESS_HI = 0.121, 0.144` |
| `scripts/PlotNDWI/PlotIntervalNDWI.py` | `stress_threshold = 0.1325` (and related text) |
| `scripts/PlotNDWI/PlotNDWIWaterStatistics.py`, `PlotYieldNDWITimeSeries.py`, `PlotMonthlyNDWI.py` | `0.1325` threshold lines |
| (Other) | `DroughtEffectFigureOptions.py` padding `* 0.12`; `StudyArea_YieldOptions.py` width `0.12` — **verify** these are layout/styling, not NDWI science |

*Full pass at end of Phase 3 with file:line:value table.*

### B. `IPython.display` removals (for confirmation: non–load-bearing)

| Location | Note |
|----------|------|
| `analysis/preprocessing/combine_palmer_index.py` (consolidation) | `display` dropped vs legacy |
| `analysis/preprocessing/combine_nass_metrics.py` | `from IPython.display import display` and `display(...)` → `print(...)` |
| *Rest of repo* | To be listed as remaining files are REWRITE’d |

*Current state:* **No** `IPython` / `display(` in `analysis/preprocessing/`.

### C. Figure 2 variant

- **TODO:** confirm which `outputs/SoilCompositionBand5/variants/` PNG matches `Figure02.png` (placeholder in figure manifest until byte-match).

### D. GEE / external inputs documentation

- **TODO:** `preprocess_soil_composition.py` reads GEE-exported Band-5 soil CSVs that are **not** in the repository. Phase 4 `GEE_Scripts/README.md` (or data README) should name the **specific** GEE script(s) that produce `soybeanSoilCompositionPerCounty*band5.csv`.

### E. Prose references to old `scripts/` paths (cosmetic, figures tier may supersede)

- `analysis/preprocessing/preprocess_corn_yield.py` — line ~5: update “Mirrors `scripts/PreprocessYieldData.py`” → point at `analysis/preprocessing/preprocess_soybean_yield.py`.
- `analysis/preprocessing/preprocess_10day_indices.py` — line ~53: update or remove “Mirrors … `scripts/PlotNDWI/PreprocessNDWI.py`” after `PreprocessNDWI` lands in `archive/` or new path (or remove if script is retired).

### F. Differential stress analysis

- 20th/60th percentile thresholds: **documented design** — leave as-is; no silent edits.

### G. Other (from earlier phases)

- NASS `data/` vs `data/nass/` input asymmetry: **intentional**; output pinned to `data/maryland_nass_data_cleaned_with_district.csv` (see comment in `combine_nass_metrics.py`).

---

## Deviations from earlier Phase 3 byte-match gate

- Per author direction 2026-04-25: **no** mandatory SHA256 match for the two regenerated combined CSVs before closing the tier; import guards and logic-unchanged refactor are sufficient for this public-repro context.

---

## Next step (historical)

Figures tier and archive sweep were completed after this checkpoint; see sections below.

---

# Phase 3 reorg — progress report (checkpoint: stress_analysis tier complete)

## Stress_analysis tier — status: **handed off**

**Scope (this checkpoint):** `analysis/stress_analysis/` — move canonical statistical-engine scripts from `scripts/Analysis/` into the package; verify `__main__` guards; verify clean imports; snapshot SHA256 of key inputs before imports.

### What landed (KEEP/RENAME moves)

Moved (via `mv`, because these files were untracked in git at the time of move):

- `scripts/Analysis/DetectFlashDroughts.py` → `analysis/stress_analysis/detect_flash_droughts.py`
- `scripts/Analysis/Differential_Stress_Analysis.py` → `analysis/stress_analysis/differential_stress_analysis.py`
- `scripts/Analysis/AnalyzeYieldVsDrought.py` → `analysis/stress_analysis/analyze_yield_vs_drought.py`
- `scripts/Analysis/AnalyzeIrrigationDroughtYield.py` → `analysis/stress_analysis/analyze_irrigation_drought_yield.py`
- `scripts/Analysis/AnalyzeDroughtResistance.py` → `analysis/stress_analysis/analyze_drought_resistance.py`
- `scripts/Analysis/NDWI_R4R6_TwoSample_TTests.py` → `analysis/stress_analysis/ndwi_r4r6_two_sample_ttests.py`
- `scripts/Analysis/PairedTTest_CountyYield_EarlyVsLate.py` → `analysis/stress_analysis/paired_ttest_county_yield_early_vs_late.py`
- `scripts/Analysis/Longitudinal_10Day_Index_Analysis.py` → `analysis/stress_analysis/longitudinal_10day_index_analysis.py`
- `scripts/Analysis/District_Yield_vs_R4R6_Indices.py` → `analysis/stress_analysis/district_yield_vs_r4r6_indices.py`
- `scripts/Analysis/District_DroughtPrecip_Impact_On_Indices.py` → `analysis/stress_analysis/district_droughtprecip_impact_on_indices.py`

`scripts/Analysis/DroughtEffectFigureOptions.py` was a **byte-identical duplicate** of `archive/figure_drafts/DroughtEffectFigureOptions.py` and was **removed** during the Phase 3 archive sweep (canonical OptionD-only generator lives in `analysis/figures/figure06_drought_class_yield_boxplots.py`).

### Package skeleton

- Added `analysis/stress_analysis/__init__.py`.

### `__main__` guard audit

All moved stress-analysis scripts already had `if __name__ == "__main__":` guards; no new guards were required in this tier.

### Smoke check (imports)

- All modules under `analysis.stress_analysis.*` import cleanly with no execution / no I/O on import.

### SHA256 snapshots (exists-only; prior to any execution)

Captured SHA256 for key inputs likely to be consumed by stress-analysis modules:

- `data/maryland_precipitation_combined_wide.csv` (6cd6a04c…)
- `data/maryland_nass_data_cleaned_with_district.csv` (eda2648a…)
- `data/maryland_soybean_10day_timeseries_long.csv` (c966b327…)
- `data/processed_yield/yield_clean_long_format.csv` (b31922eb…)
- `data/processed_drought/drought_monthly_county.csv` (200b3640…)
- `data/processed_drought/drought_aggregates_county_year.csv` (f0c93c00…)
- `data/processed_drought/drought_aggregates_district_year.csv` (1e3c4ce5…)
- `data/maryland_pdsi_combined_wide.csv` (8516f915…)
- `data/maryland_phdi_combined_wide.csv` (ec64c1a1…)

---

## Phase 3 final TODO list — additions from stress_analysis tier

### H. Statistical thresholds / design constants (do not silently change)

Surface for manual review (no changes made):

- `analysis/stress_analysis/differential_stress_analysis.py`
  - Plateau thresholds: `quantile(0.20)` / `quantile(0.60)` (documented design choice; keep untouched).
  - Permutation test shuffles: `n_perm=10_000` (keep untouched unless explicitly revisited).
- `analysis/stress_analysis/district_droughtprecip_impact_on_indices.py`
  - Quantile bins for precip categories: 25th / 75th percentile (`quantile(0.25)`, `quantile(0.75)`).
- `analysis/stress_analysis/ndwi_r4r6_two_sample_ttests.py`
  - Uses `scipy.stats` for Welch t-tests + ANOVA + Kruskal–Wallis; treat these as design choices (no silent edits).

### I. Prose / pointer accuracy (minor)

- Updated outdated internal messages that referenced `scripts/PreprocessDroughtData.py` or `scripts/Preprocess_MD_Soybean_10Day.py` to point at the new `analysis/preprocessing/*` locations.

### J. Repo-root manuscript artifacts / working notes

- **Archive sweep (2026-04-26):** `abstract` → `archive/abstract_builder.py`; `analysis.txt` and `irrigation_speaker_notes.md` → `archive/notes/`; `Abstract_Submission.docx` and `Manuscript_Sriram_Kumar_IB_HK.docx - Google Docs.pdf` (renamed to `Manuscript_Sriram_Kumar_IB_HK.pdf`) → `archive/manuscript/`.
- **Phase 4 still TODO:** `.gitignore` rules for these artifact classes, `archive/manuscript/README.md` with published-DOI pointer, and any Zenodo packaging decisions.

---

# Phase 3 — **canonical record** (figures tier + archive sweep complete)

**Status:** Phase 3 is **complete** as of 2026-04-26. Subsequent reorg work is Phase 4 (public-release packaging) unless explicitly reopened.

## Figures tier — status: **accepted**

**Scope:** `analysis/figures/` — manuscript Figures 1–10 generators, orchestrator `regenerate_manuscript_figures.py`, baseline JSON `docs/manuscript_figures_baseline.json`, side-by-side review tiles under `outputs/manuscript_figures/_comparison/`.

**Author visual review:** All nine comparison figures (Figures 01, 03–10 plus Figure 02 placeholder comparison) show **cosmetic drift only**; no substantive scientific differences. Figure 6 categorical colors + correlation annotations were restored where Matplotlib’s boxplot API had previously dropped per-class facecolors.

**Canonical outputs:** Individual generators write **descriptive** paths under `outputs/`; the orchestrator copies to `outputs/manuscript_figures/FigureNN.png`. Figure 2 remains a **documented placeholder** (Variant_06 stand-in) pending manual variant identification.

**Archived dependencies still invoked by wrappers:** `analysis/figures/figure03_district_precip_decade_overlay.py` loads `archive/figure_drafts/PlotDistrictPrecipitationClimatology.py`; `analysis/figures/figure04_study_area_map.py` loads `archive/figure_drafts/StudyArea_Option2_Variations.py` (variation 3, faceted kg/ha). These paths were updated when the sources left `scripts/Plotting/`.

**Manifest:** `analysis/figures/regenerate_manuscript_figures.py` (`FIGURE_MANIFEST`) and `docs/manuscript_figures_baseline.json` are the machine-readable figure↔script↔output map.

---

## Archive sweep — status: **complete** (2026-04-26)

Executed `REORG_PHASE2_PROPOSAL.md` §4.D **ARCHIVE** moves. Every row is **`source` → `target`** (repo-root relative).

### `archive/figure_drafts/` (21 moves; plus duplicate removal)

| Source | Target |
|--------|--------|
| `scripts/Plotting/ComprehensiveYieldPlots.py` | `archive/figure_drafts/ComprehensiveYieldPlots.py` |
| `scripts/Plotting/AnalyzeIrrigation.py` | `archive/figure_drafts/AnalyzeIrrigation.py` |
| `scripts/Plotting/Statewide_Drought_Analysis.py` | `archive/figure_drafts/Statewide_Drought_Analysis.py` |
| `scripts/Plotting/SoilCompositionBand5_CountyDistrictHeatmap.py` | `archive/figure_drafts/SoilCompositionBand5_CountyDistrictHeatmap.py` |
| `scripts/Plotting/PlotDistrictPrecipitationClimatology.py` | `archive/figure_drafts/PlotDistrictPrecipitationClimatology.py` |
| `scripts/Plotting/PlotSoilComposition_Band5.py` | `archive/figure_drafts/PlotSoilComposition_Band5.py` |
| `scripts/PlotNDWI/PlotIntervalNDWI.py` | `archive/figure_drafts/PlotIntervalNDWI.py` |
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
| `scripts/Plotting/PlotSoilComposition.py` | `archive/figure_drafts/PlotSoilComposition.py` |

*(Pre-existing in this folder: `archive/figure_drafts/DroughtEffectFigureOptions.py` — full A–E generator; `scripts/Analysis/DroughtEffectFigureOptions.py` removed as duplicate.)*

### `archive/exploratory/` (4 files)

| Source | Target |
|--------|--------|
| `scripts/PlotNDWIByDistrict.py` | `archive/exploratory/PlotNDWIByDistrict.py` |
| `scripts/PlotSoilandNDWI.py` | `archive/exploratory/PlotSoilandNDWI.py` |
| `scripts/SoilData.py` | `archive/exploratory/SoilData.py` |
| `scripts/CombineETData.py` | `archive/exploratory/CombineETData.py` |

### `archive/plotndwi_legacy/` (5 files)

| Source | Target |
|--------|--------|
| `scripts/PlotNDWI/PreprocessNDWI.py` | `archive/plotndwi_legacy/PreprocessNDWI.py` |
| `scripts/PlotNDWI/PlotMonthlyNDWI.py` | `archive/plotndwi_legacy/PlotMonthlyNDWI.py` |
| `scripts/PlotNDWI/PlotNDWIWaterStatistics.py` | `archive/plotndwi_legacy/PlotNDWIWaterStatistics.py` |
| `scripts/PlotNDWI/PlotYieldNDWITimeSeries.py` | `archive/plotndwi_legacy/PlotYieldNDWITimeSeries.py` |
| `scripts/PlotNDWI/PlotBusinessPatterns.py` | `archive/plotndwi_legacy/PlotBusinessPatterns.py` |

### `archive/ndre_pipeline/` (2 files)

| Source | Target |
|--------|--------|
| `scripts/CreateNDRE/CombineNDRE.py` | `archive/ndre_pipeline/CombineNDRE.py` |
| `scripts/CreateNDRE/PreprocessNDRE.py` | `archive/ndre_pipeline/PreprocessNDRE.py` |

### `archive/economic_context/` (1 file)

| Source | Target |
|--------|--------|
| `scripts/PreprocessBusinessPatterns.py` | `archive/economic_context/PreprocessBusinessPatterns.py` |

### `archive/notebooks/` (1 file)

| Source | Target |
|--------|--------|
| `scripts/CreateNDVI/Export_MD_Monthly_NDVI.ipynb` | `archive/notebooks/Export_MD_Monthly_NDVI.ipynb` |

### `archive/notes/` + `archive/manuscript/` + root script rename

| Source | Target |
|--------|--------|
| `analysis.txt` | `archive/notes/analysis.txt` |
| `irrigation_speaker_notes.md` | `archive/notes/irrigation_speaker_notes.md` |
| `abstract` | `archive/abstract_builder.py` |
| `Abstract_Submission.docx` | `archive/manuscript/Abstract_Submission.docx` |
| `Manuscript_Sriram_Kumar_IB_HK.docx - Google Docs.pdf` | `archive/manuscript/Manuscript_Sriram_Kumar_IB_HK.pdf` |

### Not moved (absent on disk)

- **`outputs/DroughtIndices/` 15,127-byte error PNGs** → `archive/outputs_archive/DroughtIndices_15kb_errors/`: paths from Phase 2 were not present in this working tree; directory `archive/outputs_archive/DroughtIndices_15kb_errors/` was created for a future copy if those files reappear.

### `scripts/` after sweep (**not empty** — flagged for Phase 4 / later migration)

The following **16** files remain under `scripts/` (canonical GEE + plotting helpers **not** classified as ARCHIVE in Phase 2; they were slated for `analysis/figures/supporting/` in the proposal but that migration was **out of scope** for this sweep):

- `scripts/CreateNDVI/Monthly_NDVI_Soybean.js`
- `scripts/GEE_Scripts/NDWI_Extraction`
- `scripts/GEE_Scripts/10_Day_NDVI_Reduction`
- `scripts/GEE_Scripts/10_Day_NDVI_Reduction_PRE2017`
- `scripts/NASSPlotting/DeriveNassInsights.py`
- `scripts/Plotting/AnalyzeIrrigationSoilComposition.py`
- `scripts/Plotting/CompareCountyAndDistrictVsNational.py`
- `scripts/Plotting/CompareNationalVsMaryland_AcreageYield.py`
- `scripts/Plotting/CountyDistrict_Yield_Heatmaps.py`
- `scripts/Plotting/MapSoilCompositionBand5.py`
- `scripts/Plotting/PlotDistrictPrecipitationTrends.py`
- `scripts/Plotting/PlotIrrigatedAcres.py`
- `scripts/Plotting/PlotNDVI_NDWI_Scissors.py`
- `scripts/Plotting/PlotPDSIVsYield.py`
- `scripts/Plotting/PlotPrecipVsYield.py`
- `scripts/Plotting/StudyArea_Options3_4.py`

**Recommendation:** Phase 4 or a small “Phase 3.5” PR moves these into `analysis/figures/supporting/` (and relocates `GEE_Scripts/` per Phase 2 §4.A) so `scripts/` can shrink to empty or near-empty.

---

## Outstanding TODOs (carry forward — **do not resolve here**)

These items are **explicitly deferred** to Phase 4 or manual author review:

1. **Figure 2 variant identification** — which `Variant_*.png` is the published Figure 2; orchestrator placeholder note until then.
2. **Threshold drift census** — full file:line table for `0.121` / `0.1325` / `0.12` / NDWI stress band literals (partial list exists earlier in this report; archived copies under `archive/plotndwi_legacy/` and `archive/figure_drafts/` add paths).
3. **`IPython.display` removals** — remaining legacy scripts under `archive/` may still contain imports; canonical `analysis/` pipeline should stay notebook-free.
4. **Cosmetic `scripts/` references** — docstrings in `analysis/preprocessing/` that still mention old `scripts/` paths; update when supporting scripts migrate.
5. **Repo-root cleanup / `.gitignore`** — Phase 4: ignore patterns for outputs, comparison tiles, manuscript DOCX at root if any reappear, venv, etc.
6. **`scripts/` → `analysis/figures/supporting/` + `GEE_Scripts/` top-level** — structural migration per Phase 2 §1 / §4.A (not executed in this sweep).
7. **`archive/README.md` + per-subfolder README** — provenance blurbs (Phase 4 prose).

---

## Phase 3 sign-off

All planned Phase 3 tiers (**preprocessing**, **stress_analysis**, **figures**, **archive sweep**) are **done**. **Phase 4** begins with a separate inventory/proposal document; execution waits for author sign-off per prior phase policy.
