"""Orthographic z-buffer renderer for CAD triangles; no invented geometry.

Used because Matplotlib's painter ordering leaves artifacts on touching CAD
surfaces. Triangles are rendered double-sided with per-pixel depth testing.
"""
import numpy as np
from matplotlib.colors import to_rgb

def render(items, width=1100, height=900, elevation=58, azimuth=-65):
    e,a=np.deg2rad([elevation,azimuth])
    toward=np.array([np.cos(e)*np.cos(a),np.cos(e)*np.sin(a),np.sin(e)])
    right=np.array([-np.sin(a),np.cos(a),0])
    up=np.cross(toward,right)
    basis=np.column_stack([right,up,toward])
    vertices=[];triangles=[];colors=[]
    offset=0
    for item in items:
        v=np.asarray(item['vertices'],dtype=float)
        f=np.asarray(item['triangles'],dtype=int)
        vertices.append(v);triangles.append(f+offset)
        colors.extend([to_rgb(item['color'])]*len(f));offset+=len(v)
    v=np.concatenate(vertices);f=np.concatenate(triangles);colors=np.asarray(colors)
    projection=v@basis
    low=projection[:,:2].min(axis=0); high=projection[:,:2].max(axis=0)
    scale=min(width/(high[0]-low[0]),height/(high[1]-low[1]))*.88
    center=(low+high)/2
    projection[:,0]=(projection[:,0]-center[0])*scale+width/2
    projection[:,1]=height/2-(projection[:,1]-center[1])*scale
    depth=np.full((height,width),-np.inf)
    rgb=np.empty((height,width,3),dtype=np.uint8);rgb[:]=[245,247,250]
    norms=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
    lengths=np.linalg.norm(norms,axis=1)
    norms/=np.where(lengths>1e-12,lengths,1)[:,None]
    # Orient each visible surface normal toward the camera for double-sided CAD.
    norms*=np.where(norms@toward>=0,1,-1)[:,None]
    light=np.array([.25,-.3,.92]);light/=np.linalg.norm(light)
    shades=.56+.44*np.clip(norms@light,0,1)
    colors=np.clip(colors*shades[:,None]*255,0,255).astype(np.uint8)
    for idx,face in enumerate(f):
        tri=projection[face]
        x0=max(0,int(np.floor(tri[:,0].min())));x1=min(width-1,int(np.ceil(tri[:,0].max())))
        y0=max(0,int(np.floor(tri[:,1].min())));y1=min(height-1,int(np.ceil(tri[:,1].max())))
        if x0>x1 or y0>y1:continue
        ax,ay,az=tri[0];bx,by,bz=tri[1];cx,cy,cz=tri[2]
        den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
        if abs(den)<1e-9:continue
        xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        wa=((by-cy)*(xx-cx)+(cx-bx)*(yy-cy))/den
        wb=((cy-ay)*(xx-cx)+(ax-cx)*(yy-cy))/den
        wc=1-wa-wb
        zz=wa*az+wb*bz+wc*cz
        current=depth[y0:y1+1,x0:x1+1]
        visible=(wa>=-1e-8)&(wb>=-1e-8)&(wc>=-1e-8)&(zz>current+1e-7)
        current[visible]=zz[visible]
        rgb[y0:y1+1,x0:x1+1][visible]=colors[idx]
    return rgb
