#!/usr/bin/env python3
"""
Differential Stress Analysis (2008–2024): explain where NDVI plateaus and NDWI succeeds.

Inputs (repo paths):
  - data/maryland_soybean_10day_timeseries_long.csv
  - data/processed_yield/yield_clean_long_format.csv
  - data/maryland_only_soil_water_content_FINAL.csv
  - data/maryland_pdsi_combined_wide.csv
  - data/maryland_phdi_combined_wide.csv

Outputs:
  outputs/DifferentialStressAnalysis/tables/*.csv
  outputs/DifferentialStressAnalysis/figures/*.png

Implemented analyses:
  1) NDVI Plateau (district saturation proxy)
     - For each district + DOY in 200–260: compute across-county variance per year, then take median across years.
     - Define plateau DOY as first DOY where:
         NDVI_var_median <= q_ndvi (20th pct within district, DOY 200–260)
         AND NDWI_var_median >= q_ndwi (60th pct within district, DOY 200–260)
     - Outputs plateau DOY per district + variance curves.

  2) Leading Indicator Test (temporal lag)
     - Cross-correlation between NDWI and NDVI in DOY 200–260 at lags (−3..+3) 10-day steps,
       computed per county-year and summarized (mean + bootstrap CI).
     - Event test: NDWI drop ≥10% from DOY 200 to DOY 210 predicts:
         (a) NDVI change from DOY 210 to DOY 230 (≈20 days later)
         (b) yield anomaly (yield − county mean)
       Significance via permutation test (10,000 shuffles).

  3) Soil-water tipping point (2012)
     - Split counties into Low/High AWC by median avg_water_content.
     - For 2012: find first DOY where NDWI < 0.2 (within DOY 120–275).
       Compare groups via permutation test.
     - Also compare 2012 NDWI slope over DOY 200–260 (linear fit NDWI ~ DOY) by group.

  4) Heatmap regularization (trend removal + z-scores)
     - Compute district-month mean NDWI (May–Sep) by year.
     - De-trend using a trailing 5-year rolling mean within each district-month.
     - Convert detrended anomalies to z-scores within each district-month.
     - Plot heatmaps (X=Year, Y=Month, color=z).

  5) Yield anomaly prediction (AUC optimization)
     - Compute NDWI AUC over DOY 200–260 per county-year using trapezoidal integration in time.
     - Compare linear models (closed-form OLS):
         Yield ~ NDWI_r4r6_mean
         Yield ~ NDWI_AUC_r4r6
         Yield_anom ~ NDWI_AUC_r4r6
       Report R^2 on the full sample and Leave-One-Year-Out (LOYO) CV R^2.

Dependencies: numpy, pandas, matplotlib (no scipy/sklearn).
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = "outputs/DifferentialStressAnalysis"

INPUT_INDICES = "data/maryland_soybean_10day_timeseries_long.csv"
INPUT_YIELD = "data/processed_yield/yield_clean_long_format.csv"
INPUT_SOIL = "data/maryland_only_soil_water_content_FINAL.csv"
INPUT_PDSI = "data/maryland_pdsi_combined_wide.csv"
INPUT_PHDI = "data/maryland_phdi_combined_wide.csv"


DISTRICT_ORDER = [
    "WESTERN",
    "NORTH CENTRAL",
    "SOUTHERN",
    "UPPER EASTERN SHORE",
    "LOWER EASTERN SHORE",
]


def ensure_outdir():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "tables"), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "figures"), exist_ok=True)


def _standardize_county(s: str) -> str:
    s = str(s).strip().title()
    s = re.sub(r"'S\b", "'s", s)
    return s


def load_indices_imputed() -> pd.DataFrame:
    df = pd.read_csv(INPUT_INDICES, parse_dates=["date"])
    df["County"] = df["County"].map(_standardize_county)
    df["Ag_District"] = df["Ag_District"].astype(str)
    df["Year"] = df["date"].dt.year
    df["Month"] = df["date"].dt.month
    df["DOY"] = df["date"].dt.dayofyear
    df = df.sort_values(["County", "date"])
    # ffill/bfill per county (same logic family as PreprocessNDWI.py)
    df["NDVI"] = df.groupby("County")["NDVI"].ffill().bfill()
    df["NDWI"] = df.groupby("County")["NDWI"].ffill().bfill()
    return df


def load_yield() -> pd.DataFrame:
    y = pd.read_csv(INPUT_YIELD)
    y["County"] = y["County"].map(_standardize_county)
    y["Year"] = pd.to_numeric(y["Year"], errors="coerce").astype("Int64")
    y["Yield"] = pd.to_numeric(y["Yield"], errors="coerce")
    y = y.dropna(subset=["County", "Year", "Yield"])
    y["Year"] = y["Year"].astype(int)
    return y[["County", "Year", "Yield", "District"]].copy()


def load_soil() -> pd.DataFrame:
    s = pd.read_csv(INPUT_SOIL)
    s["County"] = s["County"].map(_standardize_county)
    s["avg_water_content"] = pd.to_numeric(s["avg_water_content"], errors="coerce")
    s = s.dropna(subset=["County", "avg_water_content"])
    # duplicates exist; mean-collapse
    s = s.groupby("County", as_index=False)["avg_water_content"].mean()
    return s


def _wide_palmer_to_long(df_wide: pd.DataFrame, prefix: str) -> pd.DataFrame:
    df = df_wide.copy()
    df["County"] = df["County"].map(_standardize_county)
    cols = [c for c in df.columns if c.startswith(prefix + "_")]
    long = df.melt(id_vars=["County"], value_vars=cols, var_name="ym", value_name=prefix)
    long["ym"] = long["ym"].str.replace(prefix + "_", "", regex=False)
    long["ym"] = pd.to_datetime(long["ym"] + "-01", errors="coerce")
    long[prefix] = pd.to_numeric(long[prefix], errors="coerce")
    long = long.dropna(subset=["ym"])
    long["Year"] = long["ym"].dt.year
    long["Month"] = long["ym"].dt.month
    return long[["County", "Year", "Month", prefix]]


def load_palmer() -> pd.DataFrame:
    pdsi = _wide_palmer_to_long(pd.read_csv(INPUT_PDSI), "PDSI")
    phdi = _wide_palmer_to_long(pd.read_csv(INPUT_PHDI), "PHDI")
    return pd.merge(pdsi, phdi, on=["County", "Year", "Month"], how="outer")


def permutation_pvalue_diff_means(x: np.ndarray, y: np.ndarray, n_perm: int = 10_000, seed: int = 0) -> float:
    """Two-sided permutation p-value for difference in means."""
    x = x[np.isfinite(x)]
    y = y[np.isfinite(y)]
    if len(x) < 2 or len(y) < 2:
        return np.nan
    obs = float(np.mean(x) - np.mean(y))
    pool = np.concatenate([x, y])
    n_x = len(x)
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        d = float(np.mean(pool[:n_x]) - np.mean(pool[n_x:]))
        if abs(d) >= abs(obs):
            count += 1
    return (count + 1) / (n_perm + 1)


def bootstrap_ci_mean(x: np.ndarray, n_boot: int = 2000, seed: int = 0) -> Tuple[float, float, float]:
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_boot):
        samp = rng.choice(x, size=len(x), replace=True)
        means.append(float(np.mean(samp)))
    means = np.array(means)
    return float(np.mean(x)), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def ndvi_plateau_by_district(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute district-level median across-county variance curves for DOY 200–260.
    Returns:
      - curves: district, DOY, NDVI_var_median, NDWI_var_median
      - plateau: district, plateau_DOY, plateau_rule thresholds
    """
    sub = df[(df["DOY"] >= 200) & (df["DOY"] <= 260)].copy()
    # variance across counties within district-year-DOY
    vy = (
        sub.groupby(["Ag_District", "Year", "DOY"], as_index=False)
        .agg(
            NDVI_var=("NDVI", "var"),
            NDWI_var=("NDWI", "var"),
            n_counties=("County", "nunique"),
        )
    )
    curves = (
        vy.groupby(["Ag_District", "DOY"], as_index=False)
        .agg(
            NDVI_var_median=("NDVI_var", "median"),
            NDWI_var_median=("NDWI_var", "median"),
            n_years=("Year", "nunique"),
        )
    )

    rows = []
    for d in DISTRICT_ORDER:
        dd = curves[curves["Ag_District"] == d].copy().sort_values("DOY")
        if dd.empty:
            continue
        # Saturation proxy:
        # pick DOY where NDVI variance is minimal, but only among DOYs where NDWI variance
        # is at/above its median (NDWI remains "responsive"/variable).
        ndwi_med = float(dd["NDWI_var_median"].median())
        candidates = dd[dd["NDWI_var_median"] >= ndwi_med].copy()
        if candidates.empty:
            candidates = dd
        plateau_doy = int(candidates.loc[candidates["NDVI_var_median"].idxmin(), "DOY"])
        q_ndvi = float(dd["NDVI_var_median"].quantile(0.20))
        q_ndwi = float(dd["NDWI_var_median"].quantile(0.60))
        rows.append(
            {
                "Ag_District": d,
                "plateau_DOY": plateau_doy,
                "NDVI_var_thresh_q20": q_ndvi,
                "NDWI_var_thresh_q60": q_ndwi,
                "NDWI_var_median_reference": ndwi_med,
            }
        )
    plateau = pd.DataFrame(rows)
    return curves, plateau


def plot_plateau_curves(curves: pd.DataFrame, plateau: pd.DataFrame):
    for d in DISTRICT_ORDER:
        dd = curves[curves["Ag_District"] == d].sort_values("DOY")
        if dd.empty:
            continue
        p = plateau[plateau["Ag_District"] == d]
        pdoy = int(p["plateau_DOY"].iloc[0]) if not p.empty else None

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dd["DOY"], dd["NDVI_var_median"], label="NDVI variance (median across years)", color="#ff7f0e", linewidth=2)
        ax.plot(dd["DOY"], dd["NDWI_var_median"], label="NDWI variance (median across years)", color="#2ca02c", linewidth=2)
        if pdoy is not None:
            ax.axvline(pdoy, color="black", linestyle="--", linewidth=1.5, label=f"Plateau DOY ≈ {pdoy}")
        ax.set_title(f"NDVI plateau diagnostic (DOY 200–260): {d}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Day of Year (DOY)")
        ax.set_ylabel("Across-county variance")
        ax.grid(alpha=0.25)
        ax.legend()
        plt.tight_layout()
        out = os.path.join(OUT_DIR, "figures", f"Plateau_VarianceCurves_{d.replace(' ', '_')}.png")
        plt.savefig(out, dpi=300, bbox_inches="tight")
        plt.close()


def extract_doy_value(df: pd.DataFrame, doy: int, value_col: str) -> pd.DataFrame:
    """
    For each county-year, take the row at the given DOY.
    If multiple dates share the same DOY (rare), take mean.
    """
    sub = df[df["DOY"] == doy].copy()
    out = (
        sub.groupby(["County", "Ag_District", "Year"], as_index=False)
        .agg(**{value_col: (value_col, "mean")})
    )
    return out


def extract_nearest_doy_value(df: pd.DataFrame, target_doy: int, value_col: str, max_abs_delta: int = 4) -> pd.DataFrame:
    """
    For each county-year, take the value at the nearest available DOY to target_doy.
    Only uses matches within +/- max_abs_delta days; otherwise drops the record.
    """
    sub = df.copy()
    sub["abs_delta"] = (sub["DOY"] - target_doy).abs()
    sub = sub[sub["abs_delta"] <= max_abs_delta]
    if sub.empty:
        return pd.DataFrame(columns=["County", "Ag_District", "Year", value_col, "DOY_used"])

    # pick nearest DOY per county-year (if multiple, mean values at that DOY)
    best = sub.sort_values(["County", "Year", "abs_delta", "DOY"]).groupby(["County", "Year"], as_index=False).first()
    picked = sub.merge(best[["County", "Year", "DOY"]], on=["County", "Year", "DOY"], how="inner")
    out = (
        picked.groupby(["County", "Ag_District", "Year", "DOY"], as_index=False)
        .agg(**{value_col: (value_col, "mean")})
        .rename(columns={"DOY": "DOY_used"})
    )
    return out


def cross_correlation_ndwi_ndvi(df: pd.DataFrame, lags_steps: List[int]) -> pd.DataFrame:
    """
    Compute per county-year cross-correlation between NDWI(t) and NDVI(t+lag),
    over DOY 200–260 aligned on the common 10-day sampling dates within that county-year.

    Lag is measured in number of 10-day steps (not exact days).
    """
    sub = df[(df["DOY"] >= 200) & (df["DOY"] <= 260)].copy()
    # build per county-year ordered sequences
    rows = []
    for (county, year), g in sub.groupby(["County", "Year"], sort=True):
        g = g.sort_values("date")
        x = g["NDWI"].to_numpy(dtype=float)
        y = g["NDVI"].to_numpy(dtype=float)
        if len(x) < 6:
            continue
        for lag in lags_steps:
            if lag == 0:
                xx, yy = x, y
            elif lag > 0:
                xx, yy = x[:-lag], y[lag:]
            else:
                k = -lag
                xx, yy = x[k:], y[:-k]
            if len(xx) < 4:
                continue
            r = np.corrcoef(xx, yy)[0, 1]
            rows.append({"County": county, "Year": int(year), "lag_steps": int(lag), "r": float(r)})
    return pd.DataFrame(rows)


def summarize_xcorr(xcorr: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lag, g in xcorr.groupby("lag_steps", sort=True):
        m, lo, hi = bootstrap_ci_mean(g["r"].to_numpy(dtype=float))
        rows.append({"lag_steps": int(lag), "mean_r": m, "ci95_lo": lo, "ci95_hi": hi, "n": int(len(g))})
    return pd.DataFrame(rows).sort_values("lag_steps")


def plot_xcorr_summary(summ: pd.DataFrame):
    if summ.empty:
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(summ["lag_steps"], summ["mean_r"], color="#34495e", linewidth=2)
    ax.fill_between(summ["lag_steps"], summ["ci95_lo"], summ["ci95_hi"], color="#95a5a6", alpha=0.35, linewidth=0)
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xlabel("Lag (10-day steps): NDVI(t+lag) vs NDWI(t)")
    ax.set_ylabel("Mean cross-correlation r")
    ax.set_title("Cross-correlation: NDWI leading vs NDVI (DOY 200–260)", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.25)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "figures", "CrossCorrelation_NDWI_to_NDVI_DOY200_260.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()


def leading_indicator_event_test(df: pd.DataFrame, yld: pd.DataFrame) -> pd.DataFrame:
    """
    Event: NDWI at R4 proxy <= 0.9 * NDWI at baseline proxy (>=10% drop).
      - baseline target DOY = 200 (nearest available DOY within +/-4)
      - R4 target DOY = 210 (nearest available DOY within +/-4; in this dataset typically DOY=212)
      - R6 target DOY = 230 (nearest available DOY within +/-4; in this dataset typically DOY=232)
    Outcomes:
      - NDVI_drop_20d = NDVI_230 - NDVI_210
      - Yield_anom = Yield - county mean
    Permutation p-values for difference in means between event vs non-event.
    """
    base = extract_nearest_doy_value(df, 200, "NDWI").rename(columns={"NDWI": "NDWI_base", "DOY_used": "DOY_base"})
    r4 = extract_nearest_doy_value(df, 210, "NDWI").rename(columns={"NDWI": "NDWI_r4", "DOY_used": "DOY_r4"})
    ndvi_r4 = extract_nearest_doy_value(df, 210, "NDVI").rename(columns={"NDVI": "NDVI_r4", "DOY_used": "DOY_r4_ndvi"})
    ndvi_r6 = extract_nearest_doy_value(df, 230, "NDVI").rename(columns={"NDVI": "NDVI_r6", "DOY_used": "DOY_r6"})

    m = base.merge(r4, on=["County", "Ag_District", "Year"], how="inner")
    m = m.merge(ndvi_r4, on=["County", "Ag_District", "Year"], how="inner").merge(ndvi_r6, on=["County", "Ag_District", "Year"], how="inner")
    m["event_ndwi_drop10"] = m["NDWI_r4"] <= 0.9 * m["NDWI_base"]
    m["NDVI_drop_20d"] = m["NDVI_r6"] - m["NDVI_r4"]

    yy = yld.copy()
    yy["County"] = yy["County"].map(_standardize_county)
    yy["Yield_anom"] = yy["Yield"] - yy.groupby("County")["Yield"].transform("mean")
    m = m.merge(yy[["County", "Year", "Yield", "Yield_anom"]], on=["County", "Year"], how="inner")

    ev = m[m["event_ndwi_drop10"]]
    ne = m[~m["event_ndwi_drop10"]]

    out = {
        "n_total": int(len(m)),
        "n_event": int(len(ev)),
        "mean_DOY_base_used": float(m["DOY_base"].mean()) if "DOY_base" in m else np.nan,
        "mean_DOY_r4_used": float(m["DOY_r4"].mean()) if "DOY_r4" in m else np.nan,
        "mean_DOY_r6_used": float(m["DOY_r6"].mean()) if "DOY_r6" in m else np.nan,
        "mean_NDVI_drop_20d_event": float(ev["NDVI_drop_20d"].mean()) if len(ev) else np.nan,
        "mean_NDVI_drop_20d_non_event": float(ne["NDVI_drop_20d"].mean()) if len(ne) else np.nan,
        "p_perm_NDVI_drop_20d": permutation_pvalue_diff_means(ev["NDVI_drop_20d"].to_numpy(), ne["NDVI_drop_20d"].to_numpy()),
        "mean_Yield_anom_event": float(ev["Yield_anom"].mean()) if len(ev) else np.nan,
        "mean_Yield_anom_non_event": float(ne["Yield_anom"].mean()) if len(ne) else np.nan,
        "p_perm_Yield_anom": permutation_pvalue_diff_means(ev["Yield_anom"].to_numpy(), ne["Yield_anom"].to_numpy()),
    }
    return pd.DataFrame([out])


def soil_tipping_point_2012(df: pd.DataFrame, soil: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    2012 tipping point:
      - first DOY where NDWI < 0.2 after DOY 200 (focus on reproductive/late season)
      - NDWI slope over DOY 220–272 (late-season decline fit NDWI ~ DOY)
    """
    d2012 = df[(df["Year"] == 2012) & (df["DOY"] >= 120) & (df["DOY"] <= 275)].copy()
    d2012 = d2012.merge(soil, on="County", how="left")
    awc_med = float(d2012["avg_water_content"].median())
    d2012["AWC_group"] = np.where(d2012["avg_water_content"] <= awc_med, "Low_AWC", "High_AWC")

    # first crossing NDWI < 0.2 after DOY 200
    cross_rows = []
    for county, g in d2012.groupby("County", sort=True):
        g = g.sort_values("DOY")
        below = g[(g["DOY"] >= 200) & (g["NDWI"] < 0.2)]
        cross_doy = int(below["DOY"].iloc[0]) if not below.empty else np.nan
        cross_rows.append(
            {
                "County": county,
                "AWC_group": str(g["AWC_group"].iloc[0]),
                "avg_water_content": float(g["avg_water_content"].iloc[0]) if pd.notna(g["avg_water_content"].iloc[0]) else np.nan,
                "first_DOY_NDWI_lt_0p2": cross_doy,
            }
        )
    cross = pd.DataFrame(cross_rows)

    # slope in late season DOY 220–272
    slope_rows = []
    ssub = d2012[(d2012["DOY"] >= 220) & (d2012["DOY"] <= 272)].copy()
    for county, g in ssub.groupby("County", sort=True):
        x = g["DOY"].to_numpy(dtype=float)
        y = g["NDWI"].to_numpy(dtype=float)
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() < 4:
            continue
        b, a = np.polyfit(x[m], y[m], 1)  # y = a + b*x
        slope_rows.append(
            {
                "County": county,
                "AWC_group": str(g["AWC_group"].iloc[0]),
                "avg_water_content": float(g["avg_water_content"].iloc[0]) if pd.notna(g["avg_water_content"].iloc[0]) else np.nan,
                "NDWI_slope_per_DOY_2012_220_272": float(b),
            }
        )
    slope = pd.DataFrame(slope_rows)

    # group-level stats + permutation tests
    low_cross = cross[cross["AWC_group"] == "Low_AWC"]["first_DOY_NDWI_lt_0p2"].to_numpy(dtype=float)
    high_cross = cross[cross["AWC_group"] == "High_AWC"]["first_DOY_NDWI_lt_0p2"].to_numpy(dtype=float)
    p_cross = permutation_pvalue_diff_means(low_cross, high_cross)

    low_slope = slope[slope["AWC_group"] == "Low_AWC"]["NDWI_slope_per_DOY_2012_220_272"].to_numpy(dtype=float)
    high_slope = slope[slope["AWC_group"] == "High_AWC"]["NDWI_slope_per_DOY_2012_220_272"].to_numpy(dtype=float)
    p_slope = permutation_pvalue_diff_means(low_slope, high_slope)

    summary = pd.DataFrame(
        [
            {
                "metric": "first_DOY_NDWI_lt_0.2",
                "n_low": int(np.isfinite(low_cross).sum()),
                "n_high": int(np.isfinite(high_cross).sum()),
                "mean_low": float(np.nanmean(low_cross)),
                "mean_high": float(np.nanmean(high_cross)),
                "p_perm": p_cross,
            },
            {
                "metric": "NDWI_slope_per_DOY_2012_220_272",
                "n_low": int(np.isfinite(low_slope).sum()),
                "n_high": int(np.isfinite(high_slope).sum()),
                "mean_low": float(np.nanmean(low_slope)),
                "mean_high": float(np.nanmean(high_slope)),
                "p_perm": p_slope,
            },
        ]
    )
    return cross, slope, summary


def detrended_zscore_heatmaps(df: pd.DataFrame):
    """
    District-month NDWI with trailing 5-year rolling-mean detrend, then z-score by district-month.
    """
    sub = df[df["Month"].isin([5, 6, 7, 8, 9])].copy()
    dm = sub.groupby(["Ag_District", "Year", "Month"], as_index=False)["NDWI"].mean().rename(columns={"NDWI": "NDWI_month"})
    dm = dm.sort_values(["Ag_District", "Month", "Year"])

    # trailing 5-year rolling mean within each district-month
    dm["roll5"] = (
        dm.groupby(["Ag_District", "Month"])["NDWI_month"]
        .transform(lambda s: s.rolling(window=5, min_periods=3).mean())
    )
    dm["detrended"] = dm["NDWI_month"] - dm["roll5"]
    # z-score within each district-month (using detrended values)
    grp = dm.groupby(["Ag_District", "Month"])["detrended"]
    dm["z"] = (dm["detrended"] - grp.transform("mean")) / grp.transform("std")

    years = list(range(2008, 2025))
    months = [5, 6, 7, 8, 9]
    month_labels = ["May", "Jun", "Jul", "Aug", "Sep"]

    for d in DISTRICT_ORDER:
        dd = dm[dm["Ag_District"] == d]
        mat = np.full((len(months), len(years)), np.nan, dtype=float)
        for i, m in enumerate(months):
            row = dd[dd["Month"] == m].set_index("Year")["z"]
            for j, y in enumerate(years):
                if y in row.index:
                    mat[i, j] = float(row.loc[y])
        fig, ax = plt.subplots(figsize=(14, 4))
        im = ax.imshow(mat, aspect="auto", cmap="RdBu_r", vmin=-3, vmax=3)
        ax.set_title(f"Detrended stress heatmap (NDWI z-score), {d} (2008–2024)", fontsize=13, fontweight="bold")
        ax.set_xlabel("Year")
        ax.set_ylabel("Month")
        ax.set_xticks(np.arange(len(years)))
        ax.set_xticklabels(years, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(np.arange(len(months)))
        ax.set_yticklabels(month_labels)
        cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
        cbar.set_label("Z-score (detrended within district-month)")
        plt.tight_layout()
        out = os.path.join(OUT_DIR, "figures", f"Heatmap_Detrended_Zscore_{d.replace(' ', '_')}.png")
        plt.savefig(out, dpi=300, bbox_inches="tight")
        plt.close()

    dm.to_csv(os.path.join(OUT_DIR, "tables", "District_Monthly_NDWI_Detrended_Zscore.csv"), index=False)


def auc_and_mean_r4r6(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute county-year NDWI mean and AUC over DOY 200–260.
    AUC uses trapezoid over actual day deltas between dates.
    """
    sub = df[(df["DOY"] >= 200) & (df["DOY"] <= 260)].copy()
    rows = []
    for (county, year), g in sub.groupby(["County", "Year"], sort=True):
        g = g.sort_values("date")
        t = g["date"].astype("int64").to_numpy(dtype=float) / (1e9 * 86400.0)  # days
        x = g["NDWI"].to_numpy(dtype=float)
        m = np.isfinite(t) & np.isfinite(x)
        if m.sum() < 4:
            continue
        t = t[m]
        x = x[m]
        auc = float(np.trapz(x, t))
        rows.append(
            {
                "County": county,
                "Year": int(year),
                "Ag_District": str(g["Ag_District"].iloc[0]),
                "NDWI_r4r6_mean": float(np.mean(x)),
                "NDWI_r4r6_AUC": auc,
                "n_points": int(len(x)),
            }
        )
    return pd.DataFrame(rows)

def county_year_feature_set(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build an expanded feature set intended for yield prediction.
    All features are computed from county-level mean NDVI/NDWI time series.
    """
    rows = []
    for (county, year), g in df.groupby(["County", "Year"], sort=True):
        g = g.sort_values("date")
        district = str(g["Ag_District"].iloc[0])

        def window(lo: int, hi: int) -> pd.DataFrame:
            return g[(g["DOY"] >= lo) & (g["DOY"] <= hi)]

        w_r4r6 = window(200, 260)
        w_late = window(220, 272)
        w_peak = window(160, 220)
        if len(w_r4r6) < 4 or len(w_late) < 4:
            continue

        # AUC in R4–R6 window
        t = w_r4r6["date"].astype("int64").to_numpy(dtype=float) / (1e9 * 86400.0)
        ndwi = w_r4r6["NDWI"].to_numpy(dtype=float)
        m = np.isfinite(t) & np.isfinite(ndwi)
        if m.sum() < 4:
            continue
        auc_ndwi_r4r6 = float(np.trapz(ndwi[m], t[m]))

        ndvi_r4r6 = w_r4r6["NDVI"].to_numpy(dtype=float)
        ndwi_late = w_late["NDWI"].to_numpy(dtype=float)

        ndwi_peak = float(np.nanmax(w_peak["NDWI"].to_numpy(dtype=float))) if len(w_peak) else np.nan
        ndwi_late_mean = float(np.nanmean(ndwi_late))
        ndwi_drop_peak_to_late = ndwi_peak - ndwi_late_mean if np.isfinite(ndwi_peak) and np.isfinite(ndwi_late_mean) else np.nan

        rows.append(
            {
                "County": county,
                "Year": int(year),
                "Ag_District": district,
                "NDWI_AUC_r4r6": auc_ndwi_r4r6,
                "NDWI_mean_r4r6": float(np.nanmean(ndwi)),
                "NDWI_min_r4r6": float(np.nanmin(ndwi)),
                "NDWI_mean_late": ndwi_late_mean,
                "NDWI_min_late": float(np.nanmin(ndwi_late)),
                "NDWI_peak_160_220": ndwi_peak,
                "NDWI_drop_peak_to_late": float(ndwi_drop_peak_to_late) if np.isfinite(ndwi_drop_peak_to_late) else np.nan,
                "NDVI_mean_r4r6": float(np.nanmean(ndvi_r4r6)),
                "NDVI_max_r4r6": float(np.nanmax(ndvi_r4r6)),
                "NDVI_std_r4r6": float(np.nanstd(ndvi_r4r6)),
                "n_points_r4r6": int(len(w_r4r6)),
            }
        )
    return pd.DataFrame(rows)


def ols_r2(y: np.ndarray, X: np.ndarray) -> float:
    """R^2 for OLS with intercept included in X."""
    y = y.astype(float)
    X = X.astype(float)
    # solve beta
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan


def loyo_r2(df: pd.DataFrame, y_col: str, x_cols: List[str], year_col: str = "Year") -> float:
    years = sorted(df[year_col].unique())
    preds = []
    trues = []
    for y in years:
        train = df[df[year_col] != y]
        test = df[df[year_col] == y]
        if len(test) < 3 or len(train) < 10:
            continue
        ytr = train[y_col].to_numpy(dtype=float)
        Xtr = np.column_stack([np.ones(len(train))] + [train[c].to_numpy(dtype=float) for c in x_cols])
        beta, *_ = np.linalg.lstsq(Xtr, ytr, rcond=None)
        Xte = np.column_stack([np.ones(len(test))] + [test[c].to_numpy(dtype=float) for c in x_cols])
        yhat = Xte @ beta
        preds.append(yhat)
        trues.append(test[y_col].to_numpy(dtype=float))
    if not preds:
        return np.nan
    yhat = np.concatenate(preds)
    ytrue = np.concatenate(trues)
    ss_res = float(np.sum((ytrue - yhat) ** 2))
    ss_tot = float(np.sum((ytrue - float(np.mean(ytrue))) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan


def yield_models(df_metrics: pd.DataFrame, yld: pd.DataFrame) -> pd.DataFrame:
    m = df_metrics.merge(yld[["County", "Year", "Yield"]], on=["County", "Year"], how="inner")
    m["Yield_anom"] = m["Yield"] - m.groupby("County")["Yield"].transform("mean")
    m = m.dropna(subset=["NDWI_r4r6_mean", "NDWI_r4r6_AUC", "Yield", "Yield_anom"])

    models = [
        ("Yield ~ NDWI_r4r6_mean", "Yield", ["NDWI_r4r6_mean"]),
        ("Yield ~ NDWI_r4r6_AUC", "Yield", ["NDWI_r4r6_AUC"]),
        ("Yield_anom ~ NDWI_r4r6_AUC", "Yield_anom", ["NDWI_r4r6_AUC"]),
        ("Yield ~ NDWI_r4r6_AUC + NDWI_r4r6_mean", "Yield", ["NDWI_r4r6_AUC", "NDWI_r4r6_mean"]),
    ]

    rows = []
    for name, ycol, xcols in models:
        y = m[ycol].to_numpy(dtype=float)
        X = np.column_stack([np.ones(len(m))] + [m[c].to_numpy(dtype=float) for c in xcols])
        r2 = ols_r2(y, X)
        r2_loyo = loyo_r2(m, ycol, xcols)
        rows.append({"model": name, "n": int(len(m)), "R2_full": float(r2), "R2_LOYO": float(r2_loyo)})
    return pd.DataFrame(rows)

def yield_models_extended(features: pd.DataFrame, yld: pd.DataFrame, soil: pd.DataFrame, palmer: pd.DataFrame) -> pd.DataFrame:
    """
    Try a richer set of models, including drought + soil covariates and district fixed effects.
    """
    # JAS drought indices per county-year
    jas = palmer[palmer["Month"].isin([7, 8, 9])].groupby(["County", "Year"], as_index=False).agg(PDSI_JAS=("PDSI", "mean"), PHDI_JAS=("PHDI", "mean"))
    df = features.merge(yld[["County", "Year", "Yield"]], on=["County", "Year"], how="inner")
    df = df.merge(soil, on="County", how="left").merge(jas, on=["County", "Year"], how="left")
    df["Yield_anom"] = df["Yield"] - df.groupby("County")["Yield"].transform("mean")

    # district dummies
    dummies = pd.get_dummies(df["Ag_District"], prefix="D", drop_first=True)
    df = pd.concat([df, dummies], axis=1)

    # candidate model specs
    model_specs = [
        ("Yield ~ NDWI_AUC_r4r6", "Yield", ["NDWI_AUC_r4r6"]),
        ("Yield ~ NDWI_AUC_r4r6 + NDWI_min_late", "Yield", ["NDWI_AUC_r4r6", "NDWI_min_late"]),
        ("Yield ~ NDWI_AUC_r4r6 + NDWI_min_late + NDVI_mean_r4r6", "Yield", ["NDWI_AUC_r4r6", "NDWI_min_late", "NDVI_mean_r4r6"]),
        ("Yield ~ NDWI_AUC_r4r6 + NDWI_min_late + PHDI_JAS", "Yield", ["NDWI_AUC_r4r6", "NDWI_min_late", "PHDI_JAS"]),
        ("Yield ~ NDWI_AUC_r4r6 + NDWI_min_late + PHDI_JAS + avg_water_content", "Yield", ["NDWI_AUC_r4r6", "NDWI_min_late", "PHDI_JAS", "avg_water_content"]),
        ("Yield ~ (indices + soil + drought) + district FE", "Yield", ["NDWI_AUC_r4r6", "NDWI_min_late", "PHDI_JAS", "avg_water_content"] + list(dummies.columns)),
        ("Yield_anom ~ (indices + soil + drought) + district FE", "Yield_anom", ["NDWI_AUC_r4r6", "NDWI_min_late", "PHDI_JAS", "avg_water_content"] + list(dummies.columns)),
    ]

    out_rows = []
    for name, ycol, xcols in model_specs:
        use = df.dropna(subset=[ycol] + xcols).copy()
        if len(use) < 60:
            out_rows.append({"model": name, "n": int(len(use)), "R2_full": np.nan, "R2_LOYO": np.nan})
            continue
        y = use[ycol].to_numpy(dtype=float)
        X = np.column_stack([np.ones(len(use))] + [use[c].to_numpy(dtype=float) for c in xcols])
        r2 = ols_r2(y, X)
        r2_loyo = loyo_r2(use, ycol, xcols)
        out_rows.append({"model": name, "n": int(len(use)), "R2_full": float(r2), "R2_LOYO": float(r2_loyo)})

    # district-specific models (often tighter relationships)
    for d in DISTRICT_ORDER:
        use_d = df[df["Ag_District"] == d].dropna(subset=["Yield", "NDWI_AUC_r4r6", "NDWI_min_late"]).copy()
        if len(use_d) < 30:
            continue
        y = use_d["Yield"].to_numpy(dtype=float)
        X = np.column_stack([np.ones(len(use_d)), use_d["NDWI_AUC_r4r6"].to_numpy(dtype=float), use_d["NDWI_min_late"].to_numpy(dtype=float)])
        r2 = ols_r2(y, X)
        r2_loyo = loyo_r2(use_d, "Yield", ["NDWI_AUC_r4r6", "NDWI_min_late"])
        out_rows.append({"model": f"Yield ~ NDWI_AUC_r4r6 + NDWI_min_late (district={d})", "n": int(len(use_d)), "R2_full": float(r2), "R2_LOYO": float(r2_loyo)})

    return pd.DataFrame(out_rows)

def main():
    ensure_outdir()
    idx = load_indices_imputed()
    yld = load_yield()
    soil = load_soil()
    palmer = load_palmer()  # not used in all sections yet, but kept for extension

    # 1) NDVI Plateau
    curves, plateau = ndvi_plateau_by_district(idx)
    curves.to_csv(os.path.join(OUT_DIR, "tables", "Plateau_VarianceCurves_ByDistrict_DOY200_260.csv"), index=False)
    plateau.to_csv(os.path.join(OUT_DIR, "tables", "Plateau_DOY_ByDistrict.csv"), index=False)
    plot_plateau_curves(curves, plateau)

    # 2) Leading Indicator
    xcorr = cross_correlation_ndwi_ndvi(idx, lags_steps=list(range(-3, 4)))
    xcorr.to_csv(os.path.join(OUT_DIR, "tables", "CrossCorrelation_PerCountyYear.csv"), index=False)
    xcorr_summ = summarize_xcorr(xcorr)
    xcorr_summ.to_csv(os.path.join(OUT_DIR, "tables", "CrossCorrelation_Summary.csv"), index=False)
    plot_xcorr_summary(xcorr_summ)

    lead = leading_indicator_event_test(idx, yld)
    lead.to_csv(os.path.join(OUT_DIR, "tables", "LeadingIndicator_EventTest.csv"), index=False)

    # 3) Soil tipping point 2012
    cross, slope, soil_summ = soil_tipping_point_2012(idx, soil)
    cross.to_csv(os.path.join(OUT_DIR, "tables", "SoilTippingPoint_2012_CrossingDOY.csv"), index=False)
    slope.to_csv(os.path.join(OUT_DIR, "tables", "SoilTippingPoint_2012_NDWI_Slopes.csv"), index=False)
    soil_summ.to_csv(os.path.join(OUT_DIR, "tables", "SoilTippingPoint_2012_Summary.csv"), index=False)

    # 4) Detrended heatmaps (z-scores)
    detrended_zscore_heatmaps(idx)

    # 5) Yield models using AUC
    metrics = auc_and_mean_r4r6(idx)
    metrics.to_csv(os.path.join(OUT_DIR, "tables", "R4R6_NDWI_Mean_and_AUC_CountyYear.csv"), index=False)
    ym = yield_models(metrics, yld)
    ym.to_csv(os.path.join(OUT_DIR, "tables", "YieldModel_Performance.csv"), index=False)

    feats = county_year_feature_set(idx)
    feats.to_csv(os.path.join(OUT_DIR, "tables", "CountyYear_FeatureSet.csv"), index=False)
    ym_ext = yield_models_extended(feats, yld, soil, palmer)
    ym_ext.to_csv(os.path.join(OUT_DIR, "tables", "YieldModel_Performance_Extended.csv"), index=False)

    print("Saved outputs to", OUT_DIR)


if __name__ == "__main__":
    main()

