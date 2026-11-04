"""Local ATLAS export. Does not commit, push, deploy or change other reports."""
from pathlib import Path
import json, re, shutil, tempfile, zipfile
from build_showcase import sync_generated_tree, file_hash, BUNDLE
from verify_showcase import verify
P=Path(__file__).resolve().parent;R=P.parent;D=P/'dist'
A=Path('C:/Users/artzy/Documents/ChatGPT/test_board/showcase')
O=A/'reports/rf-current-probe'
STYLE_VERSION='20260923-a03-500-1'
CSS='''
:root{font-family:var(--sc-font);color:var(--sc-ink);background:var(--sc-page)}
body{color:var(--sc-ink);background:var(--sc-page)}
header,header.set-header{background:var(--sc-surface)!important;color:var(--sc-ink)!important;border-bottom:1px solid var(--sc-line);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;padding:16px 24px}
header a,header .set-brand,header .set-brand span,header .brand,header .set-nav a{color:var(--sc-ink)!important}
header nav,header .set-nav{display:flex;flex-wrap:wrap;gap:16px;padding:0!important;margin:0!important;font-size:14px}
header nav a,header .set-nav a{background:transparent!important;box-shadow:none!important;border:0!important;padding:5px 0!important}
header nav a.active,header .set-nav a.active{color:var(--sc-accent)!important;text-decoration:underline;text-underline-offset:6px}
.set-brand{font-size:22px;font-weight:800}.set-brand span{font-size:14px;font-weight:500;margin-left:14px}
.atlas-brand{display:flex;align-items:center;gap:18px;flex-wrap:wrap}.atlas-back{font-size:14px;white-space:nowrap}
a{color:var(--sc-accent)}.workspace,.sheet,.card,.step-bom,.panel,.stats>div,.table-wrap{background:var(--sc-surface);border-color:var(--sc-line)}
.intro,.instruction-block,.proof{border-color:var(--sc-line)}.toc{border-color:var(--sc-line)}
.button.primary,nav button[aria-pressed=true],button[aria-pressed=true]{background:var(--sc-accent);border-color:var(--sc-accent);color:var(--sc-surface)}
.card:hover{border-color:var(--sc-accent)}.card,.card h2,h1,h2{color:var(--sc-ink)}
.card .open,.eyebrow,.step-button[aria-current=step]{color:var(--sc-accent)}
.subtle,.lead,.card p,footer,.scope-note{color:var(--sc-muted)}
details>summary{cursor:pointer}details[open]>summary{margin-bottom:10px}details.proof{border-left:0;background:transparent}details.proof summary{font-weight:650}
.readmore{gap:8px 12px}.tablewrap{max-width:100%;overflow:auto}.split>article{min-width:0}
@media(max-width:580px){header,header.set-header{padding:14px 16px!important}.set-brand span{display:block;margin-left:0!important}.atlas-brand{gap:8px 16px}.set-nav{gap:8px 14px!important}.toolbar button{padding:7px 10px}}
'''

def adapt(text,name):
    text=re.sub(r'<title>(.*?)</title>',lambda m:'<title>'+m[1]+' | ATLAS</title>',text,count=1)
    text=text.replace('</head>',f'<link rel="stylesheet" href="../../assets/theme.v1.css"><link rel="icon" href="../../assets/favicon.svg"><link rel="stylesheet" href="document-set.css?v={STYLE_VERSION}"></head>',1)
    return re.sub(r'(<header\b[^>]*>)(<a .*?</a>)',lambda m:m[1]+'<div class="atlas-brand"><a class="atlas-back" href="../../" aria-label="ATLAS 라이브러리로 돌아가기">← ATLAS</a>'+m[2]+'</div>',text,count=1,flags=re.S)

def publish(repository=None):
    global A,O
    if repository is not None:
        A=Path(repository).resolve();O=A/'reports/rf-current-probe'
    manifest=json.loads((P/'set_sources/showcase_manifest.json').read_text(encoding='utf-8'))
    assert manifest['profile']=='PUBLIC_SHOWCASE_ALLOWLIST'
    actual={f.relative_to(D).as_posix() for f in D.rglob('*') if f.is_file()}
    assert actual==set(manifest['files']), 'Rebuild the showcase; dist contains unexpected files'
    for rel,digest in manifest['files'].items():assert file_hash(D/rel)==digest,rel
    verify(D)
    theme=(A/'assets/theme.v1.css').read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='.rfcp-atlas-',dir=A) as tmp:
        out=Path(tmp);assert out.resolve().parent==A.resolve()
        for rel in sorted(actual-{BUNDLE}):
            target=out/rel;target.parent.mkdir(parents=True,exist_ok=True)
            if rel.endswith('.html'):target.write_text(adapt((D/rel).read_text(encoding='utf-8'),rel),encoding='utf-8')
            else:shutil.copyfile(D/rel,target)
        (out/'document-set.css').write_text(CSS,encoding='utf-8')
        with zipfile.ZipFile(out/BUNDLE,'w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out.rglob('*')):
                if not f.is_file() or f.name==BUNDLE:continue
                rel=f.relative_to(out).as_posix()
                if f.suffix=='.html':
                    text=f.read_text(encoding='utf-8').replace('<link rel="stylesheet" href="../../assets/theme.v1.css">','<style>'+theme+'</style>')
                    text=text.replace(f'<link rel="stylesheet" href="document-set.css?v={STYLE_VERSION}">','<style>'+CSS+'</style>')
                    text=text.replace('<link rel="icon" href="../../assets/favicon.svg">','')
                    text=text.replace('href="../../"','href="https://ckh7488.github.io/showcase/"')
                    text=re.sub(r'<a\b[^>]*href="'+BUNDLE+r'"[^>]*>.*?</a>','<span>오프라인 문서 세트</span>',text,flags=re.S)
                    z.writestr(rel,text)
                else:z.write(f,rel)
        validation=verify(out,atlas=True)
        sync_generated_tree(out,O,export_repository=A)
        fixture=P/'fixture_reference';fixture_target=A/'reports/vna-calibration-fixture'
        if fixture.is_dir() and fixture_target.is_dir():
            changed={'index.html','app.js','README.md'}
            for file in fixture.iterdir():
                if file.is_file() and file.name not in changed:
                    assert file_hash(file)==file_hash(fixture_target/file.name), f'Review independent fixture change first: {file.name}'
            for name in sorted(changed):shutil.copyfile(fixture/name,fixture_target/name)
        catalog=json.loads((A/'reports.json').read_text(encoding='utf-8'))
        entry=next(e for e in catalog['reports'] if e['id']=='rf-current-probe')
        entry.update(summary='분할 코어와 수동 권선으로 케이블의 RF 합전류를 관측하는 시제품 설계. 3D 구조, 46단계 조립절차, 부품 규격과 Fixture A03의 500 MHz 보정 원리와 측정 순서를 살펴봅니다.',date='2026-09-28')
        (A/'reports.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        report=dict(target=str(O),validation=validation,files={f.relative_to(O).as_posix():file_hash(f) for f in sorted(O.rglob('*')) if f.is_file()})
        record=R/'viewer_A05/set_sources/atlas_export.json';record.parent.mkdir(parents=True,exist_ok=True)
        record.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(validation,ensure_ascii=False))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path)
    publish(parser.parse_args().repo)
