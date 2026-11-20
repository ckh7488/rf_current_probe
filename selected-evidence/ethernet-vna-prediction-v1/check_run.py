"""Reject missing, grossly misconnected or energetically invalid port runs."""
from pathlib import Path
import argparse
import json
import numpy as np

HERE=Path(__file__).resolve().parent
MATES={1:5,2:8,3:11,4:14,5:1,6:17,7:18,8:2,9:19,10:22,11:3,12:20,
       13:21,14:4,15:23,16:24,17:6,18:7,19:9,20:12,21:13,22:10,23:15,24:16}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('name');args=ap.parse_args()
    folder=HERE/'runs'/args.name
    meta=json.loads((folder/'model.json').read_text())
    drive=meta['args']['drive']
    assert 'wall_seconds' in meta, 'Run has not completed its postprocessing'
    with np.load(folder/'results.npz') as values:
        a=np.stack([values['uf_inc_'+str(i)] for i in range(1,25)],axis=1)
        b=np.stack([values['uf_ref_'+str(i)] for i in range(1,25)],axis=1)
        assert np.isfinite(a).all() and np.isfinite(b).all()
        source=a[:,drive-1]
        assert np.min(abs(source))>1e-20
        through=abs(b[0,MATES[drive]-1]/source[0])
        energy=np.sum(abs(b)**2,axis=1)/np.sum(abs(a)**2,axis=1)
        off=a.copy();off[:,drive-1]=0
        unwanted=np.max(abs(off)/abs(source[:,None]))
        duration=values['u_time_'+str(drive)][-1]*1e9
    checks={'driven_port':drive,'same_net_output':MATES[drive],
            'same_net_transmission_at_1mhz_linear':float(through),
            'max_total_outgoing_to_incident_power':float(energy.max()),
            'max_passive_incident_relative_to_source':float(unwanted),
            'recorded_duration_ns':float(duration)}
    checks['pass']=bool(.8<through<1.15 and energy.max()<1.10 and unwanted<.25 and duration>2)
    (folder/'run-check.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks))
    assert checks['pass'], 'Run failed the basic physical/numerical check'


if __name__=='__main__':main()
