from itertools import combinations,product
from math import sqrt,atan,degrees,isfinite
from fractions import Fraction
import pytest
from src.siv import Config,Game,observation_cells,canonical,tube_slacks
from review_oracle import branches,feasible,recovery_sequences

def test_independent_exact_branch_oracle():
    universe=((-6,0),(-1,1),(0,0),(2,-1),(7,0))
    for size in range(1,6):
        for states in combinations(universe,size):
            for s,e in product((0,1),(0,.25,.5,1,2)):
                actual={b for b,y in observation_cells(states,s,Config(epsilon=e))}
                assert actual==branches(states,s,Fraction(e))

def test_independent_budget_tree_oracle():
    # 3 horizons x 5 separations x 3 information modes x 8 budgets.
    for n,d,mode in product((1,2,3),(1,2,3,4,5),('siv','passive','blind')):
        states=((-2*d,0),(2*d,0));value=Game(Config(horizon=n,mode=mode)).solve(0,states)[0]
        for budget in range(3*n,3*n+8):
            assert (value<=budget)==feasible(states,n,budget,mode=mode)

def test_independent_two_step_witness():
    assert recovery_sequences((-8,0),2)==[(1,-1)]
    assert recovery_sequences((8,0),2)==[(-1,1)]
    assert not feasible(((-8,0),(8,0)),2,12,epsilon=0)

def test_independent_five_step_deadline():
    b=((-12,0),(12,0))
    assert not feasible(b,5,18)
    assert feasible(b,5,19)
    # 30 is the largest possible charge for any five-step action sequence.
    assert not feasible(b,5,30,delay=1)

def test_correlated_history_countermodel():
    # Outside the rectangular model: marginal intersections alone are insufficient.
    histories={'left':{(0,0),(1,1)},'right':{(0,1),(1,0)}}
    for j in (0,1):
        assert {h[j] for h in histories['left']} & {h[j] for h in histories['right']}
    assert not histories['left'] & histories['right']
    # Dummy first two actions, then disjoint left/right recovery actions.
    for truth,allowed in histories.items():
        for h in allowed:
            inferred='left' if h[0]==h[1] else 'right'
            assert inferred==truth

def test_physical_and_reservation_bounds():
    thrust=max(sqrt(2.12**2+a*a) for a in (-1,0,1))
    assert thrust<2.35 and degrees(atan(1/2.12))<26
    assert all(3+abs(a)>=sqrt(2.12**2+a*a) for a in (-1,0,1))
    assert 3>thrust  # Added |a| is a synthetic effort penalty, not needed for bound.

def test_complete_hold_slack_includes_initial_state_and_extremum():
    assert tube_slacks((20,-1),0,Config())[0]==2
    # Direct helper supports testing an interior extremum even outside solver lattice.
    assert tube_slacks((20,.5),-1,Config())[0]==pytest.approx(1.875)

@pytest.mark.parametrize('kw',[{'sensing_cost':-1},{'epsilon':-1},{'horizon':0},{'horizon':2.5},{'amax':2},{'mode':'unknown'}])
def test_invalid_configuration_rejected(kw):
    with pytest.raises(ValueError):Config(**kw)

def test_invalid_encoded_state_rejected():
    with pytest.raises(ValueError):Game(Config()).solve(0,((1.5,0),))

def test_game_configuration_cannot_be_reassigned():
    g=Game(Config())
    with pytest.raises(AttributeError):g.cfg=Config(sensing_cost=0)

def test_duplicate_hypotheses_merge():
    cfg=Config();b=((-4,0),(4,0))
    assert canonical(b+b)==b
    assert Game(cfg).solve(0,b+b)[0]==Game(cfg).solve(0,b)[0]

def test_cost_restriction_and_blind_coarsening_small_grid():
    for n,d in product((2,3,4),(1,2,3,4)):
        b=((-2*d,0),(2*d,0))
        base=Game(Config(horizon=n)).solve(0,b)[0]
        assert base<=Game(Config(horizon=n,sensing_cost=4)).solve(0,b)[0]
        assert base<=Game(Config(horizon=n,mode='passive')).solve(0,b)[0]
        assert base<=Game(Config(horizon=n,mode='blind')).solve(0,b)[0]
