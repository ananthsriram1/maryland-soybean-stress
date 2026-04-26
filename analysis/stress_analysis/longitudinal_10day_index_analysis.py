#!/usr/bin/env python3
"""
Longitudinal analysis for 10-day NDVI/NDWI soybean time series (2008–2024).

Data inputs (expected in this repo):
  - data/maryland_soybean_10day_timeseries_long.csv
      (created by analysis/preprocessing/preprocess_10day_indices.py)
  - data/maryland_pdsi_combined_wide.csv
  - data/maryland_phdi_combined_wide.csv
  - data/processed_yield/yield_clean_long_format.csv
  - data/maryland_only_soil_water_content_FINAL.csv

Scientific outputs (written to outputs/IndexStressAnalysis):
  1) Index sensitivity (R4–R6 window, DOY 200–260):
     - County-year regression slopes: NDVI~NDWI and NDWI~NDVI + correlations
  2) Drought correlation (PDSI/PHDI vs late-season NDVI/NDWI anomalies; 2012–2024 overlap):
     - Correlation table + scatter plots
  3) Soil resilience attribution (AWC proxy via avg_water_content):
     - Low vs high AWC comparison of NDWI decline during dry years
  4) 2012 drought signature:
     - Statewide NDWI percent drop vs 2008–2024 climatology by 10-day step
  5) Heatmap of Stress:
     - District NDWI monthly anomaly heatmaps (2008–2024)
  6) Critical phenological window:
     - Per-county 30-day (3-interval) window of maximum interannual volatility

Notes:
  - Missing NDVI/NDWI values are imputed using forward-fill/backward-fill along the
    full time axis per county (consistent with analysis/preprocessing/preprocess_10day_indices.py).
  - PDSI/PHDI datasets in this repo begin in 2012, so drought correlations use 2012–2024.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re


OUT_DIR = "outputs/IndexStressAnalysis"

INPUT_INDICES_LONG = "data/maryland_soybean_10day_timeseries_long.csv"
INPUT_PDSI_WIDE = "data/maryland_pdsi_combined_wide.csv"
INPUT_PHDI_WIDE = "data/maryland_phdi_combined_wide.csv"
INPUT_YIELD_LONG = "data/processed_yield/yield_clean_long_format.csv"
INPUT_SOIL = "data/maryland_only_soil_water_content_FINAL.csv"


DISTRICT_ORDER = [
    "WESTERN",
    "NORTH CENTRAL",
    "SOUTHERN",
    "UPPER EASTERN SHORE",
    "LOWER EASTERN SHORE",
]

DISTRICT_COLORS = {
    "WESTERN": "#FFD700",
    "NORTH CENTRAL": "#FF6B6B",
    "SOUTHERN": "#90EE90",
    "UPPER EASTERN SHORE": "#9370DB",
    "LOWER EASTERN SHORE": "#4ECDC4",
}


def ensure_outdir():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "tables"), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "figures"), exist_ok=True)


def _standardize_county(s: str) -> str:
    """Normalize county names to match the indices dataset convention."""
    s = str(s).strip()
    # Normalize case (yield data is often ALL CAPS)
    s = s.title()
    # Fix apostrophe artifacts from .title(): "George'S" -> "George's"
    s = re.sub(r"'S\b", "'s", s)
    # Canonical fixes used across this repo
    s = s.replace("Prince George's", "Prince George's")
    s = s.replace("Queen Anne's", "Queen Anne's")
    s = s.replace("St. Mary's", "St. Mary's")
    return s


def load_indices_long_imputed() -> pd.DataFrame:
    df = pd.read_csv(INPUT_INDICES_LONG, parse_dates=["date"])
    df["County"] = df["County"].map(_standardize_county)
    df["Ag_District"] = df["Ag_District"].astype(str)
    df["Year"] = df["date"].dt.year
    df["Month"] = df["date"].dt.month
    df["DOY"] = df["date"].dt.dayofyear

    # Forward-fill/backward-fill along the full time axis per county (across years)
    df = df.sort_values(["County", "date"])
    df["NDVI"] = df.groupby("County")["NDVI"].ffill().bfill()
    df["NDWI"] = df.groupby("County")["NDWI"].ffill().bfill()

    return df


def _wide_palmer_to_long(df_wide: pd.DataFrame, value_prefix: str) -> pd.DataFrame:
    """
    Convert wide Palmer index (County, PREFIX_YYYY-MM columns) to long:
      County, ym (datetime), value
    """
    df = df_wide.copy()
    df["County"] = df["County"].map(_standardize_county)

    value_cols = [c for c in df.columns if c.startswith(value_prefix + "_")]
    if not value_cols:
        raise ValueError(f"No columns found with prefix {value_prefix!r}")

    long = df.melt(id_vars=["County"], value_vars=value_cols, var_name="ym", value_name=value_prefix)
    long["ym"] = long["ym"].str.replace(value_prefix + "_", "", regex=False)
    long["ym"] = pd.to_datetime(long["ym"] + "-01", errors="coerce")
    long[value_prefix] = pd.to_numeric(long[value_prefix], errors="coerce")
    long = long.dropna(subset=["ym"])
    long["Year"] = long["ym"].dt.year
    long["Month"] = long["ym"].dt.month
    return long[["County", "Year", "Month", value_prefix]]


def load_palmer() -> pd.DataFrame:
    pdsi_w = pd.read_csv(INPUT_PDSI_WIDE)
    phdi_w = pd.read_csv(INPUT_PHDI_WIDE)
    pdsi = _wide_palmer_to_long(pdsi_w, "PDSI")
    phdi = _wide_palmer_to_long(phdi_w, "PHDI")
    out = pd.merge(pdsi, phdi, on=["County", "Year", "Month"], how="outer")
    return out


def load_soil_awc() -> pd.DataFrame:
    soil = pd.read_csv(INPUT_SOIL)
    soil["County"] = soil["County"].map(_standardize_county)
    soil["avg_water_content"] = pd.to_numeric(soil["avg_water_content"], errors="coerce")
    # The soil file includes duplicates for some counties; aggregate to a single county value.
    soil = soil.groupby("County", as_index=False)["avg_water_content"].mean()
    return soil


def load_yield() -> pd.DataFrame:
    y = pd.read_csv(INPUT_YIELD_LONG)
    y["County"] = y["County"].astype(str).map(_standardize_county)
    y["Year"] = pd.to_numeric(y["Year"], errors="coerce")
    y["Yield"] = pd.to_numeric(y["Yield"], errors="coerce")
    y = y.dropna(subset=["Year", "County", "Yield"])
    y["Year"] = y["Year"].astype(int)
    return y[["County", "Year", "Yield", "District"]].copy()


def pearson_r2(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
    mask = x.notna() & y.notna()
    n = int(mask.sum())
    if n < 3:
        return np.nan, np.nan, n
    r = float(x[mask].corr(y[mask]))
    return r, float(r * r), n


def linreg_slope(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Ordinary least squares slope/intercept for y = a + b*x.
    Returns (b, a). Requires >=2 points.
    """
    if len(x) < 2:
        return np.nan, np.nan
    b, a = np.polyfit(x, y, 1)
    return float(b), float(a)


def r4r6_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute NDVI-vs-NDWI sensitivity metrics in DOY 200–260.
    """
    win = df[(df["DOY"] >= 200) & (df["DOY"] <= 260)].copy()
    rows = []
    for (county, year), g in win.groupby(["County", "Year"], sort=True):
        x_ndwi = g["NDWI"].to_numpy(dtype=float)
        y_ndvi = g["NDVI"].to_numpy(dtype=float)
        x_ndvi = g["NDVI"].to_numpy(dtype=float)
        y_ndwi = g["NDWI"].to_numpy(dtype=float)

        # Drop NaNs for regression (should be imputed, but keep safe)
        m1 = np.isfinite(x_ndwi) & np.isfinite(y_ndvi)
        m2 = np.isfinite(x_ndvi) & np.isfinite(y_ndwi)

        slope_ndvi_on_ndwi, _ = linreg_slope(x_ndwi[m1], y_ndvi[m1])
        slope_ndwi_on_ndvi, _ = linreg_slope(x_ndvi[m2], y_ndwi[m2])

        r, r2, n = pearson_r2(g["NDWI"], g["NDVI"])

        # Saturation diagnostic: variability when NDVI is high (proxy for high biomass)
        high = g["NDVI"] >= 0.75
        ndwi_std_high = float(g.loc[high, "NDWI"].std()) if int(high.sum()) >= 2 else np.nan
        ndvi_std_high = float(g.loc[high, "NDVI"].std()) if int(high.sum()) >= 2 else np.nan
        n_high = int(high.sum())

        rows.append(
            {
                "County": county,
                "Year": int(year),
                "Ag_District": str(g["Ag_District"].iloc[0]),
                "N_points": int(len(g)),
                "NDVI_mean": float(np.nanmean(y_ndvi)),
                "NDVI_max": float(np.nanmax(y_ndvi)),
                "NDVI_std": float(np.nanstd(y_ndvi)),
                "NDWI_mean": float(np.nanmean(y_ndwi)),
                "NDWI_min": float(np.nanmin(y_ndwi)),
                "NDWI_std": float(np.nanstd(y_ndwi)),
                "slope_NDVI_on_NDWI": slope_ndvi_on_ndwi,
                "slope_NDWI_on_NDVI": slope_ndwi_on_ndvi,
                "pearson_r": r,
                "pearson_r2": r2,
                "pearson_n": n,
                "N_points_high_NDVI": n_high,
                "NDWI_std_high_NDVI": ndwi_std_high,
                "NDVI_std_high_NDVI": ndvi_std_high,
            }
        )
    out = pd.DataFrame(rows)
    return out


def seasonal_index_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build county-year seasonal summaries and anomalies for:
      - late-season (DOY 220–260): NDVI_late, NDWI_late
      - reproductive window (DOY 200–260): NDVI_r4r6, NDWI_r4r6
    Anomalies are computed relative to each county's 2008–2024 mean.
    """
    def summarize(window_name: str, lo: int, hi: int) -> pd.DataFrame:
        sub = df[(df["DOY"] >= lo) & (df["DOY"] <= hi)].copy()
        agg = (
            sub.groupby(["County", "Ag_District", "Year"], as_index=False)
            .agg(
                NDVI=("NDVI", "mean"),
                NDWI=("NDWI", "mean"),
            )
        )
        agg = agg.rename(columns={"NDVI": f"NDVI_{window_name}", "NDWI": f"NDWI_{window_name}"})
        return agg

    late = summarize("late", 220, 260)
    r4r6 = summarize("r4r6", 200, 260)
    out = pd.merge(late, r4r6, on=["County", "Ag_District", "Year"], how="outer")

    # County climatology across available years (2008–2024)
    for col in ["NDVI_late", "NDWI_late", "NDVI_r4r6", "NDWI_r4r6"]:
        clim = out.groupby("County")[col].transform("mean")
        out[col + "_anom"] = out[col] - clim
    return out


def drought_correlations(seasonal: pd.DataFrame, palmer: pd.DataFrame) -> pd.DataFrame:
    """
    Correlate seasonal index anomalies with Palmer drought indices.
    Uses July–September mean PDSI/PHDI per county-year.
    """
    # July–September mean drought index per county-year
    p = palmer[palmer["Month"].isin([7, 8, 9])].copy()
    p = p.groupby(["County", "Year"], as_index=False).agg(PDSI_JAS=("PDSI", "mean"), PHDI_JAS=("PHDI", "mean"))

    df = pd.merge(seasonal, p, on=["County", "Year"], how="inner")

    # correlation across all county-years
    rows = []
    for drought_col in ["PDSI_JAS", "PHDI_JAS"]:
        for idx_col in ["NDWI_late_anom", "NDVI_late_anom", "NDWI_r4r6_anom", "NDVI_r4r6_anom"]:
            r, r2, n = pearson_r2(df[drought_col], df[idx_col])
            rows.append({"drought": drought_col, "index": idx_col, "pearson_r": r, "r2": r2, "n": n})
    return pd.DataFrame(rows).sort_values(["drought", "index"])


def soil_resilience(df: pd.DataFrame, palmer: pd.DataFrame, soil: pd.DataFrame) -> pd.DataFrame:
    """
    Compare NDWI declines for low vs high AWC counties during dry years.
    Dry year definition (implemented): county-year where JAS PHDI <= -2.0.
    NDWI decline metrics (implemented):
      - NDWI_late_mean - NDWI_early_mean (directional change)
      - NDWI_peak_mean - NDWI_late_mean (drop from within-season peak into late season)
      early window: DOY 160–190
      peak window:  DOY 160–220 (max across 10-day steps, averaged across ties)
      late window:  DOY 220–260
    """
    # Windows
    early = df[(df["DOY"] >= 160) & (df["DOY"] <= 190)].groupby(["County", "Year"], as_index=False)["NDWI"].mean().rename(columns={"NDWI": "NDWI_early"})
    late = df[(df["DOY"] >= 220) & (df["DOY"] <= 260)].groupby(["County", "Year"], as_index=False)["NDWI"].mean().rename(columns={"NDWI": "NDWI_late"})
    # Peak NDWI between DOY 160–220 (peak canopy period)
    peak = (
        df[(df["DOY"] >= 160) & (df["DOY"] <= 220)]
        .groupby(["County", "Year"], as_index=False)["NDWI"]
        .max()
        .rename(columns={"NDWI": "NDWI_peak"})
    )

    nd = early.merge(late, on=["County", "Year"], how="inner").merge(peak, on=["County", "Year"], how="left")
    nd["NDWI_decline_late_minus_early"] = nd["NDWI_late"] - nd["NDWI_early"]
    nd["NDWI_drop_peak_to_late"] = nd["NDWI_peak"] - nd["NDWI_late"]

    # County-year drought metric (JAS PHDI)
    p = palmer[palmer["Month"].isin([7, 8, 9])].groupby(["County", "Year"], as_index=False)["PHDI"].mean().rename(columns={"PHDI": "PHDI_JAS"})

    out = nd.merge(p, on=["County", "Year"], how="inner").merge(soil, on="County", how="left")

    # AWC group by median across counties
    awc_med = float(out["avg_water_content"].median())
    out["AWC_group"] = np.where(out["avg_water_content"] <= awc_med, "Low_AWC", "High_AWC")
    out["is_dry_year"] = out["PHDI_JAS"] <= -2.0
    return out


def statewide_2012_signature(df: pd.DataFrame) -> pd.DataFrame:
    """
    Quantify 2012 NDWI drop vs 2008–2024 climatology at the 10-day (date) resolution.

    Implemented:
      - statewide mean NDWI for each day-of-year step (across counties, within year)
      - climatology mean across years for each DOY step
      - percent drop = (2012 - climatology) / climatology * 100
    """
    d = df.copy()
    d["DOY"] = d["date"].dt.dayofyear
    step = d.groupby(["Year", "DOY"], as_index=False)["NDWI"].mean().rename(columns={"NDWI": "NDWI_state_mean"})
    clim = step.groupby("DOY", as_index=False)["NDWI_state_mean"].mean().rename(columns={"NDWI_state_mean": "NDWI_clim_mean"})
    out = step.merge(clim, on="DOY", how="left")
    out["NDWI_anom"] = out["NDWI_state_mean"] - out["NDWI_clim_mean"]
    out["NDWI_pct_drop"] = (out["NDWI_state_mean"] - out["NDWI_clim_mean"]) / out["NDWI_clim_mean"] * 100.0
    return out[out["Year"].isin([2012])].copy()


def district_monthly_heatmaps(df: pd.DataFrame):
    """
    Heatmap: X=Year (2008–2024), Y=Month, value=NDWI anomaly for a district.
    Anomaly baseline is the district-month mean across all years.
    """
    sub = df.copy()
    sub = sub[sub["Month"].isin([5, 6, 7, 8, 9])]
    dm = (
        sub.groupby(["Ag_District", "Year", "Month"], as_index=False)["NDWI"]
        .mean()
        .rename(columns={"NDWI": "NDWI_month_mean"})
    )
    # district-month climatology
    dm["NDWI_month_clim"] = dm.groupby(["Ag_District", "Month"])["NDWI_month_mean"].transform("mean")
    dm["NDWI_month_anom"] = dm["NDWI_month_mean"] - dm["NDWI_month_clim"]

    years = list(range(2008, 2025))
    months = [5, 6, 7, 8, 9]
    month_labels = ["May", "Jun", "Jul", "Aug", "Sep"]

    for district in DISTRICT_ORDER:
        dd = dm[dm["Ag_District"] == district]
        mat = np.full((len(months), len(years)), np.nan, dtype=float)
        for i, m in enumerate(months):
            row = dd[dd["Month"] == m].set_index("Year")["NDWI_month_anom"]
            for j, y in enumerate(years):
                if y in row.index:
                    mat[i, j] = float(row.loc[y])

        fig, ax = plt.subplots(figsize=(14, 4))
        im = ax.imshow(mat, aspect="auto", cmap="RdBu_r", vmin=-0.15, vmax=0.15)
        ax.set_title(f"Heatmap of Stress (NDWI anomaly), {district} (2008–2024)", fontsize=14, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel("Month")
        ax.set_xticks(np.arange(len(years)))
        ax.set_xticklabels(years, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(np.arange(len(months)))
        ax.set_yticklabels(month_labels)
        cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
        cbar.set_label("NDWI anomaly (vs district-month mean)")
        plt.tight_layout()
        out = os.path.join(OUT_DIR, "figures", f"Heatmap_Stress_NDWI_Anomaly_{district.replace(' ', '_')}.png")
        plt.savefig(out, dpi=300, bbox_inches="tight")
        plt.close()

    dm.to_csv(os.path.join(OUT_DIR, "tables", "District_Monthly_NDWI_Anomalies.csv"), index=False)


def critical_window_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per county, find the 3-step (~30 day) window with maximum interannual volatility.
    Volatility is defined as the interannual standard deviation at each DOY step.

    Implemented:
      - For each county and DOY: std across years of NDWI and NDVI (using imputed values)
      - For each county: compute rolling mean std over 3 consecutive DOY steps (as ordered by DOY)
      - Pick the window with maximum rolling mean for NDWI (also report NDVI volatility over same window)
    """
    d = df.copy()
    d["DOY"] = d["date"].dt.dayofyear
    # Keep only growing-season-like range observed in the dataset (roughly May–Sep)
    d = d[(d["DOY"] >= 120) & (d["DOY"] <= 275)].copy()

    vol = (
        d.groupby(["County", "DOY"], as_index=False)
        .agg(
            NDWI_std=("NDWI", "std"),
            NDVI_std=("NDVI", "std"),
            N_years=("Year", "nunique"),
        )
        .sort_values(["County", "DOY"])
    )

    rows = []
    for county, g in vol.groupby("County", sort=True):
        g = g.sort_values("DOY").reset_index(drop=True)
        # rolling window of 3 steps (approx 30 days for 10-day sampling)
        g["NDWI_roll3"] = g["NDWI_std"].rolling(3, min_periods=3).mean()
        g["NDVI_roll3"] = g["NDVI_std"].rolling(3, min_periods=3).mean()
        if g["NDWI_roll3"].notna().sum() == 0:
            continue
        idx = int(g["NDWI_roll3"].idxmax())
        start_doy = int(g.loc[idx - 2, "DOY"])
        end_doy = int(g.loc[idx, "DOY"])
        rows.append(
            {
                "County": county,
                "start_DOY": start_doy,
                "end_DOY": end_doy,
                "start_mmdd": pd.Timestamp("2001-01-01") + pd.to_timedelta(start_doy - 1, unit="D"),
                "end_mmdd": pd.Timestamp("2001-01-01") + pd.to_timedelta(end_doy - 1, unit="D"),
                "NDWI_volatility_roll3_std": float(g.loc[idx, "NDWI_roll3"]),
                "NDVI_volatility_roll3_std": float(g.loc[idx, "NDVI_roll3"]),
                "min_N_years_in_window": int(g.loc[idx - 2 : idx, "N_years"].min()),
            }
        )
    out = pd.DataFrame(rows).sort_values("County")
    if not out.empty:
        out["start_mmdd"] = pd.to_datetime(out["start_mmdd"]).dt.strftime("%b-%d")
        out["end_mmdd"] = pd.to_datetime(out["end_mmdd"]).dt.strftime("%b-%d")
    return out


def soil_awc_anomaly_group_analysis(seasonal: pd.DataFrame, palmer: pd.DataFrame, soil: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Grouped analysis using NDWI/NDVI seasonal anomalies rather than within-season "declines".

    Implemented:
      - Define dry county-years by PHDI_JAS <= -2.0 (JAS = Jul–Aug–Sep mean)
      - Split counties into Low/High AWC groups by median avg_water_content
      - Summarize mean/median anomalies for NDWI_late_anom and NDVI_late_anom in dry years
    """
    p = palmer[palmer["Month"].isin([7, 8, 9])].groupby(["County", "Year"], as_index=False)["PHDI"].mean().rename(columns={"PHDI": "PHDI_JAS"})
    df = seasonal.merge(p, on=["County", "Year"], how="inner").merge(soil, on="County", how="left")
    awc_med = float(df["avg_water_content"].median())
    df["AWC_group"] = np.where(df["avg_water_content"] <= awc_med, "Low_AWC", "High_AWC")
    df["is_dry_year"] = df["PHDI_JAS"] <= -2.0

    dry = df[df["is_dry_year"]].copy()
    if dry.empty:
        return df, pd.DataFrame()

    summary = (
        dry.groupby("AWC_group", as_index=False)
        .agg(
            n=("County", "size"),
            mean_PHDI_JAS=("PHDI_JAS", "mean"),
            mean_awc=("avg_water_content", "mean"),
            mean_NDWI_late_anom=("NDWI_late_anom", "mean"),
            median_NDWI_late_anom=("NDWI_late_anom", "median"),
            mean_NDVI_late_anom=("NDVI_late_anom", "mean"),
            median_NDVI_late_anom=("NDVI_late_anom", "median"),
        )
    )
    return df, summary


def yield_interval_correlations(df: pd.DataFrame, y: pd.DataFrame) -> pd.DataFrame:
    """
    Pearson correlations between yield and 10-day interval indices (county-year level).

    Implemented:
      - For each DOY step: correlate Yield vs NDWI and Yield vs NDVI across county-years
      - Uses years where both yield and indices exist.
    """
    # merge yield
    dd = df.copy()
    dd["County"] = dd["County"].map(_standardize_county)
    yy = y.copy()
    yy["County"] = yy["County"].map(_standardize_county)

    merged = dd.merge(yy[["County", "Year", "Yield"]], on=["County", "Year"], how="inner")
    merged["DOY"] = merged["date"].dt.dayofyear

    rows = []
    for doy, g in merged.groupby("DOY", sort=True):
        r_ndwi, r2_ndwi, n_ndwi = pearson_r2(g["Yield"], g["NDWI"])
        r_ndvi, r2_ndvi, n_ndvi = pearson_r2(g["Yield"], g["NDVI"])
        rows.append(
            {
                "DOY": int(doy),
                "n_county_years": int(len(g.dropna(subset=["Yield"]))),
                "r_Yield_NDWI": r_ndwi,
                "r2_Yield_NDWI": r2_ndwi,
                "r_Yield_NDVI": r_ndvi,
                "r2_Yield_NDVI": r2_ndvi,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("DOY")


def yield_interval_correlations_by_district(df: pd.DataFrame, y: pd.DataFrame) -> pd.DataFrame:
    """
    Same as yield_interval_correlations, but stratified by agricultural district.
    """
    dd = df.copy()
    dd["County"] = dd["County"].map(_standardize_county)
    yy = y.copy()
    yy["County"] = yy["County"].map(_standardize_county)

    merged = dd.merge(yy[["County", "Year", "Yield"]], on=["County", "Year"], how="inner")
    merged["DOY"] = merged["date"].dt.dayofyear

    rows = []
    for (district, doy), g in merged.groupby(["Ag_District", "DOY"], sort=True):
        r_ndwi, r2_ndwi, _ = pearson_r2(g["Yield"], g["NDWI"])
        r_ndvi, r2_ndvi, _ = pearson_r2(g["Yield"], g["NDVI"])
        rows.append(
            {
                "Ag_District": str(district),
                "DOY": int(doy),
                "n_county_years": int(len(g.dropna(subset=["Yield"]))),
                "r_Yield_NDWI": r_ndwi,
                "r2_Yield_NDWI": r2_ndwi,
                "r_Yield_NDVI": r_ndvi,
                "r2_Yield_NDVI": r2_ndvi,
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["Ag_District", "DOY"])


def plot_sensitivity_summary(sens: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 5))
    # boxplot-like via scatter jitter (no seaborn dependency)
    rng = np.random.default_rng(0)
    for i, d in enumerate(DISTRICT_ORDER):
        sub = sens[sens["Ag_District"] == d]
        x = i + rng.normal(0, 0.06, size=len(sub))
        ax.scatter(x, sub["slope_NDVI_on_NDWI"], s=18, alpha=0.6, color=DISTRICT_COLORS[d], edgecolor="none")
        if len(sub) > 0:
            ax.hlines(sub["slope_NDVI_on_NDWI"].median(), i - 0.25, i + 0.25, colors="black", linewidth=2)
    ax.set_xticks(range(len(DISTRICT_ORDER)))
    ax.set_xticklabels(DISTRICT_ORDER, rotation=20, ha="right")
    ax.set_ylabel("Slope (NDVI ~ NDWI) in DOY 200–260")
    ax.set_title("Index sensitivity during reproductive window (R4–R6 proxy)", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "figures", "R4R6_Sensitivity_Slope_NDVI_on_NDWI_ByDistrict.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()


def plot_drought_scatter(seasonal: pd.DataFrame, palmer: pd.DataFrame):
    p = palmer[palmer["Month"].isin([7, 8, 9])].groupby(["County", "Year"], as_index=False).agg(PDSI_JAS=("PDSI", "mean"), PHDI_JAS=("PHDI", "mean"))
    df = seasonal.merge(p, on=["County", "Year"], how="inner")

    pairs = [
        ("PDSI_JAS", "NDWI_late_anom"),
        ("PHDI_JAS", "NDWI_late_anom"),
        ("PDSI_JAS", "NDVI_late_anom"),
        ("PHDI_JAS", "NDVI_late_anom"),
    ]
    for xcol, ycol in pairs:
        x = df[xcol]
        y = df[ycol]
        r, r2, n = pearson_r2(x, y)

        fig, ax = plt.subplots(figsize=(6.5, 5.5))
        ax.scatter(x, y, s=22, alpha=0.65, color="#2c3e50")
        # regression line
        mask = x.notna() & y.notna()
        if mask.sum() >= 2:
            b, a = np.polyfit(x[mask].to_numpy(), y[mask].to_numpy(), 1)
            xx = np.linspace(float(x[mask].min()), float(x[mask].max()), 100)
            ax.plot(xx, a + b * xx, color="red", linewidth=2)
        ax.set_xlabel(xcol)
        ax.set_ylabel(ycol)
        ax.set_title(f"{ycol} vs {xcol}\nPearson r={r:.2f}, $R^2$={r2:.2f}, n={n}", fontsize=12, fontweight="bold")
        ax.grid(alpha=0.25)
        plt.tight_layout()
        out = os.path.join(OUT_DIR, "figures", f"Scatter_{ycol}_vs_{xcol}.png")
        plt.savefig(out, dpi=300, bbox_inches="tight")
        plt.close()


def plot_2012_signature(sig2012: pd.DataFrame):
    # Focus on DOY range covered by the 10-day series (roughly May–Sep)
    s = sig2012[(sig2012["DOY"] >= 120) & (sig2012["DOY"] <= 275)].copy()
    fig, ax1 = plt.subplots(figsize=(12, 4.5))
    ax1.plot(s["DOY"], s["NDWI_pct_drop"], color="#1f77b4", linewidth=2)
    ax1.axhline(0, color="black", linewidth=1)
    ax1.set_xlabel("Day of Year (DOY)")
    ax1.set_ylabel("NDWI percent difference vs 2008–2024 climatology (%)")
    ax1.set_title("2012 drought signature: statewide NDWI percent difference vs climatology", fontsize=14, fontweight="bold")
    ax1.grid(alpha=0.25)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "figures", "Statewide_2012_NDWI_PercentDiff_vs_Climatology.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()


def plot_yield_correlations(corr: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(corr["DOY"], corr["r_Yield_NDWI"], label="r(Yield, NDWI)", color="#2ca02c", linewidth=2)
    ax.plot(corr["DOY"], corr["r_Yield_NDVI"], label="r(Yield, NDVI)", color="#ff7f0e", linewidth=2)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xlabel("Day of Year (DOY)")
    ax.set_ylabel("Pearson r across county-years")
    ax.set_title("Yield vs 10-day indices: Pearson correlation by DOY", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend()
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "figures", "Yield_Correlation_By_DOY.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()


def plot_soil_resilience(res: pd.DataFrame):
    # box-like scatter for dry years only
    dry = res[res["is_dry_year"]].copy()
    if dry.empty:
        return
    fig, ax = plt.subplots(figsize=(7, 5))
    rng = np.random.default_rng(0)
    groups = ["Low_AWC", "High_AWC"]
    for i, gname in enumerate(groups):
        sub = dry[dry["AWC_group"] == gname]
        x = i + rng.normal(0, 0.06, size=len(sub))
        ax.scatter(x, sub["NDWI_decline_late_minus_early"], s=24, alpha=0.65, color="#34495e", edgecolor="none")
        if len(sub) > 0:
            ax.hlines(sub["NDWI_decline_late_minus_early"].median(), i - 0.22, i + 0.22, colors="red", linewidth=2)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.set_ylabel("NDWI(late) − NDWI(early) (negative = decline)")
    ax.set_title("Soil resilience during dry years (PHDI_JAS ≤ −2)", fontsize=13, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "figures", "SoilResilience_NDWI_Decline_DryYears_Low_vs_High_AWC.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()

def soil_resilience_summary_table(res: pd.DataFrame) -> pd.DataFrame:
    dry = res[res["is_dry_year"]].copy()
    if dry.empty:
        return pd.DataFrame()
    summ = (
        dry.groupby("AWC_group", as_index=False)
        .agg(
            n=("NDWI_drop_peak_to_late", "size"),
            median_drop_peak_to_late=("NDWI_drop_peak_to_late", "median"),
            mean_drop_peak_to_late=("NDWI_drop_peak_to_late", "mean"),
            median_change_late_minus_early=("NDWI_decline_late_minus_early", "median"),
            mean_change_late_minus_early=("NDWI_decline_late_minus_early", "mean"),
            mean_PHDI_JAS=("PHDI_JAS", "mean"),
            mean_awc=("avg_water_content", "mean"),
        )
    )
    return summ


def statewide_window_percentdiff(df: pd.DataFrame, lo: int, hi: int, label: str) -> Dict[str, float]:
    d = df.copy()
    d = d[(d["DOY"] >= lo) & (d["DOY"] <= hi)].copy()
    state_year = d.groupby("Year", as_index=False)["NDWI"].mean().rename(columns={"NDWI": "NDWI_state_mean"})
    clim = float(state_year["NDWI_state_mean"].mean())
    y2012 = float(state_year[state_year["Year"] == 2012]["NDWI_state_mean"].iloc[0]) if (state_year["Year"] == 2012).any() else np.nan
    pct = (y2012 - clim) / clim * 100.0 if np.isfinite(y2012) and np.isfinite(clim) and clim != 0 else np.nan
    return {"window": label, "NDWI_climatology_mean": clim, "NDWI_2012_mean": y2012, "NDWI_2012_pct_diff": pct}


def r4r6_statewide_drop_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Single-number 2012 percent differences vs 2008–2024 climatology for key windows.
    """
    rows = [
        statewide_window_percentdiff(df, 160, 190, "DOY_160_190 (early)"),
        statewide_window_percentdiff(df, 200, 260, "DOY_200_260 (R4–R6 proxy)"),
        statewide_window_percentdiff(df, 220, 260, "DOY_220_260 (late)"),
        statewide_window_percentdiff(df, 240, 272, "DOY_240_272 (very late)"),
    ]
    return pd.DataFrame(rows)


def main():
    ensure_outdir()

    print("Loading 10-day indices (imputed)...")
    idx = load_indices_long_imputed()

    print("Loading Palmer drought indices (PDSI/PHDI)...")
    palmer = load_palmer()

    print("Loading soil water capacity (avg_water_content)...")
    soil = load_soil_awc()

    print("Loading yield data...")
    yld = load_yield()

    # 1) Sensitivity analysis (R4–R6 proxy window)
    print("Computing R4–R6 (DOY 200–260) NDVI/NDWI sensitivity metrics...")
    sens = r4r6_sensitivity(idx)
    sens.to_csv(os.path.join(OUT_DIR, "tables", "R4R6_Sensitivity_CountyYear.csv"), index=False)
    plot_sensitivity_summary(sens)

    # 2) Seasonal anomalies (for drought correlation & 2012 signature)
    print("Computing seasonal index anomalies...")
    seasonal = seasonal_index_anomalies(idx)
    seasonal.to_csv(os.path.join(OUT_DIR, "tables", "Seasonal_Index_Anomalies_CountyYear.csv"), index=False)

    print("Computing drought correlation summary (2012–2024 overlap)...")
    drought_tbl = drought_correlations(seasonal, palmer)
    drought_tbl.to_csv(os.path.join(OUT_DIR, "tables", "Drought_Correlation_Summary.csv"), index=False)
    plot_drought_scatter(seasonal, palmer)

    # 3) Soil resilience attribution
    print("Computing soil resilience grouped analysis...")
    soil_res = soil_resilience(idx, palmer, soil)
    soil_res.to_csv(os.path.join(OUT_DIR, "tables", "SoilResilience_CountyYear.csv"), index=False)
    plot_soil_resilience(soil_res)
    # Anomaly-based soil/AWC group analysis for dry years
    soil_anom, soil_anom_summ = soil_awc_anomaly_group_analysis(seasonal, palmer, soil)
    soil_anom.to_csv(os.path.join(OUT_DIR, "tables", "SoilResilience_AnomalyBased_CountyYear.csv"), index=False)
    if not soil_anom_summ.empty:
        soil_anom_summ.to_csv(os.path.join(OUT_DIR, "tables", "SoilResilience_AnomalyBased_DryYears_Summary.csv"), index=False)

    # 4) 2012 drought signature (statewide)
    print("Quantifying 2012 drought signature vs climatology...")
    sig2012 = statewide_2012_signature(idx)
    sig2012.to_csv(os.path.join(OUT_DIR, "tables", "Statewide_2012_NDWI_Signature.csv"), index=False)
    plot_2012_signature(sig2012)
    r4r6_drop = r4r6_statewide_drop_summary(idx)
    r4r6_drop.to_csv(os.path.join(OUT_DIR, "tables", "Statewide_2012_NDWI_R4R6_PercentDiff.csv"), index=False)

    # 5) Heatmap of Stress by district
    print("Generating district NDWI anomaly heatmaps...")
    district_monthly_heatmaps(idx)

    # 6) Critical phenological window (volatility)
    print("Computing critical phenological windows by county (volatility)...")
    crit = critical_window_volatility(idx)
    crit.to_csv(os.path.join(OUT_DIR, "tables", "County_CriticalWindow_Volatility.csv"), index=False)

    # Yield correlations by 10-day interval (DOY)
    print("Computing yield correlations by DOY...")
    yc = yield_interval_correlations(idx, yld)
    yc.to_csv(os.path.join(OUT_DIR, "tables", "Yield_Correlation_By_DOY.csv"), index=False)
    plot_yield_correlations(yc)
    ycd = yield_interval_correlations_by_district(idx, yld)
    ycd.to_csv(os.path.join(OUT_DIR, "tables", "Yield_Correlation_By_DOY_ByDistrict.csv"), index=False)

    # Soil resilience summary (dry years)
    soil_summ = soil_resilience_summary_table(soil_res)
    if not soil_summ.empty:
        soil_summ.to_csv(os.path.join(OUT_DIR, "tables", "SoilResilience_DryYears_Summary.csv"), index=False)

    print("Done.")


if __name__ == "__main__":
    main()

