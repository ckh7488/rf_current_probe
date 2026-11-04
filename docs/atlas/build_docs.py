"""Build both ATLAS procedure documents from shared, revisioned local sources.

No CAD/PCB generation, fabrication edits, purchases, or network publication here.
"""
import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
SOURCE = HERE / "source"
DEFAULT_ATLAS = Path(r"C:\Users\artzy\Documents\ChatGPT\test_board\showcase")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", type=Path, default=DEFAULT_ATLAS)
    args = parser.parse_args()
    out = args.atlas / "reports/rf-current-probe"
    design = read_json(SOURCE / "design.json")

    def render(text):
        def value(match):
            result = design
            for key in match[1].split("."):
                result = result[key]
            if isinstance(result, (dict, list)):
                raise ValueError(f"Scalar token required: {match[1]}")
            return str(result)
        result = re.sub(r"\{\{([a-zA-Z0-9_.]+)\}\}", value, text)
        if "{{" in result:
            raise ValueError("Unresolved template token")
        return result

    # Refuse to carry a successful old check forward after a hardware change.
    manifest = read_json(out / "assets" / (design["fixture"]["asset"] + ".json"))
    assert manifest["source_sha256"] == sha(PROJECT / design["fixture"]["cad_source"]), "CAD export is stale"
    assert len(manifest["parts"]) == design["cad"]["expected_parts"]
    assert manifest["triangle_count"] == design["cad"]["expected_triangles"]
    assert manifest["binary_sha256"] == sha(out / "assets" / manifest["binary"])
    verified = read_json(out / "records/a02-design-verification.json")
    assert verified["pcb"]["pcb_sha256"] == sha(PROJECT / design["fixture"]["pcb_file"]), "Repeat PCB review after source changes"
    assert verified["pcb"]["cad_sha256"] == sha(PROJECT / design["fixture"]["cad_file"]), "Repeat mechanical review after source changes"

    pages = {
        "assembly": {
            "title": "조립 절차서", "number": "01",
            "lead": "코어 권선과 헤드 PCB, 집게, 평판 교정지그를 차례로 조립합니다. 실제 설계 형상을 돌려 보고 단계별 완료 조건을 확인하세요.",
            "sections": ["purpose", "structure", "assembly-procedure", "design-review", "change-control"],
            "nav": [("structure", "실제 형상"), ("assembly", "조립 순서"), ("design-review", "설계 비교"), ("changes", "변경 시 확인")],
            "jump": '#assembly', "jump_label": "A01부터 조립 순서 보기 ↓",
        },
        "testing": {
            "title": "점검·교정·측정 절차서", "number": "02",
            "lead": "조립한 프로브와 지그를 무전원 점검한 뒤, VNA 연결을 네 단계로 바꿔 측정합니다. 상대 응답부터 확보하고, 조건을 입증한 범위만 전류로 환산합니다.",
            "sections": ["test-start", "calibration", "quality", "conversion", "scope", "records", "change-control"],
            "nav": [("preflight", "준비"), ("calibration", "연결 순서"), ("quality", "비교 시험"), ("records", "기록")],
            "jump": '#calibration', "jump_label": "실제 형상으로 연결 순서 보기 ↓",
        },
    }
    for key, page in pages.items():
        tabs = ''.join(f'<a href="{design["documents"][name]}"' + (' aria-current="page"' if name == key else '') + f'><small>문서 {item["number"]}</small>{item["title"]}</a>' for name, item in pages.items())
        nav = ''.join(f'<a href="#{anchor}">{label}</a>' for anchor, label in page["nav"])
        sections = '\n'.join((SOURCE / "sections" / f"{s}.html").read_text(encoding="utf-8") for s in page["sections"])
        legacy = ''
        if key == 'assembly':
            legacy = '<script>if(new URLSearchParams(location.search).has("step")||["#calibration","#conversion","#quality","#scope","#records"].includes(location.hash))location.replace("testing.html"+location.search+location.hash);</script>'
        text = f'''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>RF 전류 프로브 · {page["title"]} | ATLAS</title>
<meta name="description" content="{html.escape(page['lead'], quote=True)}">
<link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../../assets/theme.v1.css">
<link rel="stylesheet" href="report.css?v={design['document']['cache']}">
{legacy}
<script src="design-data.js?v={design['document']['cache']}" defer></script>
<script src="vendor/three.min.js" defer></script><script src="vendor/OrbitControls.js" defer></script>
<script src="cad-viewer.js?v={design['document']['cache']}" defer></script><script src="report.js?v={design['document']['cache']}" defer></script>
</head><body data-document="{key}">
<header class="site-header"><a href="../../" aria-label="ATLAS 라이브러리로 돌아가기">← ATLAS</a><nav aria-label="문서 목차">{nav}</nav></header>
<main>
<nav class="document-tabs" aria-label="두 절차서">{tabs}</nav>
<section class="intro" aria-labelledby="page-title">
<p class="eyebrow">하드웨어 · 측정 도구 / 문서 {page['number']} / {design['document']['date']}</p>
<h1 id="page-title">RF 전류 프로브<br><span>{page['title']}</span></h1>
<p class="lead">{page['lead']}</p>
<div class="status-line"><span class="status">설계 검토용 초안</span><span>실물 조립·RF 측정 전 · 문서 v{design['document']['revision']}</span></div>
<p class="baseline">현재 구성 · 지그 <b>{design['fixture']['revision']} / PCB 1장</b> · 헤드 <b>{design['head']['revision']}</b> · 집게 <b>{design['clamp']['revision']}</b> · 권선 <b>{design['head']['turns']}턴</b><br><small>설계 ID <code>{design['document']['design_id']}</code></small></p>
<p class="note">먼저 1–100 MHz에서 재현성을 확인합니다. 100 kHz–300 MHz는 전체 개발 목표, 500 MHz는 특성 확인·확장 목표입니다. 아직 측정 완료 사양이 아닙니다.</p>
<a class="jump" href="{page['jump']}">{page['jump_label']}</a>
</section>
{sections}
<nav class="document-tabs end-tabs" aria-label="다른 절차서로 이동">{tabs}</nav>
</main>
<footer><a href="../../">← ATLAS · Interactive Library</a><span>공통 설계 기준 · 문서 v{design['document']['revision']} · 실측 전</span></footer>
</body></html>
'''
        (out / design['documents'][key]).write_text(render(text), encoding="utf-8")

    for path in (SOURCE / "runtime").iterdir():
        (out / path.name).write_text(render(path.read_text(encoding="utf-8")), encoding="utf-8")
    raw_design = json.dumps(design, ensure_ascii=False, indent=2) + '\n'
    (out / "records/design.json").write_text(raw_design, encoding="utf-8")
    (out / "design-data.js").write_text('"use strict";\nwindow.RFCP_DESIGN = ' + raw_design.rstrip() + ';\n', encoding="utf-8")
    (out / "records/bench-checklist.md").write_text(render((SOURCE / "bench-checklist.md").read_text(encoding="utf-8")), encoding="utf-8")
    shutil.copyfile(PROJECT / "hardware/probe_head_A02/review/pcb_top.png", out / "assets/head-a02-pcb.png")
    shutil.copyfile(PROJECT / "docs/ATLAS_A02_DESIGN_REVIEW.md", out / "records/a02-design-review.md")
    for name in ['source-notes.md', 'README.md']:
        target = out / (('records/' if name == 'source-notes.md' else '') + name)
        target.write_text(render((SOURCE / name).read_text(encoding="utf-8")), encoding="utf-8")
    evidence = {
        "document_date": design['document']['date'], "document_revision": design['document']['revision'],
        "design_id": design['document']['design_id'], "documents": design['documents'],
        "status": "DRAFT: CALCULATED geometry/PCB checks, assembly and test procedures. No measured RF results.",
        "illustrations": "Original CAD tessellation, no geometry reduction. External cables/plugs/load/standards are illustrative envelopes.",
        "cad_export": {k: manifest[k] for k in ['source','source_sha256','binary_sha256','triangle_count','geometry_reduction']},
        "sources": [{"project_relative_path": path, "sha256": sha(PROJECT / path)} for path in design['sources']],
        "authoring": [{"project_relative_path": str(path.relative_to(PROJECT)).replace('\\','/'), "sha256": sha(path)} for path in sorted(SOURCE.rglob('*')) if path.is_file()],
        "independent_design_checks": "a02-design-verification.json",
        "not_performed": ["Physical assembly/fit/strength", "RF characterization/calibration", "EM simulation", "cost quotation/order approval"],
    }
    (out / 'records/evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    catalog = read_json(args.atlas / 'reports.json')
    report = next(r for r in catalog['reports'] if r['id'] == 'rf-current-probe')
    report['title'] = 'RF 전류 프로브 · 조립과 테스트'
    report['summary'] = '평판 PCB 1장 A0.2 기준의 조립 절차서와 점검·교정·측정 절차서. 실제 CAD, 이전 구조 비교, VNA 연결 순서와 설계 변경 시 재확인할 항목을 살펴봅니다.'
    report['date'] = design['document']['date']
    (args.atlas / 'reports.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({"documents": list(design['documents'].values()), "revision": design['document']['revision'], "cad_source_current": True, "pcb_review_current": True, "cad_review_current": True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
