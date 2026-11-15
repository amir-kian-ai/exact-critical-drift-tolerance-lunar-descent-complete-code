from itertools import product
from dataclasses import replace
from math import inf,isfinite
from src.enhanced import Geometry,Recovery
from src.static_visibility import initial,update,propagate,project,StaticRecovery,verify_policy
from static_oracle import solve as oracle

def test_open_boundary_and_history_consistency():
    c=Geometry(footprint=4,visibility_uncertainty=.5)
    b=initial(((8,0),),c)
    seen=update(b,0,4,c);assert seen==((8,0,4,4.5,True),)
    assert update(seen,0,None,c)==()
    missing=update(b,0,None,c);assert missing==((8,0,3.5,4.,False),)
    assert update(missing,0,4,c)==()
    exact=initial(((8,0),),replace(c,visibility_uncertainty=0))
    assert update(exact,0,None,c)==()

def test_static_reset_and_known_boundary():
    for n,rs,R,e in product((2,3),[((-6,0),(6,0)),((4,0),(6,0)),((-4,1),(2,-1),(6,0))],(3,4),(0,.75)):
        cfg=Geometry(horizon=n,footprint=R,epsilon=e)
        assert StaticRecovery(cfg).solve(0,initial(rs,cfg))[0]==Recovery(cfg).solve(0,rs)[0]
        cfg=replace(cfg,visibility_uncertainty=.5)
        assert StaticRecovery(cfg,reset=True).solve(0,initial(rs,cfg))[0]==Recovery(cfg).solve(0,rs)[0]
        assert StaticRecovery(cfg).solve(0,initial(rs,cfg))[0]<=Recovery(cfg).solve(0,rs)[0]

def test_independent_expanded_parameter_optima():
    for n,rs,e in product((2,3),[((-6,0),(6,0)),((4,0),(6,0)),((-4,1),(2,-1))],(.5,.75)):
        cfg=Geometry(horizon=n,footprint=4,visibility_uncertainty=.5,epsilon=e)
        g=StaticRecovery(cfg);v,_=g.solve(0,initial(rs,cfg))
        assert v==oracle(rs,n,e=e)[0]
        if isfinite(v):assert verify_policy(g,0,initial(rs,cfg),v)

def test_legacy_triple_is_not_automatically_repaired():
    cfg=Geometry(footprint=4,visibility_uncertainty=.5)
    assert StaticRecovery(cfg).solve(0,initial(((-8,0),(8,0),(10,0)),cfg))[0]==inf

def test_positive_width_certified_recovery_witness():
    rs=((4,0),(6,0));cfg=Geometry(footprint=3,visibility_uncertainty=.5,epsilon=.75)
    g=StaticRecovery(cfg);b=initial(rs,cfg)
    assert g.solve(0,b)[0]==19 and verify_policy(g,0,b,19)
    assert oracle(rs,5,e=.75,R=3,eta=.5)[0]==19
    assert Recovery(cfg).solve(0,rs)[0]==inf
    assert StaticRecovery(cfg,reset=True).solve(0,b)[0]==inf
    assert StaticRecovery(cfg,schedule=(0,0,1,0,0)).solve(0,b)[0]==19
    assert StaticRecovery(cfg).solve(0,tuple(reversed(b))+b[:1])[0]==19

def test_signature_family_and_four_step_policy():
    for m,eta in product((2,3,4),(.5,.75)):
        cfg=Geometry(horizon=4,landmark=2*m,sites=(-m,m),footprint=m,visibility_uncertainty=eta,epsilon=.875)
        rs=((2*(m-1),0),(2*m,0));b=initial(rs,cfg)
        g=StaticRecovery(cfg,schedule=(0,1,0,0))
        assert g.solve(0,b)[0]==16 and verify_policy(g,0,b,16)
        for theta in (m-eta,m,m+eta):
            assert ((m-1)<=theta,(m+1)<=theta)==(True,False)
            assert (m<=theta)==(abs(m-2*m)<=theta)
