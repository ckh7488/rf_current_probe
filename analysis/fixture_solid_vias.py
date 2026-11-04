"""Full saved Fixture A03 FDTD exploration. NOT measured or production-qualified.

Actual filled copper/windows/pads, two layers and 45 interconnects. Connector
launch is an explicitly idealized 7 mm shell/5-pin/lumped 50-ohm feed model;
it is not the manufacturer's unseen internal SMA geometry or a TEM reference.
"""
from pathlib import Path
import os,json,argparse,hashlib,sys,time
R=Path(__file__).resolve().parents[1]; O=R/'reviews/recheck_20260922/em_solid'
runtime=R/'tools/openems/v0.37.0-rc2/runtime/openEMS'
os.environ['OPENEMS_INSTALL_PATH']=str(runtime);os.environ['CSXCAD_INSTALL_PATH']=str(runtime)
import numpy as np
from shapely.geometry import Polygon,Point
from shapely import union_all,constrained_delaunay_triangles
import CSXCAD,openEMS as pkg
from CSXCAD import ContinuousStructure
from CSXCAD.SmoothMeshLines import SmoothMeshLines
from openEMS import openEMS
from openEMS.ports import UI_data

ap=argparse.ArgumentParser();ap.add_argument('--name',default='coarse');ap.add_argument('--mesh',type=float,default=1.5);ap.add_argument('--port-mesh',type=float,default=.4);ap.add_argument('--z-mesh',type=float,default=.5);ap.add_argument('--debug-pec',action='store_true');ap.add_argument('--excite',type=int,default=1);ap.add_argument('--margin',type=float,default=80);ap.add_argument('--epsilon',type=float,default=4.3);ap.add_argument('--connector-height',type=float,default=6.4);ap.add_argument('--simplify',type=float,default=0);ap.add_argument('--setup',action='store_true');ap.add_argument('--post',action='store_true');ap.add_argument('--threads',type=int,default=8)
ap.add_argument('--geometry',default='reviews/fixture_em_20260921/geometry.json');ap.add_argument('--max-steps',type=int,default=250000);ap.add_argument('--max-ns',type=float,default=24);ap.add_argument('--fmax-mhz',type=float,default=300);ap.add_argument('--f0-mhz',type=float,default=400);ap.add_argument('--loss-sigma',type=float,default=0);ap.add_argument('--bore-radius',type=float,default=2.2)
ap.add_argument('--end-criteria',type=float,default=1e-5)
args=ap.parse_args();D=O/args.name
if D.exists() and not args.post:raise RuntimeError('Refuse to overwrite existing run '+str(D))
D.mkdir(parents=True,exist_ok=args.post)
g=json.loads((R/args.geometry).read_text()); h=g['thickness']
def shape(row):return Polygon(row['outer'],row['holes'])
board=union_all([shape(r) for r in g['outline']])
# All plated holes are completely occupied by solid PEC in this model.
# Removing them from FR4/copper then filling with the higher-priority PEC is
# physically identical to retaining them in the lower-priority polygons.
# Avoid redundant tiny hole triangulations; preserve all actual NPTH holes.
holes=union_all([Point(p['x'],p['y']).buffer(p['drill']/2,quad_segs=12) for p in g['pads'] if not p['plated']])
board=board.difference(holes)
csx=ContinuousStructure();grid=csx.GetGrid();grid.SetDeltaUnit(1e-3)
fdtd=openEMS(NrTS=args.max_steps,EndCriteria=args.end_criteria,MaxTime=args.max_ns*1e-9);fdtd.SetCSX(csx);fdtd.SetGaussExcite(args.f0_mhz*1e6,args.fmax_mhz*1e6);fdtd.SetBoundaryCond(['PML_8']*6)
fr4=csx.AddMaterial('FR4_assumed_lossless',epsilon=args.epsilon,kappa=args.loss_sigma);ptfe=csx.AddMaterial('connector_PTFE_assumed',epsilon=2.1);air=csx.AddMaterial('connector_bore_air',epsilon=1)
sig=csx.AddMetal('SIG_PEC');gnd=csx.AddMetal('GND_PEC');wire=csx.AddMetal('solid_via_PEC');shell=csx.AddMetal('connector_shell_PEC');pin=csx.AddMetal('connector_pin_PEC')
tri_count=0
def polygons(prop,area,z,thickness=0,priority=10):
 global tri_count
 if args.simplify:area=area.simplify(args.simplify,preserve_topology=True)
 for t in constrained_delaunay_triangles(area).geoms:
  pts=np.array(t.exterior.coords[:-1]).T.tolist();tri_count+=1
  if thickness:prop.AddLinPoly(priority=priority,points=pts,norm_dir=2,elevation=z,length=thickness)
  else:prop.AddPolygon(priority=priority,points=pts,norm_dir=2,elevation=z)
polygons(fr4,board,0,h,0)
for layer,z in [('F.Cu',h),('B.Cu',0)]:
 for net,prop in [('/SIG',sig),('/GND',gnd)]:
  areas=[shape(p) for zone in g['zones'] if zone['layer']==layer and zone['net']==net for p in zone['polygons']]
  areas += [Point(p['x'],p['y']).buffer(p['diameter']/2,quad_segs=12) for p in g['pads']+g['vias'] if p['net']==net]
  polygons(prop,union_all(areas).difference(holes),z)
# openEMS FAQ: finite solid PEC cylinders, radius equal to finished drill/2.
# These are simulation approximations, not a request for filled PCB manufacture.
# Centre/surface mesh lines below explicitly resolve every via without curves.
for p in g['vias']:
 x,y=p['x'],p['y']
 wire.AddCylinder(priority=12,start=[x,y,0],stop=[x,y,h],radius=p['drill']/2)
for p in g['pads']:
 if not p['plated']:continue
 x,y=p['x'],p['y'];prop=sig if p['net']=='/SIG' else gnd
 # Ideal fully solder-filled PTH: resolve a solid electrical connection.
 # A25um PEC shell on a0.25mm grid created disconnected tangential edges.
 prop.AddCylinder(priority=12,start=[x,y,0],stop=[x,y,h],radius=p['drill']/2+.025)
 # Ideal solder bonds connect pins to copper around finished holes. These are
 # not a solder-fillet model; avoid accidental unconnected air gaps in FDTD.
 for z in [0,h]:prop.AddCurve(priority=13,points=[[x-p['diameter']/2,x+p['diameter']/2],[y,y],[z,z]])
# Idealized symmetric launches: actual 5.08 mm footprint, 1.27 mm centre pin,
# 1.0 mm square ground legs. Shell bore, dielectric and height are assumptions.
for k,(x,y) in enumerate(g['ports'],1):
 shell.AddBox(priority=20,start=[x-3.5,y-3.5,3.6],stop=[x+3.5,y+3.5,8.4])
 ptfe.AddCylinder(priority=21,start=[x,y,3.6],stop=[x,y,8.4],radius=args.bore_radius)
 pin.AddCylinder(priority=22,start=[x,y,-.4],stop=[x,y,8.4],radius=.635)
 for dx in [-2.54,2.54]:
  for dy in [-2.54,2.54]:shell.AddBox(priority=22,start=[x+dx-.5,y+dy-.5,-.4],stop=[x+dx+.5,y+dy+.5,3.6])
 # Finite-volume feed leads avoid short-curve edge rasterization ambiguity.
 pin.AddBox(priority=23,start=[x+.5,y-.5,args.connector_height-.5],stop=[x+1,y+.5,args.connector_height+.5])
 shell.AddBox(priority=23,start=[x+2,y-.5,args.connector_height-.5],stop=[x+2.5,y+.5,args.connector_height+.5])

def lines(regions,essential,extent):
 a=list(essential)+[-extent,extent]
 for start,stop,step in regions:a.extend(np.linspace(start,stop,max(2,int(np.ceil((stop-start)/step))+1)))
 a=np.sort(np.unique(np.round(a,7)))
 # Avoid accidental tiny slivers from overlapping region endpoints.
 keep=[a[0]]
 for v in a[1:]:
  if v-keep[-1]>.08:keep.append(v)
 return SmoothMeshLines(np.array(keep),8,ratio=1.5)
m=args.mesh;pm=args.port_mesh
xs=lines([(-76,-4,m),(-4,4,pm),(4,76,m)],[-72,72,0],76+args.margin)
ys=lines([(-51,-38.35,m),(-38.35,-30.35,pm),(-30.35,-25.35,m),(-25.35,-19.35,pm),(-19.35,19.35,m),(19.35,25.35,pm),(25.35,30.35,m),(30.35,38.35,pm),(38.35,51,m)],[-34.35,34.35,0],51+args.margin)
zm=args.z_mesh
zs=lines([(-2,0,zm),(0,h,zm),(h,8.4,zm)],[-3,-6,-10,-16,-25,-40,10,14,20,30,45],args.margin)
# Preserve exact via centres and cylinder surfaces; remove only nonessential
# pre-existing lines within 0.08 mm, avoiding accidental mesh slivers.
def resolve_vias(a,axis,other_required):
 required=np.unique(np.round([p[axis]+q*p['drill']/2 for p in g['vias'] for q in [-1,0,1]]+list(other_required),7))
 a=np.array([v for v in a if min(abs(required-v))>.08])
 return SmoothMeshLines(np.unique(np.r_[a,required]),8,ratio=1.5)
xs=resolve_vias(xs,'x',[0,1,2])
ys=resolve_vias(ys,'y',[0]+[y+dy for x,y in g['ports'] for dy in [-.5,0,.5]])
for d,a in zip('xyz',[xs,ys,zs]):grid.SetLines(d,a)
# Force finite port cross sections onto grid nodes; half-cell ties must not
# collapse the lumped resistor into a zero-area edge.
grid.AddLine('x',[1,2])
essential_z=np.array([0,h,args.connector_height-.5,args.connector_height,args.connector_height+.5])
zs=grid.GetLines('z');zs=np.array([v for v in zs if min(abs(essential_z-v))>.15])
grid.SetLines('z',np.unique(np.r_[zs,essential_z]))
for x,y in g['ports']:grid.AddLine('y',[y-.5,y,y+.5])
ports={}
for k,(x,y) in enumerate(g['ports'],1):ports[k]=fdtd.AddLumpedPort(k,50,[x+2,y-.5,args.connector_height-.5],[x+1,y+.5,args.connector_height+.5],'x',excite=1 if k==args.excite else 0,priority=30)
xs,ys,zs=[grid.GetLines(d) for d in 'xyz']
# Extra nearby integration planes do not change the electromagnetic mesh.
for name,y in [('centre_minus',-0.0001),('centre_plus',0.0001)]:
 probe=csx.AddProbe(name,p_type=1,weight=1,norm_dir=1);probe.AddBox(start=[-5,y,-.7],stop=[5,y,2.3])
probe_names=[]
for i,y in enumerate([-12,-6,0,6,12]):
 for j,(w,z0,z1) in enumerate([(5,-.7,2.3),(8,-1.5,3.1)]):
  name=f'core_{i}_{j}';probe=csx.AddProbe(name,p_type=1,weight=1,norm_dir=1);probe.AddBox(start=[-w,y,z0],stop=[w,y,z1]);probe_names.append((name,y,j))
meta=dict(classification='SIMULATED_MODEL_NOT_MEASURED',source_board_sha256=g['sha256'],script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),openems=pkg.__version__,csxcad=CSXCAD.__version__,parameters=vars(args),mesh=[len(a) for a in [xs,ys,zs]],min_cell_mm=[float(np.min(np.diff(a))) for a in [xs,ys,zs]],via_model='solid PEC AddCylinder, drill radius; no via curves or artificial pad bonds',via_source='https://docs.openems.de/en/latest/faq.html',cells=int(np.prod([len(a)-1 for a in [xs,ys,zs]])),triangle_primitives=tri_count,port_reference='idealized lumped radial feed inside assumed connector; NOT SMA TEM mating face',materials='PEC sheets; lossless assumed FR4/PTFE;45 solid PEC via cylinders at drill radius with centre/surface mesh lines; ideal solid solder-filled SMA PTH',limitations=['No core, winding, actual connector internals, dielectric/conductor loss, cable, or bench included.','Current probe is an Ampere-loop estimate including displacement current through its surface; nested contours and longitudinal probes are compared.','Current model is not calibration approval. Ports require reference validation, convergence and connector sensitivity.'])
(D/'model.json').write_text(json.dumps(meta,indent=2))
if not args.post:
 (D/'model_source.py').write_bytes(Path(__file__).read_bytes())
 csx.Write2XML(str(D/'model.xml'))
 fdtd.Write2XML(str(D/'solver.xml'))
print(json.dumps(dict(model=args.name,cells=meta['cells'],triangles=tri_count,mesh=meta['mesh'])),flush=True)
if not args.post:fdtd.Run(str(D),cleanup=False,setup_only=args.setup,verbose=1,numThreads=args.threads,engine='multithreaded',dump_statistics=True,debug_PEC=args.debug_pec)
if args.setup:sys.exit(0)
freq=np.unique(np.r_[np.geomspace(1e6,500e6,151),[1e6,10e6,30e6,100e6,200e6,300e6,500e6]])
for p in ports.values():p.CalcPort(str(D),freq,ref_impedance=50)
src=ports[args.excite];out=ports[3-args.excite];s11=src.uf_ref/src.uf_inc;s21=out.uf_ref/src.uf_inc
curr={n:UI_data(n,str(D),freq).ui_f_val[0] for n,y,j in probe_names}
rows=[]
for i,f in enumerate(freq):
 a=src.uf_inc[i]/np.sqrt(50);I=curr['core_2_0'][i];ideal=src.uf_inc[i]/50
 row=dict(f_Hz=float(f),S11_re=float(s11[i].real),S11_im=float(s11[i].imag),S21_re=float(s21[i].real),S21_im=float(s21[i].imag),S11_dB=float(20*np.log10(abs(s11[i]))),S21_dB=float(20*np.log10(abs(s21[i]))),HI_re=float((I/a).real),HI_im=float((I/a).imag),I_over_matched_mag=float(abs(I/ideal)),I_over_port_mag=float(abs(I/src.if_tot[i])),I_over_matched_phase_deg=float(np.angle(I/ideal,deg=True)),power_fraction=float(abs(s11[i])**2+abs(s21[i])**2),nested_current_delta_percent=float(100*abs(curr['core_2_1'][i]-I)/max(abs(I),1e-30)),along_core_variation_percent=float(100*max(abs(curr[f'core_{n}_0'][i]-I) for n in range(5))/max(abs(I),1e-30)))
 rows.append(row)
(D/'results.json').write_text(json.dumps(dict(model=meta,rows=rows),indent=2))
import csv
with (D/'hi_empty.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps([r for r in rows if r['f_Hz'] in [1e6,10e6,100e6,300e6,500e6]],indent=2),flush=True)
