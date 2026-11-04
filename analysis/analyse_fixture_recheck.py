"""Reanalyse preserved ASCII V/I, including reverse signs and time windows.

Does not modify the original model or raw output. Every diagnostic snapshot
copies and hashes complete lines, so an in-progress calculation is reproducible.
"""
from pathlib import Path
import os,json,argparse,hashlib,re,csv,shutil,xml.etree.ElementTree as ET
import numpy as np
R=Path(__file__).resolve().parents[1]
rt=R/'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH']=str(rt);os.environ['CSXCAD_INSTALL_PATH']=str(rt)
from openEMS.utilities import DFT_time2freq
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--snapshot',required=True);p.add_argument('--source-snapshot');a=p.parse_args()
base=R/'reviews/recheck_20260922';d=base/'em'/a.name
meta=json.loads((d/'model.json').read_text());src=meta['parameters']['excite'];out=3-src
dest=d/a.snapshot;dest.mkdir(exist_ok=False)
names=['port_ut_1','port_it_1','port_ut_2','port_it_2']+[f'core_{i}_{j}' for i in range(5) for j in range(2)]+['centre_minus','centre_plus']
data={};hashes={};probe_positions={}
mesh=ET.parse(d/'model.xml')
grid={axis:np.array([float(v) for v in mesh.find('.//'+axis.upper()+'Lines').text.split(',')]) for axis in 'xyz'}
raw_source=d/a.source_snapshot if a.source_snapshot else d
for n in names:
    raw=(raw_source/n).read_bytes();raw=raw[:raw.rfind(b'\n')+1]
    (dest/n).write_bytes(raw);hashes[n]=hashlib.sha256(raw).hexdigest()
    lines=[x for x in raw.decode().splitlines() if x and not x.startswith(('%','#'))]
    data[n]=np.array([[float(v) for v in x.split()[:2]] for x in lines])
    if n.startswith('core_') or n.startswith('centre_'):
        # v0.37.0-rc2 ProcessIntegral header writes PRIMARY coordinates even
        # for ProcessCurrent, which samples the DUAL mesh. Use saved indices
        # and adjacent primary lines to obtain the actual integration plane.
        headers=raw.decode().splitlines()[1:3]
        indices=[tuple(int(v) for v in re.search(r'-> \[(\d+),(\d+),(\d+)\]',h).groups()) for h in headers]
        assert indices[0][1]==indices[1][1]
        coords=[]
        for ind in indices:coords.append([(grid[axis][ind[j]]+grid[axis][ind[j]+1])/2 for j,axis in enumerate('xyz')])
        probe_positions[n]=dict(actual_dual_start_mm=coords[0],actual_dual_stop_mm=coords[1],actual_y_mm=coords[0][1])
last=min(x[-1,0] for x in data.values());end=np.floor(last*1e9)*1e-9
if end<7e-9:raise RuntimeError('Source/settling window too short for a decision')
freq=np.unique(np.r_[np.geomspace(1e6,500e6,151),[1e6,10e6,30e6,100e6,200e6,300e6,500e6]])
windows=[];responses=[]
ys=np.array([probe_positions[f'core_{j}_0']['actual_y_mm'] for j in range(5)])
assert np.all(np.diff(ys)>0) and ys[0]<0<ys[-1]
def interpolation_weights(x):
    return np.array([np.prod([-x[k]/(x[j]-x[k]) for k in range(len(x)) if k!=j]) for j in range(len(x))])
weights=interpolation_weights(ys)
assert np.allclose([sum(weights*ys**k) for k in range(5)],[1,0,0,0,0],atol=1e-9)
near=np.sort(np.argsort(abs(ys))[:4]);weights4=interpolation_weights(ys[near])
right=np.searchsorted(ys,0);left=right-1;alpha=-ys[left]/(ys[right]-ys[left])
# Nominal ferrite axial thickness is 12.7 mm, centred at assembly Z=6.35.
# In the EM axes this is y=-6.35..+6.35. These are empty-fixture currents;
# an average here is not a model of the actual magnetic core response.
axial_weights=[];axial_mean_weights=[]
for j in range(5):
    poly=np.poly1d([1.])
    for k in range(5):
        if k!=j:poly*=np.poly1d([1.,-ys[k]])/(ys[j]-ys[k])
    axial_weights.append([float(poly(-6.35)),float(poly(6.35))])
    integ=np.polyint(poly);axial_mean_weights.append(float((integ(6.35)-integ(-6.35))/12.7))
axial_weights=np.array(axial_weights).T
for t in sorted(set([max(7e-9,end-10e-9),max(7e-9,end-5e-9),max(7e-9,end-2e-9),end-1e-9,end])):
    v={}
    for n,x in data.items():
        z=x[x[:,0]<=t];v[n]=DFT_time2freq(z[:,0],z[:,1],freq)
    ui=v[f'port_ut_{src}'];ii=v[f'port_it_{src}'];uo=v[f'port_ut_{out}'];io=v[f'port_it_{out}']
    inc=(ui+50*ii)/2;refl=(ui-50*ii)/2
    sr=refl/inc;st=(uo-50*io)/2/inc
    plane_values=np.array([v[f'core_{j}_0'] for j in range(5)])
    centre=weights@plane_values
    centre_linear=(1-alpha)*plane_values[left]+alpha*plane_values[right]
    centre_cubic=weights4@plane_values[near]
    yminus=probe_positions['centre_minus']['actual_y_mm'];yplus=probe_positions['centre_plus']['actual_y_mm']
    assert yminus<0<yplus
    centre_near=(yplus*v['centre_minus']-yminus*v['centre_plus'])/(yplus-yminus)
    centre_outer=weights@np.array([v[f'core_{j}_1'] for j in range(5)])
    axial_ends=axial_weights@plane_values;axial_mean=np.array(axial_mean_weights)@plane_values
    hi=centre/inc*np.sqrt(50)
    # Fixed physical current axis is +Y, so reverse excitation changes sign.
    hi_aligned=hi*(1 if src==1 else -1)
    im=hi_aligned*np.sqrt(50)
    rows=[]
    for i,f in enumerate(freq):
        current=centre[i]
        rows.append(dict(f_Hz=float(f),S_ref_re=float(sr[i].real),S_ref_im=float(sr[i].imag),
            S_thru_re=float(st[i].real),S_thru_im=float(st[i].imag),
            S_ref_dB=float(20*np.log10(abs(sr[i]))),S_thru_dB=float(20*np.log10(abs(st[i]))),
            HI_physical_re=float(hi[i].real),HI_physical_im=float(hi[i].imag),
            HI_aligned_re=float(hi_aligned[i].real),HI_aligned_im=float(hi_aligned[i].imag),
            I_over_matched_mag=float(abs(im[i])),I_over_matched_phase_deg=float(np.angle(im[i],deg=True)),
            power_fraction=float(abs(sr[i])**2+abs(st[i])**2),
            original_snapped_HI_re=float((v['core_2_0'][i]/inc[i]*np.sqrt(50)).real),
            original_snapped_HI_im=float((v['core_2_0'][i]/inc[i]*np.sqrt(50)).imag),
            centre_near_pair_vs_quartic_percent=float(100*abs(centre_near[i]/current-1)),
            centre_linear_vs_quartic_percent=float(100*abs(centre_linear[i]/current-1)),
            centre_cubic_vs_quartic_percent=float(100*abs(centre_cubic[i]/current-1)),
            core_axial_end_vs_centre_percent=float(100*np.max(abs(axial_ends[:,i]/current-1))),
            core_axial_mean_vs_centre_percent=float(100*abs(axial_mean[i]/current-1)),
            nested_delta_percent=float(100*abs(centre_outer[i]/current-1)),
            along_delta_percent=float(100*max(abs(v[f'core_{j}_0'][i]/current-1) for j in range(5)))))
    windows.append(dict(end_ns=float(t*1e9),rows=rows));responses.append((sr,st,hi_aligned))
changes=[]
for old,new in zip(responses,responses[1:]):
    changes.append(dict(s_ref_abs_max=float(np.max(abs(new[0]-old[0]))),
                        s_thru_abs_max=float(np.max(abs(new[1]-old[1]))),
                        hi_complex_relative_max=float(np.max(abs(new[2]/old[2]-1)))))
    changes[-1]['bands']={}
    for label,lo,hi_f in [('1_100_MHz',1e6,100e6),('100_300_MHz',100e6,300e6),('300_500_MHz',300e6,500e6)]:
        mask=(freq>=lo)&(freq<=hi_f)
        changes[-1]['bands'][label]=dict(hi_complex_relative_percent=float(100*np.max(abs(new[2][mask]/old[2][mask]-1))),s_ref_abs_max=float(np.max(abs(new[0][mask]-old[0][mask]))),s_thru_abs_max=float(np.max(abs(new[1][mask]-old[1][mask]))))
logpath=base/(a.name+'.log');log=logpath.read_text(errors='replace')
energy=re.findall(r'Energy:.*?\(\s*(-?\s*[\d.]+)dB\)',log)
completed=(d/'results.json').exists()
term='RUNNING'
if completed:
    term='MAXIMUM_TIMESTEPS' if 'Max. number of timesteps was reached' in log else 'SOLVER_RETURNED'
if (d/'ABORT').exists():term='INTENTIONAL_DIAGNOSTIC_STOP'
result=dict(data_kind='SIMULATED_NOT_MEASURED',completed_solver_return=completed,
            run=a.name,model=meta,raw_sha256=hashes,last_common_ns=float(last*1e9),
            termination=term,last_reported_energy_db=float(energy[-1].replace(' ','')) if energy else None,
            windows=windows,changes=changes,raw_source=str(raw_source),probe_positions=probe_positions,
            centre_reconstruction=dict(method='degree-4 spatial interpolation to physical y=0; linear and cubic estimates compared',positions_y_mm=ys.tolist(),weights=weights.tolist(),original_core_2_actual_y_mm=float(ys[2]),solver_source_commit='8f480d04e0e17a780df28e0ac12e2086be041f9e'),
            limitations=['Port is inside idealized SMA, not the physical mating plane.','No core/winding/cable.','Ampere current may include displacement current.','Physical y=0 current is spatially interpolated, not a direct integral at y=0.','End-window stability is not proof of full-field or spatial convergence.'])
(dest/'analysis.json').write_text(json.dumps(result,indent=2))
(dest/'analysis_source.py').write_bytes(Path(__file__).read_bytes())
(dest/'solver_log_snapshot.txt').write_bytes(logpath.read_bytes())
with (dest/'hi_empty_SIMULATED.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(windows[-1]['rows'][0]));w.writeheader();w.writerows(windows[-1]['rows'])
print(json.dumps(dict(run=a.name,termination=term,last_ns=last*1e9,energy_db=result['last_reported_energy_db'],changes=changes,
                     samples=[x for x in windows[-1]['rows'] if x['f_Hz'] in [1e6,100e6,300e6,500e6]]),indent=2))
