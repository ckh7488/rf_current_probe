"""One shared statement of release status for all current documents."""
from pathlib import Path
import json,html
DATA=json.loads((Path(__file__).resolve().parent/'set_sources/readiness.json').read_text(encoding='utf-8'))
def banner():
 return '<div id="readiness-banner" class="notice" style="margin:16px 24px"><b>'+DATA['overall']+'</b> '+DATA['summary']+' <a href="bom.html#readiness">완료·진행 항목 보기 →</a></div>'
def table():
 rows=[]
 for g in DATA['gates']:
  rows.append('<tr id="'+g['id']+'"><td><b>'+g['name']+'</b><small style="display:block">'+g['phase']+'</small></td><td>'+g['status']+'</td><td>'+g['finding']+'</td><td>'+g['next']+' <a href="'+g['link']+'">관련 문서 →</a></td></tr>')
 return '<section class="sheet" id="readiness"><h2>제작·사용 준비 상태 · 전체 대조</h2><p><b>현행 시제품 원본은 Head A04·A14/C07이며 교정지그는 Fixture A03입니다.</b> 교정은 출구 전류 기준(DEC-053)으로1–500 MHz까지 수행하고 주파수별 오차를 기록합니다. 아래에서 실물 전 설계 검토와 입고 뒤 시험을 구분합니다.</p><div class="tablewrap"><table><thead><tr><th>항목 · 확인 시점</th><th>현재 상태</th><th>근거</th><th>해결 조건</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div><p>현재 기준: A14/C07 · Head A04. BOM 58행과 조립 45단계를 같은 리비전으로 대조합니다. 공개 페이지에는 내부 구매 파일이나 기각된 지그 Gerber를 포함하지 않습니다.</p></section>'
def purchase_state(r):
 i=r['id']
 if r['group']=='3D 출력':return '파일 승인 · 미결제'
 if i=='E01':return '판매 단위 확인 전'
 if i=='E02':return 'JLC Y21 Approved · 결제 대기'
 if i=='E03':return 'Fixture A03 · JLC Y22 Approved · 결제 대기'
 if i in ['F01','F02']:return 'M2×12 구성 확정 · 소량 조달 전'
 if r['group']=='체결·구동':return '소량 견적·사내 재고 대조 전'
 if i=='R08':return '대상 하네스 해당 없음'
 if i=='E04':return '공차 계산 완료 · 기존 9종 카트 3개 · 실물 삽입 전'
 if i in ['R05','R06']:return '기존 9종 카트 포함'
 if i=='R01':return '보유 1 + 카트에 추가 1'
 if i=='R02':return '구매서 7개 · 기존 카트 밖'
 if i in ['E05','E06']:return '구매서 상품 링크 포함'
 if i=='R03':return '보유 · 모델/개체 확인'
 if i=='T04':return '인두 보유 · 플럭스/팁 추가'
 return '실제 보유·규격 확인 필요'
