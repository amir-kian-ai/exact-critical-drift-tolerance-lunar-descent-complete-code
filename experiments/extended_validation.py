"""Fixed-factorial robustness panel; no tuning of the original experiments."""
from pathlib import Path
from itertools import product
from dataclasses import replace
from math import isfinite
import csv,json,sys
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from src.siv import Game,Config,verify_policy
from review_oracle import feasible

rows=[];oracle_checks=0
for n,d,shift,count,landmark in product((2,3,4,5),(2,4,6),(-1,0,1),(2,3),(3,6)):
    positions=[shift-d,shift+d]+([shift+d+1] if count==3 else [])
    b=tuple((2*p,0) for p in positions);cfg=Config(horizon=n,landmark=landmark)
    g=Game(cfg);value,act=g.solve(0,b)
    physical=max(g.solve(0,(x,))[0] for x in b)
    passive=Game(replace(cfg,mode='passive')).solve(0,b)[0]
    blind=Game(replace(cfg,mode='blind')).solve(0,b)[0]
    assert physical<=value<=passive<=blind
    if isfinite(value):
        assert verify_policy(g,0,b,value)
        assert feasible(b,n,int(value),landmark=landmark)
        assert not feasible(b,n,int(value)-1,landmark=landmark)
        oracle_checks+=2
    else:
        assert not feasible(b,n,6*n,landmark=landmark);oracle_checks+=1
    row=dict(horizon=n,half_separation_m=d,shift_m=shift,hypotheses=count,landmark_m=landmark,
             initial_positions=json.dumps(positions),physical_required=physical,siv_required=value,
             passive_required=passive,blind_required=blind,first_action=json.dumps(act))
    rows.append(row)
out=root/'results/data'
with (out/'extended_validation.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
def summary(rr):
    return dict(cases=len(rr),**{k:sum(isfinite(r[k+'_required']) for r in rr) for k in ('physical','siv','passive','blind')},
                strict_siv_over_passive=sum(r['siv_required']<r['passive_required'] for r in rr))
groups={f'{count}_hypotheses_{kind}':summary([r for r in rows if r['hypotheses']==count and (r['shift_m']==0 if kind=='unshifted' else r['shift_m']!=0)]) for count in (2,3) for kind in ('unshifted','shifted')}
for r in rows:
 if r['hypotheses']==3:
    pair=next(x for x in rows if all(x[k]==r[k] for k in ('horizon','half_separation_m','shift_m','landmark_m')) and x['hypotheses']==2)
    assert pair['siv_required']<=r['siv_required']
threshold=[]
for eps in (0,.5,2,4,5.5,6,6.5):
    v,a=Game(Config(epsilon=eps)).solve(0,((-12,0),(12,0)))
    threshold.append(dict(epsilon_m=eps,required=v if isfinite(v) else None,action=a))
result=dict(overall=summary(rows),groups=groups,independent_budget_checks=oracle_checks,noise_threshold=threshold)
(out/'extended_summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
