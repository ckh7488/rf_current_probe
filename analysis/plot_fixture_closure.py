"""Static review plots from preserved final SIMULATED snapshots."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];B=R/'reviews/design_closure_20260921'
d=json.loads((B/'comparison.json').read_text())
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':10})
fig,axs=plt.subplots(2,2,figsize=(13,8),layout='constrained')
labels={'revised_holes_600':'A03 기준 모델','revised_numeric_corner':'격자·영역 변경','revised_epsilon45':'유전율 4.5','revised_material_launch_corner':'유전율 4.5 + 런치 변경'}
for name,label in labels.items():
    rows=json.loads((B/'em'/name/'final_analysis/analysis.json').read_text())['windows'][-1]['rows'];f=np.array([v['f_Hz'] for v in rows])/1e6
    for ax,key in [(axs[0,0],'S_ref_dB'),(axs[0,1],'S_thru_dB'),(axs[1,0],'I_over_matched_mag'),(axs[1,1],'I_over_matched_phase_deg')]:
        ax.plot(f,[v[key] for v in rows],label=label,lw=1.7);ax.set_xscale('log');ax.grid(alpha=.25);ax.axvspan(1,100,color='#d5efe4',alpha=.23,zorder=-10);ax.set_xlim(1,500);ax.set_xlabel('주파수 (MHz)')
axs[0,0].axhline(-20,color='#b14e38',ls='--',lw=1);axs[0,0].set_ylabel('입력 반사 S11 (dB)');axs[0,0].legend(fontsize=9)
axs[0,1].set_ylabel('전달 S21 (dB)');axs[1,0].set_ylabel('|중앙 전류| / (|입사전압| / 50 Ω)');axs[1,0].axhline(1,color='#555555',ls='--',lw=1)
axs[1,1].set_ylabel('입사전압 기준 중앙 전류 위상 (°)')
fig.suptitle('교정 PCB A03: 외형 유지 · SMA 홀 확대 검토\nSIMULATED — 무코어·이상적 SMA 내부 기준면·무손실 재료',fontsize=15,fontweight='bold')
fig.savefig(B/'fixture_comparison.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained')
for c in d['comparisons']:
    if c['name'] not in ['combined_numerics','epsilon','launch']:continue
    def h(name):
        r=json.loads((B/'em'/name/'final_analysis/analysis.json').read_text())['windows'][-1]['rows']
        return np.array([v['f_Hz']/1e6 for v in r]),np.array([complex(v['HI_aligned_re'],v['HI_aligned_im']) for v in r])
    f,a=h(c['baseline']);_,b=h(c['variant']);ax.plot(f,100*abs(b/a-1),label={'combined_numerics':'격자·영역 복합 변경','epsilon':'유전율만 4.3 → 4.5','launch':'런치 높이·내경 변경'}[c['name']])
ax.set_xscale('log');ax.set_xlim(1,500);ax.axvspan(1,100,color='#d5efe4',alpha=.3);ax.axhline(1,color='#b14e38',ls='--',lw=1,label='원인 검토 기준 1%');ax.grid(alpha=.25);ax.legend();ax.set_xlabel('주파수 (MHz)');ax.set_ylabel('중앙 전류의 복소 상대차 (%)');ax.set_title('가정·수치 설정에 대한 민감도 — 실측 정확도나 오차 상한이 아님',fontweight='bold')
fig.savefig(B/'fixture_sensitivity.png',dpi=150);plt.close(fig)
print('two SIMULATED figures written')
