#!/usr/bin/env python3
"""
Manuscript Figure 3: district precipitation mean ± SD by 10-year blocks (annual + Jul–Sep).

Canonical output matches the manuscript baseline:
  outputs/Precipitation/District_Precip_Climatology_MeanSD_ByDecadeBlocks.png

Implementation delegates to the archived climatology builder under
`archive/figure_drafts/` (reads NOAA county precipitation and aggregates to districts).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_climatology_main():
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "archive" / "figure_drafts" / "PlotDistrictPrecipitationClimatology.py"
    spec = importlib.util.spec_from_file_location("plot_district_precip_climatology", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def main() -> None:
    main_fn = _load_climatology_main()
    main_fn()


if __name__ == "__main__":
    main()
