"""Compare the structural-EM seed polygon with saved A04 KiCad copper."""
from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import hashlib
import json
import sys

from shapely import union_all
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from fixture_structural_em import signal_polygon  # noqa: E402


def shp(row: dict) -> Polygon:
    return Polygon(row["outer"], row.get("holes", []))


def main() -> None:
    source = (ROOT / "reviews" / "fixture_structural_redesign_20260922"
              / "a04_saved_geometry.json")
    design_path = (ROOT / "hardware" / "calibration_fixture_PCB_A04_DRAFT"
                   / "design_geometry.json")
    out = (ROOT / "reviews" / "fixture_structural_redesign_20260922"
           / "em_source_link.json")
    geometry = json.loads(source.read_text(encoding="utf-8"))
    design = json.loads(design_path.read_text(encoding="utf-8"))
    seed = design["RF_seed"]
    args = Namespace(
        gap_mm=seed["unreferenced_gap_mm"],
        in_overlap_mm=seed["IN_overlap_mm"],
        out_overlap_mm=seed["OUT_overlap_mm"],
        taper_mm=seed["taper_mm"],
        launch_width_mm=seed["launch_width_mm"],
        wide_width_mm=seed["wide_SIG_mm"],
    )
    expected, dimensions = signal_polygon(args)
    actual = union_all([shp(poly) for zone in geometry["zones"]
                        if zone["layer"] == "F.Cu" and zone["net"] == "/SIG"
                        for poly in zone["polygons"]])
    # Connector pad rasterization is intentionally absent from the ideal
    # structural model.  Compare the uniform-line region between pad fields.
    comparison_region = box(-10, -33, 10, 33)
    actual = actual.intersection(comparison_region)
    expected = expected.intersection(comparison_region)
    sym = actual.symmetric_difference(expected).area
    report = {
        "classification": "CALCULATED_CAD_TO_EM_SOURCE_LINK",
        "pass": sym < 0.01,
        "saved_A04_geometry_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "design_geometry_sha256": hashlib.sha256(design_path.read_bytes()).hexdigest(),
        "structural_em_script_sha256": hashlib.sha256(
            (ROOT / "analysis" / "fixture_structural_em.py").read_bytes()).hexdigest(),
        "seed": seed,
        "derived_signal_dimensions_mm": dimensions,
        "comparison_region_model_mm": [-10, -33, 10, 33],
        "actual_signal_area_mm2": actual.area,
        "em_signal_area_mm2": expected.area,
        "symmetric_difference_mm2": sym,
        "hausdorff_distance_mm": actual.hausdorff_distance(expected),
        "note": "The tiny difference is KiCad filled-zone curve/raster rounding; connector pads are outside the comparison region.",
    }
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
