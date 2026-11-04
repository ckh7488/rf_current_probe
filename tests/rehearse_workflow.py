"""Run a deterministic, explicitly SYNTHETIC connection-to-current rehearsal.

No instruments controlled. Writes a NEW output directory, never measurements/.
"""
import argparse
import copy
import json
from pathlib import Path

import numpy as np
from analysis import rfcp, scope_tone
from analysis.connection_plan import verify_route
from tests.rehearsal_data import example


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.is_relative_to((rfcp.ROOT / "measurements").resolve()) or out.is_relative_to((rfcp.ROOT / "release").resolve()):
        parser.error("Synthetic rehearsal must stay outside measurements/release")
    out.mkdir(parents=True, exist_ok=False)
    p1 = [["VNA.P1", None, "SMA-F"], ["CAB-P1", "SMA-M", "SMA-M"], ["FIXTURE", "SMA-F", "SMA-F"]]
    p2 = [["CAB-P2", "SMA-M", "SMA-M"], ["VNA.P2", "SMA-F", None]]
    head = [["HEAD.OUT", None, "SMA-F"]]
    full = head + [["ATT", "SMA-M", "SMA-F"], ["CAB-01", "SMA-M", "BNC-M"]]
    plans = {
        "through_primary": p1+p2,
        "through_head_terminated": head+[["HEAD-LOAD", "SMA-M", None]],
        "transfer_primary_terminated": p1+[["PRIMARY-LOAD", "SMA-M", None]],
        "transfer_head_to_vna": head+p2,
        "complete_chain_to_vna": full+[["ADAPT-CAL", "BNC-F", "SMA-F"]]+p2,
        "complete_chain_to_scope": full+[["SCOPE.CH1", "BNC-F", None]],
        "sol_female_on_test_cable": p1[:2]+[["SOL-STANDARD", "SMA-F", None]],
        "thru_female_female": p1[:2]+[["THRU", "SMA-F", "SMA-F"]]+p2,
    }
    checks = [{"id": key, "kind": "CALCULATED", "joins": verify_route(route), "pass": True} for key, route in plans.items()]
    old = full+[["OLD-ADAPT", "BNC-F", "SMA-M"]]+p2
    try:
        verify_route(old)
    except ValueError as exc:
        checks.append({"id": "old_adapter_rejected", "pass": True, "reason": str(exc)})
    else:
        raise AssertionError("Old male-to-male adapter arrangement was accepted")
    tone_results = []
    for frequency in [1e6, 10e6, 30e6, 100e6]:
        f, s, cal, t, v, scope = example(frequency)
        result = scope_tone.quantify(t, v, scope, cal, rfcp.extract(f, s, cal))
        assert abs(result["current_rms_a"] - .001) < 1e-12
        tone_results.append(result)
    f, s, cal, t, v, scope = example()
    inp = out / 'inputs'
    inp.mkdir()
    lines = ['! SYNTHETIC ideal 5 ohm sensor + matched 10 dB attenuation. S12/S22 placeholders.', '# Hz S RI R 50']
    for freq, sm in zip(f, s):
        lines.append(f'{freq:.17g} '+' '.join(f'{z.real:.17g} {z.imag:.17g}' for z in [sm[0,0],sm[1,0],sm[0,1],sm[1,1]]))
    (inp/'transfer.s2p').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    for name, value in [('transfer.json', cal), ('scope.json', scope)]:
        (inp/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    np.savetxt(inp/'cw.csv', np.column_stack([t,v]), delimiter=',', header='time_s,voltage_v', comments='')
    rfcp.export(inp/'transfer.s2p', inp/'transfer.json', out/'vna_extraction')
    processed = scope_tone.export(inp/'cw.csv', inp/'scope.json', out/'scope_current', inp/'transfer.s2p', inp/'transfer.json')
    voltage = scope_tone.export(inp/'cw.csv', inp/'scope.json', out/'scope_voltage')
    assert voltage['current_rms_a'] is None
    reject = []
    mutations = {
        'adapter_removed': lambda c, m: c['included_chain_ids'].append('UNCORRECTED-ADAPTER'),
        'wrong_reference_plane': lambda c, m: m.update(input_reference_plane_id='SMA-NOT-BNC'),
        'double_50ohm': lambda c, m: m.update(external_50ohm_termination=True),
        'input_1meg': lambda c, m: m.update(input_ohm=1e6),
        'probe_10x': lambda c, m: m.update(probe_factor=10),
        'sweeping_source': lambda c, m: m.update(source_mode='VNA_SWEEP'),
        'double_attenuation': lambda c, m: m.update(additional_correction_ids=['SYN-ATT10']),
        'unknown_receiver': lambda c, m: m['receiver_response'].update(verified=False),
        'relative_only': lambda c, m: c.update(current_model={'mode':'relative'}),
        'clipped_record': lambda c, m: m.update(clipped=True),
    }
    for name, mutate in mutations.items():
        c, m = copy.deepcopy(cal), copy.deepcopy(scope)
        mutate(c, m)
        try:
            scope_tone.quantify(t, v, m, c, rfcp.extract(f, s, c))
        except ValueError as exc:
            reject.append({'id':name, 'rejected':True, 'reason':str(exc)})
        else:
            raise AssertionError(f'Unsafe/invalid scenario accepted: {name}')
    report = {'data_kind':'SYNTHETIC', 'meaning':'Software/declared connection rehearsal, not measured hardware or RF EM simulation',
              'connection_checks': checks, 'tone_checks':tone_results, 'negative_scenarios':reject,
              'all_expected_outcomes':True, 'expected_fundamental_current_a':.001,
              'wrong_whole_waveform_rms_current_a':processed['total_vrms_displayed']/.9/(5/np.sqrt(10)),
              'code_sha256':{str(p.relative_to(rfcp.ROOT)):rfcp.sha256(p) for p in [Path(__file__), Path(rfcp.__file__), Path(scope_tone.__file__), rfcp.ROOT/'analysis/connection_plan.py', rfcp.ROOT/'tests/rehearsal_data.py']}}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (out/'connection_plan.json').write_text(json.dumps(plans, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'connection_checks':len(checks), 'tone_checks':len(tone_results), 'rejections':len(reject), 'all_expected_outcomes':True,
                      'whole_rms_error_percent':(report['wrong_whole_waveform_rms_current_a']/.001-1)*100}))


if __name__ == '__main__':
    main()
