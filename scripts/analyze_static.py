from pathlib import Path
import csv,json,math,statistics
root=Path(__file__).resolve().parents[1];out=root/'results/static'
def read(n):
 with (out/(n+'.csv')).open() as f:return list(csv.DictReader(f))
finite=lambda r,k:math.isfinite(float(r[k]))
counts={}
for name in ('exploration','boundary','theorem_family','heldout'):
 rows=read(name)
 counts[name]=dict(n=len(rows),static=sum(finite(r,'static') for r in rows),rectangular=sum(finite(r,'rectangular') for r in rows),new=sum(finite(r,'static') and not finite(r,'rectangular') for r in rows),saving=sum(finite(r,'rectangular') and float(r['static'])<float(r['rectangular']) for r in rows))
timings=[]
for n,m,method in [(n,m,method) for n in (3,5) for m in (2,3) for method in ('static','rectangular','independent_rational')]:
 rs=[r for r in read('timings') if int(r['horizon'])==n and int(r['hypotheses'])==m and r['method']==method]
 timings.append(dict(horizon=n,hypotheses=m,method=method,median_ms=1000*statistics.median(float(r['runtime_s']) for r in rs),median_peak_bytes=statistics.median(int(r['python_peak_bytes']) for r in rs),nodes=int(rs[0]['nodes'])))
held=read('heldout');groups={}
for key in ('horizon','draw','landmark','eta','epsilon'):
 groups[key]={value:dict(n=sum(r[key]==value for r in held),static=sum(r[key]==value and finite(r,'static') for r in held),new=sum(r[key]==value and float(r['static'])<float(r['rectangular']) for r in held)) for value in sorted({r[key] for r in held})}
result=dict(counts=counts,timings=timings,groups=groups,all_reset_equal=all(r['reset']==r['rectangular'] for r in held),fixed_finite=sum(finite(r,'fixed') for r in read('fixed')),heldout_synthesis_median_ms=1000*statistics.median(float(r['synthesis_s']) for r in held),heldout_verify_median_ms=1000*statistics.median(float(r['verification_s']) for r in held if finite(r,'static')))
(out/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
