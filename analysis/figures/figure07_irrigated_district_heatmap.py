#!/usr/bin/env python3
"""
Heatmap of irrigated soybean acres (harvested) by Maryland ag district and census year.

Input:
  data/nass/IrrigatedAcresHarvestedByCounty.csv

Output:
  outputs/Irrigation/Irrigated_Acres_District_CensusYears_Heatmap.png  (values in ha, SI)
  outputs/Irrigation/Irrigated_Acres_District_CensusYears_Table.csv      (acres, source units)
  outputs/Irrigation/Irrigated_Hectares_District_CensusYears_Table.csv (ha, SI)
"""

from __future__ import annotations

import os
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# SI: 1 acre = 4046.856422 m²; 1 ha = 10,000 m² → 1 ac = 0.404685642 ha
ACRE_TO_HA = 0.404685642

OUT_DIR = "outputs/Irrigation"
os.makedirs(OUT_DIR, exist_ok=True)

CENSUS_YEARS = [1997, 2002, 2007, 2012, 2017, 2022]
DISTRICT_ORDER = ["WESTERN", "NORTH CENTRAL", "SOUTHERN", "LOWER EASTERN SHORE", "UPPER EASTERN SHORE"]


def _to_number(val) -> float:
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if "(D" in s:
        return np.nan
    s = s.replace(",", "").strip()
    s = re.sub(r"[^\d\.\-]", "", s)
    return float(s) if s else np.nan


def main() -> None:
    df = pd.read_csv("data/nass/IrrigatedAcresHarvestedByCounty.csv")
    df = df[(df["State"] == "MARYLAND") & (df["Geo Level"] == "COUNTY") & (df["Period"] == "YEAR")].copy()
    df = df[df["Program"].astype(str).str.upper() == "CENSUS"]
    df = df[df["Commodity"] == "SOYBEANS"]
    df = df[df["Data Item"].astype(str).str.contains("IRRIGATED - ACRES HARVESTED", na=False)]

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df[df["Year"].isin(CENSUS_YEARS)].copy()
    df["district"] = df["Ag District"].astype(str).str.upper().str.strip()
    df["acres"] = df["Value"].map(_to_number)

    # Aggregate counties to district totals for each census year
    agg = df.groupby(["district", "Year"], as_index=False)["acres"].sum(min_count=1)

    table = (
        agg.pivot(index="district", columns="Year", values="acres")
        .reindex(DISTRICT_ORDER)
        .reindex(columns=CENSUS_YEARS)
    )
    table_out = os.path.join(OUT_DIR, "Irrigated_Acres_District_CensusYears_Table.csv")
    table.to_csv(table_out)

    table_ha = table * ACRE_TO_HA
    table_ha_out = os.path.join(OUT_DIR, "Irrigated_Hectares_District_CensusYears_Table.csv")
    table_ha.to_csv(table_ha_out)

    # Plot heatmap (SI: hectares)
    fig, ax = plt.subplots(figsize=(13, 5.8))

    data = table_ha.to_numpy(dtype=float)
    masked = np.ma.masked_invalid(data)

    cmap = mpl.cm.Blues.copy()
    cmap.set_bad(color="#f0f0f0")  # suppressed/NA

    vmax = np.nanmax(data) if np.isfinite(np.nanmax(data)) else 1.0
    im = ax.imshow(masked, aspect="auto", cmap=cmap, vmin=0, vmax=vmax)

    # Axis labels/ticks
    ax.set_title(
        "Irrigated soybean area harvested by district and census year (ha)",
        fontsize=14,
        fontweight="bold",
        pad=12,
    )
    ax.set_ylabel("Agricultural District", fontweight="bold")
    ax.set_xlabel("Census year", fontweight="bold")

    ax.set_yticks(np.arange(len(DISTRICT_ORDER)))
    ax.set_yticklabels(DISTRICT_ORDER)
    ax.set_xticks(np.arange(len(CENSUS_YEARS)))
    ax.set_xticklabels([str(y) for y in CENSUS_YEARS])

    # Gridlines between cells
    ax.set_xticks(np.arange(-0.5, len(CENSUS_YEARS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(DISTRICT_ORDER), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Annotate values
    for i in range(len(DISTRICT_ORDER)):
        for j in range(len(CENSUS_YEARS)):
            v = data[i, j]
            if np.isnan(v):
                txt = "D"
                color = "#555555"
            else:
                if v < 10:
                    txt = f"{v:.1f}"
                else:
                    txt = f"{int(round(v)):,}"
                # contrast based on intensity
                color = "white" if v > 0.6 * vmax else "black"
            ax.text(j, i, txt, ha="center", va="center", fontsize=9, fontweight="bold", color=color)

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Irrigated area (ha, harvested)", fontweight="bold")

    plt.tight_layout()
    out = os.path.join(OUT_DIR, "Irrigated_Acres_District_CensusYears_Heatmap.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved: {out}")
    print(f"Saved: {table_out}")
    print(f"Saved: {table_ha_out}")


if __name__ == "__main__":
    main()

