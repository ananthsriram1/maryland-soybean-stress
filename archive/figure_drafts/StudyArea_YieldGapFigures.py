#!/usr/bin/env python3
"""
Study-area baseline "yield gap" visuals.

Option 1: District yields over time with Maryland + US national reference lines.
Option 2: District yield gap vs US national (District - National) over time.

Uses:
  - data/processed_yield/yield_district_averages_by_year.csv
  - data/processed_yield/yield_clean_long_format.csv (for Maryland statewide mean)
  - data/NationalAveragesSoybeanAcreageYield.csv (NATIONAL, Period==YEAR, yield)

Outputs:
  - outputs/YieldAnalysis/StudyArea/District_Yield_vs_MD_US.png
  - outputs/YieldAnalysis/StudyArea/District_YieldGap_vs_US.png
  - outputs/YieldAnalysis/StudyArea/District_YieldGap_Table.csv
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = "outputs/YieldAnalysis/StudyArea"
os.makedirs(OUT_DIR, exist_ok=True)

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


def load_national_yield():
    df = pd.read_csv("data/NationalAveragesSoybeanAcreageYield.csv")
    df = df[(df["Geo Level"] == "NATIONAL") & (df["Period"] == "YEAR")]
    df = df[df["Data Item"] == "SOYBEANS - YIELD, MEASURED IN BU / ACRE"][["Year", "Value"]].copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["National_Yield"] = pd.to_numeric(df["Value"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    return df[["Year", "National_Yield"]].dropna().sort_values("Year")


def load_md_statewide():
    md = pd.read_csv("data/processed_yield/yield_clean_long_format.csv")
    md = md[~md["Is_Other_Combined"]].copy() if "Is_Other_Combined" in md.columns else md.copy()
    md_state = md.groupby("Year", as_index=False)["Yield"].mean().rename(columns={"Yield": "Maryland_Yield"})
    return md_state.sort_values("Year")


def load_district_yield():
    d = pd.read_csv("data/processed_yield/yield_district_averages_by_year.csv")
    # standardize column names
    d = d.rename(columns={"Yield_mean": "District_Yield"})
    d["District"] = d["District"].astype(str)
    d["Year"] = pd.to_numeric(d["Year"], errors="coerce")
    return d[["District", "Year", "District_Yield"]].dropna().sort_values(["District", "Year"])


def option1_plot(district: pd.DataFrame, md_state: pd.DataFrame, nat: pd.DataFrame):
    # Merge on year range intersection
    years = sorted(set(district["Year"]) & set(md_state["Year"]) & set(nat["Year"]))
    district = district[district["Year"].isin(years)]
    md_state = md_state[md_state["Year"].isin(years)]
    nat = nat[nat["Year"].isin(years)]

    fig, ax = plt.subplots(figsize=(14, 8))

    # Reference lines
    ax.plot(nat["Year"], nat["National_Yield"], color="black", linewidth=3, label="US National")
    ax.plot(md_state["Year"], md_state["Maryland_Yield"], color="crimson", linewidth=3, label="Maryland (statewide mean)")

    # District lines
    for dname in DISTRICT_ORDER:
        sub = district[district["District"] == dname]
        if sub.empty:
            continue
        ax.plot(
            sub["Year"],
            sub["District_Yield"],
            color=DISTRICT_COLORS.get(dname, "#808080"),
            linewidth=2.2,
            alpha=0.85,
            label=dname.title(),
        )

    ax.set_title("Soybean yield baseline by district vs Maryland and US (1997–present)", fontsize=16, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Yield (bu/acre)")
    ax.grid(True, alpha=0.25)
    ax.legend(ncol=2, loc="upper left")

    out = os.path.join(OUT_DIR, "District_Yield_vs_MD_US.png")
    plt.tight_layout()
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def option2_plot(district: pd.DataFrame, nat: pd.DataFrame):
    # Merge district with national for gap
    merged = district.merge(nat, on="Year", how="inner")
    merged["Yield_Gap_vs_US"] = merged["District_Yield"] - merged["National_Yield"]

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axhline(0, color="black", linewidth=2, alpha=0.7)

    for dname in DISTRICT_ORDER:
        sub = merged[merged["District"] == dname]
        if sub.empty:
            continue
        ax.plot(
            sub["Year"],
            sub["Yield_Gap_vs_US"],
            color=DISTRICT_COLORS.get(dname, "#808080"),
            linewidth=2.5,
            alpha=0.9,
            label=dname.title(),
        )

    ax.set_title("District yield gap vs US national (District − US)", fontsize=16, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Yield gap (bu/acre)")
    ax.grid(True, alpha=0.25)
    ax.legend(ncol=2, loc="upper left")

    out = os.path.join(OUT_DIR, "District_YieldGap_vs_US.png")
    plt.tight_layout()
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")

    # Save table for writing
    merged_out = merged[["District", "Year", "District_Yield", "National_Yield", "Yield_Gap_vs_US"]].sort_values(["District", "Year"])
    merged_out.to_csv(os.path.join(OUT_DIR, "District_YieldGap_Table.csv"), index=False)


def main():
    nat = load_national_yield()
    md_state = load_md_statewide()
    district = load_district_yield()

    option1_plot(district, md_state, nat)
    option2_plot(district, nat)


if __name__ == "__main__":
    main()

