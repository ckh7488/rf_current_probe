"""Read-only count check of BOM usage quantities against frozen native CAD."""
from pathlib import Path
import sys,json,hashlib
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import FreeCAD as App
from set_content import ROWS
native=P.parent/'mechanical/assembly_A14_DRAFT/RFCP_A14_Integrated_DRAFT.FCStd'
doc=App.openDocument(str(native))
results=[];used=[]
for row in ROWS:
 if not row['cad']:continue
 counts={}
 for name in row['cad']:
  obj=doc.getObject(name)
  assert obj is not None,(row['id'],name)
  counts[name]=len(obj.Shape.Solids)
  used.append(name)
 # Each connector is a catalog assembly (body plus five pins), not six purchases.
 total=len(counts) if row['id']=='E04' else sum(counts.values())
 if isinstance(row['qty'],int):assert total==row['qty'],(row['id'],total,row['qty'])
 results.append(dict(id=row['id'],objects=counts,usage_quantity=row['qty'],cad_solids=sum(counts.values()),counted_units=total,count_basis='connector assembly' if row['id']=='E04' else 'solid'))
assert len(set(used))==len(used),'CAD object assigned to multiple BOM lines'
report=dict(classification='CALCULATED_CAD_QUANTITY_CHECK_NOT_FIT_OR_RF_VALIDATION',native_sha256=hashlib.sha256(native.read_bytes()).hexdigest(),rows=results,unassigned_shape_objects=[o.Name for o in doc.Objects if hasattr(o,'Shape') and o.Name not in used])
assert report['unassigned_shape_objects']==['SignalCopper','ReturnCopper']
report['pass']=True
report['unassigned_explanation']='SignalCopper and ReturnCopper are copper on the fixture PCB E03, not separate purchased pieces.'
(P/'set_sources/bom_cad_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
App.closeDocument(doc.Name)
print(json.dumps({'pass':True,'cad_rows':len(results),'named_objects':len(used),'unassigned':report['unassigned_shape_objects']}))
