"""Exploratory development slice; every evaluated case is saved."""
from pathlib import Path
import sys,csv,json,time
from itertools import product
from math import isfinite
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from src.enhanced import Geometry,Recovery
from src.static_visibility import StaticRecovery,initial
out=root/'results/static';out.mkdir(exist_ok=True)
rows=[]
for n,p,R,eta in product((5,7),range(-5,5),(3,4,5),(.5,1)):
 b=((2*p,0),(2*(p+1),0));c=Geometry(horizon=n,footprint=R,visibility_uncertainty=eta,epsilon=.75)
 t=time.perf_counter();g=StaticRecovery(c);sv,act=g.solve(0,initial(b,c));rv=Recovery(c).solve(0,b)[0]
 assert sv<=rv
 row=dict(horizon=n,p=p,footprint=R,eta=eta,epsilon=.75,static=sv,rectangular=rv,action=json.dumps(act),nodes=g.nodes,runtime_s=time.perf_counter()-t);rows.append(row)
 if sv<rv:print('STRICT',row,flush=True)
with (out/'exploration.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print('COMPLETE',len(rows),'strict',sum(r['static']<r['rectangular'] for r in rows),flush=True)
