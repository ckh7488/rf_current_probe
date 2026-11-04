"""Quasi-static screen for a structure-only return cage around Fixture A05.

The solve is a 2-D electrostatic cross-section normal to the fixture current
path.  It answers one bounded question before another expensive 3-D run:
does a four-sided return placed outside the complete probe/keeper envelope
lower the local line impedance enough to justify modelling the transitions?

This is deliberately not a calibration-accuracy result.  It omits the SMA
launches, longitudinal transitions, ferrite dispersion/loss, seams and all
manufacturing contact resistance.
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

Z_L4 = -0.8
Z_L3 = -0.5896
Z_L2 = 0.5896
Z_L1 = 0.8
COPPER_Z = [Z_L4, Z_L3, Z_L2, Z_L1]
RETURN_INNER = 34.5005
BOARD_OUTER = 71.4995
BOARD_HALF = 15.5005


def axis(anchors: list[float], h: float, lower: float, upper: float) -> np.ndarray:
    values = {lower, upper}
    span = upper - lower
    for anchor in anchors:
        if lower <= anchor <= upper:
            values.add(anchor)
        for sign in (-1, 1):
            distance = h
            while distance < 2 * span:
                value = anchor + sign * distance
                if lower < value < upper:
                    values.add(value)
                distance *= 1.23
    raw = np.asarray(sorted(values))
    protected = set(a for a in anchors if lower <= a <= upper) | {lower, upper}
    keep: list[float] = []
    for value in raw:
        if keep and value - keep[-1] < h * 0.24:
            if value in protected and keep[-1] not in protected:
                keep[-1] = value
            elif value in protected and keep[-1] in protected:
                keep.append(value)
        else:
            keep.append(value)
    return np.asarray(keep)


def overlap(lo: np.ndarray, hi: np.ndarray, lower: float, upper: float) -> np.ndarray:
    return np.maximum(0.0, np.minimum(hi, upper) - np.maximum(lo, lower))


def solve(h: float, cage_x: float, cage_z: float, signal_width: float,
          signal_height: float, dielectric: bool, save_field: bool = False) -> dict:
    """Solve capacitance per length for a closed rectangular return cage.

    signal_height=0 represents the saved A05 L1-only zero-thickness trace.
    Positive height is a geometry study for an equipotential rectangular
    current bar centred on the board mid-plane; it is not present in A05.
    """
    sig_half = signal_width / 2
    sig_z_lo = -signal_height / 2 if signal_height else Z_L1
    sig_z_hi = signal_height / 2 if signal_height else Z_L1
    x = axis([-cage_x, -RETURN_INNER, -BOARD_HALF, -sig_half, 0,
              sig_half, BOARD_HALF, RETURN_INNER, cage_x], h, -cage_x, cage_x)
    z = axis([-cage_z, sig_z_lo, Z_L4, Z_L3, 0, Z_L2, Z_L1,
              sig_z_hi, cage_z], h, -cage_z, cage_z)
    nx, nz = len(x), len(z)
    xx, zz = np.meshgrid(x, z)

    if signal_height:
        signal = ((np.abs(xx) <= sig_half + 1e-9)
                  & (zz >= sig_z_lo - 1e-9) & (zz <= sig_z_hi + 1e-9))
    else:
        signal = (np.isclose(zz, Z_L1, atol=1e-9)
                  & (np.abs(xx) <= sig_half + 1e-9))

    # The cage is a closed, equipotential return.  The four saved A05 side
    # planes remain included where they fit inside it and are connected to it.
    wall = (np.isclose(np.abs(xx), cage_x, atol=1e-9)
            | np.isclose(np.abs(zz), cage_z, atol=1e-9))
    layer = np.logical_or.reduce(
        [np.isclose(zz, plane, atol=1e-9) for plane in COPPER_Z])
    side_planes = layer & (np.abs(xx) >= RETURN_INNER - 1e-9)
    ground = wall | side_planes
    fixed = signal | ground
    if np.any(signal & ground):
        raise RuntimeError("signal intersects cage/ground")

    xb = np.r_[x[0], (x[1:] + x[:-1]) / 2, x[-1]]
    zb = np.r_[z[0], (z[1:] + z[:-1]) / 2, z[-1]]
    wx = np.diff(xb)
    wz = np.diff(zb)

    # A05 has FR-4 only under the 31 mm bridge and in the side-board regions.
    xmid = (x[1:] + x[:-1]) / 2
    solid_x_edge = ((np.abs(xmid) <= BOARD_HALF)
                    | (np.abs(xmid) >= RETURN_INNER))
    if dielectric:
        outer_fraction = (overlap(zb[:-1], zb[1:], Z_L4, Z_L3)
                          + overlap(zb[:-1], zb[1:], Z_L2, Z_L1)) / wz
        core_fraction = overlap(zb[:-1], zb[1:], Z_L3, Z_L2) / wz
        eps_z_node = (1 + (4.3 - 1) * outer_fraction
                      + (4.3 - 1) * core_fraction)
        eps_x_edge = 1 + ((eps_z_node - 1)[:, None] * solid_x_edge[None, :])
    else:
        eps_x_edge = np.ones((nz, nx - 1))
    gx = eps_x_edge * wz[:, None] / np.diff(x)[None, :]

    zmid = (z[1:] + z[:-1]) / 2
    solid_fraction_x = (overlap(xb[:-1], xb[1:], -BOARD_HALF, BOARD_HALF)
                        + overlap(xb[:-1], xb[1:], -cage_x, -RETURN_INNER)
                        + overlap(xb[:-1], xb[1:], RETURN_INNER, cage_x)) / wx
    if dielectric:
        er_z_edge = np.where((zmid >= Z_L4) & (zmid <= Z_L1), 4.3, 1.0)
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
    voltage[free] = spsolve(matrix[free][:, free], -(matrix @ voltage)[free])
    charge = matrix @ voltage
    capacitance = float(charge[signal.ravel()].sum() * epsilon_0)
    ground_charge = float(charge[ground.ravel()].sum() * epsilon_0)
    energy_cap = float(np.dot(conductance, (voltage[u] - voltage[v]) ** 2)
                       * epsilon_0)
    if save_field:
        np.savez_compressed(
            OUT / "a05_cage_cross_section_field.npz", x=x, z=z,
            voltage=voltage.reshape(nz, nx), signal=signal, ground=ground)
    return {
        "h_mm": h,
        "nodes": nx * nz,
        "C_F_per_m": capacitance,
        "charge_balance_relative": abs(capacitance + ground_charge) / capacitance,
        "energy_relative_error": abs(energy_cap - capacitance) / capacitance,
    }


def evaluate(cage_x: float, cage_z: float, signal_width: float,
             signal_height: float, convergence: bool = False) -> dict:
    hs = [0.30, 0.15, 0.075] if convergence else [0.15]
    rows = []
    for h in hs:
        air = solve(h, cage_x, cage_z, signal_width, signal_height, False)
        diel = solve(h, cage_x, cage_z, signal_width, signal_height, True,
                     save_field=(convergence and h == hs[-1]))
        c0, cc = air["C_F_per_m"], diel["C_F_per_m"]
        rows.append({
            "air": air,
            "dielectric": diel,
            "Z_ohm": 1 / (c * np.sqrt(cc * c0)),
            "effective_er": cc / c0,
            "L_H_per_m": 1 / (c * c * c0),
        })
    z = rows[-1]["Z_ohm"]
    gamma = abs((z - 50) / (z + 50))
    return {
        "geometry_mm": {"cage_half_x": cage_x, "cage_half_z": cage_z,
                         "signal_width": signal_width,
                         "signal_height": signal_height},
        "cases": rows,
        "selected": rows[-1],
        "local_step_return_loss_dB": float(20 * np.log10(gamma)) if gamma else -300.0,
        "convergence_Z_spread_percent": (
            100 * (max(r["Z_ohm"] for r in rows) - min(r["Z_ohm"] for r in rows)) / z),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Three cage envelopes and three structural centre-conductor shapes are
    # enough to identify the controlling variable without threshold chasing.
    candidates = []
    for cage_x, cage_z in [(46, 36), (48, 38), (50, 40)]:
        for sig_h in (0.0, 1.6, 8.0, 12.0):
            candidates.append(evaluate(cage_x, cage_z, 30.0, sig_h))
    best = min(candidates, key=lambda r: abs(r["selected"]["Z_ohm"] - 50))
    selected = evaluate(best["geometry_mm"]["cage_half_x"],
                        best["geometry_mm"]["cage_half_z"], 30.0,
                        best["geometry_mm"]["signal_height"], True)
    result = {
        "classification": "SIMULATED_2D_QUASISTATIC_STRUCTURE_SCREEN_NOT_MEASURED",
        "question": "Does a mechanically external four-sided return cage make a structure-only 100-500 MHz candidate plausible?",
        "saved_A05_reference": {"signal_width_mm": 29.999,
                                "nearest_planar_return_abs_x_mm": 34.5005,
                                "selected_Z_ohm": 130.492},
        "candidate_sweep": candidates,
        "selected_for_convergence": selected,
        "mechanical_basis_mm": {
            "core_max_outer_half_width": 31.115,
            "keeper_bounds_x": [-44, 44],
            "keeper_bounds_board_normal": [-33.5, 33.5],
            "tightest_cage_nominal_clearance_to_keeper_x": 2,
            "tightest_cage_nominal_clearance_to_keeper_normal": 2.5,
        },
        "interpretation_rules": [
            "The local step return loss is a discontinuity diagnostic, not the finite-length fixture S11.",
            "Only a promising local impedance proceeds to a three-dimensional transition solve.",
            "Positive signal height is a new metal current-bar concept and is not present in the A05 PCB.",
        ],
        "limitations": [
            "Ideal closed and perfectly bonded return cage; removable seams/contact impedance are omitted.",
            "Ferrite, keeper dielectric, SMA launches and longitudinal tapers are omitted.",
            "Zero-thickness copper except for the explicitly swept signal-bar height.",
            "This result cannot establish calibration accuracy or manufacturing fit.",
        ],
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    path = OUT / "a05_cage_cross_section.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "candidates": [{**r["geometry_mm"],
                        "Z_ohm": r["selected"]["Z_ohm"],
                        "local_step_RL_dB": r["local_step_return_loss_dB"]}
                       for r in candidates],
        "selected": selected,
        "output": str(path),
    }, indent=2))


if __name__ == "__main__":
    main()
