#!/usr/bin/env python3
"""Run the missing-list tolerance sweep for Exact-Markov tail stopping.

Only the Exact-Markov tail-stopping variant is evaluated. The sweep records
how the prescribed tolerance changes BLER, membership-query count, and the
reported missing-list estimate.
"""
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.experiments import compare_gauss_markov_rlc
from src.plotting import plot_metric_vs_x


def main():
    """Run the tolerance sweep and write the requested summary files."""
    p=argparse.ArgumentParser(description='Missing-list tolerance sweep for the Exact-Markov tail-stopping rule.')
    p.add_argument('--n',type=int,default=128); p.add_argument('--k',type=int,default=116)
    p.add_argument('--frames','--trials',dest='frames',type=int,default=2000)
    p.add_argument('--snr-db','--ebn0',dest='ebn0',type=float,default=3.0)
    p.add_argument('--rho',type=float,default=0.5); p.add_argument('--eta',type=float,nargs='+',default=[1e-1,1e-2,1e-3,1e-4,1e-5])
    p.add_argument('--max-queries','--qmax',dest='qmax',type=int,default=20000); p.add_argument('--seed',type=int,default=0)
    p.add_argument('--progress-every',type=int,default=100); p.add_argument('--out',type=Path,default=Path('results/eta_sweep.csv'))
    p.add_argument('--no-plot',action='store_true')
    args=p.parse_args(); rows=[]; seed=args.seed
    for eta in args.eta:
        part=compare_gauss_markov_rlc(n=args.n,k=args.k,ebn0_db=args.ebn0,rho=args.rho,frames=args.frames,qmax=args.qmax,eta=eta,seed=seed,progress_every=args.progress_every,include_interleaved=False,include_tail_stop=True,methods_filter=('Tail-Calibrated-SOGRAND-exactMarkov-tailStop',))
        for r in part: r['eta_sweep']=eta
        rows.extend(part); seed+=1
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f'wrote {args.out}')
    if not args.no_plot:
        for ykey,ylabel,logy,fname in [('bler','BLER',True,'bler_vs_eta.png'),('avg_queries',r'Average membership-query count',True,'avg_queries_vs_eta.png'),('mean_miss_prob',r'Mean estimated missing-list probability $\widehat{P}_{\mathrm{miss}}$',True,'mean_miss_vs_eta.png')]:
            path=args.out.parent/fname
            plot_metric_vs_x(rows,path,xkey='eta_sweep',ykey=ykey,xlabel=r'Missing-list tolerance $\eta$',ylabel=ylabel,logy=logy,ci=(ykey=='bler'))
            print(f'wrote {path}')
if __name__=='__main__': main()
