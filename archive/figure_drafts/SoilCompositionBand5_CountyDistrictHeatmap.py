#!/usr/bin/env python3
"""
Band-5 Soybean Soil Composition: County + District summary heatmap (single figure).

Creates one publication-style figure that includes:
1) District-average soil composition (%)
2) County-level soil composition (%) grouped by district

Notes:
- Uses 2020 band5 processed soil data by default.
- Drops soil types that are 0.0 across all counties.
- Uses full soil names (e.g., 'Loam' instead of 'Lo').
"""

import os

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import cm


# Consistent district colors used elsewhere in the repo
DISTRICT_COLORS = {
    "NORTH CENTRAL": "#FF6B6B",
    "SOUTHERN": "#90EE90",
    "LOWER EASTERN SHORE": "#4ECDC4",
    "UPPER EASTERN SHORE": "#9370DB",
    "WESTERN": "#FFD700",
}

DISTRICT_ORDER = [
    "WESTERN",
    "NORTH CENTRAL",
    "SOUTHERN",
    "UPPER EASTERN SHORE",
    "LOWER EASTERN SHORE",
]

# County to district mapping (matches PreprocessYieldData + soil plotting scripts)
COUNTY_TO_DISTRICT = {
    "Allegany": "WESTERN",
    "Anne Arundel": "SOUTHERN",
    "Baltimore": "NORTH CENTRAL",
    "Baltimore City": "NORTH CENTRAL",
    "Calvert": "SOUTHERN",
    "Caroline": "UPPER EASTERN SHORE",
    "Carroll": "NORTH CENTRAL",
    "Cecil": "UPPER EASTERN SHORE",
    "Charles": "SOUTHERN",
    "Dorchester": "LOWER EASTERN SHORE",
    "Frederick": "NORTH CENTRAL",
    "Garrett": "WESTERN",
    "Harford": "NORTH CENTRAL",
    "Howard": "NORTH CENTRAL",
    "Kent": "UPPER EASTERN SHORE",
    "Montgomery": "NORTH CENTRAL",
    "Prince George's": "SOUTHERN",
    "Queen Anne's": "UPPER EASTERN SHORE",
    "Somerset": "LOWER EASTERN SHORE",
    "St. Mary's": "SOUTHERN",
    "Talbot": "UPPER EASTERN SHORE",
    "Washington": "NORTH CENTRAL",
    "Wicomico": "LOWER EASTERN SHORE",
    "Worcester": "LOWER EASTERN SHORE",
}


def _apply_contrast_text(ax, data: pd.DataFrame, vmin: float, vmax: float, cmap_name: str = "viridis"):
    """
    Seaborn applies one annot_kws to all text, so we post-process labels to ensure
    readability by switching text color based on the underlying cell color.
    """
    cmap = cm.get_cmap(cmap_name)
    vals = data.to_numpy()
    nrows, ncols = vals.shape

    # Seaborn inserts texts in row-major order
    text_i = 0
    for i in range(nrows):
        for j in range(ncols):
            if text_i >= len(ax.texts):
                return
            t = ax.texts[text_i]
            text_i += 1

            v = vals[i, j]
            if np.isnan(v):
                continue

            # Normalize and get background color
            if vmax == vmin:
                norm = 0.0
            else:
                norm = (v - vmin) / (vmax - vmin)
            r, g, b, _ = cmap(np.clip(norm, 0, 1))
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

            if luminance > 0.6:
                t.set_color("black")
                t.set_path_effects([pe.withStroke(linewidth=2.5, foreground="white")])
            else:
                t.set_color("white")
                t.set_path_effects([pe.withStroke(linewidth=2.5, foreground="black")])


def main():
    sns.set_theme(style="white")

    soil_path = "data/processed_band5/maryland_soil_composition_processed_band5_2020band5.csv"
    mapping_path = "data/processed_band5/soil_type_mapping_band5.csv"
    out_dir = "outputs/SoilCompositionBand5"
    os.makedirs(out_dir, exist_ok=True)

    soil = pd.read_csv(soil_path)
    mapping = pd.read_csv(mapping_path)

    # Determine which soil codes are present and non-zero
    code_to_name = dict(zip(mapping["Code"], mapping["Name"]))
    pct_cols = [f"{code}_Percentage" for code in mapping["Code"] if f"{code}_Percentage" in soil.columns]

    # Drop all-zero soil types across all counties
    nonzero_cols = [c for c in pct_cols if (soil[c].abs() > 1e-9).any()]
    nonzero_codes = [c.replace("_Percentage", "") for c in nonzero_cols]

    # Create a county x soil dataframe with full names as columns
    county_df = soil[["County"] + nonzero_cols].copy()
    county_df["District"] = county_df["County"].map(COUNTY_TO_DISTRICT)
    county_df = county_df.dropna(subset=["District"])

    rename_map = {f"{code}_Percentage": code_to_name.get(code, code) for code in nonzero_codes}
    county_df = county_df.rename(columns=rename_map)

    soil_name_cols = [rename_map[f"{code}_Percentage"] for code in nonzero_codes]

    # Keep only the dominant soil types for cleaner figures
    keep_soils = ["Loam", "Silty Loam", "Sandy Loam"]
    soil_name_cols = [c for c in soil_name_cols if c in keep_soils]
    if not soil_name_cols:
        raise RuntimeError(f"None of the requested soil types were found: {keep_soils}")

    # Sort counties by district (and alphabetically within district)
    county_df["District"] = pd.Categorical(county_df["District"], categories=DISTRICT_ORDER, ordered=True)
    county_df = county_df.sort_values(["District", "County"]).reset_index(drop=True)

    # District averages (mean % across counties in district)
    district_avg = (
        county_df.groupby("District", observed=True)[soil_name_cols]
        .mean()
        .reindex(DISTRICT_ORDER)
    )

    # Build a district color strip for the county heatmap rows
    district_strip_colors = [DISTRICT_COLORS.get(d, "#808080") for d in county_df["District"].astype(str)]

    # ----- FIGURE 1: District averages (color + numbers) -----
    vmax = float(max(district_avg.max().max(), county_df[soil_name_cols].max().max()))
    vmin = 0.0

    fig1, ax1 = plt.subplots(figsize=(12, 4.2))
    sns.heatmap(
        district_avg,
        ax=ax1,
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        annot=True,
        fmt=".1f",
        cbar=True,
        cbar_kws={"label": "Soil Percentage (%)"},
        linewidths=0.6,
        linecolor="white",
        annot_kws={"size": 10},
    )
    _apply_contrast_text(ax1, district_avg, vmin=vmin, vmax=vmax, cmap_name="viridis")
    ax1.set_title("Band-5 Soybean Soil Composition (2020)\nDistrict average percentage by soil type", fontsize=14, fontweight="bold", pad=10)
    ax1.set_xlabel("")
    ax1.set_ylabel("")
    ax1.tick_params(axis="x", rotation=25)
    ax1.tick_params(axis="y", rotation=0)
    out_path1 = os.path.join(out_dir, "District_Average_Soil_Distribution_Band5_2020.png")
    plt.tight_layout()
    plt.savefig(out_path1, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path1}")

    # ----- FIGURE 2: County distributions (color + numbers) -----
    county_mat = county_df.set_index("County")[soil_name_cols]
    fig2 = plt.figure(figsize=(16, max(9, 0.55 * len(county_mat))))
    gs2 = fig2.add_gridspec(nrows=1, ncols=2, width_ratios=[0.12, 1], wspace=0.02)
    ax_strip = fig2.add_subplot(gs2[0, 0])
    ax2 = fig2.add_subplot(gs2[0, 1])

    sns.heatmap(
        county_mat,
        ax=ax2,
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        annot=True,
        fmt=".1f",
        cbar=True,
        cbar_kws={"label": "Soil Percentage (%)", "shrink": 0.85, "pad": 0.02},
        linewidths=0.35,
        linecolor="white",
        annot_kws={"size": 7},
    )
    _apply_contrast_text(ax2, county_mat, vmin=vmin, vmax=vmax, cmap_name="viridis")
    ax2.set_title("Band-5 Soybean Soil Composition (2020)\nCounty percentage by soil type (grouped by district)", fontsize=14, fontweight="bold", pad=10)
    ax2.set_xlabel("")
    ax2.set_ylabel("")
    ax2.tick_params(axis="x", rotation=25)
    ax2.tick_params(axis="y", rotation=0)

    # District separators (horizontal lines) in county heatmap
    start = 0
    for d in DISTRICT_ORDER:
        n = int((county_df["District"].astype(str) == d).sum())
        if n == 0:
            continue
        start += n
        ax2.axhline(start, color="black", linewidth=1.2)

    # Left strip: district colors aligned to county rows
    ax_strip.set_xlim(0, 1)
    ax_strip.set_ylim(0, len(county_mat))
    ax_strip.invert_yaxis()
    for i, color in enumerate(district_strip_colors):
        ax_strip.add_patch(plt.Rectangle((0, i), 1, 1, facecolor=color, edgecolor="white", linewidth=0.5))
    ax_strip.set_xticks([])
    ax_strip.set_yticks([])
    ax_strip.set_title("District", fontsize=10)

    handles = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=DISTRICT_COLORS[d], markeredgecolor="black", markersize=10, label=d)
        for d in DISTRICT_ORDER
    ]
    # Put district legend above the plot (so it never overlaps the colorbar)
    fig2.legend(
        handles=handles,
        title="Agricultural District",
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        frameon=True,
    )

    out_path2 = os.path.join(out_dir, "County_Soil_Distribution_Band5_2020.png")
    plt.tight_layout()
    plt.savefig(out_path2, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path2}")


if __name__ == "__main__":
    main()

