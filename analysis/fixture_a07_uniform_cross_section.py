"""Quasi-static design screen for a probe-specific uniform calibration line.

The candidate replaces the A05 planar centre transition with one constant
rounded current bar inside a rectangular return enclosure.  A thin dielectric
centering sleeve is optional.  Results are topology calculations, not a
measured fixture calibration and not a ferrite/probe-loaded model.
"""
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
from scipy.constants import c, epsilon_0
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reviews" / "fixture_structural_redesign_20260922"


def rounded_rect(x: np.ndarray, z: np.ndarray, half_x: float,
                 half_z: float, radius: float) -> np.ndarray:
    """Boolean mask for an axis-aligned rounded rectangle."""
    radius = min(radius, half_x, half_z)
    qx = np.abs(x) - (half_x - radius)
    qz = np.abs(z) - (half_z - radius)
    return ((np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2 <= radius**2)
            & (qx <= radius) & (qz <= radius))


def make_axis(anchors: list[float], h: float, lo: float, hi: float) -> np.ndarray:
    values = set(np.arange(lo, hi + h/2, h).round(8))
    values.update(round(v, 8) for v in anchors)
    return np.asarray(sorted(v for v in values if lo <= v <= hi))


def solve(h: float, cage_x: float, cage_z: float, bar_w: float, bar_h: float,
          bar_r: float, sleeve_t: float, sleeve_er: float) -> dict:
    x = make_axis([-cage_x, -bar_w/2, 0, bar_w/2, cage_x], h,
                  -cage_x, cage_x)
    z = make_axis([-cage_z, -bar_h/2, 0, bar_h/2, cage_z], h,
                  -cage_z, cage_z)
    xx, zz = np.meshgrid(x, z)
    signal = rounded_rect(xx, zz, bar_w/2, bar_h/2, bar_r)
    ground = (np.isclose(np.abs(xx), cage_x, atol=1e-9)
              | np.isclose(np.abs(zz), cage_z, atol=1e-9))
    fixed = signal | ground

    # Relative permittivity on edges, based on the controlled centering sleeve.
    xmid = (x[1:] + x[:-1]) / 2
    zmid = (z[1:] + z[:-1]) / 2
    xxe, zze = np.meshgrid(xmid, z)
    xxv, zzv = np.meshgrid(x, zmid)
    sleeve_x = bar_w/2 + sleeve_t
    sleeve_z = bar_h/2 + sleeve_t
    sleeve_r = bar_r + sleeve_t
    eps_x = np.where(rounded_rect(xxe, zze, sleeve_x, sleeve_z, sleeve_r),
                     sleeve_er, 1.0)
    eps_z = np.where(rounded_rect(xxv, zzv, sleeve_x, sleeve_z, sleeve_r),
                     sleeve_er, 1.0)

    xb = np.r_[x[0], (x[1:] + x[:-1])/2, x[-1]]
    zb = np.r_[z[0], (z[1:] + z[:-1])/2, z[-1]]
    wx, wz = np.diff(xb), np.diff(zb)
    gx = eps_x * wz[:, None] / np.diff(x)[None, :]
    gz = eps_z * wx[None, :] / np.diff(z)[:, None]
    nz, nx = len(z), len(x)
    ids = np.arange(nx*nz).reshape(nz, nx)
    u = np.r_[ids[:, :-1].ravel(), ids[:-1, :].ravel()]
    v = np.r_[ids[:, 1:].ravel(), ids[1:, :].ravel()]
    g = np.r_[gx.ravel(), gz.ravel()]
    mat = coo_matrix((np.r_[g, g, -g, -g],
                      (np.r_[u, v, u, v], np.r_[u, v, v, u])),
                     shape=(nx*nz, nx*nz)).tocsr()
    free = ~fixed.ravel()
    voltage = signal.astype(float).ravel()
    voltage[free] = spsolve(mat[free][:, free], -(mat @ voltage)[free])
    charge = mat @ voltage
    capacitance = float(charge[signal.ravel()].sum()*epsilon_0)
    return {"h_mm": h, "nodes": nx*nz, "C_F_per_m": capacitance}


def evaluate(sleeve_t: float, sleeve_er: float) -> dict:
    geom = {"cage_half_x_mm": 44.5, "cage_half_z_mm": 34.5,
            "bar_width_mm": 30.0, "bar_height_mm": 20.0,
            "bar_corner_radius_mm": 5.0, "sleeve_thickness_mm": sleeve_t,
            "sleeve_er": sleeve_er}
    rows = []
    for h in (0.40, 0.25, 0.16):
        air = solve(h, 44.5, 34.5, 30, 20, 5, 0, 1)
        loaded = solve(h, 44.5, 34.5, 30, 20, 5, sleeve_t, sleeve_er)
        c0, cc = air["C_F_per_m"], loaded["C_F_per_m"]
        z0 = 1/(c*np.sqrt(c0*cc))
        rows.append({"air": air, "loaded": loaded, "Z_ohm": z0,
                     "effective_er": cc/c0})
    z = rows[-1]["Z_ohm"]
    gamma_step = abs((z-50)/(z+50))
    # Worst reflection of a lossless uniform Z section between two 50-ohm
    # reference planes occurs at an odd quarter wave.
    r = z/50
    gamma_section_max = abs((r*r-1)/(r*r+1))
    outer_corner_radius = np.hypot(10-5, 15-5)+5+sleeve_t
    return {"geometry": geom, "mesh_rows": rows,
            "selected_Z_ohm": z,
            "single_step_return_loss_dB": 20*np.log10(gamma_step),
            "uniform_section_worst_return_loss_dB": 20*np.log10(gamma_section_max),
            "catalogue_min_core_ID_radial_margin_mm": 18.16-outer_corner_radius,
            "convergence_spread_percent": 100*(max(x["Z_ohm"] for x in rows)-min(x["Z_ohm"] for x in rows))/z}


def main() -> None:
    # Bounded sleeve sweep.  epsilon=1 is the empty-line reference; 2.8 and
    # 4.2 bracket common controlled plastic/FR-4-like structural inserts.
    cases = [evaluate(0, 1), evaluate(0.5, 2.8), evaluate(0.5, 4.2),
             evaluate(1.0, 2.8), evaluate(1.0, 4.2)]
    payload = {
        "classification": "CALCULATED_2D_QUASISTATIC_NOT_MEASURED",
        "architecture": "constant rounded current bar in constant rectangular external return enclosure",
        "cases": cases,
        "decision": "Select only a case with positive minimum-ID margin and a whole-section bound near -20 dB; do not tune decimals.",
        "limits": [
            "No ferrite, winding, keeper, seam, SMA launch, conductor loss or probe loading.",
            "The uniform-section formula is a conservative two-interface bound, not a 3-D launch result.",
            "Permittivity values are design brackets until a specific insert material is selected and verified.",
        ],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT/"a07_uniform_cross_section.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
