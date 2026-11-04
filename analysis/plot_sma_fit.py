"""Draw the calculated minimum-hole/max-pin envelope, not a product photo."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
R=Path(__file__).resolve().parents[1]
plt.rcParams['font.family']='Malgun Gothic'
plt.rcParams['axes.unicode_minus']=False
fig,axs=plt.subplots(1,2,figsize=(10,5),constrained_layout=True)
for ax,old,new,title in zip(axs,[1.42,1.62],[1.62,1.82],['중심핀 / 중심홀','접지핀 / 접지홀']):
    ax.add_patch(Circle((0,0),new/2,fill=False,lw=2,color='#1474ad',label=f'수정 후 최소 홀 Ø{new:.2f}'))
    ax.add_patch(Circle((0,0),old/2,fill=False,lw=2,linestyle='--',color='#c44234',label=f'기존 최소 홀 Ø{old:.2f}'))
    if ax is axs[0]:ax.add_patch(Circle((.05,.05),1.37/2,facecolor='#f7c873',edgecolor='#614b23',alpha=.65,label='최대 핀 Ø1.37 + XY 위치오차'))
    else:ax.add_patch(Rectangle((-.5,-.5),1.1,1.1,facecolor='#f7c873',edgecolor='#614b23',alpha=.65,label='최대 핀 포락 + XY 위치오차'))
    ax.set(xlim=(-1.15,1.15),ylim=(-1.15,1.15),aspect='equal',xlabel='mm',ylabel='mm',title=title)
    ax.grid(alpha=.2);ax.legend(loc='lower center',fontsize=8)
fig.suptitle('SMA 홀 공차 비교 · CALCULATED',fontsize=15)
fig.text(.5,-.04,'GCT 도면 대칭/중심핀 정렬 가정. JLC 홀 위치 XY 각 ±0.05 mm. 실물 삽입·납땜 보증이 아님.',ha='center',fontsize=9)
fig.savefig(R/'reviews/design_closure_20260921/sma/fit_envelopes.png',dpi=170,bbox_inches='tight')
