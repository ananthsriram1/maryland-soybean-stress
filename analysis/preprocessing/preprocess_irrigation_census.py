#!/usr/bin/env python3
"""
Build a single cleaned CSV of all Census NASS irrigation data
(soybeans, Maryland, by county; 1997, 2002, 2007, 2012, 2017, 2022).

Inputs:
  data/nass/IrrigationvsNonirrigated.csv
    NASS Census of Agriculture county-level export with Year, County,
    Program, Geo Level, Commodity, Period, Value, CV (%), and the suppression
    flags (D)/(L) embedded in the Value column.

Outputs:
  data/census_nass_irrigation_all.csv
    Long-format county-year-metric table with parsed numeric values, a
    Value_suppressed boolean for (D)/(L) rows, and CV_Pct.

Paper figures:
  - Feeds Figure 7 (irrigated soybean area heatmap by district x census year;
    analysis/figures/figure07_irrigated_district_heatmap.py).
  - Feeds the supporting irrigation-vs-yield analyses under
    analysis/stress_analysis/ and analysis/figures/supporting/.
"""

import pandas as pd
from pathlib import Path

SRC = Path("data/nass/IrrigationvsNonirrigated.csv")
OUT = Path("data/census_nass_irrigation_all.csv")


def main():
    df = pd.read_csv(SRC)

    # Census, Maryland, county-level, soybeans only
    df = df[
        (df["Program"].astype(str).str.upper() == "CENSUS")
        & (df["State"] == "MARYLAND")
        & (df["Geo Level"] == "COUNTY")
        & (df["Commodity"] == "SOYBEANS")
        & (df["Period"] == "YEAR")
    ].copy()

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df.dropna(subset=["Year"])
    df["Year"] = df["Year"].astype(int)

    # Value parsing
    raw = df["Value"].astype(str).str.strip()
    df["Value_suppressed"] = raw.str.contains(r"\(D\)|\(L\)", na=False, regex=True)
    df["Value_clean"] = (
        raw.str.replace(",", "", regex=False)
        .str.replace(r"\(D\)|\(L\)", "", regex=True)
        .str.strip()
    )
    df["Value_numeric"] = pd.to_numeric(df["Value_clean"], errors="coerce")
    df["CV_Pct"] = pd.to_numeric(df["CV (%)"], errors="coerce")

    out = df[
        [
            "Year",
            "County",
            "Ag District",
            "Ag District Code",
            "Data Item",
            "Value_numeric",
            "CV_Pct",
            "Value",
            "Value_suppressed",
        ]
    ].copy()
    out = out.rename(
        columns={
            "Ag District": "Ag_District",
            "Ag District Code": "Ag_District_Code",
            "Data Item": "Data_Item",
            "Value": "Value_raw",
        }
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(out)} rows)")
    print(f"  Years: {sorted(out['Year'].unique())}")
    print(f"  Data items: {out['Data_Item'].unique().tolist()}")
    print(f"  Counties: {out['County'].nunique()}")


if __name__ == "__main__":
    main()
