"""Theory-directed parameter family, explicitly NOT the heldout panel."""
from pathlib import Path
import sys,csv,json
from itertools import product
from math import inf
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from src.enhanced import Geometry,Recovery
from src.static_visibility import StaticRecovery,initial,verify_policy,successors,propagate
from static_oracle import solve as oracle
rows=[];checks=0
for m,eta,f,e in product((2,3,4),(.5,.625,.75,.875),(.25,.5,.75),(.625,.875,1.25)):
 R=m-1+eta+f*(2-2*eta)
 cfg=Geometry(horizon=4,sites=(-m,m),landmark=2*m,footprint=R,visibility_uncertainty=eta,epsilon=e)
 rs=((2*(m-1),0),(2*m,0));b=initial(rs,cfg);g=StaticRecovery(cfg);v,_=g.solve(0,b)
 fixed=StaticRecovery(cfg,schedule=(0,1,0,0));fv,_=fixed.solve(0,b);rv=Recovery(cfg).solve(0,rs)[0]
 assert v==fv==16 and rv==inf and verify_policy(fixed,0,b,16)
 if f==.5 and e==.625:
  assert oracle(rs,4,e=e,l=2*m,R=R,eta=eta,sites=(-m,m))[0]==v;checks+=1
 rows.append(dict(midpoint=m,eta=eta,fraction=f,epsilon=e,footprint=R,static=v,fixed=fv,rectangular=rv))
out=root/'results/static'
with (out/'theorem_family.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
# Four-step explanatory witness policy under the optimized fixed schedule.
cfg=Geometry(horizon=4,footprint=3,visibility_uncertainty=.5,epsilon=.75)
b=initial(((4,0),(6,0)),cfg);g=StaticRecovery(cfg,schedule=(0,1,0,0));tree=[];seen=set()
def walk(k,b):
 if k==4 or (k,b) in seen:return
 seen.add((k,b));v,act=g.solve(k,b);a,s=act;children=successors(propagate(b,a),s,cfg,labels=True)
 tree.append(dict(k=k,belief=b,value=v,action=act,children=[dict(y=y,belief=c) for c,y in children]))
 for c,y in children:walk(k+1,c)
walk(0,b);(out/'four_step_policy.json').write_text(json.dumps(tree,indent=2))
(out/'theorem_checks.json').write_text(json.dumps(dict(cases=len(rows),independent_queries=checks,all_cost16=True,all_rectangular_infinite=True),indent=2))
print('Theorem-directed cases',len(rows),'independent checks',checks)
