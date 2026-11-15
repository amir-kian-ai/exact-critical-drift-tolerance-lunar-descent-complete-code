"""Audit matched geometry, certified comparisons and measured implementation cost."""
from pathlib import Path
import csv,json,math,statistics,sys
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from src.enhanced import Geometry,Recovery,check_policy
from enhanced_oracle import feasible
out=root/'results/enhanced'
def read(n):
 with (out/(n+'.csv')).open() as f:return list(csv.DictReader(f))
g=read('geometry');finite=lambda r,k:math.isfinite(float(r[k]))
key=lambda r:tuple(r[k] for k in ('horizon','family','moving','landmark','sites','epsilon','footprint'))
index={(key(r),float(r['visibility_uncertainty'])):r for r in g}
for r in g:
 if float(r['visibility_uncertainty'])==.5:
  assert float(index[key(r),0]['adaptive'])<=float(r['adaptive'])
groups={}
for R,eta in [(math.inf,0),(4,0),(4,.5),(8,0),(8,.5)]:
 rr=[r for r in g if float(r['footprint'])==R and float(r['visibility_uncertainty'])==eta]
 groups[str((R,eta))]={}
 for label,pred in [('all',lambda r:True),('heldout',lambda r:r['heldout']=='1'),('triple_close',lambda r:r['family']=='2'),('moving',lambda r:r['moving']=='1')]:
  ss=[r for r in rr if pred(r)]
  groups[str((R,eta))][label]=dict(n=len(ss),physical=sum(finite(r,'physical') for r in ss),adaptive=sum(finite(r,'adaptive') for r in ss),passive=sum(finite(r,'passive') for r in ss),feasibility_gain=sum(r['value_class']=='feasibility_gain' for r in ss),resource_saving=sum(r['value_class']=='resource_saving' for r in ss))
ab=read('triple_ablation');witnesses=[]
for r in ab:
 if float(r['epsilon'])==.5 and float(r['radius'])==.5 and finite(r,'required'):
  cfg=Geometry(epsilon=.5,footprint=float(r['footprint']),visibility_uncertainty=float(r['eta']))
  b=((-8,0),(8,0),(10,0));v,a=Recovery(cfg).solve(0,b)
  assert feasible(b,5,int(v),e=.5,R=cfg.footprint,eta=cfg.visibility_uncertainty)
  assert not feasible(b,5,int(v)-1,e=.5,R=cfg.footprint,eta=cfg.visibility_uncertainty)
  witnesses.append(dict(**r,action=a))
t=read('efficiency');ratios=[]
for n in (3,5,7):
 for m in (2,3,5,9):
  for R in (math.inf,4):
   rr=[r for r in t if int(r['horizon'])==n and int(r['hypotheses'])==m and float(r['footprint'])==R]
   a=[r for r in rr if r['pruned']=='0'];b=[r for r in rr if r['pruned']=='1']
   med=lambda rows,k:statistics.median(float(r[k]) for r in rows)
   ratios.append(dict(horizon=n,hypotheses=m,footprint=R,unpruned_ms=med(a,'runtime_ms'),pruned_ms=med(b,'runtime_ms'),speedup=med(a,'runtime_ms')/med(b,'runtime_ms'),node_ratio=med(b,'nodes')/med(a,'nodes'),memory_ratio=med(b,'python_peak_bytes')/med(a,'python_peak_bytes')))
p=read('paired_rollouts');pairs=list(zip(p[::2],p[1::2]));wins=[(a,b) for a,b in pairs if a['success']!=b['success']]
assert all(a['certified']=='0' and b['certified']=='0' for a,b in wins)
seed_diffs=[sum(int(a['success'])-int(b['success']) for a,b in pairs if int(a['seed'])==s)/80 for s in range(20)]
result=dict(groups=groups,hard_mask_witnesses=witnesses,efficiency=ratios,efficiency_summary={k:dict(min=min(r[k] for r in ratios),median=statistics.median(r[k] for r in ratios),max=max(r[k] for r in ratios)) for k in ('speedup','node_ratio','memory_ratio')},seed_net_percentage_points=[100*x for x in seed_diffs],discordances_all_uncertified=True)
(out/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
