from pathlib import Path
import sys,json
from fractions import Fraction as Q
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from drift_oracle import solve
v,n=solve(((4,0),(6,0)),5,lower=Q(2),upper=Q(13,4),gamma=Q(1,2))
assert v==21
(root/'results/drift/motion_independent.json').write_text(json.dumps(dict(horizon=5,gamma='1/2',prior=['2','13/4'],value=float(v),nodes=n,independent_full_history=True),indent=2))
print('Independent moving-probe optimum:',v,'nodes:',n)
