"""Reproduce new drift results without modifying earlier-generation data."""
from pathlib import Path
import csv,json,hashlib,subprocess,sys
root=Path(__file__).resolve().parents[1]
def snapshot():
 ans={}
 for f in sorted((root/'results/drift').glob('*.csv')):
  with f.open() as h:rows=list(csv.DictReader(h))
  rows=[{k:v for k,v in row.items() if k not in {'runtime_s','python_peak_bytes'}} for row in rows]
  rows.sort(key=lambda x:json.dumps(x,sort_keys=True));ans[f.name]=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
 return ans
before=snapshot()
subprocess.run([sys.executable,'-m','pytest','-q'],cwd=root,check=True)
for script in ('experiments/drift_diagnostic.py','experiments/drift_validation.py','scripts/analyze_drift.py','experiments/drift_figures.py'):
 subprocess.run([sys.executable,script],cwd=root,check=True)
after=snapshot()
if '--check' in sys.argv:assert before==after,(before,after)
(root/'results/logs/drift_reproduction.json').write_text(json.dumps(dict(match=before==after,deterministic_hashes=after,excluded=['runtime_s','python_peak_bytes']),indent=2))
print('PASS drift deterministic reproduction',before==after)
