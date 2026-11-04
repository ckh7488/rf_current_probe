"""A18/C10: remove acute underside base fins flagged by JLC. Separate candidate.

Uses frozen A17 and explicit reviewed cutter prisms. No vendor actions.
The complete upper functional geometry and unchanged print files are retained.
Saved-CAD, full surface thickness screening, assembly and FEA are separate.
"""
from pathlib import Path
import argparse, hashlib, json, shutil
import FreeCAD as A, Part, MeshPart
R=Path(__file__).resolve().parents[1];P=R/'mechanical/assembly_A17_DRAFT';V=A.Vector
ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(R/'mechanical/assembly_A18_DRAFT'));args=ap.parse_args()
O=Path(args.out);O.mkdir(parents=True,exist_ok=True);(O/'parts').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
specfile=R/'mechanical/base_A18_tip_cuts.json';spec=json.loads(specfile.read_text(encoding='utf-8'))
native=P/'RFCP_A17_Integrated_DRAFT.FCStd'
assert sha(native)==spec['source_native_sha256'],'A17 changed; review before rebuilding'
d=A.openDocument(str(native));S={o.Name:o.Shape.copy() for o in d.Objects if hasattr(o,'Shape')};old={n:s.copy() for n,s in S.items()}
M=json.loads((P/'mesh.json').read_text(encoding='utf-8'));prior=json.loads((P/'build_report.json').read_text(encoding='utf-8'))
changes=[]
for n,cuts in spec['parts'].items():
    tools=[]
    for c in cuts:
        points=[V(x,c['y_min_mm'],z) for x,z in c['polygon_xz_mm']]
        tools.append(Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(0,c['y_max_mm']-c['y_min_mm'],0)))
    cutter=tools[0].multiFuse(tools[1:]).removeSplitter()
    S[n]=old[n].cut(cutter).removeSplitter()
    for x,y,z,dx,dy,dz in spec.get('support_boxes_mm',{}).get(n,[]):
        S[n]=S[n].fuse(Part.makeBox(dx,dy,dz,V(x,y,z))).removeSplitter()
    assert S[n].isValid() and len(S[n].Solids)==1,n
    changes.append(dict(part=n,old_volume_mm3=old[n].Volume,new_volume_mm3=S[n].Volume,added_mm3=S[n].cut(old[n]).Volume,removed_mm3=old[n].cut(S[n]).Volume,cutters=len(cuts)))
    print('BASE',n,changes[-1],flush=True)
status='DRAFT - NOT FOR FABRICATION; A18/C10 base thin-fin correction candidate'
out=A.newDocument('RFCP_A18_C10_DRAFT');mesh={}
for n,s in S.items():
    meta={k:v for k,v in M[n].items() if k not in ['vertices','triangles']}
    if n in spec['parts']:meta.update(revision='A18',color='#147d80')
    obj=out.addObject('PartDesign::Feature',n);obj.Shape=s
    for k,v in [('Status',status),('DisplayColorHex',meta['color']),('Group',meta['group'])]:obj.addProperty('App::PropertyString',k);setattr(obj,k,v)
    vertices,triangles=s.tessellate(.2);mesh[n]=dict(vertices=[list(v) for v in vertices],triangles=triangles,**meta)
out.recompute();out.saveAs(str(O/'RFCP_A18_Integrated_DRAFT.FCStd'))
Part.makeCompound(list(S.values())).exportStep(str(O/'RFCP_A18_Integrated_DRAFT.step'))
(O/'mesh.json').write_text(json.dumps(mesh,separators=(',',':')),encoding='utf-8')
names={'P05':'BaseCenter','P14':'BaseFront','P15':'BaseRear'}
oldfiles={r['file'] for r in prior['parts'] if r['id'] in names}
for p in (P/'parts').iterdir():
    if p.suffix.lower() in ['.stl','.step'] and p.with_suffix('.stl').name not in oldfiles:shutil.copy2(p,O/'parts'/p.name)
parts=[]
for r in prior['parts']:
    row=dict(r);row['changed_from_A17']=r['id'] in names
    row['changed_from_A16']=r['id'] in ['P05','P06','P14','P15']
    row['changed_from_A15']=r['id'] in ['P05','P06','P14','P15']
    if r['id'] in names:
        n=names[r['id']];row['file']=n+'_A18_DRAFT.stl';s=S[n];s.exportStep(str(O/'parts'/Path(row['file']).with_suffix('.step')))
        b=s.BoundBox;q=s.copy();q.translate(V(-b.XMin,-b.YMin,-b.ZMin))
        MeshPart.meshFromShape(Shape=q,LinearDeflection=.08,AngularDeflection=.12,Relative=False).write(str(O/'parts'/row['file']))
    row['sha256']=sha(O/'parts'/row['file']);parts.append(row)
assert len(parts)==15 and sum(r['quantity'] for r in parts)==20
report=dict(classification='CALCULATED_BASE_THIN_FIN_CORRECTION',status=status,freecad=A.Version(),source_native_sha256=sha(native),source_hashes={str(p.relative_to(R)):sha(p) for p in [native,Path(__file__),specfile]},native_sha256=sha(O/'RFCP_A18_Integrated_DRAFT.FCStd'),changed_objects=changes,parts=parts,material_changes=[],additional_fasteners=0,limits=['Native inherits legacy hardware placement from A17; current DEC-066 standard bolt assembly is supplied separately.','No vendor upload, risk acceptance, payment or production approval.','Separate geometry, thickness and load verification is required.'])
(O/'build_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert sha(native)==spec['source_native_sha256']
print('SAVED',str(O),flush=True)
