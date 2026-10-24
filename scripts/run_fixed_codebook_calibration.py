#!/usr/bin/env python3
"""Validate the missing-list estimate for fixed-size random codebooks.

Each codebook is sampled uniformly from all subsets of ``{0,1}^n`` with
cardinality ``2^k``. The script writes a calibration summary, binned
reliability data, and a reliability diagram.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.experiments import fixed_size_random_codebook_calibration
from src.plotting import configure_matplotlib


def _write_rows(path: Path, rows: list[dict]) -> None:
    """Write a nonempty list of dictionaries as a CSV table."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("no rows to write")
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict]:
    """Read a CSV table into a list of dictionaries."""
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _plot_bins(rows: list[dict], out_png: Path, summary: dict) -> None:
    """Plot the fixed-codebook reliability diagram.

    The log--log plot cannot display bins whose empirical frequency is zero.
    Those bins are omitted from the figure, but they remain in the CSV files
    and in the reported ECE.
    """
    try:
        configure_matplotlib()
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception as exc:  # pragma: no cover - optional plotting dependency
        print(f"plot skipped: matplotlib unavailable ({exc})")
        return

    all_rows = [r for r in rows if int(r["count"]) > 0]
    plot_rows = [r for r in all_rows if float(r["empirical"]) > 0.0]
    omitted_zero = len(all_rows) - len(plot_rows)
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

    plt.figure(figsize=(6.6, 5.0))
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
        plt.annotate(f"{c}", (xi, yi), fontsize=7, xytext=(5, 4), textcoords="offset points")

    title = (
        rf"Fixed-size random codebook, $[n,k]=[{int(float(summary['n']))},{int(float(summary['k']))}]$, "
        rf"$E_b/N_0={float(summary['ebn0_db']):g}\,\mathrm{{dB}}$"
    )
    plt.title(title, fontsize=10)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlim(xmin, xmax)
    plt.ylim(xmin, xmax)
    plt.xlabel(r"Mean binwise estimate of $\widehat{P}_{\mathrm{miss}}$")
    plt.ylabel(r"Empirical frequency of $X^n\notin\mathcal{L}_q$")
    plt.grid(True, which="both", linewidth=0.5, alpha=0.6)
    plt.legend(fontsize=8, loc="upper left")
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=300)
    plt.close()
    if omitted_zero:
        print(f"wrote {out_png} (omitted {omitted_zero} nonempty zero-event bin(s) from log-y plot)")
    else:
        print(f"wrote {out_png}")

def _latex_table_line(summary: dict) -> str:
    """Format the calibration summary as one LaTeX table row."""
    code = f"$[{summary['n']},{summary['k']}]$"
    ebn0 = f"${float(summary['ebn0_db']):g}$ dB"
    frames = int(summary["frames"])
    miss_events = int(summary["missing_events"])
    mean_pred = float(summary["mean_miss_prob"])
    emp = float(summary["empirical_miss_freq"])
    ece = float(summary["ece"])
    return (
        f"{code} & {ebn0} & {frames} & {miss_events} & "
        f"{mean_pred:.3e} & {emp:.3e} & {ece:.3e} \\\\"
    )

def main() -> None:
    """Run or replot the fixed-size random-codebook calibration experiment."""
    parser = argparse.ArgumentParser(
        description="Fixed-size random-codebook validation of the missing-list estimate."
    )
    parser.add_argument("--n", type=int, default=28)
    parser.add_argument("--k", type=int, default=18)
    parser.add_argument("--ebn0", "--snr-db", dest="ebn0", type=float, default=2.0)
    parser.add_argument("--rho", type=float, default=0.5)
    parser.add_argument("--codebooks", type=int, default=10)
    parser.add_argument("--frames-per-codebook", type=int, default=200)
    parser.add_argument("--qmax", "--max-queries", dest="qmax", type=int, default=5000)
    parser.add_argument("--eta", type=float, default=1e-4)
    parser.add_argument("--list-size", type=int, default=4)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--tail-stop", action="store_true", help="Use tail stopping instead of stopping at the prescribed list size.")
    parser.add_argument("--summary-out", type=Path, default=Path("results/fixed_codebook_calibration_summary.csv"))
    parser.add_argument("--bins-out", type=Path, default=Path("results/fixed_codebook_calibration_bins.csv"))
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--plot-only", action="store_true", help="Regenerate the reliability diagram from existing summary and bin CSV files.")
    args = parser.parse_args()

    if args.plot_only:
        summary_rows = _read_rows(args.summary_out)
        if len(summary_rows) != 1:
            raise ValueError(f"expected exactly one summary row in {args.summary_out}")
        summary = summary_rows[0]
        bin_rows = _read_rows(args.bins_out)
        print(f"read {args.summary_out}")
        print(f"read {args.bins_out}")
    else:
        print(
            "Starting fixed-size random-codebook validation "
            f"n={args.n}, k={args.k}, codebooks={args.codebooks}, "
            f"frames/codebook={args.frames_per_codebook}, Eb/N0={args.ebn0}, "
            f"rho={args.rho}, qmax={args.qmax}, list_size={args.list_size}",
            flush=True,
        )
        result = fixed_size_random_codebook_calibration(
            n=args.n,
            k=args.k,
            ebn0_db=args.ebn0,
            rho=args.rho,
            codebooks=args.codebooks,
            frames_per_codebook=args.frames_per_codebook,
            qmax=args.qmax,
            eta=args.eta,
            list_size=args.list_size,
            seed=args.seed,
            stop_on_list_size=not args.tail_stop,
        )
        summary = result["summary"]
        bins = result["bins"]

        summary_rows = [summary]
        bin_rows = []
        for i in range(len(bins["bin_center"])):
            bin_rows.append({
                "bin_center": float(bins["bin_center"][i]),
                "predicted": float(bins["predicted"][i]),
                "empirical": float(bins["empirical"][i]),
                "empirical_low": float(bins["empirical_low"][i]),
                "empirical_high": float(bins["empirical_high"][i]),
                "count": int(bins["count"][i]),
            })

        _write_rows(args.summary_out, summary_rows)
        _write_rows(args.bins_out, bin_rows)
        print(f"wrote {args.summary_out}")
        print(f"wrote {args.bins_out}")

    print("\nSummary")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("\nLaTeX table row")
    print(_latex_table_line(summary))

    if not args.no_plot:
        _plot_bins(bin_rows, args.bins_out.with_suffix(".png"), summary)


if __name__ == "__main__":
    main()
