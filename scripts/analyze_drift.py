from pathlib import Path
import csv,json,statistics,math
root=Path(__file__).resolve().parents[1];out=root/'results/drift'
def read(n):
 with (out/f'{n}.csv').open() as f:return list(csv.DictReader(f))
rows=read('reserved');fixed=read('fixed');tim=read('timings');dia=read('rate_diagrams')
analysis=dict(summary=json.loads((out/'summary.json').read_text()),timings=[],by_gamma={},fixed_finite=sum(math.isfinite(float(x['fixed'])) for x in fixed))
for g in sorted({x['gamma'] for x in rows},key=float):
 rr=[x for x in rows if x['gamma']==g];analysis['by_gamma'][g]={key:sum(math.isfinite(float(x[key])) for x in rr) for key in ('static','drift','rectangular','passive')};analysis['by_gamma'][g]['n']=len(rr)
for n,m in sorted({(x['horizon'],x['hypotheses']) for x in tim}):
 result=dict(horizon=int(n),hypotheses=int(m))
 for method in ('interval','history'):
  rr=[x for x in tim if x['horizon']==n and x['hypotheses']==m and x['method']==method]
  result[method]=dict(median_ms=1000*statistics.median(float(x['runtime_s']) for x in rr),median_bytes=statistics.median(int(x['python_peak_bytes']) for x in rr),nodes=int(rr[0]['nodes']))
 result['speedup']=result['history']['median_ms']/result['interval']['median_ms'];analysis['timings'].append(result)
(out/'analysis.json').write_text(json.dumps(analysis,indent=2));print(json.dumps(analysis,indent=2))
