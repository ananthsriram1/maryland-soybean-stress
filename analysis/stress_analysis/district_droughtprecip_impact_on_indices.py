#!/usr/bin/env python3
"""
District-by-district effect of precipitation and drought on NDVI/NDWI (2008–2024).

Creates:
  outputs/StressDrivers/tables/DistrictYear_StressDrivers_and_Indices.csv
  outputs/StressDrivers/figures/District_PrecipJAS_vs_IndicesLate_Anomaly.png
  outputs/StressDrivers/figures/District_PHDIJAS_vs_IndicesLate_Anomaly.png
  outputs/StressDrivers/figures/District_Standardized_TimeSeries_StressDrivers.png

Definitions (implemented):
  - Indices late-season window: DOY 200–260, district-year mean across counties.
  - Precipitation: Jul–Sep total of district monthly mean precip (inches), district-year.
  - Drought: Jul–Sep mean of county PHDI/PDSI, averaged across counties within district-year.
  - Anomalies: value minus district mean across available years (for that variable).
  - Z-score: anomaly / district std across years (for that variable).

Notes:
  - Indices are forward/backward-filled per county (consistent with repo preprocessing style).
  - PHDI/PDSI data in this repo start in 2012, so drought plots/time-series use 2012–2024.
"""

from __future__ import annotations

import os
import re
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = "outputs/StressDrivers"
OUT_TABLE = os.path.join(OUT_DIR, "tables", "DistrictYear_StressDrivers_and_Indices.csv")

INPUT_INDICES = "data/maryland_soybean_10day_timeseries_long.csv"
INPUT_PRECIP_WIDE = "data/maryland_precipitation_combined_wide.csv"
INPUT_PDSI_WIDE = "data/maryland_pdsi_combined_wide.csv"
INPUT_PHDI_WIDE = "data/maryland_phdi_combined_wide.csv"


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

# Same mapping used in precipitation scripts
COUNTY_TO_DISTRICT: Dict[str, str] = {
    "Allegany": "WESTERN",
    "Garrett": "WESTERN",
    "Baltimore": "NORTH CENTRAL",
    "Baltimore City": "NORTH CENTRAL",
    "Carroll": "NORTH CENTRAL",
    "Frederick": "NORTH CENTRAL",
    "Harford": "NORTH CENTRAL",
    "Howard": "NORTH CENTRAL",
    "Montgomery": "NORTH CENTRAL",
    "Washington": "NORTH CENTRAL",
    "Anne Arundel": "SOUTHERN",
    "Calvert": "SOUTHERN",
    "Charles": "SOUTHERN",
    "Prince George's": "SOUTHERN",
    "St. Mary's": "SOUTHERN",
    "Caroline": "UPPER EASTERN SHORE",
    "Cecil": "UPPER EASTERN SHORE",
    "Kent": "UPPER EASTERN SHORE",
    "Queen Anne's": "UPPER EASTERN SHORE",
    "Talbot": "UPPER EASTERN SHORE",
    "Dorchester": "LOWER EASTERN SHORE",
    "Somerset": "LOWER EASTERN SHORE",
    "Wicomico": "LOWER EASTERN SHORE",
    "Worcester": "LOWER EASTERN SHORE",
}


def ensure_outdir():
    os.makedirs(os.path.join(OUT_DIR, "tables"), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "figures"), exist_ok=True)


def _standardize_county(s: str) -> str:
    s = str(s).strip().title()
    s = re.sub(r"'S\b", "'s", s)
    return s


def load_indices_district_year() -> pd.DataFrame:
    df = pd.read_csv(INPUT_INDICES, parse_dates=["date"])
    df["County"] = df["County"].map(_standardize_county)
    df["Ag_District"] = df["Ag_District"].astype(str)
    df["Year"] = df["date"].dt.year
    df["DOY"] = df["date"].dt.dayofyear
    df = df.sort_values(["County", "date"])
    df["NDVI"] = df.groupby("County")["NDVI"].ffill().bfill()
    df["NDWI"] = df.groupby("County")["NDWI"].ffill().bfill()

    late = df[(df["DOY"] >= 200) & (df["DOY"] <= 260)].copy()
    out = (
        late.groupby(["Ag_District", "Year"], as_index=False)
        .agg(
            NDVI_late_mean=("NDVI", "mean"),
            NDWI_late_mean=("NDWI", "mean"),
            n_counties=("County", "nunique"),
        )
    )
    return out


def parse_wide_precip_to_long(df_wide: pd.DataFrame) -> pd.DataFrame:
    value_cols = [c for c in df_wide.columns if c.startswith("Precip_")]
    long = df_wide.melt(id_vars=["County"], value_vars=value_cols, var_name="ym", value_name="precip_in")
    long["ym"] = long["ym"].str.replace("Precip_", "", regex=False)
    long["date"] = pd.to_datetime(long["ym"] + "-01", errors="coerce")
    long["Year"] = long["date"].dt.year
    long["Month"] = long["date"].dt.month
    long["precip_in"] = pd.to_numeric(long["precip_in"], errors="coerce")
    return long.dropna(subset=["date"])


def load_precip_district_year() -> pd.DataFrame:
    wide = pd.read_csv(INPUT_PRECIP_WIDE)
    long = parse_wide_precip_to_long(wide)
    long["County"] = long["County"].map(_standardize_county)
    long["Ag_District"] = long["County"].map(COUNTY_TO_DISTRICT)
    long = long.dropna(subset=["Ag_District"])

    # district monthly mean across counties
    dm = (
        long.groupby(["Ag_District", "Year", "Month"], as_index=False)["precip_in"]
        .mean()
        .rename(columns={"precip_in": "district_mean_month_in"})
    )
    jas = dm[dm["Month"].isin([7, 8, 9])].groupby(["Ag_District", "Year"], as_index=False)["district_mean_month_in"].sum()
    jas = jas.rename(columns={"district_mean_month_in": "Precip_JAS_in"})
    return jas


def _wide_palmer_to_long(path: str, prefix: str) -> pd.DataFrame:
    w = pd.read_csv(path)
    w["County"] = w["County"].map(_standardize_county)
    cols = [c for c in w.columns if c.startswith(prefix + "_")]
    long = w.melt(id_vars=["County"], value_vars=cols, var_name="ym", value_name=prefix)
    long["ym"] = long["ym"].str.replace(prefix + "_", "", regex=False)
    long["ym"] = pd.to_datetime(long["ym"] + "-01", errors="coerce")
    long[prefix] = pd.to_numeric(long[prefix], errors="coerce")
    long = long.dropna(subset=["ym"])
    long["Year"] = long["ym"].dt.year
    long["Month"] = long["ym"].dt.month
    return long[["County", "Year", "Month", prefix]]


def load_palmer_district_year() -> pd.DataFrame:
    pdsi = _wide_palmer_to_long(INPUT_PDSI_WIDE, "PDSI")
    phdi = _wide_palmer_to_long(INPUT_PHDI_WIDE, "PHDI")
    pal = pd.merge(pdsi, phdi, on=["County", "Year", "Month"], how="outer")
    pal["Ag_District"] = pal["County"].map(COUNTY_TO_DISTRICT)
    pal = pal.dropna(subset=["Ag_District"])
    jas = pal[pal["Month"].isin([7, 8, 9])].groupby(["Ag_District", "Year"], as_index=False).agg(
        PDSI_JAS=("PDSI", "mean"),
        PHDI_JAS=("PHDI", "mean"),
    )
    return jas


def add_anoms_z(df: pd.DataFrame, col: str) -> pd.DataFrame:
    mu = df.groupby("Ag_District")[col].transform("mean")
    sd = df.groupby("Ag_District")[col].transform("std")
    df[col + "_anom"] = df[col] - mu
    df[col + "_z"] = df[col + "_anom"] / sd
    return df


def linfit_stats(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
    m = x.notna() & y.notna()
    n = int(m.sum())
    if n < 3:
        return np.nan, np.nan, n
    r = float(x[m].corr(y[m]))
    return r, float(r * r), n


def scatter_grid(
    df: pd.DataFrame,
    xcol: str,
    ycols: Tuple[str, str],
    title: str,
    out_png: str,
    year_min: int,
    year_max: int,
):
    d = df[(df["Year"] >= year_min) & (df["Year"] <= year_max)].copy()
    years = d["Year"].to_numpy()
    cmap = plt.get_cmap("viridis")
    norm = plt.Normalize(year_min, year_max)

    fig, axes = plt.subplots(len(DISTRICT_ORDER), 2, figsize=(12, 14), sharex=False, sharey=False)
    for i, district in enumerate(DISTRICT_ORDER):
        sub = d[d["Ag_District"] == district].copy()
        for j, ycol in enumerate(ycols):
            ax = axes[i, j]
            ax.scatter(sub[xcol], sub[ycol], c=cmap(norm(sub["Year"])), s=35, alpha=0.85, edgecolor="none")
            # regression line
            m = sub[xcol].notna() & sub[ycol].notna()
            if int(m.sum()) >= 3:
                b, a = np.polyfit(sub.loc[m, xcol].to_numpy(dtype=float), sub.loc[m, ycol].to_numpy(dtype=float), 1)
                xx = np.linspace(float(sub.loc[m, xcol].min()), float(sub.loc[m, xcol].max()), 100)
                ax.plot(xx, a + b * xx, color="red", linewidth=2)
            r, r2, n = linfit_stats(sub[xcol], sub[ycol])
            ax.text(
                0.02,
                0.96,
                f"r={r:.2f}, $R^2$={r2:.2f}, n={n}",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#cccccc", alpha=0.9),
            )
            # highlight 2012 if present
            p2012 = sub[sub["Year"] == 2012]
            if not p2012.empty and p2012[xcol].notna().any() and p2012[ycol].notna().any():
                ax.scatter(p2012[xcol], p2012[ycol], s=80, facecolor="none", edgecolor="black", linewidth=2)
            if i == 0:
                ax.set_title(ycol, fontweight="bold")
            if j == 0:
                ax.set_ylabel(district)
            ax.grid(alpha=0.25)

    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.995)
    for ax in axes[-1, :]:
        ax.set_xlabel(xcol)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), fraction=0.015, pad=0.01)
    cbar.set_label("Year")
    plt.tight_layout(rect=[0, 0, 1, 0.985])
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()


def standardized_timeseries(df: pd.DataFrame, out_png: str):
    # Use 2012–2024 so precip/PHDI/indices all exist together (PHDI starts 2012)
    d = df[(df["Year"] >= 2012) & (df["Year"] <= 2024)].copy()

    fig, axes = plt.subplots(len(DISTRICT_ORDER), 1, figsize=(12, 14), sharex=True)
    for i, district in enumerate(DISTRICT_ORDER):
        ax = axes[i]
        sub = d[d["Ag_District"] == district].sort_values("Year")
        ax.plot(sub["Year"], sub["Precip_JAS_in_z"], label="Precip JAS (z)", color="#1f77b4", linewidth=2)
        ax.plot(sub["Year"], sub["PHDI_JAS_z"], label="PHDI JAS (z)", color="#d62728", linewidth=2)
        ax.plot(sub["Year"], sub["NDWI_late_mean_z"], label="NDWI late (z)", color="#2ca02c", linewidth=2)
        ax.plot(sub["Year"], sub["NDVI_late_mean_z"], label="NDVI late (z)", color="#ff7f0e", linewidth=2)
        ax.axvline(2012, color="black", linestyle="--", linewidth=1)
        ax.set_ylabel(district)
        ax.grid(alpha=0.25)
        if i == 0:
            ax.legend(ncol=4, loc="upper left", frameon=True)
    axes[-1].set_xlabel("Year")
    fig.suptitle("District standardized stress drivers vs indices (z-scores, JAS + late-season)", fontsize=14, fontweight="bold", y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.985])
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()


def _quantile_bins(s: pd.Series) -> pd.Series:
    """
    Per-district binning for "dry / normal / wet" using quartiles:
      dry: <= 25th percentile
      wet: >= 75th percentile
      normal: otherwise
    """
    if s.dropna().nunique() < 4:
        return pd.Series(["normal"] * len(s), index=s.index)
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    out = pd.Series(np.where(s <= q1, "dry", np.where(s >= q3, "wet", "normal")), index=s.index)
    out = out.where(s.notna(), np.nan)
    return out


def category_effect_plot(df: pd.DataFrame, out_png: str):
    """
    Show the effect of "dry vs normal vs wet" summers on NDWI/NDVI anomalies,
    separately for precipitation and PHDI (when available).
    """
    d = df.copy()

    # Precip categories using district-specific precipitation anomaly distribution (all available years)
    d["Precip_cat"] = d.groupby("Ag_District")["Precip_JAS_in_anom"].transform(_quantile_bins)

    # PHDI categories (only where PHDI exists); use common Palmer interpretation thresholds
    def phdi_cat(v: float) -> str:
        if pd.isna(v):
            return np.nan
        if v <= -2.0:
            return "severe (≤-2)"
        if v <= -1.0:
            return "moderate (-2 to -1)"
        if v < 1.0:
            return "near-normal (-1 to 1)"
        return "wet (≥1)"

    d["PHDI_cat"] = d["PHDI_JAS"].map(phdi_cat)

    fig, axes = plt.subplots(len(DISTRICT_ORDER), 2, figsize=(14, 14), sharex=False, sharey=False)

    for i, district in enumerate(DISTRICT_ORDER):
        sub = d[d["Ag_District"] == district].copy()

        # Left: precip categories
        ax = axes[i, 0]
        order = ["dry", "normal", "wet"]
        x = np.arange(len(order))
        for k, label, color in [
            ("NDWI_late_mean_anom", "NDWI (late) anomaly", "#2ca02c"),
            ("NDVI_late_mean_anom", "NDVI (late) anomaly", "#ff7f0e"),
        ]:
            means = [sub.loc[sub["Precip_cat"] == cat, k].mean() for cat in order]
            ax.plot(x, means, marker="o", linewidth=2, label=label, color=color, alpha=0.95)
        ax.axhline(0, color="#444444", linewidth=1, alpha=0.7)
        ax.set_xticks(x, order)
        ax.set_ylabel(district)
        ax.grid(alpha=0.25)
        if i == 0:
            ax.set_title("Index anomaly by JAS precip category (district-relative)", fontweight="bold")
            ax.legend(ncol=2, loc="upper left", frameon=True)

        # Right: PHDI categories (2012+ only; could be missing for some districts/years)
        ax2 = axes[i, 1]
        order2 = ["severe (≤-2)", "moderate (-2 to -1)", "near-normal (-1 to 1)", "wet (≥1)"]
        x2 = np.arange(len(order2))
        for k, label, color in [
            ("NDWI_late_mean_anom", "NDWI (late) anomaly", "#2ca02c"),
            ("NDVI_late_mean_anom", "NDVI (late) anomaly", "#ff7f0e"),
        ]:
            means2 = [sub.loc[sub["PHDI_cat"] == cat, k].mean() for cat in order2]
            ax2.plot(x2, means2, marker="o", linewidth=2, label=label, color=color, alpha=0.95)
        ax2.axhline(0, color="#444444", linewidth=1, alpha=0.7)
        ax2.set_xticks(x2, order2)
        ax2.grid(alpha=0.25)
        if i == 0:
            ax2.set_title("Index anomaly by JAS PHDI category (2012–2024)", fontweight="bold")

    fig.suptitle(
        "District-wise NDWI/NDVI late-season response to low precipitation and drought",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.985])
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()


def _inputs_exist() -> bool:
    return all(os.path.exists(p) for p in [INPUT_INDICES, INPUT_PRECIP_WIDE, INPUT_PDSI_WIDE, INPUT_PHDI_WIDE])


def main():
    ensure_outdir()

    if _inputs_exist():
        idx = load_indices_district_year()
        pr = load_precip_district_year()
        pal = load_palmer_district_year()

        # merge district-year
        df = idx.merge(pr, on=["Ag_District", "Year"], how="left").merge(pal, on=["Ag_District", "Year"], how="left")

        # anomalies and z-scores
        for col in ["NDVI_late_mean", "NDWI_late_mean", "Precip_JAS_in", "PHDI_JAS", "PDSI_JAS"]:
            df = add_anoms_z(df, col)

        df.to_csv(OUT_TABLE, index=False)
    elif os.path.exists(OUT_TABLE):
        df = pd.read_csv(OUT_TABLE)
    else:
        raise FileNotFoundError(
            "Raw inputs not found and no precomputed table exists. Expected either:\n"
            f"- Raw inputs: {INPUT_INDICES}, {INPUT_PRECIP_WIDE}, {INPUT_PDSI_WIDE}, {INPUT_PHDI_WIDE}\n"
            f"- Or precomputed table: {OUT_TABLE}"
        )

    # Precip effects (2008–2024)
    scatter_grid(
        df,
        xcol="Precip_JAS_in_anom",
        ycols=("NDWI_late_mean_anom", "NDVI_late_mean_anom"),
        title="District-by-district: Jul–Sep precipitation anomaly vs late-season index anomaly (DOY 200–260)",
        out_png=os.path.join(OUT_DIR, "figures", "District_PrecipJAS_vs_IndicesLate_Anomaly.png"),
        year_min=2008,
        year_max=2024,
    )

    # Drought effects (2012–2024, PHDI available)
    scatter_grid(
        df,
        xcol="PHDI_JAS",
        ycols=("NDWI_late_mean_anom", "NDVI_late_mean_anom"),
        title="District-by-district: Jul–Sep PHDI vs late-season index anomaly (DOY 200–260)",
        out_png=os.path.join(OUT_DIR, "figures", "District_PHDIJAS_vs_IndicesLate_Anomaly.png"),
        year_min=2012,
        year_max=2024,
    )

    scatter_grid(
        df,
        xcol="PDSI_JAS",
        ycols=("NDWI_late_mean_anom", "NDVI_late_mean_anom"),
        title="District-by-district: Jul–Sep PDSI vs late-season index anomaly (DOY 200–260)",
        out_png=os.path.join(OUT_DIR, "figures", "District_PDSIJAS_vs_IndicesLate_Anomaly.png"),
        year_min=2012,
        year_max=2024,
    )

    standardized_timeseries(
        df,
        out_png=os.path.join(OUT_DIR, "figures", "District_Standardized_TimeSeries_StressDrivers.png"),
    )

    category_effect_plot(
        df,
        out_png=os.path.join(OUT_DIR, "figures", "District_CategoryEffects_DryWet_vs_Indices.png"),
    )

    print(f"Saved: {OUT_TABLE}")


if __name__ == "__main__":
    main()

