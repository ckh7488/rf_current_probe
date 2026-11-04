"""A19 centre-base DFM revision, subtractive rounded windows in broad lap plates.

FreeCAD 1.0.2, millimetres. Retains all fasteners, posts, datum heights and
mounting bores. This is not a cure-shrinkage/warpage simulation or warranty.
"""
from pathlib import Path
import argparse,json,hashlib
import FreeCAD as A,Part,MeshPart
R=Path(__file__).resolve().parents[1];V=A.Vector
ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(R/'mechanical/base_A19_DRAFT'));args=ap.parse_args()
O=Path(args.out);(O/'parts').mkdir(parents=True,exist_ok=True)
src=R/'reviews/base_dfm_fix_20260928/RFCP_A18_CurrentHardware_Assembly_DRAFT.FCStd'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='67829f7a524d8b958b5be427cf04ca1c725a494f1633a9e74bc166e044da6c40'
assert sha(src)==expected
d=A.openDocument(str(src));old=d.getObject('BaseCenter').Shape.copy()
def box(x,y,z,dx,dy,dz):return Part.makeBox(dx,dy,dz,V(x,y,z))
def fuse(ss):return ss[0].multiFuse(ss[1:]).removeSplitter() if len(ss)>1 else ss[0]
def rounded_window(x0,z0,x1,z1,r=4):
    y=-90;h=20;w=x1-x0;l=z1-z0
    assert w>=2*r and l>=2*r
    return fuse([box(x0+r,y,z0,w-2*r,h,l),box(x0,y,z0+r,w,h,l-2*r)]+[Part.makeCylinder(r,h,V(x,y,z),V(0,1,0)) for x in [x0+r,x1-r] for z in [z0+r,z1-r]])
windows=[[-75,-59.2,-59,-48],[-33,-59.2,-4,-40],[4,-59.2,33,-40],[57,-59.2,77,-48],[83,-59.2,97,-40],[-56,92,-4,103.2],[4,92,56,103.2],[80,92,97,103.2]]
tools=[rounded_window(*w) for w in windows];new=old.cut(fuse(tools)).removeSplitter()
assert new.isValid() and len(new.Solids)==1
assert new.cut(old).Volume<1e-6
old_bounds=old.BoundBox;new_bounds=new.BoundBox
assert max(abs(a-b) for a,b in zip([old_bounds.XMin,old_bounds.YMin,old_bounds.ZMin,old_bounds.XMax,old_bounds.YMax,old_bounds.ZMax],[new_bounds.XMin,new_bounds.YMin,new_bounds.ZMin,new_bounds.XMax,new_bounds.YMax,new_bounds.ZMax]))<1e-6
obj=d.getObject('BaseCenter');obj.Shape=new;obj.Label='BaseCenter A19 DRAFT - rounded lap windows'
obj.addProperty('App::PropertyString','A19Status');obj.A19Status='DRAFT - engineering review; no cure-warp prediction'
d.recompute();native=O/'RFCP_A19_CurrentHardware_Assembly_DRAFT.FCStd';d.saveAs(str(native))
step=O/'parts/BaseCenter_A19_DRAFT.step';new.exportStep(str(step))
q=new.copy();b=q.BoundBox;q.translate(V(-b.XMin,-b.YMin,-b.ZMin))
stl=O/'parts/BaseCenter_A19_DRAFT.stl';MeshPart.meshFromShape(Shape=q,LinearDeflection=.06,AngularDeflection=.10,Relative=False).write(str(stl))
mesh={}
for label,s in [('before',old),('after',new)]:
    v,t=s.tessellate(.15);mesh[label]=dict(vertices=[list(p) for p in v],triangles=t)
(O/'comparison_mesh.json').write_text(json.dumps(mesh),encoding='utf-8')
report=dict(classification='CALCULATED_SUBTRACTIVE_DFM_CANDIDATE_NOT_WARP_SIMULATION',freecad=A.Version(),source=str(src.relative_to(R)),source_sha256=expected,windows_xz_mm=windows,window_corner_radius_mm=4,old_volume_mm3=old.Volume,new_volume_mm3=new.Volume,volume_reduction_percent=(1-new.Volume/old.Volume)*100,added_volume_mm3=new.cut(old).Volume,removed_volume_mm3=old.cut(new).Volume,additional_fasteners=0,changed_print_types=1,changed_pieces=1,unchanged_print_types=14,print_types_total=15,print_pieces_total=20,material='9600 Resin',files={str(p.relative_to(O)):sha(p) for p in [native,step,stl]},limits=['No supplier quote/approval or physical fit established by this builder.','Broad lap face area is intentionally reduced; hole seats and required contact areas must be verified.','Existing strength results do not automatically apply to A19.'])
(O/'build_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert sha(src)==expected
print(json.dumps(report,indent=2),flush=True)
