"""Compare frozen final snapshots; no implied measured performance or error bound."""
from pathlib import Path
import json,argparse,numpy as np
R=Path(__file__).resolve().parents[1];B=R/'reviews/design_closure_20260921'
p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');a=p.parse_args()
names=['reference_1g_pm020','reference_1g_pm025','forward_600','reverse_600','revised_holes_600','revised_numeric_corner','revised_epsilon45','revised_material_launch_corner']
data={}
for name in names:
    f=B/'em'/name/'final_analysis/analysis.json'
    if f.exists():data[name]=json.loads(f.read_text())
    elif not a.partial:raise FileNotFoundError(f)
bands=[('1–100 MHz',1e6,100e6),('100–300 MHz',100e6,300e6),('300–500 MHz',300e6,500e6)]
def arrays(name):
    rows=data[name]['windows'][-1]['rows']
    def c(k):return np.array([complex(v[k+'_re'],v[k+'_im']) for v in rows])
    return np.array([v['f_Hz'] for v in rows]),c('S_ref'),c('S_thru'),c('HI_aligned')
pairs=[('old_local_mesh','reference_1g_pm020','reference_1g_pm025','Old board; 0.20 vs 0.25 mm local mesh, source 1 GHz.'),('source_and_window','reference_1g_pm020','forward_600','Old board, same mesh; source bandwidth and final time window both differ.'),('direction','forward_600','reverse_600','Old asymmetric board, reversed source; current sign aligned.'),('holes_and_source','reference_1g_pm025','revised_holes_600','Same mesh; holes and source/window differ. Not an isolated hole derivative.'),('new_holes_and_local_mesh','forward_600','revised_holes_600','Source 600 MHz; holes and local mesh differ together.'),('combined_numerics','revised_holes_600','revised_numeric_corner','New board; XY 2→1.5 mm, Z 0.5→0.3 mm, domain margin 80→120 mm together.'),('epsilon','revised_holes_600','revised_epsilon45','New board; assumed FR4 epsilon 4.3→4.5 only.'),('launch','revised_epsilon45','revised_material_launch_corner','New board, same epsilon4.5; assumed feed height6.4→5.4 mm and bore radius2.2→2.1 mm together.')]
comparisons=[]
for label,old,new,note in pairs:
    if old not in data or new not in data:continue
    f,s1,t1,h1=arrays(old);f2,s2,t2,h2=arrays(new);assert np.array_equal(f,f2)
    b=[]
    for band,lo,hi in bands:
        m=(f>=lo)&(f<=hi)
        b.append(dict(band=band,HI_complex_delta_percent=float(100*max(abs(h2[m]/h1[m]-1))),HI_magnitude_delta_percent=float(100*max(abs(abs(h2[m])/abs(h1[m])-1))),S_through_complex_abs_delta=float(max(abs(t2[m]-t1[m]))),S_reflection_complex_abs_delta=float(max(abs(s2[m]-s1[m])))))
    comparisons.append(dict(name=label,baseline=old,variant=new,note=note,bands=b))
summaries=[]
for name,d in data.items():
    f,s,t,h=arrays(name);rows=d['windows'][-1]['rows'];low=f<=1e8
    passivity=max(v['power_fraction'] for v in rows)
    s=dict(name=name,new_execution=not name.startswith('reference_'),last_common_ns=d['last_common_ns'],DFT_end_ns=d['windows'][-1]['end_ns'],energy_db=d['last_reported_energy_db'],termination=d['termination'],time_window_changes=d['changes'],max_power_fraction=passivity,max_nested_percent_1_100=max(v['nested_delta_percent'] for v in rows if v['f_Hz']<=1e8),max_linear_vs_quartic_percent_1_100=max(v['centre_linear_vs_quartic_percent'] for v in rows if v['f_Hz']<=1e8),max_cubic_vs_quartic_percent_1_100=max(v['centre_cubic_vs_quartic_percent'] for v in rows if v['f_Hz']<=1e8),max_core_end_vs_centre_percent_1_100=max(v['core_axial_end_vs_centre_percent'] for v in rows if v['f_Hz']<=1e8),max_core_mean_vs_centre_percent_1_100=max(v['core_axial_mean_vs_centre_percent'] for v in rows if v['f_Hz']<=1e8),matched_magnitude_max_error_percent_1_100=float(100*max(abs(abs(h[low])*np.sqrt(50)-1))),port_current_complex_error_percent_1_100=float(100*max(abs(((1-s[low])/np.sqrt(50))/h[low]-1))),samples=[v for v in rows if v['f_Hz'] in [1e6,10e6,30e6,100e6,300e6,500e6]])
    summaries.append(s)
out=dict(classification='SIMULATED_MODEL_COMPARISON_NOT_MEASURED',partial=a.partial,runs=summaries,comparisons=comparisons,limitations=['Finite-window stability is not global field convergence.','No magnetic core/winding, physical SMA mating-plane reference or real material characterization.','Case differences are not uncertainty bounds or statistically independent terms.'])
stem='partial_comparison' if a.partial else 'comparison'
(B/(stem+'.json')).write_text(json.dumps(out,indent=2))
print(json.dumps(dict(runs=[dict(name=v['name'],last_ns=v['last_common_ns'],energy=v['energy_db'],I_error_percent_1_100=v['matched_magnitude_max_error_percent_1_100']) for v in summaries],comparisons=comparisons),indent=2))
