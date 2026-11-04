"""Compare frozen final solid-via runs and all four entries of the two-port S."""
from pathlib import Path
import argparse,json,numpy as np,hashlib
R=Path(__file__).resolve().parents[1];B=R/'reviews/recheck_20260922';D=B/'em_solid'
p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');a=p.parse_args()
names=['solid_baseline','solid_xy','solid_z','solid_domain','solid_reverse','solid_epsilon','solid_launch']
actual={n:('solid_domain_extended' if n=='solid_domain' else n) for n in names}
data={}
for n in names:
 f=D/actual[n]/'final/analysis.json'
 if f.exists():data[n]=json.loads(f.read_text())
 elif not a.partial:raise FileNotFoundError(f)
bands=[('1_100_MHz',1e6,100e6),('100_300_MHz',100e6,300e6),('300_500_MHz',300e6,500e6)]
def arr(n):
 rows=data[n]['windows'][-1]['rows']
 def c(k):return np.array([complex(v[k+'_re'],v[k+'_im']) for v in rows])
 return np.array([v['f_Hz'] for v in rows]),c('S_ref'),c('S_thru'),c('HI_aligned')
comparisons=[]
if 'solid_baseline' in data:
 f,s0,t0,h0=arr('solid_baseline')
 for n in names[1:]:
  if n not in data:continue
  f2,s,t,h=arr(n);assert np.array_equal(f,f2)
  values={}
  for band,lo,hi in bands:
   m=(f>=lo)&(f<=hi)
   values[band]=dict(HI_complex_delta_percent=float(100*max(abs(h[m]/h0[m]-1))),HI_magnitude_delta_dB=float(max(abs(20*np.log10(abs(h[m]/h0[m]))))),HI_phase_delta_deg=float(max(abs(np.angle(h[m]/h0[m],deg=True)))),S_ref_complex_abs_delta=float(max(abs(s[m]-s0[m]))),S_through_complex_abs_delta=float(max(abs(t[m]-t0[m]))))
  comparisons.append(dict(baseline='solid_baseline',variant=n,bands=values,kind='directional_current_is_not_reciprocity' if n=='solid_reverse' else 'one_parameter_group_at_a_time'))
summary=[]
for n,d in data.items():
 rows=d['windows'][-1]['rows'];top=json.loads((D/actual[n]/'all_pec_components.json').read_text());definition=json.loads((D/actual[n]/'solid_via_definition.json').read_text())
 obs={}
 for band,lo,hi in bands:
  rs=[r for r in rows if lo<=r['f_Hz']<=hi]
  obs[band]={k:float(max(r[k] for r in rs)) for k in ['power_fraction','nested_delta_percent','centre_near_pair_vs_quartic_percent','centre_cubic_vs_quartic_percent','core_axial_mean_vs_centre_percent','core_axial_end_vs_centre_percent']}
 summary.append(dict(name=n,last_ns=d['last_common_ns'],DFT_end_ns=d['windows'][-1]['end_ns'],energy_db=d['last_reported_energy_db'],termination=d['termination'],topology_pass=top['pass_exactly_two_conducting_components'],finite_vias_pass=definition['pass_finite_cylinder_dimensions_and_mesh'],source_spectrum_min_ratio=d['windows'][-1]['incident_spectrum_min_to_max'],last_window_change=d['changes'][-1],all_window_changes=d['changes'],observables=obs,samples=[r for r in rows if r['f_Hz'] in [1e6,10e6,30e6,100e6,300e6,500e6]]))
 summary[-1]['natural_return_before_planned_12ns']=d.get('natural_return_before_planned_12ns',False)
 summary[-1]['actual_run_directory']=actual[n]
twoport=None
if 'solid_baseline' in data and 'solid_reverse' in data:
 f,s11,s21,h1=arr('solid_baseline');f2,s22,s12,h2=arr('solid_reverse');assert np.array_equal(f,f2)
 S=np.zeros((len(f),2,2),complex);S[:,0,0]=s11;S[:,1,0]=s21;S[:,0,1]=s12;S[:,1,1]=s22
 sigma=np.linalg.svd(S,compute_uv=False)[:,0];twoport={}
 for band,lo,hi in bands:
  m=(f>=lo)&(f<=hi);j=np.where(m)[0][np.argmax(sigma[m])]
  twoport[band]=dict(max_singular_value=float(max(sigma[m])),maximum_excess_power_percent=float(max(0,max(sigma[m])**2-1)*100),worst_frequency_Hz=float(f[j]),reciprocity_max_abs_S21_minus_S12=float(max(abs(s21[m]-s12[m]))))
checks={}
for c in comparisons:
 if c['variant'] in ['solid_xy','solid_z','solid_domain']:
  checks[c['variant']]=dict(first_band_HI_under_1_percent=c['bands']['1_100_MHz']['HI_complex_delta_percent']<=1,upper_target_band_HI_under_3_percent=c['bands']['100_300_MHz']['HI_complex_delta_percent']<=3)
out=dict(classification='SIMULATED_SOLID_VIA_MODEL_COMPARISON_NOT_MEASURED',partial=a.partial,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),runs=summary,comparisons=comparisons,full_twoport=twoport,predeclared_mesh_screens=checks,limitations=['A difference between cases is not a strict remaining-error bound.','Ports inside idealized SMA; no actual mating-plane, cable, core, winding or physical material characterization.','No measured probe precision or manufacturer approval follows from this result.'])
target=B/('solid_comparison_partial.json' if a.partial else 'solid_comparison.json');target.write_text(json.dumps(out,indent=2))
print(json.dumps(dict(runs=[{k:s[k] for k in ['name','last_ns','energy_db','termination','topology_pass']} for s in summary],comparisons=comparisons,full_twoport=twoport,predeclared_mesh_screens=checks),indent=2))
