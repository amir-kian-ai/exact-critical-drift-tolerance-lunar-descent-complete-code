"""Prespecified heldout, boundary, schedule and resource panels."""
from pathlib import Path
import sys,csv,json,random,time,tracemalloc,gc
from itertools import product
from dataclasses import replace
from math import inf,isfinite
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from src.enhanced import Geometry,Recovery
from src.static_visibility import StaticRecovery,initial,verify_policy,successors,propagate,project
from static_oracle import solve as oracle
out=root/'results/static';out.mkdir(exist_ok=True)
def save(n,rows):
 with (out/(n+'.csv')).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
def fixed(cfg,b):
 best=(inf,None)
 for schedule in product((0,1),repeat=cfg.horizon):
  g=StaticRecovery(cfg,schedule=schedule);v,_=g.solve(0,b)
  if v<best[0]:best=v,schedule
 if isfinite(best[0]):assert verify_policy(StaticRecovery(cfg,schedule=best[1]),0,b,best[0])
 return best
def result(cfg,rs):
 b=initial(rs,cfg);g=StaticRecovery(cfg);t=time.perf_counter();v,act=g.solve(0,b);elapsed=time.perf_counter()-t
 t=time.perf_counter()
 if isfinite(v):assert verify_policy(g,0,b,v)
 verifytime=time.perf_counter()-t
 rv=Recovery(cfg).solve(0,rs)[0];reset=StaticRecovery(cfg,reset=True).solve(0,b)[0]
 assert reset==rv and v<=rv
 passive=StaticRecovery(replace(cfg,mode='passive')).solve(0,b)[0];assert v<=passive
 return dict(static=v,rectangular=rv,reset=reset,passive=passive,action=json.dumps(act),nodes=g.nodes,branches=g.edges,synthesis_s=elapsed,verification_s=verifytime)
# Fixed partition instantiated without inspecting heldout outcomes.
rng=random.Random(20261019);draws=[]
for d in range(12):
 ps=sorted(rng.sample(range(-5,6),2+d%3));rs=tuple((2*p,0 if d%2==0 else (-1 if i%2==0 else 1)) for i,p in enumerate(ps));draws.append(rs)
cases=list(product(range(12),(4,6),(-4,5),(3.5,4.5),(.5,.75),(.625,.875)))
select=random.Random(20261020);fixed_indices=set(sum([select.sample([i for i,c in enumerate(cases) if c[1]==n],12) for n in (4,6)],[]))
oracle_indices=set(select.sample([i for i,c in enumerate(cases) if c[1]==4],12))
(out/'partition.json').write_text(json.dumps(dict(draws=draws,cases=cases,fixed_indices=sorted(fixed_indices),oracle_indices=sorted(oracle_indices)),indent=2))
rows=[];comparisons=[];checks=[]
for idx,(d,n,l,R,eta,e) in enumerate(cases):
 rs=draws[d];sites=(-3,3) if d%2==0 else (-2,4);cfg=Geometry(horizon=n,landmark=l,footprint=R,visibility_uncertainty=eta,epsilon=e,sites=sites)
 row=dict(case=idx,draw=d,horizon=n,landmark=l,footprint=R,eta=eta,epsilon=e,sites=json.dumps(sites),states=json.dumps(rs),**result(cfg,rs));rows.append(row)
 if idx in fixed_indices:
  fv,sched=fixed(cfg,initial(rs,cfg));assert row['static']<=fv
  comparisons.append(dict(case=idx,adaptive=row['static'],fixed=fv,schedule=json.dumps(sched),strict=int(row['static']<fv)))
 if idx in oracle_indices:
  ov,_=oracle(rs,n,e=e,l=l,R=R,eta=eta,sites=sites);assert ov==row['static'];checks.append(dict(case=idx,production=row['static'],oracle=ov))
 if idx%64==0:print('Heldout',idx,'/',len(cases),flush=True)
save('heldout',rows);save('fixed',comparisons);save('independent',checks)
# Positive-width witness boundary, geometry and cost perturbations.
boundary=[]
rs=((4,0),(6,0))
for e,eta,R,n,cs in product((0,.25,.5,.625,.75,1),(0,.25,.5,.75,1),(2.75,3,3.25),(4,5),(1,2,3)):
 cfg=Geometry(horizon=n,footprint=R,visibility_uncertainty=eta,epsilon=e,sensing_cost=cs)
 row=dict(epsilon=e,eta=eta,footprint=R,horizon=n,sensing_cost=cs,**result(cfg,rs));boundary.append(row)
save('boundary',boundary);print('Boundary',len(boundary),flush=True)
# Earlier five-step witness; the later four-step construction is also retained.
cfg=Geometry(horizon=5,footprint=3,visibility_uncertainty=.5,epsilon=.75);b=initial(rs,cfg);g=StaticRecovery(cfg);v,act=g.solve(0,b)
assert v==19 and oracle(rs,5,e=.75,R=3,eta=.5)[0]==19
schedules=[dict(schedule=json.dumps(s),cost=StaticRecovery(cfg,schedule=s).solve(0,b)[0]) for s in product((0,1),repeat=5)]
save('witness_schedules',schedules)
tree=[];seen=set()
def traverse(k,b):
 if (k,b) in seen or k==cfg.horizon:return
 seen.add((k,b));value,act=g.solve(k,b);a,s=act
 children=successors(propagate(b,a),s,cfg,labels=True)
 tree.append(dict(k=k,belief=b,cost=value,action=act,children=[dict(output=y,belief=child) for child,y in children]))
 for child,y in children:traverse(k+1,child)
traverse(0,b);(out/'witness_policy.json').write_text(json.dumps(tree,indent=2))
timings=[]
for n,count,rep in product((3,5),(2,3),range(3)):
 cfg=replace(cfg,horizon=n);rs2=((4,0),(6,0)) if count==2 else ((2,0),(4,0),(6,0))
 methods=('static','rectangular','independent_rational') if rep%2==0 else ('independent_rational','rectangular','static')
 values={}
 for method in methods:
  gc.collect();tracemalloc.start();t=time.perf_counter()
  if method=='static':engine=StaticRecovery(cfg);value,_=engine.solve(0,initial(rs2,cfg));nodes=engine.nodes
  elif method=='rectangular':engine=Recovery(cfg,False);value,_=engine.solve(0,rs2);nodes=engine.nodes
  else:value,nodes=oracle(rs2,n,e=.75,R=3,eta=.5)
  elapsed=time.perf_counter()-t;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop();values[method]=value
  timings.append(dict(horizon=n,hypotheses=count,repeat=rep,method=method,value=value,nodes=nodes,runtime_s=elapsed,python_peak_bytes=peak))
 assert values['static']==values['independent_rational']<=values['rectangular']
save('timings',timings)
summary=dict(heldout=len(rows),static_finite=sum(isfinite(r['static']) for r in rows),rectangular_finite=sum(isfinite(r['rectangular']) for r in rows),passive_finite=sum(isfinite(r['passive']) for r in rows),new_feasible=sum(isfinite(r['static']) and not isfinite(r['rectangular']) for r in rows),finite_cost_improvements=sum(isfinite(r['rectangular']) and r['static']<r['rectangular'] for r in rows),fixed_cases=len(comparisons),fixed_strict=sum(r['strict'] for r in comparisons),independent_checks=len(checks),boundary_cases=len(boundary),timing_runs=len(timings))
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
