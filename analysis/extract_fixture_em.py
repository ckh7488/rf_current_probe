"""Read saved KiCad A02 copper/board geometry for EM; never save the board."""
from pathlib import Path
import json,hashlib
import pcbnew as p
R=Path(__file__).resolve().parents[1]
f=R/'hardware/calibration_fixture_PCB_A02/RFCP_Fixture_Flat_A02_DRAFT.kicad_pcb'
O=R/'reviews/fixture_em_20260921';O.mkdir(exist_ok=True)
b=p.LoadBoard(str(f));before=hashlib.sha256(f.read_bytes()).hexdigest()
def ring(r):return [[p.ToMM(r.CPoint(i).x)-72,p.ToMM(r.CPoint(i).y)-46.35] for i in range(r.PointCount())]
def polys(s):return [{'outer':ring(s.COutline(i)),'holes':[ring(s.CHole(i,j)) for j in range(s.HoleCount(i))]} for i in range(s.OutlineCount())]
outline=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(outline,False)
zones=[]
for z in b.Zones():zones.append(dict(net=z.GetNetname(),layer=b.GetLayerName(z.GetLayer()),polygons=polys(z.GetFilledPolysList(z.GetLayer()))))
pads=[]
for fp in b.GetFootprints():
 for a in fp.Pads():pads.append(dict(ref=fp.GetReference(),net=a.GetNetname(),x=p.ToMM(a.GetPosition().x)-72,y=p.ToMM(a.GetPosition().y)-46.35,diameter=p.ToMM(a.GetSize().x),drill=p.ToMM(a.GetDrillSize().x),plated=a.GetAttribute()==p.PAD_ATTRIB_PTH))
vias=[]
for a in b.GetTracks():
 if isinstance(a,p.PCB_VIA):vias.append(dict(net=a.GetNetname(),x=p.ToMM(a.GetPosition().x)-72,y=p.ToMM(a.GetPosition().y)-46.35,diameter=p.ToMM(a.GetWidth(p.F_Cu)),drill=p.ToMM(a.GetDrillValue())))
d=dict(classification='CAD_EXTRACTED_SAVED_FILLED_BOARD',source=f.relative_to(R).as_posix(),sha256=before,kicad=p.GetBuildVersion(),units='mm',axes='board x-72; board y-46.35; z=normal from bottom copper to top copper',thickness=p.ToMM(b.GetDesignSettings().GetBoardThickness()),outline=polys(outline),zones=zones,pads=pads,vias=vias,ports=[[0,-34.35],[0,34.35]],core_center_y=0)
assert hashlib.sha256(f.read_bytes()).hexdigest()==before
(O/'geometry.json').write_text(json.dumps(d,indent=2),encoding='utf-8')
print(json.dumps(dict(zones=len(zones),pads=len(pads),vias=len(vias),board_contours=len(d['outline']),source_unchanged=True)))
