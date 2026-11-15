"""Post-holdout falsification of midpoint/landmark alignment; not holdout data."""
from pathlib import Path
import sys,csv
from itertools import product
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from src.enhanced import Geometry,Recovery
from src.static_visibility import StaticRecovery,initial
from static_oracle import solve as oracle
rows=[]
for shift,l,n,e in product((-1,-.5,0,.5,1),(5.5,6,6.5),(4,5),(.75,.875)):
 cfg=Geometry(horizon=n,landmark=l,footprint=3,visibility_uncertainty=.5,epsilon=e,sites=(-3+shift,3+shift))
 rs=((int(2*(2+shift)),0),(int(2*(3+shift)),0));v=StaticRecovery(cfg).solve(0,initial(rs,cfg))[0];rv=Recovery(cfg).solve(0,rs)[0]
 assert v<=rv
 if l==5.5 and n==4 and e==.875:assert oracle(rs,n,e=e,l=l,R=3,eta=.5,sites=cfg.sites)[0]==v
 rows.append(dict(shift=shift,landmark=l,horizon=n,epsilon=e,static=v,rectangular=rv))
with (root/'results/static/geometry_perturbation.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print('Geometry perturbations',len(rows),'strict',sum(r['static']<r['rectangular'] for r in rows))
