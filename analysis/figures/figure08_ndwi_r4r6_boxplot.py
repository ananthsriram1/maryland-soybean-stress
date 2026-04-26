#!/usr/bin/env python3
"""
Compare NDWI distributions at R4–R6 (Beginning Seed, DOY 200–260) across Maryland districts.

Data: All 10-day NDWI values in the R4–R6 window, by Ag_District.
Visual goal:
  - Upper Eastern Shore (highly irrigated): boxplot stays between 0.37 and 0.58 (Iowa optimal benchmark).
  - Southern Maryland (rainfed): boxplot shows a long tail dropping below 0.12 (stress threshold).
  - Other three districts (Western, North Central, Lower Eastern Shore) shown for comparison.

Periods: 5-year spans aligned with census years (2007, 2012, 2017, 2022) → 2008–2012, 2013–2017, 2018–2022, 2023–2024.
Western district: NDWI from Garrett County only, from 2021 onward (NASS yield for Western is Garrett from 2021).

Input: data/maryland_soybean_10day_timeseries_long.csv
Outputs:
  - outputs/StressDrivers/figures/NDWI_R4R6_ByDistrict_Boxplot.png (single panel)
  - outputs/StressDrivers/figures/NDWI_R4R6_ByDistrict_Boxplot_ByCensusPeriod.png (4 subplots by period)
"""

from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DOY_R4R6_LO, DOY_R4R6_HI = 200, 260
NDWI_OPTIMAL_LO, NDWI_OPTIMAL_HI = 0.37, 0.58
# NDWI stress band (highlight in red); values in [0.121, 0.144] are stress zone.
NDWI_STRESS_LO, NDWI_STRESS_HI = 0.121, 0.144

DATA_PATH = Path("data/maryland_soybean_10day_timeseries_long.csv")
YIELD_DISTRICT_AVG_PATH = Path("data/processed_yield/yield_district_averages_by_year.csv")
OUT_DIR = Path("outputs/StressDrivers/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Order: irrigated (Upper Eastern Shore) first, rainfed (Southern) last; others in between.
DISTRICT_ORDER = [
    "UPPER EASTERN SHORE",
    "LOWER EASTERN SHORE",
    "NORTH CENTRAL",
    "WESTERN",
    "SOUTHERN",
]

# High-contrast: each district a distinct hue
DISTRICT_COLORS = {
    "UPPER EASTERN SHORE": "#1565c0",   # blue (irrigated)
    "LOWER EASTERN SHORE": "#00838f",   # cyan
    "NORTH CENTRAL": "#2e7d32",         # green
    "WESTERN": "#ef6c00",               # orange
    "SOUTHERN": "#c62828",              # red (rainfed / stress-prone)
}
OPTIMAL_BAND_COLOR = "#2e7d32"   # green (optimal zone)
STRESS_BAND_COLOR = "#c62828"    # red (stress zone)

# 5-year spans aligned with census years (data is 2008–2024).
# (census_year, year_lo, year_hi, subplot_title)
CENSUS_PERIODS = [
    (2007, 2008, 2012, "2008–2012\n(2007 census)"),
    (2012, 2013, 2017, "2013–2017\n(2012 census)"),
    (2017, 2018, 2022, "2018–2022\n(2017 census)"),
    (2022, 2023, 2024, "2023–2024\n(2022 census)"),
]


def load_r4r6_ndwi() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df["DOY"] = df["date"].dt.dayofyear
    df["Year"] = df["date"].dt.year
    df["NDWI"] = pd.to_numeric(df["NDWI"], errors="coerce")
    df = df[(df["DOY"] >= DOY_R4R6_LO) & (df["DOY"] <= DOY_R4R6_HI)].copy()
    df = df[["County", "Ag_District", "Year", "DOY", "NDWI"]].dropna(subset=["NDWI"])
    # Western: only Garrett County, and only from 2021 (NASS yield for Western is Garrett from 2021).
    western_mask = (df["Ag_District"].str.upper() == "WESTERN")
    keep_western = (df["County"].str.upper() == "GARRETT") & (df["Year"] >= 2021)
    df = df.loc[~western_mask | keep_western].copy()
    return df


def load_first_yield_year_by_district() -> dict[str, int]:
    """First calendar year with NASS yield per district (from processed district averages)."""
    y = pd.read_csv(YIELD_DISTRICT_AVG_PATH)
    y["Year"] = pd.to_numeric(y["Year"], errors="coerce")
    y = y.dropna(subset=["Year"])
    first = y.groupby("District", as_index=False)["Year"].min()
    return dict(zip(first["District"].str.upper(), first["Year"].astype(int)))


def _draw_one_boxplot(
    ax: plt.Axes,
    df: pd.DataFrame,
    title: str,
    districts_to_show: Optional[List[str]] = None,
) -> None:
    """Draw district boxplot + ref lines. If districts_to_show is set, only those districts (order preserved)."""
    order = districts_to_show if districts_to_show is not None else DISTRICT_ORDER
    df = df[df["Ag_District"].isin(order)].copy()
    df["Ag_District"] = pd.Categorical(df["Ag_District"], categories=order, ordered=True)
    df = df.sort_values("Ag_District")

    data = [df.loc[df["Ag_District"] == d, "NDWI"].values for d in order]
    labels = [d.replace(" ", "\n") for d in order]
    n_vals = [len(x) for x in data]

    bp = ax.boxplot(
        data,
        labels=[f"{lab}\n(n={n:,})" for lab, n in zip(labels, n_vals)],
        patch_artist=True,
        showfliers=True,
        widths=0.6,
    )

    for patch, d in zip(bp["boxes"], order):
        patch.set_facecolor(DISTRICT_COLORS.get(d, "#b0b0b0"))
        patch.set_alpha(0.88)

    ax.axhspan(NDWI_OPTIMAL_LO, NDWI_OPTIMAL_HI, color=OPTIMAL_BAND_COLOR, alpha=0.2, zorder=0)
    ax.axhline(NDWI_OPTIMAL_LO, color=OPTIMAL_BAND_COLOR, linestyle="--", linewidth=1.2, alpha=0.7)
    ax.axhline(NDWI_OPTIMAL_HI, color=OPTIMAL_BAND_COLOR, linestyle="--", linewidth=1.2, alpha=0.7)
    ax.axhspan(NDWI_STRESS_LO, NDWI_STRESS_HI, color=STRESS_BAND_COLOR, alpha=0.3, zorder=0)
    ax.axhline(NDWI_STRESS_LO, color=STRESS_BAND_COLOR, linestyle="--", linewidth=1.2, alpha=0.85)
    ax.axhline(NDWI_STRESS_HI, color=STRESS_BAND_COLOR, linestyle="--", linewidth=1.2, alpha=0.85)
    ax.set_ylim(-0.15, 0.75)
    ax.grid(axis="y", alpha=0.4)
    ax.set_ylabel("NDWI")
    ax.set_title(title, fontsize=11, fontweight="bold")


def plot_boxplot(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    _draw_one_boxplot(ax, df, "NDWI at R4–R6 (Beginning Seed, DOY 200–260) by district")
    ax.set_ylabel("NDWI (R4–R6, Beginning Seed)", fontsize=11)
    ax.set_xlabel("Ag District", fontsize=11)
    ax.set_title(
        "NDWI at R4–R6 (Beginning Seed, DOY 200–260) by district\n"
        "Upper Eastern Shore (irrigated) vs Southern (rainfed) vs others",
        fontsize=12,
        fontweight="bold",
    )
    ax.text(len(DISTRICT_ORDER) + 0.38, (NDWI_OPTIMAL_LO + NDWI_OPTIMAL_HI) / 2,
            "Iowa optimal\n0.37–0.58", fontsize=8, color=OPTIMAL_BAND_COLOR, va="center", ha="left", alpha=0.95)
    ax.text(len(DISTRICT_ORDER) + 0.35, (NDWI_STRESS_LO + NDWI_STRESS_HI) / 2,
            "NDWI stress\n0.12–0.14", va="center", fontsize=9, color=STRESS_BAND_COLOR)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close()


# Title and caption for the by-period figure.
BY_PERIOD_TITLE = "NDWI at Beginning Seed (R4–R6) by Maryland District and Census Period"

def plot_boxplot_by_period(df: pd.DataFrame, out_path: Path) -> None:
    first_yield = load_first_yield_year_by_district()
    fig, axes = plt.subplots(2, 2, figsize=(12, 11))
    axes = axes.flatten()
    for ix, (_census, year_lo, year_hi, title) in enumerate(CENSUS_PERIODS):
        # Only include districts that have NASS yield in this period (first yield year <= year_hi).
        districts_in_period = [
            d for d in DISTRICT_ORDER
            if first_yield.get(d, 9999) <= year_hi
        ]
        sub = df[(df["Year"] >= year_lo) & (df["Year"] <= year_hi)]
        sub = sub[sub["Ag_District"].isin(districts_in_period)]
        _draw_one_boxplot(axes[ix], sub, title, districts_to_show=districts_in_period)
    fig.suptitle(BY_PERIOD_TITLE, fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout(rect=[0, 0.03, 1, 0.98])
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    df = load_r4r6_ndwi()
    plot_boxplot(df, OUT_DIR / "NDWI_R4R6_ByDistrict_Boxplot.png")
    print(f"Saved: {OUT_DIR / 'NDWI_R4R6_ByDistrict_Boxplot.png'}")
    plot_boxplot_by_period(df, OUT_DIR / "NDWI_R4R6_ByDistrict_Boxplot_ByCensusPeriod.png")
    print(f"Saved: {OUT_DIR / 'NDWI_R4R6_ByDistrict_Boxplot_ByCensusPeriod.png'}")


if __name__ == "__main__":
    main()
