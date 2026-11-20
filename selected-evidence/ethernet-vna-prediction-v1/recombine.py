"""Attach circuit blocks to the saved PCB response without rerunning openEMS."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import skrf as rf
from analyze import observables,csv_traces
from network import assembled

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--parameters',type=Path,default=HERE/'electrical-assumptions.json')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise SystemExit('Choose a new output directory.')
    parameters=json.loads(args.parameters.read_text())
    with np.load(HERE/'prediction-v1/pcb-network.npz') as data:f,pcb=data['frequency_hz'],data['s']
    networks={mode:assembled(pcb,f,mode,parameters) for mode in ['open','match','loopback']}
    args.output.mkdir(parents=True)
    csv_traces(args.output/'predicted-observables.csv',f,observables(networks))
    for mode,s in networks.items():
        rf.Network(frequency=rf.Frequency.from_f(f,unit='Hz'),s=s,z0=50).write_touchstone(str(args.output/(mode+'-sma')))
    parameter_hash=hashlib.sha256(args.parameters.read_bytes()).hexdigest()
    frozen_hash=next(item['sha256'] for item in json.loads((HERE/'input-freeze-v3/manifest.json').read_text())['files'] if item['file']=='electrical-assumptions.json')
    receipt={'classification':'SIMULATED_CIRCUIT_RECOMBINATION','pcb_geometry_recomputed':False,
             'new_rf_measurements_used':False if parameter_hash==frozen_hash else None,
             'parameters_are_frozen_v1':parameter_hash==frozen_hash,'frequency_hz':[float(f[0]),float(f[-1])],
             'parameters_sha256':parameter_hash,
             'pcb_network_sha256':hashlib.sha256((HERE/'prediction-v1/pcb-network.npz').read_bytes()).hexdigest()}
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
