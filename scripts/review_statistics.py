"""Paired diagnostics and trace-level checks; fixed designed scenario panel."""
from pathlib import Path
import csv,json
import numpy as np
root=Path(__file__).resolve().parents[1]
with (root/'results/data/rollouts.csv').open() as f: rows=list(csv.DictReader(f))
def key(r):return (r['half_separation_m'],r['budget_mps'],r['seed'])
by={n:{key(r):r for r in rows if r['controller']==n} for n in {r['controller'] for r in rows}}
assert all(set(v)==set(by['siv']) for v in by.values())
nom,rob=by['nominal_mpc'],by['robust_mpc']
stats={'matched_trials':len(nom),'nominal_robust_action_trace_differences':sum(nom[k]['action_trace']!=rob[k]['action_trace'] for k in nom),
       'nominal_robust_success_differences':sum(nom[k]['success']!=rob[k]['success'] for k in nom),
       'pairs':{}}
for name in sorted(by):
    if name=='siv':continue
    pairs=[(int(by['siv'][k]['success']),int(by[name][k]['success'])) for k in by['siv']]
    seed_diffs=[sum(int(by['siv'][k]['success'])-int(by[name][k]['success']) for k in by['siv'] if int(k[2])==s) for s in range(20)]
    per_scenario={}
    for d in range(1,8):
      for b in (17,19,21,23):
        diffs=[int(by['siv'][k]['success'])-int(by[name][k]['success']) for k in by['siv'] if float(k[0])==d and int(k[1])==b]
        per_scenario[f'd={d},b={b}']={'sum':sum(diffs),'distinct':sorted(set(diffs))}
    stats['pairs'][name]={'siv_only':sum(a and not b for a,b in pairs),'other_only':sum(b and not a for a,b in pairs),
        'both_success':sum(a and b for a,b in pairs),'neither':sum(not a and not b for a,b in pairs),
        'net_successes_by_seed':seed_diffs,'scenario_differences':per_scenario}
(root/'results/logs/review_statistics.json').write_text(json.dumps(stats,indent=2))
print(json.dumps({k:v for k,v in stats.items() if k!='pairs'},indent=2))
print('Greedy net gains by seed:',stats['pairs']['information_greedy']['net_successes_by_seed'])
