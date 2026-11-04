"""Render real CAD sections. Each before/after pair uses identical scale and cut."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.ticker import MultipleLocator
O=Path(__file__).resolve().parent;out=O/'images';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':12})
notes={
 'jaw':dict(before='몸체 폭 8 mm · 홈 방향 불일치',after='몸체 폭 14 mm · 홈 방향 일치',why='사각 너트 홈이 비스듬한 턱의 옆면을 뚫고 나가던 형상.\n홈을 턱과 나란하게 돌리고 양옆에 각각 2.6 mm 벽을 남겼습니다.',oldpoint=(34,3.8),newpoint=(34,5.7),oldlabel='옆면으로 터지는 홈',newlabel='양옆 벽 2.6 mm'),
 'lug':dict(before='폭 10 mm · 얇은 옆벽과 뒷벽',after='폭 14 mm · 너트 뒤도 함께 보강',why='가로대를 잠글 때 힘을 받는 너트 주변이 약했습니다.\n옆벽 1.1 → 3.1 mm, 홈 뒤쪽 벽 1.1 → 2.4 mm로 늘렸습니다.',oldpoint=(53.5,22),newpoint=(54.5,24),oldlabel='옆벽 1.1 mm',newlabel='옆벽 3.1 mm'),
 'guide':dict(before='앞쪽 턱 두께 1.2 mm',after='앞쪽 턱 두께 2.4 mm',why='슬라이딩 턱이 앞으로 빠지지 않게 받치는 부분입니다.\n두께를 두 배로 늘리고, 넓어진 턱에 맞춰 통로도 넓혔습니다.',oldpoint=(6,-1.4),newpoint=(9,-2),oldlabel='얇은 앞턱',newlabel='2.4 mm 앞턱'),
 'catch':dict(before='코어 이탈 방지턱 1.0 mm',after='코어 이탈 방지턱 2.0 mm',why='고정바에 붙은 긴 턱이 출력·취급 중 깨질 여지를 줄였습니다.\n권선 통로와 고정바 탈착 경로는 다시 확인했습니다.',oldpoint=(9,-13),newpoint=(9,-11.5),oldlabel='1.0 mm',newlabel='2.0 mm'),
 'boss':dict(before='나사 구멍–코어 공간 사이 1.4 mm',after='나사 위치 이동 · 바깥쪽 받침 확대',why='고정바 나사를 1 mm 바깥으로 옮기고 주변 받침을 넓혔습니다.\n코어 공간을 좁히지 않고 안쪽 벽 2.4 mm를 확보했습니다.',oldpoint=(33.2,21.2),newpoint=(33.7,21.2),oldlabel='1.4 mm 벽',newlabel='2.4 mm 벽'),
 'post':dict(before='둥근 기둥을 너트 홈이 파고듦',after='14 × 14 mm 기둥 · 벽 3 mm',why='둥근 기둥에 사각 홈이 겹치면서 가장자리가 얇아졌습니다.\n사각 기둥으로 바꿔 너트 홈 양옆에 3 mm 벽을 남겼습니다.',oldpoint=(70,48),newpoint=(70.5,48),oldlabel='얇아지는 모서리',newlabel='3 mm 벽'),
 'lead':dict(before='구동축 구멍 위·아래 벽 1.5 mm',after='받침 두께 확대 · 축 위치 이동',why='M6 축이 통과하는 부분을 두껍게 하고 축도 3 mm 옮겼습니다.\n구멍 위 벽 3.5 mm, 아래 벽 4.5 mm. 너트 홈 뒤도 2.4 mm를 남겼습니다.',oldpoint=(80,27.25),newpoint=(80,31.25),oldlabel='1.5 mm',newlabel='3.5 mm'),
 'wire':dict(before='권선 출구에 남은 1 mm 막벽',after='막벽 제거 · 출구를 연결',why='권선 통로와 PCB 공간 사이의 불필요한 얇은 벽을 제거했습니다.\n주변 지붕은 0.75 → 2.4 mm, PCB 받침의 아래 벽은 3 mm로 보강했습니다.',oldpoint=(-34.5,10),newpoint=(-34.5,10),oldlabel='1 mm 잔여 벽',newlabel='열린 권선 통로'),
}
cases=json.loads((O/'comparison_geometry.json').read_text());result=[]
for idx,c in enumerate(cases):
 n=notes[c['key']];fig=plt.figure(figsize=(13.5,5.3),facecolor='#f2f6f8');gs=fig.add_gridspec(1,2,left=.045,right=.97,bottom=.25,top=.69,wspace=.14)
 fig.text(.045,.93,f"{idx+1:02d}  {c['title']}",fontsize=20,weight='bold',color='#142d3b')
 fig.text(.045,.86,'실제 CAD를 같은 위치에서 자른 단면 · 좌우 같은 배율 · 치수 단위 mm',fontsize=11,color='#56717f')
 for j,m in enumerate(c['models']):
  ax=fig.add_subplot(gs[j]);color=['#b45743','#177c91'][j]
  verts=m['vertices'];tri=[[verts[k] for k in t] for t in m['triangles']]
  ax.add_collection(PolyCollection(tri,facecolors=color,edgecolors='none',antialiased=False,zorder=3))
  x0,x1,y0,y1=c['bounds'];ax.set_xlim(x0,x1);ax.set_ylim(y0,y1);ax.set_aspect('equal');ax.set_facecolor('white')
  ax.grid(color='#e6edf1',linewidth=.6,zorder=0);ax.xaxis.set_major_locator(MultipleLocator(5));ax.yaxis.set_major_locator(MultipleLocator(5));ax.tick_params(labelsize=9,colors='#65818d',length=0)
  for s in ax.spines.values():s.set_color('#d2dfe5')
  ax.set_title(('수정 전  A09 / C03' if j==0 else '수정 후  A10 / C04')+'\n'+n['before' if j==0 else 'after'],loc='left',color=color,fontsize=12,pad=12,linespacing=1.8)
  pt=n['oldpoint' if j==0 else 'newpoint'];label=n['oldlabel' if j==0 else 'newlabel']
  # Annotation outside the material at upper left/right; precise target point.
  ax.annotate(label,xy=pt,xytext=(.03,.95),textcoords='axes fraction',ha='left',va='top',fontsize=10,color='#142d3b',bbox=dict(boxstyle='round,pad=.3',fc='white',ec='#d5e1e8',alpha=.96),arrowprops=dict(arrowstyle='->',color='#122f3e',lw=1.3),zorder=5)
 fig.text(.045,.125,n['why'],fontsize=13,color='#183b4a',linespacing=1.8)
 fig.text(.97,.035,'설계 수정·계산 검토 / 실제 출력·내구성 시험 전',ha='right',fontsize=10,color='#607c89')
 f=out/(c['key']+'_before_after.png');fig.savefig(f,dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
 result.append(dict(key=c['key'],title=c['title'],image=f.name,**n))
(O/'comparison_content.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Rendered',len(result),'actual CAD comparisons')
