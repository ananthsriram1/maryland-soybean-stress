#!/usr/bin/env python3
"""
Create multiple more-descriptive variants of the drought vs yield figure.

Outputs (all saved under outputs/DroughtEffect/Options):
  - OptionA_ViolinWithPoints.png
  - OptionB_MeanCI_WithN.png
  - OptionC_YieldAnomaly_Boxplot.png
  - OptionD_ByDistrict_SmallMultiples.png (+ v2_nAboveBoxes, v3_largerAxisLabels): 5 districts, key shows PDSI bins
  - OptionD_ByDistrict_Individuals/OptionD_<DISTRICT>.png (one panel per district for thesis/embed)
  - OptionE_ScatterWithBinnedMeans.png
"""

from __future__ import annotations

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
    """Visual key: thick median line + diamond mean (matches boxplot styling)."""
    return [
        plt.Line2D([0], [0], color="black", linewidth=2.8, solid_capstyle="round", label="Median"),
        plt.Line2D(
            [0],
            [0],
            marker="D",
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


def option_a_violin_with_points(df: pd.DataFrame) -> None:
    data = [(df[df["drought_class"] == c]["yield"] * BUAC_TO_KGHA).values for c in ORDER]
    ns = [len(v) for v in data]

    fig, ax = plt.subplots(figsize=(12.5, 6.5))
    parts = ax.violinplot(data, showmeans=True, showmedians=False, showextrema=False)
    for i, body in enumerate(parts["bodies"]):
        body.set_facecolor(COLORS[i])
        body.set_edgecolor("black")
        body.set_alpha(0.45)

    # jittered points (subsample for readability if huge)
    rng = np.random.default_rng(7)
    for i, c in enumerate(ORDER, start=1):
        sub = df[df["drought_class"] == c]
        if len(sub) > 800:
            sub = sub.sample(800, random_state=7)
        x = rng.normal(i, 0.06, size=len(sub))
        ax.scatter(x, sub["yield"], s=10, c="black", alpha=0.18, linewidth=0)

    ax.set_xticks(range(1, len(ORDER) + 1))
    ax.set_xticklabels([f"{lab}\n(n={n})" for lab, n in zip(LABELS, ns)], fontweight="bold")
    ax.set_ylabel("Yield (kg/ha)")
    ax.set_title("Yield declines with increasing drought severity (distribution + points)\nPDSI May–Sep mean", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "OptionA_ViolinWithPoints.png", dpi=300, bbox_inches="tight")
    plt.close()


def option_b_mean_ci_with_n(df: pd.DataFrame) -> None:
    rows = []
    for c in ORDER:
        y = (df[df["drought_class"] == c]["yield"] * BUAC_TO_KGHA).dropna()
        n = int(y.shape[0])
        m = float(y.mean()) if n else np.nan
        sd = float(y.std(ddof=1)) if n > 1 else np.nan
        se = sd / np.sqrt(n) if n > 1 else np.nan
        ci = 1.96 * se if n > 1 else np.nan
        rows.append({"class": c, "n": n, "mean": m, "ci95": ci})
    s = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    x = np.arange(len(ORDER))
    ax.bar(x, s["mean"], color=COLORS, alpha=0.55, edgecolor="black", linewidth=1.0)
    ax.errorbar(x, s["mean"], yerr=s["ci95"], fmt="none", ecolor="black", elinewidth=2, capsize=5, capthick=2)

    for xi, (m, n) in enumerate(zip(s["mean"], s["n"])):
        if np.isfinite(m):
            ax.text(xi, m + 0.8, f"{m:.1f}", ha="center", va="bottom", fontweight="bold", fontsize=10)
        ax.text(xi, 1.5, f"n={n}", ha="center", va="bottom", fontsize=9, alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, fontweight="bold")
    ax.set_ylabel("Mean yield (kg/ha) ± 95% CI")
    ax.set_title("Mean yield decreases as drought severity increases\n(PDSI May–Sep mean; 95% CI shown)", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "OptionB_MeanCI_WithN.png", dpi=300, bbox_inches="tight")
    plt.close()


def option_c_yield_anomaly_boxplot(df: pd.DataFrame) -> None:
    # County-demeaned anomaly to control for baseline differences between counties
    sub = df.copy()
    sub["county_mean"] = sub.groupby("county_norm")["yield"].transform("mean")
    sub["yield_anom"] = sub["yield"] - sub["county_mean"]

    data = [sub[sub["drought_class"] == c]["yield_anom"].values for c in ORDER]
    ns = [len(v) for v in data]

    fig, ax = plt.subplots(figsize=(12, 6.5))
    bp = ax.boxplot(data, labels=[f"{lab}\n(n={n})" for lab, n in zip(LABELS, ns)], showmeans=True, patch_artist=True)
    for box, col in zip(bp["boxes"], COLORS):
        box.set_facecolor(col)
        box.set_alpha(0.55)
        box.set_edgecolor("black")
        box.set_linewidth(1.0)
    for key in ["whiskers", "caps", "medians", "means"]:
        for item in bp[key]:
            item.set_color("black")
            item.set_linewidth(1.1)

    ax.axhline(0, color="black", linewidth=1.5, alpha=0.7)
    ax.set_ylabel("Yield anomaly (county-demeaned, bu/acre)")
    ax.set_title("Drought effect after controlling for county baseline yield\n(yield anomaly relative to county mean)", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "OptionC_YieldAnomaly_Boxplot.png", dpi=300, bbox_inches="tight")
    plt.close()


def _compute_global_yield_ylim_kgha(df: pd.DataFrame) -> Tuple[float, float]:
    """Common y-axis for district small multiples (kg/ha); avoids degenerate boxplot ylim with sharey."""
    y_kg = (df["yield"].astype(float) * BUAC_TO_KGHA).to_numpy()
    y_kg = y_kg[np.isfinite(y_kg)]
    if len(y_kg) == 0:
        return (0.0, 6000.0)
    hi = float(np.nanpercentile(y_kg, 99.9))
    hi = max(hi * 1.12, 4000.0)
    lo = _yield_ylim_kgha_lower_step500(float(np.nanmin(y_kg)))
    return (lo, min(hi, 10500.0))


def _district_boxplot_axes(
    ax: plt.Axes,
    sub: pd.DataFrame,
    *,
    medianprops: dict,
    meanprops: dict,
    whiskerprops: dict,
    capprops: dict,
    xtick_fs: int,
    x_style: str = "name_n_under",
    ylim_shared: Optional[Tuple[float, float]] = None,
) -> None:
    """
    x_style:
      - name_n_under: two lines — class name, then "n = k" (no parentheses)
      - name_only_n_above: one line class names; "n = k" printed above each column
    """
    raw = [(sub[sub["drought_class"] == c]["yield"] * BUAC_TO_KGHA).values for c in ORDER]
    ns = [int(len(v)) for v in raw]
    # Boxplot behaves poorly on empty groups; use NaN placeholder so y-limits stay finite
    data = [np.asarray(v, dtype=float) if len(v) else np.array([np.nan]) for v in raw]

    if x_style == "name_n_under":
        labels = [f"{name}\nn = {n}" for name, n in zip(SHORT_CLASS, ns)]
    elif x_style == "name_only_n_above":
        labels = list(SHORT_CLASS)
    else:
        raise ValueError(x_style)

    bp = ax.boxplot(
        data,
        labels=labels,
        showmeans=True,
        patch_artist=True,
        medianprops=medianprops,
        meanprops=meanprops,
        whiskerprops=whiskerprops,
        capprops=capprops,
    )
    for box, col in zip(bp["boxes"], COLORS):
        box.set_facecolor(col)
        box.set_alpha(0.45)
        box.set_edgecolor("black")
        box.set_linewidth(0.9)
    ax.grid(axis="y", alpha=0.2)
    ax.tick_params(axis="x", labelsize=xtick_fs)
    ax.tick_params(axis="y", labelsize=max(12, xtick_fs))
    for lab in ax.get_xticklabels():
        lab.set_fontweight("bold")
    # Tilt labels so middle categories (e.g. Mild dry vs Near norm.) do not overlap
    plt.setp(
        ax.get_xticklabels(),
        rotation=22,
        ha="right",
        rotation_mode="anchor",
    )
    ax.tick_params(axis="x", pad=6)

    # Robust y-limits: boxplots with NaN-only groups can return degenerate ylim (e.g. 0–1), which
    # breaks sharey across panels. Prefer explicit limits from real yield values (kg/ha).
    real_y = np.concatenate([np.asarray(v, dtype=float) for v in raw if len(v) > 0])
    real_y = real_y[np.isfinite(real_y)]
    if ylim_shared is not None:
        ax.set_ylim(ylim_shared[0], ylim_shared[1])
    elif len(real_y) == 0:
        ax.set_ylim(0, 6000)
    else:
        lo, hi = float(np.nanmin(real_y)), float(np.nanmax(real_y))
        pad = max((hi - lo) * 0.12, 120.0)
        ax.set_ylim(_yield_ylim_kgha_lower_step500(lo), hi + pad)

    if x_style == "name_only_n_above":
        # Place n above each tick in blended coords so we do not resize ylim (keeps sharey stable)
        for j, ni in enumerate(ns):
            ax.text(
                j + 1,
                1.06,
                f"n = {ni}",
                transform=ax.get_xaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=max(9, xtick_fs - 1),
                color="#333333",
                clip_on=False,
            )

    xs = pd.to_numeric(sub["pdsi"], errors="coerce")
    ys = pd.to_numeric(sub["yield"], errors="coerce")
    m = xs.notna() & ys.notna()
    r = float(np.corrcoef(xs[m], ys[m])[0, 1]) if m.sum() >= 3 else np.nan
    r_text = f"r = {r:.2f}" if np.isfinite(r) else "r = NA"
    ax.text(
        0.97,
        0.07,
        r_text,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=max(13, int(xtick_fs)),
        fontweight="bold",
        color="#B03A2E",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#dddddd", alpha=0.9),
    )


def _fill_key_panel(key_ax: plt.Axes, handles: list) -> None:
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
    # If we have an empty slot, we use it for the key panel; prefer layouts that naturally give one.
    # For 5 districts, ncols=2 yields a 3x2 grid (6 slots) which makes each panel larger/readable.
    # Do not use sharey=True: the spare "key" cell must not participate in shared axes (breaks y-scale).
    # All data panels use the same ylim_shared instead.
    # Wide/tall canvas so each subplot’s *data area* stays ~the size of the pre-rotation 18×5.5 layout,
    # while leaving room for angled x labels (rotation does not shrink the plotted region).
    # Spacing tuning:
    # - 3-col grid: keep wide but compact
    # - 2-col grid (3x2 for 5 districts + key): make each panel larger and add air between subplots
    base_w = 24 if ncols >= 3 else 19.5
    row_h = 6.45 if ncols >= 3 else 7.25
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(base_w, row_h * nrows),
        squeeze=False,
        sharey=False,
        gridspec_kw={"wspace": 0.22 if ncols >= 3 else 0.24, "hspace": 0.24 if ncols >= 3 else 0.34},
    )

    medianprops = dict(color="black", linewidth=1.6)
    meanprops = dict(marker="D", markerfacecolor="white", markeredgecolor="black", markersize=6, markeredgewidth=1.2)
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

    # Give more bottom margin for rotated x tick labels (esp. 2-col layouts)
    plt.tight_layout(rect=[0, 0.075 if ncols < 3 else 0.055, 1, 0.965])
    # bbox_inches="tight" can inflate height badly with some tick/label combinations; fixed canvas is safer
    plt.savefig(OUT_DIR / out_name, dpi=300)
    plt.close()


def option_d_by_district_small_multiples(df: pd.DataFrame) -> None:
    """Multiple PNG variants; all include five districts in one figure."""
    _option_d_small_multiples_save(
        df,
        "OptionD_ByDistrict_SmallMultiples.png",
        x_style="name_n_under",
        xtick_fs=13,
        sup_xlabel="Drought class (columns, dry → wet). Second line under each label is sample size (n = county-years).",
    )
    _option_d_small_multiples_save(
        df,
        "OptionD_ByDistrict_SmallMultiples_2col_3rows.png",
        x_style="name_n_under",
        xtick_fs=13,
        ncols=2,
        sup_xlabel="Drought class (columns, dry → wet). Second line under each label is sample size (n = county-years).",
    )
    _option_d_small_multiples_save(
        df,
        "OptionD_ByDistrict_SmallMultiples_v2_nAboveBoxes.png",
        x_style="name_only_n_above",
        xtick_fs=13,
        sup_xlabel="Drought class (columns, dry → wet). Sample sizes n are shown above each box.",
    )
    _option_d_small_multiples_save(
        df,
        "OptionD_ByDistrict_SmallMultiples_v2_nAboveBoxes_2col_3rows.png",
        x_style="name_only_n_above",
        xtick_fs=13,
        ncols=2,
        sup_xlabel="Drought class (columns, dry → wet). Sample sizes n are shown above each box.",
    )
    _option_d_small_multiples_save(
        df,
        "OptionD_ByDistrict_SmallMultiples_v3_largerAxisLabels.png",
        x_style="name_n_under",
        xtick_fs=15,
        sup_xlabel="Drought class (columns, dry → wet). Second line under each label is sample size (n = county-years).",
    )
    _option_d_small_multiples_save(
        df,
        "OptionD_ByDistrict_SmallMultiples_v3_largerAxisLabels_2col_3rows.png",
        x_style="name_n_under",
        xtick_fs=16,
        ncols=2,
        sup_xlabel="Drought class (columns, dry → wet). Second line under each label is sample size (n = county-years).",
    )


def option_d_by_district_individual_figures(df: pd.DataFrame) -> None:
    """One full-width figure per district — readable x-axis when embedded in a thesis."""
    split_dir = OUT_DIR / "OptionD_ByDistrict_Individuals"
    split_dir.mkdir(parents=True, exist_ok=True)

    districts = sorted(df["District"].dropna().unique())
    medianprops = dict(color="black", linewidth=1.6)
    meanprops = dict(marker="D", markerfacecolor="white", markeredgecolor="black", markersize=7, markeredgewidth=1.2)
    whiskerprops = dict(color="black", linewidth=1.1)
    capprops = dict(color="black", linewidth=1.1)

    for dist in districts:
        sub = df[df["District"] == dist]
        fig, ax = plt.subplots(figsize=(12, 6.2))
        _district_boxplot_axes(
            ax,
            sub,
            medianprops=medianprops,
            meanprops=meanprops,
            whiskerprops=whiskerprops,
            capprops=capprops,
            xtick_fs=14,
        )
        ax.set_title(f"Soybean yield vs drought severity — {dist.title()}\n(May–Sep mean PDSI)", fontweight="bold", fontsize=15)
        ax.set_ylabel("Yield (kg/ha)", fontsize=14, fontweight="bold")
        ax.set_xlabel(
            "Drought class (May–Sep mean PDSI); dry left → wet right",
            fontsize=13,
            fontweight="bold",
        )
        fig.legend(handles=_option_d_legend_handles(), loc="upper right", frameon=True, fontsize=13, title="Key", title_fontsize=14)
        plt.tight_layout()
        safe = dist.replace(" ", "_")
        plt.savefig(split_dir / f"OptionD_{safe}.png", dpi=300, bbox_inches="tight")
        plt.close()


def option_e_scatter_with_binned_means(df: pd.DataFrame) -> None:
    sub = df.dropna(subset=["pdsi", "yield"]).copy()
    sub["yield_si"] = sub["yield"] * BUAC_TO_KGHA
    fig, ax = plt.subplots(figsize=(12, 6.8))

    # scatter (light)
    if len(sub) > 1600:
        sub_s = sub.sample(1600, random_state=7)
    else:
        sub_s = sub
    ax.scatter(sub_s["pdsi"], sub_s["yield_si"], s=14, c="black", alpha=0.22, linewidth=0)

    # binned means across pdsi
    bins = np.linspace(sub["pdsi"].min(), sub["pdsi"].max(), 13)
    sub["bin"] = pd.cut(sub["pdsi"], bins=bins, include_lowest=True)
    g = sub.groupby("bin", observed=False).agg(pdsi_mean=("pdsi", "mean"), yield_mean=("yield_si", "mean"), n=("yield_si", "count")).reset_index(drop=True)
    g = g[g["n"] >= 15].copy()
    ax.plot(g["pdsi_mean"], g["yield_mean"], color="#D1495B", linewidth=3, marker="o", markersize=6, alpha=0.9)

    ax.set_xlabel("PDSI (May–Sep mean)  ↑ wetter / ↓ drier")
    ax.set_ylabel("Yield (kg/ha)")
    ax.set_title("Yield vs drought (continuous): points + binned mean trend", fontweight="bold")
    ax.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "OptionE_ScatterWithBinnedMeans.png", dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    df = prep()
    option_a_violin_with_points(df)
    option_b_mean_ci_with_n(df)
    option_c_yield_anomaly_boxplot(df)
    option_d_by_district_small_multiples(df)
    option_d_by_district_individual_figures(df)
    option_e_scatter_with_binned_means(df)
    print(f"Saved options to: {OUT_DIR}")
    print(f"Per-district figures: {OUT_DIR / 'OptionD_ByDistrict_Individuals'}")


if __name__ == "__main__":
    main()

