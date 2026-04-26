#!/usr/bin/env python3
"""
Create a county-level map of Maryland color-coded by agricultural district.

Districts follow the mapping used in PreprocessYieldData:
- WESTERN
- NORTH CENTRAL
- SOUTHERN
- UPPER EASTERN SHORE
- LOWER EASTERN SHORE
"""

import os

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


# County to district mapping (must match USDA NASS mapping used elsewhere)
DISTRICT_COUNTIES = {
    "WESTERN": {"Allegany", "Garrett"},
    "UPPER EASTERN SHORE": {"Caroline", "Cecil", "Kent", "Queen Anne's", "Talbot"},
    "SOUTHERN": {"Anne Arundel", "Calvert", "Charles", "Prince George's", "St. Mary's"},
    "NORTH CENTRAL": {
        "Baltimore",
        "Baltimore City",
        "Carroll",
        "Frederick",
        "Harford",
        "Howard",
        "Montgomery",
        "Washington",
    },
    "LOWER EASTERN SHORE": {"Dorchester", "Somerset", "Wicomico", "Worcester"},
}


def build_county_to_district():
    mapping = {}
    for district, counties in DISTRICT_COUNTIES.items():
        for c in counties:
            mapping[c.upper()] = district
    return mapping


def load_maryland_counties():
    """
    Load Maryland county geometries from US Census cartographic boundaries.

    We use the 1:5m generalized county layer and filter to STATEFP == '24' (Maryland).
    """
    url = (
        "https://www2.census.gov/geo/tiger/GENZ2023/shp/"
        "cb_2023_us_county_5m.zip"
    )
    gdf = gpd.read_file(url)
    # Maryland FIPS is 24
    md = gdf[gdf["STATEFP"] == "24"].copy()
    # Normalize county names to align with DISTRICT_COUNTIES keys
    md["NAME_NORM"] = (
        md["NAME"]
        .str.replace("County", "", regex=False)
        .str.strip()
        .str.replace("Saint Marys", "St. Mary's", regex=False)
        .str.replace("Queen Annes", "Queen Anne's", regex=False)
    )
    return md


def assign_districts(md_gdf):
    county_to_district = build_county_to_district()
    md_gdf["District"] = md_gdf["NAME_NORM"].str.upper().map(county_to_district)
    # Check for any counties without a district assignment
    missing = md_gdf[md_gdf["District"].isna()]
    if not missing.empty:
        print("Warning: the following counties have no district mapping:")
        print(missing[["NAME_NORM"]])
    return md_gdf


def plot_maryland_districts(md_gdf, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Define a stable color mapping for the five districts
    districts = [
        "WESTERN",
        "NORTH CENTRAL",
        "SOUTHERN",
        "UPPER EASTERN SHORE",
        "LOWER EASTERN SHORE",
    ]
    colors = ["#FFD700", "#FF6B6B", "#90EE90", "#9370DB", "#4ECDC4"]
    cmap = ListedColormap(colors)
    district_to_idx = {d: i for i, d in enumerate(districts)}

    md_gdf["district_idx"] = md_gdf["District"].map(district_to_idx)

    fig, ax = plt.subplots(figsize=(8, 10))
    md_gdf.plot(
        column="district_idx",
        cmap=cmap,
        linewidth=0.5,
        edgecolor="black",
        ax=ax,
        legend=False,
    )

    # Build legend manually so labels are ordered and human-readable
    handles = []
    for d, color in zip(districts, colors):
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker="s",
                color="none",
                markerfacecolor=color,
                markeredgecolor="black",
                markersize=10,
                label=d,
            )
        )
    ax.legend(
        handles=handles,
        title="Agricultural District",
        loc="lower left",
        frameon=True,
    )

    ax.set_axis_off()
    ax.set_title(
        "Maryland Counties by Agricultural District",
        fontsize=14,
        fontweight="bold",
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved map to {output_path}")


def main():
    md = load_maryland_counties()
    md = assign_districts(md)
    output_path = os.path.join("outputs", "Maps", "Maryland_Counties_By_District.png")
    plot_maryland_districts(md, output_path)


if __name__ == "__main__":
    main()

