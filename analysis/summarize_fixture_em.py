"""Screen basic physical sanity, without promoting a single mesh to calibration."""
from pathlib import Path
import json,math,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--name',default='finite_leads');args=ap.parse_args()
R=Path(__file__).resolve().parents[1];O=R/'reviews/fixture_em_20260921';D=O/args.name
r=json.loads((D/'results.json').read_text());rows=r['rows'];low=rows[0]
checks=dict(low_frequency_transmission=abs(10**(low['S21_dB']/20)-1)<.02,low_frequency_reflection=10**(low['S11_dB']/20)<.03,low_frequency_current=abs(low['I_over_matched_mag']-1)<.02,finite_values=all(math.isfinite(x) for row in rows for x in row.values()),passive_power_screen=max(x['power_fraction'] for x in rows)<1.03)
summary=dict(classification='SIMULATED_SINGLE_MESH_EMPTY_FIXTURE_NOT_CALIBRATION_APPROVAL',basic_checks=checks,basic_checks_pass=all(checks.values()),source_board_sha256=r['model']['source_board_sha256'],source_sha256=r['model']['script_sha256'],parameters=r['model']['parameters'],samples=[x for x in rows if x['f_Hz'] in [1e6,10e6,30e6,100e6,300e6,500e6]],limits=['No mesh/domain/material/connector convergence or reciprocal reverse excitation completed.','Actual loaded core, winding and output cable are absent; this is the empty fixture only.','Lumped port inside an assumed connector is not the actual SMA calibration plane.','Nested Ampere contours include displacement current.','No operating band or fabrication approval follows from passing these basic checks.'])
if (D/'ABORT').exists():
 summary['termination']={'kind':'INTENTIONAL_DIAGNOSTIC_STOP','reason':(D/'ABORT').read_text(encoding='utf-8-sig').strip(),'global_energy_end_criterion_met':False}
 summary['limits'].append('The original -50 dB global-energy criterion was not met. See saved time-window convergence checks; they are limited to port/current observables.')
elif (O/(args.name+'.log')).exists() and 'Max. number of timesteps was reached' in (O/(args.name+'.log')).read_text(errors='replace'):
 summary['termination']={'kind':'MAXIMUM_TIMESTEPS','reason':'The solver exhausted its configured timestep limit. See the preserved run log.','global_energy_end_criterion_met':False}
 summary['limits'].append('The original -50 dB global-energy criterion was not met. Saved time-window stability is evidence only for the sampled port/current observables.')
(D/'sanity_summary.json').write_text(json.dumps(summary,indent=2))
t='# 교정 PCB 전체 경로 계산 · '+args.name+'\n\n**SIMULATED · 단일 격자 · 무코어. 제작·교정 승인 아님.**\n\n'
t+='기본 전류·전력 검산: '+('통과' if summary['basic_checks_pass'] else '**실패 — 사용 금지**')+'\n\n'
if 'termination' in summary:
 t+=('종료: 전달·전류의 시간창 안정성을 확인하고 진단 실행을 수동 종료했습니다. ' if summary['termination']['kind']=='INTENTIONAL_DIAGNOSTIC_STOP' else '종료: 설정한 최대 시간 스텝에 도달했습니다. ')
 t+='전체 필드 에너지 −50 dB 종료 조건은 달성하지 않았습니다. 저장된 시간창 비교는 포트/전류 관측량에 한정됩니다.\n\n'
t+='| 주파수 | S11 dB | S21 dB | 중앙 전류 / 이상적50Ω 전류 | 두 전류 경로 차이 |\n|---|---:|---:|---:|---:|\n'
for x in summary['samples']:t+=f"| {x['f_Hz']/1e6:g} MHz | {x['S11_dB']:.2f} | {x['S21_dB']:.2f} | {x['I_over_matched_mag']:.4f} | {x['nested_current_delta_percent']:.3f}% |\n"
t+='\nS11/S21은 무코어 지그 양끝의 전달·반사이며 프로브 출력 S21이 아니다. 전류비는 이 모델의 급전 기준이며 실제 SMA 기준면 보정이 남는다.\n\n'
t+='중앙 국소 전류를 계산하는 실행 경로를 마련했다. 격자 수렴·포트/재료 민감도·코어 장착 영향·실제 VNA 대조가 남아 있으므로 50×S21 환산을 확정하지 않는다.\n'
(D/'SANITY.md').write_text(t,encoding='utf-8');print(json.dumps(summary,indent=2))
