#!/usr/bin/env python3
"""Run the hard-decision binary Markov-noise comparison.

The script sweeps the burst-entry probability, writes random-linear-code
Monte Carlo summaries, and plots BLER, membership-query counts, and
missing-list estimates.
"""
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.experiments import compare_binary_markov_rlc
from src.plotting import plot_metric_vs_x


def main():
    """Parse command-line options, run the sweep, and write CSV and plots."""
    p=argparse.ArgumentParser(description='Hard-decision binary Markov-noise membership-oracle comparison.')
    p.add_argument('--n',type=int,default=128); p.add_argument('--k',type=int,default=116)
    p.add_argument('--frames','--trials',dest='frames',type=int,default=2000)
    p.add_argument('--p01',type=float,nargs='+',default=[0.005,0.01,0.02,0.04])
    p.add_argument('--p10',type=float,default=0.30)
    p.add_argument('--max-queries','--qmax',dest='qmax',type=int,default=20000); p.add_argument('--eta',type=float,default=1e-5)
    p.add_argument('--seed',type=int,default=0); p.add_argument('--progress-every',type=int,default=100)
    p.add_argument('--out',type=Path,default=Path('results/binary_markov.csv')); p.add_argument('--no-plot',action='store_true')
    args=p.parse_args(); rows=[]; seed=args.seed
    for p01 in args.p01:
        rows.extend(compare_binary_markov_rlc(n=args.n,k=args.k,p01=p01,p10=args.p10,frames=args.frames,qmax=args.qmax,eta=args.eta,seed=seed,progress_every=args.progress_every))
        seed+=1
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f'wrote {args.out}')
    if not args.no_plot:
        for ykey,ylabel,logy,fname in [('bler','BLER',True,'bler_vs_p01.png'),('avg_queries',r'Average membership-query count',False,'avg_queries_vs_p01.png'),('mean_miss_prob',r'Mean estimated missing-list probability $\widehat{P}_{\mathrm{miss}}$',True,'mean_miss_vs_p01.png')]:
            path=args.out.parent/fname
            plot_metric_vs_x(rows,path,xkey='p01',ykey=ykey,xlabel=r'Burst-entry probability $p_{01}$',ylabel=ylabel,logy=logy,ci=(ykey=='bler'))
            print(f'wrote {path}')
if __name__=='__main__': main()
