"""Deterministic inward-normal STL ray samples. A screening, not proof of global minimum."""
from pathlib import Path
import hashlib, json, struct
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/clamp_A03_DRAFT'
def read_stl(path):
    raw=path.read_bytes(); count=struct.unpack_from('<I',raw,80)[0]
    assert len(raw)==84+count*50
    dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
    return np.frombuffer(raw,dtype=dtype,offset=84)['v'].astype(float)
def screen(path):
    triangles=read_stl(path)
    e1=triangles[:,1]-triangles[:,0]; e2=triangles[:,2]-triangles[:,0]
    normal=np.cross(e1,e2); area=np.linalg.norm(normal,axis=1)
    normal/=area[:,None]
    # Every face centroid plus area-weighted uniform surface samples.
    rng=np.random.default_rng(20260917)
    indices=rng.choice(len(triangles),5000,p=area/area.sum())
    uv=rng.random((len(indices),2)); uv[uv.sum(axis=1)>1]=1-uv[uv.sum(axis=1)>1]
    points=np.concatenate([triangles.mean(axis=1),triangles[indices,0]+uv[:,0,None]*e1[indices]+uv[:,1,None]*e2[indices]])
    directions=-np.concatenate([normal,normal[indices]])
    values=[]
    for k in range(0,len(points),64):
        d=directions[k:k+64]; p=points[k:k+64]
        h=np.cross(d[:,None,:],e2[None,:,:])
        det=np.einsum('mj,bmj->bm',e1,h)
        valid=np.abs(det)>1e-10
        inv=np.divide(1.,det,out=np.zeros_like(det),where=valid)
        s=p[:,None,:]-triangles[None,:,0,:]
        u=inv*np.einsum('bmj,bmj->bm',s,h)
        q=np.cross(s,e1[None,:,:])
        v=inv*np.einsum('bj,bmj->bm',d,q)
        t=inv*np.einsum('mj,bmj->bm',e2,q)
        valid&=(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>1e-4)
        values.extend(np.where(valid,t,np.inf).min(axis=1).tolist())
    values=np.asarray(values)
    suspect=np.where(values<.8)[0]
    result={'stl_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangle_count':len(triangles),
            'sample_count':len(values),'missed_rays':int(np.isinf(values).sum()),
            'minimum_sampled_mm':float(values.min()),'sample_count_under_0_8':len(suspect),
            'thin_samples':[{'point_stl_mm':points[i].tolist(),'inward_direction':directions[i].tolist(),'thickness_mm':float(values[i])} for i in suspect[:100]],
            'percentiles_mm':np.percentile(values[np.isfinite(values)],[0,1,5,50]).tolist()}
    print(json.dumps({'file':str(path),'samples':len(values),'min':result['minimum_sampled_mm'],'under_0_8':len(suspect),'misses':result['missed_rays']}),flush=True)
    return result
r={'data_kind':'CALCULATED','method':'Triangle-centroid and 5000 seeded area-weighted surface points; first inward-normal triangle intersection',
   'limitations':['Finite ray sampling can miss local thin regions; not a global minimum wall or strength guarantee.',
                  'Acute edges and near-tangent rays may report short chords; inspect flagged regions in native CAD.',
                  'No vendor DFM equivalence or printed-part test.'], 'parts':{}}
for rev in ['A02','A03']:
    for name in ['FixedTray','MovingTray']:
        r['parts'][rev+'_'+name]=screen(ROOT/f'mechanical/clamp_{rev}_DRAFT/parts/{name}_DRAFT.stl')
(OUT/'sampled_stl_wall_checks.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
