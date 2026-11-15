from itertools import combinations,product
from dataclasses import replace
from math import inf,isfinite
from src.siv import Game,Config
from src.enhanced import Geometry,Recovery,branches,maximal_sets,check_policy,information_value
from enhanced_oracle import successors,feasible

def test_visibility_recovery_and_boundary_failure():
    b=((-8,0),(8,0),(10,0))
    for eta in (0,.25):
        g=Recovery(Geometry(footprint=4,visibility_uncertainty=eta))
        assert g.solve(0,b)[0]==19
        assert check_policy(g,0,b,19)
        assert feasible(b,5,19,R=4,eta=eta)
        assert not feasible(b,5,18,R=4,eta=eta)
    for R in (4,8,inf):
        assert Recovery(Geometry(footprint=R,visibility_uncertainty=.5)).solve(0,b)[0]==inf

def test_visibility_branches_independent():
    states=((-8,0),(-1,1),(0,0),(2,-1),(8,0))
    for size in (1,2,3):
      for b in combinations(states,size):
       for eps,R,eta,s in product((.25,.5),(inf,2,4),(0,.5),(0,1)):
        cfg=Geometry(epsilon=eps,footprint=R,visibility_uncertainty=eta)
        assert set(branches(b,s,cfg))==successors(b,s,eps,6,R,eta)

def test_pruned_values_against_boolean_oracle():
    for n,b,R,eta in product((2,3),[((-8,0),(8,0)),((-6,0),(0,0),(6,0)),((-4,1),(4,-1))],(inf,4),(0,.5)):
        c=Geometry(horizon=n,footprint=R,visibility_uncertainty=eta)
        g=Recovery(c);v,a=g.solve(0,b)
        assert (v,a)==Recovery(c,False).solve(0,b)
        if isfinite(v):
            assert feasible(b,n,int(v),R=R,eta=eta)
            assert not feasible(b,n,int(v)-1,R=R,eta=eta)
            assert check_policy(g,0,b,v)
        else:assert not feasible(b,n,6*n,R=R,eta=eta)

def test_original_model_equivalence():
    for n,d,l in product((2,3,5),(2,4,6),(-6,3,6)):
        b=((-2*d,0),(2*d,0))
        assert Recovery(Geometry(horizon=n,landmark=l)).solve(0,b)==Game(Config(horizon=n,landmark=l)).solve(0,b)

def test_permanent_pair_and_uncertain_visibility():
    for n,l,R in product((2,3,5,7),(-8,-3,0,3,8),(inf,4,8)):
        c=Geometry(horizon=n,landmark=l,footprint=R,visibility_uncertainty=.5)
        assert Recovery(c).solve(0,((4,0),(6,0)))[0]==inf

def test_threshold_geometry_and_touching():
    for p,q,l in product(range(-4,5),range(-4,5),range(-6,7)):
        lo,hi=sorted((p,q));expected=hi-lo if l<=lo or l>=hi else abs(2*l-lo-hi)
        assert abs(abs(p-l)-abs(q-l))==expected
    b=((-12,0),(12,0))
    assert all(len(c)==1 for c in branches(b,1,Geometry(epsilon=5.5)))
    assert b in branches(b,1,Geometry(epsilon=6))

def test_no_identification_needed_and_value_domains():
    b=((-6,0),(6,0));c=Geometry(horizon=2,mode='passive')
    assert Recovery(c).solve(0,b)[0]==6
    assert information_value(inf,inf)==('both_infeasible',None)
    assert information_value(inf,19)==('feasibility_gain',None)
    assert information_value(21,19)==('resource_saving',2)

def test_maximal_children_and_visibility_monotonicity():
    a=((0,0),);b=((0,0),(2,0));c=((8,0),)
    assert maximal_sets((a,b,c))==(b,c)
    for n in (3,5):
        vals=[Recovery(Geometry(horizon=n,footprint=4,visibility_uncertainty=e)).solve(0,((-8,0),(8,0),(10,0)))[0] for e in (0,.25,.5)]
        assert vals==sorted(vals)
