import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest

from analysis import rfcp
from analysis.fixture_model import synthetic_fixture


def metadata(f=(1e6, 10e6, 100e6), mode="matched"):
    result = {key: "SYNTHETIC" for key in rfcp.REQUIRED}
    result.update(schema_version=1, turns=5, data_kind="SYNTHETIC", cable_ids=["SYN-CABLE"],
                  frequency_range=[f[0], f[-1]], termination="receiver_single_50_ohm", clipped=False,
                  phase_validated=False, phase_evidence="tests: analytic reference", uncertainty_db=None,
                  minimum_zt_ohm=1e-6, included_chain_ids=["SYN-CABLE"], additional_correction_ids=[],
                  valid_frequency_bands_hz=[[f[0], f[-1]]], invalid_frequency_bands_hz=[],
                  quality_review={key: True for key in rfcp.QUALITY_CHECKS})
    result["quality_review"]["evidence"] = "SYNTHETIC: exact analytic data, not hardware review"
    result["current_model"] = dict(mode=mode, evidence="SYNTHETIC analytic model", matched_path_verified=True,
                                   current_reference_verified=True, same_current_plane_verified=True,
                                   no_bypass_current_verified=True, hi_reference_verified=True)
    return result


def matched_data():
    f = np.array([1e6, 10e6, 100e6])
    s = np.zeros((3, 2, 2), complex)
    s[:, 1, 0] = 0.1
    return f, s


@pytest.mark.parametrize("unit,mult", [("Hz", 1), ("kHz", 1e3), ("MHz", 1e6), ("GHz", 1e9)])
@pytest.mark.parametrize("fmt", ["RI", "MA", "DB"])
@pytest.mark.parametrize("version,order", [("1.0", "21_12"), ("2.0", "21_12"), ("2.0", "12_21")])
def test_touchstone_units_formats_order(tmp_path, unit, mult, fmt, version, order):
    # Hand-authored serializer in test, independent of the library writer.
    vals = [0.2 + 0.1j, 0.1 - 0.05j, 0.04 + 0.03j, -0.1 + 0.02j]
    ordered = vals if order == "21_12" else [vals[0], vals[2], vals[1], vals[3]]
    def pair(z):
        a, b = (z.real, z.imag) if fmt == "RI" else (abs(z) if fmt == "MA" else 20 * math.log10(abs(z)), np.angle(z, deg=True))
        return f"{a:.16g} {b:.16g}"
    header = f"# {unit} S {fmt} R 50\n"
    if version == "2.0":
        header = f"[Version] 2.0\n{header}[Number of Ports] 2\n[Number of Frequencies] 2\n[Reference] 50 50\n[Two-Port Data Order] {order}\n[Matrix Format] Full\n[Network Data]\n"
    data = "\n".join(f"{freq / mult:.16g} " + " ".join(pair(v) for v in ordered) + " ! inline comment" for freq in [1e6, 2e6])
    path = tmp_path / "sample.s2p"
    path.write_text("! SYNTHETIC\n" + header + data + ("\n[End]\n" if version == "2.0" else "\n"))
    f, s = rfcp.read_s2p(path)
    np.testing.assert_allclose(f, [1e6, 2e6])
    np.testing.assert_allclose(s[0], [[vals[0], vals[2]], [vals[1], vals[3]]])


@pytest.mark.parametrize("content", [
    "# Hz S RI R 75\n100 0 0 .1 0 0 0 0 0\n200 0 0 .1 0 0 0 0 0\n",
    "[Version] 2.0\n# Hz S RI R 50\n[Number of Ports] 2\n[Number of Frequencies] 2\n[Reference] 50 75\n[Network Data]\n100 0 0 .1 0 0 0 0 0\n200 0 0 .1 0 0 0 0 0\n[End]",
    "[Version] 2.1\n# Hz S RI R 50\n",
    "# Hz Z RI R 50\n",
    "# Hz S RI R 50\n100 0 0 .1 0 0 0 0 0\n100 0 0 .1 0 0 0 0 0\n",
    "# Hz S RI R 50\n100 0 0 .1 0 0 0 0 0\n200 0 0 nan 0 0 0 0 0\n",
    "[Version] 2.0\n# Hz S RI R 50\n[Mixed-Mode Order] D1,2 C1,2\n",
    "# Hz S RI R 50\n# Hz S RI R 50\n",
    "# Hz S RI R 50\n[Two-Port Data Order] bad\n",
])
def test_unsupported_or_invalid_touchstone_rejected(tmp_path, content):
    path = tmp_path / "bad.s2p"
    path.write_text(content)
    with pytest.raises(ValueError): rfcp.read_s2p(path)


def test_matched_whitepaper_and_units():
    f, s = matched_data()
    rows = rfcp.extract(f, s, metadata())
    assert rows[0]["zt_magnitude_ohm"] == pytest.approx(5)
    assert rows[0]["zt_db_ohm"] == pytest.approx(13.9794000867)
    assert rows[0]["zt_real_ohm"] is None and rows[0]["phase_deg"] is None
    assert rows[0]["uncertainty_db"] is None and "UNASSESSED" in rows[0]["quality_flag"]
    assert rfcp.tone_current_rms(1e6, .005, rows, metadata(), ["SYN-CABLE"]) == pytest.approx(.001)
    assert rfcp.dbm_to_vrms(-20) == pytest.approx(.022360679775)
    assert rfcp.dbm_to_vrms(-20) / (rfcp.dbm_to_vrms(0) / 50) == pytest.approx(5)
    assert rfcp.db_micro(.005) - rfcp.db_micro(.001) == pytest.approx(20 * math.log10(5))
    assert rfcp.sine_rms(math.sqrt(2), "peak", waveform="sine") == pytest.approx(1)
    assert rfcp.sine_rms(2 * math.sqrt(2), "peak_to_peak", waveform="sine") == pytest.approx(1)
    with pytest.raises(ValueError): rfcp.sine_rms(1, "peak", waveform="pulse")


def test_mismatch_at_valid_current_plane():
    f, s = matched_data()
    gamma = .3 + .1j
    true_zt = 5 * np.exp(0.4j)
    s[:, 0, 0] = gamma
    s[:, 1, 0] = true_zt * (1 - gamma) / 50
    m = metadata(mode="input_current")
    m["phase_validated"] = True
    rows = rfcp.extract(f, s, m)
    assert rows[0]["zt_real_ohm"] + 1j * rows[0]["zt_imag_ohm"] == pytest.approx(true_zt)
    m["current_model"]["no_bypass_current_verified"] = False
    with pytest.raises(ValueError): rfcp.extract(f, s, m)


def test_bypass_counterexample_and_hi_correction():
    f = np.array([1e6, 100e6, 300e6])
    s, hi = synthetic_fixture(f)
    naive = 50 * s[:, 1, 0] / (1 - s[:, 0, 0])
    assert abs(naive[-1] / 5 - 1) > .2  # Same input S11 does not establish core current.
    m = metadata(f, mode="hi_model")
    m["current_model"].update(frequency_hz=f.tolist(), hi_real_a_per_sqrt_w=hi.real.tolist(), hi_imag_a_per_sqrt_w=hi.imag.tolist())
    rows = rfcp.extract(f, s, m)
    np.testing.assert_allclose([r["zt_magnitude_ohm"] for r in rows], 5)
    m["current_model"]["frequency_hz"] = [2e6, 100e6, 300e6]
    with pytest.raises(ValueError): rfcp.extract(f, s, m)


def test_matched_line_phase_requires_reference_evidence():
    f, s = matched_data()
    s[:, 1, 0] *= np.exp(-2j * np.pi * f * 1e-9)
    rows = rfcp.extract(f, s, metadata())
    assert rows[-1]["phase_deg"] is None
    assert rows[-1]["zt_magnitude_ohm"] == pytest.approx(5)
    m = metadata(); m["phase_validated"] = True; m.pop("phase_evidence")
    with pytest.raises(ValueError): rfcp.extract(f, s, m)


def test_relative_has_no_absolute_current_result():
    f, s = matched_data()
    m = metadata(mode="relative")
    rows = rfcp.extract(f, s, m)
    assert all(r["zt_magnitude_ohm"] is None and not r["valid"] for r in rows)
    assert rows[0]["s21_db"] == pytest.approx(-20)
    with pytest.raises(ValueError): rfcp.tone_current_rms(1e6, .005, rows, m, ["SYN-CABLE"])


@pytest.mark.parametrize("change", [
    {"clipped": True}, {"valid_frequency_bands_hz": []},
    {"quality_review": {}}, {"minimum_zt_ohm": 6},
])
def test_invalid_data_not_quantified(change):
    f, s = matched_data(); m = metadata(); m.update(change)
    rows = rfcp.extract(f, s, m)
    assert not any(r["valid"] for r in rows)
    with pytest.raises(ValueError): rfcp.tone_current_rms(1e6, .005, rows, m, ["SYN-CABLE"])
    if m["clipped"]: assert all(r["zt_magnitude_ohm"] is None for r in rows)


def test_gap_extrapolation_null_and_chain_rejected():
    f, s = matched_data(); m = metadata()
    rows = rfcp.extract(f, s, m)
    for freq in [1e5, 101e6]:
        with pytest.raises(ValueError): rfcp.tone_current_rms(freq, .005, rows, m, ["SYN-CABLE"])
    with pytest.raises(ValueError): rfcp.tone_current_rms(1e6, .005, rows, m, ["WRONG"])
    with pytest.raises(ValueError): rfcp.tone_current_rms(1e6, .005, rows, m, ["SYN-CABLE"], clipped=True)
    m["invalid_frequency_bands_hz"] = [[20e6, 30e6]]
    with pytest.raises(ValueError): rfcp.tone_current_rms(50e6, .005, rows, m, ["SYN-CABLE"])
    m["invalid_frequency_bands_hz"] = []
    m["valid_frequency_bands_hz"] = [[1e6, 10e6], [100e6, 100e6]]
    with pytest.raises(ValueError): rfcp.tone_current_rms(50e6, .005, rows, m, ["SYN-CABLE"])
    s[1, 1, 0] = 0
    rows = rfcp.extract(f, s, metadata())
    assert not rows[1]["valid"]
    with pytest.raises(ValueError): rfcp.tone_current_rms(5e6, .005, rows, metadata(), ["SYN-CABLE"])


@pytest.mark.parametrize("corrections", [["SYN-CABLE"], ["EXTRA"], ["EXTRA", "EXTRA"]])
def test_chain_correction_rejected(corrections):
    f, s = matched_data(); m = metadata(); m["additional_correction_ids"] = corrections
    with pytest.raises(ValueError): rfcp.extract(f, s, m)


@pytest.mark.parametrize("change", [{"head_id": None}, {"data_kind": "CALCULATED"}, {"turns": 0}, {"uncertainty_db": 0}, {"frequency_range": [0, 1]}, {"phase_validated": "false"}])
def test_metadata_rejected(change):
    f, s = matched_data(); m = metadata(); m.update(change)
    with pytest.raises(ValueError): rfcp.extract(f, s, m)


def test_hi_null_no_division():
    f, s = matched_data(); m = metadata(mode="input_current"); s[0, 0, 0] = 1
    rows = rfcp.extract(f, s, m)
    assert not rows[0]["valid"] and "CURRENT_MODEL_NULL" in rows[0]["quality_flag"]


def test_export_preserves_input_and_labels(tmp_path):
    p = tmp_path / "input.s2p"
    p.write_text("! SYNTHETIC\n# MHz S RI R 50\n1 0 0 .1 0 0 0 0 0\n10 0 0 .1 0 0 0 0 0\n100 0 0 .1 0 0 0 0 0\n")
    meta_path = tmp_path / "meta.json"; meta_path.write_text(json.dumps(metadata()))
    original_hash = rfcp.sha256(p)
    out = tmp_path / "new"
    manifest = rfcp.export(p, meta_path, out)
    assert manifest["eligible_rows"] == 3 and manifest["metadata"]["data_kind"] == "SYNTHETIC"
    assert rfcp.sha256(p) == original_hash
    assert (out / "response.png").stat().st_size > 1000
    assert "UNASSESSED|MAGNITUDE_ONLY" in (out / "zt.csv").read_text()
    with pytest.raises(FileExistsError): rfcp.export(p, meta_path, out)
    for forbidden in ["measurements/raw/should_not_exist", "measurements/processed/synthetic_rejected", "release/should_not_exist"]:
        with pytest.raises(ValueError): rfcp.export(p, meta_path, rfcp.ROOT / forbidden)
    mislabeled = metadata(); mislabeled["data_kind"] = "MEASURED"
    meta_path.write_text(json.dumps(mislabeled))
    with pytest.raises(ValueError, match="SYNTHETIC"):
        rfcp.export(p, meta_path, tmp_path / "mislabeled")
