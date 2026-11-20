"""Check the retained simulation inputs, one waveform set and final results."""
from pathlib import Path
import argparse
import hashlib
import json

HERE=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(numerical=False):
    retained=json.loads((HERE/'RETENTION.json').read_text())
    for item in retained['retained_files']:
        path=HERE/item['file']
        assert path.is_file() and digest(path)==item['sha256'],item['file']
    freeze=HERE/'input-freeze-v3/manifest.json'
    assert digest(freeze)==retained['original_input_manifest_sha256']
    for item in json.loads(freeze.read_text())['files']:
        assert digest(HERE/item['file'])==item['sha256'],item['file']
    output=HERE/'prediction-v1/output-receipt.json'
    assert digest(output)==retained['original_output_receipt_sha256']
    receipt=json.loads(output.read_text())
    omitted={item['file']:item['sha256'] for item in retained['omitted_derived_files']}
    for item in receipt['files']:
        relative=item['file'].replace('\\','/')
        path=HERE/relative
        if relative in omitted:
            assert item['sha256']==omitted[relative],relative
        else:
            assert digest(path)==item['sha256'],relative
    grids=set()
    for drive,item in enumerate(receipt['raw_results'],1):
        folder=HERE/item['folder'].replace('\\','/')
        assert digest(folder/'results.npz')==item['results_sha256']
        assert digest(folder/'model.json')==item['model_sha256']
        model=json.loads((folder/'model.json').read_text())
        assert model['args']['drive']==drive and model['args']['metal']=='finite-pec'
        assert json.loads((folder/'run-check.json').read_text())['pass']
        grids.add(digest(folder/'grid.npz'))
    assert len(receipt['raw_results'])==24 and len(grids)==1
    report={'classification':'SIMULATED_RETENTION_CHECK','completed_drives':24,
            'waveform_sets':1,'retained_files':len(retained['retained_files']),
            'new_rf_measurements_used':False,'status':'PASS'}
    if numerical:
        import numpy as np
        from analyze import wave_matrices,observables
        from network import assembled
        folders=[HERE/'runs'/f'nominal-finite-v1-p{i:02d}' for i in range(1,25)]
        with np.load(HERE/'prediction-v1/pcb-network.npz') as data:
            f,pcb=data['frequency_hz'],data['s']
        ff,recovered,_=wave_matrices(folders)
        np.testing.assert_array_equal(f,ff)
        np.testing.assert_allclose(recovered,pcb,atol=1e-12,rtol=1e-10)
        params=json.loads((HERE/'electrical-assumptions.json').read_text())
        curves=observables({mode:assembled(pcb,f,mode,params) for mode in ['open','match','loopback']})
        summary=json.loads((HERE/'prediction-v1/summary.json').read_text())
        for mhz,samples in summary['samples_mhz'].items():
            for key,target in samples.items():
                value=np.interp(float(mhz)*1e6,f,curves[key])
                assert abs(20*np.log10(abs(value))-target['db'])<1e-8
                phase=float(np.angle(value,deg=True))
                assert abs((phase-target['phase_deg']+180)%360-180)<1e-8
        report['saved_matrix_and_four_predictions']='PASS'
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--numerical',action='store_true')
    print(json.dumps(verify(parser.parse_args().numerical),indent=2))
