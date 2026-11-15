"""Independent exact expanded-state solver using rational threshold cells.

No production imports. All safe lattice positions define comparison thresholds;
endpoints and open-cell representatives cover a continuous calibration interval.
"""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from math import inf

def parameters(R,eta,l):
    lo,hi=Q(R)-Q(eta),Q(R)+Q(eta)
    cuts=sorted({lo,hi}|{abs(Q(p,2)-ell) for p in range(-24,25) for ell in (Q(0),Q(l)) if lo<=abs(Q(p,2)-ell)<=hi})
    return tuple(sorted(set(cuts+[(x+y)/2 for x,y in zip(cuts,cuts[1:])])))
def branches(states,s,e,l):
    visible=[(r,abs(Q(r[0],2)-(Q(l) if s else 0))) for r in states if abs(Q(r[0],2)-(Q(l) if s else 0))<=r[2]]
    missing=tuple(sorted(r for r in states if abs(Q(r[0],2)-(Q(l) if s else 0))>r[2]))
    result={missing} if missing else set()
    if visible:
        lo=min(c for r,c in visible)-Q(e);hi=max(c for r,c in visible)+Q(e)
        # Independent uniform lattice, exact for eighth-metre endpoints and their gaps.
        assert (lo*16).denominator==1 and (hi*16).denominator==1
        for i in range(int(lo*16),int(hi*16)+1):
            child=tuple(sorted(r for r,c in visible if abs(c-Q(i,16))<=Q(e)))
            if child:result.add(child)
    return result
def solve(rs,n,e=.5,l=6,R=4,eta=.5,sites=(-3,3),radius=.5,schedule=None,cs=2,passive=False):
    states=tuple(sorted((p,v,t) for p,v in rs for t in parameters(R,eta,l)))
    @lru_cache(None)
    def go(k,states):
        if k==n:return 0 if all(abs(v)<=Q(1,2) and min(abs(Q(p,2)-Q(t)) for t in sites)<=Q(radius) for p,v,theta in states) else inf
        best=inf
        for a,s in product((-1,0,1),(0,) if passive else (0,1)):
            if schedule is not None and s!=schedule[k]:continue
            good=True
            for p,v,theta in states:
                ts=[Q(0),Q(1)]
                if a and 0<Q(-v,a)<1:ts.append(Q(-v,a))
                if max(abs(Q(p,2)+v*t+Q(a,2)*t*t) for t in ts)>12 or max(abs(v),abs(v+a))>4:good=False;break
            if not good:continue
            pred=tuple(sorted({(p+2*v+a,v+a,theta) for p,v,theta in states}))
            value=3+abs(a)+cs*s+max(go(k+1,b) for b in branches(pred,s,e,l))
            best=min(best,value)
        return best
    value=go(0,states)
    return value,go.cache_info().currsize
