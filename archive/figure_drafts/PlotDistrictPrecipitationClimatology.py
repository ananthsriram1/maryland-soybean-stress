#!/usr/bin/env python3
"""
Study-area precipitation summaries (no trend emphasis) for Maryland's 5 districts.
1
Creates two figures using NOAA county precipitation (1997–2025):
Option 1) Boxplots: distribution of yearly totals by district
Option 2) Mean ± SD bars by district

Both are produced for:
- Annual precipitation totals
- Jul–Sep growing-season totals

Input (rebuilt from NOAA 1997–2025 folder):
  data/maryland_precipitation_combined_wide.csv

Outputs:
  outputs/Precipitation/District_Precip_Climatology_Boxplots.png
  outputs/Precipitation/District_Precip_Climatology_MeanSD.png
  outputs/Precipitation/District_Precip_Climatology_Annual_JulSep.csv
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patheffects as pe


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

COUNTY_TO_DISTRICT = {
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


INPUT_PATH = "data/maryland_precipitation_combined_wide.csv"
OUTPUT_DIR = "outputs/Precipitation"

# SI: 1 inch = 25.4 mm (used for decade-blocks figure)
INCH_TO_MM = 25.4

GROW_START_MONTH = 7
GROW_END_MONTH = 9
GROW_LABEL = "Jul–Sep"


def parse_wide_precip(df: pd.DataFrame) -> pd.DataFrame:
    """Convert wide precip (Precip_YYYY-MM columns) to long format."""
    value_cols = [c for c in df.columns if c.startswith("Precip_")]
    if not value_cols:
        raise ValueError("No Precip_YYYY-MM columns found in precipitation CSV.")

    long = df.melt(id_vars=["County"], value_vars=value_cols, var_name="ym", value_name="precip_in")
    long["ym"] = long["ym"].str.replace("Precip_", "", regex=False)
    long["date"] = pd.to_datetime(long["ym"] + "-01", errors="coerce")
    long["Year"] = long["date"].dt.year
    long["Month"] = long["date"].dt.month
    long["precip_in"] = pd.to_numeric(long["precip_in"], errors="coerce")
    return long.dropna(subset=["date"])


def district_year_totals(long: pd.DataFrame) -> pd.DataFrame:
    """District annual and Jul–Sep totals using mean across counties each month."""
    long = long.copy()
    long["District"] = long["County"].map(COUNTY_TO_DISTRICT)
    long = long.dropna(subset=["District"])
    long["District"] = pd.Categorical(long["District"], categories=DISTRICT_ORDER, ordered=True)

    # monthly mean across counties within a district
    dm = (
        long.groupby(["District", "Year", "Month"], as_index=False)["precip_in"]
        .mean()
        .rename(columns={"precip_in": "district_mean_month_in"})
    )

    annual = (
        dm.groupby(["District", "Year"], as_index=False)["district_mean_month_in"]
        .sum()
        .rename(columns={"district_mean_month_in": "Annual_in"})
    )
    julsep = (
        dm[dm["Month"].between(GROW_START_MONTH, GROW_END_MONTH)]
        .groupby(["District", "Year"], as_index=False)["district_mean_month_in"]
        .sum()
        .rename(columns={"district_mean_month_in": "JulSep_in"})
    )
    out = annual.merge(julsep, on=["District", "Year"], how="left")
    # Backward-compatible alias for any downstream code that expects MaySep_in.
    out["MaySep_in"] = out["JulSep_in"]
    return out


def plot_boxplots(df: pd.DataFrame, out_path: str):
    palette = [DISTRICT_COLORS[d] for d in DISTRICT_ORDER]

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

    sns.boxplot(
        data=df,
        x="District",
        y="Annual_in",
        order=DISTRICT_ORDER,
        palette=palette,
        ax=axes[0],
        showfliers=True,
    )
    axes[0].set_title("Annual precipitation by district (1997–2025)", fontsize=14, fontweight="bold")
    axes[0].set_ylabel("Annual precipitation (inches)")
    axes[0].set_xlabel("")
    axes[0].grid(axis="y", alpha=0.25)

    sns.boxplot(
        data=df,
        x="District",
        y="JulSep_in",
        order=DISTRICT_ORDER,
        palette=palette,
        ax=axes[1],
        showfliers=True,
    )
    axes[1].set_title(f"Growing-season precipitation ({GROW_LABEL}) by district (1997–2025)", fontsize=14, fontweight="bold")
    axes[1].set_ylabel(f"{GROW_LABEL} precipitation (inches)")
    axes[1].set_xlabel("Agricultural district")
    axes[1].grid(axis="y", alpha=0.25)
    axes[1].tick_params(axis="x", rotation=20)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_mean_sd(df: pd.DataFrame, out_path: str):
    stats = (
        df.groupby("District", observed=True)
        .agg(
            Annual_mean=("Annual_in", "mean"),
            Annual_sd=("Annual_in", "std"),
            JulSep_mean=("JulSep_in", "mean"),
            JulSep_sd=("JulSep_in", "std"),
        )
        .reindex(DISTRICT_ORDER)
        .reset_index()
    )

    x = np.arange(len(stats["District"]))
    colors = [DISTRICT_COLORS[d] for d in stats["District"]]

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

    axes[0].bar(x, stats["Annual_mean"], yerr=stats["Annual_sd"], color=colors, edgecolor="black", linewidth=0.8, capsize=4)
    axes[0].set_title("Annual precipitation (mean ± SD), 1997–2025", fontsize=14, fontweight="bold")
    axes[0].set_ylabel("Inches")
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(x, stats["JulSep_mean"], yerr=stats["JulSep_sd"], color=colors, edgecolor="black", linewidth=0.8, capsize=4)
    axes[1].set_title(f"{GROW_LABEL} precipitation (mean ± SD), 1997–2025", fontsize=14, fontweight="bold")
    axes[1].set_ylabel("Inches")
    axes[1].grid(axis="y", alpha=0.25)

    axes[1].set_xticks(x)
    axes[1].set_xticklabels(stats["District"], rotation=20, ha="right")
    axes[1].set_xlabel("Agricultural district")

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_mean_sd_enhanced(df: pd.DataFrame, out_path: str):
    """
    More readable Option 2:
    - dot+whisker (mean ± SD)
    - y-axis zoomed to observed range
    - mean value labels
    - statewide reference line (computed from district means)
    """
    stats = (
        df.groupby("District", observed=True)
        .agg(
            Annual_mean=("Annual_in", "mean"),
            Annual_sd=("Annual_in", "std"),
            JulSep_mean=("JulSep_in", "mean"),
            JulSep_sd=("JulSep_in", "std"),
        )
        .reindex(DISTRICT_ORDER)
        .reset_index()
    )

    x = np.arange(len(stats["District"]))
    colors = [DISTRICT_COLORS[d] for d in stats["District"]]

    # Statewide references (simple mean of district means)
    annual_ref = float(stats["Annual_mean"].mean())
    julsep_ref = float(stats["JulSep_mean"].mean())

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

    # --- Annual ---
    axes[0].axhline(annual_ref, color="black", linestyle="--", linewidth=1.5, alpha=0.7, label="Statewide ref (mean of districts)")
    axes[0].errorbar(
        x,
        stats["Annual_mean"],
        yerr=stats["Annual_sd"],
        fmt="o",
        markersize=9,
        color="black",
        ecolor="black",
        elinewidth=1.4,
        capsize=4,
        zorder=3,
    )
    for xi, m, c in zip(x, stats["Annual_mean"], colors):
        axes[0].scatter([xi], [m], s=140, color=c, edgecolor="black", linewidth=0.8, zorder=4)
    for xi, m in zip(x, stats["Annual_mean"]):
        t = axes[0].annotate(
            f"{m:.1f}",
            (xi, m),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#bbbbbb", alpha=0.9),
            zorder=10,
        )
        t.set_path_effects([pe.withStroke(linewidth=2, foreground="white")])
    ymin = float((stats["Annual_mean"] - stats["Annual_sd"]).min())
    ymax = float((stats["Annual_mean"] + stats["Annual_sd"]).max())
    pad = max(0.5, 0.06 * (ymax - ymin))
    axes[0].set_ylim(ymin - pad, ymax + pad)
    axes[0].set_title("Annual precipitation (mean ± SD), 1997–2025", fontsize=14, fontweight="bold")
    axes[0].set_ylabel("Inches")
    axes[0].grid(axis="y", alpha=0.25)
    axes[0].legend(loc="upper left", frameon=True)

    # --- Jul–Sep ---
    axes[1].axhline(julsep_ref, color="black", linestyle="--", linewidth=1.5, alpha=0.7, label="Statewide ref (mean of districts)")
    axes[1].errorbar(
        x,
        stats["JulSep_mean"],
        yerr=stats["JulSep_sd"],
        fmt="o",
        markersize=9,
        color="black",
        ecolor="black",
        elinewidth=1.4,
        capsize=4,
        zorder=3,
    )
    for xi, m, c in zip(x, stats["JulSep_mean"], colors):
        axes[1].scatter([xi], [m], s=140, color=c, edgecolor="black", linewidth=0.8, zorder=4)
    for xi, m in zip(x, stats["JulSep_mean"]):
        t = axes[1].annotate(
            f"{m:.1f}",
            (xi, m),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#bbbbbb", alpha=0.9),
            zorder=10,
        )
        t.set_path_effects([pe.withStroke(linewidth=2, foreground="white")])
    ymin = float((stats["JulSep_mean"] - stats["JulSep_sd"]).min())
    ymax = float((stats["JulSep_mean"] + stats["JulSep_sd"]).max())
    pad = max(0.5, 0.06 * (ymax - ymin))
    axes[1].set_ylim(ymin - pad, ymax + pad)
    axes[1].set_title(f"{GROW_LABEL} precipitation (mean ± SD), 1997–2025", fontsize=14, fontweight="bold")
    axes[1].set_ylabel("Inches")
    axes[1].grid(axis="y", alpha=0.25)

    axes[1].set_xticks(x)
    axes[1].set_xticklabels(stats["District"], rotation=20, ha="right")
    axes[1].set_xlabel("Agricultural district")

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_mean_sd_by_decade_blocks(df: pd.DataFrame, out_path: str):
    """
    Same dot+whisker style, but split into 10-year blocks to show change over time.

    Blocks (anchored to 1997):
      - 1997–2006
      - 2007–2016
      - 2017–2025 (partial)
    """
    d = df.copy()
    d["decade_start"] = 1997 + 10 * ((d["Year"] - 1997) // 10)
    d = d[d["decade_start"].isin([1997, 2007, 2017])].copy()
    d["decade_label"] = d["decade_start"].astype(int).astype(str) + "–" + (d["decade_start"] + 9).astype(int).astype(str)
    d.loc[d["decade_start"] == 2017, "decade_label"] = "2017–2025"

    stats = (
        d.groupby(["District", "decade_start"], observed=True)
        .agg(
            Annual_mean=("Annual_in", "mean"),
            Annual_sd=("Annual_in", "std"),
            JulSep_mean=("JulSep_in", "mean"),
            JulSep_sd=("JulSep_in", "std"),
            N_years=("Year", "nunique"),
        )
        .reset_index()
    )
    stats["District"] = pd.Categorical(stats["District"], categories=DISTRICT_ORDER, ordered=True)
    stats = stats.sort_values(["District", "decade_start"])

    # Convert to SI (mm) for figure
    stats["Annual_mean"] = stats["Annual_mean"] * INCH_TO_MM
    stats["Annual_sd"] = stats["Annual_sd"] * INCH_TO_MM
    stats["JulSep_mean"] = stats["JulSep_mean"] * INCH_TO_MM
    stats["JulSep_sd"] = stats["JulSep_sd"] * INCH_TO_MM

    x = np.arange(len(DISTRICT_ORDER))
    decade_order = [1997, 2007, 2017]
    decade_colors = {1997: "#1f77b4", 2007: "#ff7f0e", 2017: "#2ca02c"}
    offsets = {1997: -0.22, 2007: 0.0, 2017: 0.22}

    # Reference lines: overall mean across all districts (per panel), in mm
    annual_ref = float(d["Annual_in"].mean()) * INCH_TO_MM
    julsep_ref = float(d["JulSep_in"].mean()) * INCH_TO_MM

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

    # Helper to plot a panel
    def plot_panel(ax, mean_col, sd_col, ref, title, ylabel):
        ax.axhline(ref, color="black", linestyle="--", linewidth=1.5, alpha=0.7, label="Statewide ref (mean of all district-years)")
        for dec in decade_order:
            sub = stats[stats["decade_start"] == dec].set_index("District").reindex(DISTRICT_ORDER)
            y = sub[mean_col].to_numpy(dtype=float)
            yerr = sub[sd_col].to_numpy(dtype=float)

            # If SD is NaN (e.g., single year), set to 0 for plotting
            yerr = np.where(np.isfinite(yerr), yerr, 0.0)

            ax.errorbar(
                x + offsets[dec],
                y,
                yerr=yerr,
                fmt="o",
                markersize=7,
                color="black",
                ecolor="black",
                elinewidth=1.2,
                capsize=3,
                zorder=3,
            )
            ax.scatter(
                x + offsets[dec],
                y,
                s=120,
                color=decade_colors[dec],
                edgecolor="black",
                linewidth=0.8,
                zorder=4,
                label=sub.index[0] if False else None,  # noop; legend handled below
            )

        # Add labels for the latest block only (keeps plot readable)
        latest = stats[stats["decade_start"] == 2017].set_index("District").reindex(DISTRICT_ORDER)
        y_latest = latest[mean_col].to_numpy(dtype=float)
        for xi, yi in zip(x + offsets[2017], y_latest):
            if not np.isfinite(yi):
                continue
            ax.annotate(
                f"{yi:.0f}",
                (xi, yi),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#bbbbbb", alpha=0.9),
                zorder=10,
            )

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.25)

    plot_panel(
        axes[0],
        mean_col="Annual_mean",
        sd_col="Annual_sd",
        ref=annual_ref,
        title="Annual precipitation by district (mean ± SD) by 10-year blocks",
        ylabel="Precipitation (mm)",
    )
    plot_panel(
        axes[1],
        mean_col="JulSep_mean",
        sd_col="JulSep_sd",
        ref=julsep_ref,
        title=f"{GROW_LABEL} precipitation by district (mean ± SD) by 10-year blocks",
        ylabel="Precipitation (mm)",
    )

    axes[1].set_xticks(x)
    axes[1].set_xticklabels(DISTRICT_ORDER, rotation=20, ha="right")
    axes[1].set_xlabel("Agricultural district")

    # Custom legend (decades + reference)
    handles = [
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor=decade_colors[1997], markeredgecolor="black", markersize=8, linestyle="none", label="1997–2006"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor=decade_colors[2007], markeredgecolor="black", markersize=8, linestyle="none", label="2007–2016"),
        plt.Line2D([0], [0], marker="o", color="black", markerfacecolor=decade_colors[2017], markeredgecolor="black", markersize=8, linestyle="none", label="2017–2025"),
        plt.Line2D([0], [0], color="black", linestyle="--", linewidth=1.5, label="Statewide ref"),
    ]
    axes[0].legend(handles=handles, loc="upper left", frameon=True, ncol=2)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid")

    wide = pd.read_csv(INPUT_PATH)
    long = parse_wide_precip(wide)
    dy = district_year_totals(long)

    # Save table used for plots
    out_csv = os.path.join(OUTPUT_DIR, "District_Precip_Climatology_Annual_JulSep.csv")
    dy.sort_values(["District", "Year"]).to_csv(out_csv, index=False)
    # Backward-compatible filename (contents now reflect Jul–Sep).
    dy.sort_values(["District", "Year"]).to_csv(
        os.path.join(OUTPUT_DIR, "District_Precip_Climatology_Annual_MaySep.csv"),
        index=False,
    )

    plot_boxplots(dy, os.path.join(OUTPUT_DIR, "District_Precip_Climatology_Boxplots.png"))
    plot_mean_sd(dy, os.path.join(OUTPUT_DIR, "District_Precip_Climatology_MeanSD.png"))
    plot_mean_sd_enhanced(dy, os.path.join(OUTPUT_DIR, "District_Precip_Climatology_MeanSD_Enhanced.png"))
    plot_mean_sd_by_decade_blocks(dy, os.path.join(OUTPUT_DIR, "District_Precip_Climatology_MeanSD_ByDecadeBlocks.png"))


if __name__ == "__main__":
    main()

