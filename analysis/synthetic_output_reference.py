"""Create labelled SYNTHETIC file bundle for the production calibration CLI.

No instrument data or hardware accuracy claim. Every threshold is illustrative.
"""
from pathlib import Path
import argparse
import csv
import json
import math
import numpy as np
from analysis import rfcp
from analysis.output_reference import IDENTITY, UNCERTAINTY_COMPONENTS, REVIEW_NUMBERS, REVIEW_FLAGS


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def write_s(path, f, s):
    lines=['! SYNTHETIC analytic power-wave example; NOT MEASURED', '# Hz S RI R 50']
    for frequency, matrix in zip(f,s):
        values=matrix.flatten(order='F')
        lines.append(f'{frequency:.17g} '+' '.join(f'{x.real:.17g} {x.imag:.17g}' for x in values))
    Path(path).write_text('\n'.join(lines)+'\n',encoding='ascii')


def create(out, f=None, zt=None, calibration=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    f=np.array([1,10,30,100,200,300,400,500],float)*1e6 if f is None else np.asarray(f,float)
    zt=(5+.7j)*np.exp(-2j*np.pi*f*0.2e-9) if zt is None else np.broadcast_to(zt,f.shape).astype(complex)
    meta={key:'SYNTHETIC' for key in rfcp.REQUIRED}
    meta.update(schema_version=1,data_kind='SYNTHETIC',head_id='SYN-HEAD',head_revision='SYN-5T',
                turns=5,fixture_id='SYN-FIXTURE',fixture_revision='SYN-A03',configuration_id='SYN-CONFIG',
                primary_load_id='SYN-LOAD',calibration_id='SYN-OUTPUT-CAL',cable_ids=['SYN-CABLE'],
                included_chain_ids=['SYN-CABLE'],additional_correction_ids=[],termination='receiver_single_50_ohm',
                frequency_range=[float(f[0]),float(f[-1])],valid_frequency_bands_hz=[[float(f[0]),float(f[-1])]],
                invalid_frequency_bands_hz=[],clipped=False,phase_validated=True,
                phase_evidence='SYNTHETIC exact wave solution; no instrument validation',uncertainty_db=None,
                minimum_zt_ohm=1e-6,quality_review={**{key:True for key in rfcp.QUALITY_CHECKS},'evidence':'SYNTHETIC exact example'},
                output_reference_plane=dict(id='SYN-CHAIN-OUT',verified=True,impedance_ohm=50,evidence='SYNTHETIC 50 ohm'),
                current_model=dict(mode='output_reference',bundle_file='bundle.json',evidence='SYNTHETIC power-wave boundary conditions'))
    if calibration is not None:
        for key in ['head_id','head_revision','calibration_id','included_chain_ids','output_reference_plane']:
            meta[key]=calibration[key]
    def spec(name,**kwargs):
        return dict(file=name,sha256=rfcp.sha256(out/name),data_kind='SYNTHETIC',**kwargs)
    gamma=.12*np.exp(-2j*np.pi*f*.4e-9)
    write_s(out/'load.s1p',f,gamma[:,None,None])
    bundle=dict(schema_version=1,data_kind='SYNTHETIC',alignment=dict(method='exact'),
                evidence={key:'SYNTHETIC illustrative example; not a hardware assessment' for key in ['current_path','head_load_swap','limits','uncertainty']},
                uncertainty_components=sorted(UNCERTAINTY_COMPONENTS),
                limits=dict(minimum_through_magnitude=1e-5,minimum_k_magnitude=1e-3,minimum_one_minus_gamma=.05,
                            minimum_feedback_denominator=.05,minimum_snr_db=30,maximum_direct_pickup_db=-30,
                            maximum_repeatability_db=.5,maximum_direction_error_db=.5,maximum_direction_phase_deg=5))
    for direction,polarity in [('forward',1),('reverse',-1)]:
        through=np.zeros((len(f),2,2),complex)
        through[:,0,0]=.3 # Deliberately does not meet an S11 <= -20 dB gate.
        through[:,1,0]=(.81 if polarity==1 else .77)*np.exp(-2j*np.pi*f*.8e-9)
        through[:,0,1]=through[:,1,0]
        through[:,1,1]=(.14+.04j)*np.exp(-2j*np.pi*f*.3e-9)
        k=(1+.04j)*(1+(f/500e6)**2*.12)
        # Solve b2 = S21*a1 + S22*a2, a2=Gamma*b2 using a1=1 sqrt(W).
        # Power waves: Iout=(b2-a2)/sqrt(50), Vreceiver=sqrt(50)*b_receiver.
        b2=np.array([np.linalg.solve(np.array([[1,-s22],[-g,1]],complex),[s21,0])[0]
                     for s21,s22,g in zip(through[:,1,0],through[:,1,1],gamma)])
        a2=gamma*b2
        core_current=k*(b2-a2)/math.sqrt(50)
        transfer=np.zeros_like(through)
        transfer[:,1,0]=polarity*zt*core_current/math.sqrt(50)
        write_s(out/f'{direction}_through.s2p',f,through)
        write_s(out/f'{direction}_transfer.s2p',f,transfer)
        with (out/f'{direction}_k.csv').open('w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream);writer.writerow(['frequency_hz','k_real','k_imag','valid'])
            writer.writerows((x,v.real,v.imag,'true') for x,v in zip(f,k))
        group=dict(identity={key:meta[key] for key in IDENTITY},input_plane_id=f'SYN-{direction}-IN',
                   fixture_output_plane_id=f'SYN-{direction}-OUT',probe_output_plane_id=meta['output_reference_plane']['id'],
                   vna_calibration_id=f'SYN-2PORT-{direction}',setup_id=f'SYN-SETUP-{direction}',polarity=polarity,
                   phase_validated=True,reflection_phase_validated=True,evidence='SYNTHETIC current direction and fixed setup')
        for role in ['through','transfer']:
            group[role]=spec(f'{direction}_{role}.s2p',setup_id=group['setup_id'],vna_calibration_id=group['vna_calibration_id'],
                             reference_plane_ids=[group['input_plane_id'],group['fixture_output_plane_id'] if role=='through' else group['probe_output_plane_id']])
        group['k']=spec(f'{direction}_k.csv',units='Icore/Iout',output_plane_id=group['fixture_output_plane_id'],
                        applies_to_fixture_revision=meta['fixture_revision'],source_fixture_revision=meta['fixture_revision'],
                        applicability_evidence='SYNTHETIC same fixture model, complex current ratio',phase_validated=True)
        bundle[direction]=group
    bundle['load']=spec('load.s1p',load_id=meta['primary_load_id'],reference_plane_id='SYN-FEMALE-SMA',
                        calibration_id='SYN-1PORT-FEMALE',standards_model_id='SYN-MALE-SOL',connector='SMA-F',
                        calibration_method='SOL_AT_FEMALE_PLANE',calibrated=True,standards_connector='SMA-M',
                        phase_validated=True,evidence='SYNTHETIC independent SOL at female port; no physical connection',
                        applies_to_output_plane_ids=[bundle[x]['fixture_output_plane_id'] for x in ['forward','reverse']],
                        reference_plane_transfer_evidence='SYNTHETIC identical connector mating planes, no adapter/cable')
    with (out/'review.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=['frequency_hz',*REVIEW_NUMBERS,*REVIEW_FLAGS]);writer.writeheader()
        for frequency in f:
            writer.writerow(dict(frequency_hz=frequency,**{key:60 for key in REVIEW_NUMBERS if key.endswith('snr_db')},
                                 direct_pickup_db=-60,repeatability_db=.01,uncertainty_db=.2,**{key:'true' for key in REVIEW_FLAGS}))
    bundle['review']=spec('review.csv',configuration_id=meta['configuration_id'],evidence='SYNTHETIC illustrative .2 dB bound; not measured')
    write_json(out/'bundle.json',bundle);write_json(out/'metadata.json',meta)
    write_json(out/'expected.json',dict(data_kind='SYNTHETIC',frequency_hz=f.tolist(),zt_real_ohm=zt.real.tolist(),zt_imag_ohm=zt.imag.tolist()))
    return out/'forward_transfer.s2p',out/'metadata.json',zt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();create(args.out)
    print(f'SYNTHETIC bundle created: {args.out}')
