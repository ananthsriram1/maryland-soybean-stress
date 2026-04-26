#!/usr/bin/env python3
"""
District-by-district: do lower R4–R6 (DOY 200–260) NDVI/NDWI correspond to lower yield?

Inputs:
  - outputs/StressDrivers/tables/DistrictYear_StressDrivers_and_Indices.csv
      (contains district-year NDVI/NDWI late-season means and anomalies)
  - data/processed_yield/yield_district_averages_by_year.csv

Outputs:
  - outputs/StressDrivers/tables/DistrictYear_Yield_and_Indices.csv
  - outputs/StressDrivers/figures/District_Yield_vs_R4R6_IndexAnoms.png
  - outputs/StressDrivers/figures/District_Yield_vs_R4R6_IndexLevels.png

Notes:
  - Uses district-relative anomalies for a clean "specific year" interpretation:
      Yield_anom = Yield - mean(Yield over available years in that district)
      NDWI_anom/NDVI_anom are already in the indices table.
  - Points are colored by year and the lowest-yield years per district are annotated.
"""

from __future__ import annotations

import os
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = "outputs/StressDrivers"
IN_IDX = os.path.join(OUT_DIR, "tables", "DistrictYear_StressDrivers_and_Indices.csv")
IN_YLD = "data/processed_yield/yield_district_averages_by_year.csv"

OUT_TABLE = os.path.join(OUT_DIR, "tables", "DistrictYear_Yield_and_Indices.csv")
OUT_ANOM = os.path.join(OUT_DIR, "figures", "District_Yield_vs_R4R6_IndexAnoms.png")
OUT_LEVELS = os.path.join(OUT_DIR, "figures", "District_Yield_vs_R4R6_IndexLevels.png")


DISTRICT_ORDER = [
    "WESTERN",
    "NORTH CENTRAL",
    "SOUTHERN",
    "UPPER EASTERN SHORE",
    "LOWER EASTERN SHORE",
]


def ensure_outdir():
    os.makedirs(os.path.join(OUT_DIR, "tables"), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "figures"), exist_ok=True)


def linfit_stats(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
    m = x.notna() & y.notna()
    n = int(m.sum())
    if n < 3:
        return np.nan, np.nan, n
    r = float(x[m].corr(y[m]))
    return r, float(r * r), n


def load_and_merge() -> pd.DataFrame:
    idx = pd.read_csv(IN_IDX)
    idx = idx.rename(columns={"Ag_District": "District"})
    idx["Year"] = pd.to_numeric(idx["Year"], errors="coerce")

    y = pd.read_csv(IN_YLD)
    y["Year"] = pd.to_numeric(y["Year"], errors="coerce")
    y["Yield_bu_ac"] = pd.to_numeric(y["Yield_mean"], errors="coerce")
    y = y[["District", "Year", "Yield_bu_ac", "Yield_std", "Yield_count"]].copy()

    df = idx.merge(y, on=["District", "Year"], how="inner")
    df = df[df["District"].isin(DISTRICT_ORDER)].copy()

    # District-relative yield anomaly + z
    mu = df.groupby("District")["Yield_bu_ac"].transform("mean")
    sd = df.groupby("District")["Yield_bu_ac"].transform("std")
    df["Yield_anom"] = df["Yield_bu_ac"] - mu
    df["Yield_z"] = df["Yield_anom"] / sd
    return df


def _annotate_low_years(ax: plt.Axes, sub: pd.DataFrame, xcol: str, ycol: str, k: int = 2):
    # annotate k lowest-yield years with slight offsets
    s = sub.dropna(subset=[xcol, ycol, "Yield_bu_ac"]).sort_values("Yield_bu_ac", ascending=True).head(k)
    for _, r in s.iterrows():
        ax.annotate(
            str(int(r["Year"])),
            (float(r[xcol]), float(r[ycol])),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8,
            color="#222222",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="#cccccc", alpha=0.85),
        )


def scatter_grid(
    df: pd.DataFrame,
    xcols: Tuple[str, str],
    ycol: str,
    title: str,
    out_png: str,
    year_min: int,
    year_max: int,
):
    d = df[(df["Year"] >= year_min) & (df["Year"] <= year_max)].copy()
    cmap = plt.get_cmap("viridis")
    norm = plt.Normalize(year_min, year_max)

    fig, axes = plt.subplots(len(DISTRICT_ORDER), 2, figsize=(12, 14), sharex=False, sharey=False)
    for i, district in enumerate(DISTRICT_ORDER):
        sub = d[d["District"] == district].copy()
        for j, xcol in enumerate(xcols):
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
                ax.scatter(p2012[xcol], p2012[ycol], s=90, facecolor="none", edgecolor="black", linewidth=2)

            _annotate_low_years(ax, sub, xcol, ycol, k=2)

            if i == 0:
                ax.set_title(xcol, fontweight="bold")
            if j == 0:
                ax.set_ylabel(district)
            ax.grid(alpha=0.25)

    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.995)
    for ax in axes[-1, :]:
        ax.set_xlabel("Index value")

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes.ravel().tolist(), fraction=0.015, pad=0.01)
    cbar.set_label("Year")
    plt.tight_layout(rect=[0, 0, 1, 0.985])
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()


def main():
    ensure_outdir()
    df = load_and_merge()

    df.to_csv(OUT_TABLE, index=False)

    # 1) Anomaly view (best for "specific year" question)
    scatter_grid(
        df,
        xcols=("NDWI_late_mean_anom", "NDVI_late_mean_anom"),
        ycol="Yield_anom",
        title="District-by-district: yield anomaly vs R4–R6 index anomaly (DOY 200–260)\n(black circle=2012; labels=2 lowest yield years per district)",
        out_png=OUT_ANOM,
        year_min=int(df["Year"].min()),
        year_max=int(df["Year"].max()),
    )

    # 2) Levels view (absolute units)
    scatter_grid(
        df,
        xcols=("NDWI_late_mean", "NDVI_late_mean"),
        ycol="Yield_bu_ac",
        title="District-by-district: yield (bu/ac) vs R4–R6 index level (DOY 200–260)\n(black circle=2012; labels=2 lowest yield years per district)",
        out_png=OUT_LEVELS,
        year_min=int(df["Year"].min()),
        year_max=int(df["Year"].max()),
    )

    print(f"Saved: {OUT_TABLE}")
    print(f"Saved: {OUT_ANOM}")
    print(f"Saved: {OUT_LEVELS}")


if __name__ == "__main__":
    main()

