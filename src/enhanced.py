"""Visibility-conditioned finite game; original src.siv remains unchanged.

None is a non-detection symbol. Sensor footprint uncertainty is adversarial,
rectangular in time, and distinct from the bounded numeric feature error.
"""
from dataclasses import dataclass
from functools import lru_cache
from math import inf,isfinite
from .siv import Config,canonical,step,tube_safe

@dataclass(frozen=True)
class Geometry(Config):
    sites: tuple = (-3.,3.)
    footprint: float = inf
    visibility_uncertainty: float = 0.
    def __post_init__(self):
        super().__post_init__()
        if not self.sites or any(not isfinite(t) for t in self.sites):raise ValueError('Finite sites required')
        if self.footprint<=0 or self.footprint!=self.footprint:raise ValueError('Positive footprint required')
        if not isfinite(self.visibility_uncertainty) or self.visibility_uncertainty<0:raise ValueError('Invalid visibility uncertainty')

def goal(x,cfg):return min(abs(x[0]/2-t) for t in cfg.sites)<=cfg.radius and abs(x[1])<=.5

def outputs(x,s,cfg):
    center=abs(x[0]/2-(cfg.landmark if s else 0))
    numeric=center<=cfg.footprint+cfg.visibility_uncertainty
    dropout=center>cfg.footprint-cfg.visibility_uncertainty
    return (center-cfg.epsilon,center+cfg.epsilon) if numeric else None,dropout

def branches(pred,s,cfg):
    records=[(x,*outputs(x,s,cfg)) for x in pred]
    endpoints=sorted({y for x,iv,d in records if iv is not None for y in iv})
    result=set()
    for y in endpoints+[(a+b)/2 for a,b in zip(endpoints,endpoints[1:])]:
        b=canonical(x for x,iv,d in records if iv is not None and iv[0]<=y<=iv[1])
        if b:result.add(b)
    missing=canonical(x for x,iv,d in records if d)
    if missing:result.add(missing)
    return tuple(sorted(result))

def observed_update(pred,s,y,cfg):
    return canonical(x for x in pred if (outputs(x,s,cfg)[1] if y is None else outputs(x,s,cfg)[0] is not None and outputs(x,s,cfg)[0][0]<=y<=outputs(x,s,cfg)[0][1]))

def maximal_sets(children):
    sets=[set(c) for c in children]
    return tuple(c for i,c in enumerate(children) if not any(sets[i]<s for s in sets))

class Recovery:
    def __init__(self,cfg,prune=True,schedule=None):
        self.cfg=cfg;self.prune=prune;self.schedule=schedule
        self.nodes=0;self.edges=0;self.raw_edges=0
        self._visit=lru_cache(None)(self._solve)
    def solve(self,k,b):return self._visit(k,canonical(b))
    def actions(self,k):
        senses=(0,1) if self.cfg.mode=='siv' and k>=self.cfg.delay else (0,)
        if self.schedule is not None:senses=tuple(s for s in senses if s==self.schedule[k])
        return tuple((a,s) for s in senses for a in (-1,0,1))
    def _solve(self,k,b):
        self.nodes+=1
        if not b or type(k) is not int or not 0<=k<=self.cfg.horizon:raise ValueError('Invalid time/information set')
        if any(len(x)!=2 or any(type(v) is not int for v in x) for x in b):raise ValueError('Integer encoded states required')
        if k==self.cfg.horizon:return (0.,None) if all(goal(x,self.cfg) for x in b) else (inf,None)
        best=(inf,None)
        for a,s in self.actions(k):
            if not all(tube_safe(x,a,self.cfg) for x in b):continue
            pred=canonical(step(x,a) for x in b)
            children=(pred,) if self.cfg.mode=='blind' else branches(pred,s,self.cfg)
            self.raw_edges+=len(children)
            if self.prune:children=maximal_sets(children)
            self.edges+=len(children)
            val=3+abs(a)+self.cfg.sensing_cost*s+max(self._visit(k+1,c)[0] for c in children)
            if val<best[0]:best=val,(a,s)
        return best

def check_policy(game,k,b,budget):
    """Traverse ALL successors, including subsets omitted during synthesis."""
    if k==game.cfg.horizon:return budget>=0 and all(goal(x,game.cfg) for x in b)
    value,act=game.solve(k,b)
    if act is None:return False
    a,s=act;q=3+abs(a)+game.cfg.sensing_cost*s
    if q>budget or not all(tube_safe(x,a,game.cfg) for x in b):return False
    pred=canonical(step(x,a) for x in b)
    children=(pred,) if game.cfg.mode=='blind' else branches(pred,s,game.cfg)
    return all(check_policy(game,k+1,c,budget-q) for c in children)

def information_value(passive,adaptive):
    if not isfinite(adaptive):return 'both_infeasible',None
    if not isfinite(passive):return 'feasibility_gain',None
    return ('resource_saving' if passive>adaptive else 'no_gain'),passive-adaptive
