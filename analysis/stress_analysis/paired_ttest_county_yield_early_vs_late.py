#!/usr/bin/env python3
"""
Paired comparison: county-mean soybean yield (bu/ac) in 1997–2006 vs 2019–2025
for counties with observations in BOTH windows.

Tests whether the long-term increase is statistically distinguishable from zero
when counties are paired (same unit of observation over time).

Input: data/processed_yield/yield_clean_long_format.csv
Output: prints t-test, Wilcoxon, and summary stats (optionally save CSV of pairs).

Soybean yield SI: kg/ha = bu/ac × 67.251 (60 lb/bu, 1 ac = 0.404685642 ha)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy import stats

BUAC_TO_KGHA = 67.251
DATA = Path("data/processed_yield/yield_clean_long_format.csv")


def main() -> None:
    df = pd.read_csv(DATA)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Yield"] = pd.to_numeric(df["Yield"], errors="coerce")
    df = df.dropna(subset=["Year", "Yield", "County"])

    early_mask = (df["Year"] >= 1997) & (df["Year"] <= 2006)
    late_mask = (df["Year"] >= 2019) & (df["Year"] <= 2025)

    early = df[early_mask].groupby("County")["Yield"].mean()
    late = df[late_mask].groupby("County")["Yield"].mean()
    common = early.index.intersection(late.index)

    y1 = early.loc[common].values
    y2 = late.loc[common].values
    diff = y2 - y1

    t_stat, p_two = stats.ttest_rel(y2, y1)
    _, p_greater = stats.ttest_rel(y2, y1, alternative="greater")
    w_stat, p_wilcox = stats.wilcoxon(y2, y1, alternative="two-sided")

    out = pd.DataFrame(
        {
            "County": common,
            "mean_yield_bu_ac_1997_2006": y1,
            "mean_yield_bu_ac_2019_2025": y2,
            "diff_bu_ac": diff,
            "diff_kg_ha": diff * BUAC_TO_KGHA,
        }
    )
    out_path = Path("outputs/YieldAnalysis/Paired_CountyYield_EarlyVsLate.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)

    print("Paired county-mean yield: 1997–2006 vs 2019–2025")
    print(f"  Counties (n): {len(common)}")
    print(f"  Grand mean early: {y1.mean():.2f} bu/ac ({y1.mean() * BUAC_TO_KGHA:.1f} kg/ha)")
    print(f"  Grand mean late:  {y2.mean():.2f} bu/ac ({y2.mean() * BUAC_TO_KGHA:.1f} kg/ha)")
    print(f"  Mean paired difference (late − early): {diff.mean():.2f} ± {diff.std(ddof=1):.2f} bu/ac")
    print(f"    (= {diff.mean() * BUAC_TO_KGHA:.1f} kg/ha mean increase)")
    print(f"  Paired t-test: t = {t_stat:.3f}, p (two-sided) = {p_two:.2e}")
    print(f"  Paired t-test: p (one-sided, increase) = {p_greater:.2e}")
    print(f"  Wilcoxon signed-rank: statistic = {w_stat:.1f}, p (two-sided) = {p_wilcox:.2e}")
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    main()
