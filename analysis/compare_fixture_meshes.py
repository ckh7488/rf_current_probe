"""Compare preserved completed-run outputs without claiming full convergence."""
from pathlib import Path
import cmath
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reviews/fixture_em_20260921'
NAMES = ['taper_resolved_025', 'taper_resolved_020']
results = [json.loads((OUT / n / 'results.json').read_text()) for n in NAMES]
assert results[0]['model']['source_board_sha256'] == results[1]['model']['source_board_sha256']
assert results[0]['model']['script_sha256'] == results[1]['model']['script_sha256']
assert [r['f_Hz'] for r in results[0]['rows']] == [r['f_Hz'] for r in results[1]['rows']]

def z(row, key):
    return complex(row[key + '_re'], row[key + '_im'])

rows = []
for a, b in zip(results[0]['rows'], results[1]['rows']):
    hi = z(b, 'HI') / z(a, 'HI')
    s21 = z(b, 'S21') / z(a, 'S21')
    rows.append(dict(f_Hz=a['f_Hz'], s11_abs_delta=abs(z(b, 'S11') - z(a, 'S11')),
                     s21_abs_delta=abs(z(b, 'S21') - z(a, 'S21')),
                     s21_mag_delta_dB=20*math.log10(abs(s21)),
                     s21_phase_delta_deg=math.degrees(cmath.phase(s21)),
                     hi_complex_relative_delta_percent=100*abs(hi-1),
                     hi_mag_delta_percent=100*(abs(hi)-1),
                     hi_phase_delta_deg=math.degrees(cmath.phase(hi))))

bands = []
for upper in [100e6, 300e6, 500e6]:
    selected = [r for r in rows if r['f_Hz'] <= upper]
    maxima = {k: max(abs(r[k]) for r in selected) for k in selected[0] if k != 'f_Hz'}
    bands.append(dict(band_MHz=[1, upper/1e6], sampled_frequencies=len(selected), maxima=maxima))

evidence = []
for n in NAMES:
    d = OUT/n
    sanity = json.loads((d/'sanity_summary.json').read_text())
    pec = json.loads((d/'pec_connectivity.json').read_text())
    assert sanity['basic_checks_pass']
    assert pec['connections'] == dict(signal_thru=True, return_thru=True, input_short=False,
                                      output_short=False, centre_signal=True)
    windows = json.loads((d/'snapshot_02/window_stability.json').read_text())
    evidence.append(dict(run=n, termination=sanity['termination'], basic_checks=sanity['basic_checks'],
                         connectivity=pec['connections'], last_common_ns=windows['last_common_ns'],
                         window_end_ns=[w['end_ns'] for w in windows['windows']],
                         window_changes=windows['changes'],
                         results_sha256=hashlib.sha256((d/'results.json').read_bytes()).hexdigest()))

output = dict(classification='SIMULATED_TWO_LOCAL_MESHES_NOT_CONVERGENCE_OR_CALIBRATION_APPROVAL',
              source_board_sha256=results[0]['model']['source_board_sha256'],
              source_script_sha256=results[0]['model']['script_sha256'],
              evidence=evidence, bands=bands, rows=rows,
              limits=['Only local XY gap/taper mesh changes from 0.25 to 0.20 mm; bulk, Z and domain unchanged.',
                      'Neither run reached its original -50 dB global energy end criterion.',
                      'Time-window and mesh differences are empirical diagnostics, not absolute error bounds.',
                      'No core/winding, real connector reference, material sensitivity or reverse excitation validation.'])
(OUT/'mesh_comparison.json').write_text(json.dumps(output, indent=2), encoding='utf-8')

text = '# 두 국소 격자 비교 · SIMULATED\n\n'
text += '0.25 mm와0.20 mm는 SMA 주변과 신호 테이퍼의 국소 XY 격자입니다. '
text += '전체 격자/경계/재료 수렴을 완료했다는 뜻이 아닙니다. 두 실행 모두 전역 에너지 −50 dB 조건 미달입니다.\n\n'
text += '| 표본 대역 | S11 복소 절대차 최대 | S21 크기 차 최대 | 중앙 전류 복소 상대차 최대 | 중앙 전류 위상 차 최대 |\n|---|---:|---:|---:|---:|\n'
for b in bands:
    m=b['maxima']
    text += f"| 1–{b['band_MHz'][1]:g} MHz | {m['s11_abs_delta']:.5f} | {m['s21_mag_delta_dB']:.4f} dB | {m['hi_complex_relative_delta_percent']:.3f}% | {m['hi_phase_delta_deg']:.3f}° |\n"
text += '\n## 細格자(0.20 mm)의 무코어 지그 결과\n\n'.replace('細格자', '더 촘촘한 격자')
text += '| MHz | S11 | 지그 S21 | 중앙 전류 크기/이상적50Ω 전류 | 전류 위상 |\n|---|---:|---:|---:|---:|\n'
for r in results[1]['rows']:
    if r['f_Hz'] in [1e6,10e6,30e6,100e6,300e6,500e6]:
        text += f"| {r['f_Hz']/1e6:g} | {r['S11_dB']:.2f} dB | {r['S21_dB']:.3f} dB | {r['I_over_matched_mag']:.4f} | {r['I_over_matched_phase_deg']:.2f}° |\n"
text += '\n## 종료·시간창 확인\n\n'
for e in evidence:
    last=e['window_changes'][-1]
    windows='/'.join(f'{v:g}' for v in e['window_end_ns'])
    text += f"- `{e['run']}`: {e['termination']['kind']}; {windows} ns 시간창 비교. 마지막 창 확장의 전류 복소 상대차 최대 {100*last['hi_relative_max']:.5f}%, S21 복소 절대차 {last['s21_abs_max']:.7f}.\n"
text += '\n전류비는 모델 내부 급전에서 정의한 입사전압/50Ω에 대한 값입니다. '
text += 'S21은 지그 양끝의 전달이며 프로브 출력 S21이 아닙니다. 원시 파형과 실제 후처리 코드·모델은 실행 폴더에 보존했습니다.\n'
(OUT/'MESH_COMPARISON.md').write_text(text, encoding='utf-8')
print(json.dumps({'bands':bands,'evidence':evidence}, indent=2))
