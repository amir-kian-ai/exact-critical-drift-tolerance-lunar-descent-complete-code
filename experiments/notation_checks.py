"""Targeted equivalence checks for the final notation/indexing revision."""
from pathlib import Path
from fractions import Fraction as Q
import sys,json
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from src.drift_visibility import critical_rates,DriftRecovery,initial
from src.enhanced import Geometry
from src.static_visibility import verify_policy
counts=0
for n in range(1,7):
 for centers in [[],[Q(2),Q(3)],[Q(5,2),Q(11,4),Q(3),Q(7,2)]]:
  alpha,omega=Q(5,2),Q(7,2);w=omega-alpha
  vals={alpha,omega}|{x for x in centers if alpha<=x<=omega}
  old={Q(0),w}|{(u-v)/h for u in vals for v in vals if u>v for h in range(1,n) if (u-v)/h<=w}
  renamed={Q(0),w}|{(xi-zeta)/h for xi in vals for zeta in vals if xi>zeta for h in range(1,n) if (xi-zeta)/h<=w}
  assert old==renamed==set(critical_rates(centers,alpha,omega,n));counts+=1
  if n==1:assert renamed=={Q(0),w}
class IndexedRecovery(DriftRecovery):
 def actions(self,k):
  assert 0<=k<self.cfg.horizon
  return super().actions(k)
for n in (1,2,3):
 cfg=Geometry(horizon=n,footprint=3,visibility_uncertainty=.5);engine=IndexedRecovery(cfg,Q(1,4));b=initial(((6,0),),cfg)
 value,_=engine.solve(0,b);assert value==3*n
 assert verify_policy(engine,0,b,value)
 assert not verify_policy(engine,0,b,value-Q(1,2))
result=dict(rate_formula_equivalence_cases=counts,includes_N1=True,terminal_no_action_checked=True,budget_checks=3,passed=True)
(root/'results/logs/final_notation_checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

