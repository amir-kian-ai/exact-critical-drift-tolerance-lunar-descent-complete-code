"""Rerun all experiments and compare all deterministic result fields."""
from pathlib import Path
import csv,json,subprocess,sys,hashlib
root=Path(__file__).resolve().parents[1]; data=root/'results'/'data'
def snapshot():
    result={}
    for p in sorted(data.glob('*')):
        if p.suffix=='.csv':
            with p.open() as f:v=list(csv.DictReader(f))
        elif p.suffix=='.json':v=json.loads(p.read_text())
        else:continue
        def strip(x):
            if isinstance(x,dict):return {k:strip(v) for k,v in x.items() if k not in ('update_mean_ms','update_max_ms','runtime_ms','python_peak_bytes')}
            if isinstance(x,list):return [strip(v) for v in x]
            return x
        result[p.name]=hashlib.sha256(json.dumps(strip(v),sort_keys=True).encode()).hexdigest()
    return result
before=snapshot()
subprocess.run([sys.executable,'scripts/reproduce_all.py'],cwd=root,check=True)
after=snapshot()
assert before==after,(before,after)
(root/'results'/'logs'/'reproducibility.json').write_text(json.dumps(dict(match=True,deterministic_sha256=after,excluded_fields=['update_mean_ms','update_max_ms','runtime_ms','python_peak_bytes']),indent=2))
print('PASS: all deterministic result fields match across complete reruns')
