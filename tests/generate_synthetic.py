"""Rebuild deterministic test inputs; never write to measurements/."""
import json
from pathlib import Path
import numpy as np
from analysis.fixture_model import synthetic_fixture

folder = Path(__file__).resolve().parent / 'synthetic'
folder.mkdir(exist_ok=True)
f = np.geomspace(1e5, 5e8, 301)
s, hi = synthetic_fixture(f)
base = {
    'schema_version': 1, 'measurement_id': 'SYN-FIXTURE-001', 'head_id': 'SYN-IDEAL-5OHM',
    'head_revision': 'SYNTHETIC', 'core_part': 'NONE-ANALYTIC', 'turns': 5,
    'shield_revision': 'NONE', 'fixture_id': 'SYN-L30nH-C3pF-R52', 'calibration_id': 'SYN-CAL-001',
    'cable_ids': [], 'receiver_model': 'IDEAL-50OHM', 'termination': 'receiver_single_50_ohm',
    'attenuation_profile': 'NONE', 'source_level': 'NORMALIZED-POWER-WAVES',
    'frequency_range': [float(f[0]), float(f[-1])], 'if_bandwidth': 'NOT_APPLICABLE_SYNTHETIC',
    'averaging': 'NOT_APPLICABLE_SYNTHETIC', 'temperature': 'NOT_APPLICABLE_SYNTHETIC',
    'conductor_position': 'ANALYTIC-BRANCH', 'timestamp': '2026-09-16T00:00:00+09:00',
    'data_kind': 'SYNTHETIC', 'clipped': False, 'phase_validated': True,
    'phase_evidence': 'analysis/fixture_model.py: exact analytic reference; not hardware',
    'uncertainty_db': None, 'minimum_zt_ohm': 1e-6, 'included_chain_ids': ['SYN-IDEAL-RECEIVER'],
    'additional_correction_ids': [], 'valid_frequency_bands_hz': [[1e5, 5e8]],
    'invalid_frequency_bands_hz': [],
    'quality_review': {'snr': True, 'linearity': True, 'repeatability': True, 'leakage': True, 'position': True,
                       'evidence': 'Exact SYNTHETIC data by construction; no real quality assessment'},
    'current_model': {'mode': 'hi_model', 'hi_reference_verified': True,
                      'evidence': 'analysis/fixture_model.py analytic KCL model, not a real fixture',
                      'frequency_hz': f.tolist(), 'hi_real_a_per_sqrt_w': hi.real.tolist(),
                      'hi_imag_a_per_sqrt_w': hi.imag.tolist()},
    'synthetic_parameters': {'series_l_h': 30e-9, 'bypass_c_f': 3e-12, 'branch_r_ohm': 52, 'zt_ohm': 5},
    'limitations': 'S12/S22 placeholders. This is not a full reciprocal or fitted RF sensor simulation.'
}
lines = ['! SYNTHETIC: lumped math counterexample, not physical probe performance', '# Hz S RI R 50']
for freq, smat in zip(f, s):
    vals = [smat[0, 0], smat[1, 0], smat[0, 1], smat[1, 1]]
    lines.append(f'{freq:.17g} ' + ' '.join(f'{z.real:.17g} {z.imag:.17g}' for z in vals))
(folder / 'bypass_fixture.s2p').write_text('\n'.join(lines)+'\n', encoding='utf-8')
(folder / 'bypass_fixture.json').write_text(json.dumps(base, indent=2)+'\n', encoding='utf-8')
for mode in ['relative', 'input_current']:
    sample = dict(base)
    sample['current_model'] = {'mode': mode}
    if mode == 'input_current':
        # This intentionally invalid declaration must be rejected by the extractor.
        sample['current_model'].update(evidence='Synthetic bypass branch explicitly violates no-bypass condition',
                                        same_current_plane_verified=True, no_bypass_current_verified=False)
    (folder / f'{mode}.json').write_text(json.dumps(sample, indent=2)+'\n', encoding='utf-8')
naive = 50 * s[:, 1, 0] / (1 - s[:, 0, 0])
report = {'data_kind': 'SYNTHETIC', 'parameters': base['synthetic_parameters'],
          'selected_points': [{'frequency_hz': float(f[i]), 'input_s11_db': float(20*np.log10(abs(s[i,0,0]))),
                               'naive_magnitude_error_db': float(20*np.log10(abs(naive[i])/5)),
                               'naive_phase_error_deg': float(np.angle(naive[i], deg=True))}
                              for i in [0, int(np.argmin(abs(f-1e8))), int(np.argmin(abs(f-3e8))), len(f)-1]]}
(folder / 'expected_calculated.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report))
