"""A17/C10: continue two guide webs; round outside, inside and end roots.

Frozen A16 input. Separate outputs. Same resin, hardware and print quantities.
Requires separate saved-geometry and strength validation; no release approval.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
import FreeCAD as A,Part,MeshPart
R=Path(__file__).resolve().parents[1];P=R/'mechanical/assembly_A16_DRAFT';V=A.Vector
ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(R/'mechanical/assembly_A17_DRAFT'));args=ap.parse_args()
O=Path(args.out);O.mkdir(parents=True,exist_ok=True);(O/'parts').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=P/'RFCP_A16_Integrated_DRAFT.FCStd';expected='de06004040260944b5d0b273f6d03324cb95ff67584b03bc914ae1985cae25cc'
assert sha(native)==expected,'A16 source changed; review first'
d=A.openDocument(str(native));S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')};old={n:s.copy() for n,s in S.items()}
M=json.loads((P/'mesh.json').read_text());prior=json.loads((P/'build_report.json').read_text())
def mv(s,x=0,y=0,z=0):q=s.copy();q.translate(V(x,y,z));return q
frame=mv(S['Cable1_Frame'],z=118.65)
# The inner guide root originally ended at Y12, halfway along the rail.
# Extend only its rear 5 mm datum web; keep Z17 sliding datum and Z32 faces.
frame=frame.fuse(Part.makeBox(13,12.5,5,V(-44,12,12))).fuse(Part.makeBox(13,12.5,5,V(31,12,12))).removeSplitter()
edges=[];edge_bounds=[]
for e in frame.Edges:
 b=e.BoundBox
 if b.XLength<1e-6 and b.ZLength<1e-6 and abs(b.ZMin-17)<1e-6 and b.YMin>=4.99 and b.YMax<=20.01 and any(abs(abs(b.XMin)-x)<1e-6 for x in [37.7,60.3]) and b.YMin<5.01:
  edges.append(e);edge_bounds.append([b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax])
assert len(edges)==4
frame=frame.makeFillet(2.5,edges).removeSplitter()
# Round the remaining inward tensile roots below the moving yoke's Z18 back.
# Radius 0.75 ends at Z17.75, retaining the original Z>=18 sliding surfaces.
inner_edges=[]
for e in frame.Edges:
 b=e.BoundBox
 if b.XLength<1e-6 and b.ZLength<1e-6 and abs(b.ZMin-17)<1e-6 and abs(b.YMin-5)<1e-6 and abs(b.YMax-20)<1e-6 and any(abs(abs(b.XMin)-x)<1e-6 for x in [41.2,56.8]):inner_edges.append(e)
assert len(inner_edges)==4
frame=frame.makeFillet(.75,inner_edges).removeSplitter()
end_edges=[]
for e in frame.Edges:
 b=e.BoundBox
 if b.ZLength<1e-6 and abs(b.ZMin-17)<1e-6 and b.YLength<1e-6 and any(abs(b.YMin-y)<1e-6 for y in [5,20]) and b.XLength>1e-6 and b.XMin>-64 and b.XMax<64 and (b.XMax<-34 or b.XMin>34):end_edges.append(e)
assert len(end_edges)==24
frame=frame.makeFillet(.75,end_edges).removeSplitter()
assert frame.isValid() and len(frame.Solids)==1
for k,z in [(1,-118.65),(2,121.35)]:S[f'Cable{k}_Frame']=mv(frame,z=z)
status='DRAFT - NOT FOR FABRICATION; A17/C10 local guide-root candidate'
out=A.newDocument('RFCP_A17_C10_DRAFT');mesh={};changes=[]
for n,s in S.items():
 meta={k:v for k,v in M[n].items() if k not in ['vertices','triangles']}
 if n in ['Cable1_Frame','Cable2_Frame']:meta.update(revision='A17',color='#147d80')
 obj=out.addObject('PartDesign::Feature',n);obj.Shape=s
 for key,val in [('Status',status),('DisplayColorHex',meta['color']),('Group',meta['group'])]:obj.addProperty('App::PropertyString',key);setattr(obj,key,val)
 verts,tris=s.tessellate(.2);mesh[n]=dict(vertices=[list(v) for v in verts],triangles=tris,**meta)
 if n in ['Cable1_Frame','Cable2_Frame']:changes.append(dict(part=n,old_volume_mm3=old[n].Volume,new_volume_mm3=s.Volume,added_mm3=s.cut(old[n]).Volume,removed_mm3=old[n].cut(s).Volume,valid=s.isValid(),solids=len(s.Solids)))
out.recompute();out.saveAs(str(O/'RFCP_A17_Integrated_DRAFT.FCStd'))
Part.makeCompound(list(S.values())).exportStep(str(O/'RFCP_A17_Integrated_DRAFT.step'))
(O/'mesh.json').write_text(json.dumps(mesh,separators=(',',':')))
for p in (P/'parts').iterdir():
 if p.suffix.lower() in ['.stl','.step'] and p.stem!='C09_Frame_DRAFT':shutil.copy2(p,O/'parts'/p.name)
frame.exportStep(str(O/'parts/C10_Frame_DRAFT.step'));b=frame.BoundBox
MeshPart.meshFromShape(Shape=mv(frame,-b.XMin,-b.YMin,-b.ZMin),LinearDeflection=.08,AngularDeflection=.12,Relative=False).write(str(O/'parts/C10_Frame_DRAFT.stl'))
manifest=[]
for r in prior['parts']:
 q=dict(r);q['file']='C10_Frame_DRAFT.stl' if r['id']=='P06' else r['file'];q['sha256']=sha(O/'parts'/q['file']);q['changed_from_A16']=r['id']=='P06';manifest.append(q)
assert len(manifest)==15 and sum(r['quantity'] for r in manifest)==20
report=dict(classification='CALCULATED_LOCAL_ROOT_SUPPORT_CANDIDATE',status=status,freecad=A.Version(),source_native_sha256=expected,source_hashes={str(native.relative_to(R)):expected,str(Path(__file__).relative_to(R)):sha(Path(__file__))},native_sha256=sha(O/'RFCP_A17_Integrated_DRAFT.FCStd'),changed_objects=changes,parts=manifest,fastener_changes=[],material_changes=[],fillet_radius_mm=2.5,inner_root_radius_mm=.75,root_end_radius_mm=.75,root_end_edge_count=len(end_edges),original_edge_bounds_mm=edge_bounds,web_extension_boxes_mm=[[-44,12,12,13,12.5,5],[31,12,12,13,12.5,5]],source_native_unchanged=sha(native)==expected,limits=['Separate saved-CAD assembly checks and structural simulations are required.','Not a physical strength or RF qualification.','No supplier action or manufacturing approval performed.'])
(O/'build_report.json').write_text(json.dumps(report,indent=2));assert report['source_native_unchanged'];print(json.dumps(dict(out=str(O),changes=changes)))
