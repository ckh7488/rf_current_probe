"""Historical first-draft migration, retained for audit; not a rebuild entrypoint."""
raise SystemExit('Historical bootstrap. Rebuild with mechanical/build_cable_clamp_C04.py and mechanical/build_assembly_A10.py instead.')
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'mechanical/build_cable_clamp_C03.py';s=p.read_text().replace('C03','C04').replace('A09','A10')
def change(a,b):
 global s
 assert a in s,a;s=s.replace(a,b)
change('box(-59,-62,12,150,99,5)','box(-63,-62,12,154,99,5)')
change('for x in [-54,44]:','for x in [-56,42]:')
change('box(x+10.8,5,17,3.5,15,15)','box(x+14.8,5,17,3.5,15,15)')
change('# Back plate slots and radial guide walls. 0.6 mm side clearance, 0.2 mm front.','# 14 mm jaw bodies; 0.8 mm side and front clearance. 2.4 mm front lips.')
change('for lo in [-9.2,4.8]:frame=frame.fuse(rot(box(20,lo,-2,29,4.4,14),a))','for lo in [-12.2,7.8]:frame=frame.fuse(rot(box(20,lo,-3.2,29,4.4,15.2),a))')
change('for lo in [-9.2,3.5]:frame=frame.fuse(rot(box(23,lo,-2,22,5.7,-.8-(-2)),a))','for lo in [-12.2,6.5]:frame=frame.fuse(rot(box(23,lo,-3.2,22,5.7,2.4),a))')
change('box(-54,-54,18,108,10,10),box(-54,-44,18,10,70,10),box(44,-44,18,10,70,10)','box(-56,-54,18,112,10,10),box(-56,-44,18,14,70,10),box(42,-44,18,14,70,10)')
change('box(-54,26,18,108,10,10)','box(-56,26,18,112,10,10)')
change('jaw=rot(prism([(8,-1.5),(8,1.5),(14,4),(44,4),(44,-4),(14,-4)],0,10),a)\n jaw=jaw.cut(cy(2.2,14,nx*34,ny*34,-2)).cut(box(nx*34-4.4,ny*34-4.4,-1,8.8,8.8,7.8))','jaw=prism([(8,-1.5),(8,1.5),(14,7),(44,7),(44,-7),(14,-7)],0,10)\n jaw=rot(jaw.cut(cy(2.2,14,34,0,-2)).cut(box(29.6,-4.4,-1,8.8,8.8,7.8)),a)')
change('cy(2,7,nx*34,ny*34,3)','cy(2,8,nx*34,ny*34,2)')
change("box(nx*34-3.5,ny*34-3.5,3.5,7,7,3.2).cut(cy(2.1,5,nx*34,ny*34,3))","rot(box(30.5,-3.5,3.5,7,7,3.2).cut(cy(2.1,5,34,0,3)),a)")
change('box(75,-32.8,18,10,5.2,10)','box(75,-32.7,18,10,5.0,10)')
(R/'mechanical/build_cable_clamp_C04.py').write_text(s)
p=R/'mechanical/build_assembly_A09.py';s=p.read_text().replace('A09','A10').replace('C03','C04')
change("# Clear the keeper's screws; the keeper is allowed to seat at the core thickness.\nfor x in [-36,36]:lower=lower.cut(box(x-4.5,-29,10.5,9,13,8))", """# Wider keeper bosses, moved out 1 mm. Remove the old counterbore's feather edge.
for sign in [-1,1]:
 x=sign*37;left=32.5 if sign>0 else -42
 lower=lower.fuse(box(left,-30,-4.5,9.5,14,20))
 lower=lower.cut(box(31.5 if sign>0 else -43,-29,-10,11.5,12,5.5))
 lower=lower.cut(cy(2.1,36,x,-23,-12))
 lower=lower.cut(box(left,-29,10.5,9.5,13,8))
# Thicken the inherited 0.75 mm PCB relief roof outward, without closing access.
lower=lower.fuse(box(-18.5,-37,14.75,37,2,2.4))""")
change('for x in [-36,36]:\n carrier=carrier.cut(cy(2.1,36,x,23,-12)).cut(cy(4.25,4.5,x,23,-9)).cut(box(x-4.5,16,10.5,9,13,8))',"""for sign in [-1,1]:
 x=sign*37;left=32.5 if sign>0 else -42
 carrier=carrier.fuse(box(left,16,-4.5,9.5,14,20))
 carrier=carrier.cut(cy(2.1,36,x,23,-12)).cut(box(left,16,10.5,9.5,13,8))""")
change('box(-40,-43,16.5,80,6,4),box(-40,-43,16.5,8,36,4),box(32,-43,16.5,8,36,4)','box(-44,-43,16.5,88,6,4),box(-44,-43,16.5,12,36,4),box(32,-43,16.5,12,36,4)')
change('for x in [-36,36]:keeper=keeper.cut','for x in [-37,37]:keeper=keeper.cut')
change('box(x-2,-13.5,-.5,4,1.0,21)','box(x-2,-12.5,-.5,4,2.0,21)')
# Inner edge moves toward the cable by 2 mm; verify radius-13 insertion explicitly.
change('box(x-2,-42.5,16.5,4,30,4)','box(x-2,-42.5,16.5,4,32,4)')
change('for x in [-36,36]:\n  bolts.append','for x in [-37,37]:\n  bolts.append')
change('base=base.fuse(cy(6,70,x,-72,z,V(0,1,0)))','base=base.fuse(box(x-7,-72,z-7,14,70,14))')
change("'No RF, structural FEA, print process, hand assembly or durability test.'","'No RF, print process, hand assembly or durability test. Separate linear FEA is scoped in reviews/functionality_20260918.'")
(R/'mechanical/build_assembly_A10.py').write_text(s)
for old,new in [('assembly_A09','assembly_A10'),('cable_clamp_C03','cable_clamp_C04')]:
 src=R/'mechanical'/(old+'_DRAFT');dst=R/'mechanical'/(new+'_DRAFT');dst.mkdir(exist_ok=True)
 for p in src.glob('verify*.py'):
  txt=p.read_text().replace('A09','A10').replace('C03','C04')
  if p.name=='verify_retention_mount.py':txt=txt.replace('[-36,36]','[-37,37]')
  (dst/p.name).write_text(txt)
print('Created A10/C04; A09/C03 preserved.')
