"""Independent rational full-history solver; no production imports.

Feasibility uses all pairwise Lipschitz box inequalities, not interval updates.
"""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from math import inf

def boxes(history,lower,upper):
    return tuple((max(lower,c),upper,True) if detect else (lower,min(upper,c),c>upper)
                 for c,detect in history)

def feasible(history,lower,upper,gamma):
    bb=boxes(history,Q(lower),Q(upper));gamma=Q(gamma)
    return all(lo<=hi+gamma*abs(i-j) if closed else lo<hi+gamma*abs(i-j)
               for i,(lo,_,_) in enumerate(bb) for j,(_,hi,closed) in enumerate(bb))

def solve(rs,n,e=.75,l=6,lower=2.5,upper=3.5,gamma=0,sites=(-3,3),radius=.5,cs=2,schedule=None,endpoint_partition=False):
    lower,upper,e,gamma=map(Q,(lower,upper,e,gamma))
    @lru_cache(None)
    def go(k,records):
        if k==n:return Q(0) if all(abs(v)<=Q(1,2) and min(abs(Q(p,2)-Q(t)) for t in sites)<=Q(radius) for p,v,h in records) else inf
        best=inf
        for s,a in product((0,1),(-1,0,1)):
            if schedule is not None and s!=schedule[k]:continue
            safe=True
            for p,v,h in records:
                ts=[Q(0),Q(1)]
                if a and 0<Q(-v,a)<1:ts.append(Q(-v,a))
                if max(abs(Q(p,2)+v*t+Q(a,2)*t*t) for t in ts)>12 or max(abs(v),abs(v+a))>4:safe=False;break
            if not safe:continue
            pred=tuple((p+2*v+a,v+a,h) for p,v,h in records)
            centers={abs(Q(p,2)-(Q(l) if s else 0)) for p,v,h in pred}
            # Independent uniform observation lattice for the declared dyadic cases.
            lo=min(centers)-e;hi=max(centers)+e
            assert all(((z+sign*e)*8).denominator==1 for z in centers for sign in (-1,1))
            children=set()
            observations=[Q(j,16) for j in range(int(lo*16),int(hi*16)+1)]
            if endpoint_partition:
                ends=sorted({c+sign*e for c in centers for sign in (-1,1)})
                observations=ends+[(x+y)/2 for x,y in zip(ends,ends[1:])]
            for y in [None]+observations:
                child=[]
                for p,v,h in pred:
                    center=abs(Q(p,2)-(Q(l) if s else 0));hh=h+((center,y is not None),)
                    if (y is None or abs(y-center)<=e) and feasible(hh,lower,upper,gamma):child.append((p,v,hh))
                if child:children.add(tuple(child))
            value=3+abs(a)+Q(cs)*s+max(go(k+1,b) for b in children)
            best=min(best,value)
        return best
    value=go(0,tuple((p,v,()) for p,v in sorted(set(rs))))
    return value,go.cache_info().currsize
