"""Analytic end-to-end examples. No sensor/fixture/instrument measurement."""
import math
import numpy as np
from tests.test_rfcp import metadata

RECEIVER_SETTINGS = ["receiver_id", "receiver_model", "channel", "input_ohm", "coupling", "bandwidth_setting",
                     "probe_factor", "volts_per_div", "channel_offset_v", "sample_rate_hz", "acquisition_mode",
                     "head_id", "head_revision", "included_chain_ids", "input_reference_plane_id"]


def example(frequency_hz=10e6):
    f = np.array([1e6, 10e6, 30e6, 100e6])
    s = np.zeros((len(f), 2, 2), complex)
    # Ideal 5 ohm sensor followed by an ideal matched 10 dB attenuator.
    chain_zt = 5 / math.sqrt(10)
    s[:, 1, 0] = chain_zt / 50
    cal = metadata(f=f)
    cal.update(head_id="SYN-HEAD", head_revision="SYN-5T", calibration_id="SYN-BNC-CAL",
               included_chain_ids=["SYN-ATT10", "SYN-CAB01"],
               output_reference_plane={"id": "SYN-CAB01-BNC", "verified": True, "impedance_ohm": 50,
                                       "evidence": "SYNTHETIC ideal BNC reference plane; no real calibration"})
    scope = dict(schema_version=1, data_kind="SYNTHETIC", measurement_id="SYN-CW-001",
                 receiver_id="SYN-SCOPE-01", receiver_model="SYN-IDEAL", channel="CH1",
                 head_id=cal["head_id"], head_revision=cal["head_revision"], calibration_id=cal["calibration_id"],
                 timestamp="2026-09-16T00:00:00+09:00", normalization_evidence="SYNTHETIC direct SI serializer",
                 setup_evidence="SYNTHETIC settings; not read from an instrument", voltage_convention="displayed_volts_probe_1x",
                 probe_factor=1, input_ohm=50, external_50ohm_termination=False, coupling="DC", bandwidth_setting="FULL",
                 acquisition_mode="sample", clipped=False, overload=False, source_mode="CW", stationarity_verified=True,
                 aliasing_review={"verified": True, "evidence": f"SYNTHETIC analytic spectrum <= {3*frequency_hz:g} Hz"},
                 noise_review={"verified": True, "evidence": "SYNTHETIC noiseless arithmetic"}, sample_rate_hz=1e9,
                 volts_per_div=.005, channel_offset_v=0, temperature_c=25, frequency_hz=frequency_hz,
                 record_length=max(4096, math.ceil(30e9/frequency_hz)),
                 included_chain_ids=cal["included_chain_ids"].copy(), additional_correction_ids=[], external_gain_applied=False,
                 input_reference_plane_id="SYN-CAB01-BNC", fit_harmonics=3)
    scope["receiver_response"] = dict(verified=True, loading_verified=True, evidence="SYNTHETIC gain 0.9; perfect 50 ohm",
                                      settings={key: scope[key] for key in RECEIVER_SETTINGS}, frequency_hz=frequency_hz,
                                      gain_definition="displayed_V_per_calibrated_50ohm_V", gain=.9,
                                      temperature_range_c=[20, 30])
    t = np.arange(scope["record_length"]) / scope["sample_rate_hz"]
    fundamental_vrms = .001 * chain_zt * .9
    # Noncoherent record, 40% third harmonic and a DC offset: total RMS is wrong
    # for fundamental current. All amplitudes are synthetic, not expected levels.
    v = math.sqrt(2) * fundamental_vrms * (np.sin(2*np.pi*frequency_hz*t+.3) + .4*np.sin(2*np.pi*3*frequency_hz*t-.2)) + .0007
    return f, s, cal, t, v, scope
