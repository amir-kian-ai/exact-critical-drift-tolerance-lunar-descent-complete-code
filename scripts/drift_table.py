"""Regenerate the supplementary reserved-count table from recorded cases."""
from pathlib import Path
import csv,math
root=Path(__file__).resolve().parents[1]
with (root/'results/drift/reserved.csv').open() as f: rows=list(csv.DictReader(f))
lines=[r'\begin{tabular}{lrrrr}',r'\toprule',r'$\gamma$ ($\mathrm{m}$/observation) & Cases & Constant & Drift-aware & Varying \\',r'\midrule']
for g in sorted({x['gamma'] for x in rows},key=float):
 rr=[x for x in rows if x['gamma']==g]
 vals=[g,str(len(rr))]+[str(sum(math.isfinite(float(x[k])) for x in rr)) for k in ('static','drift','rectangular')]
 lines.append(' & '.join(vals)+r' \\')
lines += [r'\bottomrule',r'\end{tabular}']
text='\n'.join(lines)+'\n'
(root/'results/drift/summary_table.tex').write_text(text)
paper=root.parent/'SIV_GNC_APASE2027_Manuscript'
if (root.parent/'main.tex').exists(): paper=root.parent
if paper.exists():
 (paper/'tables').mkdir(exist_ok=True)
 (paper/'tables/drift_summary.tex').write_text(text)
