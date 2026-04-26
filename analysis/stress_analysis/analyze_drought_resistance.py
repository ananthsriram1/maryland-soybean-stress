#!/usr/bin/env python3
"""
Results-ready drought figures:

1) Show drought has a substantial effect on yield:
   - Yield distributions across drought severity bins (PDSI May–Sep mean)

2) Show "drought resistance" counties:
   - For each county, compare yield in drought years vs non-drought years.
   - Counties with drought resistance should lie near the 1:1 line (no yield penalty).

Uses:
  - County yield (1997+): data/processed_yield/by_county/yield_*.csv
  - Drought aggregates:    data/processed_drought/drought_aggregates_county_year.csv
  - Irrigation census:     data/nass/IrrigatedAcresHarvestedByCounty.csv (optional overlay)

Outputs:
  - outputs/DroughtEffect/yield_by_drought_class_boxplot.png
  - outputs/DroughtEffect/county_drought_resistance_scatter.png
  - outputs/DroughtEffect/county_drought_resistance_table.csv
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = Path("outputs/DroughtEffect")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PDSI_DROUGHT_THRESHOLD = -2.0  # moderate+ drought
PDSI_NON_DROUGHT_MIN = -1.0   # near-normal and wetter

CENSUS_YEARS = [1997, 2002, 2007, 2012, 2017, 2022]


def normalize_county_name(name: str) -> str:
    s = str(name).upper().strip()
    s = s.replace("COUNTY", "").strip()
    s = s.replace("&", "AND")
    s = re.sub(r"[.'’]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_county_yield_long() -> pd.DataFrame:
    base = Path("data/processed_yield/by_county")
    paths = sorted(base.glob("yield_*.csv"))
    if not paths:
        raise FileNotFoundError(f"No files found in {base}")

    frames = []
    for p in paths:
        df = pd.read_csv(p)
        if not {"Year", "County", "District", "Yield"}.issubset(df.columns):
            continue
        df = df.copy()
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
        df["Yield"] = pd.to_numeric(df["Yield"], errors="coerce")
        df["County"] = df["County"].astype(str)
        df["county_norm"] = df["County"].map(normalize_county_name)
        df["District"] = df["District"].astype(str).str.upper().str.strip()
        frames.append(df[["Year", "county_norm", "District", "Yield"]])

    y = pd.concat(frames, ignore_index=True)
    y = y.dropna(subset=["Year", "Yield", "county_norm"]).copy()
    y["Year"] = y["Year"].astype(int)
    y = y.rename(columns={"Yield": "yield"})
    # If duplicates exist (rare), average them.
    y = y.groupby(["Year", "county_norm", "District"], as_index=False)["yield"].mean()
    return y


def load_county_pdsi(metric: str = "may_sep_mean") -> pd.DataFrame:
    p = Path("data/processed_drought/drought_aggregates_county_year.csv")
    d = pd.read_csv(p)
    d["index"] = d["index"].astype(str).str.upper().str.strip()
    d = d[d["index"] == "PDSI"].copy()
    d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    d = d.dropna(subset=["year", "county_norm"]).copy()
    d["year"] = d["year"].astype(int)
    if metric not in d.columns:
        raise ValueError(f"Metric '{metric}' not found in {p}")
    d[metric] = pd.to_numeric(d[metric], errors="coerce")
    return d[["year", "county_norm", metric]].rename(columns={"year": "Year", metric: "pdsi"})


def _to_number(val) -> float:
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if "(D" in s or s in {"(D)", " (D)"}:
        return np.nan
    s = s.replace(",", "").strip()
    s = re.sub(r"[^\d\.\-]", "", s)
    return float(s) if s != "" else np.nan


def census_year_for_year(year: int) -> int:
    candidates = [y for y in CENSUS_YEARS if y <= year]
    return max(candidates) if candidates else min(CENSUS_YEARS)


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
    df["irrigated_acres"] = df["Value"].map(_to_number)
    df["irrigation_row_present"] = True
    out = df[["Year", "county_norm", "irrigated_acres", "irrigation_row_present"]].drop_duplicates(["Year", "county_norm"])
    return out.rename(columns={"Year": "census_year"})


def drought_class(pdsi: float) -> str:
    if pd.isna(pdsi):
        return "unknown"
    if pdsi <= -3:
        return "severe drought"
    if pdsi <= -2:
        return "moderate drought"
    if pdsi <= -1:
        return "mild dry"
    if pdsi >= 1:
        return "wet"
    return "near normal"


def plot_yield_by_drought_class(df: pd.DataFrame, outpath: Path) -> None:
    sub = df.dropna(subset=["yield", "pdsi"]).copy()
    if sub.empty:
        return

    sub["drought_class"] = sub["pdsi"].map(drought_class)
    order = ["severe drought", "moderate drought", "mild dry", "near normal", "wet"]

    data = [sub[sub["drought_class"] == c]["yield"].values for c in order]
    labels = ["severe\n(≤-3)", "moderate\n(≤-2)", "mild dry\n(≤-1)", "near\n(-1..1)", "wet\n(≥1)"]

    fig, ax = plt.subplots(figsize=(12, 6.5))
    bp = ax.boxplot(data, labels=labels, showmeans=True, patch_artist=True)

    colors = ["#C0392B", "#E67E22", "#F1C40F", "#95A5A6", "#2E86AB"]
    for box, col in zip(bp["boxes"], colors):
        box.set_facecolor(col)
        box.set_alpha(0.55)
        box.set_edgecolor("black")
        box.set_linewidth(1.0)
    for key in ["whiskers", "caps", "medians", "means"]:
        for item in bp[key]:
            item.set_color("black")
            item.set_linewidth(1.1)

    ax.set_title("County soybean yield decreases as drought severity increases\n(PDSI May–Sep mean)", fontweight="bold")
    ax.set_ylabel("Yield (bu/acre)")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()


def resistance_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each county:
      - baseline = mean yield in non-drought years (pdsi >= -1)
      - drought   = mean yield in drought years (pdsi <= -2)
      - delta     = drought - baseline (near 0 = resistant)
    """
    sub = df.dropna(subset=["yield", "pdsi"]).copy()
    if sub.empty:
        return pd.DataFrame()

    sub["is_drought"] = sub["pdsi"] <= PDSI_DROUGHT_THRESHOLD
    sub["is_baseline"] = sub["pdsi"] >= PDSI_NON_DROUGHT_MIN

    rows = []
    for county, g in sub.groupby("county_norm"):
        gd = g[g["is_drought"]]
        gb = g[g["is_baseline"]]
        if len(gd) < 2 or len(gb) < 3:
            continue
        baseline = float(gb["yield"].mean())
        drought = float(gd["yield"].mean())
        delta = drought - baseline
        pct = (delta / baseline) * 100.0 if baseline != 0 else np.nan

        district = g["District"].mode().iloc[0] if not g["District"].mode().empty else ""
        rows.append(
            {
                "county": county,
                "district": district,
                "n_baseline_years": int(len(gb)),
                "n_drought_years": int(len(gd)),
                "yield_baseline_mean": baseline,
                "yield_drought_mean": drought,
                "yield_delta": delta,
                "yield_pct_change": pct,
                "pdsi_baseline_mean": float(gb["pdsi"].mean()),
                "pdsi_drought_mean": float(gd["pdsi"].mean()),
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values("yield_pct_change", ascending=False).reset_index(drop=True)
    return out


def plot_resistance_scatter(res: pd.DataFrame, irrigation_overlay: pd.DataFrame, outpath: Path) -> None:
    if res.empty:
        return

    # attach irrigation: average irrigated acres in the 2017 census snapshot (proxy for modern irrigation footprint)
    irr2017 = irrigation_overlay[irrigation_overlay["census_year"] == 2017][["county_norm", "irrigated_acres"]].copy()
    irr2017 = irr2017.rename(columns={"county_norm": "county"})
    rr = res.merge(irr2017, on="county", how="left")
    rr["irrigated_acres"] = pd.to_numeric(rr["irrigated_acres"], errors="coerce").fillna(0.0)

    x = rr["yield_baseline_mean"].to_numpy(dtype=float)
    y = rr["yield_drought_mean"].to_numpy(dtype=float)

    sizes = 40 + np.sqrt(rr["irrigated_acres"].to_numpy(dtype=float)) * 1.2
    sizes = np.clip(sizes, 40, 320)

    fig, ax = plt.subplots(figsize=(9.5, 9.0))
    ax.scatter(x, y, s=sizes, c="#2E86AB", alpha=0.75, edgecolor="black", linewidth=0.4)

    # 1:1 line
    lo = float(np.nanmin([x.min(), y.min()])) - 1
    hi = float(np.nanmax([x.max(), y.max()])) + 1
    ax.plot([lo, hi], [lo, hi], color="#D1495B", linewidth=2.0, linestyle="--", alpha=0.8)

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.25)
    ax.set_xlabel("County mean yield in non-drought years (PDSI ≥ -1)")
    ax.set_ylabel("County mean yield in drought years (PDSI ≤ -2)")
    ax.set_title("Drought resistance: counties near the 1:1 line maintain yield in drought\n(point size ∝ irrigated acres, 2017 census)", fontweight="bold")

    # Annotate top 8 resistant + top 8 sensitive
    top = rr.sort_values("yield_pct_change", ascending=False).head(8)
    bot = rr.sort_values("yield_pct_change", ascending=True).head(8)
    ann = pd.concat([top, bot], ignore_index=True)
    for _, r in ann.iterrows():
        ax.annotate(
            r["county"].title(),
            (r["yield_baseline_mean"], r["yield_drought_mean"]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#bbbbbb", alpha=0.9),
        )

    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    y = load_county_yield_long()
    pdsi = load_county_pdsi(metric="may_sep_mean")
    df = y.merge(pdsi, on=["Year", "county_norm"], how="left")

    # Attach irrigation snapshot per year (not required for table/boxplot, but helpful context)
    irr = load_irrigation_census()
    df["census_year"] = df["Year"].map(census_year_for_year)
    df = df.merge(irr, on=["census_year", "county_norm"], how="left")
    # for sizing in other plots, treat missing census row as 0 acres
    df["irrigation_row_present"] = df["irrigation_row_present"].fillna(False)
    df["irrigated_acres_filled"] = pd.to_numeric(df["irrigated_acres"], errors="coerce")
    df.loc[~df["irrigation_row_present"], "irrigated_acres_filled"] = 0.0
    df["irrigated_acres_filled"] = df["irrigated_acres_filled"].fillna(0.0)

    plot_yield_by_drought_class(df, OUT_DIR / "yield_by_drought_class_boxplot.png")

    res = resistance_table(df)
    res_out = OUT_DIR / "county_drought_resistance_table.csv"
    res.to_csv(res_out, index=False)

    plot_resistance_scatter(res, irr, OUT_DIR / "county_drought_resistance_scatter.png")

    print(f"Saved: {OUT_DIR / 'yield_by_drought_class_boxplot.png'}")
    print(f"Saved: {res_out}")
    print(f"Saved: {OUT_DIR / 'county_drought_resistance_scatter.png'}")


if __name__ == "__main__":
    main()

