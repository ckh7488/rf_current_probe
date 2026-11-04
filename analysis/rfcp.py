"""Conditional ZT extraction; whitepaper sections 11, 12 and 16.

No automatic reference-plane correction, waveform inversion or renormalization.
Metadata assertions require external evidence; this program cannot validate hardware.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import skrf
from skrf.io.touchstone import Touchstone

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = "measurement_id head_id head_revision core_part turns shield_revision fixture_id calibration_id cable_ids receiver_model termination attenuation_profile source_level frequency_range if_bandwidth averaging temperature conductor_position timestamp data_kind".split()
QUALITY_CHECKS = ("snr", "linearity", "repeatability", "leakage", "position")
COLUMNS = "frequency_hz,s21_db,zt_real_ohm,zt_imag_ohm,zt_magnitude_ohm,zt_db_ohm,phase_deg,valid,uncertainty_db,quality_flag".split(",")


def finite_number(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name}: finite number required")
    if positive and value <= 0:
        raise ValueError(f"{name}: positive number required")
    return value


def read_touchstone(path, ports):
    """Reviewed subset: TS 1.0/2.0, full single-ended S matrix, real 50 ohm.

    Numerical parsing belongs to scikit-rf. Preflight rejects unsupported dialects
    that an accommodating parser could otherwise silently reinterpret.
    """
    source = Path(path).read_text(encoding="utf-8-sig")
    lines = [line.split("!", 1)[0].strip() for line in source.splitlines()]
    options = [line for line in lines if line.startswith("#")]
    if len(options) != 1:
        raise ValueError("Exactly one explicit Touchstone option line required")
    tokens = options[0][1:].lower().split()
    if len(tokens) != 5 or tokens[0] not in {"hz", "khz", "mhz", "ghz"} or tokens[1] != "s" or tokens[2] not in {"ri", "ma", "db"} or tokens[3] != "r":
        raise ValueError("Expected # Hz|kHz|MHz|GHz S RI|MA|DB R 50")
    if complex(tokens[4]) != 50:
        raise ValueError("Non-50-ohm input is unsupported; no implicit renormalization")
    keywords = {}
    allowed = {"version", "number of ports", "number of frequencies", "reference", "matrix format", "network data", "two-port data order", "end"}
    for line in lines:
        if line.startswith("["):
            match = re.fullmatch(r"\[([^]]+)\]\s*(.*)", line)
            if not match or match[1].lower() not in allowed:
                raise ValueError("Unsupported Touchstone keyword/dialect")
            key = match[1].lower()
            if key in keywords:
                raise ValueError(f"Duplicate keyword: {key}")
            keywords[key] = match[2].lower()
    version = keywords.get("version", "1.0")
    if version not in {"1.0", "2.0"}:
        raise ValueError("Only reviewed Touchstone 1.0 and 2.0 are supported")
    if keywords.get("matrix format", "full") != "full":
        raise ValueError("Full matrix required")
    if keywords.get("two-port data order", "21_12") not in {"21_12", "12_21"}:
        raise ValueError("Unrecognized two-port order")
    ts = Touchstone(str(path))
    f, s = ts.get_sparameter_arrays()
    if ts.rank != ports or ts.parameter != "s" or np.any(ts.port_modes != "S"):
        raise ValueError(f"Single-ended, {ports}-port S data required")
    if not np.all(np.isfinite(ts.z0)) or not np.allclose(ts.z0, 50, rtol=0, atol=1e-9):
        raise ValueError("All port references must be real 50 ohm")
    if len(f) < 2 or not np.all(np.isfinite(f)) or np.any(f <= 0) or np.any(np.diff(f) <= 0) or not np.all(np.isfinite(s)):
        raise ValueError("Finite data on a positive, strictly increasing frequency grid required")
    if "number of frequencies" in keywords and int(keywords["number of frequencies"]) != len(f):
        raise ValueError("Declared frequency count differs from data")
    return f, s


def read_s2p(path):
    return read_touchstone(path, 2)


def read_s1p(path):
    return read_touchstone(path, 1)


def require_evidence(value, name):
    if not isinstance(value, str) or not value.strip() or value.strip().upper() in {"TBD", "UNKNOWN", "NONE"}:
        raise ValueError(f"{name}: reviewed evidence reference required")


def band_mask(f, bands):
    mask = np.zeros(len(f), dtype=bool)
    if not isinstance(bands, list):
        raise ValueError("Frequency bands must be a list")
    for band in bands:
        if not isinstance(band, list) or len(band) != 2:
            raise ValueError("Each frequency band needs [low_hz, high_hz]")
        lo, hi = [finite_number(x, "band", positive=True) for x in band]
        if lo > hi:
            raise ValueError("Reversed frequency band")
        mask |= (f >= lo) & (f <= hi)
    return mask


def validate_metadata(meta, f):
    for key in REQUIRED:
        if key not in meta or meta[key] is None or meta[key] == "":
            raise ValueError(f"Missing metadata: {key}; use an explicit UNKNOWN for unavailable observations")
    if meta.get("schema_version") != 1 or meta["data_kind"] not in {"SYNTHETIC", "MEASURED", "SIMULATED"}:
        raise ValueError("schema_version=1 and explicit data_kind required")
    if meta["termination"] != "receiver_single_50_ohm":
        raise ValueError("Receiver single 50 ohm termination required")
    if not isinstance(meta["turns"], int) or isinstance(meta["turns"], bool) or meta["turns"] < 1:
        raise ValueError("Positive integer turns required")
    if meta["frequency_range"] != [float(f[0]), float(f[-1])]:
        raise ValueError("Metadata frequency range must equal the input endpoints in Hz")
    if type(meta.get("clipped")) is not bool or type(meta.get("phase_validated")) is not bool:
        raise ValueError("Explicit clipped and phase_validated booleans required")
    ids = meta.get("included_chain_ids")
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) or not x.strip() for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Unique nonempty included_chain_ids required (use HEAD_DIRECT for a direct head)")
    corrections = meta.get("additional_correction_ids", [])
    if not isinstance(corrections, list) or any(not isinstance(x, str) for x in corrections):
        raise ValueError("additional_correction_ids must be a list of identifiers")
    if set(ids) & set(corrections) or len(set(corrections)) != len(corrections):
        raise ValueError("Double chain correction rejected")
    if corrections:
        raise ValueError("Extra chain corrections not implemented: characterize the complete chain")
    u = meta.get("uncertainty_db")
    if u is not None:
        finite_number(u, "uncertainty_db", positive=True)
        require_evidence(meta.get("uncertainty_evidence"), "uncertainty")
    finite_number(meta.get("minimum_zt_ohm"), "minimum_zt_ohm", positive=True)
    if meta["phase_validated"]:
        require_evidence(meta.get("phase_evidence"), "phase")
    band_mask(f, meta.get("valid_frequency_bands_hz"))
    band_mask(f, meta.get("invalid_frequency_bands_hz", []))
    quality = meta.get("quality_review", {})
    for key in QUALITY_CHECKS:
        if quality.get(key) not in (True, False, None) or (quality.get(key) is not None and type(quality[key]) is not bool):
            raise ValueError(f"Quality check {key}: true/false/null required")
    if all(quality.get(key) is True for key in QUALITY_CHECKS):
        require_evidence(quality.get("evidence"), "quality review")


def extract(f, s, meta, *, output_reference=None):
    """Return rows; valid means conditional current-conversion eligibility only."""
    f, s = np.asarray(f, float), np.asarray(s, complex)
    if len(f) < 2 or s.shape != (len(f), 2, 2) or not np.all(np.isfinite(s)) or not np.all(np.isfinite(f)) or np.any(f <= 0) or np.any(np.diff(f) <= 0):
        raise ValueError("Invalid frequency/S matrix")
    validate_metadata(meta, f)
    model = meta.get("current_model", {"mode": "relative"})
    mode = model.get("mode", "relative")
    if mode == "output_reference":
        from analysis.output_reference import extract_output_reference
        return extract_output_reference(f, s, meta, output_reference)
    if mode not in {"relative", "matched", "input_current", "hi_model"}:
        raise ValueError("Unknown current model")
    conditions = {"matched": ["matched_path_verified", "current_reference_verified"], "input_current": ["same_current_plane_verified", "no_bypass_current_verified"], "hi_model": ["hi_reference_verified"]}
    if mode != "relative":
        require_evidence(model.get("evidence"), "current model")
        for key in conditions[mode]:
            if model.get(key) is not True:
                raise ValueError(f"Current conversion requires {key}")
    s11, s21 = s[:, 0, 0], s[:, 1, 0]
    if mode == "relative":
        hi = np.full(len(f), np.nan, complex)
    elif mode == "matched":
        hi = np.full(len(f), 1 / math.sqrt(50), complex)
    elif mode == "input_current":
        hi = (1 - s11) / math.sqrt(50)
    else:
        if model.get("frequency_hz") != f.tolist():
            raise ValueError("HI grid must exactly equal S-parameter grid; no automatic interpolation")
        real = np.asarray(model.get("hi_real_a_per_sqrt_w"), float)
        imag = np.asarray(model.get("hi_imag_a_per_sqrt_w"), float)
        if real.shape != f.shape or imag.shape != f.shape or not np.all(np.isfinite(real)) or not np.all(np.isfinite(imag)):
            raise ValueError("HI needs finite real and imaginary arrays in A/sqrt(W)")
        hi = real + 1j * imag
    good_hi = np.isfinite(hi) & (np.abs(hi) > 1e-12)
    zt = np.full(len(f), np.nan + 1j * np.nan)
    zt[good_hi] = math.sqrt(50) * s21[good_hi] / hi[good_hi]
    in_band = band_mask(f, meta["valid_frequency_bands_hz"]) & ~band_mask(f, meta.get("invalid_frequency_bands_hz", []))
    quality_ok = all(meta.get("quality_review", {}).get(k) is True for k in QUALITY_CHECKS)
    rows = []
    for i, freq in enumerate(f):
        reasons = []
        if mode == "relative": reasons.append("RELATIVE_ONLY")
        elif not good_hi[i]: reasons.append("CURRENT_MODEL_NULL")
        if not in_band[i]: reasons.append("OUTSIDE_VALID_BAND")
        if not quality_ok: reasons.append("QUALITY_UNASSESSED_OR_FAILED")
        if meta["clipped"]: reasons.append("CLIPPED")
        mag = float(abs(zt[i]))
        if not math.isfinite(mag) or mag <= meta["minimum_zt_ohm"]:
            reasons.append("ZT_NULL_OR_UNAVAILABLE")
        valid = not reasons
        flags = reasons[:]
        if meta.get("uncertainty_db") is None: flags.append("UNASSESSED")
        if not meta["phase_validated"]: flags.append("MAGNITUDE_ONLY")
        # Retain diagnostic S21 even when absolute conversion is forbidden.
        row = {key: None for key in COLUMNS}
        row.update(frequency_hz=float(freq), s21_db=float(20 * math.log10(abs(s21[i]))) if abs(s21[i]) > 0 else None,
                   valid=valid, uncertainty_db=meta.get("uncertainty_db"), quality_flag="|".join(flags) or "REVIEWED")
        if mode != "relative" and good_hi[i] and math.isfinite(mag) and not meta["clipped"]:
            row.update(zt_magnitude_ohm=mag, zt_db_ohm=20 * math.log10(mag) if mag > 0 else None)
            if meta["phase_validated"]:
                row.update(zt_real_ohm=float(zt[i].real), zt_imag_ohm=float(zt[i].imag), phase_deg=float(np.angle(zt[i], deg=True)))
        rows.append(row)
    return rows


def tone_current_rms(frequency_hz, voltage_rms, rows, meta, chain_ids, *, clipped=False):
    """Single sinusoidal component only. No waveform or peak reconstruction."""
    finite_number(frequency_hz, "frequency_hz", positive=True)
    finite_number(voltage_rms, "voltage_rms")
    if voltage_rms < 0 or clipped or meta["clipped"]:
        raise ValueError("Negative RMS/clipped data cannot be quantified")
    if chain_ids != meta["included_chain_ids"]:
        raise ValueError("Measurement chain/order differs from calibration")
    f = np.array([r["frequency_hz"] for r in rows])
    if frequency_hz < f[0] or frequency_hz > f[-1]:
        raise ValueError("Extrapolation prohibited")
    right = int(np.searchsorted(f, frequency_hz))
    indices = [right] if f[right] == frequency_hz else [right - 1, right]
    if any(not rows[i]["valid"] or not rows[i]["zt_magnitude_ohm"] for i in indices):
        raise ValueError("Invalid/null calibration interval")
    # Explicitly rejected gaps may lie between two retained samples.
    for lo, hi in meta.get("invalid_frequency_bands_hz", []):
        if lo <= f[indices[-1]] and hi >= f[indices[0]]:
            raise ValueError("Interpolation across invalid band prohibited")
    if not any(lo <= f[indices[0]] and hi >= f[indices[-1]] for lo, hi in meta["valid_frequency_bands_hz"]):
        raise ValueError("Interpolation across a gap prohibited")
    magnitudes = [rows[i]["zt_magnitude_ohm"] for i in indices]
    mag = float(np.exp(np.interp(np.log(frequency_hz), np.log(f[indices]), np.log(magnitudes))))
    if mag <= meta["minimum_zt_ohm"]:
        raise ValueError("Null inversion prohibited")
    return voltage_rms / mag


def sine_rms(value, convention, *, waveform):
    finite_number(value, "amplitude")
    if waveform != "sine" or value < 0:
        raise ValueError("Peak/RMS conversion requires a nonnegative sinusoidal amplitude")
    if convention not in {"rms", "peak", "peak_to_peak"}:
        raise ValueError("Unknown amplitude convention")
    return value / {"rms": 1, "peak": math.sqrt(2), "peak_to_peak": 2 * math.sqrt(2)}[convention]


def dbm_to_vrms(dbm, resistance=50):
    finite_number(dbm, "dBm")
    finite_number(resistance, "resistance", positive=True)
    return math.sqrt(1e-3 * 10 ** (dbm / 10) * resistance)


def db_micro(value):
    return 20 * math.log10(finite_number(value, "voltage/current", positive=True) / 1e-6)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_calibration(input_path, metadata_path):
    """Shared VNA/CW entry point; return all dependencies for provenance."""
    f, s = read_s2p(input_path)
    meta = json.loads(Path(metadata_path).read_text(encoding="utf-8-sig"))
    if "! SYNTHETIC" in Path(input_path).read_text(encoding="utf-8-sig").upper() and meta.get("data_kind") != "SYNTHETIC":
        raise ValueError("Input is labeled SYNTHETIC; contradictory metadata rejected")
    inputs = [Path(input_path).resolve(), Path(metadata_path).resolve()]
    prepared = None
    if meta.get("current_model", {}).get("mode") == "output_reference":
        from analysis.output_reference import load_bundle
        prepared, dependencies = load_bundle(input_path, metadata_path, meta)
        inputs.extend(dependencies)
    rows = extract(f, s, meta, output_reference=prepared)
    return f, s, meta, rows, list(dict.fromkeys(inputs))


def code_hashes():
    return {name: sha256(Path(__file__).with_name(name)) for name in ["rfcp.py", "output_reference.py"]}


def export(input_path, metadata_path, output_dir):
    f, s, meta, rows, inputs = load_calibration(input_path, metadata_path)
    output = Path(output_dir).resolve()
    forbidden = [ROOT / "measurements/raw", ROOT / "release"]
    if meta["data_kind"] != "MEASURED": forbidden.append(ROOT / "measurements")
    if any(output.is_relative_to(p.resolve()) for p in forbidden):
        raise ValueError("Output location is reserved for raw/approved/real measurement data")
    output.mkdir(parents=True, exist_ok=False)
    with (output / "zt.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, layout="constrained")
    mhz = f / 1e6
    axes[0].semilogx(mhz, [r["s21_db"] for r in rows], label="S21 (diagnostic)")
    axes[0].set_ylabel("S21 (dB)")
    for label, valid, style in [("eligible samples", True, "o-"), ("invalid samples", False, "x")]:
        y = [r["zt_db_ohm"] if r["valid"] == valid else np.nan for r in rows]
        axes[1].semilogx(mhz, y, style, markersize=3, label=label)
    axes[1].set_ylabel("Conditional |ZT| (dB ohm)")
    axes[1].set_xlabel("Frequency (MHz)")
    for ax in axes:
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(loc="best", fontsize=8)
    if all(r["zt_db_ohm"] is None for r in rows):
        axes[1].get_legend().remove()
        axes[1].set_yticks([])
        axes[1].text(.5, .5, "Absolute ZT unavailable\nNo eligible current conversion", transform=axes[1].transAxes,
                     ha="center", va="center", fontsize=13)
    bands = ", ".join(f"{lo/1e6:g}-{hi/1e6:g}" for lo, hi in meta["valid_frequency_bands_hz"]) or "none"
    uncertainty = "Per-frequency reviewed bound in zt.csv" if meta.get("current_model", {}).get("mode") == "output_reference" else "UNASSESSED" if meta.get("uncertainty_db") is None else f"{meta['uncertainty_db']:g} dB (see evidence)"
    fig.suptitle(f"{meta['data_kind']} | {meta['head_id']} | {meta['calibration_id']}\nModel: {meta.get('current_model', {}).get('mode', 'relative')} | Uncertainty: {uncertainty}\nReviewed candidate bands (MHz): {bands}", fontsize=10)
    fig.savefig(output / "response.png", dpi=160)
    plt.close(fig)
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
                "scikit_rf": skrf.__version__, "numpy": np.__version__, "metadata": meta,
                "inputs": {str(Path(p).resolve()): sha256(p) for p in inputs},
                "code_sha256": sha256(__file__), "analysis_code_sha256": code_hashes(), "rows": len(rows), "eligible_rows": sum(r["valid"] for r in rows),
                "scope_internal_response_included": False,
                "meaning": "Conditional extraction, not proof of hardware performance or uncertainty."}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Two-port Touchstone file")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="New directory; never overwrite")
    args = parser.parse_args()
    try:
        manifest = export(args.input, args.metadata, args.out)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Rejected: {exc}\n")
    print(json.dumps({k: manifest[k] for k in ["rows", "eligible_rows", "meaning"]}))


if __name__ == "__main__":
    main()
