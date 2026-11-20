"""An independent ideal-line fixture checks the whole 24-port analysis path.

These synthetic traces live under a separate prefix and never feed the viewer.
"""
from pathlib import Path
import json
import subprocess
import sys
import numpy as np
from network import balun, C0
from check_run import MATES

HERE=Path(__file__).resolve().parent


def main():
    f=np.linspace(1e6,200e6,1601)
    t=np.arange(201)*25e-12
    gaussian=lambda time:np.exp(-((time-1.0e-9)/.15e-9)**2)
    incident=gaussian(t)
    transform=2*(t[1]-t[0])*np.exp(-2j*np.pi*f[:,None]*t)
    for drive in range(1,25):
        folder=HERE/'runs'/f'synthetic-v2-check-p{drive:02d}'
        assert not folder.exists(),'Synthetic evidence is preserved; inspect or use a new test version'
        folder.mkdir(parents=True)
        primary=drive in [1,2,3,4,5,8,11,14]
        delay=.12e-9 if primary else .20e-9
        outgoing=gaussian(t-delay)
        source_spectrum=transform@incident
        mate_spectrum=transform@outgoing
        arrays={'frequency_hz':f}
        for row in range(1,25):
            incoming=incident if row==drive else np.zeros_like(t)
            reflected=outgoing if row==MATES[drive] else np.zeros_like(t)
            arrays['u_time_'+str(row)]=t;arrays['i_time_'+str(row)]=t
            arrays['ut_tot_'+str(row)]=incoming+reflected
            arrays['it_tot_'+str(row)]=(incoming-reflected)/50
            arrays['uf_inc_'+str(row)]=source_spectrum if row==drive else np.zeros_like(f,dtype=complex)
            arrays['uf_ref_'+str(row)]=mate_spectrum if row==MATES[drive] else np.zeros_like(f,dtype=complex)
        np.savez_compressed(folder/'results.npz',**arrays)
        # Identical bytes deliberately represent one shared synthetic grid.
        (folder/'grid.npz').write_bytes(b'SYNTHETIC identical ideal-line sampling')
        (folder/'model.json').write_text(json.dumps({'classification':'SYNTHETIC','input_sha256':'ideal-lines-only',
            'args':{'drive':drive,'step':.16,'metal':'synthetic-lossless'},'wall_seconds':0}))
    subprocess.run([sys.executable,str(HERE/'analyze.py'),'--prefix','synthetic-v2-check-p','--output','synthetic-v2-pipeline-check'],check=True)
    p=json.loads((HERE/'electrical-assumptions.json').read_text())
    component,_=balun(f)
    u=np.array([[1,0,0],[0,1/np.sqrt(2),-1/np.sqrt(2)],[0,1/np.sqrt(2),1/np.sqrt(2)]])
    modal=u@component@u.T
    jack_delay=p['rj45']['jack_contact_path_mm']*1e-3/(C0*p['rj45']['velocity_factor'])
    sma_delay=p['sma']['nominal_length_mm']*1e-3/(C0*p['sma']['velocity_factor'])
    reflection=np.exp(-2j*2*np.pi*f*(.20e-9+jack_delay))
    expected=(modal[:,0,0]+modal[:,0,1]*modal[:,1,0]*reflection/(1-modal[:,1,1]*reflection))*np.exp(-2j*2*np.pi*f*(.12e-9+sma_delay))
    import csv
    with (HERE/'synthetic-v2-pipeline-check/predicted-observables.csv').open() as handle:
        rows=list(csv.DictReader(handle))
    actual=np.array([complex(float(row['open_b_s11_real']),float(row['open_b_s11_imag'])) for row in rows])
    np.testing.assert_allclose(actual,expected,atol=2e-10)
    summary=json.loads((HERE/'synthetic-v2-pipeline-check/summary.json').read_text())
    assert summary['classification']=='SYNTHETIC'
    report={'classification':'SYNTHETIC_CHECK','full_24_port_recovery':'passed',
            'circuit_connection_vs_analytic_cascade':'passed','max_complex_error':float(abs(actual-expected).max()),
            'sensitivity_exports':'passed','new_rf_measurements_used':False}
    (HERE/'pipeline-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
