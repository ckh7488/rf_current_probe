"""Reopen saved native CAD and STLs; check actual PCB drill alignment."""
from pathlib import Path
import hashlib
import json
import FreeCAD as A
import Part
import Mesh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/clamp_A04_DRAFT'
report=json.loads((OUT/'mechanical_checks.json').read_text(encoding='utf-8'))
assert report['generator_sha256']==hashlib.sha256((ROOT/'mechanical/build_clamp_A04.py').read_bytes()).hexdigest(), 'Rebuild mechanical checks after editing generator'
assert report['nominal_checks_pass']
doc=A.openDocument(str(OUT/'RFCP_Clamp_A04_DRAFT.FCStd'))
parts={name:doc.getObject(name).Shape for name in ['FixedTray','MovingTray','FixedKeeper','MovingKeeper','FitCoupon']}
stl_results={}
for name,s in parts.items():
    assert s.isValid() and len(s.Solids)==1
    path=OUT/'parts'/f'{name}_DRAFT.stl'
    mesh=Mesh.Mesh(str(path))
    assert mesh.isSolid(), f'Non-solid STL: {name}'
    relative_volume_error=abs(mesh.Volume-s.Volume)/s.Volume
    assert relative_volume_error<.005, (name,relative_volume_error)
    bb=mesh.BoundBox
    assert abs(bb.ZMin)<.0001 and bb.XMin>-.0001 and bb.YMin>-.0001
    stl_results[name]={'solid_mesh':True,'triangles':mesh.CountFacets,'volume_relative_error':relative_volume_error,'bbox_mm':[bb.XLength,bb.YLength,bb.ZLength],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

pcb_report=json.loads((ROOT/'hardware/probe_head_A03/review/saved_board_verification.json').read_text(encoding='utf-8'))
assert report['source_board_step_sha256']==pcb_report['sha256']['review/board_only.step']
board=doc.getObject('PCB').Shape
bb=board.BoundBox
assert all(abs(a-b)<1e-4 for a,b in zip([bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax],[-18,18,-60,-32,4.75,6.35]))
holes=[]
for row in pcb_report['pcb_pads']:
    x=row['x_mm']-18;y=-32-row['y_mm'];r=row['drill_mm']/2
    # A slightly smaller bore must remain empty through the whole substrate.
    bore=Part.makeCylinder(r-.005,2,A.Vector(x,y,4.5))
    void_overlap=board.common(bore).Volume
    assert void_overlap<1e-5, (row,void_overlap)
    # There must also be material around the hole, not a missing corner.
    outer=Part.makeCylinder(r+.15,1,A.Vector(x,y,5))
    assert board.common(outer).Volume>.01
    holes.append({'ref':row['ref'],'pad':row['pad'],'center_cad_mm':[x,y],'drill_mm':row['drill_mm'],'bore_overlap_mm3':void_overlap})
for n in ['FixedCore','MovingCore','Winding','PCB','SMAEnvelope']:
    assert doc.getObject(n).Shape.isValid()
shoulder_checks=[]
tray=doc.getObject('FixedTray').Shape
for sign in [-1,1]:
    a=A.Vector(sign*18.3,-35,10);c=A.Vector(sign*22.5,-35,10)
    intersection=tray.common(Part.makeLine(a,c))
    length=sum(e.Length for e in intersection.Edges)
    assert abs(length-4.2)<1e-5
    # The former thin upper rim between enlarged PCB and core pocket is gone.
    void_probe=Part.makeSphere(.04,A.Vector(sign*14.36,-31.1,10))
    assert tray.common(void_probe).Volume<1e-8
    shoulder_checks.append({'side':sign,'section_y_z_mm':[-35,10],'material_length_mm':length,'old_upper_fin_removed':True})
access_checks=[]
obstacles=Part.makeCompound([doc.getObject(n).Shape for n in ['FixedTray','MovingTray','FixedKeeper','MovingKeeper','FixedCore','MovingCore','Winding','PCB','PCBScrews']])
for diameter in [12,16]:
    plug=Part.makeCylinder(diameter/2,30,A.Vector(0,-45,8.15))
    volume=plug.common(obstacles).Volume
    assert volume<1e-5
    access_checks.append({'kind':'assumed_plug_envelope','diameter_mm':diameter,'height_mm':30,'start_xyz_mm':[0,-45,8.15],'overlap_mm3':volume,'minimum_distance_mm':plug.distToShape(obstacles)[0]})
for x in [-14.5,14.5]:
    driver=Part.makeCylinder(2,35,A.Vector(x,-56.5,7.66))
    volume=driver.common(obstacles).Volume
    assert volume<1e-5
    access_checks.append({'kind':'assumed_head_mount_driver_shaft','diameter_mm':4,'start_xyz_mm':[x,-56.5,7.66],'overlap_mm3':volume})
result={'data_kind':'CALCULATED','status':'DRAFT - NOT FOR FABRICATION','saved_native_and_stl_checks_pass':True,
    'native_file_sha256':hashlib.sha256((OUT/'RFCP_Clamp_A04_DRAFT.FCStd').read_bytes()).hexdigest(),
    'mechanical_checks_sha256':hashlib.sha256((OUT/'mechanical_checks.json').read_bytes()).hexdigest(),
    'stl_parts':stl_results,'pcb_drill_alignment_from_saved_kicad':holes,'new_shoulder_sections':shoulder_checks,'plug_and_mount_tool_envelopes':access_checks,
    'limitations':['Finite sampled motion and nominal dimensions only.','STL topology/volume checks do not validate print supports, material strength, tolerances or fit.']}
(OUT/'saved_assembly_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'saved_native_and_stl_checks_pass':True,'stl_count':len(stl_results),'pcb_holes_checked':len(holes)}),flush=True)
