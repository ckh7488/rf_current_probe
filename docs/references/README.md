# 확보한 제조사 원본

확보 작업: 2026-09-15~16 (Asia/Seoul). 원본을 보존하고 렌더링·파생 계산과 구분한다. 파일별 SHA-256은 [manifest.json](manifest.json)에 있다.

| 파일 | 출처 / 역할 |
|---|---|
| [2644181281_catalog.pdf](2644181281_catalog.pdf) | [Fair-Rite 직접 배포 도면](https://docs.fair-rite.com/part-models/2644181281~cat.pdf), 도면 날짜 2020-03-03. 치수·접합면 시각 확인에 사용 |
| [2644181281_model.zip](2644181281_model.zip) | [Fair-Rite 직접 배포 CAD](https://docs.fair-rite.com/part-models/2644181281~cat~.zip) |
| [2644181281.STEP](2644181281.STEP) | 위 ZIP의 동일 이름 단일 항목을 내용 변경 없이 추출 |
| [core_official.html](core_official.html) | [제조사 제품 페이지](https://www.fair-rite.com/product/round-cable-snap-its-2644181281/)의 다운로드 사본. PDF/STEP 링크 출처 |
| [core_farnell.pdf](core_farnell.pdf) | [Farnell이 배포하는 제조사 구형 PDF](https://www.farnell.com/datasheets/2700033.pdf), 2018년 생성. 형상 비교용; 최신치와 혼용하지 않음 |
| [VAT-10A_plus.pdf](VAT-10A_plus.pdf) | [Mini-Circuits 직접 PDF](https://www.minicircuits.com/pdfs/VAT-10A%2B.pdf), Rev.C 2026-06-30, RF 정격·단자 확인 |
| [CAB27480_linked_drawing.pdf](CAB27480_linked_drawing.pdf) | [SparkFun 제품 페이지가 연결한 공급사 도면](https://cdn.sparkfun.com/assets/9/b/1/b/9/PN_28367_VPN_BCCA3788_Drawing.pdf), BCCA3788, 2024-11-21. 단자·길이·RG316 확인; RF 대역 보증 없음 |
| [RFPC-SMA28-F.pdf](RFPC-SMA28-F.pdf) | [TME 배포 GCT 제조사 도면](https://www.tme.com/Document/1c95feb1da661cbfe6e78e2fd3e8e209/RFPC-SMA28-F.pdf), Rev.1.2, 2025-05-12, 2쪽. 권장 홀·외형 확인. 두 페이지 Poppler 렌더링/시각 검토 실행 |

`*_page1.png`는 Poppler 26.07.0으로 렌더링한 시각 확인본이다. 제조사 도면은 UNCONTROLLED CATALOG DRAWING으로, 상세 형상의 일부 생략을 명시한다. 생산 관리도면·실물 확인을 대신하지 않는다.

카탈로그 도면의 전기 표는 mate pair, N=1, #22 AWG, WL=3인치 조건에서 25 MHz 36 Ω min, 100 MHz 57 Ω min을 적는다. 제품 웹페이지의 typical 억제 임피던스와 조건/표기가 다르므로 동일 보증값으로 합치지 않는다. 어느 값도 5턴 프로브의 ZT로 사용하지 않았다.

STEP은 한 반쪽의 공칭 형상이다. 반쪽 2개를 조립해야 한다는 물리적 구성은 확인했으나, 유통사 주문 단위는 이 파일들로 확정되지 않는다.

SMA PDF의 메타데이터 제목은 SMA25-F로 되어 있으나, 두 도면 본문과 품번/도면번호는 SMA28-F다. 본문을 우선하고 불일치를 기록했다. 프로젝트의 SMA 3D 파일은 이 도면 치수로 만든 외형 모델이며 제조사 상세 CAD로 표시하지 않는다.

## 후속 프로세스 검토의 온라인 일차자료

조회일 2026-09-16. 아래는 온라인에서 확인한 자료이며 위 manifest의 다운로드 원본 8개에 추가된 파일은 아니다.

- [Amphenol RF 901-9173](https://www.amphenolrf.com/en-us/part/901-9173/7570/): BNC jack–SMA jack, 50 Ω, DC~4 GHz. 가격/재고는 새로 조회하지 않았다. 단자/규격 확인 후보이며 개체 S2P는 없음.
- [LibreVNA 공식 매뉴얼](https://github.com/jankae/LibreVNA/blob/master/Documentation/UserManual/manual.tex): SOLT 표준 모델/Defined Through, de-embedding 순서, CW 발생기의 레벨/고조파 한계. master 조회본이며 보유 장비 버전과의 일치는 미확인.
- [LibreVNA 유지보수자 답변 #309](https://github.com/jankae/LibreVNA/discussions/309): 2025-05-06, 25 MHz 부근 소스 전환과 필터에 따른 고조파 설명. 현재 장비의 실측 결과로 취급하지 않음.
- [Tektronix 071-2121-04 원 MSO/DPO4000 사용자 매뉴얼](https://download.tek.com/manual/071212104web.pdf): 본문 86~89쪽의 coupling/입력 저항/대역/Probe Setup. AC coupling에서 1 MΩ로 전환됨을 확인. MSO4000B의 매뉴얼을 혼용하지 않음.

적용과 한계는 [전체 절차 검토](../END_TO_END_REHEARSAL.md)에 기록했다. 기존 다운로드 파일과 원본 해시는 변경하지 않았다.

## 2026-09-17 지그 자료

[별도 manifest](fixture_20260917/manifest.json)에 제조사 Amphenol 카탈로그의 공개 유통사 배포본과 도면 렌더를 등록했다. 원래 manifest 8개는 보존했다. [검토서](../BUILD_READINESS_20260917.md)에 현행 생산 도면 다운로드 403과 최신 공차 미확인을 명시했다.
