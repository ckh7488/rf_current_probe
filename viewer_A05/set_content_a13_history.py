"""A13/C07 document set: usage quantities, never purchase-pack quantities."""
from urllib.parse import quote
ROWS=[]
def row(id,group,name,qty,unit,spec,status,note='',links=(),cad=(),file=None):
 ROWS.append(dict(id=id,group=group,name=name,qty=qty,unit=unit,spec=spec,status=status,note=note,links=list(links),cad=list(cad),file=file))
def dk(mpn):return ('DigiKey 품번 검색','https://www.digikey.kr/ko/products?keywords='+quote(mpn,safe=''))
parts=[('LowerBody','프로브 아래 몸체'),('UpperLid','프로브 뚜껑'),('LowerKeeper','아래 코어 고정바'),('UpperKeeper','위 코어 고정바'),('CommonBase','공통 바닥')]
for i,(n,label) in enumerate(parts,1):
 row(f'P{i:02}','3D 출력',label,1,'개',n+'_FREE_DRAFT.stl','제작',
     '뚜껑은 자유 형상(FREE)만 출력. 조립 STEP에서 추출하지 않음.' if n=='UpperLid' else 'A13 원본 사용. 비전도성 무충전 나일론 후보; 공정·공차는 업체 확인.',cad=[n],file='parts/'+n+'_FREE_DRAFT.stl')
for i,(n,label) in enumerate([('Frame','클램프 고정틀'),('DriveYoke','클램프 연결틀'),('TopBridgeJaw','클램프 가로대·위 턱'),('Jaw1','아래 왼쪽 턱'),('Jaw2','아래 오른쪽 턱')],6):
 row(f'P{i:02}','3D 출력',label,2,'개','C07_'+n+'_DRAFT.stl','제작','앞·뒤 클램프에 각 1개.',cad=['Cable1_'+n,'Cable2_'+n],file='parts/C07_'+n+'_DRAFT.stl')
row('E01','전자·권선','분할 페라이트 코어',2,'반쪽','Fair-Rite 2644181281 · 44 재료','선정','물리적 반쪽 2개로 한 코어. 판매 단위가 반쪽인지 한 쌍인지 확인한 뒤 주문 수량 결정.',[('제조사','https://fair-rite.com/product/round-cable-snap-its-2644181281/'),dk('2644181281')],['FixedCore','MovingCore'])
row('E02','전자·권선','헤드 PCB',1,'장','RFCP_Head_A03_DRAFT · 36×28×1.6 mm · 2층','제작','권선 출력과 SMA 연결. 별도 50 Ω 종단저항은 실장하지 않음.',cad=['PCB'])
row('E03','전자·권선','평판 교정 PCB',1,'장','RFCP_Fixture_Flat_A02_DRAFT · 144×92.7×1.6 mm · 2층','보류','2026-09-18 단면 해석 약 242 Ω(무코어·균일 구간 근사). 50 Ω 정합 미확립으로 발주 보류. 수정 후 새 리비전 사용.',cad=['FlatPCB'])
row('E04','전자·권선','수직 SMA 암 커넥터',3,'개','GCT RFPC-SMA28-F · 표준 SMA, THT','선정','헤드 1개 + 교정 PCB 2개. RP-SMA 대체 금지.',[('제조사','https://gct.co/connector/rfpc-sma28-f'),dk('RFPC-SMA28-F')],['SMAEnvelope','SMAInput','SMAOutput'])
row('E05','전자·권선','에나멜선',None,'필요 길이','UEW Ø0.3 mm 후보','선정','권선용 한 종류. 초기 5턴 비교안이며 최종 턴수는 교정으로 결정. 1롤은 구매 포장 단위로 잉여 발생.',[('판매 페이지','https://www.devicemart.co.kr/goods/view?no=24937')],['Winding'])
row('E06','전자·권선','폴리이미드 절연 테이프',None,'필요 길이','폭 5 mm 후보 · 얇은 한 겹','선정','권선과 코어 사이 절연. 맞댐면 제외. 감은 뒤 실제 외경·간극 확인.',[('판매 페이지','https://www.devicemart.co.kr/goods/view?no=34614')])
row('F01','체결·구동','헤드 PCB 나사',2,'개','나일론 M2×10 · CAD 머리 Ø3.8×1.3','대조 필요','기존 50M020040P010 후보. 머리·길이·실물 공구 접근 대조.',[dk('50M020040P010')],['PCBScrews'])
row('F02','체결·구동','헤드 PCB 너트',2,'개','나일론 M2 · CAD 대변 3.9 / 높이 1.2','대조 필요','기존 04M020040HN 후보. 뒤에서 작은 너트를 잡아야 함.',[dk('04M020040HN')],['PCBNuts'])
row('F03','체결·구동','코어 고정바 나사',4,'개','나일론 M3×35 · 머리 Ø6.5×3.3 이내','미선정','위 2 + 아래 2. 이전 M3×25/30으로 주문하지 않음. 실제 머리·나사산 길이 확인.',cad=['LowerKeeperScrews','UpperKeeperScrews'])
row('F04','체결·구동','코어 고정바 너트',4,'개','나일론 M3 · 대변 5.5 / 높이 2.4 이내','대조 필요','기존 04M030050HNDIN34814 후보. 금속으로 일괄 대체하지 않음.',[dk('04M030050HNDIN34814')],['LowerKeeperNuts','UpperKeeperNuts'])
row('F05','체결·구동','프로브 개폐 손나사',2,'개','M4×50 · CAD 손잡이 Ø20×10','미선정','최종 품번 미확정. 옆 기둥에 체결; 코어를 직접 강하게 조이지 않음.',cad=['HeadHandScrews'])
row('F06','체결·구동','모듈·가로대 손나사',10,'개','M4×20 · CAD Ø12 / 높이 최대 7.5','대조 필요','바닥 6 + 클램프 가로대 4. NBK KNMS-12-M4-20 후보. 바닥 왼쪽 2곳의 머리 간섭은 미해결.',[('제조사 후보','https://www.nbk1560.com/en-US/products/machine_element/knob/KNMS/')],[*[f'MountScrew{i}' for i in range(6)],*[f'Cable{k}_BridgeScrew{i}' for k in [1,2] for i in [1,2]]])
row('F07','체결·구동','M4 사각너트',16,'개','7×7×3.2 mm · M4','대조 필요','프로브 2 + 바닥 6 + 가로대 4 + 팔로워 4. Bossard BN147 / 8236739 후보. 육각너트로 임의 대체하지 않음.',[('제조사 후보','https://www.bossard.com/us-en/eshop/square-nuts/square-nuts/p/147/')],['HeadSquareNuts',*[f'MountNut{i}' for i in range(6)],*[f'Cable{k}_{kind}Nut{i}' for k in [1,2] for kind in ['Bridge','Follower'] for i in [1,2]]])
row('F08','체결·구동','큰 노브 일체형 구동축',2,'개','M6×1, 나사부 110 mm · CAD 노브 Ø28×12','미선정','앞뒤 각 1개. 축과 노브의 결합·나사산 범위·실제 판매품 확인 필요. 그림처럼 생겼다는 이유로 주문하지 않음.',cad=['Cable1_LeadScrewKnob','Cable2_LeadScrewKnob'])
row('F09','체결·구동','M6 사각 구동너트',2,'개','M6×1 · 10×10×5 mm 공칭','미선정','홈 높이 6 mm로 공칭 상하 유격 1 mm. 최종 품번과 실제 두께 대조 필요.',cad=['Cable1_DriveNut','Cable2_DriveNut'])
row('F10','체결·구동','M6 축 위치 조절 너트',2,'개','Bossard BN33024 / 5813950 · M6×1 · AF10 / H6','선정','나일론 삽입형 풀림방지 너트 후보. 조절 후 축과 함께 회전. 프레임에 꽉 죄지 않음.',[('제조사','https://www.bossard.com/kr-ko/eshop/locking-nuts-with-polyamide-insert/prevailing-torque-type-hex-lock-nuts-thin-type-with-polyamide-insert/p/33024/')],['Cable1_LeadLockNut','Cable2_LeadLockNut'])
row('F11','체결·구동','M6 축 받침 와셔',2,'개','외경 12 / 내경 6.4 / 두께 0.8 mm','미선정','두께가 축 여유에 영향을 줌. 최종 품번 미확정.',cad=['Cable1_ThrustWasher','Cable2_ThrustWasher'])
row('F12','체결·구동','팔로워 어깨나사',4,'개','M4 나사부 8 / 어깨 Ø5×20 / 머리 Ø9×4 mm','미선정','경사 홈을 따라 움직이는 축. 일반 M4 나사로 바로 대체하지 않음.',cad=[f'Cable{k}_Follower{i}' for k in [1,2] for i in [1,2]])
row('F13','체결·구동','교정 PCB 고정 나사',4,'개','나일론 M3×12 · CAD 머리 Ø6×3','대조 필요','기존 50M030050P012 후보. 사내 금속 나사와 동일하게 취급하지 않음.',[dk('50M030050P012')],['CalibrationScrews'])
row('F14','체결·구동','교정 PCB 날개너트',4,'개','Kang Yang SMO-3(N) · M3 · PA66','선정','바깥쪽 열린 받침에 삽입. 날개 외형·구매 가능 여부 확인.',[('제조사 도면','https://www.kangyang-europe.com/wp-content/uploads/product_files/pdf/SMO-3.pdf')],['CalibrationNuts'])
row('R01','측정 체인','SMA 수–수 50 Ω 케이블',2,'개 사용','표준 SMA male–male','보유+추가','보유 1개 + 부족한 1개만 추가. CSE-SGAM-305-SGAM은 기존 후보; 305 mm 길이의 실제 배치 확인.',[dk('CSE-SGAM-305-SGAM')])
row('R02','측정 체인','SMA 수 50 Ω 로드',1,'개 사용','보유품 또는 TE 2467938-1 후보','보유','사용자 보유/별도 구매 예정품 공유. RF OFF에서 지그 출력 ↔ 헤드 출력으로 옮겨 사용. 새로 1개씩 이중 구매하지 않음.',[dk('2467938-1')])
row('R03','측정 체인','SMA OPEN / SHORT / LOAD',1,'세트','보유 교정 표준','보유','VNA 케이블 끝 기준면과 성별·모델값·유효 대역 확인.')
row('R04','측정 체인','SMA 암–암 THRU',1,'개 필요','2포트 교정용 연결 기준','보유 확인','보유 키트에 포함되어 있는지, through 정의가 맞는지 확인 후 부족할 때만 구매.')
row('R05','측정 체인','10 dB 감쇠기',1,'개','Mini-Circuits VAT-10A+ 후보','선정','정의된 출력 체인에 포함. 감쇠기만으로 현장 펄스/과전압 보호가 완성되지는 않음.',[('제조사','https://www.minicircuits.com/pdfs/VAT-10A+.pdf'),dk('VAT-10A+')])
row('R06','측정 체인','SMA–BNC 50 Ω 케이블',1,'개','SparkFun 27480 · 1 m 기존 후보','선정','50 Ω BNC 입력 오실로스코프 연결용. 실제 플러그 외형·감쇠·기준면 검증 필요.',[dk('1568-27480-ND')])
row('R07','측정 체인','BNC–SMA 교정 어댑터',1,'개 조건부','Cinch 29-3835 기존 후보','조건부','BNC 케이블 끝을 교정 체인에 포함하는 경로에서 사용. 해당 경로 확정 전 필수 구매로 합산하지 않음.',[dk('29-3835')])
row('R08','측정 체인','현장 입력 보호',None,'선정 후','허용 펄스·전압·에너지에 맞는 보호 체인','미선정','사용 조건과 정격 검증 후 선정. 이 항목이 미정인 상태를 현장 사용 가능 세트로 해석하지 않음.')
row('T01','장비·공구','2포트 이상 VNA',1,'대','50 Ω · 복소 S11/S21 · 1–300 MHz 포함, 500 MHz까지 확장 권장','보유 확인','100 kHz 목표까지 평가하려면 하한도 100 kHz 이하. 복소 S11/S21/S12/S22와 케이블 끝 2포트 교정, 출력 레벨·IF BW 조절, Touchstone 저장 지원. 보유 장비가 조건을 만족하면 재사용.')
row('T02','장비·공구','오실로스코프',1,'대','아날로그 대역폭 500 MHz 이상 권장 · 정의된 50 Ω 입력','보유 확인','사용 채널 수에서 2.5 GS/s 이상 권장. DC 결합·50 Ω 설정, 원시 파형 저장, 트리거·기록 길이 확인. 내부 종단이 없으면 대역/전력 정격이 검증된 외장 50 Ω 종단 사용. 장비 응답도 전체 체인에 포함해 확인.')
row('T03','장비·공구','스패너·드라이버',1,'세트','10 mm / 5.5 mm / M2 너트에 맞는 소형 공구','보유 확인','10 mm 스패너는 검사 외형 머리폭 18·두께 4 mm. 실제 보유 공구 대조. 임의의 몽키스패너 적합성은 미확인.')
row('T04','장비·공구','인두·납·플럭스·테스터',1,'세트','권선·납땜·도통 확인','보유 확인','소모품은 보유량 우선. 기존 발룬 통합 구매와 중복 확인.')
row('T05','장비·공구','치수·축 여유 확인 도구',1,'세트','캘리퍼 / 필러 게이지 등','보유 확인','코어 실제 치수, 출력 맞춤, 약 0.2 mm 축 여유 확인용.')

MANUAL='''
<section class="sheet" id="purpose"><span class="eyebrow">01 · 목적과 범위</span><h2>케이블 전체를 감싸서 RF 합전류를 본다</h2>
<p>산업용 Ethernet·24 V 하네스의 간헐 장애를 조사하기 위한 수동 RF 전류 프로브다. 코어 안을 지나는 도체들의 전류를 부호까지 더해서 본다. 서로 상쇄되는 정상 차동 전류와 달리, 케이블 밖으로 귀환하는 공통모드 성분은 합전류로 남을 수 있다.</p>
<p>교류의 시간 평균이 0이어도 주파수별 크기나 순간 전류는 0이 아니다. 이 프로브는 그 RF 성분을 관측한다. DC 전류 센서는 포함하지 않는다. 실드까지 감싸면 실드 전류도 합에 포함되므로, 어떤 도체군을 통과시켰는지 기록한다.</p>
<div class="notice">개발 목표 100 kHz–300 MHz, 먼저 확인할 구간 1–100 MHz. 500 MHz는 확장 특성 확인 목표다. 어느 구간도 실측 완료 사양이 아니다.</div></section>
<section class="sheet" id="parts"><span class="eyebrow">02 · 구성</span><h2>프로브·두 클램프·교정 PCB의 역할</h2>
<table><thead><tr><th>부분</th><th>하는 일</th></tr></thead><tbody><tr><td>가운데 프로브</td><td>분할 코어+권선 → 헤드 PCB → SMA. 전류를 출력 전압으로 바꾸는 센서.</td></tr><tr><td>앞뒤 케이블 클램프</td><td>각각 큰 노브 하나로 세 턱을 움직여 케이블 위치와 하중을 받는다. 앞뒤 노브는 따로 조작한다.</td></tr><tr><td>공통 바닥</td><td>세 모듈의 높이 기준을 맞춘다. 공칭 중심높이 84 mm, 바닥 254×314 mm. 실제 정렬은 확인해야 한다.</td></tr><tr><td>큰 평판 교정 PCB</td><td>교정 때 알려진 전류 경로를 만든다. 중앙 경로만 코어 안을 지나고 귀환은 두 바깥 레일로 간다.</td></tr></tbody></table>
<p class="subtle">클램프의 공칭 설계 구경은 Ø6–26 mm다. 실제 케이블의 중심 오차·외피 눌림·최대 커넥터 통과는 별도 확인 대상이다.</p>
<p><a href="assembly.html">캘리브레이션 및 사용법 보기 →</a></p></section>
<section class="sheet" id="assembly"><span class="eyebrow">03 · 조립</span><h2>조립은 절차서 순서대로</h2>
<ol class="sequence"><li>헤드 PCB에 SMA를 먼저 납땜한다. 아래 코어에 절연과 권선을 준비한다.</li><li>코어·PCB·고정바를 조립하고 권선 끝을 S+ / S−에 납땜한다. PCB는 기울여 넣는 경로를 사용한다.</li><li>같은 케이블 클램프를 두 개 조립한다. 가로대 사각너트는 가로대를 올리기 직전에 넣는다.</li><li>바닥 위에 세 모듈을 올린다. 아래 너트를 한 개씩 받치며 체결한다. 너트 여섯 개를 미리 넣고 뒤집지 않는다.</li><li>교정할 때만 큰 PCB를 장착한다. 권선·코어 맞댐면·PCB에 무리한 힘을 가하지 않는다.</li></ol>
<p>권선과 납땜 외에 동판 가공, 패드 재단, 스프링 조립은 없다. 반복 체결은 관통 홀과 기성 너트를 사용한다. 제품 CAD는 A13/C07이며 출력용 뚜껑은 <code>UpperLid_FREE_DRAFT</code>다.</p>
<p><a href="assembly-guide.html">36단계 조립절차서 열기 →</a></p>
<h3>큰 노브축의 조절</h3><p>위쪽 풀림방지 너트는 프레임을 꽉 죄는 용도가 아니다. 약 0.2 mm의 축 여유를 시험 목표로 맞추고, 스패너를 뺀 뒤 너트가 축과 함께 회전해야 한다. 과조임은 회전을 막을 수 있고, 과한 여유는 덜컥거림을 만든다. 아래 구동너트 홈의 공칭 1 mm 유격은 별개다.</p>
<p class="subtle">이는 조정이 필요한 시제품 구조다. 반복 회전 후 여유 유지·마찰·케이블 고정력은 실물에서 확인해야 한다. <a href="assembly-guide.html?step=C07">축 조절 단계 →</a></p></section>
<section class="sheet" id="calibration"><span class="eyebrow">04 · 실험실 교정</span><h2>먼저 지그를 확인하고, 다음에 프로브를 교정한다</h2>
<h3>A. 지그 through 확인</h3><div class="flow"><span>VNA PORT1</span><i>→</i><span>교정 PCB 입력 → 출력</span><i>→</i><span>VNA PORT2</span></div>
<div class="notice"><b>교정 PCB A02 발주 보류:</b> 2026-09-18 중앙 단면 해석에서 약 242 Ω(무코어·균일 단면 근사). 현재 PCB의 50 Ω 정합은 확립되지 않았습니다. <a href="impedance-review.html">계산 근거와 수정 방향</a>을 확인하세요. 아래 연결은 개발·검증 절차이며 완료된 교정 성능이 아닙니다.</div>
<p>케이블 끝 기준면에서 유효한 2포트 교정을 먼저 한다. 프로브 없는 지그의 S11/S21을 저장한다. 다음에는 프로브를 장착하고 프로브 출력을 외장 50 Ω 로드로 종단한 채 다시 저장해, 삽입에 따른 변화를 확인한다.</p>
<h3>B. 프로브 전달 응답 측정</h3><div class="flow"><span>VNA PORT1</span><i>→</i><span>교정 PCB 입력 → 출력</span><i>→</i><span>외장 50 Ω 로드</span></div><div class="flow"><span>프로브 출력 SMA</span><i>→</i><span>VNA PORT2 · 50 Ω</span></div>
<p>RF 출력을 끈 상태에서 재배선한다. 같은 외장 로드를 프로브 출력에서 지그 출력으로 옮기면 된다. 프로브 출력은 PORT2가 종단하므로 외장 로드를 추가로 병렬 연결하지 않는다.</p>
<p>시작 설정안은 1–100 MHz, 1601 points, −30 dBm, IF BW 1 kHz, 평균 4회다. 실제 장비 지원값·입력 정격·교정 유효성을 확인하고 설정을 저장한다. 더 높은 대역은 별도로 확장해 평가한다.</p>
<p>교정량은 <code>ZT(f) = Vout(f) / Iprimary(f)</code>다. <code>ZT ≈ 50×S21</code>은 기준면·정합·일차 전류 모델이 입증된 경우에만 적용한다. 지그 S11만으로 임의 보정하지 않는다. 먼저 상대 S21을 저장하고 전류 환산 조건을 확인한다.</p>
<p><strong>Ethernet의 100 Ω 차동 임피던스에 맞춰 프로브를 다시 교정하는 뜻은 아니다.</strong> 50 Ω은 지그와 출력 측정 체인의 조건이다. 검증된 범위에서 통과한 도체군의 RF 합전류를 환산하되, 프로브 장착 자체가 원래 전류를 바꾸는지도 확인해야 한다.</p>
<p class="subtle">장비 절차 근거: <a href="https://github.com/jankae/LibreVNA/blob/master/Documentation/UserManual/manual.tex">LibreVNA 공식 매뉴얼</a>. 수치와 판정 범위는 프로젝트의 초기 시험안이다.</p></section>
<section class="sheet" id="measurement"><span class="eyebrow">05 · 실제 케이블 측정</span><h2>기본은 탁상 사용, 프로브만 분리도 가능</h2>
<ol class="sequence"><li>교정 PCB와 지그용 로드를 제거한다. 코어 뚜껑과 앞뒤 가로대를 연다.</li><li>측정할 케이블을 위에서 놓는다. 세 곳을 닫고 앞뒤 큰 노브로 가볍게 중심을 맞춘다. 코어가 케이블 하중을 받지 않게 한다.</li><li>프로브 SMA를 검증된 출력 체인으로 수신기에 연결한다. 동축 무게와 당김은 별도로 받친다.</li><li>같은 위치·동축 경로·출력 체인을 유지하고 파형, 장애 로그, 측정 도체군을 기록한다.</li></ol>
<div class="flow"><span>프로브 SMA</span><i>→</i><span>정의된 보호·감쇠 체인</span><i>→</i><span>SMA–BNC</span><i>→</i><span>오실로스코프 · 50 Ω</span></div>
<p>시작 설정은 DC 결합, 정의된 50 Ω 종단, 전압 입력, 대역 제한 해제, 일반 샘플링이다. 메뉴 이름·지원 조합·입력 정격은 사용할 장비의 설명서에서 대조한다. 내부 50 Ω과 외장 50 Ω 종단을 병렬로 사용하지 않는다. AC coupling에서 같은 50 Ω 조건이 유지된다고 가정하지 않는다. 외부 감쇠 보정을 이중 적용하지 않는다.</p>
<p>바닥 고정 나사 두 개를 빼면 프로브만 분리할 수 있다. 이때 앞뒤 중심 클램프의 지지는 없어지므로 선 위치와 동축 하중을 따로 관리한다. 분리 전후 응답이 같다는 보장은 없으며 실제 사용 배치로 확인한다.</p>
<p>현장 입력 보호와 정격이 아직 확정되지 않았다. 감쇠기 하나가 서지 보호 전체를 대신하지 않는다. 보호접지 제거·실드 임의 절단·고전압 직접 적용 없이, 검증된 저에너지 벤치 시험부터 진행한다.</p>
<p class="subtle">500 MHz 대역폭·2.5 GS/s는 이 시제품의 장비 선정 권장 조건이며 전 대역 진폭 정확도를 보장하지 않는다. 대역폭·샘플링 관계: <a href="https://www.tek.com/en/documents/primer/evaluating-oscilloscopes">Tektronix 계측기 선정 자료</a>. 장비 근거: <a href="https://download.tek.com/manual/077024701Rev_A_web.pdf">Tektronix 원 MSO4054 계열 검증 매뉴얼</a>. VNA 교정만으로 스코프 입력 응답까지 자동 보정되지는 않는다.</p></section>
<section class="sheet" id="check"><span class="eyebrow">06 · 첫 조립과 측정의 확인</span><h2>어디까지 확인됐는가</h2>
<table><thead><tr><th>구분</th><th>현재 상태 / 확인할 내용</th></tr></thead><tbody>
<tr><td>공칭 CAD</td><td>저장 형상과 일부 조립·개폐 경로를 검사했다. 슬라이더는 나사산·손·마찰을 푸는 시뮬레이터가 아니다.</td></tr>
<tr><td>조립 중 남은 곳</td><td>H05 PCB 기울임과 작은 뒤 너트 접근, B05/B07의 왼쪽 손나사 머리 간섭, C07 축 여유·회전 유지. 해당 조립 단계에 표시했다.</td></tr>
<tr><td>실물 맞춤</td><td>핵심 기성품 치수, 출력 공차·평탄도, 코어 맞댐과 닫힘 힘, 앞뒤 중심 정렬, 케이블 외피 눌림 확인 전.</td></tr>
<tr><td>RF 확인</td><td>지그 정합, 선형성, 위치 민감도, 직접 픽업, 삽입 영향, 개폐 반복성과 유효 대역을 측정해야 한다. 금속과 코어 사이 거리만으로 무영향을 보장하지 않는다.</td></tr></tbody></table>
<p>권선의 DC 저항이 낮다고 곧바로 단락 불량은 아니다. 권선 연속성과 일차 경로·다른 금속으로의 의도치 않은 도통을 구분해 검사한다. 헤드 출력에 수신기 외의 50 Ω 종단을 중복 추가하지 않는다.</p>
<p>실측에서는 최소 5회 개폐 반복, 여러 케이블 위치, 소스 레벨 변경, 프로브 장착 전후를 비교한다. 현재 목표값을 통과한 측정 결과로 표현하지 않는다.</p></section>
<section class="sheet" id="records"><span class="eyebrow">07 · 기록과 유지</span><h2>형상과 교정 ID를 함께 보관한다</h2>
<ul><li>헤드 ID, 코어·권선 수, PCB/기구 리비전, 사진, 체결 상태.</li><li>VNA·케이블·로드·감쇠기 ID, 기준면, 주파수·레벨·IF BW·평균 설정.</li><li>원시 <code>.s2p</code>, 스코프 원시 파형, 장비 설정, 실패한 결과까지 보존.</li><li>유효 주파수 구간과 불확도. 기준면이나 출력 체인을 바꾸면 교정 재사용 가능성을 다시 확인.</li></ul>
<p>코어 맞댐면은 깨끗하게 유지하고 이물질·테이프·접착제를 넣지 않는다. 균열, 권선 피복 손상, 노브 유격 변화가 있으면 사용을 멈추고 확인한다. 리비전이 바뀐 부품을 이전 구매서와 섞지 않는다.</p>
<p class="subtle">이 설명서는 현재 설계의 사용·검증 절차를 정리한 문서다. 실물 제작 완료나 현장 사용 승인을 뜻하지 않는다.</p></section>
'''
