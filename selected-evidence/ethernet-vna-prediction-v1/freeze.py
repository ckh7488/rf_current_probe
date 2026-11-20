"""Record a dated input/code receipt without including any new VNA traces."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import argparse
import shutil

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', default='input-freeze-v1')
    args = ap.parse_args()
    folder = HERE/args.name
    if folder.exists():
        raise SystemExit('Existing input freeze is preserved; use a new revision.')
    folder.mkdir()
    sources = [HERE/name for name in ['prepare.py','run.py','network.py','analyze.py','check_mesh.py',
                                      'check_run.py','batch.py','freeze.py','check_pipeline.py',
                                      'compute-plan.json',
                                      'prediction-plan.json','electrical-assumptions.json']]
    sources += list((HERE/'input').glob('*'))
    entries = []
    for source in sorted(sources):
        if not source.is_file():
            continue
        target = folder/source.relative_to(HERE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        entries.append({'file': source.relative_to(HERE).as_posix(), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'bytes': source.stat().st_size})
    runtime=HERE.parents[1]/'tools/openems/v0.37.0-rc2/runtime/openEMS'
    tools=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
           for p in [runtime/'openEMS.exe',runtime/'CSXCAD.dll']]
    manifest = {'created_at_kst': datetime.now(timezone(timedelta(hours=9))).isoformat(),
                'purpose': 'Independent forward-model inputs before new RF measurements',
                'new_rf_measurements_used': False, 'files': entries,'runtime':tools,
                'changes': 'Any later numerical/model revision gets a separate receipt; this folder is not overwritten.'}
    path = folder/'manifest.json'
    path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (folder/'SHA256.txt').write_text(digest+'  manifest.json\n')
    print(json.dumps({'freeze': str(folder), 'manifest_sha256': digest, 'files': len(entries), 'new_rf_measurements_used': False}))


if __name__ == '__main__':
    main()
