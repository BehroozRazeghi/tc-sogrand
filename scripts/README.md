# Scripts

This directory contains the experiment and plotting scripts used in the Tail-Calibrated SOGRAND study.

## Figure generation from archived results

`regenerate_plots_from_csv.py` regenerates the summary and sweep figures from CSV files in `results/`. It uses `plotting_utils.py` and does not require the source implementation.

## Experiment scripts

The `run_*.py` scripts record the simulations, command-line options, and parameter settings used in the study. They require source modules that are not distributed in this repository and therefore do not run from this repository alone.
