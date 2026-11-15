"""Traceable summary and paired-seed bootstrap (fixed scenario panel)."""
import csv,json,hashlib
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'results'
with (out/'data'/'rollouts.csv').open() as f:rows=list(csv.DictReader(f))
names=sorted(set(r['controller'] for r in rows));seeds=sorted(set(int(r['seed']) for r in rows))
means={n:np.array([np.mean([int(r['success']) for r in rows if r['controller']==n and int(r['seed'])==s]) for s in seeds]) for n in names}
rng=np.random.default_rng(20261017);indices=rng.integers(len(seeds),size=(10000,len(seeds)))
paired={n:dict(difference=float(np.mean(means['siv']-means[n])),ci95=np.quantile((means['siv']-means[n])[indices].mean(axis=1),[.025,.975]).tolist()) for n in names if n!='siv'}
assert all(int(r['success']) for r in rows if r['controller']=='siv' and int(r['certified']))
with (out/'data'/'region.csv').open() as f:reg=list(csv.DictReader(f))
assert all(int(r['blind'])<=int(r['passive'])<=int(r['siv'])<=int(r['physical']) for r in reg)
with (out/'data'/'scaling.csv').open() as f:scale=list(csv.DictReader(f))
stats=dict(grid_points=len(reg),rollouts=len(rows),seeds=seeds,
    grid_counts={k:sum(int(r[k]) for r in reg) for k in ('physical','siv','passive','blind')},
    paired_seed_bootstrap=paired,scaling_max_ms=max(float(r['runtime_ms']) for r in scale),
    peak_traced_bytes=max(int(r['python_peak_bytes']) for r in scale),
    max_nodes=max(int(r['nodes']) for r in scale),max_edges=max(int(r['successor_edges']) for r in scale))
(out/'logs'/'audit.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats,indent=2))
