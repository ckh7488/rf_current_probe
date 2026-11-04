"""SIMULATED: quasi-static cross-section screening, NOT a full fixture EM model.

Finite-volume Laplace solve on a nonuniform Cartesian nodal grid. Natural
outer boundary (zero normal flux); grounded return electrodes fix the gauge.
Charge is obtained from electrode edge flux. Both copper faces are treated as
equipotential zero-thickness sheets; via inductance, launches, core and loss
are omitted. All dimensions below are mm; capacitance per length is SI F/m.
"""
from pathlib import Path
import json, hashlib, time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.special import ellipk
from scipy.constants import epsilon_0, c

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reviews/fixture_impedance_20260918'
OUT.mkdir(exist_ok=True)

def axis(anchors, h, domain):
    # Uniform locally refined intervals near every conductor edge, geometric
    # growth out into air. Exact boundaries are retained, not snapped.
    values=set([-domain,domain])
    for a in anchors:
        values.add(a)
        for sign in [-1,1]:
            d=h
            while d<2*domain:
                v=a+sign*d
                if -domain<v<domain: values.add(v)
                d*=1.23
    raw=np.array(sorted(values))
    # Reject redundant points, but preserve all exact anchors.
    keep=[]
    protected=set(anchors)|{-domain,domain}
    for v in raw:
        if keep and v-keep[-1]<h*.24:
            if v in protected:
                if keep[-1] not in protected:keep[-1]=v
                else:keep.append(v)
        else:keep.append(v)
    return np.array(keep)

def capacitance(h=.16, domain=500, er=4.3, benchmark=False, save=False):
    a,b,g=3.4,51.3,71.5
    x=axis([-g,-b,-4,-a,0,a,4,b,g],h,domain)
    y=axis([0] if benchmark else [-.8,0,.8],h,domain)
    nx,ny=len(x),len(y)
    X,Y=np.meshgrid(x,y)
    faces=np.isclose(Y,0,atol=1e-9) if benchmark else np.isclose(abs(Y),.8,atol=1e-9)
    signal=faces&(abs(X)<=a+1e-9)
    ground=faces&(abs(X)>=b-1e-9)&((abs(X)<=g+1e-9) if not benchmark else True)
    fixed=signal|ground
    # Dual-cell widths. Edge epsilon is integrated along the perpendicular
    # dual face; exact y material interfaces are between the electrode planes.
    xb=np.r_[x[0],(x[1:]+x[:-1])/2,x[-1]]
    yb=np.r_[y[0],(y[1:]+y[:-1])/2,y[-1]]
    wx=np.diff(xb); wy=np.diff(yb)
    def overlap(lo,hi,L,H):return np.maximum(0,np.minimum(hi,H)-np.maximum(lo,L))
    # Horizontal conductance: dielectric exists only in solid FR4 strips.
    xm=(x[1:]+x[:-1])/2
    solidx=(abs(xm)<=4)|((abs(xm)>=51)&(abs(xm)<=72))
    fy=overlap(yb[:-1],yb[1:],-.8,.8)/wy
    ex=1+(er-1)*fy[:,None]*solidx[None,:] if not benchmark else np.ones((ny,nx-1))
    gx=ex*wy[:,None]/np.diff(x)[None,:]
    ym=(y[1:]+y[:-1])/2
    fx=(overlap(xb[:-1],xb[1:],-4,4)+overlap(xb[:-1],xb[1:],-72,-51)+overlap(xb[:-1],xb[1:],51,72))/wx
    ey=1+(er-1)*(abs(ym)<.8)[:,None]*fx[None,:] if not benchmark else np.ones((ny-1,nx))
    gy=ey*wx[None,:]/np.diff(y)[:,None]
    ids=np.arange(nx*ny).reshape(ny,nx)
    u=np.r_[ids[:,:-1].ravel(),ids[:-1,:].ravel()]
    v=np.r_[ids[:,1:].ravel(),ids[1:,:].ravel()]
    gval=np.r_[gx.ravel(),gy.ravel()]
    A=coo_matrix((np.r_[gval,gval,-gval,-gval],(np.r_[u,v,u,v],np.r_[u,v,v,u])),shape=(nx*ny,nx*ny)).tocsr()
    free=~fixed.ravel();V=signal.astype(float).ravel()
    V[free]=spsolve(A[free][:,free],-(A@V)[free])
    q=A@V
    cap=float(q[signal.ravel()].sum()*epsilon_0)
    groundq=float(q[ground.ravel()].sum()*epsilon_0)
    energy=float(np.dot(gval,(V[u]-V[v])**2)*epsilon_0)
    result={'h_mm':h,'domain_half_mm':domain,'er':er,'benchmark':benchmark,'nodes':nx*ny,'C_F_per_m':cap,'charge_balance_relative':abs(cap+groundq)/cap,'energy_relative_error':abs(energy-cap)/cap}
    if save:np.savez_compressed(OUT/'potential_field.npz',x=x,y=y,V=V.reshape(ny,nx),signal=signal,ground=ground)
    return result

def run():
    result={'kind':'SIMULATED','model':'2D quasi-static central cross-section; no core/launch/via inductance/loss; not 3D full-board EM','geometry_mm':{'signal_width':6.8,'FR4_center_width':8,'FR4_thickness':1.6,'ground_inner_abs_x':51.3,'ground_outer_abs_x':71.5,'window_length':33.75},'benchmark':[],'cases':[]}
    # Infinite air CPW: Z = 30*pi*K(kprime)/K(k), C = 4*eps0*K(k)/K(kprime).
    k=3.4/51.3
    analytic=4*epsilon_0*ellipk(k*k)/ellipk(1-k*k)
    for h,d in [(.3,1000),(.15,2000),(.075,3000)]:
        r=capacitance(h,d,1,True);r['analytic_C_F_per_m']=analytic;r['relative_error']=r['C_F_per_m']/analytic-1
        result['benchmark'].append(r);print('benchmark',r,flush=True)
    for h,d in [(.3,500),(.15,500),(.075,500),(.15,1000)]:
        air=capacitance(h,d,1)
        diel=capacitance(h,d,4.3,save=h==.075)
        C0,C=air['C_F_per_m'],diel['C_F_per_m']
        result['cases'].append({'air':air,'dielectric':diel,'Z_ohm':1/(c*np.sqrt(C*C0)),'effective_er':C/C0,'L_H_per_m':1/(c*c*C0)})
        print('case',result['cases'][-1],flush=True)
    nominal=result['cases'][2];z=nominal['Z_ohm'];ee=nominal['effective_er'];length=.03375
    result['uniform_section_illustration']=[]
    for mhz in [1,10,30,100,200,300,500]:
        theta=2*np.pi*mhz*1e6*length*np.sqrt(ee)/c
        A=D=np.cos(theta);B=1j*z*np.sin(theta);C=1j*np.sin(theta)/z
        den=A+B/50+C*50+D
        S11=(A+B/50-C*50-D)/den;S21=2/den
        # Current at middle relative to incident wave current a1/sqrt(50).
        # Input current alone is not the centre current at RF.
        vin=1+S11; iin=(1-S11)/50
        imid=iin*np.cos(theta/2)-1j*vin*np.sin(theta/2)/z
        result['uniform_section_illustration'].append({'f_MHz':mhz,'S11_dB':float(20*np.log10(abs(S11))),'S21_dB':float(20*np.log10(abs(S21))),'I_center_over_incident_magnitude':float(abs(imid*50))})
    L=nominal['L_H_per_m']*length;Ctot=nominal['dielectric']['C_F_per_m']*length
    result['low_frequency_pi_matching_candidate']={'L_nH':L*1e9,'intrinsic_C_pF':Ctot*1e12,'extra_shunt_each_end_pF':(L/50**2-Ctot)/2*1e12,'status':'CALCULATED candidate only. Full launches/core/3D and measured S-parameters required before PCB change.'}
    result['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('DONE',OUT,flush=True)
if __name__=='__main__':run()
