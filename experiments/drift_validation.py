"""Frozen reserved panel, full critical-rate diagrams and matched exact timing."""
from pathlib import Path
import sys,csv,json,random,time,gc,tracemalloc
from itertools import product
from fractions import Fraction as Q
from dataclasses import replace
from math import inf,isfinite
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from src.enhanced import Geometry,Recovery
from src.drift_visibility import DriftRecovery,initial,all_centers,critical_rates
from src.static_visibility import verify_policy
from drift_oracle import solve as oracle
out=root/'results/drift';out.mkdir(exist_ok=True)
def save(name,rows):
 with (out/f'{name}.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
def bestfixed(cfg,rs,gamma):
 b=initial(rs,cfg);best=(inf,None)
 for schedule in product((0,1),repeat=cfg.horizon):
  eng=DriftRecovery(cfg,gamma,schedule);v,_=eng.solve(0,b)
  if v<best[0]:best=v,schedule
 if isfinite(best[0]):assert verify_policy(DriftRecovery(cfg,gamma,best[1]),0,b,best[0])
 return best
rng=random.Random(20261021);draws=[]
for i in range(16):
 ps=sorted(rng.sample(range(-5,6),2+i%2));draws.append(tuple((2*p,0 if i%2==0 else (-1 if j%2==0 else 1)) for j,p in enumerate(ps)))
cases=list(product(range(16),(3,5),(-5,5.5),(0,.125,.5,1.5)))
select=random.Random(20261022);fixed_ids=set(select.sample(range(len(cases)),16));oracle_ids=set(select.sample([i for i,x in enumerate(cases) if x[1]==3],8))
(out/'reserved_partition.json').write_text(json.dumps(dict(seed=20261021,selection_seed=20261022,draws=draws,cases=cases,fixed_ids=sorted(fixed_ids),oracle_ids=sorted(oracle_ids)),indent=2))
rows=[];fixed=[];checks=[]
for i,(d,n,l,gamma) in enumerate(cases):
 cfg=Geometry(horizon=n,landmark=l,footprint=3.5,visibility_uncertainty=.75,epsilon=.875);rs=draws[d];b=initial(rs,cfg)
 eng=DriftRecovery(cfg,gamma);t=time.perf_counter();v,act=eng.solve(0,b);elapsed=time.perf_counter()-t
 if isfinite(v):assert verify_policy(eng,0,b,v)
 static=DriftRecovery(cfg,0).solve(0,b)[0];rect=Recovery(cfg).solve(0,rs)[0];passive=DriftRecovery(replace(cfg,mode='passive'),gamma).solve(0,b)[0]
 assert static<=v<=rect and v<=passive
 rows.append(dict(case=i,draw=d,horizon=n,landmark=l,gamma=gamma,states=json.dumps(rs),static=float(static),drift=float(v),rectangular=float(rect),passive=float(passive),nodes=eng.nodes,runtime_s=elapsed))
 if i in fixed_ids:
  fv,sched=bestfixed(cfg,rs,gamma);assert v<=fv;fixed.append(dict(case=i,adaptive=float(v),fixed=float(fv),schedule=json.dumps(sched)))
 if i in oracle_ids:
  ov,nodes=oracle(rs,n,e=.875,l=l,lower=2.75,upper=4.25,gamma=gamma);assert ov==v;checks.append(dict(case=i,production=float(v),oracle=float(ov)))
 if i%32==0:print('Reserved',i,flush=True)
save('reserved',rows);save('fixed',fixed);save('independent',checks)
print('Reserved complete',flush=True)
# Exact diagrams: every candidate rate, one interval representative, plus validation thirds.
diagram=[];independent=[]
for name,n,lower,upper in [('old4',4,Q(5,2),Q(7,2)),('motion5',5,Q(2),Q(13,4))]:
 cfg=Geometry(horizon=n,footprint=(lower+upper)/2,visibility_uncertainty=(upper-lower)/2,epsilon=.75)
 rs=((4,0),(6,0));b=initial(rs,cfg);rates=critical_rates(all_centers(cfg),lower,upper,n)
 probes=[(g,'endpoint') for g in rates]+[((a+b)/2,'interior') for a,b in zip(rates,rates[1:])]
 for gamma,kind in sorted(probes):
  eng=DriftRecovery(cfg,gamma);v,_=eng.solve(0,b)
  if isfinite(v):assert verify_policy(eng,0,b,v)
  diagram.append(dict(model=name,horizon=n,lower=str(lower),upper=str(upper),gamma=str(gamma),gamma_float=float(gamma),kind=kind,value=float(v),nodes=eng.nodes))
 for a,bb in zip(rates,rates[1:]):
  mid=(a+bb)/2;expected=next(x['value'] for x in diagram if x['model']==name and Q(x['gamma'])==mid)
  for g in ((2*a+bb)/3,(a+2*bb)/3):assert DriftRecovery(cfg,g).solve(0,b)[0]==expected
 if name=='old4':
  for gamma in (Q(0),Q(1,4),Q(1,2),Q(3,4)):
   v=DriftRecovery(cfg,gamma).solve(0,b)[0];ov,nn=oracle(rs,n,e=.75,lower=lower,upper=upper,gamma=gamma)
   assert v==ov;independent.append(dict(model=name,gamma=str(gamma),production=float(v),oracle=float(ov),oracle_nodes=nn))
 print('Diagram complete',name,flush=True)
save('rate_diagrams',diagram);save('diagram_independent',independent)
timing=[]
for n,count,rep in product((2,3),(2,3),range(3)):
 cfg=Geometry(horizon=n,footprint=3,visibility_uncertainty=.5,epsilon=.75);rs=((4,0),(6,0)) if count==2 else ((2,0),(4,0),(6,0));gamma=Q(1,4);values=[]
 for method in (('interval','history') if rep%2==0 else ('history','interval')):
  gc.collect();tracemalloc.start();t=time.perf_counter()
  if method=='interval':
   eng=DriftRecovery(cfg,gamma);v,_=eng.solve(0,initial(rs,cfg));nodes=eng.nodes
  else:v,nodes=oracle(rs,n,gamma=gamma,endpoint_partition=True)
  elapsed=time.perf_counter()-t;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop();values.append(v)
  timing.append(dict(horizon=n,hypotheses=count,repeat=rep,method=method,value=float(v),nodes=nodes,runtime_s=elapsed,python_peak_bytes=peak))
 assert values[0]==values[1]
save('timings',timing)
summary=dict(reserved=len(rows),drift_finite=sum(isfinite(x['drift']) for x in rows),static_finite=sum(isfinite(x['static']) for x in rows),rectangular_finite=sum(isfinite(x['rectangular']) for x in rows),passive_finite=sum(isfinite(x['passive']) for x in rows),new_vs_rectangular=sum(x['drift']<x['rectangular'] for x in rows),loss_vs_static=sum(x['drift']>x['static'] for x in rows),fixed=len(fixed),fixed_strict=sum(x['adaptive']<x['fixed'] for x in fixed),independent_reserved=len(checks),independent_diagram=len(independent),diagram_points=len(diagram),timings=len(timing))
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
