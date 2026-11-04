"""Export/check only the new DRAFT revisions; preserve all previous artifacts."""
from pathlib import Path
import json,subprocess,zipfile,hashlib
R=Path(__file__).resolve().parents[1]
K=r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
for directory in ['probe_head_A04_DRAFT','calibration_fixture_PCB_A03_DRAFT']:
    h=R/'hardware'/directory;c=json.loads((h/'revision.json').read_text())
    n=c['new_name'];p=h/(n+'.kicad_pcb');s=h/(n+'.kicad_sch');v=h/'review';f=h/'gerbers_DRAFT'
    jobs=[
        ['sch','erc','--format','json','--severity-all','--exit-code-violations','-o',str(v/'erc.json'),str(s)],
        ['pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','--severity-all','--exit-code-violations','-o',str(v/'drc.json'),str(p)],
        ['sch','export','netlist','--format','kicadxml','-o',str(v/'netlist.xml'),str(s)],
        ['pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--subtract-soldermask','-o',str(f),str(p)],
        ['pcb','export','drill','--excellon-separate-th','--excellon-oval-format','route','--generate-report','--report-path',str(v/'drill_report.txt'),'-o',str(f),str(p)],
        ['pcb','export','step','--force','--board-only','--user-origin','0x0mm','-o',str(v/'board_only.step'),str(p)],
        ['pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--layers','F.Cu,F.Silkscreen,Edge.Cuts','-o',str(v/'top.svg'),str(p)],
    ]
    runs=[]
    for i,args in enumerate(jobs):
        run=subprocess.run([K]+args,capture_output=True)
        (v/f'export_{i:02d}.log').write_bytes(run.stdout+b'\n'+run.stderr)
        runs.append(dict(command=[K]+args,returncode=run.returncode))
        (v/'commands.json').write_text(json.dumps(runs,indent=2))
        print(directory,i,run.returncode,flush=True)
        if run.returncode:raise RuntimeError((run.stdout+run.stderr).decode('utf-8','replace'))
    z=h/(n+'_REVIEW_ONLY.zip')
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(f.iterdir()):archive.write(file,file.name)
    (h/'export_manifest.json').write_text(json.dumps(dict(status='DRAFT - NOT FOR FABRICATION',zip_sha256=hashlib.sha256(z.read_bytes()).hexdigest(),files={file.name:hashlib.sha256(file.read_bytes()).hexdigest() for file in sorted(f.iterdir())}),indent=2))
