import copy
import json
import math
import subprocess
import sys

import numpy as np
import pytest

from analysis import rfcp, scope_tone
from tests.rehearsal_data import example


def test_end_to_end_attenuator_receiver_harmonics():
    f, s, cal, t, v, scope = example()
    result = scope_tone.quantify(t, v, scope, cal, rfcp.extract(f, s, cal))
    assert result["current_rms_a"] == pytest.approx(.001, rel=1e-11)
    assert result["partial_thd_ratio"] == pytest.approx(.4)
    assert result["uncertainty_db"] is None
    assert result["total_vrms_displayed"] > result["fundamental_vrms_displayed"] * 1.1
    # The 10 dB attenuator was inside ZT, so it was counted once.
    assert result["fundamental_vrms_displayed"] == pytest.approx(.001*5/math.sqrt(10)*.9)


def test_voltage_only_does_not_invent_current():
    _, _, _, t, v, scope = example()
    scope.pop("receiver_response")
    result = scope_tone.quantify(t, v, scope)
    assert result["current_rms_a"] is None and result["status"] == "VOLTAGE_ONLY"


@pytest.mark.parametrize("key,value,error", [
    ("probe_factor", 10, "1x"), ("input_ohm", 1e6, "50 ohm"),
    ("external_50ohm_termination", True, "50 ohm"), ("clipped", True, "clipping"),
    ("clipped", None, "clipping"), ("overload", True, "overload"),
    ("source_mode", "VNA_SWEEP", "CW"), ("stationarity_verified", False, "CW"),
    ("coupling", "AC", "DC"), ("bandwidth_setting", "20MHz", "FULL"),
    ("external_gain_applied", True, "reapply"), ("additional_correction_ids", ["SYN-ATT10"], "reapply"),
    ("head_id", "OTHER", "head_id"), ("head_revision", "7T", "head_revision"),
    ("calibration_id", "OTHER", "calibration_id"),
    ("included_chain_ids", ["SYN-CAB01", "SYN-ATT10"], "included_chain_ids"),
    ("input_reference_plane_id", "ADAPTER_SMA_SIDE", "reference plane differs"),
    ("data_kind", "MEASURED", "provenance"), ("sample_rate_hz", 2e9, "sample rate"),
    ("record_length", 8192, "record length"), ("temperature_c", 40, "temperature"),
    ("volts_per_div", .001, "settings"), ("channel", "CH2", "settings"),
    ("aliasing_review", {"verified": False}, "aliasing_review"),
    ("noise_review", {"verified": None}, "noise_review"),
])
def test_wrong_connection_or_setting_refused(key, value, error):
    f, s, cal, t, v, scope = example()
    scope[key] = value
    with pytest.raises(ValueError, match=error):
        scope_tone.quantify(t, v, scope, cal, rfcp.extract(f, s, cal))


@pytest.mark.parametrize("mutation,error", [
    ("adapter_removed", "included_chain_ids"), ("unreviewed_plane", "reference plane"),
    ("unknown_receiver", "Receiver amplitude"), ("unknown_loading", "loading"),
    ("wrong_gain_frequency", "this tone"), ("relative_calibration", "Invalid/null"),
    ("invalid_band", "Invalid/null"), ("unknown_quality", "Invalid/null"),
])
def test_bad_calibration_refused(mutation, error):
    f, s, cal, t, v, scope = example()
    if mutation == "adapter_removed": cal["included_chain_ids"].append("SYN-UNCORRECTED-ADAPTER")
    elif mutation == "unreviewed_plane": cal.pop("output_reference_plane")
    elif mutation == "unknown_receiver": scope["receiver_response"]["verified"] = False
    elif mutation == "unknown_loading": scope["receiver_response"]["loading_verified"] = False
    elif mutation == "wrong_gain_frequency": scope["receiver_response"]["frequency_hz"] = 30e6
    elif mutation == "relative_calibration": cal["current_model"] = {"mode": "relative"}
    elif mutation == "invalid_band": cal["invalid_frequency_bands_hz"] = [[9e6, 11e6]]
    elif mutation == "unknown_quality": cal["quality_review"]["snr"] = None
    with pytest.raises(ValueError, match=error):
        scope_tone.quantify(t, v, scope, cal, rfcp.extract(f, s, cal))


@pytest.mark.parametrize("mutation,error", [
    ("time_ms", "Nyquist"), ("reverse_time", "increasing"), ("jitter", "Uniform"),
    ("nan", "finite"), ("short", "128"), ("few_cycles", "20 tone cycles"),
    ("drift", "residual"),
])
def test_waveform_defects(mutation, error):
    _, _, _, t, v, scope = example()
    if mutation == "time_ms": t *= 1000
    elif mutation == "reverse_time": t = t[::-1]
    elif mutation == "jitter": t[55] += .01e-9
    elif mutation == "nan": v[5] = np.nan
    elif mutation == "short": t, v = t[:100], v[:100]
    elif mutation == "few_cycles": t, v = t[:150], v[:150]
    elif mutation == "drift": v = .002*np.sin(2*np.pi*10.7e6*t)
    with pytest.raises(ValueError, match=error): scope_tone.quantify(t, v, scope)


def test_cli_normalized_input_and_preserved_outputs(tmp_path):
    _, _, _, t, v, scope = example()
    waveform = tmp_path / "wave.csv"
    np.savetxt(waveform, np.column_stack([t, v]), delimiter=",", header="time_s,voltage_v", comments="")
    meta = tmp_path / "wave.json"
    meta.write_text(json.dumps(scope))
    out = tmp_path / "out"
    cmd = [sys.executable, "-m", "analysis.scope_tone", str(waveform), "--metadata", str(meta), "--out", str(out)]
    good = subprocess.run(cmd, capture_output=True, text=True)
    assert good.returncode == 0, good.stderr
    assert json.loads(good.stdout)["current_rms_a"] is None
    before = rfcp.sha256(out / "tone_result.json")
    assert subprocess.run(cmd, capture_output=True).returncode == 2
    assert before == rfcp.sha256(out / "tone_result.json")
    waveform.write_text("time_ms,voltage_mV\n0,1\n")
    with pytest.raises(ValueError, match="Normalize"): scope_tone.read_waveform(waveform)


def test_synthetic_output_cannot_enter_measurements():
    # export() uses this path check; validated numerical data reaches the guard.
    from unittest.mock import patch
    _, _, _, t, v, scope = example()
    with patch.object(scope_tone, "read_waveform", return_value=(t, v)), \
         patch.object(scope_tone.Path, "read_text", return_value=json.dumps(scope)), \
         pytest.raises(ValueError, match="reserved"):
        scope_tone.export("unused.csv", "unused.json", rfcp.ROOT / "measurements/processed/SHOULD_NOT_EXIST")
