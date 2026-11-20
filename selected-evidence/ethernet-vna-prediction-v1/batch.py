"""Run a persistent local extraction queue and preserve every run and receipt.

This worker only computes local files. It neither reads new VNA data nor writes
to the ATLAS publication checkout.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOLVER=ROOT/'tools/openems/venv/Scripts/python.exe'
POST=ROOT/'.venv/Scripts/python.exe'


def stamp():return datetime.now(timezone(timedelta(hours=9))).isoformat()


class ExistingProcess:
    def __init__(self,pid):
        self.pid=pid
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32]
        self.kernel.OpenProcess.restype=ctypes.c_void_p
        self.kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint32)]
        self.kernel.GetExitCodeProcess.restype=ctypes.c_int
        self.handle=self.kernel.OpenProcess(0x100000|0x1000,False,pid)
        if not self.handle:raise OSError(ctypes.get_last_error(),'Cannot adopt solver process')
    def poll(self):
        code=ctypes.c_uint32()
        if not self.kernel.GetExitCodeProcess(self.handle,ctypes.byref(code)):
            raise OSError(ctypes.get_last_error(),'Cannot inspect adopted solver')
        return None if code.value==259 else code.value


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--prefix',required=True)
    ap.add_argument('--metal',choices=['pec-sheet','copper-sheet','finite-pec'],required=True)
    ap.add_argument('--freeze',required=True)
    ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--threads',type=int,default=8)
    ap.add_argument('--adopt-port1-pid',type=int)
    ap.add_argument('--self-check-only',action='store_true')
    args=ap.parse_args()
    manifest_path=HERE/args.freeze/'manifest.json'
    receipt=json.loads(manifest_path.read_text())
    plan=json.loads((HERE/'compute-plan.json').read_text())
    assert args.prefix==plan['primary_run_prefix'] and args.metal==plan['metal']
    assert args.workers==plan['concurrent_primary_jobs'] and args.threads==plan['threads_per_job']
    def verify_inputs():
        for entry in receipt['files']:
            actual=hashlib.sha256((HERE/entry['file']).read_bytes()).hexdigest()
            assert actual==entry['sha256'],'Frozen input changed: '+entry['file']
        for entry in receipt['runtime']:
            assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['sha256'],'Solver runtime changed'
    verify_inputs()
    subprocess.run([str(POST),str(HERE/'analyze.py'),'--self-check-only'],check=True,cwd=ROOT)
    if args.self_check_only:
        print('Batch preflight passed',flush=True);return
    state={'created_at_kst':stamp(),'status':'RUNNING','args':vars(args),
           'input_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
           'new_rf_measurements_used':False,'jobs':[]}
    running={};pending=[];failed=False
    for drive in range(1,25):
        name=args.prefix+f'{drive:02d}'
        folder=HERE/'runs'/name
        job={'drive':drive,'name':name,'status':'PENDING'}
        state['jobs'].append(job)
        if (folder/'results.npz').exists():
            subprocess.run([str(POST),str(HERE/'check_run.py'),name],check=True,cwd=ROOT)
            job['status']='COMPLETE'
        elif drive==1 and args.adopt_port1_pid:
            process=ExistingProcess(args.adopt_port1_pid)
            running[drive]=(process,None)
            job.update(status='RUNNING',pid=process.pid,adopted=True)
        else:
            assert not folder.exists(),'Incomplete run needs a fresh prefix: '+name
            pending.append(drive)
    def save():
        state['updated_at_kst']=stamp()
        state['completed']=sum(j['status']=='COMPLETE' for j in state['jobs'])
        tmp=HERE/'queue-status.tmp.json'
        tmp.write_text(json.dumps(state,indent=2)+'\n')
        tmp.replace(HERE/'queue-status.json')
    lock=HERE/'batch.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    # Keep the system awake for this worker; allow the display to sleep.
    execution=ctypes.windll.kernel32.SetThreadExecutionState
    execution.argtypes=[ctypes.c_uint32];execution.restype=ctypes.c_uint32
    execution(0x80000001)
    try:
        save()
        while pending or running:
            while pending and len(running)<args.workers and not failed:
                verify_inputs()
                drive=pending.pop(0);job=state['jobs'][drive-1]
                log=(HERE/(job['name']+'.log')).open('wb')
                command=[str(SOLVER),'-X','utf8','-B',str(HERE/'run.py'),'--name',job['name'],
                         '--drive',str(drive),'--metal',args.metal,'--threads',str(args.threads)]
                process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                                         creationflags=subprocess.CREATE_NO_WINDOW)
                running[drive]=(process,log)
                job.update(status='RUNNING',pid=process.pid,started_at_kst=stamp())
                print(stamp(),'START',job['name'],flush=True)
                save()
            for drive,(process,log) in list(running.items()):
                code=process.poll()
                if code is None:continue
                if log:log.close()
                job=state['jobs'][drive-1]
                job.update(exit_code=code,finished_at_kst=stamp())
                if code==0:
                    checked=subprocess.run([str(POST),str(HERE/'check_run.py'),job['name']],cwd=ROOT)
                    code=checked.returncode
                if code:
                    job['status']='FAILED';failed=True
                    print(stamp(),'FAILED',job['name'],code,flush=True)
                else:
                    job['status']='COMPLETE'
                    print(stamp(),'COMPLETE',job['name'],flush=True)
                del running[drive]
                save()
                subprocess.run([str(POST),str(HERE/'build_preview.py')],cwd=ROOT)
            if failed and not running:
                state['status']='STOPPED_ON_NUMERICAL_OR_EXECUTION_FAILURE';save();return 1
            time.sleep(15)
            save()
        verify_inputs()
        state['status']='ASSEMBLING_NETWORK';save()
        subprocess.run([str(POST),str(HERE/'analyze.py'),'--prefix',args.prefix,'--input-freeze',args.freeze],check=True,cwd=ROOT)
        state['status']='COMPUTED_PENDING_NUMERICAL_REVIEW';save()
        subprocess.run([str(POST),str(HERE/'build_preview.py')],check=True,cwd=ROOT)
        print(stamp(),state['status'],flush=True)
        return 0
    except BaseException as error:
        state['status']='FAILED';state['error']=str(error);save()
        raise
    finally:
        execution(0x80000000)
        lock.unlink(missing_ok=True)


if __name__=='__main__':sys.exit(main() or 0)
