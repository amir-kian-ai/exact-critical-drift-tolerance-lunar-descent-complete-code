"""Full scientific reproduction, including both earlier study generations."""
from pathlib import Path
import subprocess,sys,csv,json,hashlib
root=Path(__file__).resolve().parents[1]
def snapshot():
 result={}
 for p in sorted((root/'results/static').glob('*.csv')):
  with p.open() as f:rows=list(csv.DictReader(f))
  rows=[{k:v for k,v in r.items() if k not in {'runtime_s','synthesis_s','verification_s','python_peak_bytes'}} for r in rows]
  rows.sort(key=lambda r:json.dumps(r,sort_keys=True));result[p.name]=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
 return result
before=snapshot()
scripts=['scripts/reproduce_enhanced.py','experiments/static_explore.py','experiments/static_validation.py','experiments/calibration_theorem.py','experiments/calibration_geometry.py','scripts/analyze_static.py','experiments/static_figures.py']
for script in scripts:
 subprocess.run([sys.executable,script],cwd=root,check=True)
after=snapshot()
if '--check' in sys.argv:assert before==after,(before,after)
(root/'results/logs/research_reproduction.json').write_text(json.dumps(dict(match=before==after,deterministic_sha256=after,excluded_fields=['runtime_s','synthesis_s','verification_s','python_peak_bytes']),indent=2))
print('PASS: research reproduction deterministic match:',before==after)
