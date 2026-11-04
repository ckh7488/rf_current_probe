"""Render the actual old/new fixed-tray underside with the existing CAD rasterizer."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from raster_cad import render
ROOT=Path(__file__).resolve().parent
fig,axes=plt.subplots(1,2,figsize=(13,7),facecolor='#f5f7fa')
for ax,rev,title in zip(axes,['A02','A03'],['A0.2 | before','A0.3 | reinforced']):
    m=json.loads((ROOT/f'clamp_{rev}_DRAFT/assembly_mesh.json').read_text(encoding='utf-8'))
    ax.imshow(render([m['FixedTray']],elevation=-58,azimuth=-65));ax.axis('off')
    ax.set_title(title,loc='left',color='#18354b',fontsize=17)
fig.suptitle('Fixed tray underside | nut pocket reinforcement',x=.04,ha='left',fontsize=21,color='#18354b')
fig.text(.04,.89,'DRAFT - nominal CAD geometry; not a strength or print-fit test',color='#a2442c',fontsize=12)
fig.text(.04,.08,'Same screw centers and keepers. Two 8.4 mm diameter bosses added on each tray.',fontsize=12)
fig.text(.04,.035,'Audited side-wall point: 0.448 -> 2.241 mm. Boss radial wall >= 1.833 mm; roof 1.2 mm.',fontsize=12)
fig.subplots_adjust(left=.025,right=.985,top=.85,bottom=.13,wspace=.02)
fig.savefig(ROOT/'clamp_A03_DRAFT/reinforcement_before_after.png',dpi=160)
