"""Render tessellated CAD parts, never a generated product illustration."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from raster_cad import render

OUT=Path(__file__).resolve().parent/'clamp_A01_DRAFT'
mesh=json.loads((OUT/'assembly_mesh.json').read_text(encoding='utf-8'))
fig=plt.figure(figsize=(15,7.8),facecolor='#f5f7fa')
for col,opened in enumerate([False,True]):
    ax=fig.add_subplot(1,2,col+1)
    ax.set_facecolor('#f5f7fa')
    scene=[]
    for name,item in mesh.items():
        if name in ['FitCoupon','BackingPads','RadialPads','FrontPads','KeeperScrews','KeeperNuts']:continue
        if opened and name=='LatchScrew':continue
        vv=np.array(item['vertices'])
        if opened and name in ['MovingTray','MovingKeeper','MovingCore','LatchNut']:
            vv[:,0]+=40
            vv[:,:2]=vv[:,:2]@np.array([[0,1],[-1,0]])
            vv[:,0]-=40
        scene.append({**item,'vertices':vv})
    ax.imshow(render(scene))
    ax.set_axis_off()
    ax.set_title('Closed clamp' if not opened else '90° open / latch screw removed',loc='left',fontsize=16,color='#203446',pad=-5)
fig.suptitle('RF current probe  |  A0.1 mechanical prototype',x=.04,ha='left',y=.96,fontsize=24,color='#18354b')
fig.text(.04,.895,'DRAFT — NOT FOR FABRICATION   •   Images rendered from the saved CAD geometry',fontsize=12,color='#a2442c')
fig.text(.04,.12,'Teal: PETG tray + keeper     Grey: manufacturer core     Gold: winding / SMA     Green: PCB',fontsize=12,color='#334b5b')
fig.text(.04,.075,'30 mm target aperture  •  20 × 16 mm PCB  •  nylon hinge and screw latch  •  no physical fit or RF test yet',fontsize=12,color='#334b5b')
fig.subplots_adjust(left=.02,right=.99,top=.85,bottom=.16,wspace=.03)
fig.savefig(OUT/'assembly_preview.png',dpi=180,facecolor=fig.get_facecolor())

# Top projection is useful for reviewing insertion route and core seam.
from matplotlib.collections import PolyCollection
fig,ax=plt.subplots(figsize=(9,10),layout='constrained')
for name,item in mesh.items():
    if name in ['FitCoupon','BackingPads','RadialPads','FrontPads']:continue
    vv=np.array(item['vertices']); tris=vv[np.asarray(item['triangles'])]
    # Sort by depth so higher surfaces hide lower surfaces.
    # Collect globally below, not object-by-object, for correct overlap.
    if 'all_tri' not in locals(): all_tri=[]
    for tri in tris:all_tri.append((tri[:,2].mean(),tri[:,:2],item['color']))
all_tri.sort(key=lambda x:x[0])
ax.add_collection(PolyCollection([t[1] for t in all_tri],facecolors=[t[2] for t in all_tri],edgecolors='none',antialiased=False))
ax.add_patch(plt.Circle((0,0),15,fill=False,linestyle='--',edgecolor='#217d71',linewidth=1.4))
ax.text(0,0,'Ø30 mm\ntarget gauge',ha='center',va='center',fontsize=13,color='#18554e')
ax.axhline(0,color='#526c7b',linestyle=':',linewidth=.7)
ax.annotate('Continuous 5-turn winding',xy=(1,-27),xytext=(0,-59),ha='center',arrowprops={'arrowstyle':'->','color':'#6e572c'},fontsize=11)
ax.annotate('20 × 16 mm PCB',xy=(8,-43),xytext=(32,-46),ha='center',arrowprops={'arrowstyle':'->'},fontsize=10)
ax.annotate('M3 nylon hinge',xy=(-40,1),xytext=(-28,43),ha='center',arrowprops={'arrowstyle':'->'},fontsize=10)
ax.annotate('M3 nylon screw latch',xy=(40,-4),xytext=(23,43),ha='center',arrowprops={'arrowstyle':'->'},fontsize=10)
ax.set(xlim=(-50,50),ylim=(-63,49),aspect='equal',xlabel='X (mm)',ylabel='Y (mm)')
ax.grid(alpha=.12)
ax.set_title('RFCP A0.1 | actual CAD front projection\nDRAFT — nominal geometry, not a measured assembly',fontsize=14)
fig.savefig(OUT/'front_projection.png',dpi=170)
