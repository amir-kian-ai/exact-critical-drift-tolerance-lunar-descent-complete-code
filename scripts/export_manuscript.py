from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parents[1];r=root/'results';paper=root.parent/'SIV_GNC_APASE2027_Manuscript'
a=json.loads((r/'logs/audit.json').read_text());s=json.loads((r/'data/comparison.json').read_text());t=next(x for x in s if x['controller']=='siv')
text=(f"On the recorded Windows desktop with Python 3.12, mean SIV-GNC update time was {t['update_mean_ms']:.2f} ms "
f"and the maximum observed update was {t['update_max_ms']:.2f} ms. A separate cold-cache scaling sweep used horizons "
f"3--7, two to nine hypotheses and three repetitions. Its largest measured solve took {a['scaling_max_ms']:.1f} ms, "
f"with up to {a['max_nodes']} cached nodes, {a['max_edges']} successor edges, and "
f"{a['peak_traced_bytes']/1024:.1f} KiB of traced Python allocations.")
(r/'tables/runtime.tex').write_text(text)
if paper.exists():
 for folder in ('figures','tables'):
  for f in (r/folder).iterdir():
   if f.suffix in ('.pdf','.tex'):shutil.copy2(f,paper/folder/f.name)
