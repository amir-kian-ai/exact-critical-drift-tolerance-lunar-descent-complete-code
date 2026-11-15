from dataclasses import replace
from math import inf
from .siv import Game,canonical,step,tube_safe,cost,observation_cells

class Controller:
    """Baselines are reduced-model comparators, not published reproductions."""
    def __init__(self,name,cfg):
        self.name=name; self.cfg=cfg
        mode={'robust_mpc':'blind','passive':'passive'}.get(name,'siv')
        self.game=Game(replace(cfg,mode=mode,sensing_cost=0 if name=='free_sensing' else cfg.sensing_cost))
        self.nominal=Game(replace(cfg,mode='blind'))
    def choose(self,k,b):
        if self.name in ('siv','robust_mpc','passive','free_sensing'):
            req,act=self.game.solve(k,b)
            if act is not None:return act
        if self.name=='information_greedy':
            options=[]
            for a,s in self.game.actions(k):
                if not all(tube_safe(x,a,self.cfg) for x in b):continue
                p=canonical(step(x,a) for x in b)
                ambiguity=max(len(c) for c,y in observation_cells(p,s,self.cfg))
                # Full-information cost breaks information ties, then fuel.
                rem=max(self.nominal.solve(k+1,(x,))[0] for x in p)
                options.append(((ambiguity,rem+cost(a,s,self.cfg),abs(a),s,a),(a,s)))
            if options:return min(options)[1]
        # Nominal MPC / explicit uncertified fallback selects one surviving
        # hypothesis (lexicographic), never silently declares a certificate.
        act=self.nominal.solve(k,(b[0],))[1]
        return act if act is not None else (0,0)
