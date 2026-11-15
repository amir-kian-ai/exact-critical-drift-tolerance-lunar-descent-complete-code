"""Editable vector masters and Inkscape-rendered publication assets.

Numerical geometry is generated from raw CSV; Inkscape opens each SVG and
exports vector PDF and a PNG for inspection. Set INKSCAPE to its executable.
"""
from pathlib import Path
import csv,json,os,shutil,subprocess
import numpy as np
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pypdf import PdfReader,PdfWriter
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
root=Path(__file__).resolve().parents[1];out=root/'results/figures'
masters=out/'editable_svg';pub=out/'publication_pdf';preview=out/'previews'
for p in (masters,pub,preview):p.mkdir(parents=True,exist_ok=True)
ink=os.environ.get('INKSCAPE') or shutil.which('inkscape') or r'C:\Program Files\Inkscape\bin\inkscape.com'
if not Path(ink).exists():raise RuntimeError('Inkscape required; set INKSCAPE to its executable')
env=os.environ.copy()
for name,rel in [('INKSCAPE_PROFILE_DIR','inkscape'),('LOCALAPPDATA','local'),('XDG_CACHE_HOME','cache')]:
    d=root/'.cache'/rel;d.mkdir(parents=True,exist_ok=True);env[name]=str(d)
fontconfig=root/'.cache/fonts.conf'
fontconfig.write_text('<fontconfig><dir>C:/Windows/Fonts</dir><dir>'+str(Path(matplotlib.get_data_path())/'fonts/ttf').replace('\\','/')+'</dir><cachedir>'+str(root/'.cache/fontconfig').replace('\\','/')+'</cachedir></fontconfig>')
(root/'.cache/fontconfig').mkdir(exist_ok=True)
env['FONTCONFIG_FILE']=str(fontconfig)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
blue='#236192';orange='#b65321';gray='#e9edf1';dark='#202a35'
def read(name):
    with (root/'results/data'/name).open() as f:return list(csv.DictReader(f))
rows=[r for r in read('region.csv') if int(r['horizon'])==5]
fig,axes=plt.subplots(1,3,figsize=(6.3,1.85),sharex=True,sharey=True,layout='constrained')
for ax,key,title in zip(axes,('physical','siv','passive'),('Full information','SIV-GNC','Passive')):
    ds=sorted({float(r['half_separation_m']) for r in rows});bs=sorted({int(r['budget_mps']) for r in rows})
    z=[[int(next(r[key] for r in rows if float(r['half_separation_m'])==d and int(r['budget_mps'])==b)) for d in ds] for b in bs]
    ax.pcolormesh(ds,bs,z,cmap=ListedColormap([gray,blue]),vmin=0,vmax=1,shading='nearest',rasterized=False)
    ax.set(title=title,xlabel='Half-separation (m)',xticks=[1,3,5,7],yticks=[15,19,23,27])
axes[0].set_ylabel('Resource budget (m/s)')
fig.savefig(masters/'recovery.svg');plt.close(fig)
rows=read('sensitivity.csv')
fig,axes=plt.subplots(1,2,figsize=(6.3,1.9),layout='constrained',gridspec_kw={'width_ratios':[1.1,1]})
vals=np.array([[float(next(r['required_budget_mps'] for r in rows if float(r['half_separation_m'])==d and int(r['delay_s'])==t and float(r['epsilon_m'])==.5 and int(r['sensing_cost_mps'])==2)) for t in range(5)] for d in (4,5,6,7)])
axes[0].pcolormesh(range(5),range(4),np.isfinite(vals),cmap=ListedColormap([gray,'#dceaf5']),vmin=0,vmax=1,shading='nearest',rasterized=False)
axes[0].invert_yaxis()
for i in range(4):
 for j in range(5):axes[0].text(j,i,f'{vals[i,j]:.0f}' if np.isfinite(vals[i,j]) else '×',ha='center',va='center',fontsize=10,color=dark)
axes[0].set(xticks=range(5),yticks=range(4),yticklabels=[4,5,6,7],xlabel='First acquisition index',ylabel='Half-separation (m)',title='Required resource (m/s)')
curves=[]
for e in (0,.5,2,4):
    rr=sorted((r for r in rows if float(r['half_separation_m'])==6 and float(r['epsilon_m'])==e and int(r['delay_s'])==0),key=lambda r:int(r['sensing_cost_mps']))
    curves.append([float(r['required_budget_mps']) for r in rr])
assert all(v==curves[0] for v in curves)
axes[1].plot([0,1,2,4,8],curves[0],'-o',color=blue,ms=4)
axes[1].set(xlabel='Sensing charge (m/s)',ylabel='Required resource (m/s)',xticks=[0,2,4,6,8],yticks=[17,19,21,23,25])
axes[1].text(.03,.94,'Error bounds 0, 0.5, 2, 4 m\nAll four curves coincide\nCenters 12 m apart',transform=axes[1].transAxes,va='top',fontsize=8)
fig.savefig(masters/'tradeoffs.svg');plt.close(fig)

def svg(body,w=960,h=270):
 return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="160mm" height="{160*h/w}mm" viewBox="0 0 {w} {h}">
 <defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L7,3.5 L0,7 Z" fill="{dark}"/></marker></defs>
 <rect width="{w}" height="{h}" fill="white"/><g id="diagram-body" font-family="DejaVu Sans" font-size="18" fill="{dark}" stroke-width="2">{body}</g></svg>'''
def text(x,y,t,size=18,color=dark):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{t}</text>'
def line(x1,y1,x2,y2,arrow=False,color=dark):return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}"'+(' marker-end="url(#arrow)"' if arrow else '')+'/>'
b=text(10,23,'(a) Two-site benchmark',21)+text(495,23,'(b) Incompatible first actions',21)
b+=line(10,198,465,198)+text(12,254,'Safe sites: ±3 m, radius 0.5 m',18)
for x in (150,300):b+=f'<rect x="{x-12.5}" y="190" width="25" height="16" fill="{blue}"/>'
for x,label in ((225,'0: free'),(375,'6: charged')):
 b+=f'<path d="M{x},179 l-7,12 h14 Z" fill="{orange}"/>'+text(x-38,227,label,16)
for x in (125,325):
 b+=f'<circle cx="{x}" cy="72" r="7" fill="{blue}"/>'+line(x,87,x,145,True)
b+=text(36,61,'p = −4 m',17)+text(294,61,'p = +4 m',17)+text(152,123,'Prescribed',16)+text(152,143,'vertical descent',16)
b+=f'<path d="M125,72 L325,72" stroke="{orange}" stroke-dasharray="5,4" fill="none"/>'
b+=text(10,177,'Equal horizontal features',16,orange)+line(24,94,65,94,True)+text(13,81,'p',18)
b+=text(495,60,'Initial state',17)+text(652,60,'First action',17)+text(807,60,'Second action',17)
for y,init,a,c in ((103,'(−4 m, 0)','+1','−1'),(151,'(+4 m, 0)','−1','+1')):
 b+=text(500,y,init,18)+text(681,y,a,21,blue)+text(846,y,c,21,blue)+line(619,y-6,657,y-6,True)+line(738,y-6,820,y-6,True)
b+=line(780,75,780,174,color=orange)+text(716,199,'First observation',17,orange)
b+=text(501,230,'Each path costs 8; no common first action.',17)+text(501,254,'Observation arrives too late to recover.',17)
(masters/'benchmark.svg').write_text(svg(b),encoding='utf-8')
b=text(15,27,'Observation-feedback recursion: one candidate action',22)
for x,y,w,t in ((15,90,190,'Initial hypotheses'),(260,90,175,'Common action'),(540,50,190,'Successor subset'),(540,155,190,'Successor subset')):
 b+=f'<rect x="{x}" y="{y}" width="{w}" height="46" rx="5" fill="{gray}"/>'+text(x+10,y+29,t,17)
b+=line(207,113,255,113,True)+line(438,113,532,74,True)+line(438,113,532,178,True)
b+=text(445,53,'Observation 1',15)+text(445,222,'Observation 2',15)
b+=text(748,80,'Recoverable',18,blue)+text(748,184,'Infeasible',18,orange)
b+=text(15,257,'Charge the action before observing; reject a candidate if any possible successor is infeasible.',17)
(masters/'mechanism.svg').write_text(svg(b),encoding='utf-8')
records=[]
for p in sorted(masters.glob('*.svg')):
    # Native Inkscape alignment/refinement; editable text is retained in SVG.
    group='diagram-body' if p.stem in ('benchmark','mechanism') else 'figure_1'
    refined=p.with_suffix('.refined.svg')
    cmd=[ink,str(p),f'--actions=select-by-id:{group};object-align:hcenter page;select-clear',
         '--export-type=svg',f'--export-filename={refined}']
    r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',check=True,env=env)
    refined.replace(p)
    records.append({'input':p.name,'operation':'Inkscape native horizontal page alignment; SVG serialization','command':cmd,'stderr':r.stderr})
    for ext,target in [('pdf',pub/(p.stem+'.pdf')),('png',preview/(p.stem+'.png'))]:
        cmd=[ink,str(p),f'--export-type={ext}',f'--export-filename={target}']
        if ext=='pdf':cmd+=['--export-text-to-path']
        else:cmd+=['--export-width=1600']
        r=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",check=True,env=env)
        if ext=='pdf':
            # Opaque white-background figures need no page transparency group.
            # pdfTeX otherwise imports Cairo's group alongside its own /Group,
            # producing duplicate dictionary keys. Preserve all vector content.
            reader=PdfReader(target);writer=PdfWriter()
            for page in reader.pages:
                if '/Group' in page:del page['/Group']
                writer.add_page(page)
            with target.open('wb') as stream:writer.write(stream)
        records.append({'input':p.name,'output':target.name,'command':cmd,'stderr':r.stderr})
(root/'results/logs/inkscape.json').write_text(json.dumps(records,indent=2))
paper=root.parent/'SIV_GNC_APASE2027_Manuscript'
if paper.exists():
 for source,folder in ((masters,'editable_svg'),(pub,'publication_pdf')):
    dest=paper/'figures'/folder;dest.mkdir(parents=True,exist_ok=True)
    for p in source.iterdir():shutil.copy2(p,dest/p.name)
print('Inkscape rendered',len(list(masters.glob('*.svg'))),'editable SVG masters to PDF and PNG.')

