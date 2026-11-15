from itertools import combinations,product
from fractions import Fraction as Q
from math import isfinite
from src.siv import Game,Config,step,observation_cells,cost
from review_oracle import advance,safe,goal,feasible

def test_public_cache_canonicalization():
    g=Game(Config());b=((-8,0),(8,0))
    expected=g.solve(0,b);nodes=g.nodes
    assert g.solve(0,tuple(reversed(b))+b)==expected and g.nodes==nodes
    g.clear();assert g.nodes==0

def test_prefix_obstruction_all_lengths():
    # Independent sequence enumeration, including h=1 and h=N.
    actions=tuple(product((-1,0,1),(0,1)));premises=0
    for n,eps,states in product((2,3),(0,Q(1,2),8),combinations(((-8,0),(-6,0),(6,0),(8,0)),2)):
        sequences=[]
        for r in states:
            wins=[]
            for seq in product(actions,repeat=n):
                x=r;ok=True
                for a,s in seq:ok=ok and safe(x,a);x=advance(x,a)
                if ok and goal(x):wins.append(seq)
            sequences.append(wins)
        for h in range(1,n+1):
            shared=True
            for j in range(1,h):
                for seq in product(actions,repeat=j):
                    xs=list(states);ok=True
                    for a,s in seq:
                        ok=ok and all(safe(x,a) for x in xs);xs=[advance(x,a) for x in xs]
                    if not ok:continue
                    centers=[abs(Q(x[0],2)-(6 if seq[-1][1] else 0)) for x in xs]
                    if max(c-eps for c in centers)>min(c+eps for c in centers):shared=False
            prefixes=[{seq[:h] for seq in wins} for wins in sequences]
            if shared and not set.intersection(*prefixes):
                premises+=1
                assert not feasible(states,n,6*n,epsilon=eps)
    assert premises>0

def test_all_lattice_transitions_match_rational_equations():
    for p2,v,a in product(range(-24,25),range(-4,5),(-1,0,1)):
        out=step((p2,v),a)
        assert Q(out[0],2)==Q(p2,2)+v+Q(a,2)
        assert out[1]==v+a

def test_sensing_error_threshold_and_charges():
    b=((-12,0),(12,0))
    # First action for d=6 is coast and acquire: centers12 and0 differ by12m.
    for eps in (0,.5,2,4):
        val,act=Game(Config(epsilon=eps)).solve(0,b)
        assert act==(0,1) and val==19
        assert all(len(c)==1 for c,y in observation_cells(b,1,Config(epsilon=eps)))
    assert b in {c for c,y in observation_cells(b,1,Config(epsilon=6))}
    vals=[Game(Config(epsilon=e)).solve(0,b)[0] for e in (4,5.5,6,6.5)]
    assert vals==sorted(vals)
    charges=[Game(Config(sensing_cost=c)).solve(0,b)[0] for c in (0,1,2,4,8)]
    assert charges==[17,18,19,21,25]
