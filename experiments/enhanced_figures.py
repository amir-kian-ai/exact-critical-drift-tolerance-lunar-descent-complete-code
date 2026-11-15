"""CSV-derived vector figures, editable text, native Inkscape refinement/export."""
from pathlib import Path
import csv,json,os,shutil,subprocess
import numpy as np
root=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(root/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pypdf import PdfReader,PdfWriter
from matplotlib.colors import ListedColormap
out=root/'results/figures';masters=out/'editable_svg';pub=out/'publication_pdf';pre=out/'previews'
for p in (masters,pub,pre):p.mkdir(exist_ok=True,parents=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
blue='#236192';orange='#b65321';gray='#e9edf1'
def read(n):
 with (root/'results/enhanced'/f'{n}.csv').open() as f:return list(csv.DictReader(f))
summary=json.loads((root/'results/enhanced/summary.json').read_text());analysis=json.loads((root/'results/enhanced/analysis.json').read_text())
fig,ax=plt.subplots(1,2,figsize=(6.3,1.8),layout='constrained',gridspec_kw={'width_ratios':[1,1.3]})
for c,y,col in ((4,1,blue),(5,0,orange)):
 ax[0].plot([c-.5,c+.5],[y,y],color=col,lw=5,solid_capstyle='butt');ax[0].plot(c,y,'o',color=col)
ax[0].axvline(4.5,color='#555555',ls=':',lw=1);ax[0].set(xlim=(3.3,5.7),ylim=(-.5,1.5),yticks=[0,1],yticklabels=['p = 5 m','p = 4 m'],xticks=[3.5,4.5,5.5],xlabel='Numeric feature (m)',title='(a) Closed intervals touch')
ax[1].axis('off');ax[1].set_title('(b) Detection carries information')
for y,heading,a,b in ((.83,'Full visibility','[3.5, 4.5]','[4.5, 5.5]'),(.53,'R = 4, eta = 0','[3.5, 4.5]','No detection'),(.23,'R = 4, eta = 0.5','Interval or none','No detection')):
 ax[1].text(.01,y,heading,fontsize=8.5,weight='bold');ax[1].text(.03,y-.14,a,color=blue,fontsize=8.1);ax[1].text(.56,y-.14,b,color=orange,fontsize=8.1)
fig.savefig(masters/'visibility.svg');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(6.3,2.05),layout='constrained',gridspec_kw={'width_ratios':[1.3,1]})
keys=['(inf, 0)','(4, 0)','(4, 0.5)','(8, 0)','(8, 0.5)'];x=np.arange(5)
for offset,k,col,label in [(-.18,'adaptive',blue,'Adaptive'),(.18,'passive',orange,'Passive')]:
 vals=[summary['geometry_by_model'][s][k] for s in keys];bars=ax[0].bar(x+offset,vals,.35,color=col,label=label)
 ax[0].bar_label(bars,padding=2,fontsize=7)
ax[0].axhline(318,color='#555555',ls=':',lw=1);ax[0].text(0,323,'Full state: 318',fontsize=8)
ax[0].set(xticks=x,xticklabels=['Full','4 / 0','4 / .5','8 / 0','8 / .5'],ylim=(0,355),ylabel='Feasible cases / 360',xlabel='Footprint R / boundary band eta (m)',title='(a) Geometry stress panel');ax[0].legend(loc='upper right',fontsize=7,frameon=False,bbox_to_anchor=(1,.83),ncol=2,columnspacing=.8,handlelength=1.4)
cats=['physical','first_action','persistent_pair','feasible'];vals=[summary['historical_categories'][k] for k in cats]
ax[1].barh(np.arange(4),vals,color=[gray,orange,orange,blue],edgecolor='#555555',lw=.5)
ax[1].set(yticks=np.arange(4),yticklabels=['Individual failure','First action','Persistent pair','Recoverable'],xlabel='Cases / 144',xlim=(0,53),title='(b) Historical decomposition');ax[1].invert_yaxis()
for i,v in enumerate(vals):ax[1].text(v+1,i,str(v),va='center',fontsize=8)
fig.savefig(masters/'generalization.svg');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(6.3,1.95),layout='constrained')
rr=read('threshold');eps=sorted({float(r['epsilon']) for r in rr});z=[[int(np.isfinite(float(next(r['required'] for r in rr if float(r['epsilon'])==e and int(r['delay'])==d)))) for e in eps] for d in range(6)]
ax[0].pcolormesh(eps,range(6),z,cmap=ListedColormap([gray,blue]),vmin=0,vmax=1,shading='nearest')
ax[0].set(xticks=[4,5,6,6.5],yticks=[0,1,3,5],xlabel='Numeric error bound (m)',ylabel='First active index',title='(a) Recovery: blue feasible')
ax[0].text(4.1,2.8,'N = 5, initial p = ±6 m\nFinite cost = 19 m/s-equivalent\nTouching at 6 m loses recovery',fontsize=8)
for R,marker,col in [(float('inf'),'o',blue),(4,'s',orange)]:
 for n in (3,5,7):
  rs=[r for r in analysis['efficiency'] if r['horizon']==n and r['footprint']==R]
  ax[1].plot([r['hypotheses'] for r in rs],[r['node_ratio'] for r in rs],marker=marker,color=col,alpha={3:1,5:.7,7:.4}[n],ms=3,lw=1)
ax[1].set(xticks=[2,3,5,9],ylim=(.55,1.07),xlabel='Initial hypotheses',ylabel='Pruned / unpruned nodes',title='(b) Exact reduction, N = 3, 5, 7')
ax[1].text(2.2,.59,'Circles: full visibility; squares: R = 4 m',fontsize=7.2)
fig.savefig(masters/'threshold_efficiency.svg');plt.close(fig)
ink=os.environ.get('INKSCAPE') or shutil.which('inkscape') or r'C:\Program Files\Inkscape\bin\inkscape.com'
env=os.environ.copy();env['INKSCAPE_PROFILE_DIR']=str(root/'.cache/inkscape');env['FONTCONFIG_FILE']=str(root/'.cache/fonts.conf');records=[]
for name in ('visibility','generalization','threshold_efficiency'):
 p=masters/f'{name}.svg';ref=p.with_suffix('.refined.svg')
 commands=[[ink,str(p),'--actions=select-by-id:figure_1;object-align:hcenter page;select-clear','--export-type=svg',f'--export-filename={ref}']]
 subprocess.run(commands[0],check=True,capture_output=True,env=env);ref.replace(p)
 for ext,dest in [('pdf',pub),('png',pre)]:
  target=dest/f'{name}.{ext}';cmd=[ink,str(p),f'--export-type={ext}',f'--export-filename={target}', '--export-text-to-path' if ext=='pdf' else '--export-width=1600']
  result=subprocess.run(cmd,capture_output=True,text=True,errors='replace',check=True,env=env);commands.append(cmd)
  if ext=='pdf':
   reader=PdfReader(target);writer=PdfWriter()
   for page in reader.pages:
    if '/Group' in page:del page['/Group']
    writer.add_page(page)
   with target.open('wb') as f:writer.write(f)
 records.append(dict(figure=name,commands=commands,editable_text=True))
 paper=root.parent/'SIV_GNC_APASE2027_Manuscript'
 if paper.exists():
  for src,folder in [(masters,'editable_svg'),(pub,'publication_pdf')]:shutil.copy2(src/f'{name}.{ "svg" if src==masters else "pdf"}',paper/'figures'/folder)
(root/'results/logs/enhanced_inkscape.json').write_text(json.dumps(records,indent=2))
print('Exported three enhanced vector figures with Inkscape.')
