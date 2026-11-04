"""One non-blocking audit of live runs; graceful stop only on documented criteria."""
from pathlib import Path
import subprocess,json,sys,datetime
R=Path(__file__).resolve().parents[1];B=R/'reviews/design_closure_20260921'
for d in sorted((B/'em').iterdir()):
    if not d.is_dir() or not (d/'model.json').exists():continue
    if (d/'ABORT').exists() or (d/'results.json').exists():
        print(d.name,'STOP_REQUESTED' if (d/'ABORT').exists() else 'RETURNED');continue
    p=d/'core_2_0'
    if not p.exists():print(d.name,'SETUP');continue
    lines=p.read_text().splitlines();data=[v for v in lines if v and not v.startswith('%')]
    if len(data)<2:continue
    last=float(data[-2].split()[0])*1e9
    if last<12:print(d.name,round(last,3),'ns; continue');continue
    tag='stability_'+str(int(last))
    if (d/tag).exists():print(d.name,tag,'already examined; continue');continue
    cmd=[sys.executable,str(R/'analysis/analyse_fixture_validation.py'),d.name,'--snapshot',tag]
    run=subprocess.run(cmd,cwd=R,capture_output=True,text=True)
    (B/(d.name+'_'+tag+'.txt')).write_text(run.stdout+'\n'+run.stderr)
    if run.returncode:raise RuntimeError(run.stderr)
    a=json.loads((d/tag/'analysis.json').read_text())
    passed=all(c['hi_complex_relative_max']<=.0005 and c['s_ref_abs_max']<=.0005 and c['s_thru_abs_max']<=.0005 for c in a['changes'])
    print(d.name,round(a['last_common_ns'],3),a['changes'],'PASS' if passed else 'CONTINUE')
    if passed:
        decision=dict(classification='SIMULATION_STOP_DECISION_NOT_FULL_FIELD_CONVERGENCE',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),snapshot=tag,last_common_ns=a['last_common_ns'],criteria='>=12 ns; each of the two successive 1 ns extensions: complex HI change <=0.05% and complex S change <=0.0005 over 1-500 MHz',changes=a['changes'],last_energy_db=a['last_reported_energy_db'],reason='Observables passed finite-window checks; global -50 dB not claimed. Preserve remaining model uncertainty.',mechanism='openEMS CheckAbortCond documented ABORT file, graceful output flush')
        (d/'stop_decision.json').write_text(json.dumps(decision,indent=2))
        (d/'ABORT').write_text('Documented observable-stability stop; see stop_decision.json. Not global energy convergence.\n')
