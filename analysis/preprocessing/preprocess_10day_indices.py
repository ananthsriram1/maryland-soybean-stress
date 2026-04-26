#!/usr/bin/env python3
"""
Preprocess 10-day soybean NDVI/NDWI time series to Maryland only.

Inputs:
  data/MD_SOYBEAN_10DAY/MD_Soybean_10Day_TimeSeries_YYYY.csv
    Expected columns: NAME, date, NDVI, NDWI

Processing (implemented):
  - Concatenate all yearly files
  - Standardize county names (strip whitespace)
  - Filter to the repo's canonical Maryland county list (24 incl. Baltimore City)
  - Parse `date` to datetime
  - De-duplicate by (County, date) using mean of NDVI/NDWI (skips NaNs)
  - Export:
      1) Long (tidy): one row per county-date with NDVI/NDWI
      2) Wide (pivoted): columns NDVI_YYYY-MM-DD and NDWI_YYYY-MM-DD
      3) Wide (imputed): forward-fill then backward-fill across time per county, per metric
  - Add `Ag_District` column using the district definitions already used in this repo

Outputs:
  data/maryland_soybean_10day_timeseries_long.csv
  data/maryland_soybean_10day_timeseries_wide.csv
  data/maryland_soybean_10day_timeseries_wide_imputed.csv

Paper figures:
  - Feeds Figure 8 (NDWI distribution by district and census period;
    analysis/figures/figure08_ndwi_r4r6_boxplot.py).
  - Feeds Figure 9 (NDVI/NDWI dual-axis "Invisible Stress Window";
    analysis/figures/figure09_ndvi_ndwi_scissors_dualaxis.py).
  - Feeds the differential and index stress analyses under
    analysis/stress_analysis/.
"""

from __future__ import annotations

import os
from glob import glob
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


INPUT_DIR = "data/MD_SOYBEAN_10DAY"

OUT_LONG = "data/maryland_soybean_10day_timeseries_long.csv"
OUT_WIDE = "data/maryland_soybean_10day_timeseries_wide.csv"
OUT_WIDE_IMPUTED = "data/maryland_soybean_10day_timeseries_wide_imputed.csv"


# Canonical Maryland counties (24 incl. Baltimore City) by agricultural district.
# Mirrors the structure used in archive/plotndwi_legacy/PreprocessNDWI.py (legacy NDWI-only path).
DISTRICT_COUNTIES: Dict[str, set] = {
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


def build_county_to_district() -> Dict[str, str]:
    m: Dict[str, str] = {}
    for d, counties in DISTRICT_COUNTIES.items():
        for c in counties:
            m[c] = d
    return m


def list_input_files(input_dir: str) -> List[str]:
    files = sorted(glob(os.path.join(input_dir, "MD_Soybean_10Day_TimeSeries_*.csv")))
    if not files:
        raise FileNotFoundError(f"No input files found in {input_dir!r}.")
    return files


def load_and_concat(files: List[str]) -> pd.DataFrame:
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["__source_file"] = os.path.basename(f)
        dfs.append(df)
    out = pd.concat(dfs, ignore_index=True)
    return out


def standardize_county_name(name: str) -> str:
    # Keep as-is but strip whitespace; preserve punctuation (e.g., Queen Anne's, St. Mary's)
    return str(name).strip()


def preprocess(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = {"NAME", "date", "NDVI", "NDWI"}
    missing = required - set(df_raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df_raw.copy()
    df["County"] = df["NAME"].map(standardize_county_name)
    df = df.drop(columns=["NAME"])

    # Parse date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # Numeric casting (blank strings -> NaN)
    df["NDVI"] = pd.to_numeric(df["NDVI"], errors="coerce")
    df["NDWI"] = pd.to_numeric(df["NDWI"], errors="coerce")

    # Filter to Maryland counties only (canonical list)
    md_counties = sorted([c for s in DISTRICT_COUNTIES.values() for c in s])
    df = df[df["County"].isin(md_counties)].copy()

    # De-duplicate by (County, date). Mean will ignore NaNs.
    # This is necessary because some county names appear in multiple states (e.g., Kent)
    # and the input files do not include a State field.
    dedup = (
        df.groupby(["County", "date"], as_index=False)
        .agg(
            NDVI=("NDVI", "mean"),
            NDWI=("NDWI", "mean"),
        )
        .sort_values(["County", "date"])
    )

    county_to_district = build_county_to_district()
    dedup["Ag_District"] = dedup["County"].map(county_to_district)

    # Export long (tidy)
    long_df = dedup[["County", "Ag_District", "date", "NDVI", "NDWI"]].copy()
    long_df["Year"] = long_df["date"].dt.year
    long_df["Month"] = long_df["date"].dt.month
    long_df["Day"] = long_df["date"].dt.day

    # Pivot to wide with two variable blocks: NDVI_* and NDWI_*
    wide_ndvi = long_df.pivot(index="County", columns="date", values="NDVI")
    wide_ndwi = long_df.pivot(index="County", columns="date", values="NDWI")

    # Ensure consistent ordering by date
    wide_ndvi = wide_ndvi.sort_index(axis=1)
    wide_ndwi = wide_ndwi.sort_index(axis=1)

    wide_ndvi.columns = [f"NDVI_{c.date().isoformat()}" for c in wide_ndvi.columns]
    wide_ndwi.columns = [f"NDWI_{c.date().isoformat()}" for c in wide_ndwi.columns]

    wide = pd.concat([wide_ndvi, wide_ndwi], axis=1)
    wide.insert(0, "Ag_District", wide.index.map(county_to_district))
    wide = wide.sort_index()

    # Impute across time per variable (ffill then bfill along time axis)
    ndvi_cols = [c for c in wide.columns if c.startswith("NDVI_")]
    ndwi_cols = [c for c in wide.columns if c.startswith("NDWI_")]

    def _impute_block(w: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        block = w[cols].copy()
        # Ensure columns are sorted chronologically based on the date suffix
        cols_sorted = sorted(cols, key=lambda x: x.split("_", 1)[1])
        block = block[cols_sorted]
        block = block.ffill(axis=1).bfill(axis=1)
        return block

    wide_imputed = wide.copy()
    wide_imputed[ndvi_cols] = _impute_block(wide_imputed, ndvi_cols)
    wide_imputed[ndwi_cols] = _impute_block(wide_imputed, ndwi_cols)

    return long_df, wide, wide_imputed


def main():
    files = list_input_files(INPUT_DIR)
    print(f"Found {len(files)} input files in {INPUT_DIR!r}.")

    raw = load_and_concat(files)
    print(f"Raw rows: {len(raw):,}")

    long_df, wide_df, wide_imputed_df = preprocess(raw)

    print(f"Maryland-only long rows: {len(long_df):,}")
    print(f"Maryland counties: {long_df['County'].nunique()} (expected 24)")
    print(f"Date range: {long_df['date'].min().date()} to {long_df['date'].max().date()}")

    long_df.to_csv(OUT_LONG, index=False)
    wide_df.to_csv(OUT_WIDE)
    wide_imputed_df.to_csv(OUT_WIDE_IMPUTED)

    print(f"Saved: {OUT_LONG}")
    print(f"Saved: {OUT_WIDE}")
    print(f"Saved: {OUT_WIDE_IMPUTED}")


if __name__ == "__main__":
    main()

