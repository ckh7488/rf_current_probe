"""Compare the four bench files with the frozen, premeasurement predictions."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import numpy as np
import skrf as rf

ROOT=Path(__file__).resolve().parents[2]
PRED=ROOT/'selected-evidence/ethernet-vna-prediction-v1/prediction-v1'
CASES={
    '01_open_B_J3.s1p':('open_b_s11','Open B reflection',0,0),
    '02_open_D_to_C.s2p':('open_d_to_c_s21','Open D to C coupling',1,0),
    '03_load_A_J2.s1p':('matched_a_s11','100 ohm A match',0,0),
    '04_loop_D_to_C.s2p':('loopback_d_to_c_s21','D to C loopback',1,0)}


def phase_delta(actual,expected):return np.angle(actual*np.conj(expected),deg=True)


def read_measured(path,frequency,row,column):
    net=rf.Network(str(path))
    if net.nports<=max(row,column):raise ValueError(path.name+': wrong port count')
    if not np.allclose(net.z0,50,rtol=0,atol=1e-6):raise ValueError(path.name+': use 50 ohm reference')
    if len(net.f)!=len(frequency) or not np.allclose(net.f,frequency,rtol=0,atol=.01):
        raise ValueError(path.name+': use a linear 1-200 MHz sweep with 1601 points')
    return net.s[:,row,column]


def compare(session,output):
    if output.exists():raise ValueError('Choose a new comparison output directory')
    files=[]
    for name,definition in CASES.items():
        path=session/name
        if not path.is_file() and name.endswith('.s1p'):path=path.with_suffix('.s2p')
        if path.is_file():files.append((path,path.name,*definition))
    if not files:raise ValueError('No named Touchstone files found; see README.md')
    metadata_path=session/'receipt.json'
    if not metadata_path.is_file():raise ValueError('Copy receipt-template.json to receipt.json and record the measurement conditions')
    metadata=json.loads(metadata_path.read_text(encoding='utf-8-sig'))
    if not metadata.get('board_unit_id') or not metadata.get('acquired_at_kst') or not metadata.get('instrument'):
        raise ValueError('Record board_unit_id, acquired_at_kst and instrument in receipt.json')
    with (PRED/'predicted-observables.csv').open() as handle:rows=list(csv.DictReader(handle))
    with (PRED/'time-window-review.csv').open() as handle:windows=list(csv.DictReader(handle))
    frequency=np.array([float(r['frequency_hz']) for r in rows])
    classification='SYNTHETIC_COMPARISON_CHECK' if str(metadata.get('classification','')).startswith('SYNTHETIC') else 'MEASURED_VS_SIMULATED'
    report={'classification':classification,'measurement':metadata,'prediction':'premeasurement-v1',
            'prediction_receipt_sha256':hashlib.sha256((PRED/'output-receipt.json').read_bytes()).hexdigest(),
            'reference_ohm':50,'frequency_points':len(frequency),'interpolation':False,'cases':{}}
    prepared=[]
    for path,name,key,label,row,col in files:
        source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        measured=read_measured(path,frequency,row,col)
        expected=np.array([complex(float(r[key+'_real']),float(r[key+'_imag'])) for r in rows])
        stable=np.array([bool(int(r[key+'_resolved'])) for r in windows])
        db=lambda values:20*np.log10(np.maximum(abs(values),1e-30))
        delta=db(measured)-db(expected);phase=phase_delta(measured,expected)
        sample=int(np.argmin(abs(frequency-100e6)))
        report['cases'][key]={'file':name,'sha256':source_hash,'classification':'MEASURED',
            'near_100mhz':{'frequency_hz':float(frequency[sample]),'measured_db':float(db(measured)[sample]),
                'predicted_db':float(db(expected)[sample]),'difference_db':float(delta[sample]),'phase_difference_deg':float(phase[sample])},
            'max_abs_difference_db_on_time_stable_points':float(abs(delta[stable]).max()),
            'max_abs_phase_difference_deg_on_time_stable_points':float(abs(phase[stable]).max()),
            'prediction_time_unstable_points':int((~stable).sum())}
        prepared.append((key,label,measured,expected,delta,phase,stable))
    output.mkdir(parents=True)
    for key,label,measured,expected,delta,phase,stable in prepared:
        with (output/(key+'.csv')).open('w',newline='') as handle:
            writer=csv.writer(handle);writer.writerow(['frequency_hz','predicted_db','measured_db','difference_db','phase_difference_deg','prediction_time_stable'])
            for f,p,m,d,a,ok in zip(frequency,db(expected),db(measured),delta,phase,stable):writer.writerow([f,p,m,d,a,int(ok)])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(len(prepared),2,squeeze=False,figsize=(11,3.2*len(prepared)),layout='constrained')
    for axrow,(_,label,measured,expected,delta,phase,stable) in zip(axes,prepared):
        axrow[0].plot(frequency/1e6,db(expected),label='Predicted',color='#197d71')
        axrow[0].plot(frequency/1e6,db(measured),label='Measured',color='#9b6a32',lw=1)
        axrow[0].set_ylabel('dB');axrow[0].set_title(label,loc='left');axrow[0].legend()
        axrow[1].plot(frequency/1e6,phase,color='#197d71');axrow[1].set_ylabel('Measured - predicted (deg)')
        for ax in axrow:ax.set_xlabel('MHz');ax.grid(alpha=.2);ax.set_xlim(1,200)
    fig.savefig(output/'comparison.png',dpi=160);plt.close(fig)
    (output/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for path,name,*_ in files:assert hashlib.sha256(path.read_bytes()).hexdigest()==next(x['sha256'] for x in report['cases'].values() if x['file']==name)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('session');args=parser.parse_args()
    if not args.session or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.session):
        raise SystemExit('Use a session name containing letters, numbers, dash or underscore')
    try:
        result=compare(ROOT/'measurements/raw/ethernet-vna'/args.session,ROOT/'measurements/processed/ethernet-vna'/args.session)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,FileNotFoundError) as error:raise SystemExit(str(error))
