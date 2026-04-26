#!/usr/bin/env python3
"""Generate manuscript Figure 5 (flash-drought proxy events per year).

This is a thin wrapper to keep the Figure 5 generator discoverable under
`analysis/figures/` while preserving the actual statistical engine in:
  analysis/stress_analysis/detect_flash_droughts.py

Outputs (descriptive):
  outputs/FlashDrought/flash_drought_descriptive_summary.png
  (and the companion CSVs under outputs/FlashDrought/)
"""

from __future__ import annotations

from analysis.stress_analysis.detect_flash_droughts import main


if __name__ == "__main__":
    main()

