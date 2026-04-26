#!/usr/bin/env python3
"""
Two-sample and omnibus tests for R4–R6 NDWI: Southern vs Upper/Lower Eastern Shore (and pooled Eastern).

- Welch t-test (unequal variances) on NDWI values (same filter as Fig. 8 boxplots).
- Chi-square test on counts inside vs outside the stress band [0.121, 0.144].
- One-way ANOVA (scipy f_oneway) across all five districts in Fig. 8 (omnibus test for
  differences in mean NDWI among districts). Kruskal–Wallis non-parametric omnibus test
  reported alongside (does not assume normality / equal variances).

Caveat: 10-day observations are clustered by county and year; p-values from treating
each row as i.i.d. can be anti-conservative. For publication, consider a mixed model with
random intercepts for county (and optionally year) as a robustness check. Classical ANOVA
assumes equal variances; Welch t-tests above are the primary pairwise comparisons when
variances differ.

Input: data/maryland_soybean_10day_timeseries_long.csv
Output: NDWI_R4R6_TwoSample_Tests.csv, NDWI_R4R6_Omnibus_Tests.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

DATA_PATH = Path("data/maryland_soybean_10day_timeseries_long.csv")
DOY_LO, DOY_HI = 200, 260
NDWI_STRESS_LO, NDWI_STRESS_HI = 0.121, 0.144
OUT_CSV = Path("outputs/StressDrivers/tables/NDWI_R4R6_TwoSample_Tests.csv")
OUT_OMNIBUS = Path("outputs/StressDrivers/tables/NDWI_R4R6_Omnibus_Tests.csv")

# Same five districts as Fig. 8 (PlotNDWI_R4R6_ByDistrict_Boxplot.DISTRICT_ORDER)
DISTRICTS_FIG8 = [
    "UPPER EASTERN SHORE",
    "LOWER EASTERN SHORE",
    "NORTH CENTRAL",
    "WESTERN",
    "SOUTHERN",
]


def load_r4r6() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df["DOY"] = df["date"].dt.dayofyear
    df["Year"] = df["date"].dt.year
    df["NDWI"] = pd.to_numeric(df["NDWI"], errors="coerce")
    df = df[(df["DOY"] >= DOY_LO) & (df["DOY"] <= DOY_HI)].copy()
    df["Ag_District"] = df["Ag_District"].astype(str).str.upper().str.strip()
    df = df.dropna(subset=["NDWI"])
    western = df["Ag_District"] == "WESTERN"
    df = df.loc[~western | ((df["County"].str.upper() == "GARRETT") & (df["Year"] >= 2021))].copy()
    return df


def main() -> None:
    df = load_r4r6()
    rows = []

    def vec(d: str) -> np.ndarray:
        return df[df["Ag_District"] == d]["NDWI"].values

    southern = vec("SOUTHERN")
    upper = vec("UPPER EASTERN SHORE")
    lower = vec("LOWER EASTERN SHORE")
    eastern = np.concatenate([upper, lower])

    comparisons = [
        ("UPPER EASTERN SHORE", upper),
        ("LOWER EASTERN SHORE", lower),
        ("EASTERN_SHORE_POOLED", eastern),
    ]

    for name, other in comparisons:
        t2, p2 = stats.ttest_ind(southern, other, equal_var=False)
        t1, p1 = stats.ttest_ind(southern, other, equal_var=False, alternative="less")
        rows.append(
            {
                "comparison": f"SOUTHERN_vs_{name}",
                "n_southern": len(southern),
                "n_other": len(other),
                "mean_southern": southern.mean(),
                "mean_other": other.mean(),
                "welch_t_two_sided": t2,
                "p_two_sided": p2,
                "welch_t_one_sided_less": t1,
                "p_one_sided_southern_lower": p1,
            }
        )

    def stress_contingency(a: np.ndarray, b: np.ndarray, label: str) -> None:
        s_a = int(np.sum((a >= NDWI_STRESS_LO) & (a <= NDWI_STRESS_HI)))
        s_b = int(np.sum((b >= NDWI_STRESS_LO) & (b <= NDWI_STRESS_HI)))
        n_a, n_b = len(a), len(b)
        tab = np.array([[s_a, n_a - s_a], [s_b, n_b - s_b]])
        chi2, p, dof, _ = stats.chi2_contingency(tab)
        rows.append(
            {
                "comparison": f"CHISQ_STRESS_{label}",
                "n_southern": n_a,
                "n_other": n_b,
                "mean_southern": s_a / n_a,
                "mean_other": s_b / n_b,
                "welch_t_two_sided": chi2,
                "p_two_sided": p,
                "welch_t_one_sided_less": np.nan,
                "p_one_sided_southern_lower": np.nan,
            }
        )

    stress_contingency(southern, upper, "SOUTHERN_vs_UPPER")
    stress_contingency(southern, lower, "SOUTHERN_vs_LOWER")
    stress_contingency(southern, eastern, "SOUTHERN_vs_EASTERN_POOLED")

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    print(out.to_string())
    print(f"\nSaved: {OUT_CSV}")

    # Omnibus tests across all five districts (same R4–R6 filter as Fig. 8)
    groups = [vec(d) for d in DISTRICTS_FIG8]
    k = len(DISTRICTS_FIG8)
    n_per = [len(g) for g in groups]
    n_total = sum(n_per)
    f_stat, p_anova = stats.f_oneway(*groups)
    df_between = k - 1
    df_within = n_total - k
    h_stat, p_kw = stats.kruskal(*groups)

    omnibus = pd.DataFrame(
        [
            {
                "test": "one_way_ANOVA_f_oneway",
                "statistic": f_stat,
                "p_value": p_anova,
                "df_between": df_between,
                "df_within": df_within,
                "n_total": n_total,
                "n_by_district": ";".join(f"{d}:{n}" for d, n in zip(DISTRICTS_FIG8, n_per)),
            },
            {
                "test": "kruskal_wallis_omnibus",
                "statistic": h_stat,
                "p_value": p_kw,
                "df_between": np.nan,
                "df_within": np.nan,
                "n_total": n_total,
                "n_by_district": ";".join(f"{d}:{n}" for d, n in zip(DISTRICTS_FIG8, n_per)),
            },
        ]
    )
    omnibus.to_csv(OUT_OMNIBUS, index=False)
    print("\n--- Omnibus tests (all five districts, Fig. 8 filter) ---")
    print(omnibus.to_string(index=False))
    print(f"\nSaved: {OUT_OMNIBUS}")


if __name__ == "__main__":
    main()
