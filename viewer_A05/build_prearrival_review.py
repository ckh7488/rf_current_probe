"""Include the latest local prearrival review in the offline document set."""
from pathlib import Path
import html,shutil
R=Path(__file__).resolve().parent.parent
def build(D,frame):
 source=R/'reviews/recheck_20260922/README.md'
 text=source.read_text(encoding='utf-8')
 shutil.copyfile(source,D/'files/RFCP_PREARRIVAL_REVIEW.md')
 included={'RFCP_PREARRIVAL_REVIEW.md'}
 body='<section class="intro"><span class="eyebrow">2026.09.22 · CALCULATED / SIMULATED</span><h1>실물 입고 전 재검토</h1><p><a href="files/RFCP_PREARRIVAL_REVIEW.md" download>검토 기록 저장</a> · <a href="bom.html#E02">현행 PCB 파일과 BOM</a></p></section>'
 archive=source.parent/'RFCP_PREARRIVAL_EVIDENCE_20260922.zip'
 if archive.exists():
  shutil.copyfile(archive,D/'files/RFCP_PREARRIVAL_EVIDENCE.zip');included.add('RFCP_PREARRIVAL_EVIDENCE.zip')
  body+='<section class="sheet"><h2>원본과 검증 기록</h2><p><a class="button" href="files/RFCP_PREARRIVAL_EVIDENCE.zip" download>해석·제조 검토 자료 전체 저장</a></p><p>압축을 풀고 reviews/recheck_20260922/README.md부터 확인합니다. 문서의 상대 경로와 원시 출력·해석 설정·제작 원본을 함께 보존했습니다. 요약 Markdown만 저장하면 내부 자료 링크는 열리지 않습니다. 계산·시뮬레이션 자료이며 실측 교정값이나 업체 승인이 아닙니다.</p></section>'
 body+='<section class="sheet"><pre style="white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;line-height:1.8">'+html.escape(text)+'</pre></section>'
 for name,label in [('solid_via_model.png','중실 비아와 실제 FDTD 도체 연결'),('solid_fixture_comparison.png','무코어 지그 응답과 격자 비교 — 실측 아님')]:
  src=source.parent/name
  if src.exists():
   shutil.copyfile(src,D/'files'/name);included.add(name)
   body+='<section class="sheet"><h2>'+html.escape(label)+'</h2><img style="display:block;width:100%;height:auto" src="files/'+name+'" alt="'+html.escape(label,quote=True)+'"></section>'
 (D/'design-review.html').write_text(frame('design-review.html','실물 입고 전 재검토',body),encoding='utf-8')
 return included
