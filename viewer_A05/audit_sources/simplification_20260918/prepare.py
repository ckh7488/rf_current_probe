"""Remove A12/C06 nut-loss hardware, preserving A11/C05 repairs."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def read(p):return (R/p).read_text(encoding='utf-8')
def write(p,s):
 p=R/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
a=read('mechanical/build_assembly_A11.py').replace('A11','A13').replace('C05','C07')
a12=read('mechanical/build_assembly_A12.py')
wing=a12[a12.index('def wing_nut('):a12.index("a07=A.openDocument")]
a=a.replace("a07=A.openDocument",wing+"a07=A.openDocument",1)
start=a.index('  # Side-open tool window:')
end=a.index('  base=base.fuse(post)',start)
a=a[:start]+'''  # Short open wing-nut seat, no cover, receiver, or retaining mechanism.
  # Roof carries the screw load. Nut is placed from the outward X side.
  sign=1 if x>0 else -1
  post=box(x-7,-72,z-7,14,52,14).fuse(box(x-7,-20,z-11,14,18,22))
  post=post.cut(box(x-3.8 if sign>0 else x-7.1,-16.1,z-8.6,10.9,8.9,17.2))
  post=post.cut(cy(1.9,24,x,-24,z,V(0,1,0)))
'''+a[end:]
old="  n=hexz(0,0,0,5.5,2.4).cut(cy(1.6,5,0,0,-1));n.rotate(V(),V(1,0,0),-90);n.translate(V(x,-9.6,z));nuts.append(n)"
assert old in a;a=a.replace(old,'  nuts.append(wing_nut(x,z))')
a=a.replace("calibration_nut_holding='Side-open window; thin 5.5mm spanner approaches outward X'","calibration_nut_holding='Open outward wing-nut seat; place before installing PCB. No loss-prevention cover.'")
a=a.replace("'C07 uses candidate hardware envelopes; purchasing part numbers not finalized.'","'C07 uses candidate hardware envelopes; purchasing part numbers not finalized.','Nut loss prevention is intentionally omitted. Support loose nuts when fully removing screws.'")
write('mechanical/build_assembly_A13.py',a)
c=read('mechanical/build_cable_clamp_C05.py').replace('C05','C07').replace('A11','A13')
start=c.index('# Two standard M6 thin jam nuts')
end=c.index("add('ThrustWasher'",start)
c=c[:start]+'''# Retain C06 single M6 nyloc thrust adjustment, which has a working role.
# This is shaft endplay control, not a loose-nut cover. Rotate with lead shaft.
add('LeadLockNut',hexnut(80,35,26,10,6,'y'),'#b5c0c6','LEAD')
'''+c[end:]
c=c.replace('M6x110 knob screw + two M6 thin jam nuts + washer envelope; exact purchasable products/material still pending.','Fully threaded M6x110 knob screw + DIN985 M6 AF10/H6 locknut + washer envelopes; exact products and reversing-load adjustment require confirmation.')
c=c.replace('# Bridge M4 screws release before cap moves. Nuts remain in visible yoke pockets.','# Bridge screws release before the bridge moves. Open square-nut seats prevent rotation; loose nuts may fall out when unscrewed.')
write('mechanical/build_cable_clamp_C07.py',c)
for name in ['verify_assembly.py','verify_retention_mount.py']:
 s=read('mechanical/assembly_A12_DRAFT/'+name)
 # Never replace A12 globally: FreeCAD Matrix.A12 is a matrix element.
 for old,new in [('assembly_A12_DRAFT','assembly_A13_DRAFT'),('RFCP_A12_Integrated_DRAFT','RFCP_A13_Integrated_DRAFT'),('build_assembly_A12.py','build_assembly_A13.py'),('cable_clamp_C06_DRAFT','cable_clamp_C07_DRAFT'),('Cable_Clamp_C06_DRAFT','Cable_Clamp_C07_DRAFT')]:s=s.replace(old,new)
 write('mechanical/assembly_A13_DRAFT/'+name,s)
s=read('mechanical/cable_clamp_C06_DRAFT/verify_assembly.py').replace('C06','C07')
s=s.replace(",S['BridgeNutCover1'],S['BridgeNutCover2']",'')
write('mechanical/cable_clamp_C07_DRAFT/verify_assembly.py',s)
write('reviews/simplification_20260918/check_prints.py',read('reviews/independent_a12_20260918/check_prints.py'))
print('Prepared A13/C07, no cap/helper dependencies.')
