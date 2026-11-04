"""Apply the documented user-directed practical window criterion; no fake energy pass."""
from pathlib import Path
import json,time,subprocess,sys,re,math
R=Path(__file__).resolve().parents[1];O=R/'reviews/recheck_20260922';D=O/'em_solid'
names=['solid_baseline','solid_xy','solid_z','solid_domain','solid_reverse','solid_epsilon','solid_launch','solid_domain_extended']
seen={};stopped=set()
def stamp():return time.strftime('%Y-%m-%dT%H:%M:%S%z')
while True:
 finished=0
 for n in names:
  d=D/n;log=O/(n+'.log')
  if (d/'results.json').exists():finished+=1;continue
  if n in stopped or not (d/'all_pec_components.json').exists() or not log.exists():continue
  top=json.loads((d/'all_pec_components.json').read_text());via=json.loads((d/'solid_via_definition.json').read_text())
  if not top['pass_exactly_two_conducting_components'] or not via['pass_finite_cylinder_dimensions_and_mesh']:continue
  text=log.read_text(errors='replace');ex=re.search(r'Excitation Length \(s\)\s*:\s*([\d.eE+-]+)',text)
  if not ex:continue
  try:
   raw=(d/'core_2_0').read_text();raw=raw[:raw.rfind('\n')]
   last=float(raw.splitlines()[-1].split()[0])*1e9
  except (OSError,ValueError,IndexError):continue
  end=math.floor(last+1e-7);minimum=max(12,math.ceil(float(ex[1])*1e9+2))
  if end<minimum or seen.get(n,-1)>=end:continue
  seen[n]=end;snapshot='stability_'+str(end)+'ns'
  if (d/snapshot).exists():continue
  with (d/(snapshot+'.log')).open('w') as out:
   proc=subprocess.run([sys.executable,str(R/'analysis/analyse_fixture_solid.py'),n,'--snapshot',snapshot],cwd=R,stdout=out,stderr=subprocess.STDOUT)
  if proc.returncode:
   print(json.dumps(dict(time=stamp(),name=n,analysis_failure=proc.returncode,snapshot=snapshot)),flush=True);continue
  result=json.loads((d/snapshot/'analysis.json').read_text());windows=result['windows'];changes=result['changes'][-2:]
  actual_ends=[x['end_ns'] for x in windows[-3:]]
  ok=len(changes)==2 and len(actual_ends)==3 and all(abs(b-a-1)<1e-6 for a,b in zip(actual_ends,actual_ends[1:]))
  for c in changes:
   for band in ['1_100_MHz','100_300_MHz']:
    b=c['bands'][band];ok=ok and b['hi_complex_relative_percent']<=.2 and b['s_ref_abs_max']<=.002 and b['s_thru_abs_max']<=.002
  ok=ok and windows[-1]['incident_spectrum_min_to_max']>.001
  record=dict(time=stamp(),name=n,snapshot=snapshot,source_finished_ns=float(ex[1])*1e9,window_ends_ns=actual_ends,consecutive_window_changes=changes,energy_db=result['last_reported_energy_db'],observable_criterion_pass=bool(ok),energy_end_criterion_not_claimed=True,policy='reviews/recheck_20260922/NUMERICAL_STOP_POLICY_REVISION.md')
  (d/(snapshot+'_decision.json')).write_text(json.dumps(record,indent=2))
  print(json.dumps(dict(time=stamp(),name=n,end_ns=end,observable_criterion_pass=bool(ok),last_HI_1_100_percent=changes[-1]['bands']['1_100_MHz']['hi_complex_relative_percent'],energy_db=result['last_reported_energy_db'])),flush=True)
  if ok and not (d/'results.json').exists():
   record['reason']='OBSERVABLE_STABILITY_0P2_PERCENT_USER_SCOPE'
   (d/'ABORT_REASON.json').write_text(json.dumps(record,indent=2));(d/'ABORT').touch();stopped.add(n)
 if finished==len(names):break
 time.sleep(10)
print(json.dumps(dict(time=stamp(),stage='ALL_CASES_FINISHED',observable_stops=sorted(stopped))),flush=True)
