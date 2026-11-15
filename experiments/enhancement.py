"""Predeclared scientific stress panels; no optimization over reported cases."""
from pathlib import Path
from itertools import product
from dataclasses import replace,asdict
from math import inf,isfinite
import csv,json,sys,time,tracemalloc,random,platform,gc
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from src.siv import step,tube_safe,canonical
from src.enhanced import Geometry,Recovery,goal,check_policy,information_value,outputs,observed_update
from enhanced_oracle import feasible
out=root/'results/enhanced';out.mkdir(exist_ok=True)
def save(name,rows):
    with (out/(name+'.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
def states(ps,moving):return tuple((2*p,(-1 if i%2==0 else 1) if moving else 0) for i,p in enumerate(ps))
families=[(-4,4),(-3,5),(-4,4,5),(-4,0,4),(-4,-1,2,5)]
models=[(inf,0),(4,0),(4,.5),(8,0),(8,.5)]
rows=[];independent=0
for n,fi,l,moving,sites,e in product((3,5,7),range(5),(-6,3,6),(False,True),((-3,3),(-2,4)),(.25,.5)):
 b=states(families[fi],moving)
 for R,eta in models:
    cfg=Geometry(horizon=n,landmark=l,sites=sites,epsilon=e,footprint=R,visibility_uncertainty=eta)
    g=Recovery(cfg);v,a=g.solve(0,b);reference=Recovery(cfg,False).solve(0,b)
    assert (v,a)==reference
    physical=max(Recovery(cfg).solve(0,(x,))[0] for x in b)
    passive=Recovery(replace(cfg,mode='passive')).solve(0,b)[0]
    assert physical<=v<=passive
    if isfinite(v):assert check_policy(g,0,b,v)
    if n==3 and l==3 and not moving and sites==(-3,3):
        kwargs=dict(e=e,l=l,R=R,eta=eta,sites=sites)
        assert feasible(b,n,int(v) if isfinite(v) else 6*n,**kwargs)==isfinite(v);independent+=1
        if isfinite(v):assert not feasible(b,n,int(v)-1,**kwargs);independent+=1
    tag,saving=information_value(passive,v)
    rows.append(dict(horizon=n,family=fi,positions=json.dumps(families[fi]),moving=int(moving),landmark=l,sites=json.dumps(sites),epsilon=e,footprint=R,visibility_uncertainty=eta,physical=physical,adaptive=v,passive=passive,value_class=tag,saving=saving,first_action=json.dumps(a),heldout=int(n==7 or l==-6)))
save('geometry',rows);print('Enhanced geometry complete',len(rows),flush=True)
# Historical mechanism decomposition with overlapping flags.
historical=[]
with (root/'results/data/extended_validation.csv').open() as f:old=list(csv.DictReader(f))
for r in old:
 n=int(r['horizon']);ps=json.loads(r['initial_positions']);b=states(ps,False);cfg=Geometry(horizon=n,landmark=float(r['landmark_m']))
 physical=float(r['physical_required']);v=float(r['siv_required'])
 first=[]
 for x in b:
    first.append({a for a in (-1,0,1) if tube_safe(x,a,cfg) and isfinite(Recovery(cfg).solve(1,(step(x,a),))[0])})
 common=bool(set.intersection(*first))
 persistent=any(0<abs(p-q)<=1 for i,p in enumerate(ps) for q in ps[i+1:])
 cause='feasible' if isfinite(v) else 'physical' if not isfinite(physical) else 'first_action' if not common else 'persistent_pair' if persistent else 'residual_information'
 delayed=Recovery(replace(cfg,delay=1)).solve(0,b)[0]
 historical.append(dict(**r,category=cause,empty_common_first=int(not common),persistent_pair=int(persistent),delay_loss=int(isfinite(v) and not isfinite(delayed)),budget_shortage=int(isfinite(v) and v>3*n+4)))
save('historical_failures',historical)
# Exact best precommitted schedule; matched execution diagnostics.
comparisons=[];rollouts=[]
for idx,(n,fi,l,moving,R) in enumerate(product((3,5),range(5),(3,6),(False,True),(inf,4))):
 cfg=Geometry(horizon=n,landmark=l,footprint=R);b=states(families[fi],moving)
 adaptive=Recovery(cfg);av,aa=adaptive.solve(0,b)
 best=(inf,None,None)
 for sched in product((0,1),repeat=n):
    engine=Recovery(cfg,schedule=sched);v,a=engine.solve(0,b)
    if v<best[0]:best=(v,sched,engine)
 fv,schedule,fixed=best
 if fixed is None:schedule=(0,)*n;fixed=Recovery(cfg,schedule=schedule)
 assert av<=fv
 if isfinite(fv):assert check_policy(fixed,0,b,fv)
 comparisons.append(dict(case=idx,horizon=n,family=fi,landmark=l,moving=int(moving),footprint=R,adaptive=av,fixed=fv,schedule=json.dumps(schedule),strict=int(av<fv)))
 budget=3*n+6
 for seed in range(20):
    rng=random.Random(20261018+seed);truth=b[rng.randrange(len(b))];errors=[rng.uniform(-.5,.5) for _ in range(n)]
    for name,engine in [('adaptive',adaptive),('fixed_schedule',fixed)]:
        x=truth;belief=b;remaining=budget;safe=True;trace=[]
        for k in range(n):
            _,act=engine.solve(k,belief)
            if act is None:act=(0,schedule[k] if name=='fixed_schedule' else 0)
            a,s=act;safe=safe and tube_safe(x,a,cfg);x=step(x,a)
            remaining-=3+abs(a)+2*s;safe=safe and remaining>=0
            center=abs(x[0]/2-(l if s else 0));y=center+errors[k] if center<=R else None
            belief=observed_update(canonical(step(r,a) for r in belief),s,y,cfg)
            assert x in belief
            trace.append(act)
        rollouts.append(dict(case=idx,seed=seed,controller=name,budget=budget,success=int(safe and goal(x,cfg)),certified=int(engine.solve(0,b)[0]<=budget),trace=json.dumps(trace),resource=budget-remaining))
save('comparator',comparisons);save('paired_rollouts',rollouts);print('Comparator complete',len(comparisons),flush=True)
threshold=[]
for eps,delay in product([4+i*.25 for i in range(11)],range(6)):
 cfg=Geometry(epsilon=eps,delay=delay);v,a=Recovery(cfg).solve(0,((-12,0),(12,0)))
 threshold.append(dict(epsilon=eps,delay=delay,required=v,feasible17=int(v<=17),feasible19=int(v<=19),feasible23=int(v<=23),feasible30=int(v<=30)))
save('threshold',threshold)
ablation=[]
for e,eta,R,radius in product((0,.25,.5,.75),(0,.25,.5,.75),(4,8),(.5,1)):
 cfg=Geometry(epsilon=e,visibility_uncertainty=eta,footprint=R,radius=radius)
 v,a=Recovery(cfg).solve(0,((-8,0),(8,0),(10,0)))
 ablation.append(dict(epsilon=e,eta=eta,footprint=R,radius=radius,required=v))
save('triple_ablation',ablation)
timings=[]
for n,count,R,rep in product((3,5,7),(2,3,5,9),(inf,4),range(3)):
 coords={2:[-8,8],3:[-8,0,8],5:[-8,-4,0,4,8],9:list(range(-8,9,2))}[count];b=tuple((p,0) for p in coords)
 cfg=Geometry(horizon=n,footprint=R,visibility_uncertainty=.5)
 answers=[]
 for prune in ((False,True) if rep%2==0 else (True,False)):
    gc.collect()
    tracemalloc.start();t=time.perf_counter();g=Recovery(cfg,prune);ans=g.solve(0,b);elapsed=1000*(time.perf_counter()-t);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop();answers.append(ans)
    timings.append(dict(horizon=n,hypotheses=count,footprint=R,repeat=rep,pruned=int(prune),required=ans[0],nodes=g.nodes,successors=g.edges,raw_successors=g.raw_edges,runtime_ms=elapsed,python_peak_bytes=peak))
 assert answers[0]==answers[1]
save('efficiency',timings)
summary=dict(geometry_cases=len(rows),independent_queries=independent,comparator_cases=len(comparisons),paired_rollouts=len(rollouts),timing_runs=len(timings),python=sys.version,platform=platform.platform(),processor=platform.processor())
summary['geometry_by_model']={str((R,eta)):dict(cases=sum(r['footprint']==R and r['visibility_uncertainty']==eta for r in rows),physical=sum(isfinite(r['physical']) for r in rows if r['footprint']==R and r['visibility_uncertainty']==eta),adaptive=sum(isfinite(r['adaptive']) for r in rows if r['footprint']==R and r['visibility_uncertainty']==eta),passive=sum(isfinite(r['passive']) for r in rows if r['footprint']==R and r['visibility_uncertainty']==eta)) for R,eta in models}
summary['historical_categories']={k:sum(r['category']==k for r in historical) for k in sorted({r['category'] for r in historical})}
summary['fixed_comparison']=dict(adaptive=sum(isfinite(r['adaptive']) for r in comparisons),fixed=sum(isfinite(r['fixed']) for r in comparisons),strict=sum(r['strict'] for r in comparisons))
summary['rollouts']={name:dict(success=sum(r['success'] for r in rollouts if r['controller']==name),certified=sum(r['certified'] for r in rollouts if r['controller']==name),certified_failures=sum(r['certified'] and not r['success'] for r in rollouts if r['controller']==name)) for name in ('adaptive','fixed_schedule')}
pairs=[(rollouts[i],rollouts[i+1]) for i in range(0,len(rollouts),2)]
summary['paired']=dict(adaptive_only=sum(a['success'] and not b['success'] for a,b in pairs),fixed_only=sum(b['success'] and not a['success'] for a,b in pairs),trace_differences=sum(a['trace']!=b['trace'] for a,b in pairs))
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
