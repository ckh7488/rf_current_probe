# A11 / C05 최종 출력 파일 독립 검사

2026-09-18 · **DRAFT — NOT FOR FABRICATION**

현재 저장된 A11 STL **10종 / 출력 수량 15개**를 직접 검사했다. 모두 폐곡면이며 부피가 양수다. C05 클램프 5종은 원본 STL과 복사본의 SHA-256이 일치한다. 개별 파일·STEP 원본 해시, 크기와 수량은 [print_manifest.csv](print_manifest.csv), 검증 입력 해시는 [manifest.json](manifest.json)에 있다.

## 두께 표본 검사

각 STL에서 면적에 비례한 4,000개 표면 점을 뽑아 안쪽 법선 방향의 첫 출구까지 거리를 계산했다. 기존 A10 검사와 같은 알고리즘·시드 `20260918`를 사용했다. 총 40,000개 광선 모두 출구를 찾았다.

| 출력물 | 수량 | 최소 표본 거리 |
|---|---:|---:|
| C05 DriveYoke | 2 | 2.200 mm |
| C05 Frame | 2 | 2.400 mm |
| C05 Jaw1 / Jaw2 | 각각 2 | 2.600 mm |
| C05 TopBridgeJaw | 2 | 2.300 mm |
| CommonBase FREE | 1 | 3.000 mm |
| LowerBody FREE | 1 | 2.255 mm |
| LowerKeeper / UpperKeeper FREE | 각각 1 | 2.000 mm |
| UpperLid FREE | 1 | 2.400 mm |

최종 표본에서 **1.5 mm 미만은 0개**다. UpperKeeper의 원시 `below_2mm_samples` 123개는 모두 부동소수점 값 `1.9999999999999998 mm`이며, 2 mm 형상의 계산 반올림이다. 결과: [wall_scan_A11/summary.json](wall_scan_A11/summary.json).

**이 검사는 전체 형상의 최소 두께를 보증하는 검사가 아니다.** 작은 면적은 표본에 잡히지 않을 수 있으며 모서리·곡면의 법선 거리도 해석이 필요하다. 출력 업체 DFM, 재료 강도·뒤틀림·크리프, 나사 조임과 실제 조립 검증은 별도다. 기계 최대 출력 영역 안에 들어간다는 계산 또한 업체 승인이나 평탄도 보증이 아니다.

## 이번에 찾은 얇은 잔여 형상

첫 표본 검사에서 LowerBody에 1.0 mm 거리가 한 번 나왔다. CAD 단면을 확인하니 A10에도 있던 **X −6…6 mm, Y −35…−34 mm, Z 4.75…4.9 mm의 작은 잔여 턱**이었다. 앞뒤 폭은 0.15 mm이며, 큰 하중을 받는 벽으로 판정한 것은 아니다. Z 4.74 mm 단면은 두께 3 mm이고 Z 4.76–4.89 mm에서만 1 mm로 줄었다. 서로 어긋난 PCB 여유 가공이 남긴 형상이므로 A11 담당자가 불필요한 중앙 덮개 영역을 제거했다.

초기 결과는 [before_roof_cleanup](before_roof_cleanup/manifest.json)에 보존했다. [inherited_lip_extent.json](inherited_lip_extent.json)은 A10 원본에서 위치·단면을 확인한 기록이고, [low_chord_inspection.json](low_chord_inspection.json)은 같은 위치를 최종 A11과 비교한 기록이다. 수정 후 저장된 STL 10종을 다시 같은 40,000개 표본으로 검사했다.

## 출력할 파일 구분

- `FREE` 5종은 원래의 자유 형상 출력 파일이다. 특히 뚜껑은 **UpperLid_FREE_DRAFT.stl**만 사용한다.
- `C05_` 5종은 클램프 원본 파일이며 앞뒤에 각각 한 세트씩 사용한다.
- 통합 STEP/native에는 나사·코어·PCB 및 변형을 가정한 닫힌 뚜껑이 포함된다. 이 전체 조립체나 `CarrierLoaded_INTERNAL.step`를 출력물로 제출하지 않는다.
- STL 업로드 단위는 **mm / 100%**다. STL 파일 자체에는 단위 표기가 없다.

실행 원본: `check_prints.py`, `inspect_low_chord.py`, `inspect_inherited_lip.py`. Python 3.12 / trimesh 4.11.5 및 FreeCAD 1.0.2를 사용했다.
