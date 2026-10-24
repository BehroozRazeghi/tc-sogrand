#!/usr/bin/env python3
"""Run a Gauss--Markov correlation sweep at fixed SNR and blocklength.

The script varies the channel correlation parameter and writes BLER,
membership-query, and software-work summaries for the selected orderings.
"""
from __future__ import annotations

import argparse, csv, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.experiments import compare_gauss_markov_rlc
from src.plotting import plot_metric_vs_x


def main() -> None:
    """Run the correlation sweep and write CSV and plots."""
    p = argparse.ArgumentParser(description="Gauss--Markov correlation sweep at fixed Eb/N0.")
    p.add_argument("--n", type=int, default=128)
    p.add_argument("--k", type=int, default=116)
    p.add_argument("--frames", "--trials", dest="frames", type=int, default=2000)
    p.add_argument("--snr-db", "--ebn0", dest="ebn0", type=float, default=3.0)
    p.add_argument("--rho", type=float, nargs="+", default=[0, 0.25, 0.5, 0.75])
    p.add_argument("--max-queries", "--qmax", dest="qmax", type=int, default=20000)
    p.add_argument("--eta", type=float, default=1e-5)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", type=Path, default=Path("results/rho_sweep.csv"))
    p.add_argument("--progress-every", type=int, default=100)
    p.add_argument("--methods", nargs="*", default=["ORBGRAND-interleaved", "ORBGRAND-AI-b4", "ORBGRAND-AI-b8", "Tail-Calibrated-SOGRAND-exactMarkov"])
    p.add_argument("--include-exact-block-product", action="store_true", help="include the exact nonoverlapping block-product likelihood ablation")
    p.add_argument("--no-plot", action="store_true")
    args = p.parse_args()
    rows=[]; seed=args.seed
    for rho in args.rho:
        rows.extend(compare_gauss_markov_rlc(
            n=args.n,k=args.k,ebn0_db=args.ebn0,rho=rho,frames=args.frames,qmax=args.qmax,eta=args.eta,
            seed=seed,progress_every=args.progress_every,methods_filter=tuple(args.methods),include_exact_block_product=args.include_exact_block_product
        ))
        seed += 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {args.out}")
    if not args.no_plot:
        for ykey,ylabel,logy,fname in [
            ('bler','BLER',True,'bler_vs_rho.png'),
            ('avg_queries',r'Average membership-query count',False,'avg_queries_vs_rho.png'),
            ('avg_complexity_units',r'Average software-work proxy $C_{\mathrm{sw}}$',False,'complexity_proxy_vs_rho.png'),
        ]:
            path=args.out.parent/fname
            plot_metric_vs_x(rows,path,xkey='rho',ykey=ykey,xlabel=r'Correlation $\rho$',ylabel=ylabel,logy=logy,ci=(ykey=='bler'))
            print(f"wrote {path}")

if __name__ == '__main__':
    main()
