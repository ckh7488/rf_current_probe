"""Align report defaults with the new PCB assembly procedure, without changing it."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REPORT=Path('C:/Users/artzy/Documents/ChatGPT/test_board/showcase/reports/rf-current-probe')
paths=[REPORT/'index.html',REPORT/'report.js',REPORT/'records/bench-checklist.md',ROOT/'docs/ATLAS_CURRENT_PROBE_DRAFT.md']
replacements={
 'fixture_through_empty.s2p':'fixture_empty.s2p',
 'fixture_through_head_loaded.s2p':'fixture_probe_loaded.s2p',
 'probe_transfer_5t_Lm30':'probe_transfer_01',
 'repeat_01.s2p … repeat_05.s2p':'probe_transfer_02.s2p … 05.s2p',
 '1~100 MHz, 1601점, linear':'1~100 MHz, 401점, linear',
 '−30 dBm / 1 kHz / 4 sweeps':'−20 dBm / 1 kHz / 실제 평균값 기록',
 '1~100 MHz / 1601점 linear / −30 dBm / IF BW 1 kHz / 평균 4':'1~100 MHz / 401점 linear / −20 dBm / IF BW 1 kHz / 실제 평균값 기록',
 '첫 레벨은 절차의 −30 dBm 설정안을 장비 지원·정격 확인 후 적용':'첫 레벨은 새 PCB 절차의 −20 dBm 설정안을 장비 지원·정격 확인 후 적용',
 '새 PCB 교정지그 A0.1: 새 구조 초안. 이 페이지의 도식·교정 절차는 RF 성능 확인 전입니다.':'새 PCB 교정지그 A0.1: 회로·PCB·조립 CAD와 저장된 ERC/DRC·공칭 검사 기록. 실물 제작·RF 성능은 확인 전입니다.'
}
for p in paths:
 text=p.read_text(encoding='utf-8')
 for old,new in replacements.items():text=text.replace(old,new)
 text=text.replace('평균값 기록회','평균값 기록')
 p.write_text(text,encoding='utf-8')
print('Aligned PCB procedure settings and raw file names.')
