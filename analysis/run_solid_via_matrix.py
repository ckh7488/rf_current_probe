"""Run bounded, provenance-preserving solid-via fixture comparisons locally."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,json,time,sys,argparse,hashlib
R=Path(__file__).resolve().parents[1];O=R/'reviews/recheck_20260922';D=O/'em_solid'
p=argparse.ArgumentParser();p.add_argument('--group',choices=['convergence','sensitivity','followup'],default='convergence');p.add_argument('--case',help='Run one named case from the selected group');a=p.parse_args()
cases={'solid_baseline':[], 'solid_xy':['--mesh','1.5'], 'solid_z':['--z-mesh','0.3'], 'solid_domain':['--margin','120']} if a.group=='convergence' else {'solid_reverse':['--excite','2'],'solid_epsilon':['--epsilon','4.5'],'solid_launch':['--bore-radius','2.0','--connector-height','5.9'],'solid_excitation':['--f0-mhz','500','--fmax-mhz','350']}
if a.group=='followup':cases={'solid_domain_extended':['--margin','120','--end-criteria','1e-8']}
if a.case:
 assert a.case in cases,a.case
 cases={a.case:cases[a.case]}
assert all(not (D/name).exists() for name in cases),'Preserve existing cases; do not rerun over them'
geometry='reviews/design_closure_20260921/revised_fixture/geometry.json'
common=['--geometry',geometry,'--mesh','2','--z-mesh','0.5','--margin','80','--port-mesh','0.25','--f0-mhz','400','--fmax-mhz','300','--max-ns','80','--max-steps','1000000','--threads','6','--simplify','0.03','--debug-pec']
def stamp():return time.strftime('%Y-%m-%dT%H:%M:%S%z')
def run(name,extra):
 cmd=[sys.executable,str(R/'analysis/fixture_solid_vias.py'),'--name',name]+common+extra
 record=dict(name=name,command=cmd,started=stamp(),source_sha256=hashlib.sha256((R/'analysis/fixture_solid_vias.py').read_bytes()).hexdigest())
 (O/(name+'_execution.json')).write_text(json.dumps(record,indent=2))
 with (O/(name+'.log')).open('w') as log:
  proc=subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
  record['pid']=proc.pid;record['state']='RUNNING';(O/(name+'_execution.json')).write_text(json.dumps(record,indent=2))
  audited=False
  while proc.poll() is None:
   pec=D/name/'PEC_dump.vtp'
   # Read only after XML/VTK has been fully emitted and solver starts.
   text=(O/(name+'.log')).read_text(errors='replace')
   if not audited and pec.exists() and 'Running FDTD engine' in text:
    with (D/name/'topology_audit.log').open('w') as f:
     r1=subprocess.run([sys.executable,str(R/'analysis/audit_solid_via_definition.py'),str(D/name),'--geometry',geometry],cwd=R,stdout=f,stderr=subprocess.STDOUT)
     r2=subprocess.run([sys.executable,str(R/'analysis/audit_all_pec_components.py'),str(D/name),'--geometry',geometry,'--expect-two'],cwd=R,stdout=f,stderr=subprocess.STDOUT)
    audited=True;record['topology_pass']=r1.returncode==0 and r2.returncode==0
    if not record['topology_pass']:
     (D/name/'ABORT').touch();(D/name/'ABORT_REASON.json').write_text(json.dumps(dict(reason='FULL_SOLID_TOPOLOGY_AUDIT_FAILED',time=stamp()),indent=2))
    (O/(name+'_execution.json')).write_text(json.dumps(record,indent=2))
   time.sleep(5)
  record.update(exit_code=proc.returncode,finished=stamp(),state='SOLVER_RETURNED' if proc.returncode==0 else 'FAILED')
 if proc.returncode==0 and record.get('topology_pass'):
  with (D/name/'final_analysis.log').open('w') as f:
   result=subprocess.run([sys.executable,str(R/'analysis/analyse_fixture_solid.py'),name,'--snapshot','final'],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  record['analysis_exit_code']=result.returncode
 (O/(name+'_execution.json')).write_text(json.dumps(record,indent=2))
 return record
with ThreadPoolExecutor(max_workers=4) as pool:
 for result in as_completed([pool.submit(run,k,v) for k,v in cases.items()]):print(json.dumps(result.result()),flush=True)
