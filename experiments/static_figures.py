"""Editable scientific figures, Inkscape native refinement and vector export."""
from pathlib import Path
import os,csv,json,subprocess,shutil
import numpy as np
root=Path(__file__).resolve().parents[1];os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from pypdf import PdfReader,PdfWriter
out=root/'results/figures';masters=out/'editable_svg';pub=out/'publication_pdf';pre=out/'previews'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
blue='#236192';orange='#b65321';gray='#e9edf1';green='#22764b'
def read(n):
 with (root/'results/static'/f'{n}.csv').open() as f:return list(csv.DictReader(f))
analysis=json.loads((root/'results/static/analysis.json').read_text())
fig,ax=plt.subplots(1,2,figsize=(6.3,2.0),layout='constrained')
ax[0].set(xlim=(-.3,6.3),ylim=(-1.6,1),xticks=[0,2,3,6],yticks=[],xlabel='Horizontal position (m)',title='(a) One threshold, two features')
ax[0].axhline(0,color='#aaaaaa',lw=1)
ax[0].scatter([0,6],[0,0],marker='^',s=65,color=orange);ax[0].scatter([2,3],[0,0],s=45,c=[blue,green])
ax[0].text(.1,.66,'Fixed threshold: 2.5 to 3.5 m',fontsize=8)
ax[0].text(.1,-.6,'At 2 m: detect, then miss',color=blue,fontsize=8.5)
ax[0].text(.1,-1.12,'At 3 m: detect twice or miss twice',color=green,fontsize=8.5)
ax[0].text(2,.2,'A',ha='center',color=blue);ax[0].text(3,.2,'B',ha='center',color=green)
t=np.linspace(0,4,161);p=np.where(t<=2,2,np.where(t<=3,2+.5*(t-2)**2,2.5+(t-3)-.5*(t-3)**2))
ax[1].plot(t,p,color=blue,lw=2,label='A: 2 m initial');ax[1].plot(t,np.full_like(t,3),color=green,ls='--',lw=2,label='B: 3 m initial')
ax[1].axvspan(0,2,color=gray);ax[1].set(xlim=(0,4),ylim=(1.9,3.6),xticks=range(5),yticks=[2,2.5,3],xlabel='Time (s)',ylabel='Position (m)',title='(b) Four-step certified recovery')
ax[1].text(.12,3.4,'Probe 0 m, then 6 m',fontsize=8);ax[1].text(2.1,3.4,'Feedback control',fontsize=8)
ax[1].legend(loc='lower right',fontsize=7,frameon=False)
fig.savefig(masters/'calibration_mechanism.svg');plt.close(fig)
names=['exploration','boundary','theorem_family','geometry_perturbation','heldout'];labels=['Exploratory\n120','Boundary\n540','Theorem family\n108','Geometry\n60','Reserved\n384']
fig,ax=plt.subplots(figsize=(6.3,1.85),layout='constrained');x=np.arange(5)
for offset,key,col,label in [(-.18,'static',blue,'Constant threshold'),(.18,'rectangular',orange,'Varying threshold')]:
 counts=[sum(np.isfinite(float(r[key])) for r in read(n)) for n in names];den=[len(read(n)) for n in names]
 bars=ax.bar(x+offset,[100*c/d for c,d in zip(counts,den)],.35,color=col,label=label)
 ax.bar_label(bars,labels=[str(c) for c in counts],fontsize=8,padding=2)
ax.set(xticks=x,xticklabels=labels,ylim=(0,145),yticks=[0,50,100],ylabel='Certified feasible (%)');ax.legend(loc='upper center',ncol=2,frameon=False,fontsize=8)
fig.savefig(masters/'calibration_results.svg');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(6.3,2.0),layout='constrained')
rr=[r for r in read('boundary') if r['footprint']=='3' and r['horizon']=='4' and r['sensing_cost']=='2'];es=sorted({float(r['epsilon']) for r in rr});etas=sorted({float(r['eta']) for r in rr});z=[]
for eta in etas:
 z.append([next(r for r in rr if float(r['epsilon'])==e and float(r['eta'])==eta) for e in es])
cat=[[0 if not np.isfinite(float(r['static'])) else 1 if np.isfinite(float(r['rectangular'])) else 2 for r in row] for row in z]
ax[0].pcolormesh(range(6),range(5),cat,cmap=ListedColormap([gray,'#c3dfd1',blue]),vmin=0,vmax=2,shading='nearest')
for i,row in enumerate(z):
 for j,r in enumerate(row):ax[0].text(j,i,str(int(float(r['static']))) if np.isfinite(float(r['static'])) else '×',ha='center',va='center',color='white' if cat[i][j]==2 else '#202a35',fontsize=8)
ax[0].set(xticks=range(6),xticklabels=['0','.25','.5','.625','.75','1'],yticks=range(5),yticklabels=['0','.25','.5','.75','1'],xlabel='Numeric error bound (m)',ylabel='Threshold halfwidth (m)',title='(a) Static optimum (m/s-equivalent)')
ax[0].legend(handles=[Patch(color=blue,label='Static only'),Patch(color='#c3dfd1',label='Both'),Patch(color=gray,label='Neither')],loc='upper center',bbox_to_anchor=(.5,-.3),ncol=3,fontsize=6.5,frameon=False,handlelength=.8,columnspacing=.8)
for method,col,label in [('static',blue,'Constant'),('rectangular',orange,'Varying')]:
 vals=[r['median_ms'] for r in analysis['timings'] if r['method']==method]
 ax[1].plot(range(4),vals,'o-',color=col,label=label)
ax[1].set(xticks=range(4),xticklabels=['3 / 2','3 / 3','5 / 2','5 / 3'],yscale='log',ylabel='Median synthesis (ms)',xlabel='Horizon / initial hypotheses',title='(b) Cost of retaining calibration');ax[1].legend(frameon=False,fontsize=8)
fig.savefig(masters/'calibration_boundary.svg');plt.close(fig)
ink=os.environ.get('INKSCAPE') or shutil.which('inkscape') or r'C:\Program Files\Inkscape\bin\inkscape.com';env=os.environ.copy();env['INKSCAPE_PROFILE_DIR']=str(root/'.cache/inkscape');env['FONTCONFIG_FILE']=str(root/'.cache/fonts.conf');records=[]
for name in ('calibration_mechanism','calibration_results','calibration_boundary'):
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
 if paper.exists():
  for folder,ext in [('editable_svg','svg'),('publication_pdf','pdf')]:
   dest=paper/'figures'/folder;dest.mkdir(parents=True,exist_ok=True)
   shutil.copy2(out/folder/f'{name}.{ext}',dest)
(root/'results/logs/static_inkscape.json').write_text(json.dumps(records,indent=2))
print('Three calibration figures exported with Inkscape.')
