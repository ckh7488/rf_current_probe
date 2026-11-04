"""Independent saved-CAD tool-access comparison, not workshop/RF qualification.
Read only product CAD. FreeCADCmd 1.0.2. Run again after A11 exists.
"""
from pathlib import Path
import json, hashlib, itertools, math
import FreeCAD as A, Part
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;V=A.Vector
def mv(s,x=0,y=0,z=0):
 q=s.copy();q.translate(V(x,y,z));return q
def volume(a,b):return a.common(b).Volume if a.BoundBox.intersect(b.BoundBox) else 0.
def collisions(s,obs):
 return [dict(part=n,overlap_mm3=round(v,7)) for n,b in obs.items() if (v:=volume(s,b))>1e-4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def solder_gauge(x,y,z):
 tip=Part.makeCylinder(.8,6,V(x,y,z))
 taper=Part.makeCone(.8,3,12,V(x,y,z+6))
 stem=Part.makeCylinder(3,50,V(x,y,z+18))
 return tip.fuse(taper).fuse(stem)
result={'classification':'CALCULATED_SAVED_CAD_TOOL_GAUGES_NOT_REAL_TOOLS',
 'script_sha256':sha(Path(__file__)), 'revisions':{},
 'limits':['These are specified generic tool/connector gauges, not manufacturer tool drawings.',
 'No thermal, hand dexterity, solder splash, torque, print variation or RF measurement.',
 'Keeper +/-0.635 shift represents nominal core depth range only; other product tolerances are not combined.']}
for rev in ['A10','A11']:
 p=R/f'mechanical/assembly_{rev}_DRAFT/RFCP_{rev}_Integrated_DRAFT.FCStd'
 if not p.exists():continue
 d=A.openDocument(str(p));S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')}
 row={'native_sha256':sha(p),'tools':[]}
 for shift in [-.635,0,.635]:
  Q={n:(mv(s,z=shift) if n=='LowerKeeper' else s) for n,s in S.items()}
  # Same head SMA connector size as prior manufacturing audit. Nominal SMA
  # threads start forward of the laminate; exclude the SMA itself deliberately.
  gauge=Part.makeCylinder(8,45,V(0,-49,12))
  row['tools'].append(dict(operation='head_SMA_D16x45',keeper_z_shift_mm=shift,
    collisions=collisions(gauge,{n:s for n,s in Q.items() if n!='SMAEnvelope'})))
  for x,tag in [(-1.27,'Splus'),(1.27,'Sminus')]:
   row['tools'].append(dict(operation=tag+'_tapered_solder_tool',keeper_z_shift_mm=shift,
    collisions=collisions(solder_gauge(x,-38.5,6.8),{n:s for n,s in Q.items() if n not in ['PCB','Winding']})))
 # Both M2 screwdrivers and keeper tools, over a full long shaft.
 for x in [-14.5,14.5]:
  gauge=Part.makeCylinder(2,85,V(x,-60.5,8))
  row['tools'].append(dict(operation='PCB_M2_D4x85_driver',x_mm=x,
   collisions=collisions(gauge,{n:s for n,s in S.items() if n!='PCBScrews'})))
 for side in [-1,1]:
  for x in [-37,37]:
   gauge=Part.makeCylinder(4,65,V(x,side*23,23.8))
   exclude='LowerKeeperScrews' if side<0 else 'UpperKeeperScrews'
   row['tools'].append(dict(operation='keeper_M3_D8x65_driver',x_mm=x,y_mm=side*23,
    collisions=collisions(gauge,{n:s for n,s in S.items() if n!=exclude})))
 row['tool_cases']=len(row['tools']);row['failed_cases']=sum(bool(x['collisions']) for x in row['tools'])
 # Bench plane is a product requirement, not an arbitrary collision specimen.
 row['mount_bench_clearance_mm']={n:round(s.BoundBox.YMin+84,6) for n,s in S.items() if n.startswith('MountScrew')}
 result['revisions'][rev]=row
 print(rev,'tools',row['tool_cases'],'failures',row['failed_cases'],flush=True)
 A.closeDocument(d.Name)
(O/'operation_tools.json').write_text(json.dumps(result,indent=2)+'\n')
print('REPORT',str(O/'operation_tools.json'),flush=True)
