#!/usr/bin/env python3
"""Run the main Gauss--Markov random-linear-code comparison.

The script compares the selected membership-oracle orderings, including
interleaved ORBGRAND, ORBGRAND-AI local-block orderings, optional
ExactBlockProduct ablations, and Exact-Markov Tail-Calibrated SOGRAND.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.experiments import compare_gauss_markov_rlc
from src.plotting import write_standard_plots, write_gain_table


def _fmt(v):
    """Format a table entry for compact console output."""
    if isinstance(v, float):
        if v != v:
            return "nan"
        return f"{v:.4g}"
    return str(v)


def _print_table(rows: list[dict]) -> None:
    """Print the main Monte Carlo summary columns."""
    cols = [
        "method", "rho", "rho_model", "ebn0_db", "frames", "errors", "bler", "bler_low", "bler_high",
        "avg_queries", "p99_queries", "avg_metric_evals", "avg_heap_pops", "avg_precompute_ops", "avg_complexity_units", "mean_miss_prob",
    ]
    cols = [c for c in cols if c in rows[0]]
    widths = {c: max(len(c), *(_fmt(r.get(c, "")).__len__() for r in rows)) for c in cols}
    print("\nSummary")
    print(" ".join(c.ljust(widths[c]) for c in cols))
    print(" ".join("-" * widths[c] for c in cols))
    for r in rows:
        print(" ".join(_fmt(r.get(c, "")).ljust(widths[c]) for c in cols))


def main() -> None:
    """Run the selected Gauss--Markov comparison and write result tables."""
    p = argparse.ArgumentParser(description="Gauss--Markov random-linear-code membership-oracle comparison.")
    p.add_argument("--n", type=int, default=128)
    p.add_argument("--k", type=int, default=116)
    p.add_argument("--frames", "--trials", dest="frames", type=int, default=1000)
    p.add_argument("--min-errors", type=int, default=0, help="stop a Monte Carlo run after this many errors; 0 disables this rule")
    p.add_argument("--min-frames", type=int, default=100, help="minimum number of frames before min-error stopping is allowed")
    p.add_argument("--qmax", "--max-queries", dest="qmax", type=int, default=20000)
    p.add_argument("--eta", type=float, default=1e-5)
    p.add_argument("--ebn0", "--snr-db", dest="ebn0", type=float, nargs="+", default=[-1, 0, 1, 2, 3, 4, 5, 6])
    p.add_argument("--rho", type=float, nargs="+", default=[0.5])
    p.add_argument("--rho-model", type=float, default=None, help="correlation parameter assumed by the Exact-Markov enumerator; default: true rho")
    p.add_argument("--ai-block-sizes", type=int, nargs="+", default=[1, 2, 4, 8])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", type=Path, default=Path("results/orbgrand_ai_rlc_results.csv"))
    p.add_argument("--progress-every", type=int, default=50)
    p.add_argument("--no-plot", action="store_true")
    p.add_argument("--methods", nargs="*", default=None, help="optional method-name filter")
    p.add_argument("--include-burst", action="store_true", help="include burst-atom ablation")
    p.add_argument("--include-tail-stop", action="store_true", help="include the Exact-Markov tail-stopping variant")
    p.add_argument("--include-exact-block-product", action="store_true", help="include the exact nonoverlapping block-product likelihood ablation")
    p.add_argument("--no-interleaved", action="store_true", help="omit the interleaved ORBGRAND baseline")
    p.add_argument("--include-mismatched", action="store_true", help="include memoryless no-interleaver mismatched baselines")
    args = p.parse_args()

    rows: list[dict] = []
    seed = args.seed
    for rho in args.rho:
        for eb in args.ebn0:
            print(f"Starting n={args.n}, k={args.k}, frames={args.frames}, Eb/N0={eb}, rho={rho}, qmax={args.qmax}", flush=True)
            rows.extend(compare_gauss_markov_rlc(
                n=args.n, k=args.k, ebn0_db=eb, rho=rho, frames=args.frames,
                qmax=args.qmax, eta=args.eta, seed=seed, progress_every=args.progress_every,
                ai_block_sizes=tuple(args.ai_block_sizes), include_burst=args.include_burst,
                include_interleaved=not args.no_interleaved, include_mismatched=args.include_mismatched,
                include_tail_stop=args.include_tail_stop, include_exact_block_product=args.include_exact_block_product,
                rho_model=args.rho_model,
                methods_filter=tuple(args.methods) if args.methods else None,
                min_errors=args.min_errors, min_frames=args.min_frames,
            ))
            seed += 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.out}")
    _print_table(rows)
    if len(args.ebn0) == 1:
        print("Note: only one Eb/N0 value was simulated; Eb/N0 plots contain markers rather than curves.")
    if not args.no_plot:
        for path in write_standard_plots(rows, args.out, xkey="ebn0_db"):
            print(f"wrote {path}")
        gain_path = args.out.parent / "snr_gain_table.csv"
        write_gain_table(rows, gain_path)
        print(f"wrote {gain_path}")


if __name__ == "__main__":
    main()
