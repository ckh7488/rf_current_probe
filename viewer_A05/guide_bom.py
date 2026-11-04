"""Assembly-step references to current BOM; counts are handled parts, not new purchases."""
import json
from pathlib import Path
from set_content import ROWS
P=Path(__file__).resolve().parent
def add_bom(steps):
 counts={n:q for r in json.loads((P/'set_sources/bom_cad_check.json').read_text(encoding='utf-8'))['rows'] for n,q in r['objects'].items()}
 lookup={n:r for r in ROWS for n in r['cad']}

 for n in ['UpperLeft','UpperRight']:lookup[n+'Free']=lookup[n];counts[n+'Free']=1
 for i in range(1,5):lookup['CalibrationNut'+str(i)]=lookup['CalibrationNuts'];counts['CalibrationNut'+str(i)]=1
 extra={'H01':['PCB'],'H02':['FixedCore'],'H03':['LowerCenter'],'H06':['PCB'],'H09':['UpperLeftFree','UpperRightFree'],'C01':['Cable1_Jaw1','Cable1_Jaw2'],'C02':['Cable1_Frame'],'C07':['Cable1_DriveNut','Cable1_LeadLockNut','Cable1_ThrustWasher'],'B01':['BaseFront','BaseCenter','BaseRear'],'H12A':['HeadHandScrews'],'C04A':['Cable1_LeadStud'],'L00A':['LowerCenter'],'U00A':['UpperLeftFree'],'B00A':['BaseFront','BaseRear'],'Q03':['CalibrationNut'+str(i) for i in range(1,5)]}
 for s in steps:
  by_id={}
  if s['id']=='Q00':extra['Q00']=['FlatPCB']
  names=set(s['active']+extra.get(s['id'],[]))-set(s.get('previewOnly',[]))
  for n in sorted(names):
   if n in ['SignalCopper','ReturnCopper']:continue
   assert n in lookup,(s['id'],n)
   r=lookup[n];q=1 if r['id']=='E04' else counts[n]
   item=by_id.setdefault(r['id'],dict(id=r['id'],name=r['name'],qty=0,unit=r['unit']))
   item['qty']+=q
  if s['id']=='H02':by_id['E06']=dict(id='E06',name='폴리이미드 절연 테이프',qty=None,unit='필요 길이')
  for item in by_id.values():
   if item['id']=='E05':item['qty']=None
  s['bom']=sorted(by_id.values(),key=lambda r:r['id'])
 return steps
