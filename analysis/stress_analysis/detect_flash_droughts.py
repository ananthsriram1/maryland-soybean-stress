#!/usr/bin/env python3
"""
Detect "flash drought" occurrences from monthly Palmer indices (PDSI/PHDI/PMDI).

Important limitation:
  Flash drought definitions are typically weekly (2–8 weeks), and often use USDM category
  jumps and/or atmospheric demand (EDDI). This repo currently has monthly Palmer indices
  only (no USDM, no EDDI), so this script implements a *monthly proxy*:

  - Time window: 1–2 months (≈4–8 weeks)
  - Intensification: drought severity worsens by >= 2 categories within that window
    (USDM-like categories derived from Palmer thresholds)
  - Persistence: the peak category is sustained for >= 1 additional month

Outputs:
  outputs/FlashDrought/flash_drought_events_proxy.csv
  outputs/FlashDrought/flash_drought_counts_by_year_index.csv
  outputs/FlashDrought/flash_drought_counts_timeseries.png
  outputs/FlashDrought/flash_drought_descriptive_by_year_index.csv
  outputs/FlashDrought/flash_drought_descriptive_summary.png
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


IN_MONTHLY = Path("data/processed_drought/drought_monthly_county.csv")
OUT_DIR = Path("outputs/FlashDrought")
OUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Params:
    lookahead_months: int = 1          # 1 month ≈ 4 weeks (data are monthly)
    min_category_jump: int = 2         # "two-category change" proxy
    min_value_drop: float = 0.0        # keep aligned to "category jump" definition; still reported
    persist_months: int = 1            # monthly proxy for "sustained" (stricter than 2 weeks)


def palmer_severity_category(v: float) -> int:
    """
    Map Palmer value to a USDM-like severity scale.

    Returns integer severity where bigger = drier:
      0 = wet/near-normal (>= -1)
      1 = D0 ([-2, -1))
      2 = D1 ([-3, -2))
      3 = D2 ([-4, -3))
      4 = D3 ([-5, -4))
      5 = D4 (<= -5)

    Note: Palmer isn't USDM; this is a proxy for category jumps only.
    """
    if not np.isfinite(v):
        return -1
    if v >= -1.0:
        return 0
    if v >= -2.0:
        return 1
    if v >= -3.0:
        return 2
    if v >= -4.0:
        return 3
    if v >= -5.0:
        return 4
    return 5


def load_monthly() -> pd.DataFrame:
    if not IN_MONTHLY.exists():
        raise FileNotFoundError(
            f"Missing {IN_MONTHLY}. Run python -m analysis.preprocessing.preprocess_palmer_indices first."
        )
    df = pd.read_csv(IN_MONTHLY)
    df["index"] = df["index"].astype(str).str.upper().str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["county_norm", "index", "year", "month", "value"]).copy()
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    df = df.sort_values(["index", "county_norm", "date"]).reset_index(drop=True)
    return df


def detect_events_for_series(g: pd.DataFrame, params: Params) -> list[dict]:
    """
    g: one county + one index, sorted by date, monthly frequency
    """
    dates = g["date"].to_numpy()
    vals = g["value"].to_numpy(dtype=float)
    sev = np.array([palmer_severity_category(v) for v in vals], dtype=int)

    events: list[dict] = []
    i = 0
    n = len(g)
    while i < n:
        if sev[i] < 0:
            i += 1
            continue

        found = False
        # search earliest peak within lookahead that meets category jump and value drop
        for k in range(1, params.lookahead_months + 1):
            j = i + k
            if j >= n or sev[j] < 0:
                continue
            cat_jump = sev[j] - sev[i]
            val_drop = vals[i] - vals[j]  # positive if drying (value decreases)
            if cat_jump >= params.min_category_jump and val_drop >= params.min_value_drop:
                peak_idx = j
                peak_sev = sev[peak_idx]
                # persistence check: hold peak category for persist_months beyond peak
                persist_ok = True
                for p in range(1, params.persist_months + 1):
                    t = peak_idx + p
                    if t >= n or sev[t] < peak_sev:
                        persist_ok = False
                        break
                if not persist_ok:
                    continue

                # define a minimal event window: onset month -> peak month, plus sustain-through month
                sustain_through = min(n - 1, peak_idx + params.persist_months)
                events.append(
                    {
                        "county_norm": g["county_norm"].iloc[0],
                        "index": g["index"].iloc[0],
                        "start_date": pd.Timestamp(dates[i]),
                        "peak_date": pd.Timestamp(dates[peak_idx]),
                        "sustain_through_date": pd.Timestamp(dates[sustain_through]),
                        "start_value": float(vals[i]),
                        "peak_value": float(vals[peak_idx]),
                        "value_drop": float(val_drop),
                        "start_severity": int(sev[i]),
                        "peak_severity": int(peak_sev),
                        "category_jump": int(cat_jump),
                        "lookahead_months_used": int(k),
                    }
                )
                # skip ahead to reduce overlapping detections
                i = sustain_through + 1
                found = True
                break
        if not found:
            i += 1

    return events


def detect_all(df: pd.DataFrame, params: Params) -> pd.DataFrame:
    rows: list[dict] = []
    for (_, _), g in df.groupby(["index", "county_norm"], sort=False):
        g = g.sort_values("date")
        rows.extend(detect_events_for_series(g, params))
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["start_year"] = out["start_date"].dt.year
    out["peak_year"] = out["peak_date"].dt.year
    return out.sort_values(["index", "county_norm", "start_date"]).reset_index(drop=True)


def summarize(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    s = (
        events.groupby(["index", "start_year"], as_index=False)
        .agg(n_events=("start_date", "count"))
        .sort_values(["index", "start_year"])
    )
    return s


def summarize_descriptive(events: pd.DataFrame, monthly: pd.DataFrame) -> pd.DataFrame:
    """
    Add descriptiveness:
      - n_counties_total (per index)
      - n_counties_with_event (per index-year)
      - pct_counties_affected
      - mean_value_drop / mean_category_jump / mean_lookahead
    """
    if events.empty:
        return pd.DataFrame()

    counties_total = monthly.groupby("index", as_index=False)["county_norm"].nunique().rename(columns={"county_norm": "n_counties_total"})

    by = (
        events.groupby(["index", "start_year"], as_index=False)
        .agg(
            n_events=("start_date", "count"),
            n_counties_with_event=("county_norm", "nunique"),
            mean_value_drop=("value_drop", "mean"),
            mean_category_jump=("category_jump", "mean"),
            mean_lookahead_months=("lookahead_months_used", "mean"),
        )
        .rename(columns={"start_year": "year"})
    )

    out = by.merge(counties_total, on="index", how="left")
    out["pct_counties_affected"] = (out["n_counties_with_event"] / out["n_counties_total"]) * 100.0
    return out.sort_values(["index", "year"]).reset_index(drop=True)


def plot_counts(summary: pd.DataFrame, outpath: Path) -> None:
    if summary.empty:
        return
    indices = sorted(summary["index"].unique())
    n = len(indices)
    fig, axes = plt.subplots(n, 1, figsize=(12, 3.6 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, idx in zip(axes, indices):
        sub = summary[summary["index"] == idx]
        ax.bar(sub["start_year"], sub["n_events"], color="#2E86AB", alpha=0.8)
        ax.set_title(f"Flash-drought proxy events per year ({idx})", fontweight="bold")
        ax.set_ylabel("Event count")
        ax.grid(axis="y", alpha=0.25)

    axes[-1].set_xlabel("Year")
    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()


def plot_descriptive(descr: pd.DataFrame, outpath: Path) -> None:
    if descr.empty:
        return

    indices = sorted(descr["index"].unique())
    n = len(indices)
    fig, axes = plt.subplots(n, 1, figsize=(14, 4.6 * n), sharex=True)
    if n == 1:
        axes = [axes]

    # Bars only: annual event counts (Palmer proxy). Definition belongs in caption.
    axis_label_fs = 14
    tick_label_fs = 13
    title_fs = 14
    base_year_label_fs = 11

    # Shared y-axis scale across indices so counts are visually comparable.
    global_max = float(descr["n_events"].max()) if "n_events" in descr.columns and len(descr) else 0.0
    ylim_hi = (global_max * 1.18) if global_max > 0 else 1.0

    for ax, idx in zip(axes, indices):
        sub = descr[descr["index"] == idx].copy()
        years = sub["year"].astype(int).to_numpy()

        ax.bar(years, sub["n_events"], color="#2E86AB", alpha=0.75, zorder=2)
        ax.set_ylabel("Events (count)", fontsize=axis_label_fs, fontweight="bold", labelpad=10)
        ax.tick_params(axis="y", labelsize=tick_label_fs)
        ax.tick_params(axis="x", labelsize=tick_label_fs, labelbottom=True)
        ax.grid(axis="y", alpha=0.25, zorder=0)
        ax.set_title(f"Flash-drought proxy events per year ({idx})", fontweight="bold", fontsize=title_fs)
        ax.set_ylim(0, ylim_hi)

        # Label every year where events occur (not just the peaks).
        # Keep labels compact to avoid clutter when embedded.
        n_labeled = int((sub["n_events"].astype(float) > 0).sum())
        year_label_fs = 9 if n_labeled >= 10 else (10 if n_labeled >= 7 else base_year_label_fs)
        for _, r in sub.iterrows():
            if float(r["n_events"]) <= 0:
                continue
            ax.annotate(
                str(int(r["year"])),
                (int(r["year"]), float(r["n_events"])),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=year_label_fs,
                fontweight="bold",
                zorder=6,
                clip_on=False,
            )

    axes[-1].set_xlabel("Year", fontsize=axis_label_fs, fontweight="bold", labelpad=12)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    params = Params()
    df = load_monthly()
    events = detect_all(df, params)

    events_out = OUT_DIR / "flash_drought_events_proxy.csv"
    events.to_csv(events_out, index=False)

    summary = summarize(events)
    summary_out = OUT_DIR / "flash_drought_counts_by_year_index.csv"
    summary.to_csv(summary_out, index=False)

    plot_counts(summary, OUT_DIR / "flash_drought_counts_timeseries.png")

    descr = summarize_descriptive(events, df)
    descr_out = OUT_DIR / "flash_drought_descriptive_by_year_index.csv"
    descr.to_csv(descr_out, index=False)
    plot_descriptive(descr, OUT_DIR / "flash_drought_descriptive_summary.png")

    print(f"Saved events: {events_out}")
    print(f"Saved summary: {summary_out}")
    print(f"Saved plot: {OUT_DIR / 'flash_drought_counts_timeseries.png'}")
    print(f"Saved descriptive summary: {descr_out}")
    print(f"Saved descriptive plot: {OUT_DIR / 'flash_drought_descriptive_summary.png'}")


if __name__ == "__main__":
    main()

