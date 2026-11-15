"""One command reproduces originals and enhanced results, tests, figures, audits.
Use --check to compare existing deterministic enhanced CSVs to the rerun.
Timing and Python traced peak allocations are explicitly nondeterministic.
"""
from pathlib import Path
import csv,json,subprocess,sys,hashlib
root=Path(__file__).resolve().parents[1]
def snapshot():
 result={}
 for p in sorted((root/'results/enhanced').glob('*.csv')):
  with p.open() as f:rows=list(csv.DictReader(f))
  rows=[{k:v for k,v in r.items() if k not in ('runtime_ms','python_peak_bytes')} for r in rows]
  rows.sort(key=lambda r:json.dumps(r,sort_keys=True))
  result[p.name]=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
 return result
before=snapshot()
for script in ('scripts/check_reproduction.py','experiments/enhancement.py','scripts/analyze_enhanced.py','experiments/enhanced_figures.py'):
 subprocess.run([sys.executable,script],cwd=root,check=True)
after=snapshot()
if '--check' in sys.argv:assert before==after,(before,after)
(root/'results/logs/enhanced_reproduction.json').write_text(json.dumps(dict(match=before==after,deterministic_sha256=after,excluded_fields=['runtime_ms','python_peak_bytes']),indent=2))
print('PASS: enhanced pipeline complete; deterministic match:',before==after)
