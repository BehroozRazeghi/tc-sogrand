#!/usr/bin/env python3
"""Run a code-rate sweep at fixed blocklength for the Gauss--Markov RLC setting.

The script varies ``k`` at fixed ``n`` and reports BLER, membership-query
counts, and the software-work proxy for the selected orderings.
"""
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.experiments import compare_gauss_markov_rlc
from src.plotting import plot_metric_vs_x


def main():
    """Run the rate sweep and write CSV and plots."""
    p=argparse.ArgumentParser(description='Code-rate sweep at fixed blocklength for the Gauss--Markov RLC setting.')
    p.add_argument('--n',type=int,default=128)
    p.add_argument('--k',type=int,nargs='+',default=[104,110,116,120])
    p.add_argument('--frames','--trials',dest='frames',type=int,default=2000)
    p.add_argument('--snr-db','--ebn0',dest='ebn0',type=float,default=3.0); p.add_argument('--rho',type=float,default=0.5)
    p.add_argument('--max-queries','--qmax',dest='qmax',type=int,default=20000); p.add_argument('--eta',type=float,default=1e-5)
    p.add_argument('--seed',type=int,default=0); p.add_argument('--progress-every',type=int,default=100)
    p.add_argument('--methods',nargs='*',default=['ORBGRAND-interleaved','ORBGRAND-AI-b8','Tail-Calibrated-SOGRAND-exactMarkov'])
    p.add_argument('--out',type=Path,default=Path('results/rate_sweep.csv'))
    p.add_argument('--include-exact-block-product', action='store_true', help='include the exact nonoverlapping block-product likelihood ablation')
    p.add_argument('--no-plot',action='store_true')
    args=p.parse_args(); rows=[]; seed=args.seed
    for k in args.k:
        part=compare_gauss_markov_rlc(n=args.n,k=k,ebn0_db=args.ebn0,rho=args.rho,frames=args.frames,qmax=args.qmax,eta=args.eta,seed=seed,progress_every=args.progress_every,methods_filter=tuple(args.methods),include_exact_block_product=args.include_exact_block_product)
        for r in part:
            r['rate']=float(k/args.n)
        rows.extend(part); seed+=1
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f'wrote {args.out}')
    if not args.no_plot:
        for ykey,ylabel,logy,fname in [('bler','BLER',True,'bler_vs_rate.png'),('avg_queries',r'Average membership-query count',False,'avg_queries_vs_rate.png'),('avg_complexity_units',r'Average software-work proxy $C_{\mathrm{sw}}$',False,'complexity_vs_rate.png')]:
            path=args.out.parent/fname
            plot_metric_vs_x(rows,path,xkey='rate',ykey=ykey,xlabel=r'Code rate $R_{\mathrm{c}}=k/n$',ylabel=ylabel,logy=logy,ci=(ykey=='bler'))
            print(f'wrote {path}')
if __name__=='__main__': main()
