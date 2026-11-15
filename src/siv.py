"""Exact finite-hypothesis terminal-descent game (SI units).

Position is stored as twice its value to avoid grid rounding. No continuous
state enclosure is claimed. Bounded observation errors are handled exactly
by enumerating interval-arrangement cells, including their endpoints.
"""
from dataclasses import dataclass
from functools import lru_cache
from math import inf, isfinite

State = tuple[int, int]  # (twice horizontal position [m], velocity [m/s])
Belief = tuple[State, ...]

def canonical(states):
    return tuple(sorted(set(states)))

@dataclass(frozen=True)
class Config:
    horizon: int = 5
    epsilon: float = 0.5  # total bounded range error [m]
    sensing_cost: int = 2  # synthetic allocated resource [m/s-equivalent]
    delay: int = 0  # first permitted active acquisition index
    landmark: float = 6.0  # active horizontal landmark coordinate [m]
    target: float = 3.0  # sites at +/- target [m]
    radius: float = 0.5
    xmax: float = 12.0
    vmax: float = 4.0
    amax: int = 1
    mode: str = 'siv'  # siv, passive, blind

    def __post_init__(self):
        if type(self.horizon) is not int or self.horizon < 1:
            raise ValueError('Positive integer horizon required')
        if type(self.delay) is not int or self.delay < 0 or self.amax != 1:
            raise ValueError('Nonnegative integer acquisition index and amax=1 required')
        if self.mode not in ('siv','passive','blind'):
            raise ValueError('Unknown observation mode')
        for key in ('epsilon','sensing_cost','radius','xmax','vmax','target'):
            value=getattr(self,key)
            if not isfinite(value) or value < 0: raise ValueError(f'Invalid {key}')
        if not isfinite(self.landmark): raise ValueError('Invalid landmark')

def step(x, a):
    p2, v = x
    return (p2 + 2*v + a, v+a)

def tube_safe(x, a, cfg):
    pslack,vslack=tube_slacks(x,a,cfg)
    return pslack>=0 and vslack>=0

def tube_slacks(x, a, cfg):
    p, v = x[0]/2, x[1]
    times = [0., 1.]
    if a and 0 < -v/a < 1:
        times.append(-v/a)
    return (cfg.xmax-max(abs(p+v*t+0.5*a*t*t) for t in times),
            cfg.vmax-max(abs(v),abs(v+a)))

def terminal(x, cfg):
    return abs(abs(x[0]/2)-cfg.target) <= cfg.radius and abs(x[1]) <= 0.5

def cost(a, sense, cfg):
    # 3+|a| bounds sqrt((g_moon+0.5)^2+a^2) at g_moon=1.62.
    return 3+abs(a)+cfg.sensing_cost*sense

def interval(x, sense, cfg):
    center=abs(x[0]/2-(cfg.landmark if sense else 0.))
    return center-cfg.epsilon, center+cfg.epsilon

def update(predicted, sense, y, cfg):
    b=canonical(x for x in predicted if interval(x,sense,cfg)[0] <= y <= interval(x,sense,cfg)[1])
    if not b:
        raise ValueError('Observation inconsistent with the bounded-error model; certificate invalid')
    return b

def observation_cells(predicted, sense, cfg):
    endpoints=sorted(set(t for x in predicted for t in interval(x,sense,cfg)))
    ys=endpoints+[(l+r)/2 for l,r in zip(endpoints,endpoints[1:])]
    cells={}
    for y in ys:
        b=canonical(x for x in predicted if interval(x,sense,cfg)[0] <= y <= interval(x,sense,cfg)[1])
        if b: cells.setdefault(b,y)
    return tuple(sorted(cells.items()))

class Game:
    def __init__(self,cfg):
        self._cfg=cfg
        self.nodes=0
        self.edges=0
        self._cached=lru_cache(maxsize=None)(self._solve)
    def solve(self,k,b):
        return self._cached(k,canonical(b))
    @property
    def cfg(self):
        return self._cfg
    def actions(self,k):
        senses=(0,1) if self.cfg.mode=='siv' and k>=self.cfg.delay else (0,)
        return tuple((a,s) for s in senses for a in range(-self.cfg.amax,self.cfg.amax+1))
    def successors(self,b,a,s):
        p=canonical(step(x,a) for x in b)
        if self.cfg.mode=='blind': return (p,)
        return tuple(c for c,y in observation_cells(p,s,self.cfg))
    def _solve(self,k,b):
        self.nodes+=1
        if not b: raise ValueError('Empty belief is not a physical information state')
        if type(k) is not int or not 0<=k<=self.cfg.horizon:
            raise ValueError('Time index outside horizon')
        if any(len(x)!=2 or any(type(v) is not int for v in x) for x in b):
            raise ValueError('States require integer twice-position and integer velocity')
        if k==self.cfg.horizon:
            return (0.,None) if all(terminal(x,self.cfg) for x in b) else (inf,None)
        best=(inf,None)
        for a,s in self.actions(k):
            if not all(tube_safe(x,a,self.cfg) for x in b): continue
            children=self.successors(b,a,s)
            self.edges+=len(children)
            future=max(self._cached(k+1,c)[0] for c in children)
            val=cost(a,s,self.cfg)+future
            if val<best[0]: best=(val,(a,s))
        return best
    def clear(self):
        self._cached.cache_clear();self.nodes=0;self.edges=0

def physical_requirement(cfg,b):
    # Full state information after each action is unnecessary when dynamics
    # are deterministic: each singleton remains a singleton.
    g=Game(cfg)
    return max(g.solve(0,(x,))[0] for x in b)

def verify_policy(game,k,b,budget):
    """All-cell consistency traversal; shares model helpers with synthesis."""
    if k==game.cfg.horizon:
        return all(terminal(x,game.cfg) for x in b) and budget>=0
    _,act=game.solve(k,b)
    if act is None:return False
    a,s=act
    if budget<cost(a,s,game.cfg) or not all(tube_safe(x,a,game.cfg) for x in b):return False
    predicted=canonical(step(x,a) for x in b)
    return all(verify_policy(game,k+1,c,budget-cost(a,s,game.cfg))
               for c,y in observation_cells(predicted,s,game.cfg))

def vertical(k,horizon):
    """Prescribed descent: z=.25*(N-k)^2 m, vz=-.5*(N-k) m/s."""
    return .25*(horizon-k)**2,-.5*(horizon-k)
