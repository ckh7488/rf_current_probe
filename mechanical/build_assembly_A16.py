"""A16/C09: strengthen the lead-screw support and remove thin base fins.

FreeCAD 1.0.2 bundled Python. Frozen A15 input; output in a separate directory.
No supplier actions. Verification and structural results are separate artifacts.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
import FreeCAD as A,Part,MeshPart
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(R/'mechanical/assembly_A16_DRAFT'));args=ap.parse_args()
O=Path(args.out);O.mkdir(parents=True,exist_ok=True);(O/'parts').mkdir(exist_ok=True)
P=R/'mechanical/assembly_A15_DRAFT';V=A.Vector
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=P/'RFCP_A15_Integrated_DRAFT.FCStd';expected='93fedf3e1d47e9e2216d6ec3c0e577abcb1fc74b2f57cdcceaa7553fc308dece'
assert sha(native)==expected,'A15 source changed; review first'
d=A.openDocument(str(native));S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')};old={n:s.copy() for n,s in S.items()}
M=json.loads((P/'mesh.json').read_text());prior=json.loads((P/'build_report.json').read_text())
def box(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
def fuse(ss):return ss[0].multiFuse(ss[1:]).removeSplitter() if len(ss)>1 else ss[0]
status='DRAFT - NOT FOR FABRICATION; A16/C09 engineering review candidate'

# The added backbone remains behind the original Z=12 rear datum wall.
# It joins the thrust seat to the existing right rear rib; Y=-27 leaves
# the established lift25/outward mounting-knob corridor below it untouched.
frame=mv(S['Cable1_Frame'],z=118.65)
backbone=box(71,-27,0,20,77,12)
frame=frame.fuse(backbone).removeSplitter()
for k,z in [(1,-118.65),(2,121.35)]:S[f'Cable{k}_Frame']=mv(frame,z=z)

# Merge the flat 0.65 mm fin into the front rim. Nothing above the original
# pocket ceiling Y=-77 or in a screw-seat/tool aperture is modified.
S['BaseFront']=S['BaseFront'].fuse(box(-75,-88,-129,170,11,3)).removeSplitter()
# Widen the 1.4 mm strips away from the protected PCB-post/mount interfaces,
# and merge the isolated 0.5 mm right-hand fin into a 3 mm web.
cleanup=fuse([box(-75,-88,-19,170,11,3),box(-75,-88,60,170,11,3),box(60,-88,63,3,11,15)])
S['BaseCenter']=S['BaseCenter'].fuse(cleanup).removeSplitter()
changed=['BaseFront','BaseCenter','Cable1_Frame','Cable2_Frame']
for n in changed:assert S[n].isValid() and len(S[n].Solids)==1,n

out=A.newDocument('RFCP_A16_C09_DRAFT');mesh={};changes=[]
for n,s in S.items():
    meta={k:v for k,v in M[n].items() if k not in ['vertices','triangles']}
    if n in changed:meta.update(revision='A16',color='#147d80')
    obj=out.addObject('PartDesign::Feature',n);obj.Shape=s
    for key,val in [('Status',status),('DisplayColorHex',meta['color']),('Group',meta['group'])]:obj.addProperty('App::PropertyString',key);setattr(obj,key,val)
    verts,tris=s.tessellate(.2);mesh[n]=dict(vertices=[list(v) for v in verts],triangles=tris,**meta)
    if n in changed:changes.append(dict(part=n,old_volume_mm3=old[n].Volume,new_volume_mm3=s.Volume,added_mm3=s.cut(old[n]).Volume,removed_mm3=old[n].cut(s).Volume,valid=s.isValid(),solids=len(s.Solids)))
out.recompute();out.saveAs(str(O/'RFCP_A16_Integrated_DRAFT.FCStd'))
Part.makeCompound(list(S.values())).exportStep(str(O/'RFCP_A16_Integrated_DRAFT.step'))
(O/'mesh.json').write_text(json.dumps(mesh,separators=(',',':')))
replaced={'BaseFront_A15_DRAFT','BaseCenter_A15_DRAFT','C08_Frame_DRAFT'}
for p in (P/'parts').iterdir():
    if p.suffix.lower() in ['.stl','.step'] and p.stem not in replaced:shutil.copy2(p,O/'parts'/p.name)
for name,s in {'BaseFront_A16_DRAFT':S['BaseFront'],'BaseCenter_A16_DRAFT':S['BaseCenter'],'C09_Frame_DRAFT':frame}.items():
    s.exportStep(str(O/'parts'/(name+'.step')));b=s.BoundBox
    MeshPart.meshFromShape(Shape=mv(s,-b.XMin,-b.YMin,-b.ZMin),LinearDeflection=.08,AngularDeflection=.12,Relative=False).write(str(O/'parts'/(name+'.stl')))
replacement={'P05':'BaseCenter_A16_DRAFT.stl','P06':'C09_Frame_DRAFT.stl','P14':'BaseFront_A16_DRAFT.stl'}
manifest=[]
for r in prior['parts']:
    q=dict(r);q['file']=replacement.get(r['id'],r['file']);q['sha256']=sha(O/'parts'/q['file']);q['changed_from_A15']=r['id'] in replacement
    # "changed" remains relative to submitted A14, so P15 is still a replacement.
    manifest.append(q)
assert len(manifest)==15 and sum(r['quantity'] for r in manifest)==20
report=dict(classification='CALCULATED_SAVED_CAD_STRENGTH_REVISION',status=status,freecad=A.Version(),source_native_sha256=expected,source_hashes={str(native.relative_to(R)):expected,str(Path(__file__).relative_to(R)):sha(Path(__file__))},native_sha256=sha(O/'RFCP_A16_Integrated_DRAFT.FCStd'),changed_objects=changes,parts=manifest,fastener_changes=[],backbone_bounds_mm=[71,-27,0,91,50,12],source_native_unchanged=sha(native)==expected,limits=['See separate saved-CAD geometry and structural validation.','No supplier upload/payment/manufacturing approval performed.'])
(O/'build_report.json').write_text(json.dumps(report,indent=2))
assert report['source_native_unchanged']
print(json.dumps(dict(out=str(O),native_sha256=report['native_sha256'],changes=changes)),flush=True)
