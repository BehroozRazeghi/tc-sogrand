"""Regenerate publication figures from previously saved CSV files.

This script redraws the standard summary figures and sweep figures from the
CSV files already present in the results directory. It does not rerun any
Monte Carlo experiments.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plotting_utils import plot_metric_vs_x, read_csv_rows, write_standard_plots


def _regen_standard(results_dir: Path, csv_name: str) -> None:
    path = results_dir / csv_name
    if not path.exists():
        return
    rows = read_csv_rows(path)
    for out in write_standard_plots(rows, path, xkey="ebn0_db"):
        print(f"wrote {out}")


def _regen_custom(results_dir: Path, csv_name: str, xkey: str, specs: list[tuple[str, str, bool, str]], xlabel: str) -> None:
    path = results_dir / csv_name
    if not path.exists():
        return
    rows = read_csv_rows(path)
    for ykey, ylabel, logy, fname in specs:
        out = results_dir / fname
        plot_metric_vs_x(rows, out, xkey=xkey, ykey=ykey, xlabel=xlabel, ylabel=ylabel, logy=logy, ci=(ykey == "bler"))
        print(f"wrote {out}")


def main() -> None:
    p = argparse.ArgumentParser(description="Regenerate figures from saved CSV files.")
    p.add_argument("--results-dir", type=Path, default=Path("results"))
    p.add_argument("--main-csv", type=str, default="fig3_rlc_rho05_paper_with_blockproduct.csv")
    p.add_argument("--use-tex", action="store_true", help="Render plot text with an external LaTeX installation.")
    args = p.parse_args()
    results_dir = args.results_dir
    if args.use_tex:
        import os
        os.environ["TC_SOGRAND_USE_TEX"] = "1"

    _regen_standard(results_dir, args.main_csv)

    _regen_custom(
        results_dir,
        "rho_sweep.csv",
        "rho",
        [
            ("bler", "BLER", True, "bler_vs_rho.png"),
            ("avg_queries", r"Average membership-query count", False, "avg_queries_vs_rho.png"),
            ("avg_complexity_units", r"Average software-work proxy $C_{\mathrm{sw}}$", False, "complexity_proxy_vs_rho.png"),
        ],
        xlabel=r"Correlation coefficient $\rho$",
    )
    _regen_custom(
        results_dir,
        "rate_sweep.csv",
        "rate",
        [
            ("bler", "BLER", True, "bler_vs_rate.png"),
            ("avg_queries", r"Average membership-query count", False, "avg_queries_vs_rate.png"),
            ("avg_complexity_units", r"Average software-work proxy $C_{\mathrm{sw}}$", False, "complexity_vs_rate.png"),
        ],
        xlabel=r"Code rate $R_{\mathrm{c}}=k/n$",
    )
    _regen_custom(
        results_dir,
        "qmax_sweep.csv",
        "qmax_sweep",
        [
            ("bler", "BLER", True, "bler_vs_qmax.png"),
            ("found_rate", r"Found-codeword rate", False, "found_rate_vs_qmax.png"),
            ("avg_queries", r"Average membership-query count", True, "avg_queries_vs_qmax.png"),
        ],
        xlabel=r"Maximum query budget $q_{\max}$",
    )
    _regen_custom(
        results_dir,
        "eta_sweep.csv",
        "eta_sweep",
        [
            ("bler", "BLER", True, "bler_vs_eta.png"),
            ("avg_queries", r"Average membership-query count", True, "avg_queries_vs_eta.png"),
            ("mean_miss_prob", r"Mean estimated missing-list probability $\widehat{P}_{\mathrm{miss}}$", True, "mean_miss_vs_eta.png"),
        ],
        xlabel=r"Missing-list tolerance $\eta$",
    )
    _regen_custom(
        results_dir,
        "binary_markov.csv",
        "p01",
        [
            ("bler", "BLER", True, "bler_vs_p01.png"),
            ("avg_queries", r"Average membership-query count", False, "avg_queries_vs_p01.png"),
            ("mean_miss_prob", r"Mean estimated missing-list probability $\widehat{P}_{\mathrm{miss}}$", True, "mean_miss_vs_p01.png"),
        ],
        xlabel=r"Burst-entry probability $p_{01}$",
    )
    _regen_custom(
        results_dir,
        "gilbert_elliott.csv",
        "p_bad",
        [
            ("bler", "BLER", True, "bler_vs_pbad.png"),
            ("avg_queries", r"Average membership-query count", False, "avg_queries_vs_pbad.png"),
        ],
        xlabel=r"Bad-state crossover probability $p_{\mathrm{bad}}$",
    )
    _regen_custom(
        results_dir,
        "model_mismatch.csv",
        "sweep_rho_model",
        [
            ("bler", "BLER", True, "bler_vs_rho_model.png"),
            ("avg_queries", r"Average membership-query count", False, "avg_queries_vs_rho_model.png"),
        ],
        xlabel=r"Assumed correlation $\hat{\rho}$",
    )

    print("Regenerated figures available from archived CSV summaries.")


if __name__ == "__main__":
    main()
