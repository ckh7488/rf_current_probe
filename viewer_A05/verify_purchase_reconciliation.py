"""Catch dropped purchase commitments; distinguish a saved cart from planned additions."""
from pathlib import Path
import json,re,base64,zipfile
P=Path(__file__).resolve().parent;D=P/'dist';S=P/'set_sources'
audit=json.loads((S/'purchase_reconciliation.json').read_text(encoding='utf-8'))
groups=['retained','missing_restore','justified_design_removals','explicit_holds','mechanical_revision']
ids=[r['id'] for g in groups for r in audit[g]]
assert len(ids)==len(set(ids))==audit['old_rows_count']==33
rows=json.loads((D/'purchase-files/purchase_items.json').read_text(encoding='utf-8'))
by={r['id']:r for r in rows};assert len(by)==len(rows)==15
page=(D/'purchase.html').read_text(encoding='utf-8')
expected={'SHARED-FLUX':(2,34426),'SHARED-LOAD':(7,28028),'TIP-1.6D':(1,9350),'TIP-2.4D':(1,9350)}
for id,(qty,amount) in expected.items():
 r=by[id];assert (r['qty'],r['line_krw'])==(qty,amount)
 assert r['price_date']=='2026-09-17' and not r['in_existing_9_item_cart']
 assert f'id="{id}"' in page and r['url'] in page
 assert '/short/' not in r['url'] and 'order/cart' not in r['url']
dk=[r for r in rows if r['vendor']=='DigiKey'];dom=[r for r in rows if r['vendor']=='디바이스마트']
assert len(dk)==11 and sum(r['line_krw'] for r in dk)==410967
assert len(dom)==4 and sum(r['line_krw'] for r in dom)==48840
cart=[r for r in rows if r['in_existing_9_item_cart']]
assert len(cart)==9 and sum(r['line_krw'] for r in cart)==348513
bulk=(D/'purchase-files/DigiKey_11_items.txt').read_bytes()
assert bulk.decode().splitlines()==[f"{r['qty']},{r['sku']},{r['id']}" for r in dk]
inline=re.search(r'data:text/plain;charset=utf-8;base64,([A-Za-z0-9+/=]+)',page)[1]
assert base64.b64decode(inline).decode().splitlines()==bulk.decode().splitlines()
assert '아직 11종으로 갱신하지 않았습니다' in page
assert not re.search(r'href="(?:file:|http://127\.0\.0\.1|[A-Z]:)',page)
assert all(u.startswith(('https:','data:','#')) for u in re.findall(r'href="([^"]+)"',page))
bom={r['id']:r for r in json.loads((S/'bom.json').read_text(encoding='utf-8'))}
assert bom['R02']['status']=='선정' and '7개' in bom['R02']['note']
assert '플럭스 2개' in bom['T04']['note']
with zipfile.ZipFile(D/'RFCP_A14_DOCUMENT_SET.zip') as z:
 assert z.read('purchase-files/DigiKey_11_items.txt')==bulk
 for id in expected:assert f'id="{id}"' in z.read('purchase.html').decode()
report=dict(classification='PURCHASE_RECORD_RECONCILIATION_NOT_LIVE_QUOTE_OR_ORDER',passed=True,previous_rows_reconciled=33,restored=expected,listed_purchase_rows=15,digikey_bulk_rows=11,existing_shared_cart_rows=9,prices_are_historical=True,payment_made=False)
(S/'purchase_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
