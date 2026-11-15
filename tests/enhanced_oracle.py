"""Independent Fraction Boolean search with eighth-metre measurement lattice.
No production transition, safety, observation or recursion helpers imported.
"""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from math import isfinite

def successors(rs,s,e,l,R,eta):
    centers={r:abs(Q(r[0],2)-(Q(l) if s else 0)) for r in rs}
    numeric={r:c for r,c in centers.items() if not isfinite(R) or c<=Q(R)+Q(eta)}
    missing=tuple(sorted(r for r,c in centers.items() if isfinite(R) and c>Q(R)-Q(eta)))
    result={missing} if missing else set()
    if numeric:
        lo=min(numeric.values())-Q(e);hi=max(numeric.values())+Q(e)
        assert all((4*v).denominator==1 for v in [lo,hi,*numeric.values()])
        for i in range(int(lo*8),int(hi*8)+1):
            child=tuple(sorted(r for r,c in numeric.items() if abs(c-Q(i,8))<=Q(e)))
            if child:result.add(child)
    return result

def feasible(rs,n,budget,e=.5,l=6,R=float('inf'),eta=0,sites=(-3,3),radius=.5,delay=0,schedule=None):
    @lru_cache(None)
    def go(k,states,b):
        if b<0:return False
        if k==n:return all(abs(x[1])<=Q(1,2) and min(abs(Q(x[0],2)-Q(t)) for t in sites)<=Q(radius) for x in states)
        for a,s in product((-1,0,1),(0,1)):
            if s and k<delay or schedule is not None and s!=schedule[k]:continue
            q=3+abs(a)+2*s
            if q>b:continue
            good=True
            for p2,v in states:
                ts=[Q(0),Q(1)]
                if a and 0<Q(-v,a)<1:ts.append(Q(-v,a))
                if max(abs(Q(p2,2)+v*t+Q(a,2)*t*t) for t in ts)>12 or max(abs(v),abs(v+a))>4:good=False
            if not good:continue
            ps=tuple(sorted({(p+2*v+a,v+a) for p,v in states}))
            if all(go(k+1,c,b-q) for c in successors(ps,s,e,l,R,eta)):return True
        return False
    return go(0,tuple(sorted(set(rs))),budget)
