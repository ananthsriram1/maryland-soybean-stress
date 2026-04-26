#!/usr/bin/env python3
"""
Preprocess Corn Yield Data (1997-2024)

Mirrors `scripts/PreprocessYieldData.py` (soybean) but for corn grain yield.

Input:
  - data/Corn_Yield_1997to2024.csv (NASS-style export; county-level)

Outputs:
  - data/county_corn_yield_all.csv (canonical per-county dataset; all numeric columns)
  - data/processed_corn_yield/ (clean long, wide, by county, summaries, etc.)

Paper context:
  Auxiliary preprocessing only. Corn yield is used as a comparator/cross-check
  against soybean signals in the supporting analyses. None of the canonical
  manuscript figures (Figures 1-10) consume this dataset directly, but the
  outputs are read by exploratory scripts archived under archive/exploratory/.
"""

from __future__ import annotations

import os
import pandas as pd
import numpy as np


# District mapping (NASS ag district codes)
district_codes = {
    10: "WESTERN",
    20: "NORTH CENTRAL",
    30: "UPPER EASTERN SHORE",
    80: "SOUTHERN",
    90: "LOWER EASTERN SHORE",
    99: "OTHER",
}

district_counties = {
    "WESTERN": {"Allegany", "Garrett"},
    "UPPER EASTERN SHORE": {"Caroline", "Cecil", "Kent", "Queen Anne's", "Talbot"},
    "SOUTHERN": {"Anne Arundel", "Calvert", "Charles", "Prince George's", "St. Mary's"},
    "NORTH CENTRAL": {"Baltimore", "Baltimore City", "Carroll", "Frederick", "Harford", "Howard", "Montgomery", "Washington"},
    "LOWER EASTERN SHORE": {"Dorchester", "Somerset", "Wicomico", "Worcester"},
}


def load_and_clean_corn_yield_data() -> pd.DataFrame:
    """Load and clean the corn yield dataset (county-year)."""
    print("🔄 Loading corn yield data...")

    df = pd.read_csv("data/Corn_Yield_1997to2024.csv")
    print(f"   📊 Raw data: {len(df)} records")

    # Filter to the intended slice (robust to minor naming differences)
    if "Geo Level" in df.columns:
        df = df[df["Geo Level"].astype(str).str.upper().eq("COUNTY")].copy()
    if "State" in df.columns:
        df = df[df["State"].astype(str).str.upper().eq("MARYLAND")].copy()
    if "Period" in df.columns:
        df = df[df["Period"].astype(str).str.upper().eq("YEAR")].copy()

    if "Commodity" in df.columns:
        df = df[df["Commodity"].astype(str).str.upper().eq("CORN")].copy()
    if "Data Item" in df.columns:
        di = df["Data Item"].astype(str).str.upper()
        df = df[di.str.contains("YIELD", na=False) & di.str.contains("BU", na=False)].copy()

    # Clean year
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"]).copy()
    df["Year"] = df["Year"].astype(int)

    # Clean county names
    df["County"] = df["County"].astype(str).str.strip()
    df["County"] = df["County"].str.replace("QUEEN ANNES", "QUEEN ANNE'S", regex=False)
    df["County"] = df["County"].str.replace("PRINCE GEORGES", "PRINCE GEORGE'S", regex=False)
    df["County"] = df["County"].str.replace("ST MARYS", "ST. MARY'S", regex=False)

    # Clean yield values
    df["Value"] = df["Value"].astype(str).str.strip().str.replace(",", "", regex=False)
    df["Yield"] = pd.to_numeric(df["Value"], errors="coerce")

    # Clean CV values
    if "CV (%)" in df.columns:
        df["CV"] = pd.to_numeric(df["CV (%)"], errors="coerce")
    else:
        df["CV"] = np.nan

    # Map district codes to names
    df["Ag District Code"] = pd.to_numeric(df["Ag District Code"], errors="coerce")
    df["District"] = df["Ag District Code"].map(district_codes)

    # For counties without district codes, map by name
    county_to_district: dict[str, str] = {}
    for district, counties in district_counties.items():
        for county in counties:
            county_to_district[county.upper()] = district

    missing_district = df["District"].isna()
    df.loc[missing_district, "District"] = df.loc[missing_district, "County"].str.upper().map(county_to_district)

    clean_df = df[["Year", "County", "District", "Ag District Code", "Yield", "CV", "Program"]].copy()
    clean_df = clean_df.dropna(subset=["Yield"]).copy()

    clean_df["Is_Other_Combined"] = clean_df["County"].str.contains("OTHER", case=False, na=False)

    print(f"   ✅ Clean data: {len(clean_df)} records")
    print(f"   📅 Years: {clean_df['Year'].min()} to {clean_df['Year'].max()}")
    print(f"   📍 Counties: {clean_df['County'].nunique()}")
    return clean_df


def create_output_formats(df: pd.DataFrame) -> None:
    """Generate multiple clean CSV formats (same set as soybean preprocessing)."""
    print("\n📁 Creating output CSV files (corn)...")

    output_base = "data/processed_corn_yield"
    os.makedirs(output_base, exist_ok=True)

    # Remove OTHER counties for most outputs
    df_no_other = df[~df["Is_Other_Combined"]].copy()

    # Format 0: Canonical per-county yield dataset (all numbers, one file)
    print("   📄 Format 0: Per-county corn yield dataset (data/county_corn_yield_all.csv)...")
    out_cols = df_no_other[["Year", "County", "District", "Ag District Code", "Yield", "CV", "Program"]].copy()
    out_cols = out_cols.rename(columns={"Ag District Code": "Ag_District_Code", "Yield": "Yield_Bu_Acre", "CV": "CV_Pct"})
    out_cols.to_csv("data/county_corn_yield_all.csv", index=False)
    print(f"      💾 Saved: data/county_corn_yield_all.csv ({len(out_cols)} records)")

    # Format 1: Clean long format (all data)
    print("   📄 Format 1: Clean long format...")
    df_no_other.to_csv(f"{output_base}/yield_clean_long_format.csv", index=False)
    print(f"      💾 Saved: yield_clean_long_format.csv ({len(df_no_other)} records)")

    # Format 2: Wide format by county (years as columns)
    print("   📄 Format 2: Wide format (counties x years)...")
    wide_df = df_no_other.pivot_table(index="County", columns="Year", values="Yield", aggfunc="first")
    wide_df.to_csv(f"{output_base}/yield_wide_by_county.csv")
    print(f"      💾 Saved: yield_wide_by_county.csv ({len(wide_df)} counties x {len(wide_df.columns)} years)")

    # Format 3: One file per district
    print("   📄 Format 3: Separate files by district...")
    for district in sorted(df_no_other["District"].dropna().unique()):
        district_df = df_no_other[df_no_other["District"] == district].copy()
        filename = f"{output_base}/yield_{district.lower().replace(' ', '_')}.csv"
        district_df.to_csv(filename, index=False)
        print(f"      💾 Saved: {os.path.basename(filename)} ({len(district_df)} records)")

    # Format 4: One file per county
    print("   📄 Format 4: Separate files by county...")
    county_dir = f"{output_base}/by_county"
    os.makedirs(county_dir, exist_ok=True)

    for county in sorted(df_no_other["County"].unique()):
        if county in ["OTHER COUNTIES", "OTHER (COMBINED) COUNTIES"]:
            continue
        county_df = df_no_other[df_no_other["County"] == county].copy()
        county_clean = county.lower().replace(" ", "_").replace("'", "")
        filename = f"{county_dir}/yield_{county_clean}.csv"
        county_df.to_csv(filename, index=False)
    print(f"      💾 Saved {df_no_other['County'].nunique()} county files")

    # Format 5: Summary statistics by county
    print("   📄 Format 5: Summary statistics by county...")
    summary = (
        df_no_other.groupby(["County", "District"])
        .agg(
            Yield_count=("Yield", "count"),
            Yield_mean=("Yield", "mean"),
            Yield_std=("Yield", "std"),
            Yield_min=("Yield", "min"),
            Yield_max=("Yield", "max"),
            Yield_median=("Yield", "median"),
            CV_mean=("CV", "mean"),
            Year_min=("Year", "min"),
            Year_max=("Year", "max"),
        )
        .round(2)
        .reset_index()
    )
    summary.to_csv(f"{output_base}/yield_summary_by_county.csv", index=False)
    print("      💾 Saved: yield_summary_by_county.csv")

    # Format 6: District averages by year
    print("   📄 Format 6: District averages by year...")
    district_avg = (
        df_no_other.groupby(["District", "Year"])
        .agg(Yield_mean=("Yield", "mean"), Yield_std=("Yield", "std"), Yield_count=("Yield", "count"), CV_mean=("CV", "mean"))
        .round(2)
        .reset_index()
    )
    district_avg.to_csv(f"{output_base}/yield_district_averages_by_year.csv", index=False)
    print("      💾 Saved: yield_district_averages_by_year.csv")

    # Format 7: Wide format by district (years as columns)
    print("   📄 Format 7: Wide format by district...")
    district_wide = district_avg.pivot_table(index="District", columns="Year", values="Yield_mean", aggfunc="first")
    district_wide.to_csv(f"{output_base}/yield_district_wide.csv")
    print("      💾 Saved: yield_district_wide.csv")

    # Format 8: Recent years only (2014-2024)
    print("   📄 Format 8: Recent period (2014-2024) subset...")
    recent_df = df_no_other[df_no_other["Year"] >= 2014].copy()
    recent_df.to_csv(f"{output_base}/yield_2014_2024.csv", index=False)
    print(f"      💾 Saved: yield_2014_2024.csv ({len(recent_df)} records)")

    # Format 9: Census years only (to match irrigation data)
    print("   📄 Format 9: Census years only (1997, 2002, 2007, 2012, 2017, 2022)...")
    census_years = [1997, 2002, 2007, 2012, 2017, 2022]
    census_df = df_no_other[df_no_other["Year"].isin(census_years)].copy()
    census_df.to_csv(f"{output_base}/yield_census_years.csv", index=False)
    print(f"      💾 Saved: yield_census_years.csv ({len(census_df)} records)")

    print(f"\n✅ All formats created in: {output_base}/")


def main() -> None:
    print("=" * 80)
    print("CORN YIELD DATA PREPROCESSING (1997-2024)")
    print("=" * 80)

    clean_df = load_and_clean_corn_yield_data()
    create_output_formats(clean_df)

    print("\n" + "=" * 80)
    print("✅ Preprocessing complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

