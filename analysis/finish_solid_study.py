"""Continue the already-authorized local study after convergence cases finish."""
from pathlib import Path
import json,time,subprocess,sys
R=Path(__file__).resolve().parents[1];O=R/'reviews/recheck_20260922'
names=['solid_baseline','solid_xy','solid_z','solid_domain']
sensitivities=['solid_reverse','solid_epsilon','solid_launch','solid_domain_extended']
all_names=names+sensitivities
queue=[n for n in sensitivities if not (O/(n+'_execution.json')).exists()]
started=set(names+[n for n in sensitivities if n not in queue])
active={}
def status(stage,**extra):
 d=dict(stage=stage,time=time.strftime('%Y-%m-%dT%H:%M:%S%z'),**extra);(O/'solid_study_status.json').write_text(json.dumps(d,indent=2));print(json.dumps(d),flush=True)
status('ROLLING_QUEUE_ACTIVE',note='Use each completed convergence slot for one sensitivity case. Physics and maximum four simultaneous solvers unchanged.')
while True:
 records={}
 for n in all_names:
  try:records[n]=json.loads((O/(n+'_execution.json')).read_text())
  except (FileNotFoundError,json.JSONDecodeError):pass
 if any(r.get('state')=='FAILED' or r.get('analysis_exit_code',0)!=0 for r in records.values()):
  status('REQUIRES_MODEL_REVIEW',records=records);sys.exit(1)
 complete={n for n,r in records.items() if r.get('state')=='SOLVER_RETURNED' and r.get('analysis_exit_code')==0}
 for n,proc in list(active.items()):
  if proc.poll() is not None:
   if proc.returncode or n not in complete:
    status('SENSITIVITY_RUN_FAILURE',name=n,exit_code=proc.returncode);sys.exit(1)
   del active[n]
 if len(complete)==len(all_names):break
 occupied=sum(n not in complete for n in started)
 while queue and occupied<4:
  n=queue.pop(0)
  assert not (O/'em_solid'/n).exists(),'Never overwrite an existing run'
  group='followup' if n=='solid_domain_extended' else 'sensitivity'
  active[n]=subprocess.Popen([sys.executable,str(R/'analysis/run_solid_via_matrix.py'),'--group',group,'--case',n],cwd=R)
  started.add(n)
  occupied+=1
  status('ROLLING_QUEUE_ACTIVE',started=n,pid=active[n].pid,completed=sorted(complete),remaining_queue=queue)
 time.sleep(5)
status('GENERATING_FROZEN_COMPARISON')
with (O/'solid_comparison.log').open('w') as log:
 run=subprocess.run([sys.executable,str(R/'analysis/compare_solid_fixture.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT)
status('READY_FOR_ENGINEERING_REVIEW' if run.returncode==0 else 'COMPARISON_FAILURE',exit_code=run.returncode)
sys.exit(run.returncode)
