from fractions import Fraction as Q
from itertools import product
from math import inf
from src.enhanced import Geometry,Recovery
from src.drift_visibility import DriftRecovery,initial,expand,update,critical_rates,all_centers
from src.static_visibility import StaticRecovery,initial as static_initial,verify_policy
from drift_oracle import feasible,solve as independent

def test_all_short_history_criteria():
    cfg=Geometry(footprint=3,visibility_uncertainty=.5,epsilon=0)
    symbols=list(product((Q(2),Q(5,2),Q(3),Q(7,2)),(False,True)))
    for n in range(1,5):
        for history in product(symbols,repeat=n):
            for gamma in (Q(0),Q(1,8),Q(1,2),Q(1)):
                b=initial(((0,0),),cfg)
                for center,detect in history:
                    b=tuple((int(2*center),0,lo,hi,cl) for p,v,lo,hi,cl in b)
                    b=update(expand(b,cfg,gamma),0,center if detect else None,cfg)
                assert bool(b)==feasible(history,Q(5,2),Q(7,2),gamma)

def test_open_endpoint_and_saturation():
    cfg=Geometry(footprint=3,visibility_uncertainty=.5)
    b=((0,0,Q(5,2),Q(3),False),)
    assert expand(b,cfg,Q(1,2))[0][-1] is False
    assert expand(b,cfg,Q(5,8))[0][-1] is True
    h=((Q(3),True),(Q(5,2),False))
    assert not feasible(h,Q(2),Q(4),Q(1,2))
    assert feasible(h,Q(2),Q(4),Q(5,8))

def test_limit_models_and_ordering():
    rs=((4,0),(6,0))
    for n in (2,3,4):
        cfg=Geometry(horizon=n,footprint=3,visibility_uncertainty=.5,epsilon=.75)
        vals=[DriftRecovery(cfg,g).solve(0,initial(rs,cfg))[0] for g in (0,.25,1)]
        assert vals==sorted(vals)
        assert vals[0]==StaticRecovery(cfg).solve(0,static_initial(rs,cfg))[0]
        assert vals[-1]==Recovery(cfg).solve(0,rs)[0]

def test_moving_probe_safe_at_closed_rate_boundary():
    for r in (2,3,4):
        cfg=Geometry(horizon=5,landmark=2*r,sites=(-r,r),footprint=r-.375,visibility_uncertainty=.625,epsilon=.875)
        b=initial(((2*(r-1),0),(2*r,0)),cfg)
        g=DriftRecovery(cfg,.5,schedule=(0,1,0,0,0));v,_=g.solve(0,b)
        assert v<=21 and verify_policy(g,0,b,21)
        assert Recovery(cfg).solve(0,((2*(r-1),0),(2*r,0)))[0]==inf

def test_independent_small_policies():
    for gamma,n,rs in product((0,Q(1,4),Q(1)),(2,3),[(-6,6),(4,6)]):
        states=tuple((p,0) for p in rs);cfg=Geometry(horizon=n,footprint=3,visibility_uncertainty=.5,epsilon=.75)
        assert DriftRecovery(cfg,gamma).solve(0,initial(states,cfg))[0]==independent(states,n,gamma=gamma)[0]

def test_critical_rate_catalog_and_static_quotient_counterexample():
    cfg=Geometry(horizon=4,footprint=3,visibility_uncertainty=.5)
    rates=critical_rates(all_centers(cfg),Q(5,2),Q(7,2),4)
    assert Q(0) in rates and Q(1,2) in rates and Q(1) in rates
    assert Q(26,10)<3 and Q(29,10)<3
    assert Q(26,10)+Q(1,4)<3<=Q(29,10)+Q(1,4)
