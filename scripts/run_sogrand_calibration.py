#!/usr/bin/env python3
"""Compute missing-list calibration curves for SOGRAND-style decoders.

The output CSV records binned missing-list estimates and empirical
missing-list frequencies. The optional plot is a log--log reliability
diagram; nonempty zero-event bins remain in the CSV and ECE calculation.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.experiments import calibration_experiment
from src.plotting import configure_matplotlib


def _read_rows(path: Path) -> list[dict]:
    """Read a calibration CSV table into a list of dictionaries."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _plot(rows: list[dict], out_csv: Path) -> None:
    """Plot the missing-list reliability diagram for a calibration CSV."""
    try:
        configure_matplotlib()
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception as exc:
        print(f"plot skipped: matplotlib unavailable ({exc})")
        return

    nonempty = [r for r in rows if int(r["count"]) > 0]
    plot_rows = [r for r in nonempty if float(r["empirical"]) > 0.0]
    omitted_zero = len(nonempty) - len(plot_rows)
    if not plot_rows:
        print("plot skipped: all nonempty bins have zero empirical frequency on a log y-axis")
        return

    x = np.asarray([float(r["predicted"]) for r in plot_rows])
    y = np.asarray([float(r["empirical"]) for r in plot_rows])
    lo = np.asarray([max(float(r["empirical_low"]), 1e-12) for r in plot_rows])
    hi = np.asarray([float(r["empirical_high"]) for r in plot_rows])
    counts = [int(r["count"]) for r in plot_rows]
    yerr = [np.maximum(0.0, y - lo), np.maximum(0.0, hi - y)]

    positive_values = np.concatenate([x[x > 0], y[y > 0], lo[lo > 0], hi[hi > 0]])
    xmin = max(1e-6, 10 ** np.floor(np.log10(np.min(positive_values))))
    xmax = min(1.0, 10 ** np.ceil(np.log10(np.max(positive_values))))
    xmin = min(xmin, float(np.min(x)) / 2.0)
    xmax = max(xmax, float(np.max(x)) * 1.6)
    xmin = max(xmin, 1e-6)
    xmax = min(xmax, 1.0)

    plt.figure(figsize=(6.5, 5.2))
    plt.plot(
        [xmin, xmax],
        [xmin, xmax],
        linestyle="--",
        linewidth=1.6,
        label=r"Ideal calibration ($y=x$)",
    )
    plt.errorbar(
        x,
        y,
        yerr=yerr,
        fmt="o",
        capsize=3,
        markersize=6,
        linewidth=1.2,
        label=r"Binned empirical frequency (95\% Wilson CI)",
    )
    for xi, yi, c in zip(x, y, counts):
        plt.annotate(str(c), (xi, yi), fontsize=7, xytext=(4, 4), textcoords="offset points")

    plt.xscale("log")
    plt.yscale("log")
    plt.xlim(xmin, xmax)
    plt.ylim(xmin, xmax)
    title_map = {
        "calibration_memoryless": r"Calibration of TC-SOGRAND (memoryless)",
        "calibration_exact_markov": r"Calibration of TC-SOGRAND (Exact-Markov)",
        "calibration_exact_markov_tail": r"Calibration of TC-SOGRAND (Exact-Markov, tail stop)",
    }
    plt.xlabel(r"Mean binwise estimate of $\widehat{P}_{\mathrm{miss}}$")
    plt.ylabel(r"Empirical frequency of $X^n\notin\mathcal{L}_q$")
    plt.title(title_map.get(out_csv.stem, r"Missing-list calibration"), fontsize=10)
    plt.grid(True, which="both", linewidth=0.5, alpha=0.6)
    plt.legend(fontsize=8, loc="upper left")
    plt.tight_layout()
    path = out_csv.parent / f"calibration_{out_csv.stem}.png"
    plt.savefig(path, dpi=300)
    plt.close()
    if omitted_zero:
        print(f"wrote {path} (omitted {omitted_zero} nonempty zero-event bin(s) from log-y plot)")
    else:
        print(f"wrote {path}")


def main() -> None:
    """Run or replot the missing-list calibration experiment."""
    p = argparse.ArgumentParser(description="Missing-list calibration for SOGRAND-style decoders.")
    p.add_argument("--method", choices=["memoryless", "memoryless-mismatched", "exactMarkov", "exactMarkovTail"], default="exactMarkov")
    p.add_argument("--n", type=int, default=64)
    p.add_argument("--k", type=int, default=52)
    p.add_argument("--ebn0", "--snr-db", dest="ebn0", type=float, default=2.0)
    p.add_argument("--rho", type=float, default=0.5)
    p.add_argument("--frames", "--trials", dest="frames", type=int, default=1000)
    p.add_argument("--qmax", "--max-queries", dest="qmax", type=int, default=10000)
    p.add_argument("--eta", type=float, default=1e-4)
    p.add_argument("--list-size", type=int, default=4)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", type=Path, default=Path("results/calibration.csv"))
    p.add_argument("--no-plot", action="store_true")
    p.add_argument("--plot-only", action="store_true", help="Regenerate the reliability diagram from an existing calibration CSV.")
    args = p.parse_args()
    if args.plot_only:
        rows = _read_rows(args.out)
        print(f"read {args.out}")
    else:
        print(
            f"Starting calibration method={args.method}, n={args.n}, k={args.k}, frames={args.frames}, "
            f"Eb/N0={args.ebn0}, rho={args.rho}, qmax={args.qmax}",
            flush=True,
        )
        data = calibration_experiment(
            method=args.method, n=args.n, k=args.k, ebn0_db=args.ebn0, rho=args.rho,
            frames=args.frames, qmax=args.qmax, eta=args.eta, list_size=args.list_size, seed=args.seed,
        )
        rows = []
        for i in range(len(data["bin_center"])):
            rows.append({
                "bin_center": float(data["bin_center"][i]),
                "predicted": float(data["predicted"][i]),
                "empirical": float(data["empirical"][i]),
                "empirical_low": float(data["empirical_low"][i]),
                "empirical_high": float(data["empirical_high"][i]),
                "count": int(data["count"][i]),
            })
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {args.out}")
    print("\nCalibration table")
    print("bin_center,predicted,empirical,empirical_low,empirical_high,count")
    for r in rows:
        print(f"{float(r['bin_center']):.4g},{float(r['predicted']):.4g},{float(r['empirical']):.4g},{float(r['empirical_low']):.4g},{float(r['empirical_high']):.4g},{int(r['count'])}")
    if not args.no_plot:
        _plot(rows, args.out)


if __name__ == "__main__":
    main()
