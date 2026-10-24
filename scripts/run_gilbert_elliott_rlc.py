#!/usr/bin/env python3
"""Run hard-decision experiments for the Gilbert--Elliott noise model.

The script sweeps the bad-state crossover probability and compares
GRAND-style orderings through BLER and membership-query counts.
"""
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.experiments import compare_gilbert_elliott_rlc
from src.plotting import plot_metric_vs_x


def main():
    """Parse command-line options, run the sweep, and write CSV and plots."""
    p=argparse.ArgumentParser(description='Hard-decision Gilbert--Elliott membership-oracle comparison.')
    p.add_argument('--n',type=int,default=128); p.add_argument('--k',type=int,default=116)
    p.add_argument('--frames','--trials',dest='frames',type=int,default=2000)
    p.add_argument('--p-good',type=float,default=1e-3); p.add_argument('--p-bad',type=float,nargs='+',default=[0.05,0.10,0.20,0.30])
    p.add_argument('--p-gb',type=float,default=0.02); p.add_argument('--p-bg',type=float,default=0.30)
    p.add_argument('--max-queries','--qmax',dest='qmax',type=int,default=20000); p.add_argument('--eta',type=float,default=1e-5)
    p.add_argument('--seed',type=int,default=0); p.add_argument('--progress-every',type=int,default=100)
    p.add_argument('--out',type=Path,default=Path('results/gilbert_elliott.csv')); p.add_argument('--no-plot',action='store_true')
    args=p.parse_args(); rows=[]; seed=args.seed
    for pb in args.p_bad:
        rows.extend(compare_gilbert_elliott_rlc(n=args.n,k=args.k,p_good=args.p_good,p_bad=pb,p_gb=args.p_gb,p_bg=args.p_bg,frames=args.frames,qmax=args.qmax,eta=args.eta,seed=seed,progress_every=args.progress_every))
        seed+=1
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f'wrote {args.out}')
    if not args.no_plot:
        for ykey,ylabel,logy,fname in [('bler','BLER',True,'bler_vs_pbad.png'),('avg_queries',r'Average membership-query count',False,'avg_queries_vs_pbad.png')]:
            path=args.out.parent/fname
            plot_metric_vs_x(rows,path,xkey='p_bad',ykey=ykey,xlabel=r'Bad-state crossover probability $p_{\mathrm{bad}}$',ylabel=ylabel,logy=logy,ci=(ykey=='bler'))
            print(f'wrote {path}')
if __name__=='__main__': main()
