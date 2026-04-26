#!/usr/bin/env python3
"""
Visual variants of the district-average soil composition heatmap
(Loam, Silty Loam, Sandy Loam) for readability comparison.

Includes YlOrRd + white label boxes (hybrid of stroke-based YlOrRd and Viridis boxed labels).

Outputs: outputs/SoilCompositionBand5/variants/Variant_*.png
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import cm


DISTRICT_ORDER = [
    "WESTERN",
    "NORTH CENTRAL",
    "SOUTHERN",
    "UPPER EASTERN SHORE",
    "LOWER EASTERN SHORE",
]

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


def load_district_matrix():
    soil_path = "data/processed_band5/maryland_soil_composition_processed_band5_2020band5.csv"
    mapping_path = "data/processed_band5/soil_type_mapping_band5.csv"
    soil = pd.read_csv(soil_path)
    mapping = pd.read_csv(mapping_path)
    code_to_name = dict(zip(mapping["Code"], mapping["Name"]))
    pct_cols = [f"{code}_Percentage" for code in mapping["Code"] if f"{code}_Percentage" in soil.columns]
    nonzero_cols = [c for c in pct_cols if (soil[c].abs() > 1e-9).any()]
    nonzero_codes = [c.replace("_Percentage", "") for c in nonzero_cols]
    county_df = soil[["County"] + nonzero_cols].copy()
    county_df["District"] = county_df["County"].map(COUNTY_TO_DISTRICT)
    county_df = county_df.dropna(subset=["District"])
    rename_map = {f"{code}_Percentage": code_to_name.get(code, code) for code in nonzero_codes}
    county_df = county_df.rename(columns=rename_map)
    soil_name_cols = [rename_map[f"{code}_Percentage"] for code in nonzero_codes]
    keep_soils = ["Loam", "Silty Loam", "Sandy Loam"]
    soil_name_cols = [c for c in soil_name_cols if c in keep_soils]
    county_df["District"] = pd.Categorical(county_df["District"], categories=DISTRICT_ORDER, ordered=True)
    county_df = county_df.sort_values(["District", "County"]).reset_index(drop=True)
    district_avg = (
        county_df.groupby("District", observed=True)[soil_name_cols]
        .mean()
        .reindex(DISTRICT_ORDER)
    )
    return district_avg


def contrast_text(ax, data: pd.DataFrame, vmin: float, vmax: float, cmap_name: str):
    cmap = cm.get_cmap(cmap_name)
    vals = data.to_numpy()
    nrows, ncols = vals.shape
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
            norm = 0.0 if vmax == vmin else (v - vmin) / (vmax - vmin)
            r, g, b, _ = cmap(np.clip(norm, 0, 1))
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            if lum > 0.55:
                t.set_color("black")
                t.set_path_effects([pe.withStroke(linewidth=3, foreground="white")])
            else:
                t.set_color("white")
                t.set_path_effects([pe.withStroke(linewidth=3, foreground="black")])


def save_variant(
    district_avg: pd.DataFrame,
    out_path: str,
    *,
    cmap: str,
    vmin: float,
    vmax: float,
    annot_size: int,
    linewidth: float,
    title: str,
    use_bbox: bool = False,
):
    fig, ax = plt.subplots(figsize=(11, 5.2))
    annot_kws = {"size": annot_size, "weight": "bold"}
    if use_bbox:
        annot_kws["bbox"] = dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#333333", alpha=0.92)

    sns.heatmap(
        district_avg,
        ax=ax,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        annot=True,
        fmt=".1f",
        cbar=True,
        cbar_kws={"label": "Soil percentage (%)", "shrink": 0.85},
        linewidths=linewidth,
        linecolor="white",
        annot_kws=annot_kws,
    )
    if not use_bbox:
        contrast_text(ax, district_avg, vmin=vmin, vmax=vmax, cmap_name=cmap)
    else:
        for t in ax.texts:
            t.set_color("#111111")
            t.set_path_effects([])

    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=30, labelsize=11)
    ax.tick_params(axis="y", labelsize=11)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def main():
    district_avg = load_district_matrix()
    out_dir = "outputs/SoilCompositionBand5/variants"
    os.makedirs(out_dir, exist_ok=True)

    # Fixed 0–100 scale so colorbar matches full percentage range (clearer than data-max)
    vmin, vmax = 0.0, 100.0

    base = "Band-5 soybean soil composition (2020) — district mean %"

    save_variant(
        district_avg,
        os.path.join(out_dir, "Variant_01_Viridis_0_100_boldstroke.png"),
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        annot_size=13,
        linewidth=1.2,
        title=f"{base}\n(1) Viridis, 0–100 % scale, bold contrast stroke",
    )
    save_variant(
        district_avg,
        os.path.join(out_dir, "Variant_02_Cividis_0_100.png"),
        cmap="cividis",
        vmin=vmin,
        vmax=vmax,
        annot_size=13,
        linewidth=1.2,
        title=f"{base}\n(2) Cividis (colorblind-friendly), 0–100 %",
    )
    save_variant(
        district_avg,
        os.path.join(out_dir, "Variant_03_YlOrRd_0_100.png"),
        cmap="YlOrRd",
        vmin=vmin,
        vmax=vmax,
        annot_size=13,
        linewidth=1.2,
        title=f"{base}\n(3) Yellow–Orange–Red sequential, 0–100 %",
    )
    save_variant(
        district_avg,
        os.path.join(out_dir, "Variant_04_Blues_0_100.png"),
        cmap="Blues",
        vmin=vmin,
        vmax=vmax,
        annot_size=13,
        linewidth=1.2,
        title=f"{base}\n(4) Blues sequential, 0–100 %",
    )
    save_variant(
        district_avg,
        os.path.join(out_dir, "Variant_05_Viridis_white_label_boxes.png"),
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        annot_size=12,
        linewidth=1.5,
        title=f"{base}\n(5) Viridis + white rounded labels (max number clarity)",
        use_bbox=True,
    )
    # Hybrids: Variant 03 (YlOrRd) × Variant 05 (white rounded label boxes)
    save_variant(
        district_avg,
        os.path.join(out_dir, "Variant_06_YlOrRd_white_label_boxes.png"),
        cmap="YlOrRd",
        vmin=vmin,
        vmax=vmax,
        annot_size=12,
        linewidth=1.5,
        title=f"{base}\n(6) YlOrRd + white rounded labels (mix of 3 & 5)",
        use_bbox=True,
    )
    save_variant(
        district_avg,
        os.path.join(out_dir, "Variant_07_YlOrRd_white_label_boxes_larger_font.png"),
        cmap="YlOrRd",
        vmin=vmin,
        vmax=vmax,
        annot_size=14,
        linewidth=1.5,
        title=f"{base}\n(7) Same as (6), larger cell numbers",
        use_bbox=True,
    )


if __name__ == "__main__":
    main()
