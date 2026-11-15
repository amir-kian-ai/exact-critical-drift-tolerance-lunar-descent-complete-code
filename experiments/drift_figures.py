from pathlib import Path
import os,csv,json,subprocess,shutil
root=Path(__file__).resolve().parents[1];os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
import numpy as np
from pypdf import PdfReader,PdfWriter
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
out=root/'results/figures';masters=out/'editable_svg';pub=out/'publication_pdf';pre=out/'previews';blue='#236192';orange='#b65321';green='#22764b'
for folder in (masters,pub,pre):folder.mkdir(parents=True,exist_ok=True)
analysis=json.loads((root/'results/drift/analysis.json').read_text())
with (root/'results/drift/rate_diagrams.csv').open() as f:rows=list(csv.DictReader(f))
fig,axs=plt.subplots(1,2,figsize=(6.3,1.95),layout='constrained')
for ax,name,title in zip(axs,('old4','motion5'),('(a) Four-step case','(b) Five-step moving probe')):
 rr=[r for r in rows if r['model']==name];finite=sorted({float(r['value']) for r in rr if np.isfinite(float(r['value']))});low,high=min(finite),max(finite)
 endpoints=sorted([r for r in rr if r['kind']=='endpoint'],key=lambda r:float(r['gamma_float']))
 for left,right in zip(endpoints,endpoints[1:]):
  a,b=float(left['gamma_float']),float(right['gamma_float']);mid=next(r for r in rr if r['kind']=='interior' and a<float(r['gamma_float'])<b);v=float(mid['value'])
  if np.isfinite(v):
   ax.plot([a,b],[v,v],color=blue,lw=2)
   for edge,g in [(left,a),(right,b)]:ax.plot([g],[v],'o',mfc=blue if float(edge['value'])==v else 'white',mec=blue,ms=4)
  else:ax.axvspan(a,b,color='#eef0f2')
 for edge in endpoints:
  if np.isfinite(float(edge['value'])):ax.plot(float(edge['gamma_float']),float(edge['value']),'o',color=blue,ms=4)
 last=float(endpoints[-1]['gamma_float'])
 if last<1.25 and not np.isfinite(float(endpoints[-1]['value'])):ax.axvspan(last,1.25,color='#eef0f2')
 bad=min(float(r['gamma_float']) for r in rr if not np.isfinite(float(r['value'])))
 ax.text(max(.65,bad),low+1,'Infeasible',fontsize=9);ax.set(xlim=(-.04,1.25),ylim=(low-.6,high+.8),xticks=[0,.5,1,1.25],yticks=finite,xlabel=r'Drift bound $\gamma$ (m / observation)',ylabel=r'$C(\gamma)$ (m/s-equivalent)',title=title)
fig.savefig(masters/'drift_rates.svg');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(6.3,2.05),layout='constrained')
r=3  # Moving-probe geometric parameter, metre coordinates.
for values,col,label in [([r-1,r+.5],blue,'A'),([r,r-.5],green,'B')]:axs[0].plot([1,2],values,'o-',color=col,label=label)
axs[0].axhspan(r-1,r+.25,color='#eeeeee',zorder=-2);axs[0].set(xticks=[1,2],xticklabels=['Feature 0 m',f'Feature {2*r} m'],ylim=(1.8,3.8),ylabel='Feature center (m)',title=r'(a) Moving probe, $r=3$ m');axs[0].legend(frameon=False,loc='upper left',fontsize=8)
for acts,col,label in [([0,1,-1,0,0],blue,'A'),([0,1,-1,-1,1],green,'B')]:
 p=r-1 if label=='A' else r;v=0;tt=[];pp=[]
 for k,a in enumerate(acts):
  t=np.linspace(0,1,30);tt.extend(k+t);pp.extend(p+v*t+.5*a*t*t);p+=v+.5*a;v+=a
 axs[1].plot(tt,pp,color=col,label=label,lw=2)
axs[1].axvspan(0,2,color='#eeeeee',zorder=-2);axs[1].set(xticks=range(6),xlabel='Time (s)',ylabel='Position (m)',title='(b) Safe feedback recovery');axs[1].legend(frameon=False,fontsize=8)
fig.savefig(masters/'drift_probe.svg');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(6.3,1.9),layout='constrained')
gs=list(analysis['by_gamma']);x=np.arange(len(gs))
for offset,key,col,label in [(-.24,'static',green,'Constant'),(0,'drift',blue,'Drift'),(.24,'rectangular',orange,'Varying')]:
 vals=[analysis['by_gamma'][g][key] for g in gs];bars=axs[0].bar(x+offset,vals,.23,color=col,label=label)
axs[0].set(xticks=x,xticklabels=gs,ylim=(0,32),yticks=[0,10,20,30],xlabel=r'Drift bound $\gamma$ (m / observation)',ylabel='Feasible cases / 64',title='(a) Fresh reserved scenarios');axs[0].legend(loc='upper center',fontsize=6.5,ncol=3,frameon=False,columnspacing=.7,handlelength=.9)
for method,col,label in [('interval',blue,'Intervals'),('history',orange,'Full history')]:axs[1].plot(range(4),[t[method]['median_ms'] for t in analysis['timings']],'o-',color=col,label=label)
axs[1].set(xticks=range(4),xticklabels=[f"{t['horizon']} / {t['hypotheses']}" for t in analysis['timings']],yscale='log',xlabel=r'Horizon $N$ / hypotheses $M$',ylabel='Median synthesis (ms)',title='(b) Same rational arithmetic');axs[1].legend(frameon=False,fontsize=7)
axs[1].set(ylim=(10,1000),yticks=[10,100,1000]);axs[1].yaxis.set_minor_locator(NullLocator())
fig.savefig(masters/'drift_evidence.svg');plt.close(fig)
ink=os.environ.get('INKSCAPE') or shutil.which('inkscape') or r'C:\Program Files\Inkscape\bin\inkscape.com';env=os.environ.copy();env['INKSCAPE_PROFILE_DIR']=str(root/'.cache/inkscape');records=[]
if (root/'.cache/fonts.conf').exists():env['FONTCONFIG_FILE']=str(root/'.cache/fonts.conf')
for name in ('drift_rates','drift_probe','drift_evidence'):
 p=masters/f'{name}.svg';ref=p.with_suffix('.refined.svg');cmd=[ink,str(p),'--actions=select-by-id:figure_1;object-align:hcenter page;select-clear','--export-type=svg',f'--export-filename={ref}'];subprocess.run(cmd,check=True,capture_output=True,env=env);ref.replace(p);commands=[cmd]
 for ext,dest in [('pdf',pub),('png',pre)]:
  target=dest/f'{name}.{ext}';cmd=[ink,str(p),f'--export-type={ext}',f'--export-filename={target}','--export-text-to-path' if ext=='pdf' else '--export-width=1600'];subprocess.run(cmd,check=True,capture_output=True,env=env);commands.append(cmd)
  if ext=='pdf':
   reader=PdfReader(target);writer=PdfWriter()
   for page in reader.pages:
    if '/Group' in page:del page['/Group']
    writer.add_page(page)
   with target.open('wb') as f:writer.write(f)
 records.append(dict(name=name,commands=commands))
 paper=root.parent/'SIV_GNC_APASE2027_Manuscript'
 if (root.parent/'main.tex').exists():paper=root.parent
 if paper.exists():
  for folder,ext in [('editable_svg','svg'),('publication_pdf','pdf')]:shutil.copy2(out/folder/f'{name}.{ext}',paper/'figures'/folder)
(root/'results/logs/drift_inkscape.json').write_text(json.dumps(records,indent=2));print('Three drift figures exported.')
