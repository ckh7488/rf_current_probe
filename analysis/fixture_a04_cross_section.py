"""Quasi-static central cross-section for the four-layer Fixture A04.

Unlike the legacy A03 model, A04 has SIG on L1 only.  The four side-return
layers are tied together and remain outside the ferrite aperture.  This finite
volume Laplace solve calculates the local return-free mode used only as a
reducer seed for the subsequent 3-D model.
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

# Cross-section coordinates, centred through board thickness.
SIG_HALF = 3.4
BRIDGE_HALF = 4.0
RETURN_INNER = 51.3
RETURN_OUTER = 71.5
Z_L4 = -0.8
Z_L3 = -0.5896
Z_L2 = 0.5896
Z_L1 = 0.8
COPPER_Z = [Z_L4, Z_L3, Z_L2, Z_L1]


def axis(anchors: list[float], h: float, domain: float) -> np.ndarray:
    values = {-domain, domain}
    for anchor in anchors:
        values.add(anchor)
        for sign in [-1, 1]:
            distance = h
            while distance < 2 * domain:
                value = anchor + sign * distance
                if -domain < value < domain:
                    values.add(value)
                distance *= 1.23
    raw = np.asarray(sorted(values))
    protected = set(anchors) | {-domain, domain}
    keep: list[float] = []
    for value in raw:
        if keep and value - keep[-1] < h * 0.24:
            if value in protected:
                if keep[-1] not in protected:
                    keep[-1] = value
                else:
                    keep.append(value)
        else:
            keep.append(value)
    return np.asarray(keep)


def overlap(lo: np.ndarray, hi: np.ndarray, lower: float,
            upper: float) -> np.ndarray:
    return np.maximum(0.0, np.minimum(hi, upper) - np.maximum(lo, lower))


def solve(h: float, domain: float, dielectric: bool,
          save_field: bool = False) -> dict:
    x = axis([-RETURN_OUTER, -RETURN_INNER, -BRIDGE_HALF, -SIG_HALF,
              0, SIG_HALF, BRIDGE_HALF, RETURN_INNER, RETURN_OUTER],
             h, domain)
    z = axis(COPPER_Z, h, domain)
    nx, nz = len(x), len(z)
    xx, zz = np.meshgrid(x, z)

    signal = np.isclose(zz, Z_L1, atol=1e-9) & (np.abs(xx) <= SIG_HALF + 1e-9)
    ground_plane = np.logical_or.reduce(
        [np.isclose(zz, plane, atol=1e-9) for plane in COPPER_Z])
    ground = (ground_plane & (np.abs(xx) >= RETURN_INNER - 1e-9)
              & (np.abs(xx) <= RETURN_OUTER + 1e-9))
    fixed = signal | ground

    xb = np.r_[x[0], (x[1:] + x[:-1]) / 2, x[-1]]
    zb = np.r_[z[0], (z[1:] + z[:-1]) / 2, z[-1]]
    wx = np.diff(xb)
    wz = np.diff(zb)

    xmid = (x[1:] + x[:-1]) / 2
    solid_x_edge = ((np.abs(xmid) <= BRIDGE_HALF)
                    | ((np.abs(xmid) >= 51) & (np.abs(xmid) <= 72)))
    if dielectric:
        outer_fraction = (
            overlap(zb[:-1], zb[1:], Z_L4, Z_L3)
            + overlap(zb[:-1], zb[1:], Z_L2, Z_L1)) / wz
        core_fraction = overlap(zb[:-1], zb[1:], Z_L3, Z_L2) / wz
        eps_z_node = (1 + (4.4 - 1) * outer_fraction
                      + (4.6 - 1) * core_fraction)
        eps_x_edge = 1 + ((eps_z_node - 1)[:, None]
                          * solid_x_edge[None, :])
    else:
        eps_x_edge = np.ones((nz, nx - 1))
    gx = eps_x_edge * wz[:, None] / np.diff(x)[None, :]

    zmid = (z[1:] + z[:-1]) / 2
    solid_fraction_x = (
        overlap(xb[:-1], xb[1:], -BRIDGE_HALF, BRIDGE_HALF)
        + overlap(xb[:-1], xb[1:], -72, -51)
        + overlap(xb[:-1], xb[1:], 51, 72)) / wx
    if dielectric:
        er_z_edge = np.where(
            ((zmid >= Z_L4) & (zmid < Z_L3))
            | ((zmid > Z_L2) & (zmid <= Z_L1)),
            4.4,
            np.where((zmid >= Z_L3) & (zmid <= Z_L2), 4.6, 1.0))
        eps_z_edge = 1 + ((er_z_edge - 1)[:, None]
                          * solid_fraction_x[None, :])
    else:
        eps_z_edge = np.ones((nz - 1, nx))
    gz = eps_z_edge * wx[None, :] / np.diff(z)[:, None]

    ids = np.arange(nx * nz).reshape(nz, nx)
    u = np.r_[ids[:, :-1].ravel(), ids[:-1, :].ravel()]
    v = np.r_[ids[:, 1:].ravel(), ids[1:, :].ravel()]
    conductance = np.r_[gx.ravel(), gz.ravel()]
    matrix = coo_matrix(
        (np.r_[conductance, conductance, -conductance, -conductance],
         (np.r_[u, v, u, v], np.r_[u, v, v, u])),
        shape=(nx * nz, nx * nz)).tocsr()
    free = ~fixed.ravel()
    voltage = signal.astype(float).ravel()
    voltage[free] = spsolve(matrix[free][:, free],
                            -(matrix @ voltage)[free])
    charge = matrix @ voltage
    capacitance = float(charge[signal.ravel()].sum() * epsilon_0)
    ground_charge = float(charge[ground.ravel()].sum() * epsilon_0)
    energy_cap = float(np.dot(conductance,
                              (voltage[u] - voltage[v]) ** 2) * epsilon_0)
    if save_field:
        np.savez_compressed(OUT / "a04_cross_section_field.npz",
                            x=x, z=z, voltage=voltage.reshape(nz, nx),
                            signal=signal, ground=ground)
    return {
        "h_mm": h,
        "domain_half_mm": domain,
        "dielectric": dielectric,
        "nodes": nx * nz,
        "C_F_per_m": capacitance,
        "charge_balance_relative": abs(capacitance + ground_charge) / capacitance,
        "energy_relative_error": abs(energy_cap - capacitance) / capacitance,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = []
    for h in [0.30, 0.15, 0.075]:
        air = solve(h, 500, False)
        diel = solve(h, 500, True, save_field=h == 0.075)
        c0 = air["C_F_per_m"]
        cc = diel["C_F_per_m"]
        cases.append({
            "air": air,
            "dielectric": diel,
            "Z_ohm": 1 / (c * np.sqrt(cc * c0)),
            "effective_er": cc / c0,
            "L_H_per_m": 1 / (c * c * c0),
        })
        print(json.dumps(cases[-1]), flush=True)

    result = {
        "classification": "SIMULATED_2D_QUASISTATIC_NOT_MEASURED",
        "model": (
            "Fixture A04 central cross-section: L1-only 6.8 mm SIG; "
            "four equipotential side-return layers; no launch, longitudinal "
            "plane edge, connector, core, loss or 3-D mode conversion"),
        "geometry_mm": {
            "signal_width": 2 * SIG_HALF,
            "bridge_width": 2 * BRIDGE_HALF,
            "return_inner_abs_x": RETURN_INNER,
            "return_outer_abs_x": RETURN_OUTER,
            "stack_z": {"L4": Z_L4, "L3": Z_L3,
                        "L2": Z_L2, "L1": Z_L1},
            "outer_dielectric_er": 4.4,
            "core_dielectric_er": 4.6,
        },
        "cases": cases,
        "selected": cases[-1],
        "convergence": {
            "Z_spread_percent": 100 * (max(row["Z_ohm"] for row in cases)
                                        - min(row["Z_ohm"] for row in cases))
                                / cases[-1]["Z_ohm"],
            "effective_er_spread_percent": 100 * (
                max(row["effective_er"] for row in cases)
                - min(row["effective_er"] for row in cases))
                / cases[-1]["effective_er"],
        },
        "limitations": [
            "Zero-thickness copper and ideal equipotential via connection.",
            "Natural outer boundary at +/-500 mm; only grid convergence is sampled.",
            "The cross-section is a reducer seed and cannot establish 100-500 MHz match or calibration accuracy.",
        ],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "a04_cross_section.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"selected": result["selected"],
                      "convergence": result["convergence"]}, indent=2))


if __name__ == "__main__":
    main()
