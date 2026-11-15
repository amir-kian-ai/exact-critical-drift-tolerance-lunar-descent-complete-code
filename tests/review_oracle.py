"""Independent rational oracle: no production dynamics/branch/safety helpers.

For half-metre positions and quarter-metre error bounds, every observation
endpoint is on the quarter-metre lattice. Enumerating eighth-metres therefore
hits every endpoint and every nonempty open cell. This deliberately inefficient
method is used only for small verification instances.
"""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product

def advance(r,a): return (r[0]+2*r[1]+a,r[1]+a)

def safe(r,a):
    p,v=Q(r[0],2),Q(r[1]);ts=[Q(0),Q(1)]
    if a and 0 < -v/a < 1: ts.append(-v/a)
    return all(abs(p+v*t+Q(a,2)*t*t)<=12 for t in ts) and max(abs(v),abs(v+a))<=4

def goal(r): return abs(abs(Q(r[0],2))-3)<=Q(1,2) and abs(r[1])<=Q(1,2)

def branches(states,s,epsilon,landmark=6):
    e=Q(epsilon)
    assert (4*e).denominator==1
    centers={r:abs(Q(r[0],2)-(Q(landmark) if s else 0)) for r in states}
    lo=min(centers.values())-e;hi=max(centers.values())+e
    return {tuple(sorted(r for r,c in centers.items() if abs(Q(i,8)-c)<=e))
            for i in range(int(lo*8),int(hi*8)+1)}-{()}

def feasible(states,n,budget,epsilon=Q(1,2),delay=0,mode='siv',landmark=6):
    @lru_cache(None)
    def visit(k,rs,b):
        if b<0:return False
        if k==n:return all(goal(r) for r in rs)
        for a,s in product((-1,0,1),(0,1)):
            if s and (k<delay or mode!='siv'):continue
            charge=3+abs(a)+2*s
            if charge>b or not all(safe(r,a) for r in rs):continue
            ps=tuple(sorted({advance(r,a) for r in rs}))
            children={ps} if mode=='blind' else branches(ps,s,epsilon,landmark)
            if all(visit(k+1,c,b-charge) for c in children):return True
        return False
    return visit(0,tuple(sorted(set(states))),budget)

def recovery_sequences(r,n):
    result=[]
    for actions in product((-1,0,1),repeat=n):
        x=r;ok=True
        for a in actions:ok=ok and safe(x,a);x=advance(x,a)
        if ok and goal(x):result.append(actions)
    return result
