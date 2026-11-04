"""Read-only bounded check of a tilted PCB insertion route."""
from pathlib import Path
import json
import FreeCAD as A,Part
P=Path(__file__).resolve().parent;R=P.parent;V=A.Vector
d=A.openDocument(str(R/'mechanical/assembly_A13_DRAFT/RFCP_A13_Integrated_DRAFT.FCStd'))
S={n:d.getObject(n).Shape for n in ['LowerBody','FixedCore','PCBNuts','PCB','SMAEnvelope']}
out=[]
for angle,dy in [(-20,-1.6),(-25,-1.6),(-30,-1.6)]:
 positions=[(a,0,0) for a in [angle*i/10 for i in range(11)]]+[(angle,dy*i/10,0) for i in range(1,11)]+[(angle,dy,z*4) for z in range(1,11)]
 bad=[]
 for a,y,z in positions:
  for n in ['PCB','SMAEnvelope']:
   s=S[n].copy();s.rotate(V(0,-36,5.55),V(1,0,0),a);s.translate(V(0,y,z))
   for b in ['LowerBody','FixedCore','PCBNuts']:
    v=s.common(S[b]).Volume if s.BoundBox.intersect(S[b].BoundBox) else 0
    if v>1e-4:bad.append(dict(angle=a,y=y,z=z,part=n,obstacle=b,volume_mm3=v))
 out.append(dict(angle=angle,dy=dy,positions=len(positions),collisions=bad));print(angle,dy,len(bad),flush=True)
(P/'guide_sources/pcb_insertion_review.json').write_text(json.dumps(out,indent=2))
