"""Bundle review evidence and native reproduction files without modifying originals."""
from pathlib import Path
import json,zipfile,hashlib
R=Path(__file__).resolve().parents[1];B=R/'reviews/design_closure_20260921'
assert (B/'comparison.json').exists() and (B/'README.md').exists()
out=B/'RFCP_DESIGN_CLOSURE_REVIEW_ONLY.zip'
files=set()
for folder in [B,R/'hardware/probe_head_A04_DRAFT',R/'hardware/calibration_fixture_PCB_A03_DRAFT']:
    for p in folder.rglob('*'):
        if not p.is_file() or p==out or '__pycache__' in p.parts:continue
        # Retain final evidence, omit intermediate checkpoints and preliminary console copies.
        if any(v.startswith(('preliminary_','plane_corrected_','checkpoint_','stability_')) for v in p.parts):continue
        if p.name.startswith('partial_') or p.suffix in ['.pyc','.lck']:continue
        files.add(p)
names=['sma_fit_review.py','prepare_sma_revisions.py','export_sma_revisions.py','verify_sma_revisions.py','extract_revised_fixture_em.py','fixture_validation.py','analyse_fixture_validation.py','inspect_pec_graph.py','complete_fixture_validation.py','verify_fixture_postprocess.py','summarise_fixture_closure.py','plot_sma_fit.py','plot_fixture_closure.py','import_fixture_reference.py','package_design_closure.py']
files.update(R/'analysis'/n for n in names)
files.update(R/'analysis'/n for n in ['write_design_closure_report.py','update_design_closure_status.py'])
files.update(R/p for p in ['docs/references/RFPC-SMA28-F.pdf','docs/RF_CURRENT_PROBE_WHITEPAPER.md','docs/G2_BENCH_PROCEDURE.md','docs/CURRENT_READINESS.md','reviews/fixture_em_20260921/geometry.json','reviews/fixture_em_20260921/requirements.txt'])
manifest={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files) if p.name!='package_manifest.json'}
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for rel in manifest:z.write(R/rel,rel)
    z.writestr('REVIEW_FILE_SHA256.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for rel,digest in manifest.items():assert hashlib.sha256(z.read(rel)).hexdigest()==digest
result=dict(status='DRAFT_REVIEW_ONLY_NOT_SUBMITTED_OR_APPROVED',file=out.name,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),files=len(manifest),bytes=out.stat().st_size,internal_hashes_verified=True,scope='Review evidence and native PCB reproduction; full project required for the original-file/STL baseline audit. Not a complete mechanical release or runtime installer.')
(B/'package_manifest.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
