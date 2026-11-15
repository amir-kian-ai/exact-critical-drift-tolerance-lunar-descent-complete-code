"""Exact joint state/constant-threshold information sets.

Each record is (twice_position, velocity, lower, upper, upper_closed).
The lower endpoint is always closed. A detection implies theta >= center;
non-detection implies theta < center. No parameter discretization is used.
"""
from functools import lru_cache
from math import inf,isfinite
from .siv import step,tube_safe,canonical
from .enhanced import goal

def nonempty(lo,hi,closed):return lo<hi or lo==hi and closed
def initial(states,cfg):
    if not isfinite(cfg.footprint) or cfg.footprint-cfg.visibility_uncertainty<=0:
        raise ValueError('Static threshold interval must be finite and strictly positive')
    return tuple((p,v,cfg.footprint-cfg.visibility_uncertainty,cfg.footprint+cfg.visibility_uncertainty,True) for p,v in canonical(states))
def project(b):return canonical((p,v) for p,v,lo,hi,cl in b)
def propagate(b,a):return tuple((*step((p,v),a),lo,hi,cl) for p,v,lo,hi,cl in b)
def update(pred,s,y,cfg):
    result=[]
    for p,v,lo,hi,closed in pred:
        c=abs(p/2-(cfg.landmark if s else 0))
        if y is None:
            if c<=hi:hi,closed=c,False
        else:
            if not c-cfg.epsilon<=y<=c+cfg.epsilon:continue
            lo=max(lo,c)
        if nonempty(lo,hi,closed):result.append((p,v,lo,hi,closed))
    return tuple(sorted(set(result)))
def successors(pred,s,cfg,labels=False):
    endpoints=sorted({z for p,v,lo,hi,closed in pred for c in [abs(p/2-(cfg.landmark if s else 0))] if nonempty(max(lo,c),hi,closed) for z in (c-cfg.epsilon,c+cfg.epsilon)})
    reps=endpoints+[(a+b)/2 for a,b in zip(endpoints,endpoints[1:])]+[None]
    children={}
    for y in reps:
        b=update(pred,s,y,cfg)
        if b and b not in children:children[b]=y
    return tuple((b,y) for b,y in children.items()) if labels else tuple(children)

class StaticRecovery:
    def __init__(self,cfg,schedule=None,reset=False):
        self.cfg=cfg;self.schedule=schedule;self.reset=reset
        self.nodes=0;self.edges=0;self._visit=lru_cache(None)(self._solve)
    def solve(self,k,b):return self._visit(k,tuple(sorted(set(b))))
    def actions(self,k):
        senses=(0,1) if self.cfg.mode=='siv' and k>=self.cfg.delay else (0,)
        if self.schedule is not None:senses=tuple(s for s in senses if s==self.schedule[k])
        return tuple((a,s) for s in senses for a in (-1,0,1))
    def children(self,b,a,s):
        if self.reset:b=initial(project(b),self.cfg)
        pred=propagate(b,a)
        return successors(pred,s,self.cfg)
    def _solve(self,k,b):
        self.nodes+=1
        if not b or not 0<=k<=self.cfg.horizon:raise ValueError('Invalid information state/time')
        if k==self.cfg.horizon:return (0.,None) if all(goal(x,self.cfg) for x in project(b)) else (inf,None)
        best=(inf,None)
        for a,s in self.actions(k):
            if not all(tube_safe(x,a,self.cfg) for x in project(b)):continue
            children=self.children(b,a,s);self.edges+=len(children)
            value=3+abs(a)+self.cfg.sensing_cost*s+max(self.solve(k+1,c)[0] for c in children)
            if value<best[0]:best=value,(a,s)
        return best

def verify_policy(engine,k,b,budget):
    if k==engine.cfg.horizon:return budget>=0 and all(goal(x,engine.cfg) for x in project(b))
    value,act=engine.solve(k,b)
    if act is None:return False
    a,s=act;q=3+abs(a)+engine.cfg.sensing_cost*s
    return q<=budget and all(tube_safe(x,a,engine.cfg) for x in project(b)) and all(verify_policy(engine,k+1,c,budget-q) for c in engine.children(b,a,s))
