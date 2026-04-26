#!/usr/bin/env python3
"""Generate manuscript Figure 6: yield by PDSI drought class, faceted by district.

This is the canonical Option D extraction from the original multi-option generator:
  scripts/Analysis/DroughtEffectFigureOptions.py

The original script produced Options A–E for comparison. For the manuscript,
Option D was selected. The full A–E generator is preserved verbatim at:
  archive/figure_drafts/DroughtEffectFigureOptions.py

Outputs (descriptive):
  outputs/DroughtEffect/Options/OptionD_ByDistrict_SmallMultiples_v3_largerAxisLabels_2col_3rows.png

Note: This script intentionally produces ONLY the canonical manuscript variant
(no other OptionD layouts; no per-district split PNGs).
"""

from __future__ import annotations

# --- BEGIN: copied verbatim from scripts/Analysis/DroughtEffectFigureOptions.py ---
import re
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = Path("outputs/DroughtEffect/Options")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# SI conversion for soybean yield:
# 1 bushel soybean = 60 lb = 27.2155 kg; 1 acre = 0.404685642 ha
# => (bu/ac) * 27.2155 / 0.404685642 = 67.251 kg/ha
BUAC_TO_KGHA = 67.251


def _yield_ylim_kgha_lower_step500(y_min_kgha: float) -> float:
    """Largest multiple of 500 kg/ha at or below the data minimum (axis start, not forced to 0)."""
    return float(np.floor(float(y_min_kgha) / 500.0) * 500.0)


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


ORDER = ["severe drought", "moderate drought", "mild dry", "near normal", "wet"]
LABELS = ["severe\n(≤-3)", "moderate\n(≤-2)", "mild dry\n(≤-1)", "near normal\n(-1..1)", "wet\n(≥1)"]
# Short names for readable x-ticks (two lines: name + n). Middle labels shortened vs. "Near normal" to reduce crowding.
SHORT_CLASS = ["Severe", "Moderate", "Mild dry", "Near norm.", "Wet"]
PDSI_RULE = ["≤−3", "≤−2", "≤−1", "−1…1", "≥+1"]
COLORS = ["#C0392B", "#E67E22", "#F1C40F", "#95A5A6", "#2E86AB"]

# PDSI bin text in key panel (sans-serif; size/spacing set in _fill_key_panel)
PDSI_KEY_BLOCK = (
    "May–Sep mean PDSI (class rules)\n\n"
    "Severe           PDSI ≤ −3\n"
    "Moderate         PDSI ≤ −2\n"
    "Mild dry         PDSI ≤ −1\n"
    "Near norm.       −1 to 1\n"
    "Wet              PDSI ≥ +1"
)


def _option_d_legend_handles() -> list:
    """Visual key: thick median line + white circle mean (matches manuscript)."""
    return [
        plt.Line2D([0], [0], color="black", linewidth=2.8, solid_capstyle="round", label="Median"),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="black",
            markerfacecolor="white",
            markeredgecolor="black",
            markersize=11,
            markeredgewidth=1.4,
            linestyle="none",
            label="Mean",
        ),
    ]


def prep() -> pd.DataFrame:
    y = load_county_yield_long()
    pdsi = load_county_pdsi(metric="may_sep_mean")
    df = y.merge(pdsi, on=["Year", "county_norm"], how="inner")
    df = df.dropna(subset=["yield", "pdsi"]).copy()
    df["drought_class"] = df["pdsi"].map(drought_class)
    df = df[df["drought_class"].isin(ORDER)].copy()
    return df


def _compute_global_yield_ylim_kgha(df: pd.DataFrame) -> Tuple[float, float]:
    y = (df["yield"] * BUAC_TO_KGHA).to_numpy(dtype=float)
    y = y[np.isfinite(y)]
    if len(y) == 0:
        return (0.0, 1.0)
    lo = _yield_ylim_kgha_lower_step500(float(np.nanmin(y)))
    hi = float(np.nanmax(y))
    pad = max((hi - lo) * 0.12, 120.0)
    return (lo, hi + pad)


def _format_xticks_with_n(ax, sub: pd.DataFrame, *, x_style: str) -> None:
    ns = [int((sub[sub["drought_class"] == c]).shape[0]) for c in ORDER]
    if x_style == "name_only_n_above":
        ax.set_xticklabels(SHORT_CLASS, fontweight="bold")
        y0, y1 = ax.get_ylim()
        y = y1 - 0.06 * (y1 - y0)
        for i, n in enumerate(ns):
            ax.text(i + 1, y, f"n={n}", ha="center", va="top", fontsize=11, fontweight="bold")
    else:
        # default: name + n under
        ax.set_xticklabels([f"{name}\n(n={n})" for name, n in zip(SHORT_CLASS, ns)], fontweight="bold")


def _district_boxplot_axes(
    ax,
    sub: pd.DataFrame,
    *,
    medianprops,
    meanprops,
    whiskerprops,
    capprops,
    xtick_fs: int,
    x_style: str = "name_n_under",
    ylim_shared: Optional[Tuple[float, float]] = None,
) -> None:
    data = [(sub[sub["drought_class"] == c]["yield"] * BUAC_TO_KGHA).values for c in ORDER]
    bp = ax.boxplot(
        data,
        patch_artist=True,
        showmeans=True,
        meanprops=meanprops,
        medianprops=medianprops,
        whiskerprops=whiskerprops,
        capprops=capprops,
        showfliers=False,
    )

    # Color boxes by drought class (must use bp["boxes"]; ax.artists is unreliable across Matplotlib versions).
    for patch, color in zip(bp["boxes"], COLORS):
        patch.set_facecolor(color)
        patch.set_edgecolor("black")
        patch.set_alpha(0.88)

    ax.set_xticks(range(1, len(ORDER) + 1))
    _format_xticks_with_n(ax, sub, x_style=x_style)
    for tick in ax.get_xticklabels():
        tick.set_fontsize(xtick_fs)

    ax.grid(axis="y", alpha=0.25)
    ax.grid(axis="x", visible=False)
    if ylim_shared is not None:
        ax.set_ylim(ylim_shared)

    # County-year correlation: yield vs continuous PDSI (manuscript annotates r in red).
    pstd = sub["pdsi"].std(skipna=True)
    if sub.shape[0] >= 2 and pd.notna(pstd) and float(pstd) > 0:
        yv = (sub["yield"] * BUAC_TO_KGHA).astype(float)
        pv = sub["pdsi"].astype(float)
        m = yv.notna() & pv.notna()
        if int(m.sum()) >= 2:
            r = float(yv[m].corr(pv[m]))
            if np.isfinite(r):
                ax.text(
                    0.98,
                    0.02,
                    f"r = {r:.2f}",
                    transform=ax.transAxes,
                    ha="right",
                    va="bottom",
                    fontsize=12,
                    fontweight="bold",
                    color="crimson",
                )


def _fill_key_panel(key_ax, handles: list) -> None:
    """Spare grid cell: matplotlib legend (icons) + PDSI mapping (roomy padding + line spacing)."""
    key_ax.axis("off")
    key_ax.set_xlim(0, 1)
    key_ax.set_ylim(0, 1)
    key_ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.96),
        fontsize=14,
        title="Key",
        title_fontsize=17,
        frameon=True,
        fancybox=True,
        shadow=False,
        framealpha=1.0,
        facecolor="white",
        edgecolor="#888888",
        labelspacing=1.35,
        handlelength=3.4,
        handleheight=1.55,
        borderpad=1.05,
        handletextpad=0.9,
        columnspacing=1.2,
    )
    key_ax.text(
        0.5,
        0.30,
        PDSI_KEY_BLOCK,
        ha="center",
        va="center",
        fontsize=13,
        linespacing=1.85,
        family="sans-serif",
        bbox=dict(boxstyle="round,pad=1.05", facecolor="#f8f8f8", edgecolor="#bbbbbb", linewidth=1.05),
    )


def _option_d_small_multiples_save(
    df: pd.DataFrame,
    out_name: str,
    *,
    x_style: str,
    xtick_fs: int = 13,
    sup_xlabel: Optional[str] = None,
    ncols: int = 3,
) -> None:
    districts = sorted(df["District"].dropna().unique())
    if not districts:
        return

    n = len(districts)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=((24 if ncols >= 3 else 19.5), (6.45 if ncols >= 3 else 7.25) * nrows),
        squeeze=False,
        sharey=False,
        gridspec_kw={"wspace": 0.22 if ncols >= 3 else 0.24, "hspace": 0.24 if ncols >= 3 else 0.34},
    )

    medianprops = dict(color="black", linewidth=1.6)
    meanprops = dict(marker="o", markerfacecolor="white", markeredgecolor="black", markersize=7, markeredgewidth=1.2)
    whiskerprops = dict(color="black", linewidth=1.1)
    capprops = dict(color="black", linewidth=1.1)
    ylim_shared = _compute_global_yield_ylim_kgha(df)

    for i, dist in enumerate(districts):
        ax = axes[i // ncols][i % ncols]
        sub = df[df["District"] == dist]
        _district_boxplot_axes(
            ax,
            sub,
            medianprops=medianprops,
            meanprops=meanprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            xtick_fs=xtick_fs,
            x_style=x_style,
            ylim_shared=ylim_shared,
        )
        ax.set_title(dist.title(), fontweight="bold", fontsize=15)
        if i % ncols == 0:
            ax.set_ylabel("Yield (kg/ha)", fontsize=14, fontweight="bold")

    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")

    fig.suptitle("Drought severity vs yield by district (PDSI May–Sep mean)", fontsize=17, fontweight="bold", y=0.995)
    sx = sup_xlabel or "Drought class along columns (dry → wet). PDSI thresholds for each class are in the key panel."
    fig.text(0.5, 0.012, sx, ha="center", fontsize=12, fontweight="bold")

    handles = _option_d_legend_handles()
    empty_slots = (nrows * ncols) - n
    if empty_slots > 0:
        key_ax = axes[(n) // ncols][(n) % ncols]
        _fill_key_panel(key_ax, handles)
    else:
        fig.legend(handles=handles, loc="upper center", ncol=2, frameon=True, fontsize=11, bbox_to_anchor=(0.5, 0.98))

    plt.tight_layout(rect=[0, 0.075 if ncols < 3 else 0.055, 1, 0.965])
    plt.savefig(OUT_DIR / out_name, dpi=300)
    plt.close()


def option_d_by_district_small_multiples(df: pd.DataFrame) -> None:
    """Canonical manuscript variant only (v3 larger labels, 2 columns)."""
    _option_d_small_multiples_save(
        df,
        "OptionD_ByDistrict_SmallMultiples_v3_largerAxisLabels_2col_3rows.png",
        x_style="name_n_under",
        xtick_fs=16,
        ncols=2,
        sup_xlabel="Drought class (columns, dry → wet). Second line under each label is sample size (n = county-years).",
    )


def main() -> None:
    df = prep()
    option_d_by_district_small_multiples(df)
    print(f"Saved Figure 6 (Option D) to: {OUT_DIR}")


if __name__ == "__main__":
    main()
# --- END: copied verbatim ---
