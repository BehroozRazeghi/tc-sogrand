#!/usr/bin/env python3
"""Run a five-frame demonstration of the Gauss--Markov RLC experiment.

This command is intended only to verify imports and the main simulation
path. It is not a Monte Carlo experiment.
"""
from __future__ import annotations

import sys
from pathlib import Path
from pprint import pprint

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.experiments import compare_gauss_markov_rlc


if __name__ == "__main__":
    out = compare_gauss_markov_rlc(
        n=32,
        k=24,
        ebn0_db=3.0,
        rho=0.5,
        frames=5,
        qmax=500,
        eta=1e-4,
        seed=42,
        progress_every=0,
        include_interleaved=True,
        include_mismatched=True,
    )
    pprint(out)
