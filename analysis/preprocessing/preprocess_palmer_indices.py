#!/usr/bin/env python3
"""
Preprocess Palmer drought indices (PDSI/PHDI/PMDI) county time series.

Inputs:
  data/drought_data_1997-2025/{pdsi_county,phdi_county,pmdi_county}/*.csv

Outputs:
  data/processed_drought/drought_monthly_county.csv
  data/processed_drought/drought_aggregates_county_year.csv
  data/processed_drought/drought_aggregates_district_year.csv

Paper figures:
  - Feeds Figure 5 (flash-drought proxy events by Palmer index;
    analysis/stress_analysis/detect_flash_droughts.py).
  - Feeds Figure 6 (yield by PDSI drought class boxplots;
    analysis/figures/figure06_drought_class_yield_boxplots.py).
  - Feeds the drought-vs-yield correlation tables produced under
    analysis/stress_analysis/.

Note: The wide-format combined CSVs consumed directly by some figure scripts
(data/maryland_pdsi_combined_wide.csv, _phdi_, _pmdi_) are produced by
analysis/preprocessing/combine_palmer_index.py, which is the canonical
companion to this monthly/aggregated pipeline.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path("data/drought_data_1997-2025")
OUT_DIR = Path("data/processed_drought")
OUT_DIR.mkdir(parents=True, exist_ok=True)


INDEX_DIRS: dict[str, str] = {
    "pdsi_county": "PDSI",
    "phdi_county": "PHDI",
    "pmdi_county": "PMDI",
}


def normalize_county_name(name: str) -> str:
    """
    Normalize a county label to match across datasets.
    Keeps 'ST' (not expanded), removes punctuation, collapses whitespace.
    """
    s = str(name).upper().strip()
    s = s.replace("COUNTY", "").strip()
    s = s.replace("&", "AND")
    s = re.sub(r"[.'’]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def read_drought_csv(path: Path, index_name: str) -> pd.DataFrame:
    county_raw = path.stem
    county_norm = normalize_county_name(county_raw)

    df = pd.read_csv(path, comment="#")
    if "Date" not in df.columns or "Value" not in df.columns:
        raise ValueError(f"Unexpected columns in {path}: {list(df.columns)}")

    date = pd.to_numeric(df["Date"], errors="coerce")
    value = pd.to_numeric(df["Value"], errors="coerce")

    year = (date // 100).astype("Int64")
    month = (date % 100).astype("Int64")

    out = pd.DataFrame(
        {
            "county_raw": county_raw,
            "county_norm": county_norm,
            "index": index_name,
            "year": year,
            "month": month,
            "value": value,
        }
    )

    out = out.dropna(subset=["year", "month", "value"]).copy()
    out["year"] = out["year"].astype(int)
    out["month"] = out["month"].astype(int)
    out["value"] = out["value"].astype(float)

    out = out[(out["month"] >= 1) & (out["month"] <= 12)]
    return out


def build_monthly() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for subdir, idx in INDEX_DIRS.items():
        d = BASE_DIR / subdir
        if not d.exists():
            continue
        for p in sorted(d.glob("*.csv")):
            frames.append(read_drought_csv(p, idx))

    if not frames:
        raise FileNotFoundError(f"No drought CSVs found under {BASE_DIR}")

    monthly = pd.concat(frames, ignore_index=True)
    monthly = monthly.sort_values(["index", "county_norm", "year", "month"]).reset_index(drop=True)
    return monthly


def aggregate_county_year(monthly: pd.DataFrame) -> pd.DataFrame:
    m = monthly.copy()

    def _agg(group: pd.DataFrame) -> pd.Series:
        g = group
        ann = g["value"].mean()
        may_sep = g.loc[g["month"].between(5, 9), "value"]
        jul_sep = g.loc[g["month"].between(7, 9), "value"]
        aug_sep = g.loc[g["month"].between(8, 9), "value"]

        return pd.Series(
            {
                "annual_mean": ann,
                "may_sep_mean": float(may_sep.mean()) if len(may_sep) else np.nan,
                "jul_sep_mean": float(jul_sep.mean()) if len(jul_sep) else np.nan,
                "aug_sep_mean": float(aug_sep.mean()) if len(aug_sep) else np.nan,
                "may_sep_min": float(may_sep.min()) if len(may_sep) else np.nan,
                "may_sep_months": int(len(may_sep)),
                "may_sep_mod_drought_months": int((may_sep <= -2).sum()) if len(may_sep) else 0,
                "may_sep_sev_drought_months": int((may_sep <= -3).sum()) if len(may_sep) else 0,
                "n_months": int(len(g)),
            }
        )

    agg = (
        m.groupby(["county_raw", "county_norm", "index", "year"], as_index=False)
        .apply(_agg)
        .reset_index(drop=True)
    )
    return agg


def load_county_to_district_map() -> pd.DataFrame:
    """
    Uses NASS yield file (it contains Ag District per county) to build a stable mapping.
    """
    p = Path("data/nass/Soybean_Yield_BU:Acre_By_County.csv")
    df = pd.read_csv(p)
    df = df[(df["State"] == "MARYLAND") & (df["Geo Level"] == "COUNTY") & (df["Period"] == "YEAR")].copy()
    df = df[df["Commodity"] == "SOYBEANS"]
    df = df[df["Data Item"] == "SOYBEANS - YIELD, MEASURED IN BU / ACRE"]

    df["County"] = df["County"].astype(str)
    df = df[df["County"].str.upper() != "OTHER COUNTIES"].copy()
    df["county_norm"] = df["County"].map(normalize_county_name)
    df["district"] = df["Ag District"].astype(str).str.upper().str.strip()
    df = df[df["district"].ne("") & df["district"].ne("NAN")]

    # Mode district per county across years
    mode = (
        df.groupby("county_norm")["district"]
        .agg(lambda s: s.value_counts().index[0] if len(s.value_counts()) else np.nan)
        .reset_index()
    )
    return mode.dropna()


def aggregate_district_year(county_year: pd.DataFrame, county_to_district: pd.DataFrame) -> pd.DataFrame:
    d = county_year.merge(county_to_district, on="county_norm", how="left")
    d = d.dropna(subset=["district"]).copy()

    # Mean across counties within district-year for each index/metric
    metrics = [
        "annual_mean",
        "may_sep_mean",
        "jul_sep_mean",
        "aug_sep_mean",
        "may_sep_min",
        "may_sep_months",
        "may_sep_mod_drought_months",
        "may_sep_sev_drought_months",
        "n_months",
    ]
    out = d.groupby(["district", "index", "year"], as_index=False)[metrics].mean(numeric_only=True)
    out = out.sort_values(["district", "index", "year"]).reset_index(drop=True)
    return out


def main() -> None:
    monthly = build_monthly()
    monthly_out = OUT_DIR / "drought_monthly_county.csv"
    monthly.to_csv(monthly_out, index=False)

    county_year = aggregate_county_year(monthly)
    county_year_out = OUT_DIR / "drought_aggregates_county_year.csv"
    county_year.to_csv(county_year_out, index=False)

    county_to_district = load_county_to_district_map()
    district_year = aggregate_district_year(county_year, county_to_district)
    district_year_out = OUT_DIR / "drought_aggregates_district_year.csv"
    district_year.to_csv(district_year_out, index=False)

    print(f"Saved monthly county drought: {monthly_out}")
    print(f"Saved county-year drought aggregates: {county_year_out}")
    print(f"Saved district-year drought aggregates: {district_year_out}")


if __name__ == "__main__":
    main()

