#!/usr/bin/env python3
"""
Compare soybean yield in drought conditions between counties with vs without irrigation
using census irrigated acres harvested to label irrigation status for subsequent years.

Uses:
  - Irrigation (census years): data/nass/IrrigatedAcresHarvestedByCounty.csv
  - Yield (annual):           data/nass/Soybean_Yield_BU:Acre_By_County.csv
  - Drought aggregates:       data/processed_drought/drought_aggregates_county_year.csv

Outputs:
  - outputs/IrrigationVsDroughtYield/county_year_merged.csv
  - outputs/IrrigationVsDroughtYield/summary_by_year_droughtclass.csv
  - outputs/IrrigationVsDroughtYield/summary_overall_droughtclass.csv
  - outputs/IrrigationVsDroughtYield/yield_by_irrigation_in_drought_boxplots.png
  - outputs/IrrigationVsDroughtYield/yield_vs_pdsi_scatter.png
  - outputs/IrrigationVsDroughtYield/yield_vs_pdsi_scatter_2017_2021.png
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = Path("outputs/IrrigationVsDroughtYield")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CENSUS_YEARS = [1997, 2002, 2007, 2012, 2017, 2022]


def normalize_county_name(name: str) -> str:
    s = str(name).upper().strip()
    s = s.replace("COUNTY", "").strip()
    s = s.replace("&", "AND")
    s = re.sub(r"[.'’]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _to_number(val) -> float:
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if "(D" in s or s in {"(D)", " (D)"}:
        return np.nan
    s = s.replace(",", "").strip()
    s = re.sub(r"[^\d\.\-]", "", s)
    return float(s) if s != "" else np.nan


def load_irrigation_census() -> pd.DataFrame:
    p = Path("data/nass/IrrigatedAcresHarvestedByCounty.csv")
    df = pd.read_csv(p)
    df = df[(df["State"] == "MARYLAND") & (df["Geo Level"] == "COUNTY") & (df["Period"] == "YEAR")].copy()
    df = df[df["Program"].astype(str).str.upper() == "CENSUS"]
    df = df[df["Commodity"] == "SOYBEANS"]
    df = df[df["Data Item"].astype(str).str.contains("IRRIGATED - ACRES HARVESTED", na=False)]
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df[df["Year"].isin(CENSUS_YEARS)].copy()

    df["County"] = df["County"].astype(str)
    df = df[df["County"].str.upper() != "OTHER COUNTIES"].copy()
    df["county_norm"] = df["County"].map(normalize_county_name)
    df["district"] = df["Ag District"].astype(str).str.upper().str.strip()

    df["irrigated_acres"] = df["Value"].map(_to_number)
    df["irrigation_data_present"] = True

    keep = ["Year", "county_norm", "district", "irrigated_acres", "irrigation_data_present"]
    return df[keep].drop_duplicates(subset=["Year", "county_norm"])


def load_yield_county() -> pd.DataFrame:
    p = Path("data/nass/Soybean_Yield_BU:Acre_By_County.csv")
    df = pd.read_csv(p)
    df = df[(df["State"] == "MARYLAND") & (df["Geo Level"] == "COUNTY") & (df["Period"] == "YEAR")].copy()
    df = df[df["Commodity"] == "SOYBEANS"]
    df = df[df["Data Item"] == "SOYBEANS - YIELD, MEASURED IN BU / ACRE"]
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Year"]).copy()

    df["County"] = df["County"].astype(str)
    df = df[df["County"].str.upper() != "OTHER COUNTIES"].copy()
    df["county_norm"] = df["County"].map(normalize_county_name)
    df["district"] = df["Ag District"].astype(str).str.upper().str.strip()
    df["yield"] = pd.to_numeric(df["Value"].astype(str).str.replace(",", "", regex=False), errors="coerce")

    keep = ["Year", "county_norm", "district", "yield"]
    return df[keep].dropna(subset=["yield"]).drop_duplicates(subset=["Year", "county_norm"])


def load_drought_county(index: str = "PDSI", metric: str = "may_sep_mean") -> pd.DataFrame:
    p = Path("data/processed_drought/drought_aggregates_county_year.csv")
    df = pd.read_csv(p)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["year"]).copy()
    df["index"] = df["index"].astype(str).str.upper().str.strip()
    df = df[df["index"] == index.upper()].copy()

    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not found in {p}.")

    df[metric] = pd.to_numeric(df[metric], errors="coerce")
    out = df[["year", "county_norm", metric]].rename(columns={"year": "Year", metric: "pdsi"})
    return out


def drought_class(pdsi: float) -> str:
    if pd.isna(pdsi):
        return "unknown"
    if pdsi <= -3:
        return "severe_drought"
    if pdsi <= -2:
        return "moderate_drought"
    if pdsi <= -1:
        return "mild_dry"
    if pdsi >= 1:
        return "wet"
    return "near_normal"


def irrigation_class(acres: float) -> str:
    if pd.isna(acres):
        return "unknown_or_suppressed"
    return "irrigated" if acres > 0 else "non_irrigated"

def census_year_for_year(year: int) -> int:
    """
    Assign an analysis year to the most recent census year <= it.
    Example: 2017–2021 -> 2017; 2022+ -> 2022.
    """
    candidates = [y for y in CENSUS_YEARS if y <= year]
    return max(candidates) if candidates else min(CENSUS_YEARS)

def irrigation_class_from_census_row(irrigated_acres: float, irrigation_row_present: bool) -> str:
    """
    Classify irrigation status.
    - Missing census row: treat as non-irrigated (0 reported/omitted).
    - Present but suppressed (D): unknown (exclude from irrigated vs non-irrigated comparisons).
    """
    if not irrigation_row_present:
        return "non_irrigated"
    if pd.isna(irrigated_acres):
        return "unknown_or_suppressed"
    return "irrigated" if irrigated_acres > 0 else "non_irrigated"


def summarize(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    g = df.groupby(group_cols, as_index=False).agg(
        n=("yield", "count"),
        yield_mean=("yield", "mean"),
        yield_median=("yield", "median"),
        yield_sd=("yield", "std"),
        pdsi_mean=("pdsi", "mean"),
        irrigated_acres_mean=("irrigated_acres_filled", "mean"),
    )
    return g.sort_values(group_cols)


def plot_boxplots(df: pd.DataFrame, outpath: Path) -> None:
    # Only focus on drought-ish conditions where irrigation should matter most
    dd = df[df["drought_class"].isin(["mild_dry", "moderate_drought", "severe_drought"])].copy()
    if dd.empty:
        return

    dd = dd[dd["irrigation_class"].isin(["irrigated", "non_irrigated"])].copy()
    if dd.empty:
        return

    order = ["mild_dry", "moderate_drought", "severe_drought"]
    labels = ["mild dry", "moderate", "severe"]

    fig, ax = plt.subplots(figsize=(12.5, 6.5))

    positions = []
    data = []
    xticks = []

    pos = 1
    for cls, lab in zip(order, labels):
        sub = dd[dd["drought_class"] == cls]
        non = sub[sub["irrigation_class"] == "non_irrigated"]["yield"].dropna()
        irr = sub[sub["irrigation_class"] == "irrigated"]["yield"].dropna()
        if len(non) == 0 and len(irr) == 0:
            continue
        data.extend([non, irr])
        positions.extend([pos, pos + 0.35])
        xticks.append((pos + pos + 0.35) / 2)
        pos += 1.3

    bp = ax.boxplot(data, positions=positions, widths=0.28, patch_artist=True, showmeans=True)

    # Color by irrigation class: non-irrigated = orange, irrigated = blue
    non_color = "#F18F01"
    irr_color = "#2E86AB"
    for i, box in enumerate(bp["boxes"]):
        box.set_facecolor(non_color if i % 2 == 0 else irr_color)
        box.set_alpha(0.65)
        box.set_edgecolor("black")
        box.set_linewidth(1.2)
    for key in ["whiskers", "caps", "medians", "means"]:
        for item in bp[key]:
            item.set_color("black")
            item.set_linewidth(1.2)

    ax.set_xticks(xticks)
    ax.set_xticklabels(labels[: len(xticks)], fontweight="bold")
    ax.set_ylabel("Yield (bu/acre)")
    ax.set_title("Yield under dry conditions: irrigated vs non-irrigated counties", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)

    ax.legend(
        handles=[
            plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=non_color, markersize=12, label="non-irrigated"),
            plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=irr_color, markersize=12, label="irrigated"),
        ],
        frameon=True,
        loc="upper left",
    )

    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()


def plot_scatter(df: pd.DataFrame, outpath: Path, title: str) -> None:
    sub = df[df["irrigation_class"].isin(["irrigated", "non_irrigated"])].copy()
    sub = sub.dropna(subset=["yield", "pdsi"])
    if sub.empty:
        return

    fig, ax = plt.subplots(figsize=(12.5, 7.2))

    # Non‑irrigated: constant-size X
    non = sub[sub["irrigation_class"] == "non_irrigated"].copy()
    if not non.empty:
        ax.scatter(
            non["pdsi"],
            non["yield"],
            s=55,
            marker="x",
            c="#D1495B",  # orange-red
            linewidths=1.8,
            alpha=0.85,
            label="non-irrigated (0 acres)",
            zorder=3,
        )

    # Irrigated: blue dots sized by irrigated acres (continuous)
    irr = sub[sub["irrigation_class"] == "irrigated"].copy()
    if not irr.empty:
        acres = pd.to_numeric(irr["irrigated_acres_filled"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
        # Size scaling: gentle, readable across wide acre ranges
        sizes = 35.0 + (np.sqrt(acres) * 1.2)
        sizes = np.clip(sizes, 40, 320)
        ax.scatter(
            irr["pdsi"],
            irr["yield"],
            s=sizes,
            marker="o",
            c="#2E86AB",
            edgecolor="black",
            linewidth=0.4,
            alpha=0.75,
            label="irrigated (size ∝ acres)",
            zorder=2,
        )

    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("PDSI (May–Sep mean)  ↑ wetter / ↓ drier")
    ax.set_ylabel("Yield (bu/acre)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=True, loc="upper right")
    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    irrigation = load_irrigation_census()
    yield_df = load_yield_county()
    drought = load_drought_county(index="PDSI", metric="may_sep_mean")

    # Limit drought to yield year range and assign census irrigation snapshot per year
    y_min = int(yield_df["Year"].min())
    y_max = int(yield_df["Year"].max())
    drought = drought[(drought["Year"] >= y_min) & (drought["Year"] <= y_max)].copy()

    yield_df = yield_df.copy()
    yield_df["census_year"] = yield_df["Year"].astype(int).map(census_year_for_year)

    irrigation = irrigation.rename(columns={"Year": "census_year"}).copy()

    merged = yield_df.merge(drought, on=["Year", "county_norm"], how="left")
    merged = merged.merge(irrigation, on=["census_year", "county_norm"], how="left", suffixes=("", "_irr"))

    # Irrigation: missing census row -> 0; suppressed (D) -> unknown (excluded from irrigated vs non plots)
    merged["irrigation_data_present"] = merged["irrigation_data_present"].fillna(False)
    merged["irrigated_acres_filled"] = merged["irrigated_acres"].copy()
    merged.loc[~merged["irrigation_data_present"], "irrigated_acres_filled"] = 0.0

    merged["irrigation_class"] = merged.apply(
        lambda r: irrigation_class_from_census_row(r["irrigated_acres"], bool(r["irrigation_data_present"])),
        axis=1,
    )
    merged["drought_class"] = merged["pdsi"].map(drought_class)

    merged_out = OUT_DIR / "county_year_merged.csv"
    merged.to_csv(merged_out, index=False)

    # Summaries
    by_year = summarize(
        merged,
        group_cols=["Year", "drought_class", "irrigation_class"],
    )
    by_year_out = OUT_DIR / "summary_by_year_droughtclass.csv"
    by_year.to_csv(by_year_out, index=False)

    overall = summarize(
        merged,
        group_cols=["drought_class", "irrigation_class"],
    )
    overall_out = OUT_DIR / "summary_overall_droughtclass.csv"
    overall.to_csv(overall_out, index=False)

    # Plots
    plot_boxplots(merged, OUT_DIR / "yield_by_irrigation_in_drought_boxplots.png")
    plot_scatter(
        merged,
        OUT_DIR / "yield_vs_pdsi_scatter.png",
        title=f"County yield vs drought (PDSI May–Sep mean), irrigation labeled by latest census (years {y_min}–{y_max})",
    )

    # Also provide the specific window you mentioned as an example
    sub_2017_2021 = merged[(merged["Year"] >= 2017) & (merged["Year"] <= 2021)].copy()
    plot_scatter(
        sub_2017_2021,
        OUT_DIR / "yield_vs_pdsi_scatter_2017_2021.png",
        title="County yield vs drought (PDSI May–Sep mean), irrigation labeled by 2017 census (2017–2021)",
    )

    print(f"Saved merged: {merged_out}")
    print(f"Saved summary (by year): {by_year_out}")
    print(f"Saved summary (overall): {overall_out}")


if __name__ == "__main__":
    main()

