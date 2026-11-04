"""Offline CW fundamental measurement; never a pulse-current reconstruction.

Input is an explicitly normalized seconds/volts CSV, NOT arbitrary Tek CSV.
Current conversion additionally requires the same calibrated output plane,
external chain and a reviewed receiver gain/loading measurement at this tone.
Metadata evidence is an assertion by the reviewer, not hardware verification.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from analysis import rfcp


def read_waveform(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["time_s", "voltage_v"]:
            raise ValueError("Normalize explicitly to time_s,voltage_v; native scope CSV is not accepted")
        records = list(reader)
    if any(set(row) != {"time_s", "voltage_v"} or None in row.values() for row in records):
        raise ValueError("Exactly two populated columns required")
    try:
        return np.array([float(r["time_s"]) for r in records]), np.array([float(r["voltage_v"]) for r in records])
    except (TypeError, ValueError) as exc:
        raise ValueError("Numeric seconds and volts required") from exc


def fit_tone(t, v, frequency_hz, harmonics=3):
    """Simultaneous DC + harmonics least squares on uniformly spaced samples.

    RMS of harmonic k is hypot(sin coefficient, cos coefficient)/sqrt(2).
    No FFT window/RBW assumptions. Does not detect out-of-band aliasing.
    """
    rfcp.finite_number(frequency_hz, "tone frequency", positive=True)
    if type(harmonics) is not int or not 1 <= harmonics <= 5:
        raise ValueError("harmonics must be an integer from 1 through 5")
    t, v = np.asarray(t, float), np.asarray(v, float)
    if t.ndim != 1 or v.shape != t.shape or len(t) < 128 or not np.all(np.isfinite(t)) or not np.all(np.isfinite(v)):
        raise ValueError("At least 128 finite time/voltage samples required")
    dt = np.diff(t)
    if np.any(dt <= 0) or not np.allclose(dt, dt[0], rtol=1e-6, atol=0):
        raise ValueError("Uniform, strictly increasing seconds required")
    sample_rate = float(1 / np.median(dt))
    if frequency_hz * harmonics >= .45 * sample_rate:
        raise ValueError("Fitted harmonics too close to/above Nyquist; acquire faster or reduce fit order")
    if (t[-1] - t[0]) * frequency_hz < 20:
        raise ValueError("At least 20 tone cycles required")
    phase = 2 * math.pi * frequency_hz * (t - t[0])
    columns = [np.ones(len(t))]
    for k in range(1, harmonics + 1):
        columns.extend([np.sin(k * phase), np.cos(k * phase)])
    design = np.column_stack(columns)
    coeff, _, rank, _ = np.linalg.lstsq(design, v, rcond=None)
    if rank != len(columns):
        raise ValueError("Singular tone fit")
    amplitudes = [float(math.hypot(coeff[2*k-1], coeff[2*k]) / math.sqrt(2)) for k in range(1, harmonics+1)]
    residual = float(np.sqrt(np.mean((v - design @ coeff) ** 2)))
    if amplitudes[0] <= 1e-15:
        raise ValueError("Fundamental is null")
    return {"sample_rate_hz": sample_rate, "samples": len(t), "frequency_hz": frequency_hz,
            "fundamental_vrms_displayed": amplitudes[0], "harmonics_vrms_displayed": amplitudes,
            "fit_harmonics": harmonics,
            "partial_thd_ratio": float(np.linalg.norm(amplitudes[1:]) / amplitudes[0]) if harmonics > 1 else None,
            "dc_v_displayed": float(coeff[0]), "total_vrms_displayed": float(np.sqrt(np.mean(v*v))),
            "residual_vrms": residual, "residual_to_fundamental_ratio": residual / amplitudes[0]}


def validate_scope(meta):
    if meta.get("schema_version") != 1 or meta.get("data_kind") not in {"MEASURED", "SYNTHETIC", "SIMULATED"}:
        raise ValueError("Explicit scope schema/data_kind required")
    for key in ["measurement_id", "receiver_id", "receiver_model", "channel", "head_id", "head_revision",
                "timestamp", "normalization_evidence", "setup_evidence"]:
        rfcp.require_evidence(meta.get(key), key)
    if meta.get("voltage_convention") != "displayed_volts_probe_1x" or type(meta.get("probe_factor")) not in (int, float) or meta["probe_factor"] != 1:
        raise ValueError("Voltage probe 1x and already scaled display volts required")
    if meta.get("input_ohm") != 50 or meta.get("external_50ohm_termination") is not False:
        raise ValueError("Use internal 50 ohm only; parallel external termination rejected")
    if meta.get("coupling") != "DC" or meta.get("bandwidth_setting") != "FULL" or meta.get("acquisition_mode") != "sample":
        raise ValueError("Reviewed workflow requires DC, FULL, sample acquisition")
    if meta.get("clipped") is not False or meta.get("overload") is not False:
        raise ValueError("Explicit no-clipping and no-overload observations required")
    if meta.get("source_mode") != "CW" or meta.get("stationarity_verified") is not True:
        raise ValueError("Stationary CW required; swept VNA/pulse record is not a tone")
    for key in ["aliasing_review", "noise_review"]:
        if meta.get(key, {}).get("verified") is not True:
            raise ValueError(f"{key} required")
        rfcp.require_evidence(meta[key].get("evidence"), key)
    for key in ["sample_rate_hz", "volts_per_div", "frequency_hz"]:
        rfcp.finite_number(meta.get(key), key, positive=True)
    if type(meta.get("record_length")) is not int or meta["record_length"] < 128:
        raise ValueError("record_length required")
    for key in ["channel_offset_v", "temperature_c"]:
        rfcp.finite_number(meta.get(key), key)
    if meta.get("additional_correction_ids", []) or meta.get("external_gain_applied") is not False:
        raise ValueError("Do not reapply cable/attenuator compensation or scope current scaling")


def quantify(t, v, scope, calibration=None, rows=None):
    validate_scope(scope)
    fit = fit_tone(t, v, scope["frequency_hz"], scope.get("fit_harmonics", 3))
    if fit["samples"] != scope["record_length"] or not math.isclose(fit["sample_rate_hz"], scope["sample_rate_hz"], rel_tol=1e-6):
        raise ValueError("Waveform sample rate/record length disagree with acquisition metadata")
    # This is a consistency guard, not a bound on measurement uncertainty.
    if fit["residual_to_fundamental_ratio"] > .1:
        raise ValueError("Large unmodelled residual: check frequency, drift, noise, other tones")
    result = dict(fit, data_kind=scope["data_kind"], current_rms_a=None, uncertainty_db=None,
                  status="VOLTAGE_ONLY", scope_internal_response_included=False,
                  limitation="Fundamental only. Partial THD/residual do not prove absence of aliasing or hardware accuracy.")
    if calibration is None:
        return result
    if scope["data_kind"] != calibration["data_kind"]:
        raise ValueError("Synthetic/simulated/measured provenance must match")
    for key in ["head_id", "head_revision", "calibration_id", "included_chain_ids"]:
        if scope.get(key) != calibration.get(key):
            raise ValueError(f"Changed or missing calibrated {key}")
    plane = calibration.get("output_reference_plane", {})
    if plane.get("verified") is not True or plane.get("impedance_ohm") != 50:
        raise ValueError("Calibrated output reference plane not reviewed")
    rfcp.require_evidence(plane.get("id"), "reference plane ID")
    rfcp.require_evidence(plane.get("evidence"), "reference plane")
    if scope.get("input_reference_plane_id") != plane["id"]:
        raise ValueError("VNA-to-scope reference plane differs; adapter removal is not automatic de-embedding")
    receiver = scope.get("receiver_response", {})
    if receiver.get("verified") is not True or receiver.get("loading_verified") is not True:
        raise ValueError("Receiver amplitude response and 50-ohm loading equivalence need evidence")
    rfcp.require_evidence(receiver.get("evidence"), "receiver response")
    # Deliberately exact frequency, instrument/settings and chain binding: no
    # implicit reuse of a response table acquired at a different scale/channel.
    settings = ["receiver_id", "receiver_model", "channel", "input_ohm", "coupling", "bandwidth_setting",
                "probe_factor", "volts_per_div", "channel_offset_v", "sample_rate_hz", "acquisition_mode",
                "head_id", "head_revision", "included_chain_ids", "input_reference_plane_id"]
    if receiver.get("settings") != {key: scope[key] for key in settings}:
        raise ValueError("Receiver response settings/chain do not match")
    if receiver.get("frequency_hz") != scope["frequency_hz"] or receiver.get("gain_definition") != "displayed_V_per_calibrated_50ohm_V":
        raise ValueError("Receiver gain must refer to this tone and calibrated 50-ohm voltage")
    gain = rfcp.finite_number(receiver.get("gain"), "receiver gain", positive=True)
    limits = receiver.get("temperature_range_c")
    if not isinstance(limits, list) or len(limits) != 2:
        raise ValueError("Reviewed receiver temperature interval required")
    lo, hi = [rfcp.finite_number(x, "temperature limit") for x in limits]
    if not lo <= scope["temperature_c"] <= hi:
        raise ValueError("Receiver temperature outside reviewed interval")
    result["current_rms_a"] = rfcp.tone_current_rms(scope["frequency_hz"], fit["fundamental_vrms_displayed"] / gain,
                                                   rows, calibration, scope["included_chain_ids"])
    result.update(status="CONDITIONAL_FUNDAMENTAL_CURRENT", scope_internal_response_included=True,
                  receiver_gain=gain, calibration_id=calibration["calibration_id"],
                  uncertainty_note="UNASSESSED: calibration, receiver, loading, fit and noise require a combined budget")
    return result


def export(waveform, metadata, output, calibration_s2p=None, calibration_metadata=None):
    t, v = read_waveform(waveform)
    scope = json.loads(Path(metadata).read_text(encoding="utf-8-sig"))
    inputs = [waveform, metadata]
    cal, rows = None, None
    if bool(calibration_s2p) != bool(calibration_metadata):
        raise ValueError("Both calibration files must be provided together")
    if calibration_s2p:
        _, _, cal, rows, dependencies = rfcp.load_calibration(calibration_s2p, calibration_metadata)
        inputs.extend(dependencies)
    result = quantify(t, v, scope, cal, rows)
    out = Path(output).resolve()
    forbidden = [rfcp.ROOT / "measurements/raw", rfcp.ROOT / "release"]
    if scope["data_kind"] != "MEASURED":
        forbidden.append(rfcp.ROOT / "measurements")
    if any(out.is_relative_to(p.resolve()) for p in forbidden):
        raise ValueError("Output reserved for raw/approved/real measurement data")
    out.mkdir(parents=True, exist_ok=False)
    (out / "tone_result.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "metadata": scope,
                "python": platform.python_version(), "numpy": np.__version__,
                "calibration_metadata": cal, "inputs": {str(Path(p).resolve()): rfcp.sha256(p) for p in inputs},
                "code_sha256": {"scope_tone.py": rfcp.sha256(__file__), **rfcp.code_hashes()},
                "meaning": "Offline analysis; metadata assertions are not verification of connected instruments."}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("waveform", type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--calibration-s2p", type=Path)
    parser.add_argument("--calibration-metadata", type=Path)
    args = parser.parse_args()
    try:
        result = export(args.waveform, args.metadata, args.out, args.calibration_s2p, args.calibration_metadata)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Rejected: {exc}\n")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
