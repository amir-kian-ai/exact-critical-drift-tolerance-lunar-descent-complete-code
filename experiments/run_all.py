"""Execute exact grids, paired simulation, ablations, and scaling measurements."""
import sys, json, csv, time, platform, tracemalloc, hashlib, os
from pathlib import Path
from dataclasses import replace,asdict
from math import isfinite
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache'/'matplotlib'))
from src.siv import *
from src.controllers import Controller

OUT=ROOT/'results'
for sub in ('data','figures','tables','logs'):(OUT/sub).mkdir(parents=True,exist_ok=True)
def save(name,rows):
    with (OUT/'data'/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def finite(x):return x if isfinite(x) else None

def grids():
    rows=[];witnesses=[]
    for n in (2,3,4,5,6):
        cfg=Config(horizon=n)
        games={m:Game(replace(cfg,mode=m)) for m in ('siv','passive','blind')}
        for p2 in range(2,17):
            b=((-p2,0),(p2,0))
            phys=max(games['siv'].solve(0,(x,))[0] for x in b)
            req={m:g.solve(0,b)[0] for m,g in games.items()}
            for fuel in range(3*n,3*n+13):
                rows.append(dict(horizon=n,altitude_m=vertical(0,n)[0],half_separation_m=p2/2,budget_mps=fuel,
                                 physical=int(phys<=fuel),siv=int(req['siv']<=fuel),passive=int(req['passive']<=fuel),blind=int(req['blind']<=fuel)))
            if isfinite(req['siv']):
                assert verify_policy(games['siv'],0,b,req['siv'])
            witnesses.append(dict(horizon=n,half_separation_m=p2/2,physical_required=finite(phys),
                                  siv_required=finite(req['siv']),passive_required=finite(req['passive']),blind_required=finite(req['blind'])))
    save('region',rows);(OUT/'data'/'requirements.json').write_text(json.dumps(witnesses,indent=2))
    return rows

def sensitivity():
    rows=[]
    for eps in (0.,.25,.5,1.,2.,4.):
      for delay in range(5):
       for sensing in (0,1,2,4,8):
        for p in (2.,4.,5.,6.,7.):
         cfg=Config(epsilon=eps,delay=delay,sensing_cost=sensing)
         req,act=Game(cfg).solve(0,((-int(2*p),0),(int(2*p),0)))
         rows.append(dict(epsilon_m=eps,delay_s=delay,sensing_cost_mps=sensing,half_separation_m=p,
                          required_budget_mps=req,certified_at_21=int(req<=21),first_acceleration=None if act is None else act[0],first_sensing=None if act is None else act[1]))
    save('sensitivity',rows)

def rollout(name,cfg,b,fuel,seed):
    rng=np.random.default_rng(seed)
    true=b[int(rng.integers(len(b)))]; initial=true
    ctrl=Controller(name,cfg)
    belief=b; used=0; safe=True; margin=float('inf'); vmargin=float('inf'); times=[];trajectory=[];first_sensing=-1
    for k in range(cfg.horizon):
        t=time.perf_counter_ns();a,s=ctrl.choose(k,belief);times.append((time.perf_counter_ns()-t)/1e6)
        if s and first_sensing<0:first_sensing=k
        safe &= tube_safe(true,a,cfg)
        ps,vs=tube_slacks(true,a,cfg)
        margin=min(margin,ps);vmargin=min(vmargin,vs)
        used+=cost(a,s,cfg);safe &= used<=fuel
        true=step(true,a)
        pred=canonical(step(x,a) for x in belief)
        y=abs(true[0]/2-(cfg.landmark if s else 0))+rng.uniform(-cfg.epsilon,cfg.epsilon)
        belief=update(pred,s,y,cfg)
        assert true in belief
        trajectory.append(dict(k=k+1,p=true[0]/2,v=true[1],z=vertical(k+1,cfg.horizon)[0],a=a,s=s,belief_size=len(belief),remaining=fuel-used))
    return dict(controller=name,seed=seed,horizon=cfg.horizon,half_separation_m=abs(initial[0]/2),budget_mps=fuel,
                success=int(safe and terminal(true,cfg)),allocated_resource_mps=used,
                initial_position_m=initial[0]/2,action_trace=';'.join(f"{t['a']}:{t['s']}" for t in trajectory),
                terminal_position_error_m=abs(abs(true[0]/2)-cfg.target),terminal_velocity_error_mps=abs(true[1]),
                minimum_corridor_slack_m=margin,minimum_speed_slack_mps=vmargin,first_sensing_s=first_sensing,update_mean_ms=np.mean(times),update_max_ms=max(times)),trajectory

def comparisons():
    rows=[];trajectories={}
    names=('nominal_mpc','robust_mpc','passive','information_greedy','siv','free_sensing')
    for p in (1,2,3,4,5,6,7):
      b=((-2*p,0),(2*p,0));cfg=Config()
      exact=Game(cfg).solve(0,b)[0]
      for fuel in (17,19,21,23):
       for seed in range(20):
        for name in names:
         row,tr=rollout(name,cfg,b,fuel,seed)
         ctrl=Controller(name,cfg)
         claimed=ctrl.game.solve(0,b)[0] if name in ('siv','robust_mpc','passive','free_sensing') else float('inf')
         row.update(certified=int(claimed<=fuel),exact_feasible=int(exact<=fuel))
         rows.append(row)
         if p==6 and fuel==21 and seed==0:trajectories[name]=tr
    save('rollouts',rows)
    (OUT/'data'/'trajectories.json').write_text(json.dumps(trajectories,indent=2))
    summary=[]
    for name in names:
        r=[x for x in rows if x['controller']==name];n=len(r)
        cert=[x for x in r if x['certified']];feas=[x for x in r if x['exact_feasible']]
        summary.append(dict(controller=name,trials=n,success_rate=np.mean([x['success'] for x in r]),
          certified_rate=len(cert)/n,certificate_coverage=None if not cert else np.mean([x['success'] for x in cert]),
          false_infeasibility=None if name in ('nominal_mpc','information_greedy','free_sensing') else np.mean([1-x['certified'] for x in feas]),
          mean_allocated_resource_mps=np.mean([x['allocated_resource_mps'] for x in r]),
          mean_terminal_position_error_m=np.mean([x['terminal_position_error_m'] for x in r]),
          mean_terminal_velocity_error_mps=np.mean([x['terminal_velocity_error_mps'] for x in r]),
          update_mean_ms=np.mean([x['update_mean_ms'] for x in r]),update_max_ms=max(x['update_max_ms'] for x in r)))
    (OUT/'data'/'comparison.json').write_text(json.dumps(summary,indent=2))
    return summary

def scaling():
    rows=[]
    for n in (3,4,5,6,7):
      for count in (2,3,5,9):
       encoded={2:(-12,12),3:(-12,0,12),5:(-12,-6,0,6,12),9:(-12,-9,-6,-3,0,3,6,9,12)}
       cfg=Config(horizon=n);b=canonical((p,0) for p in encoded[count])
       for rep in range(3):
        g=Game(cfg);tracemalloc.start();start=time.perf_counter_ns()
        req,act=g.solve(0,b)
        runtime=(time.perf_counter_ns()-start)/1e6
        _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        rows.append(dict(horizon=n,hypotheses=len(b),repeat=rep,runtime_ms=runtime,python_peak_bytes=peak,nodes=g.nodes,successor_edges=g.edges,required_budget=req,solver_iterations=0))
    save('scaling',rows)

def main():
    start=time.time();grid=grids();print('grid complete',flush=True)
    sensitivity();print('sensitivity complete',flush=True)
    summary=comparisons();print('comparisons complete',flush=True)
    scaling();print('scaling complete',flush=True)
    import matplotlib
    (OUT/'logs'/'environment.json').write_text(json.dumps(dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),numpy=np.__version__,matplotlib=matplotlib.__version__,elapsed_s=time.time()-start),indent=2))
    from plotting import plot_all
    plot_all(OUT)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
