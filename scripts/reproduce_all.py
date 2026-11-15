from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','pytest','-q'],cwd=root,check=True)
subprocess.run([sys.executable,'experiments/run_all.py'],cwd=root,check=True)
subprocess.run([sys.executable,'experiments/extended_validation.py'],cwd=root,check=True)
subprocess.run([sys.executable,'scripts/audit_results.py'],cwd=root,check=True)
subprocess.run([sys.executable,'scripts/review_statistics.py'],cwd=root,check=True)
subprocess.run([sys.executable,'scripts/export_manuscript.py'],cwd=root,check=True)
subprocess.run([sys.executable,'experiments/review_figures.py'],cwd=root,check=True)
