"""A14/C07 data; A13 source is retained for traceability."""
from copy import deepcopy
from pathlib import Path
import json
from set_content_a13_history import ROWS as OLD_ROWS, MANUAL as OLD_MANUAL, dk
ROWS=deepcopy(OLD_ROWS)
mesh=json.loads((Path(__file__).resolve().parent.parent/'mechanical/assembly_A14_DRAFT/mesh.json').read_text())
def find(i): return next(r for r in ROWS if r['id']==i)
def change(i,**kw): find(i).update(kw)
def add(i,name,qty,spec,cad,links=(),note='',status='선정'):
 ROWS.append(dict(id=i,group='체결·구동',name=name,qty=qty,unit='개',spec=spec,status=status,note=note,links=list(links),cad=cad,file=None))
def matches(prefix,suffix):return [n for n in mesh if n.startswith(prefix) and n.endswith(suffix)]
for i,n,label in [('P01','LowerCenter','프로브 아래 중앙 몸체'),('P02','UpperLeft','프로브 왼쪽 뚜껑'),('P05','BaseCenter','공통 바닥 가운데')]:
 change(i,name=label,spec=n+'_A14_DRAFT.stl',cad=[n],file='parts/'+n+'_A14_DRAFT.stl',note='A14 자유 형상 STL. 조립 STEP에서 출력 형상을 추출하지 않음.')
for i,n,label in [('P11','LowerArmLeft','프로브 아래 왼팔'),('P12','LowerArmRight','프로브 아래 오른팔'),('P13','UpperRight','프로브 오른쪽 뚜껑'),('P14','BaseFront','공통 바닥 앞쪽'),('P15','BaseRear','공통 바닥 뒤쪽')]:
 ROWS.append(dict(id=i,group='3D 출력',name=label,qty=1,unit='개',spec=n+'_A14_DRAFT.stl',status='제작',note='A14 자유 형상 STL · 9/21 17:10 업체 파일 승인 완료 · 미결제.',links=[],cad=[n],file='parts/'+n+'_A14_DRAFT.stl'))
for i in ['P03','P04']:find(i)['note']='A13과 동일한 형상. A14 패키지의 해당 STL 사용.'
change('F06',note='바닥 6 + 가로대 4. NBK KNMS-12-M4-20 후보 외형. 바닥 왼쪽 2곳은 25 mm 올린 뒤 바깥쪽으로 빼는 경로를 사용.')
change('F08',name='큰 노브 · M6 암나사',spec='Ganter GN 6336.2-32-M6-E · Ø32 · 돌출 금속 부싱',status='선정',cad=['Cable1_HandKnob','Cable2_HandKnob'],links=[('제조사 도면','https://live-katalog.ganternorm.com/pdf/ganter/en/6336_1.pdf?dispositiontype=attachment')],note='F15 스터드를 10 mm 넣고 F16 잼너트를 금속 부싱에 조임. 프레임 밖에서 먼저 조립.')
add('F15','큰 노브용 기성 전나사 스터드',2,'Würth 095496120 · DIN 976 M6×120 · A2-70',['Cable1_LeadStud','Cable2_LeadStud'],[('제조사','https://eshop.wuerth.de/Threaded-rod-DIN-976-A2-70-stainless-steel-shape-A-THRPCE-DIN976-A-A2-70-M6X120/095496%20120.sku/en/US/EUR/')],'절단 가공 없이 기성 120 mm. 노브 삽입 깊이 10 mm 표시.')
add('F16','노브 고정 잼너트',2,'Fabory 51080.060.001 · DIN 934 M6 · AF10 / H5',['Cable1_TopJamNut','Cable2_TopJamNut'],[('제조사','https://www.fabory.com/nl_BE/zeskantmoer-din-934-roestvaststaal-%28rvs%29-a2-70-m6/p/51080060001')],'노브와 축을 고정하는 너트. 아래 F10 회전 여유 조절 너트와 다름.')
add('F17','축 위쪽 받침 와셔',2,'Fabory 50060.060.001 · 황동 · ID6.4 / OD12 / t1.6',['Cable1_TopWasher','Cable2_TopWasher'],[('제조사','https://www.fabory.com/nl_BE/vlakke-sluitring-din-125-1a-messing-m6/p/50060060001')],'프레임 위쪽. 아래 F11과 같은 t1.6 mm 와셔. 합계4개.')
add('F18','분할 바닥 연결 나사',4,'Essentra 50M040070P020 · PA66 M4×20',matches('BaseJoint','Screw'),[dk('50M040070P020')],'아래에서 위로 삽입. 아래/위 와셔 각 1개. 위에 육각너트.')
add('F19','분할 몸체·뚜껑 연결 나사',6,'Essentra 50M040070P030 · PA66 M4×30',matches('LowerJoint','Screw')+matches('UpperJoint','Screw'),[dk('50M040070P030')],'아래 몸체 4 + 위 뚜껑 2. 뒤에서 앞으로 삽입. 뚜껑에 M4×25 사용 금지.')
add('F20','분할 연결 육각너트',10,'Essentra 04M040070HNDIN34814 · PA66 M4',matches('BaseJoint','Nut')+matches('LowerJoint','Nut')+matches('UpperJoint','Nut'),[dk('04M040070HNDIN34814')],'AF6.8–7 / H2.9–3.2. 7 mm 공구. 기존 M4 사각너트 F07과 다름.')
add('F21','분할 연결 평와셔',20,'Essentra 17M04DIN34815 · PA66 · ID4.3 / OD9 / t0.8',matches('BaseJoint','Washer')+matches('LowerJoint','Washer')+matches('UpperJoint','Washer'),[dk('17M04DIN34815')],'나사 하나마다 머리 아래 1 + 너트 아래 1. 금속으로 일괄 대체하지 않음.')
find('T03')['spec']='7 mm / 10 mm / 5.5 mm / M2용 소형 공구 + 해당 드라이버'
ROWS.sort(key=lambda r:({'3D 출력':0,'전자·권선':1,'체결·구동':2,'측정 체인':3,'장비·공구':4}[r['group']],r['id']))
# Catalog selections verified against current source or bounded envelopes.
for patch in json.loads((Path(__file__).resolve().parent/"set_sources/catalogue_parts.json").read_text(encoding="utf-8"))["changes"]:
 if not any(r['id']==patch['id'] for r in ROWS):
  label={'F22':'개폐용 관통 노브','F23':'개폐 노브 고정 잼너트','F24':'개폐 노브 받침 와셔'}[patch['id']]
  add(patch['id'],label,patch['qty'],patch['spec'],patch['cad'])
 change(patch["id"],**{k:v for k,v in patch.items() if k!="id"})
change('F05',name='개폐 손나사용 기성 스터드')
change('F01',note='M2×12로 채택·CAD 반영 완료. 최대 너트 기준 공칭 끝 여유2.19 mm, 12.3 mm 길이의 지정61자세 무간섭. 출력물은 그대로. 입고 허용조건: 머리 아래11.7–12.3 mm / 조립 그립7.85–8.85 mm / 너트 높이1.46 mm 이하. 이는 설계 수입검사 기준이며 공급자 보증공차가 아님. H05에서 완전 나사산과 끝 간섭 확인.')
change('F02',note='제조사 개별도면 AF3.90±0.26 / H1.20±0.26 mm. 최대 외형 뒤 삽입 58자세 무간섭. F01은 M2×12로 채택. 완전 나사산이 너트 밖으로 나오는지는 첫 조립에서 확인. 실제 부품 공차를 공칭 CAD 치수와 혼동하지 않음.')
change('E02',spec='Head A04 DRAFT · 36×28×1.6 mm · FR4 2층',note='권선 출력과 SMA 연결. 수신기 단일 50 Ω 종단 사용. GCT/JLC 공차 검토 후 중심 홀1.70 / 접지 홀1.90 mm. 2026-09-22 18:49 KST JLC Y21-9961994A Approved 확인. 생산 파일 수동 승인·결제·첫 실물 삽입/납땜 전.')
change('E03',status='선정',spec='Fixture A03 DRAFT · 144×92.7×1.6 mm · FR4 2층 · JLC Y22-9961994A 5장',note='현행 교정지그. SIG만 코어 안, 리턴은 코어 밖으로 흐른다. 2026-09-23 사용자 결정(DEC-053): 이 A03으로1–500 MHz 보정을 수행한다. 판정 기준은 빈 지그 S11이 아니라 출력 포트 기준 코어 전류다. 저장 openEMS 빈 지그(SIMULATED) K는100/300/500 MHz에서 약0.05–0.10/0.41–0.78/0.87–1.65 dB다. 9/22 18:49 KST Approved·결제 대기이며 JLC 결제에서 빼지 않는다. 수동 생산파일 확인·실물 S2P·재장착·정/역방향 검증 전.')
change('E04',note='Head A04 1개 + Fixture A03 IN/OUT 2개 = 3개 모두 현행 필요량. RP-SMA 대체 금지. GCT Rev1.2 도면 및 JLC 공차의5핀 동시 삽입 계산 완료. 실물 핀 휨·평면 안착·납땜은 입고 확인.')
change('F13',status='선정',note='Fixture A03를 BaseCenter 받침4곳에 고정하는 현행 구매 대상4개. 실물 나사물림·높이는 첫 조립에서 확인.')
change('F14',status='선정',note='Fixture A03 고정용 PA66 M3 날개너트4개, 현행 구매 대상. Kang Yang SMO-3(N), PA66 M3×0.5. 제조사 도면 폭15.96±0.3/높이8±0.3 mm와 보수적 CAD 외형을 대조함. 정확 품번의 소량판매·한국배송은 확인 전. 외형이 다른 유사품 자동 대체 금지.')
change('R02',spec='TE 2467938-1 작업용 로드 · 50 Ω / SMA 수',status='선정',note='RF에서 1개 사용. 통합 구매는 발룬 6개 + 공유·예비 1개 = 7개 유지. 보유 SOL 교정 표준과 별개이며 구매 완료로 간주하지 않음. RF OFF에서 지그 출력 ↔ 헤드 출력으로 옮겨 사용. 교정 전에 이 로드의 S11을 VNA로 1회 측정해 Transfer 단계의 지그 출구 종단 보정에 사용.',links=[('통합 구매 7개','purchase.html#SHARED-LOAD')])
change('T04',name='인두·납·플럭스·인두팁·테스터',status='보유+추가',note='인두 보유. 구매팀용 목록에는 SMD291-10M 플럭스 2개와 900M-T-1.6D·2.4D 팁 각 1개 유지. 납·테스터는 보유 확인 필요. 이 1세트는 작업공구 묶음이며 구매 수량은 링크 기준.',links=[('플럭스 2개','purchase.html#SHARED-FLUX'),('인두팁 2종','purchase.html#domestic')])
ROWS.sort(key=lambda r:({'3D 출력':0,'전자·권선':1,'체결·구동':2,'측정 체인':3,'장비·공구':4}[r['group']],r['id']))
change('T03',note='PCB 뒤 M2 너트에는 가는 대향 평팁 공구. 각 끝단0.6×1.5 mm/가는 구간25 mm, 이후 Ø14×80 mm 손잡이 포락을 CAD로 검사했으며 실제 파지력·나사물림은 미검증. Ø6.5 mm 관형 소켓은 PCB 홀더에 간섭. M3 뒤 너트는 Ø8×25 mm 관형 포락 접근 확인. 10 mm 스패너는 머리폭18·두께4 mm 이내 기준. 실제 공구를 대조한다.')
change('R05',note='설치1개. 기본 운용은 감쇠기 없이 맨 프로브를 쓴다(MSO4054 50 Ω 입력 5 V RMS·피크±20 V, 정상 CM은 mA 이하). 강력 권고: 새 현장·새 케이블의 첫 측정은 반드시 이 10 dB를 넣고 최대값을 확인한 뒤 뺀다. 케이블 착탈·전원 투입 때도 넣는다. 감쇠기를 넣은 체인은 S21을 따로 측정해 보정한다. 상용전원·VFD·고전압·서지 현장은 Rev.A 범위 밖(DEC-055).')
change('R08',status='해당 없음',qty=None,unit='—',spec='대상 하네스(24 V·100BASE-TX)에서는 별도 보호 체인 없음',note='DEC-055로 종결. 이 하네스는 맨 프로브 + R05 첫 확인으로 운용한다. 상용전원·VFD 출력선·노출 고전압·서지 현장에 적용하려면 새로 선정·검증한다.')
change('T01',name='VNA (보유 LibreVNA 2포트)',status='보유',note='LibreVNA 2포트 보유. 필요 조건: 복소 S11/S21/S12/S22, 케이블 끝2포트 교정, 출력 레벨·IF BW 조절, Touchstone 저장, 하한100 kHz 이하, 500 MHz 포함. HW/FW/GUI 버전은 첫 벤치에서 기록.')
change('T02',name='오실로스코프 (보유 MSO4054)',status='보유',note='Tektronix MSO4054 보유(명판 확인 전 잠정 모델). 필요 조건: 500 MHz·50 Ω 입력·2.5 GS/s, 원시 파형 저장. FFT는 표시 샘플레이트1 GS/s 이상에서 보고, 저역을 길게 잡을 때는 대역 제한(20 MHz) 또는 Hi-Res를 켜 접힘을 막는다. 케이블+스코프 응답은 LibreVNA CW 출력을 R06으로 넣어 주파수별로 확인한다.')
change('E05',note='권선용 한 종류. 5턴 기본. 권선 직후 지그 없이 헤드 출력 S11로 자기공진을 기록한다. 필요한 대역이 신뢰 등급에 못 미칠 때만 3턴을 선택하며 턴수마다 교정 ID를 따로 둔다. 1롤은 구매 포장 단위로 잉여 발생.')
ROWS[:]=[r for r in ROWS if r['id']!='R07']  # DEC-055: R07 삭제, 스코프 응답은 CW+R06으로 확인
MANUAL=(Path(__file__).resolve().parent/'set_sources/manual_current.html').read_text(encoding='utf-8')
