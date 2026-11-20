"""Review completed, frozen outputs without changing prediction data or inputs."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import csv
import hashlib
import json
import numpy as np
import skrf as rf
from analyze import wave_matrices,observables
from network import assembled

HERE=Path(__file__).resolve().parent
KEYS=['open_b_s11','open_d_to_c_s21','matched_a_s11','loopback_d_to_c_s21']


def bands(frequency,mask):
    groups=[];start=None
    for i,value in enumerate(list(mask)+[False]):
        if value and start is None:start=i
        elif not value and start is not None:
            groups.append([float(frequency[start]/1e6),float(frequency[i-1]/1e6)]);start=None
    return groups


def trace_review(frequency,nominal,shorter3,shorter4,threshold):
    error=np.maximum(abs(nominal-shorter3),abs(nominal-shorter4))
    relative=error/np.maximum(abs(nominal),1e-30)
    mask=relative<=threshold
    samples={}
    for mhz in [1,10,50,100,150,200]:
        value=np.interp(mhz*1e6,frequency,nominal)
        a=np.interp(mhz*1e6,frequency,shorter3);b=np.interp(mhz*1e6,frequency,shorter4)
        samples[str(mhz)]={
            'db':float(20*np.log10(max(abs(value),1e-30))),
            'phase_deg':float(np.angle(value,deg=True)),
            'max_time_window_magnitude_change_db':float(max(abs(20*np.log10(max(abs(w),1e-30)/max(abs(value),1e-30))) for w in [a,b])),
            'max_time_window_phase_change_deg':float(max(abs(np.angle(w*np.conj(value),deg=True)) for w in [a,b])),
            'resolved':bool(np.interp(mhz*1e6,frequency,relative)<=threshold)}
    return {'resolved_fraction':float(mask.mean()),'resolved_bands_mhz':bands(frequency,mask),
            'unresolved_bands_mhz':bands(frequency,~mask),'at_100mhz':samples['100'],'samples':samples}


def main():
    out=HERE/'prediction-v1'
    policy=json.loads((HERE/'numerical-review-policy.json').read_text())
    summary=json.loads((out/'summary.json').read_text())
    assert summary['classification']=='SIMULATED' and summary['new_rf_measurements_used'] is False
    receipt=json.loads((out/'output-receipt.json').read_text())
    assert receipt['input_manifest_sha256']=='c32f552001013efe648bb1f30f2df84d11ccaa6134cf6a27eea3bd92459ee884'
    for record in receipt['files']:
        assert hashlib.sha256((HERE/record['file']).read_bytes()).hexdigest()==record['sha256'],record['file']
    for record in receipt['raw_results']:
        folder=HERE/record['folder']
        assert hashlib.sha256((folder/'results.npz').read_bytes()).hexdigest()==record['results_sha256'],record['folder']
        assert hashlib.sha256((folder/'model.json').read_bytes()).hexdigest()==record['model_sha256'],record['folder']
    with (out/'predicted-observables.csv').open() as handle:rows=list(csv.DictReader(handle))
    f=np.array([float(r['frequency_hz']) for r in rows])
    curves={key:np.array([complex(float(r[key+'_real']),float(r[key+'_imag'])) for r in rows]) for key in KEYS}
    folders=[HERE/'runs'/f'nominal-finite-v1-p{i:02d}' for i in range(1,25)]
    checks=[json.loads((p/'run-check.json').read_text()) for p in folders]
    assert all(check['pass'] for check in checks)
    port_tails=[]
    for drive,folder in enumerate(folders,1):
        tail={'drive':drive}
        with np.load(folder/'results.npz') as data:
            for kind in ['u','i']:
                times=data[kind+'_time_1'];keep=times>times[-1]-.5e-9
                values=np.stack([data[kind+'t_tot_'+str(port)] for port in range(1,25)],axis=1)
                source_peak=max(float(abs(values[:,drive-1]).max()),1e-30)
                tail[kind+'_last_half_ns_peak_relative_to_driven_peak']=float(abs(values[keep]).max()/source_peak)
        port_tails.append(tail)
    parameters=json.loads((HERE/'electrical-assumptions.json').read_text())
    windows={5:curves}
    for cutoff in [3,4]:
        _,s,_=wave_matrices(folders,cutoff)
        windows[cutoff]=observables({mode:assembled(s,f,mode,parameters) for mode in ['open','match','loopback']})
    checks=summary['checks']
    matrix_checks={
        'normalized_incident':checks['max_incident_matrix_condition']<=policy['max_normalized_incident_condition'],
        'pcb_passivity':checks['pcb_max_singular_value']<=policy['max_pcb_singular_value'],
        'pcb_reciprocity':checks['pcb_max_reciprocity_error_linear']<=policy['max_pcb_reciprocity_error_linear']}
    assembly={}
    for mode in ['open','match','loopback']:
        net=rf.Network(str(out/(mode+'-sma.s4p')))
        maximum=float(np.linalg.svd(net.s,compute_uv=False).max())
        assembly[mode]={'max_singular_value':maximum,'passivity_check':maximum<=policy['max_assembled_singular_value'],
                        'max_reciprocity_error_linear':float(abs(net.s-net.s.transpose(0,2,1)).max())}
        if mode in ['open','loopback']:
            forward,reverse=net.s[:,2,3],net.s[:,3,2]
            denominator=np.maximum(np.maximum(abs(forward),abs(reverse)),1e-30)
            assembly[mode]['d_c_relative_reciprocity_error']={
                'max':float((abs(forward-reverse)/denominator).max()),
                'at_100mhz':float(np.interp(100e6,f,abs(forward-reverse)/denominator))}
        matrix_checks[mode+'_passivity']=assembly[mode]['passivity_check']
    traces={}
    for key in KEYS:
        traces[key]=trace_review(f,curves[key],windows[3][key],windows[4][key],policy['resolved_complex_relative_change'])
    review={'classification':'NUMERICAL_REVIEW','reviewed':True,'reviewed_at_kst':datetime.now(timezone(timedelta(hours=9))).isoformat(),
            'matrix_checks_passed':all(matrix_checks.values()),'matrix_checks':matrix_checks,
            'assembly':assembly,'traces':traces,'port_waveform_tail_diagnostics':port_tails,
            'source_receipt_sha256':hashlib.sha256((out/'output-receipt.json').read_bytes()).hexdigest(),
            'policy_sha256':hashlib.sha256((HERE/'numerical-review-policy.json').read_bytes()).hexdigest(),
            'new_rf_measurements_used':False}
    review['status']='REVIEWED' if review['matrix_checks_passed'] else 'NUMERICAL_CHECK_FAILED'
    with (out/'time-window-review.csv').open('w',newline='') as handle:
        writer=csv.writer(handle)
        writer.writerow(['frequency_hz']+[key+'_'+part for key in KEYS for part in ['3ns_db','4ns_db','5ns_db','relative_complex_change','resolved']])
        for i,frequency in enumerate(f):
            row=[float(frequency)]
            for key in KEYS:
                values=[windows[n][key][i] for n in [3,4,5]]
                change=max(abs(values[0]-values[2]),abs(values[1]-values[2]))/max(abs(values[2]),1e-30)
                row.extend([float(20*np.log10(max(abs(v),1e-30))) for v in values]+[float(change),int(change<=policy['resolved_complex_relative_change'])])
            writer.writerow(row)
    (out/'numerical-review.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__=='__main__':main()
