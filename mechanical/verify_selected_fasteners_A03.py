"""Read-only nominal fit check for selected Essentra hardware; FreeCADCmd.

No printed tolerances, threads, forces, cable tooling or RF properties simulated.
The source CAD files are opened, never saved or regenerated.
"""
from pathlib import Path
import hashlib
import json
import FreeCAD as A
import Part

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'mechanical/clamp_A03_DRAFT'
V = A.Vector
files = [ROOT/'mechanical/clamp_A03_DRAFT/RFCP_Clamp_A03_DRAFT.FCStd',
         ROOT/'hardware/calibration_fixture/F_A_A01_DRAFT/RFCP_F_A_A01_DRAFT.FCStd']
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
head, jig = [A.openDocument(str(p)) for p in files]
def shape(doc, names):
    return Part.makeCompound([doc.getObject(n).Shape for n in names])
def cyl(r, h, x, y, z, axis=V(0,0,1)):
    return Part.makeCylinder(r,h,V(x,y,z),axis)
def mirror_z(s):
    m=A.Matrix(); m.A33=-1
    q=s.transformGeometry(m);q.translate(V(0,0,12.7));return q
hp=shape(head,['FixedTray','MovingTray','FixedKeeper','MovingKeeper','PCB','FixedCore','MovingCore','Winding','SMAEnvelope'])
jp=shape(jig,['Base','InputStand','OutputStand','HeadBracket','InputPlate','OutputPlate'])
checks=[]
def check(label, hardware, target):
    vol=hardware.common(target).Volume
    checks.append({'name':label,'overlap_mm3':vol,'distance_mm':hardware.distToShape(target)[0], 'no_nominal_interference':vol<1e-6})
# Largest published head sizes: M3 dia 5.6 x 2.4; M2 dia 4 x 1.6.
check('M3x25_hinge_max_head',cyl(2.8,2.4,-40,0,-5.4),hp)
check('M3x16_latch_max_head',cyl(2.8,2.4,40,-9.4,7,V(0,1,0)),hp)
check('M3_washer_OD7_ID3.2_T0.5',cyl(3.5,.5,-40,0,16.4).cut(cyl(1.6,.5,-40,0,16.4)),hp)
for x in [-24,24]:
    for y in [-25,25]: check(f'M2_keeper_head_{x}_{y}',cyl(2,1.6,x,y,16.4),hp)
for x in [-7,7]: check(f'M2_PCB_head_{x}',cyl(2,1.6,x,-45,6.35),Part.makeCompound([hp,jp]))
mounts=[(x,z) for x in [-65,65] for z in [-32,44.7]]+[(x,-12) for x in [-12,12]]
for x,z in mounts: check(f'M3x12_base_head_{x}_{z}',cyl(2.8,2.4,x,-61,z,V(0,1,0)),jp)
for x in [-59,59]:
    s=cyl(2.8,2.4,x,-8,-23.65)
    check(f'M3x10_input_plate_head_{x}',s,jp)
    check(f'M3x10_output_plate_head_{x}',mirror_z(s),jp)
unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
report={'classification':'CALCULATED_NOMINAL_CAD_ENVELOPES','date':'2026-09-17',
        'source_hashes':hashes,'source_files_unchanged':unchanged,'checks':checks,
        'all_no_nominal_interference':all(c['no_nominal_interference'] for c in checks),
        'limits':['Closed assembly only; head envelopes and optional washer, not full mating drawings.',
                  'Printed SLS tolerances, screw threads, torque, strength and physical fit remain unverified.',
                  'No RF measurements or fabrication approval.']}
(OUT/'selected_fastener_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(checks),'pass':report['all_no_nominal_interference'],'source_files_unchanged':unchanged}))
for d in [head,jig]: A.closeDocument(d.Name)
assert unchanged and report['all_no_nominal_interference']
