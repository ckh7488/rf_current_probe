"""SYNTHETIC lumped counterexample, not a fitted physical fixture model.

At the P1 plane a shunt capacitance bypasses the branch passing through the core.
The branch consists of series L and an effective resistive load (load + insertion).
Power waves use real Z0: V/a=sqrt(Z0)*(1+S11), HI=Icore/a.
"""
import numpy as np


def synthetic_fixture(frequency_hz, zt_ohm=5.0, series_l_h=30e-9,
                      bypass_c_f=3e-12, branch_r_ohm=52.0, z0=50.0):
    f = np.asarray(frequency_hz, dtype=float)
    if np.any(f <= 0) or not np.all(np.isfinite(f)) or series_l_h < 0 or bypass_c_f < 0 or branch_r_ohm <= 0 or z0 <= 0:
        raise ValueError("Invalid model parameters")
    jw = 2j * np.pi * f
    branch_y = 1 / (branch_r_ohm + jw * series_l_h)
    input_z = 1 / (branch_y + jw * bypass_c_f)
    s11 = (input_z - z0) / (input_z + z0)
    hi = np.sqrt(z0) * (1 + s11) * branch_y
    s = np.zeros((len(f), 2, 2), dtype=complex)
    s[:, 0, 0] = s11
    s[:, 1, 0] = zt_ohm * hi / np.sqrt(z0)
    # S12/S22 are unused placeholders in this math test, not a reciprocal RF model.
    return s, hi
