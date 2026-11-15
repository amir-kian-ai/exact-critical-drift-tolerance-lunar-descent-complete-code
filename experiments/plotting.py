import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def read(p):
    with p.open() as f:return list(csv.DictReader(f))
def plot_all(out):
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
    def save(fig,name):
        fig.savefig(out/'figures'/f'{name}.pdf',bbox_inches='tight')
        fig.savefig(out/'figures'/f'{name}.png',dpi=180,bbox_inches='tight');plt.close(fig)
    data=read(out/'data'/'region.csv')
    fig,axs=plt.subplots(1,3,figsize=(7,2.5),sharey=True)
    for ax,key,title in zip(axs,['physical','siv','passive'],['Full information','SIV-GNC','Passive information']):
        rows=[r for r in data if int(r['horizon'])==5]
        p=sorted(set(float(r['half_separation_m']) for r in rows));f=sorted(set(int(r['budget_mps']) for r in rows))
        z=np.array([[int(next(r[key] for r in rows if float(r['half_separation_m'])==x and int(r['budget_mps'])==y)) for x in p] for y in f])
        ax.pcolormesh(p,f,z,shading='nearest',cmap='Blues',vmin=0,vmax=1)
        ax.set(title=title,xlabel='Half-separation (m)');ax.set_xticks([1,3,5,7])
    axs[0].set_ylabel('Allocated budget (m/s)');fig.tight_layout();save(fig,'regions')
    rows=read(out/'data'/'sensitivity.csv')
    fig,axs=plt.subplots(1,2,figsize=(7,2.3))
    for p in (4.,5.,6.,7.):
        rr=[r for r in rows if float(r['half_separation_m'])==p and float(r['epsilon_m'])==.5 and int(r['sensing_cost_mps'])==2]
        val=[float(r['required_budget_mps']) for r in rr]
        axs[0].plot([int(r['delay_s']) for r in rr],[v if np.isfinite(v) else np.nan for v in val],'-o',label=f'{p:g} m')
    axs[0].set(xlabel='First allowed active acquisition (s)',ylabel='Required budget (m/s)');axs[0].legend(ncol=2,fontsize=7)
    for eps in (0.,):
        rr=[r for r in rows if float(r['half_separation_m'])==6 and float(r['epsilon_m'])==eps and int(r['delay_s'])==0]
        axs[1].plot([int(r['sensing_cost_mps']) for r in rr],[float(r['required_budget_mps']) for r in rr],'-o',label='0, 0.5, 2, 4 m (coincident)')
    axs[1].set(xlabel='Acquisition charge (m/s)',ylabel='Required budget (m/s)');axs[1].legend(title='Error bounds',fontsize=7)
    fig.tight_layout();save(fig,'sensitivity')
    tr=json.loads((out/'data'/'trajectories.json').read_text())
    fig,axs=plt.subplots(1,2,figsize=(7,2.4))
    for name in ('nominal_mpc','robust_mpc','information_greedy','siv'):
        r=tr[name];axs[0].plot([x['p'] for x in r],[x['z'] for x in r],'-o',label=name.replace('_',' '))
        axs[1].plot([x['k'] for x in r],[x['remaining'] for x in r],'-o',label=name.replace('_',' '))
    axs[0].set(xlabel='Horizontal position (m)',ylabel='Altitude (m)');axs[1].set(xlabel='Time (s)',ylabel='Remaining allocation (m/s)');axs[1].axhline(0,color='black',lw=.7)
    axs[0].legend(fontsize=6);fig.tight_layout();save(fig,'trajectories')
    summary=json.loads((out/'data'/'comparison.json').read_text())
    lines=['\\begin{tabular}{lrrrr}\\hline','Controller & Success (\\%) & Cert. (\\%) & Coverage (\\%) & Resource (m/s)\\\\\\hline']
    for r in summary:
        cov='--' if r['certificate_coverage'] is None else f"{100*r['certificate_coverage']:.1f}"
        label={'nominal_mpc':'Single-hypothesis','robust_mpc':'Common-sequence','passive':'Passive','information_greedy':'Information-greedy','siv':'SIV-GNC','free_sensing':'Uncharged sensing'}[r['controller']]
        lines.append(f"{label} & {100*r['success_rate']:.1f} & {100*r['certified_rate']:.1f} & {cov} & {r['mean_allocated_resource_mps']:.2f}"+r"\\")
    lines+=['\\hline\\end{tabular}']
    (out/'tables'/'comparison.tex').write_text('\n'.join(lines))
