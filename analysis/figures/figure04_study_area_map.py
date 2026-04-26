#!/usr/bin/env python3
"""
Manuscript Figure 4: district soybean yield by four time periods (faceted panels, kg/ha).

Writes:
  outputs/YieldAnalysis/StudyArea/District_Soybean_Yield_FourPeriods_Faceted_kg_ha.png

Logic is delegated to archive/figure_drafts/StudyArea_Option2_Variations.py (variation 3),
which matches the manuscript layout (five district panels, US/MD reference lines).
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path


def _load_variation3():
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "archive" / "figure_drafts" / "StudyArea_Option2_Variations.py"
    spec = importlib.util.spec_from_file_location("study_area_option2_variations", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.variation3_separated_panels


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    legacy_path = repo_root / "outputs" / "YieldAnalysis" / "StudyArea" / "Options" / "Variations" / "V3_SeparatedPanels.png"
    out_path = repo_root / "outputs" / "YieldAnalysis" / "StudyArea" / "District_Soybean_Yield_FourPeriods_Faceted_kg_ha.png"

    variation3_separated_panels = _load_variation3()
    variation3_separated_panels()

    if not legacy_path.is_file():
        raise FileNotFoundError(f"Expected legacy output missing after generator: {legacy_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(legacy_path, out_path)
    print(f"Copied manuscript-style Figure 4 to: {out_path}")


if __name__ == "__main__":
    main()
