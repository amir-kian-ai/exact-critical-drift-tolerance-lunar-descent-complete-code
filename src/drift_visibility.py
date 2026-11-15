"""Exact rational interval recovery with bounded per-observation threshold drift.

The threshold remains in the fixed prior at every time. Drift occurs before
each new observation; expansion of the initial full prior changes nothing.
States are k=0..N; action k=0..N-1 produces observation k+1.
The inherited terminal branch returns before actions at k=N.
"""
from fractions import Fraction as Q
from math import isfinite
from .static_visibility import StaticRecovery,project,propagate,nonempty

def initial(states,cfg):
    a=Q(cfg.footprint)-Q(cfg.visibility_uncertainty)
    b=Q(cfg.footprint)+Q(cfg.visibility_uncertainty)
    if a<=0:raise ValueError('Strictly positive prior required')
    return tuple((p,v,a,b,True) for p,v in sorted(set(states)))

def expand(records,cfg,gamma):
    a=Q(cfg.footprint)-Q(cfg.visibility_uncertainty)
    b=Q(cfg.footprint)+Q(cfg.visibility_uncertainty)
    result=[]
    for p,v,lo,hi,closed in records:
        upper=hi+gamma
        result.append((p,v,max(a,lo-gamma),min(b,upper),True if upper>b else closed))
    return tuple(result)

def update(pred,s,y,cfg):
    result=[]
    for p,v,lo,hi,closed in pred:
        center=abs(Q(p,2)-(Q(cfg.landmark) if s else 0))
        if y is None:
            if center<=hi:hi,closed=center,False
        else:
            if abs(y-center)>Q(cfg.epsilon):continue
            lo=max(lo,center)
        if nonempty(lo,hi,closed):result.append((p,v,lo,hi,closed))
    return tuple(sorted(result))

def successors(pred,s,cfg):
    ends=sorted({y for p,v,lo,hi,closed in pred
                 for center in [abs(Q(p,2)-(Q(cfg.landmark) if s else 0))]
                 if nonempty(max(lo,center),hi,closed)
                 for y in (center-Q(cfg.epsilon),center+Q(cfg.epsilon))})
    reps=ends+[(x+y)/2 for x,y in zip(ends,ends[1:])]+[None]
    return tuple(sorted({b for y in reps if (b:=update(pred,s,y,cfg))}))

class DriftRecovery(StaticRecovery):
    def __init__(self,cfg,gamma=0,schedule=None):
        if not isfinite(gamma) or gamma<0:raise ValueError('Finite nonnegative drift required')
        self.gamma=Q(gamma)
        super().__init__(cfg,schedule=schedule)
    def children(self,b,a,s):
        return successors(expand(propagate(b,a),self.cfg,self.gamma),s,self.cfg)

def critical_rates(centers,lower,upper,horizon):
    """Safe superset of every support-change rate, including saturation width.

    Local x,y are manuscript threshold values xi,zeta, not actions/velocity.
    d is the integer observation separation h; range(1,1) is empty for N=1."""
    vals={Q(lower),Q(upper)}|{Q(x) for x in centers if lower<=x<=upper}
    width=Q(upper)-Q(lower)
    return tuple(sorted({Q(0),width}|{(x-y)/d for x in vals for y in vals if x>y
                        for d in range(1,horizon) if (x-y)/d<=width}))

def all_centers(cfg):
    return {abs(Q(p,2)-l) for p in range(-24,25) for l in (Q(0),Q(cfg.landmark))}
