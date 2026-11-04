"""Spot-check displayed rigid paths against saved CAD. Does not qualify assembly."""
from pathlib import Path
import json,hashlib,itertools,sys
import FreeCAD as A,Part
P=Path(__file__).resolve().parent;R=P.parent;sys.path.insert(0,str(P))
from guide_steps import make_steps
V=A.Vector;C=R/'mechanical/assembly_A13_DRAFT';native=C/'RFCP_A13_Integrated_DRAFT.FCStd'
doc=A.openDocument(str(native));S={o.Name:o.Shape for o in doc.Objects if hasattr(o,'Shape')}
S['UpperLidFree']=Part.read(str(C/'UpperLid_UNLOADED_DRAFT.step'))
for i,s in enumerate(S.pop('CalibrationNuts').Solids):S['CalibrationNut'+str(i+1)]=s
mesh=json.loads((C/'mesh.json').read_text());sup=json.loads((P/'guide_sources/geometry_supplements.json').read_text());mesh.update(sup)
steps=make_steps(mesh);result={}
def move(s,p):q=s.copy();q.translate(V(*p));return q
for step in steps:
 if not step['moves']:continue
 # Narrative wire shape is not a deformable wire model; don't certify it as rigid.
 visible=set(step['rest']+step['active']);visible.discard('Winding')
 rows=[];samples=11
 for i in range(samples):
  t=i/(samples-1);ss={}
  for n in visible:
   pos=list(step.get('baseOffsets',{}).get(n,[0,0,0]));path=step['moves'].get(n)
   angle=0;pivot=[0,0,0]
   if path and 'keys' in path:
    keys=path['keys'];k=next((i for i,v in enumerate(keys) if i and v[0]>=t),len(keys)-1);a,b=keys[k-1:k+1];f=max(0,min(1,(t-a[0])/(b[0]-a[0])))
    pos=[v+u+(w-u)*f for v,u,w in zip(pos,a[1],b[1])];angle=a[2]+(b[2]-a[2])*f;pivot=path['pivot']
   elif path:
    lo,hi=path['window'];f=max(0,min(1,(t-lo)/(hi-lo)));pos=[v+f*d for v,d in zip(pos,path['vector'])]
   source=S['UpperLidFree'] if n=='UpperLid' and step.get('freeRaisedLid') else S[n]
   shape=source.copy();shape.rotate(V(*pivot),V(1,0,0),angle);ss[n]=move(shape,pos)
  for a,b in itertools.combinations(sorted(ss),2):
   if a not in step['moves'] and b not in step['moves']:continue
   if a in ['FlatPCB','ReturnCopper','SignalCopper'] and b in ['FlatPCB','ReturnCopper','SignalCopper']:continue
   if not ss[a].BoundBox.intersect(ss[b].BoundBox):continue
   volume=ss[a].common(ss[b]).Volume
   if volume>1e-4:rows.append(dict(t=t,a=a,b=b,volume_mm3=round(volume,5)))
 result[step['id']]=dict(samples=samples,collisions=rows)
 print(step['id'],len(rows),'overlaps',flush=True)
out=dict(classification='SAMPLED_DISPLAY_PATHS_NOT_SWEPT_VOLUME_OR_HAND_TOOL_TEST',native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),steps_source_sha256=hashlib.sha256((P/'guide_steps.py').read_bytes()).hexdigest(),steps=result,limits=['Eleven poses per indicated step, not a continuous swept-volume proof.','Winding excluded: flexible tails and actual turns are not modeled.','Opening flexures use prior A13 path evidence, not this rigid translation checker.','Nominal geometry only; no hands, contact force, friction or print errors.'])
(P/'guide_sources/animation_path_review.json').write_text(json.dumps(out,indent=2)+'\n')
print('BLOCKED',[k for k,v in result.items() if v['collisions']],flush=True)
