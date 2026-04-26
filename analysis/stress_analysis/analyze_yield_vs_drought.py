#!/usr/bin/env python3
"""
Analyze whether soybean yield correlates with drought.

Primary outputs:
  outputs/YieldVsDrought/correlation_summary_district.csv
  outputs/YieldVsDrought/low_yield_years_vs_drought_district.csv
  outputs/YieldVsDrought/district_yield_vs_drought_scatter.png

Notes:
  - Uses district-level yield from data/processed_yield/yield_district_averages_by_year.csv
  - Uses district-level drought aggregates from data/processed_drought/drought_aggregates_district_year.csv
  - Drought severity is interpreted as lower Palmer index = drier. We report both:
      (a) yield vs Palmer index (expect positive correlation if drought reduces yield)
      (b) yield vs dryness = -Palmer index (expect negative correlation)
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = Path("outputs/YieldVsDrought")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _pearson(x: pd.Series, y: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    m = x.notna() & y.notna()
    if m.sum() < 3:
        return np.nan
    return float(np.corrcoef(x[m], y[m])[0, 1])


def _spearman(x: pd.Series, y: pd.Series) -> float:
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    m = x.notna() & y.notna()
    if m.sum() < 3:
        return np.nan
    rx = x[m].rank()
    ry = y[m].rank()
    return float(np.corrcoef(rx, ry)[0, 1])


def load_district_yield() -> pd.DataFrame:
    p = Path("data/processed_yield/yield_district_averages_by_year.csv")
    y = pd.read_csv(p)
    y = y.rename(columns={"Yield_mean": "yield"})
    y["District"] = y["District"].astype(str).str.upper().str.strip()
    y["Year"] = pd.to_numeric(y["Year"], errors="coerce").astype("Int64")
    y["yield"] = pd.to_numeric(y["yield"], errors="coerce")
    y = y.dropna(subset=["Year", "yield"]).copy()
    y["Year"] = y["Year"].astype(int)
    return y[["District", "Year", "yield"]].sort_values(["District", "Year"])


def load_district_drought(index: str = "PDSI", metric: str = "may_sep_mean") -> pd.DataFrame:
    p = Path("data/processed_drought/drought_aggregates_district_year.csv")
    d = pd.read_csv(p)
    d["district"] = d["district"].astype(str).str.upper().str.strip()
    d["index"] = d["index"].astype(str).str.upper().str.strip()
    d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    d = d.dropna(subset=["year"]).copy()
    d["year"] = d["year"].astype(int)

    if metric not in d.columns:
        raise ValueError(f"Metric '{metric}' not found in {p}. Available: {list(d.columns)}")

    d[metric] = pd.to_numeric(d[metric], errors="coerce")
    d = d[(d["index"] == index.upper())].copy()
    return d[["district", "year", metric]].rename(columns={"district": "District", "year": "Year", metric: "palmer"})


def correlation_summary(merged: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for district, g in merged.groupby("District"):
        rows.append(
            {
                "District": district,
                "n_years": int(g[["yield", "palmer"]].dropna().shape[0]),
                "pearson_yield_vs_palmer": _pearson(g["yield"], g["palmer"]),
                "spearman_yield_vs_palmer": _spearman(g["yield"], g["palmer"]),
                "pearson_yield_vs_dryness": _pearson(g["yield"], -g["palmer"]),
                "spearman_yield_vs_dryness": _spearman(g["yield"], -g["palmer"]),
            }
        )
    out = pd.DataFrame(rows).sort_values("pearson_yield_vs_dryness")
    return out


def low_yield_years_table(merged: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    out_frames = []
    for district, g in merged.groupby("District"):
        gg = g.dropna(subset=["yield", "palmer"]).sort_values("yield").head(k).copy()
        gg["dryness"] = -gg["palmer"]
        gg["yield_rank_low"] = np.arange(1, len(gg) + 1)
        out_frames.append(gg[["District", "Year", "yield", "palmer", "dryness", "yield_rank_low"]])
    out = pd.concat(out_frames, ignore_index=True) if out_frames else pd.DataFrame()
    return out.sort_values(["District", "yield_rank_low"])


def plot_scatter(merged: pd.DataFrame, outpath: Path) -> None:
    districts = sorted(merged["District"].unique())
    if not districts:
        return

    n = len(districts)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4.8 * nrows), squeeze=False)

    for i, district in enumerate(districts):
        ax = axes[i // ncols][i % ncols]
        g = merged[merged["District"] == district].dropna(subset=["yield", "palmer"]).copy()
        ax.scatter(g["palmer"], g["yield"], s=55, alpha=0.85, edgecolor="black", linewidth=0.6)

        r = _pearson(g["yield"], g["palmer"])
        ax.set_title(f"{district.title()} (r={r:.2f})" if np.isfinite(r) else district.title(), fontweight="bold")
        ax.set_xlabel("PDSI (May–Sep mean)  ↑ wetter / ↓ drier")
        ax.set_ylabel("Yield (bu/acre)")
        ax.grid(alpha=0.25)

        # simple linear fit for visual guidance
        if len(g) >= 3 and g["palmer"].notna().sum() >= 3:
            x = g["palmer"].to_numpy()
            y = g["yield"].to_numpy()
            m, b = np.polyfit(x, y, 1)
            xs = np.linspace(np.nanmin(x), np.nanmax(x), 100)
            ax.plot(xs, m * xs + b, color="red", linewidth=2, alpha=0.7)

    # hide unused axes
    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")

    fig.suptitle("District soybean yield vs drought (PDSI, May–Sep mean)", fontsize=16, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    # Ensure drought preprocessing has been run
    if not Path("data/processed_drought/drought_aggregates_district_year.csv").exists():
        raise FileNotFoundError(
            "Missing data/processed_drought/drought_aggregates_district_year.csv. "
            "Run python -m analysis.preprocessing.preprocess_palmer_indices first."
        )

    y = load_district_yield()
    d = load_district_drought(index="PDSI", metric="may_sep_mean")
    merged = y.merge(d, on=["District", "Year"], how="inner")

    corr = correlation_summary(merged)
    corr_out = OUT_DIR / "correlation_summary_district.csv"
    corr.to_csv(corr_out, index=False)

    low = low_yield_years_table(merged, k=6)
    low_out = OUT_DIR / "low_yield_years_vs_drought_district.csv"
    low.to_csv(low_out, index=False)

    fig_out = OUT_DIR / "district_yield_vs_drought_scatter.png"
    plot_scatter(merged, fig_out)

    print(f"Saved: {corr_out}")
    print(f"Saved: {low_out}")
    print(f"Saved: {fig_out}")


if __name__ == "__main__":
    main()

