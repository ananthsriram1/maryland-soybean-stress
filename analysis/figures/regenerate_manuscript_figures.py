#!/usr/bin/env python3
"""Regenerate manuscript figures (Figures 1–10) and verify reproducibility.

This orchestrator preserves separation of concerns:
- Individual generator scripts write to descriptive output paths only.
- This script runs generators in isolated subprocesses, then copies the
  descriptive PNGs into outputs/manuscript_figures/FigureNN.png.

Baseline tracking:
- A JSON file records both:
  - manuscript_baseline_sha256: hashes of the originally submitted manuscript
    figures under outputs/manuscript_baselines/
  - current_regeneration_sha256: hashes of this repo's canonical regenerated
    figures (what a stranger should be able to reproduce).

Figure 2 placeholder policy (IMPORTANT):
- The canonical Figure 2 variant is pending manual identification.
- This orchestrator copies Variant_06 as a stand-in and prints loud warnings.
- Figure 2 is still reported as PLACEHOLDER, but a side-by-side comparison PNG is
  written so reviewers can see baseline vs the stand-in in one image.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]

MANUSCRIPT_BASELINE_DIR = REPO_ROOT / "outputs" / "manuscript_baselines"
MANUSCRIPT_OUT_DIR = REPO_ROOT / "outputs" / "manuscript_figures"
COMPARISON_DIR = MANUSCRIPT_OUT_DIR / "_comparison"

BASELINE_JSON = REPO_ROOT / "docs" / "manuscript_figures_baseline.json"


FIGURE_MANIFEST: list[dict[str, Any]] = [
    {
        "figure_number": 1,
        "generator_module": "analysis.figures.figure01_md_districts_map",
        "descriptive_output_path": "outputs/Maps/Maryland_Counties_By_District.png",
        "manuscript_path": "outputs/manuscript_figures/Figure01.png",
        "placeholder": False,
    },
    {
        "figure_number": 2,
        "generator_module": "analysis.figures.figure02_soil_district_heatmap_variants",
        "descriptive_output_path": "outputs/SoilCompositionBand5/variants/Variant_06_YlOrRd_white_label_boxes.png",
        "manuscript_path": "outputs/manuscript_figures/Figure02.png",
        "placeholder": True,
        "placeholder_note": "Variant_06 stand-in pending manual variant identification",
    },
    {
        "figure_number": 3,
        "generator_module": "analysis.figures.figure03_district_precip_decade_overlay",
        "descriptive_output_path": "outputs/Precipitation/District_Precip_Climatology_MeanSD_ByDecadeBlocks.png",
        "manuscript_path": "outputs/manuscript_figures/Figure03.png",
        "placeholder": False,
    },
    {
        "figure_number": 4,
        "generator_module": "analysis.figures.figure04_study_area_map",
        "descriptive_output_path": "outputs/YieldAnalysis/StudyArea/District_Soybean_Yield_FourPeriods_Faceted_kg_ha.png",
        "manuscript_path": "outputs/manuscript_figures/Figure04.png",
        "placeholder": False,
    },
    {
        "figure_number": 5,
        "generator_module": "analysis.figures.figure05_flash_drought_proxy",
        "descriptive_output_path": "outputs/FlashDrought/flash_drought_descriptive_summary.png",
        "manuscript_path": "outputs/manuscript_figures/Figure05.png",
        "placeholder": False,
        "note": "Only figure whose engine lives under analysis/stress_analysis/ (wrapped here).",
    },
    {
        "figure_number": 6,
        "generator_module": "analysis.figures.figure06_drought_class_yield_boxplots",
        "descriptive_output_path": "outputs/DroughtEffect/Options/OptionD_ByDistrict_SmallMultiples_v3_largerAxisLabels_2col_3rows.png",
        "manuscript_path": "outputs/manuscript_figures/Figure06.png",
        "placeholder": False,
    },
    {
        "figure_number": 7,
        "generator_module": "analysis.figures.figure07_irrigated_district_heatmap",
        "descriptive_output_path": "outputs/Irrigation/Irrigated_Acres_District_CensusYears_Heatmap.png",
        "manuscript_path": "outputs/manuscript_figures/Figure07.png",
        "placeholder": False,
    },
    {
        "figure_number": 8,
        "generator_module": "analysis.figures.figure08_ndwi_r4r6_boxplot",
        "descriptive_output_path": "outputs/StressDrivers/figures/NDWI_R4R6_ByDistrict_Boxplot_ByCensusPeriod.png",
        "manuscript_path": "outputs/manuscript_figures/Figure08.png",
        "placeholder": False,
    },
    {
        "figure_number": 9,
        "generator_module": "analysis.figures.figure09_ndvi_ndwi_scissors_dualaxis",
        "descriptive_output_path": "outputs/StressDrivers/figures/NDVI_NDWI_Scissors_DualAxis_2012_2024.png",
        "manuscript_path": "outputs/manuscript_figures/Figure09.png",
        "placeholder": False,
    },
    {
        "figure_number": 10,
        "generator_module": "analysis.figures.figure10_salo_counties_yield",
        "descriptive_output_path": "outputs/Irrigation/SaLoCounties/SaLo_Counties_Acres_and_Yield_Bars.png",
        "manuscript_path": "outputs/manuscript_figures/Figure10.png",
        "placeholder": False,
    },
]


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_baseline_json() -> dict[str, Any]:
    if not BASELINE_JSON.exists():
        return {"schema_version": 1, "created_utc": _utc_now_iso(), "figures": {}}
    return json.loads(BASELINE_JSON.read_text())


def write_baseline_json(baseline: dict[str, Any]) -> None:
    ensure_parent(BASELINE_JSON)
    BASELINE_JSON.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")


def figure_key(n: int) -> str:
    return f"{n:02d}"


def run_generator(module: str) -> tuple[int, str]:
    """Run generator as an isolated subprocess, return (exit_code, combined_output)."""
    cmd = [sys.executable, "-m", module]
    p = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return p.returncode, p.stdout


def copy_output(src: Path, dst: Path) -> None:
    ensure_parent(dst)
    shutil.copyfile(src, dst)


def try_make_comparison(
    left_png: Path,
    right_png: Path,
    out_png: Path,
    *,
    banner_left: str = "",
    banner_right: str = "",
) -> bool:
    """Return True if a combined image was written; False if pillow unavailable."""
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        return False

    ensure_parent(out_png)
    with Image.open(left_png) as left, Image.open(right_png) as right:
        left = left.convert("RGBA")
        right = right.convert("RGBA")

        h = max(left.height, right.height)
        # pad to common height
        if left.height != h:
            pad = Image.new("RGBA", (left.width, h), (255, 255, 255, 255))
            pad.paste(left, (0, 0))
            left = pad
        if right.height != h:
            pad = Image.new("RGBA", (right.width, h), (255, 255, 255, 255))
            pad.paste(right, (0, 0))
            right = pad

        combined = Image.new("RGBA", (left.width + right.width, h), (255, 255, 255, 255))
        combined.paste(left, (0, 0))
        combined.paste(right, (left.width, 0))

        if banner_left or banner_right:
            draw = ImageDraw.Draw(combined)
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 18)
            except Exception:
                font = ImageFont.load_default()

            def text_height_px(s: str) -> int:
                if hasattr(draw, "textbbox"):
                    _l, _t, _r, b = draw.textbbox((0, 0), s, font=font)
                    return int(b - _t)
                if hasattr(font, "getbbox"):
                    _l, _t, _r, b = font.getbbox(s)
                    return int(b - _t)
                # Very old Pillow fallback
                return int(font.getsize(s)[1])

            pad_y = 6
            if banner_left:
                th = text_height_px(banner_left)
                draw.rectangle([0, 0, left.width, th + 2 * pad_y], fill=(245, 245, 245, 255))
                draw.text((8, pad_y), banner_left, fill=(0, 0, 0, 255), font=font)
            if banner_right:
                th = text_height_px(banner_right)
                draw.rectangle([left.width, 0, left.width + right.width, th + 2 * pad_y], fill=(245, 245, 245, 255))
                draw.text((left.width + 8, pad_y), banner_right, fill=(0, 0, 0, 255), font=font)

        combined.save(out_png)
        return True


@dataclass
class ResultRow:
    figure_number: int
    generator_module: str
    status: str
    manuscript_sha: Optional[str]
    current_sha: Optional[str]
    observed_sha: Optional[str]
    note: str = ""


def select_figures(selected: Optional[set[int]]) -> list[dict[str, Any]]:
    if not selected:
        return FIGURE_MANIFEST
    out = [f for f in FIGURE_MANIFEST if int(f["figure_number"]) in selected]
    return out


def parse_figures_arg(vals: Optional[list[str]]) -> set[int]:
    if not vals:
        return set()
    out: set[int] = set()
    for v in vals:
        for part in str(v).split(","):
            part = part.strip()
            if not part:
                continue
            out.add(int(part))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--figure",
        dest="figures",
        action="append",
        help="Regenerate only a single figure number (repeatable). Also accepts comma lists (e.g. --figure 3,7,9).",
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Run generators but do not copy descriptive outputs into outputs/manuscript_figures/.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Do not run generators; verify current outputs/manuscript_figures/ match current_regeneration_sha256 in baseline JSON.",
    )
    parser.add_argument(
        "--update-current-baseline",
        action="store_true",
        help="Update current_regeneration_sha256 fields in the baseline JSON to match observed outputs.",
    )
    args = parser.parse_args()

    selected = parse_figures_arg(args.figures)
    figs = select_figures(selected if selected else None)

    # Load / initialize baseline JSON
    baseline = load_baseline_json()
    baseline.setdefault("schema_version", 1)
    baseline.setdefault("figures", {})

    # Ensure manuscript baseline hashes exist in baseline JSON
    for f in FIGURE_MANIFEST:
        n = int(f["figure_number"])
        k = figure_key(n)
        entry = baseline["figures"].setdefault(k, {})
        entry.setdefault("figure_number", n)
        entry.setdefault("generator_module", f["generator_module"])
        entry.setdefault("manuscript_baseline_path", str(MANUSCRIPT_BASELINE_DIR / f"Figure{k}.png"))

        base_path = MANUSCRIPT_BASELINE_DIR / f"Figure{k}.png"
        if base_path.exists() and "manuscript_baseline_sha256" not in entry:
            entry["manuscript_baseline_sha256"] = sha256_file(base_path)
            entry["manuscript_baseline_size_bytes"] = base_path.stat().st_size
            entry["manuscript_baseline_captured_utc"] = _utc_now_iso()

    ensure_parent(MANUSCRIPT_OUT_DIR / "x")
    MANUSCRIPT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[ResultRow] = []
    any_failed = False

    # Loud placeholder warning (printed once up front)
    placeholder_fig2 = next((x for x in FIGURE_MANIFEST if int(x["figure_number"]) == 2), None)
    if placeholder_fig2:
        msg = (
            "WARNING: Figure 2 is a PLACEHOLDER. This orchestrator copies Variant_06 as a stand-in "
            "until the canonical Variant_*.png is manually identified.\n"
        )
        print(msg, file=sys.stderr)

    for f in figs:
        n = int(f["figure_number"])
        k = figure_key(n)
        mod = str(f["generator_module"])
        is_placeholder = bool(f.get("placeholder", False))

        base_png = MANUSCRIPT_BASELINE_DIR / f"Figure{k}.png"
        manuscript_sha = sha256_file(base_png) if base_png.exists() else None

        dst_png = REPO_ROOT / str(f["manuscript_path"])
        src_png = REPO_ROOT / str(f["descriptive_output_path"])

        entry = baseline["figures"].setdefault(k, {})
        entry.setdefault("figure_number", n)
        entry.setdefault("generator_module", mod)
        entry.setdefault("descriptive_output_path", str(src_png))
        entry.setdefault("manuscript_path", str(dst_png))
        entry.setdefault("placeholder", is_placeholder)

        if args.verify_only:
            # Verify-only mode checks current outputs/manuscript_figures/ against current_regeneration_sha256
            if is_placeholder:
                rows.append(
                    ResultRow(
                        figure_number=n,
                        generator_module=mod,
                        status="PLACEHOLDER",
                        manuscript_sha=manuscript_sha,
                        current_sha=entry.get("current_regeneration_sha256"),
                        observed_sha=None,
                        note=str(f.get("placeholder_note", "")).strip(),
                    )
                )
                continue

            expected = entry.get("current_regeneration_sha256")
            if not dst_png.exists():
                any_failed = True
                rows.append(
                    ResultRow(
                        figure_number=n,
                        generator_module=mod,
                        status="FAIL",
                        manuscript_sha=manuscript_sha,
                        current_sha=expected,
                        observed_sha=None,
                        note=f"Missing {dst_png}",
                    )
                )
                continue

            observed = sha256_file(dst_png)
            if expected and observed == expected:
                rows.append(ResultRow(n, mod, "MATCH", manuscript_sha, expected, observed))
            else:
                any_failed = True
                rows.append(
                    ResultRow(
                        figure_number=n,
                        generator_module=mod,
                        status="FAIL",
                        manuscript_sha=manuscript_sha,
                        current_sha=expected,
                        observed_sha=observed,
                        note="Does not match current_regeneration_sha256 baseline",
                    )
                )
            continue

        # Run generator
        rc, out = run_generator(mod)
        if rc != 0:
            any_failed = True
            rows.append(
                ResultRow(
                    figure_number=n,
                    generator_module=mod,
                    status="FAIL",
                    manuscript_sha=manuscript_sha,
                    current_sha=entry.get("current_regeneration_sha256"),
                    observed_sha=None,
                    note=f"Generator exited {rc}. Output:\n{out.strip()}",
                )
            )
            # continue to next figure
            continue

        # Ensure descriptive output exists
        if not src_png.exists():
            any_failed = True
            rows.append(
                ResultRow(
                    figure_number=n,
                    generator_module=mod,
                    status="FAIL",
                    manuscript_sha=manuscript_sha,
                    current_sha=entry.get("current_regeneration_sha256"),
                    observed_sha=None,
                    note=f"Generator succeeded but missing descriptive output: {src_png}",
                )
            )
            continue

        # Copy to manuscript path unless --no-copy
        if not args.no_copy:
            if is_placeholder:
                # Loud runtime warning to stderr
                print(
                    f"WARNING: Figure 2 placeholder copy in effect: {src_png.name} -> {dst_png.name} ({f.get('placeholder_note','')})",
                    file=sys.stderr,
                )
            copy_output(src_png, dst_png)

        # Observe sha of copied output (or of descriptive if no-copy)
        observed_path = dst_png if (not args.no_copy) else src_png
        observed_sha = sha256_file(observed_path)

        # Determine status
        current_sha = entry.get("current_regeneration_sha256")

        if is_placeholder:
            rows.append(
                ResultRow(
                    figure_number=n,
                    generator_module=mod,
                    status="PLACEHOLDER",
                    manuscript_sha=manuscript_sha,
                    current_sha=current_sha,
                    observed_sha=observed_sha,
                    note=str(f.get("placeholder_note", "")).strip(),
                )
            )
        else:
            if args.update_current_baseline:
                # Intentionally refresh reproducibility baseline; do not treat drift as CI failure.
                if manuscript_sha and observed_sha == manuscript_sha:
                    status = "UPDATED_BASELINE"
                    note = "Refreshed current_regeneration_sha256 (matches manuscript baseline)"
                else:
                    status = "UPDATED_BASELINE"
                    note = "Refreshed current_regeneration_sha256 (differs from manuscript baseline)"
            elif current_sha and observed_sha == current_sha:
                status = "MATCH"
                note = ""
            else:
                # compare to manuscript baseline
                if manuscript_sha and observed_sha != manuscript_sha:
                    status = "DRIFT vs MANUSCRIPT" if (current_sha is None) else "FAIL"
                    note = "Differs from manuscript baseline"
                    if current_sha is not None:
                        note = "Does not match current_regeneration_sha256 baseline"
                        any_failed = True
                else:
                    status = "MATCH" if manuscript_sha and observed_sha == manuscript_sha else "DRIFT vs MANUSCRIPT"
                    note = ""

            rows.append(
                ResultRow(
                    figure_number=n,
                    generator_module=mod,
                    status=status,
                    manuscript_sha=manuscript_sha,
                    current_sha=current_sha,
                    observed_sha=observed_sha,
                    note=note,
                )
            )

        # Baseline JSON update logic
        if not args.no_copy and not args.verify_only:
            if entry.get("current_regeneration_sha256") is None or args.update_current_baseline:
                entry["current_regeneration_sha256"] = observed_sha
                entry["current_regeneration_size_bytes"] = observed_path.stat().st_size
                entry["current_regeneration_captured_utc"] = _utc_now_iso()

        # Visual comparison artifact (include placeholder Figure 2 with explicit banners)
        if not args.no_copy:
            cmp_path = COMPARISON_DIR / f"Figure{k}_compare.png"
            if is_placeholder:
                note_txt = str(f.get("placeholder_note", "")).strip()
                combined_ok = try_make_comparison(
                    base_png,
                    dst_png,
                    cmp_path,
                    banner_left="Manuscript baseline (Figure 2)",
                    banner_right="PLACEHOLDER regeneration — " + (note_txt or "see orchestrator warning"),
                )
            else:
                combined_ok = try_make_comparison(base_png, dst_png, cmp_path)
            if combined_ok:
                print(f"Figure {k}: visual comparison saved to {cmp_path}")
            else:
                # fallback: drop both files for review
                baseline_copy = COMPARISON_DIR / f"Figure{k}_baseline.png"
                regen_copy = COMPARISON_DIR / f"Figure{k}_regenerated.png"
                shutil.copyfile(base_png, baseline_copy)
                shutil.copyfile(dst_png, regen_copy)
                print(f"Figure {k}: comparison saved as {baseline_copy} and {regen_copy} (Pillow unavailable)")

    # Persist baseline JSON (unless verify-only)
    if not args.verify_only:
        baseline["last_run_utc"] = _utc_now_iso()
        write_baseline_json(baseline)

    # Print summary table
    print("\n=== Summary ===")
    header = ["Figure", "Generator", "Status", "Observed_SHA256", "Note"]
    print(" | ".join(header))
    print(" | ".join(["---"] * len(header)))
    for r in rows:
        fig = f"{r.figure_number:02d}"
        obs = (r.observed_sha or "")[:12]
        note = r.note.replace("\n", " ")[:120]
        print(f"{fig} | {r.generator_module} | {r.status} | {obs} | {note}")

    return 1 if any_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

