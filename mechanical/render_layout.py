"""Render the actual tessellated placement model for review, not dimensioning."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np

folder = Path(__file__).resolve().parent
mesh = json.loads((folder / 'layout_mesh.json').read_text())
fig, ax = plt.subplots(figsize=(10, 8), layout='constrained')
colors = {'FixedCore': '#334b60', 'MovingCore': '#687e90', 'Gauge30': '#bce1df', 'WindingSpace': '#e8b04f',
          'PCBRegion': '#74aa74', 'HingeRegion': '#d6dce2', 'LatchRegion': '#d6dce2'}
for name, item in mesh.items():
    v = np.asarray(item['vertices'])
    triangles = v[np.asarray(item['triangles'])][:, :, :2]
    ax.add_collection(PolyCollection(triangles, facecolor=colors[name], edgecolor='none', alpha=1))
ax.axhline(0, color='#253d52', linestyle='--', linewidth=.7)
for x, y, label in [(0, 0, '30 mm\ntarget gauge'), (0, 25, 'Moving half'), (24, -10, 'Fixed\nhalf'),
                     (0, -25, 'Winding\nallocation'), (0, -40, 'PCB allocation'), (-39, 0, 'Hinge'), (39, 0, 'Latch')]:
    ax.text(x, y, label, ha='center', va='center', fontsize=10,
            color='white' if label in {'Moving half', 'Fixed\nhalf'} else '#132f43')
ax.set(xlim=(-51, 51), ylim=(-50, 35), xlabel='X (mm)', ylabel='Y (mm)', aspect='equal')
ax.set_title('RFCP clamp placement study | DRAFT — NOT FOR FABRICATION\nManufacturer STEP + assumed allocation volumes; front projection', fontsize=13, pad=20)
ax.grid(alpha=.15)
fig.savefig(folder / 'layout_preview.png', dpi=160)
