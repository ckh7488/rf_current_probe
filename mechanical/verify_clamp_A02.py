"""Reopen saved native CAD and STLs; check actual PCB drill alignment."""
from pathlib import Path
import hashlib
import json
import FreeCAD as A
import Part
import Mesh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/clamp_A02_DRAFT'
report=json.loads((OUT/'mechanical_checks.json').read_text(encoding='utf-8'))
assert report['generator_sha256']==hashlib.sha256((ROOT/'mechanical/build_clamp_A02.py').read_bytes()).hexdigest(), 'Rebuild mechanical checks after editing generator'
assert report['nominal_checks_pass']
doc=A.openDocument(str(OUT/'RFCP_Clamp_A02_DRAFT.FCStd'))
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

pcb_report=json.loads((ROOT/'hardware/probe_head/review/saved_board_verification.json').read_text(encoding='utf-8'))
assert report['source_board_step_sha256']==pcb_report['sha256']['review/board_only.step']
board=doc.getObject('PCB').Shape
bb=board.BoundBox
assert all(abs(a-b)<1e-4 for a,b in zip([bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax],[-10,10,-48,-32,4.75,6.35]))
holes=[]
for row in pcb_report['pcb_pads']:
    x=row['x_mm']-10;y=-32-row['y_mm'];r=row['drill_mm']/2
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
result={'data_kind':'CALCULATED','status':'DRAFT - NOT FOR FABRICATION','saved_native_and_stl_checks_pass':True,
    'native_file_sha256':hashlib.sha256((OUT/'RFCP_Clamp_A02_DRAFT.FCStd').read_bytes()).hexdigest(),
    'mechanical_checks_sha256':hashlib.sha256((OUT/'mechanical_checks.json').read_bytes()).hexdigest(),
    'stl_parts':stl_results,'pcb_drill_alignment_from_saved_kicad':holes,
    'limitations':['Finite sampled motion and nominal dimensions only.','STL topology/volume checks do not validate print supports, material strength, tolerances or fit.']}
(OUT/'saved_assembly_verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'saved_native_and_stl_checks_pass':True,'stl_count':len(stl_results),'pcb_holes_checked':len(holes)}),flush=True)
