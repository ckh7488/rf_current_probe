"""Orthographic raster of actual CAD triangles, not an AI concept image."""
from pathlib import Path
import json, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb
P=Path(__file__).resolve().parent;R=P.parent
mesh=json.loads((R/'mechanical/assembly_A14_DRAFT/mesh.json').read_text())
plt.rcParams['font.family']='Malgun Gothic'
fig=plt.figure(figsize=(14,6.8),dpi=160,facecolor='#edf3f7')
def draw(ax,head=False):
 direction=np.array([1,.62,1]);direction/=np.linalg.norm(direction)
 right=np.cross([0,1,0],direction);right/=np.linalg.norm(right);up=np.cross(direction,right)
 light=np.array([.2,1,.65]);light/=np.linalg.norm(light)
 polygons=[];colors=[];depths=[]
 for n,p in mesh.items():
  g=p['group']
  if g.startswith('CALIBRATION') or n=='CalibrationNuts':continue
  if head and not g.startswith('HEAD_'):continue
  v=np.array(p['vertices']);tr=v[np.array(p['triangles'])]
  if head and g=='HEAD_CAP':tr[:, :, 1]+=22
  elif head and g=='HEAD_SCREW':tr[:,:,1]+=45
  norm=np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]);den=np.linalg.norm(norm,axis=1);keep=den>1e-9;norm[keep]/=den[keep,None]
  xy=np.stack([tr@right,tr@up],axis=-1);shade=.58+.42*np.abs(norm@light)
  col=np.clip(np.array(to_rgb(p['color']))[None,:]*shade[:,None],0,1)
  polygons.extend(xy);colors.extend(col);depths.extend(tr.mean(axis=1)@direction)
 order=np.argsort(depths);polygons=np.asarray(polygons);colors=np.asarray(colors)
 ax.add_collection(PolyCollection(polygons[order],facecolors=colors[order],edgecolors='none',antialiased=False))
 ax.autoscale_view();ax.set_aspect('equal');ax.axis('off');ax.set_facecolor('#edf3f7')
draw(fig.add_axes([.015,.08,.65,.8]))
draw(fig.add_axes([.65,.17,.33,.69]),True)
fig.text(.035,.91,'RFCP  /  A14 · C07',fontsize=22,fontweight='bold',color='#183a4c')
fig.text(.037,.86,'분할 바닥 · 열린 코어 · 앞뒤 중심 클램프',fontsize=11,color='#446674')
fig.text(.74,.12,'프로브 상부 개방',fontsize=12,color='#315d6e')
fig.text(.035,.045,'실제 저장 CAD 형상  |  조립 검토본 · 실물 / RF 검증 전',fontsize=10,color='#527383')
fig.savefig(P/'dist/cover-a14.png',facecolor=fig.get_facecolor(),dpi=160)
print('Saved current CAD cover')
