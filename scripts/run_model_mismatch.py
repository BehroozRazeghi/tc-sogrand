#!/usr/bin/env python3
"""Evaluate sensitivity to the correlation parameter used by Exact-Markov ordering.

The channel uses ``rho_true``. The Exact-Markov enumerator uses each value
of ``rho_model`` in the sweep.
"""
from __future__ import annotations

import argparse, csv, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.experiments import compare_gauss_markov_rlc
from src.plotting import plot_metric_vs_x


def main() -> None:
    """Run the assumed-correlation sweep and write CSV and plots."""
    p=argparse.ArgumentParser(description="Sensitivity of the Exact-Markov ordering to the assumed correlation parameter.")
    p.add_argument('--n',type=int,default=128); p.add_argument('--k',type=int,default=116)
    p.add_argument('--frames','--trials',dest='frames',type=int,default=2000)
    p.add_argument('--snr-db','--ebn0',dest='ebn0',type=float,default=3.0)
    p.add_argument('--rho-true',type=float,default=0.5)
    p.add_argument('--rho-model',type=float,nargs='+',default=[0,0.25,0.5,0.75,0.9])
    p.add_argument('--max-queries','--qmax',dest='qmax',type=int,default=20000)
    p.add_argument('--eta',type=float,default=1e-5); p.add_argument('--seed',type=int,default=0)
    p.add_argument('--out',type=Path,default=Path('results/model_mismatch.csv'))
    p.add_argument('--progress-every',type=int,default=100); p.add_argument('--no-plot',action='store_true')
    args=p.parse_args()
    rows=[]; seed=args.seed
    for rho_hat in args.rho_model:
        part=compare_gauss_markov_rlc(
            n=args.n,k=args.k,ebn0_db=args.ebn0,rho=args.rho_true,rho_model=rho_hat,frames=args.frames,qmax=args.qmax,eta=args.eta,
            seed=seed,progress_every=args.progress_every,include_interleaved=False,methods_filter=('Tail-Calibrated-SOGRAND-exactMarkov',)
        )
        for r in part:
            r['sweep_rho_model']=rho_hat
        rows.extend(part); seed += 1
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {args.out}")
    if not args.no_plot:
        for ykey,ylabel,logy,fname in [('bler','BLER',True,'bler_vs_rho_model.png'),('avg_queries',r'Average membership-query count',False,'avg_queries_vs_rho_model.png')]:
            path=args.out.parent/fname
            # rename xkey expected by plotter
            plot_metric_vs_x(rows,path,xkey='sweep_rho_model',ykey=ykey,xlabel=r'Assumed correlation $\hat{\rho}$',ylabel=ylabel,logy=logy,ci=(ykey=='bler'))
            print(f"wrote {path}")
if __name__=='__main__': main()
