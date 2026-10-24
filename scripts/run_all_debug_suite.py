#!/usr/bin/env python3
"""Run a short smoke suite for the experiment scripts.

The commands use reduced frame counts and query budgets. They check the
main execution paths and do not reproduce the paper-scale Monte Carlo
experiments.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

COMMANDS = [
    [PYTHON, "scripts/run_orbgrand_ai_rlc.py", "--n", "64", "--k", "52", "--trials", "50", "--snr-db", "1", "2", "3", "--rho", "0.5", "--max-queries", "5000", "--out", "results/debug_fig3.csv", "--progress-every", "25", "--methods", "ORBGRAND-interleaved", "ORBGRAND-AI-b4", "ORBGRAND-AI-b8", "Tail-Calibrated-SOGRAND-exactMarkov"],
    [PYTHON, "scripts/run_rho_sweep.py", "--n", "64", "--k", "52", "--trials", "50", "--snr-db", "2", "--rho", "0", "0.5", "0.75", "--max-queries", "5000", "--out", "results/debug_rho.csv", "--progress-every", "25"],
    [PYTHON, "scripts/run_eta_sweep.py", "--n", "64", "--k", "52", "--trials", "30", "--snr-db", "2", "--rho", "0.5", "--eta", "1e-2", "1e-4", "--max-queries", "5000", "--out", "results/debug_eta.csv", "--progress-every", "15"],
    [PYTHON, "scripts/run_sogrand_calibration.py", "--method", "exactMarkov", "--n", "32", "--k", "24", "--trials", "100", "--snr-db", "2", "--rho", "0.5", "--max-queries", "1000", "--out", "results/debug_calibration.csv"],
]


def main() -> None:
    """Run each smoke command and stop on the first failed subprocess."""
    for cmd in COMMANDS:
        print("\n$ " + " ".join(cmd), flush=True)
        subprocess.run(cmd, cwd=ROOT, check=True)
    print("\nDebug suite completed. Outputs are in results/.")


if __name__ == "__main__":
    main()
