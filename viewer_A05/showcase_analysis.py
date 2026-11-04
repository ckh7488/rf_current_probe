"""Current A03 calibration reference. Historical candidate data stays in reviews/."""
from pathlib import Path
import json

R = Path(__file__).resolve().parent.parent


def build(D: Path, frame) -> None:
    saved = json.loads((R/'reviews/fixture_a03_output_reference_20260923/k_factor_results.json').read_text(encoding='utf-8'))
    cases = [case for case in saved['cases'].values() if case['fixture'] == 'A03']
    assert len(cases) == 9
    rows = []
    for mhz in [100, 300, 500]:
        anchors = [min(case['anchors'], key=lambda a: abs(a['f_MHz']-mhz)) for case in cases]
        assert all(abs(a['f_MHz']-mhz) < 1 for a in anchors)
        cells = ''.join(f'<td>{min(a[key] for a in anchors):.2f} … {max(a[key] for a in anchors):.2f}</td>' for key in ['S11_dB', 'S21_dB', 'K_dB'])
        rows.append(f'<tr><td>{mhz} MHz</td>{cells}</tr>')
    body = '''<section class="intro"><span class="eyebrow">FIXTURE A03 · 2026.09.23</span>
<h1>A03으로500 MHz까지 보정한다</h1>
<p class="lead">교정지그는 Fixture A03, 헤드 PCB는 Head A04입니다. A03의 반사·전달 특성을 측정에 반영하는 출력 포트 기준으로1–500 MHz 보정을 수행합니다. 주파수별 보정값과 오차를 기록합니다.</p></section>
<section class="sheet"><h2>−6 dB가 뜻하는 것</h2>
<p>동일한50 Ω 기준에서−6 dB는 전력 약1/4, 전압·전류 진폭 약1/2입니다. 전달 비율을 알고 있으면 그 복소 비율로 나누어 보정합니다. S11이 크거나 전력이 줄었다는 사실만으로500 MHz를 제외하지 않습니다.</p>
<p>교정의 기준은 프로브가 감싼 도체의 전류입니다. VNA가 측정한 출구 전류에서 코어 위치의 전류로 환산하는 K를 포함합니다. <b>K는 적용할 보정량이며 보정 후 남는 오차가 아닙니다.</b></p></section>
<section class="sheet"><h2>A03 저장 모델의 수치</h2>
<p>SIMULATED · 빈 지그9개 모델 변형. 실제 계산한 주파수의 범위만 표시합니다.</p>
<div class="tablewrap"><table><thead><tr><th>주파수</th><th>S11 · dB</th><th>S21 · dB</th><th>K · dB</th></tr></thead><tbody>''' + ''.join(rows) + '''</tbody></table></div>
<p>500 MHz S21 약−5~−5.8 dB는 알려진 전달 감소를 보정하는 방향과 양립합니다. 모델은 PEC/무손실 빈 지그이며 실제 SMA 몸체·코어·권선·하우징을 포함하지 않습니다. 표의 범위를 완성 프로브의 잔여 오차로 사용하지 않습니다.</p></section>
<section class="sheet"><h2>같은 지그에서 측정할 연결</h2>
<ol><li>실제 사용할 두 케이블 끝에서2포트 SOLT를 적용합니다.</li><li>빈 A03의 복소 S2P를 저장한 뒤 프로브를 장착합니다.</li><li>지그 OUT→VNA P2, 헤드 출력→외장50 Ω 로드로 장착 through를 저장합니다.</li><li>RF OFF 후 P2와 같은 로드의 자리만 바꿉니다. 지그 OUT→외장 로드, 헤드 출력→P2로 프로브 전달을 저장합니다.</li><li>같은 로드의 반사 ΓL을 저장하고 출력 기준 식으로 환산합니다.</li></ol>
<p><code>ZT = 50 × S21(전달) × (1 − S22(through)·ΓL) / [S21(through) × (1 − ΓL)] / K</code></p>
<p>S파라미터는 위상을 포함한 복소값입니다. K는 실제 전달 측정의 종단·장착 조건에 맞춰야 합니다. 빈 지그·정합 출력 모델을 시작값으로 쓰는 경우 실제 로드와 헤드 부하 차이를 불확도에 넣습니다. 로드와 P2를 교환할 때 바뀌는 헤드 부하도 평가합니다.</p>
<p><a href="assembly.html">단계별 연결과 SOLT 안내 →</a> · <a href="manual.html#calibration">교정 절차 →</a> · <a href="bom.html#E03">A03 구성품 →</a></p></section>
<section class="sheet"><h2>기록할 결과</h2>
<p>1–100 MHz에서 시작해100–300 MHz, 300–500 MHz까지 같은 방식으로 보정합니다. 300 MHz에서 일괄 참고 처리하지 않습니다. 각 주파수의 ZT, 불확도, 유효성을 함께 저장합니다.</p>
<p>정/역방향 반복은 결과의 일관성을 확인합니다. 양방향에 공통인 모델 오차까지 증명하지는 않으므로 K 모델·종단·재장착·직접 픽업·VNA 오차를 별도로 기록합니다. 실제로 신호가 사라지는 깊은 null이나 비선형 구간이 있으면 해당 점의 원인을 기록하고 전류 환산에서 제외합니다.</p>
<p>보정 방법과 수행 범위는 정해졌습니다. 출력 기준 분석 코드는 구현하고 합성 파일 시험을 마쳤습니다. 장착 through·전달의 정/역방향 S2P, 별도 암 기준면의 로드 S1P, 복소 K와 주파수별 검토 기록을 함께 읽어 유효 구간만 절대 ZT를 출력합니다. 실측 교정 데이터와 주파수별 정확도 표는 아직 없습니다. 센서의 평탄 대역과 오실로스코프의 응답은 지그 보정 범위와 별도로 기록합니다.</p>
<p class="subtle">근거: 저장 openEMS A03 결과의 재환산 · 백서11.6 · DEC-053. 지그 응답을 이용한 보정의 일반 원리는 <a href="https://helpfiles.keysight.com/csg/N1930xB/ToolsAndUtilities/Removing_Unwanted_Effects_from_the_Measurement.html">Keysight의 지그 보정 설명</a>을 참조합니다.</p></section>'''
    (D/'design-review.html').write_text(frame('design-review.html', 'A03 · 500 MHz 보정', body), encoding='utf-8')
    # Keep an existing URL functional without publishing obsolete candidate prose.
    redirect = frame('impedance-review.html', 'A03 교정 기준', '<section class="intro"><h1>A03 교정 기준</h1><p><a href="design-review.html">현행 A03 보정 원리와 수치 →</a></p></section>')
    redirect = redirect.replace('</head>', '<meta http-equiv="refresh" content="0;url=design-review.html"></head>', 1)
    (D/'impedance-review.html').write_text(redirect, encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit('build_showcase.py에서 호출합니다')
