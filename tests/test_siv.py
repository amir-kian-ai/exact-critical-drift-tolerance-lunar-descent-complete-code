from dataclasses import replace
from math import isfinite
import pytest
from src.siv import *

def test_exact_discretization():
    assert step((4,-1),1)==(3,0)
    assert vertical(5,5)==(0,0)

def test_touching_observation_intervals_are_ambiguous():
    cfg=Config(epsilon=.5)
    b=((0,0),(2,0))
    cells=observation_cells(b,0,cfg)
    assert b in [x for x,y in cells]
    assert update(b,0,.5,cfg)==b
    with pytest.raises(ValueError):update(b,0,9,cfg)

def test_cells_match_dense_measurements():
    cfg=Config(epsilon=.5)
    b=((-4,0),(0,0),(2,1),(6,0))
    cells={x for x,y in observation_cells(b,1,cfg)}
    for i in range(-20,200):
        y=i/10
        try:assert update(b,1,y,cfg) in cells
        except ValueError:pass

def test_certified_policy_all_observations():
    cfg=Config(horizon=4)
    g=Game(cfg)
    for p in range(1,6):
        b=((-2*p,0),(2*p,0))
        req,_=g.solve(0,b)
        if isfinite(req):
            assert verify_policy(g,0,b,req)
            assert not verify_policy(g,0,b,req-1)

def test_information_and_cost_monotonicity():
    b=((-4,0),(4,0));cfg=Config(horizon=4)
    base=Game(cfg).solve(0,b)[0]
    assert Game(replace(cfg,epsilon=1.5)).solve(0,b)[0]>=base
    assert Game(replace(cfg,sensing_cost=4)).solve(0,b)[0]>=base
    assert Game(replace(cfg,mode='passive')).solve(0,b)[0]>=base
    assert Game(cfg).solve(0,(b[0],))[0]<=base

def test_safe_terminal_and_fuel_units():
    cfg=Config()
    assert terminal((6,0),cfg)
    assert not terminal((6,1),cfg)
    assert not tube_safe((24,1),0,cfg)
    assert cost(1,1,cfg)==6

def test_empty_belief_rejected():
    with pytest.raises(ValueError):Game(Config()).solve(0,())

def test_ambiguity_impossibility_even_with_future_perfect_sensor():
    cfg=Config(horizon=2,epsilon=0)
    b=((-8,0),(8,0))
    assert all(Game(cfg).solve(0,(x,))[0]==8 for x in b)
    assert not isfinite(Game(cfg).solve(0,b)[0])
    # Independently enumerate the two-action open-loop recovery sequences.
    sets=[]
    for x in b:
        sets.append({a for a in (-1,0,1) for c in (-1,0,1) if terminal(step(step(x,a),c),cfg)})
    assert sets==[{1},{-1}]

def test_sensing_deadline():
    b=((-12,0),(12,0))
    assert Game(Config()).solve(0,b)[0]==19
    assert not isfinite(Game(Config(delay=1)).solve(0,b)[0])
