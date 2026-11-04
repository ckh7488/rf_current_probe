"""Copy only read-only evidence from the earlier 1 GHz runs into this review."""
from pathlib import Path
import shutil,json,hashlib
R=Path(__file__).resolve().parents[1];B=R/'reviews/design_closure_20260921';old=R/'reviews/fixture_em_20260921'
for suffix in ['020','025']:
    src=old/('taper_resolved_'+suffix);name='reference_1g_pm'+suffix;dst=B/'em'/name
    dst.mkdir(exist_ok=False);hashes={}
    names=['model.json','model.xml','results.json','hi_empty.csv','model_source.py','PEC_dump.vtp','pec_connectivity.json']+['port_ut_1','port_it_1','port_ut_2','port_it_2']+[f'core_{i}_{j}' for i in range(5) for j in range(2)]
    for name_f in names:
        f=src/name_f
        if f.exists():shutil.copy2(f,dst/f.name);hashes[name_f]=hashlib.sha256(f.read_bytes()).hexdigest()
    shutil.copy2(old/('taper_resolved_'+suffix+'.log'),B/(name+'.log'))
    (dst/'reference_import.json').write_text(json.dumps(dict(classification='COPIED_PREVIOUS_SIMULATION_NOT_NEW_EXECUTION',source=str(src),sha256=hashes),indent=2))
    print(name,'imported')
