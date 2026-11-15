from pathlib import Path
import sys,csv
from itertools import product
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from src.enhanced import Geometry,Recovery
from src.drift_visibility import DriftRecovery,initial
from src.static_visibility import verify_policy
out=root/'results/drift';out.mkdir(exist_ok=True)
rows=[]
for n,gamma in product((4,5),(0,1/64,1/8,1/4,1/2,1)):
 cfg=Geometry(horizon=n,footprint=3,visibility_uncertainty=.5,epsilon=.75)
 g=DriftRecovery(cfg,gamma);b=initial(((4,0),(6,0)),cfg);v,_=g.solve(0,b)
 rows.append(dict(panel='old',r=3,horizon=n,epsilon=.75,gamma=gamma,cost=float(v)))
 print(rows[-1],flush=True)
for r,e,gamma in product((2,3,4),(.625,.875),(0,.125,.25,.5,.625,1.25)):
 cfg=Geometry(horizon=5,landmark=2*r,sites=(-r,r),footprint=r-.375,visibility_uncertainty=.625,epsilon=e)
 g=DriftRecovery(cfg,gamma);b=initial(((2*(r-1),0),(2*r,0)),cfg);v,_=g.solve(0,b)
 if v<float('inf'):assert verify_policy(g,0,b,v)
 rows.append(dict(panel='motion',r=r,horizon=5,epsilon=e,gamma=gamma,cost=float(v)))
 print(rows[-1],flush=True)
with (out/'diagnostic.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
