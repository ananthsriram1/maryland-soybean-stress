#!/usr/bin/env python3
"""
Dual-axis time series "scissors" plot for a severe drought year:
  - Non-irrigated district (Southern Maryland): NDVI plateau + NDWI decline → "Invisible Stress Window"
  - Irrigated district (Lower Eastern Shore): contrast (NDWI stays higher).

Left Y-axis: NDVI (plateau 0.8–0.9 in R4–R6).
Right Y-axis: NDWI (decline, crossing 0.12 stress threshold).
Benchmark: Green band 0.37–0.58 (NDWI optimal) on right axis.
Invisible Stress Window (DOY 210–250) described in caption only, not drawn.

Input: data/maryland_soybean_10day_timeseries_long.csv
Output: outputs/StressDrivers/figures/NDVI_NDWI_Scissors_DualAxis_2012_2024.png (2x2: 2012 top, 2024 bottom)
"""

from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

OUT_DIR = Path("outputs/StressDrivers/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Reproductive window (R4–R6, August) for "Invisible Stress Window" shading
DOY_WINDOW_START, DOY_WINDOW_END = 210, 250
NDWI_OPTIMAL_LO, NDWI_OPTIMAL_HI = 0.37, 0.58
NDWI_STRESS_LO, NDWI_STRESS_HI = 0.121, 0.144
NON_IRRIGATED_DISTRICT = "SOUTHERN"
IRRIGATED_DISTRICT = "LOWER EASTERN SHORE"

# High-contrast palette: clearly distinct hues (no green for NDVI)
COLOR_NDVI = "#6a1b9a"           # purple (vegetation / canopy)
COLOR_NDWI = "#1565c0"          # strong blue (water)
COLOR_OPTIMAL_FILL = "#81c784"   # light green band (optimal zone)
COLOR_OPTIMAL_LINE = "#2e7d32"   # green (optimal bounds)
COLOR_STRESS = "#c62828"         # clear red (stress / alert)

def load_district_year_curves() -> pd.DataFrame:
    """Load 10-day data and aggregate to district-year mean NDVI/NDWI per DOY."""
    df = pd.read_csv("data/maryland_soybean_10day_timeseries_long.csv", parse_dates=["date"])
    df["DOY"] = df["date"].dt.dayofyear
    df["Year"] = df["date"].dt.year
    df["Ag_District"] = df["Ag_District"].astype(str).str.upper().str.strip()
    df["NDVI"] = pd.to_numeric(df["NDVI"], errors="coerce")
    df["NDWI"] = pd.to_numeric(df["NDWI"], errors="coerce")
    df = df.dropna(subset=["DOY", "Year", "Ag_District", "NDVI", "NDWI"])
    # Western: only Garrett from 2021
    western = (df["Ag_District"] == "WESTERN")
    df = df.loc[~(western & ((df["County"].str.upper() != "GARRETT") | (df["Year"] < 2021)))].copy()
    agg = df.groupby(["Ag_District", "Year", "DOY"], as_index=False).agg(NDVI=("NDVI", "mean"), NDWI=("NDWI", "mean"))
    return agg


def smooth_curve(g: pd.DataFrame, col: str, window: int = 3) -> pd.Series:
    """Rolling median for NDVI, rolling mean for NDWI (smoother district-level curves)."""
    s = g[col].rolling(window, center=True, min_periods=1).median()
    return s


def plot_one_dual_axis(
    ax_left: plt.Axes,
    g: pd.DataFrame,
    title: str,
    subtitle: str,
    show_legend: bool = True,
) -> None:
    """Draw dual-axis scissors on a single axes (left = NDVI, right = NDWI). No Invisible Stress Window shading (see caption)."""
    g = g.sort_values("DOY").reset_index(drop=True)
    doy = g["DOY"].values
    ndvi = smooth_curve(g, "NDVI").values
    ndwi = smooth_curve(g, "NDWI").values

    # Left axis: NDVI (purple)
    ax_left.set_ylabel("NDVI", color=COLOR_NDVI, fontsize=11, fontweight="bold")
    ax_left.tick_params(axis="y", labelcolor=COLOR_NDVI)
    ax_left.set_ylim(-0.05, 1.02)
    ax_left.plot(doy, ndvi, color=COLOR_NDVI, linewidth=2.5, label="NDVI (R4–R6 plateau)")
    ax_left.set_xlim(150, 280)
    ax_left.set_xlabel("Day of year (DOY)")
    ax_left.grid(True, alpha=0.25)

    # Right axis: NDWI (teal, same color family as NDVI)
    ax_right = ax_left.twinx()
    ax_right.set_ylabel("NDWI", color=COLOR_NDWI, fontsize=11, fontweight="bold")
    ax_right.tick_params(axis="y", labelcolor=COLOR_NDWI)
    ax_right.set_ylim(-0.12, 0.75)
    ax_right.plot(doy, ndwi, color=COLOR_NDWI, linewidth=2.5, label="NDWI (decline → stress)")
    # Optimal band: subtle sage (no bright green clash)
    ax_right.axhspan(NDWI_OPTIMAL_LO, NDWI_OPTIMAL_HI, color=COLOR_OPTIMAL_FILL, alpha=0.25, zorder=0)
    ax_right.axhline(NDWI_OPTIMAL_LO, color=COLOR_OPTIMAL_LINE, linestyle="--", linewidth=1, alpha=0.7)
    ax_right.axhline(NDWI_OPTIMAL_HI, color=COLOR_OPTIMAL_LINE, linestyle="--", linewidth=1, alpha=0.7)
    # Stress window (0.121–0.144), shade only, no text
    ax_right.axhspan(NDWI_STRESS_LO, NDWI_STRESS_HI, color=COLOR_STRESS, alpha=0.3, zorder=0)
    ax_right.axhline(NDWI_STRESS_LO, color=COLOR_STRESS, linestyle="--", linewidth=1.2, alpha=0.85)
    ax_right.axhline(NDWI_STRESS_HI, color=COLOR_STRESS, linestyle="--", linewidth=1.2, alpha=0.85)

    ax_left.set_title(f"{title}\n{subtitle}", fontsize=11, fontweight="bold")
    if show_legend:
        leg_left, _ = ax_left.get_legend_handles_labels()
        leg_right, _ = ax_right.get_legend_handles_labels()
        ax_left.legend(leg_left + leg_right, ["NDVI (R4–R6 plateau)", "NDWI (decline → stress)"], loc="upper right", fontsize=9)


def main() -> None:
    ap = argparse.ArgumentParser(description="Dual-axis NDVI/NDWI scissors (2012 + 2024 in one figure).")
    ap.add_argument("--year", type=int, default=None, help="If set, output only this year (1x2) instead of 2x2 combined.")
    ap.add_argument(
        "--contrast-district",
        type=str,
        default=None,
        help="Override irrigated-comparison district for the right column (default: Lower Eastern Shore). Only used for 2x2 combined output.",
    )
    args = ap.parse_args()

    agg = load_district_year_curves()

    if args.year is not None:
        year = args.year
        non_irr = agg[(agg["Ag_District"] == NON_IRRIGATED_DISTRICT) & (agg["Year"] == year)]
        irr = agg[(agg["Ag_District"] == IRRIGATED_DISTRICT) & (agg["Year"] == year)]
        if non_irr.empty or irr.empty:
            raise ValueError(f"Missing district-year data for {year}.")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        plot_one_dual_axis(ax1, non_irr, f"Non-irrigated: {NON_IRRIGATED_DISTRICT.title()}", f"{year}", show_legend=True)
        plot_one_dual_axis(ax2, irr, f"Irrigated: {IRRIGATED_DISTRICT.title()}", f"{year}", show_legend=True)
        fig.suptitle(f"Dual-axis scissors: NDVI vs NDWI in R4–R6 (Beginning Seed), {year}", fontsize=13, fontweight="bold", y=1.02)
        plt.tight_layout()
        out_png = OUT_DIR / f"NDVI_NDWI_Scissors_DualAxis_{year}.png"
        fig.savefig(out_png, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Saved: {out_png}")
        return

    # Right column: irrigated district or --contrast-district (e.g. Lower Eastern Shore)
    contrast_district = (args.contrast_district or "").strip().upper() or IRRIGATED_DISTRICT
    # Always label the right column as the irrigated comparison (even when a contrast district is supplied).
    contrast_title = f"Irrigated: {contrast_district.title()}"

    # Combined 2x2: row 0 = 2012 (left Non-irrigated, right contrast district), row 1 = 2024
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for iy, year in enumerate([2012, 2024]):
        non_irr = agg[(agg["Ag_District"] == NON_IRRIGATED_DISTRICT) & (agg["Year"] == year)]
        irr = agg[(agg["Ag_District"] == contrast_district) & (agg["Year"] == year)]
        if non_irr.empty or irr.empty:
            raise ValueError(f"Missing district-year data for {year} (contrast={contrast_district}).")
        plot_one_dual_axis(
            axes[iy, 0], non_irr,
            f"Non-irrigated: {NON_IRRIGATED_DISTRICT.title()}",
            f"{year}",
            show_legend=(iy == 0),
        )
        plot_one_dual_axis(
            axes[iy, 1], irr,
            contrast_title,
            f"{year}",
            show_legend=(iy == 0),
        )

    fig.suptitle(
        "Dual-axis scissors: NDVI vs NDWI in R4–R6 (Beginning Seed), 2012 and 2024",
        fontsize=13,
        fontweight="bold",
        y=1.01,
    )
    plt.tight_layout(rect=[0, 0.06, 1, 0.98])
    if contrast_district == IRRIGATED_DISTRICT:
        out_png = OUT_DIR / "NDVI_NDWI_Scissors_DualAxis_2012_2024.png"
    else:
        suffix = "LowerEastern" if contrast_district == "LOWER EASTERN SHORE" else contrast_district.replace(" ", "_")
        out_png = OUT_DIR / f"NDVI_NDWI_Scissors_DualAxis_2012_2024_{suffix}.png"
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_png}")


if __name__ == "__main__":
    main()
