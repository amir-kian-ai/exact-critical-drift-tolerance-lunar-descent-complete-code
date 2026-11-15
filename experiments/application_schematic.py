"""Editable vector schematic; finalized and exported using Inkscape CLI."""
from pathlib import Path
import os,subprocess,json,shutil,csv,math
from xml.sax.saxutils import escape
from pypdf import PdfReader,PdfWriter
root=Path(__file__).resolve().parents[1]
paper=root.parent/'SIV_GNC_APASE2027_Manuscript'
if (root.parent/'main.tex').exists():paper=root.parent
out=paper/'figures';out.mkdir(exist_ok=True)
# Check every recorded four-step rate cell before displaying its exact profile.
with (root/'results/drift/rate_diagrams.csv').open() as h: records=list(csv.DictReader(h))
for row in records:
 if row['model']=='old4':
  gamma=float(row['gamma_float']);value=float(row['value'])
  assert value==(16 if gamma==0 else 18 if gamma<=.5 else math.inf)

parts=['''<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="159mm" height="44.7mm" viewBox="0 0 960 270"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10Z" fill="#236192"/></marker></defs><g id="pipeline" font-family="DejaVu Sans" font-size="17" fill="#172d3e">''']
def text(x,y,t,size=17,weight='normal',color='#172d3e'):
 parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(t)}</text>')
def path(d,color='#236192',width=2,arrow=False,dash=False):
 parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="5,4"' if dash else '')+'/>')
def box(x,y,w,h,title):
 parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#f5f8fa" stroke="#aab8c3" stroke-width="1.5"/>');text(x+12,y+24,title,18,'bold')
box(2,2,300,133,'1  Select a visual feature')
box(330,2,300,133,'2  Observation history')
box(658,2,300,133,'3  Per-hypothesis update')
box(2,150,452,118,'5  Causal recovery decision')
box(482,150,476,118,'4  Critical drift-rate diagram')
path('M304 77 H326',arrow=True);path('M632 77 H654',arrow=True);path('M808 138 V146',arrow=True);path('M478 212 H458',arrow=True)
# Lander, camera ray, two surface features. Illustrative, not a simulated trajectory.
parts.append('<path d="M53 48 L83 48 L92 67 L44 67 Z" fill="#d8e6ef" stroke="#236192" stroke-width="2"/>')
path('M22 45 V72',arrow=True)  # Illustrative descent direction.
path('M47 67 L35 85 M88 67 L100 85 M29 85 H43 M92 85 H106')
parts.append('<rect x="61" y="63" width="13" height="10" fill="#236192"/>')
path('M68 75 L180 97',arrow=True);path('M13 100 H285',color='#637888')
parts.append('<path d="M170 100 L180 85 L190 100Z" fill="#22764b"/><path d="M248 100 L258 85 L268 100Z" fill="#aab8c3"/>')
text(121,65,'camera / feature',16);text(132,90,'selection',16)
text(16,123,'Detect if c ≤ θₖ; threshold drifts',16)
# History symbols, marked illustrative.
text(344,58,'Detect  →  Miss  →  Detect',18)
path('M348 80 H608',color='#8ba1b0')
text(344,105,'Constrain compatible threshold',16)
text(344,122,'trajectories (illustrative sequence)',16)
# Exact operations as printed with editable characters.
text(671,50,'I⁻ = (I + [−γ, γ]) ∩ [α, ω]',17)
text(671,73,'I⁺ = I⁻ ∩ observation constraint',16)
text(671,96,'Detect: [c, ∞)     Miss: (−∞, c)',16)
text(671,122,'Reject empty / incompatible sets',16)
# Actual four-step rate profile, explicit endpoint inclusion.
text(496,197,'γ = 0',18,'bold');text(640,197,'0 < γ ≤ 0.5',18,'bold');text(824,197,'γ > 0.5',18,'bold')
path('M496 207 H938',color='#9cabb7');path('M617 184 V238',color='#c8d2da',width=1);path('M801 184 V238',color='#c8d2da',width=1)
text(496,229,'C(γ) = 16',16,color='#236192');text(650,229,'C(γ) = 18',16,color='#236192');text(821,229,'infeasible',17,color='#7a4325')
text(496,254,'γ: m/observation; C(γ): m/s-equivalent',16)
# Causal constraints and terminal landings.
text(16,190,'Choose action from past outputs; remain safe',16)
text(16,213,'βₖ₊₁ = βₖ − q(aₖ, sₖ) ≥ 0',18)
text(16,236,'Terminal state xₙ ∈ 𝒢 at N',17)
text(16,259,'Model-based recovery certificate',18,'bold',color='#22764b')
parts.append('</g></svg>')
# N is the terminal index, not n (SVG subscript via tspan keeps typography editable).
svg=''.join(parts).replace('xₙ ∈ 𝒢 at N','x<tspan baseline-shift="sub" font-size="12">N</tspan> ∈ 𝒢')
f=out/'lunar_descent_drift_recovery.svg';f.write_text(svg,encoding='utf-8')
ink=os.environ.get('INKSCAPE') or shutil.which('inkscape') or r'C:\Program Files\Inkscape\bin\inkscape.com'
env=os.environ.copy();env['INKSCAPE_PROFILE_DIR']=str(root/'.cache/inkscape');commands=[]
# Inkscape performs object alignment and saves a refined editable SVG.
ref=out/'schematic_refined.svg';cmd=[ink,str(f),'--actions=select-by-id:pipeline;object-align:hcenter page;select-clear','--export-type=svg',f'--export-filename={ref}'];subprocess.run(cmd,check=True,capture_output=True,env=env);commands.append(cmd);ref.replace(f)
for ext in ('pdf','png'):
 cmd=[ink,str(f),f'--export-type={ext}',f'--export-filename={out/f.stem}.{ext}','--export-text-to-path' if ext=='pdf' else '--export-width=2400'];subprocess.run(cmd,check=True,capture_output=True,env=env);commands.append(cmd)
 if ext=='pdf':
  dest=out/f'{f.stem}.pdf';reader=PdfReader(dest);writer=PdfWriter()
  for page in reader.pages:
   if '/Group' in page:del page['/Group']
   writer.add_page(page)
  with dest.open('wb') as h:writer.write(h)
log=root/'results/logs/schematic_inkscape.json';log.parent.mkdir(parents=True,exist_ok=True);log.write_text(json.dumps(dict(tool='Inkscape CLI',commands=commands),indent=2))
print('Editable schematic aligned, saved and exported with Inkscape.')
