"""A15 resin DFM candidate, derived from the frozen A14 assembly.

FreeCAD 1.0.2 Python. Only new A15 output files are written. No supplier upload.
Open, triangulated base webs replace broad asymmetric pocketed plates. Rear
channel ribs stiffen the fixed clamp frame without moving its working guides.
This is a geometry candidate, not a simulation of cure shrinkage or a warranty.
"""
from pathlib import Path
import argparse, hashlib, json, math, shutil
import FreeCAD as A
import Part, MeshPart

R = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('--out', default=str(R/'mechanical/assembly_A15_DRAFT'))
args = ap.parse_args()
O = Path(args.out)
O.mkdir(parents=True, exist_ok=True)
(O/'parts').mkdir(exist_ok=True)
P = R/'mechanical/assembly_A14_DRAFT'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
native = P/'RFCP_A14_Integrated_DRAFT.FCStd'
expected = '400618d82bd9f1d98a7f45a7e3e4bda1664310d61d81435e3d18fd1194b9e2a7'
assert sha(native) == expected, 'Source changed; review before rebuilding.'
sources = {str(p.relative_to(R)): sha(p) for p in [native, P/'mesh.json', Path(__file__)]}
d = A.openDocument(str(native))
S = {o.Name: o.Shape.copy() for o in d.Objects if hasattr(o, 'Shape')}
old = {n:s.copy() for n,s in S.items()}
M = json.loads((P/'mesh.json').read_text())
V = A.Vector
STATUS = 'DRAFT - NOT FOR FABRICATION; A15 resin DFM candidate'
BASES = ['BaseFront', 'BaseCenter', 'BaseRear']
CHANGED = BASES + ['Cable1_Frame', 'Cable2_Frame']

def box(x,y,z,dx,dy,dz):
    return Part.makeBox(dx,dy,dz,V(x,y,z))

def mv(s,x=0,y=0,z=0):
    q=s.copy();q.translate(V(x,y,z));return q

def fuse(ss):
    return ss[0].multiFuse(ss[1:]).removeSplitter() if len(ss)>1 else ss[0]

def beam_xz(p,q,width,y0,height):
    dx,dz=q[0]-p[0],q[1]-p[1]
    length=math.hypot(dx,dz);nx,nz=-dz*width/(2*length),dx*width/(2*length)
    pts=[V(p[0]+nx,y0,p[1]+nz),V(q[0]+nx,y0,q[1]+nz),
         V(q[0]-nx,y0,q[1]-nz),V(p[0]-nx,y0,p[1]-nz)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,height,0))

def rounded_xy(x,y,w,h,r,z,depth):
    # Explicit analytic primitives, so the corner radius is reproducible.
    return fuse([box(x+r,y,z,w-2*r,h,depth),box(x,y+r,z,w,h-2*r,depth)] +
                [Part.makeCylinder(r,depth,V(xx,yy,z))
                 for xx in [x+r,x+w-r] for yy in [y+r,y+h-r]])

mounts=[(-48,75),(48,75),(-54,-114.65),(80,-114.65),(-54,125.35),(80,125.35)]
protected=[box(-84,-100,seam-16,188,110,32) for seam in [-50,94]]
protected += [box(x-12,-100,z-12,24,110,24) for x,z in mounts]
protected += [box(x-13,-100,z-13,26,110,26) for x in [-65,65] for z in [-32,44.7]]
# Preserve a complete floor strip below each original registration shoulder.
# An unsupported ledge merely touching the outer rim at an edge is not a valid
# printable connection, even when the BRep's generic validity check passes.
protected += [box(-84,-100,off+38,188,110,13) for off in [-118.65,121.35]]
protected += [box(-73,-100,off-12,14,110,63) for off in [-118.65,121.35]]
protect=fuse(protected)
base_metrics=[]
for name in BASES:
    s=old[name];b=s.BoundBox
    # Entire original structure above its mounting plane is retained.
    top=s.common(box(-200,-72,-200,400,200,500))
    floor=box(-83,-88,b.ZMin,186,16,b.ZLength)
    nx=4;nz=4 if name=='BaseCenter' else 3
    xs=[-83+186*i/nx for i in range(nx+1)]
    zs=[b.ZMin+b.ZLength*i/nz for i in range(nz+1)]
    cuts=[];braces=[]
    for i in range(nx):
        for j in range(nz):
            # Eight mm external rim, eight mm internal ribs; through-open cells.
            x0=xs[i]+(8 if i==0 else 4);x1=xs[i+1]-(8 if i==nx-1 else 4)
            z0=zs[j]+(8 if j==0 else 4);z1=zs[j+1]-(8 if j==nz-1 else 4)
            cuts.append(box(x0,-89,z0,x1-x0,18,z1-z0))
            p,q=((x0-2,z0-2),(x1+2,z1+2)) if (i+j)%2==0 else ((x0-2,z1+2),(x1+2,z0-2))
            braces.append(beam_xz(p,q,4,-88,16))
    floor=floor.cut(fuse(cuts)).fuse(fuse(braces))
    # Preserve the original half-laps, screw seats, nut pockets, mounting bosses
    # and PCB-post roots exactly, including their underside tool openings.
    full=floor.fuse(top)
    q=full.cut(protect).fuse(s.common(protect)).removeSplitter()
    assert q.isValid() and len(q.Solids)==1, name
    S[name]=q
    same=s.common(protect).cut(q).Volume+q.common(protect).cut(s).Volume
    base_metrics.append(dict(part=name,old_volume_mm3=s.Volume,new_volume_mm3=q.Volume,
        protected_region_delta_mm3=same,cells=nx*nz,rim_rib_mm=8,diagonal_rib_mm=4,
        floor_y_mm=[-88,-72],grid_x_mm=xs,grid_z_mm=zs))
    assert same<1e-4
    print('BASE',name,'volume',round(s.Volume/1000,2),'->',round(q.Volume/1000,2),flush=True)

# Fixed frame: stiffening is on the rear side, within its existing Z envelope.
# Do not change the front sliding rails, follower slots, top thrust seat or feet.
frame=mv(old['Cable1_Frame'],z=118.65)
ribs=fuse([box(-63,-62,-8,6,74,20),box(85,-62,-8,6,104,20),
           box(-63,-62,-8,154,8,20),box(-3,-62,-8,6,36,20)])
# Preserve the existing mounting-knob lift corridor. Rear ribs must not cover
# the M4 heads below the guides, even though they clear the jaw movement.
ribs=ribs.cut(fuse([Part.makeCylinder(7,100,V(x,-63,4),V(0,1,0)) for x in [-54,80]]))
ribs=ribs.cut(fuse([box(-104,-38,-3,57,10,14),box(73,-38,-3,57,10,14)]))
# The retained M4x20 shaft also travels sideways after the 25mm lift, below
# the knob head. Keep a separate 6mm-wide shaft corridor, with 1mm clearance.
ribs=ribs.cut(fuse([box(-104,-58,1,57,21,6),box(73,-58,1,57,21,6)]))
windows=fuse([rounded_xy(-54,-49,18,10,2,11.5,6),
              rounded_xy(36,-49,24,10,2,11.5,6)])
new_frame=frame.fuse(ribs).cut(windows).removeSplitter()
assert new_frame.isValid() and len(new_frame.Solids)==1
for k,off in [(1,-118.65),(2,121.35)]:
    S[f'Cable{k}_Frame']=mv(new_frame,z=off)
print('FRAME volume',round(frame.Volume/1000,2),'->',round(new_frame.Volume/1000,2),flush=True)

out=A.newDocument('RFCP_A15_Resin_DFM_DRAFT')
mesh={};changes=[]
for name,s in S.items():
    meta={k:v for k,v in M[name].items() if k not in ['vertices','triangles']}
    if name in CHANGED:meta.update(revision='A15',dfm_candidate=True,color='#168d93')
    obj=out.addObject('PartDesign::Feature',name);obj.Shape=s
    for key,val in [('Status',STATUS),('DisplayColorHex',meta['color']),('Group',meta['group'])]:
        obj.addProperty('App::PropertyString',key);setattr(obj,key,val)
    verts,tris=s.tessellate(.2)
    mesh[name]=dict(vertices=[list(v) for v in verts],triangles=tris,**meta)
    if name in CHANGED:
        changes.append(dict(part=name,old_volume_mm3=old[name].Volume,new_volume_mm3=s.Volume,
            removed_mm3=old[name].cut(s).Volume,added_mm3=s.cut(old[name]).Volume,
            valid=s.isValid(),solids=len(s.Solids)))
out.recompute()
out.saveAs(str(O/'RFCP_A15_Integrated_DRAFT.FCStd'))
Part.makeCompound(list(S.values())).exportStep(str(O/'RFCP_A15_Integrated_DRAFT.step'))
(O/'mesh.json').write_text(json.dumps(mesh,separators=(',',':')))

# Keep the eleven unaffected print types byte-identical, especially free lids.
changed_files={'BaseFront_A14_DRAFT','BaseCenter_A14_DRAFT','BaseRear_A14_DRAFT','C07_Frame_DRAFT'}
for p in (P/'parts').iterdir():
    if p.suffix.lower() in ['.stl','.step'] and p.stem not in changed_files:
        shutil.copy2(p,O/'parts'/p.name)
print_shapes={name+'_A15_DRAFT':S[name] for name in BASES}
print_shapes['C08_Frame_DRAFT']=new_frame
for name,s in print_shapes.items():
    s.exportStep(str(O/'parts'/(name+'.step')))
    b=s.BoundBox
    MeshPart.meshFromShape(Shape=mv(s,-b.XMin,-b.YMin,-b.ZMin),LinearDeflection=.08,
                          AngularDeflection=.12,Relative=False).write(str(O/'parts'/(name+'.stl')))
manifest=[]
plan=json.loads((R/'procurement/print_costdown_20260923/print_plan.json').read_text(encoding='utf-8'))
replacement={'P05':'BaseCenter_A15_DRAFT.stl','P06':'C08_Frame_DRAFT.stl',
             'P14':'BaseFront_A15_DRAFT.stl','P15':'BaseRear_A15_DRAFT.stl'}
for row in plan['rows']:
    name=replacement.get(row['id'],row['file']);p=O/'parts'/name
    manifest.append(dict(id=row['id'],file=name,quantity=row['quantity'],
        material=row['material'],changed=row['id'] in replacement,sha256=sha(p),
        replaces_file=row['file'] if row['id'] in replacement else None))
assert len(manifest)==15 and sum(x['quantity'] for x in manifest)==20
result=dict(classification='CALCULATED_NOMINAL_CAD_DFM_CANDIDATE',status=STATUS,
    source_hashes=sources,freecad=A.Version(),changed_objects=changes,base_design=base_metrics,
    native_sha256=sha(O/'RFCP_A15_Integrated_DRAFT.FCStd'),parts=manifest,
    fastener_changes=[],source_native_unchanged=sha(native)==expected,
    limits=['No print-shrinkage, cure-stress, strength, creep or physical-fit validation.',
            'No supplier price, re-review, file replacement or manufacturing approval.',
            'A14 remains the submitted baseline; candidate A15 requires its own verification.'])
(O/'build_report.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['source_native_unchanged']
print('A15 BUILD DONE',str(O),flush=True)
