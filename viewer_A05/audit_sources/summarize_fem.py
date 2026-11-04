from pathlib import Path
import re,json,math,sys
import numpy as np
O=Path(__file__).resolve().parent/(sys.argv[1] if len(sys.argv)>1 else 'fem'); rows=[]
for p in sorted(O.glob('mesh_*/lid.dat')):
 text=p.read_text(); f=re.search(r'total force .*?\n\s*\n\s*([^\n]+)',text).group(1)
 reaction=[float(x) for x in f.split()]
 block=text.split('stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz)')[-1].splitlines()[2:]
 s=[];ids=[]
 for line in block:
  x=line.split()
  if len(x)!=8:continue
  try: ids.append([int(x[0]),int(x[1])]);s.append([float(v) for v in x[2:]])
  except ValueError:continue
 s=np.array(s);a,b,c,d,e,f=s.T
 vm=np.sqrt(((a-b)**2+(b-c)**2+(c-a)**2)/2+3*(d*d+e*e+f*f)); k=int(vm.argmax())
 # All integration points, not extrapolated nodal singular peaks.
 r=json.loads((p.parent/'settings.json').read_text());r.update(reaction_N=reaction,integration_points=len(vm),max_von_mises_MPa=float(vm[k]),max_stress_element_ip=ids[k],von_mises_percentiles_MPa=np.percentile(vm,[95,99,99.9]).tolist(),straight_sided_quadratic_tets=True)
 rows.append(r)
force_delta=abs(rows[0]['reaction_N'][1]-rows[1]['reaction_N'][1])/abs(rows[0]['reaction_N'][1])*100
stress_delta=abs(rows[0]['max_von_mises_MPa']-rows[1]['max_von_mises_MPa'])/abs(rows[0]['max_von_mises_MPa'])*100
result=dict(classification='SIMULATED',models=rows,two_mesh_relative_change_percent=dict(reaction=force_delta,peak_stress=stress_delta),limits=['No measured material, contact, creep, fatigue, humidity or strength allowable.','Two meshes compare one boundary condition only; sharp-edge peak stress may not converge.'])
(O/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
