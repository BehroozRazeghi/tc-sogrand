# Tail-Calibrated Soft-Output GRAND for Finite-Memory Noise-Effect Posteriors

This repository contains the archived results, figures, and scripts associated with **Tail-Calibrated Soft-Output GRAND for Finite-Memory Noise-Effect Posteriors**.

**Paper:** [arXiv:2608.04068](https://arxiv.org/abs/2608.04068)

The study considers membership-oracle simulations for GRAND-family decoders over binary random linear codes. The main experiments use binary additive channels for which the hard-decision noise-effect posterior, conditioned on the received soft information, is represented by a finite-memory energy.

## Source code

The `src/` implementation used to generate the reported results is not distributed in this repository because the applicability of third-party patent rights to this GRAND-based implementation remains unresolved.

The implementation does not contain source code from GRAND-MATLAB, SOGRAND-C, or other existing GRAND codebases.

The experiment scripts are included to record the simulations, command-line options, parameter settings, and analysis used in the paper. Scripts that depend on the source implementation do not run from this repository alone.

## Repository layout

```text
.
├── README.md
├── requirements.txt
├── results/       archived CSV outputs and figures
├── scripts/       experiment and plotting scripts
└── src/           source-code availability notice
```

## Environment

Python 3.10 or later is recommended. For the plotting scripts that operate on archived results:

```bash
python3 -m venv tcsogrand_env
source tcsogrand_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The summary and sweep figures can be regenerated from the archived CSV files with:

```bash
python scripts/regenerate_plots_from_csv.py
```

See [`scripts/README.md`](scripts/README.md) for details.

## Implementation used in the study

The following components describe the implementation used to generate the reported experiments. The corresponding source modules are not distributed in this repository.

### Codebooks

- Binary random linear codes with parity-check membership testing.
- Explicit fixed-size random codebooks for small-blocklength validation of the random-codebook occupancy estimate.

### Channels

- BPSK over AWGN.
- BPSK over real Gauss–Markov noise.
- Binary symmetric channel.
- Binary first-order Markov noise channel.
- Gilbert–Elliott hard-decision channel.

### Posterior energies and enumerators

- Memoryless AWGN posterior energy.
- First-order Gauss–Markov posterior energy for BPSK observations.
- First-order binary Markov noise energy.
- ORBGRAND reliability-weight ordering.
- ORBGRAND-AI-style nonoverlapping block-substitution ordering.
- Exact first-order finite-memory enumeration by A* search.
- Exact nonoverlapping block-product ablation.
- Restricted burst-atom ablation.

### Decoders and baselines

- `GRAND-HW`: hard-decision GRAND ordered by Hamming weight.
- `ORBGRAND-interleaved`: interleaving before the correlated channel, deinterleaving before decoding, and memoryless ORBGRAND ordering.
- `ORBGRAND-AI-b1`, `ORBGRAND-AI-b2`, `ORBGRAND-AI-b4`, `ORBGRAND-AI-b8`: ORBGRAND-AI-style block-substitution orderings.
- `ExactBlockProduct-b1`, `ExactBlockProduct-b2`, `ExactBlockProduct-b4`, `ExactBlockProduct-b8`: exact nonoverlapping block-product likelihood ablations.
- `Tail-Calibrated-SOGRAND-exactMarkov`: exact first-order Gauss–Markov posterior ordering with list-output missing-list estimates.
- `Tail-Calibrated-SOGRAND-exactMarkov-tailStop`: exact-Markov ordering with stopping based on the plug-in missing-list estimate.
- `Tail-Calibrated-SOGRAND-binaryMarkov`: first-order binary Markov hard-decision noise ordering.
- `Tail-Calibrated-SOGRAND-MarkovApproxGE`: first-order Markov approximation to the binary noise effect induced by a Gilbert–Elliott channel.

## Decoding modes

The same ordered membership-query sequence is used with different stopping rules.

- **First-hit decoding.** The decoder stops at the first listed codeword. This mode is used for the main BLER and membership-query comparisons.
- **List-output decoding.** The decoder stops after a prescribed list size is reached, or at the query limit. This mode is used for missing-list calibration.
- **Tail-stopping decoding.** The decoder continues after the first listed codeword and stops when the plug-in missing-list estimate is below the prescribed tolerance, or at the query limit. This mode is reported as the Exact-Markov-tailStop variant.

In the hard-decision summaries, the decoded word is the first listed codeword. Additional queries in the tail-stopping variant are used to estimate the missing-list probability and listed-codeword APPs.

## Experiment commands

The commands below record the configurations used for the reported experiments. They require the source implementation that is not distributed here.

### Main random-linear-code experiment

The main soft-input experiment uses a binary random linear code with `[n,k]=[128,116]`, BPSK modulation, real Gauss–Markov noise, and correlation coefficient `rho=0.5`.

Small run:

```bash
python scripts/run_orbgrand_ai_rlc.py \
  --n 128 --k 116 \
  --frames 200 \
  --snr-db -1 0 1 2 3 4 5 6 \
  --rho 0.5 \
  --max-queries 20000 \
  --eta 1e-4 \
  --seed 0 \
  --out results/fig3_rlc_rho05_small.csv \
  --progress-every 20 \
  --methods ORBGRAND-interleaved ORBGRAND-AI Tail-Calibrated-SOGRAND-exactMarkov \
  --include-exact-block-product \
  --include-tail-stop
```

Larger fixed-frame run:

```bash
python scripts/run_orbgrand_ai_rlc.py \
  --n 128 --k 116 \
  --frames 10000 \
  --snr-db 1 2 3 4 \
  --rho 0.5 \
  --max-queries 20000 \
  --eta 1e-4 \
  --seed 0 \
  --out results/fig3_rlc_rho05_paper.csv \
  --progress-every 500 \
  --methods ORBGRAND-interleaved ORBGRAND-AI Tail-Calibrated-SOGRAND-exactMarkov \
  --include-exact-block-product \
  --include-tail-stop
```

The experiment records BLER, membership-query counts, missing-list estimates, and related summary statistics. Generated outputs include:

- `bler_vs_ebn0.png`: BLER versus `E_b/N_0` with Wilson confidence intervals.
- `avg_queries_vs_ebn0.png`: average codebook membership queries.
- `p99_queries_vs_ebn0.png`: 99th-percentile membership queries.
- `mean_miss_vs_ebn0.png`: mean predicted missing-list probability where available.
- `found_rate_vs_ebn0.png`: probability that at least one codeword is found before the query budget.
- `complexity_proxy_vs_ebn0.png`: unweighted software-work proxy.
- `snr_gain_table.csv`: log-linear SNR interpolation at selected BLER targets.

### Fixed-size random-codebook validation

This experiment samples explicit fixed-size random codebooks and evaluates the plug-in missing-list estimate in the ensemble used by the occupancy analysis. The explicit codebook representation is intended for small `n` only.

```bash
python scripts/run_fixed_codebook_calibration.py \
  --n 28 --k 18 \
  --codebooks 20 \
  --frames-per-codebook 250 \
  --snr-db 0.0 \
  --rho 0.5 \
  --max-queries 5000 \
  --eta 1e-4 \
  --list-size 4 \
  --seed 13 \
  --summary-out results/fixed_codebook_calibration_summary_0db.csv \
  --bins-out results/fixed_codebook_calibration_bins_0db.csv
```

```bash
python scripts/run_fixed_codebook_calibration.py \
  --n 28 --k 18 \
  --codebooks 20 \
  --frames-per-codebook 250 \
  --snr-db 1.0 \
  --rho 0.5 \
  --max-queries 5000 \
  --eta 1e-4 \
  --list-size 4 \
  --seed 12 \
  --summary-out results/fixed_codebook_calibration_summary_1db.csv \
  --bins-out results/fixed_codebook_calibration_bins_1db.csv
```

### Missing-list calibration

Calibration compares the predicted missing-list probability with the empirical event that the transmitted codeword is absent from the output list.

Exact-Markov list-output calibration:

```bash
python scripts/run_sogrand_calibration.py \
  --method exactMarkov \
  --n 64 --k 52 \
  --frames 5000 \
  --snr-db 2.0 \
  --rho 0.5 \
  --max-queries 10000 \
  --eta 1e-4 \
  --list-size 4 \
  --seed 0 \
  --out results/calibration_exact_markov.csv
```

Exact-Markov tail-stopping calibration:

```bash
python scripts/run_sogrand_calibration.py \
  --method exactMarkovTail \
  --n 64 --k 52 \
  --frames 5000 \
  --snr-db 2.0 \
  --rho 0.5 \
  --max-queries 10000 \
  --eta 1e-4 \
  --list-size 4 \
  --seed 0 \
  --out results/calibration_exact_markov_tail.csv
```

Memoryless SOGRAND on the matched AWGN channel:

```bash
python scripts/run_sogrand_calibration.py \
  --method memoryless \
  --n 64 --k 52 \
  --frames 5000 \
  --snr-db 2.0 \
  --max-queries 10000 \
  --eta 1e-4 \
  --list-size 4 \
  --seed 0 \
  --out results/calibration_memoryless.csv
```

Memoryless SOGRAND applied to correlated observations:

```bash
python scripts/run_sogrand_calibration.py \
  --method memoryless-mismatched \
  --n 64 --k 52 \
  --frames 5000 \
  --snr-db 2.0 \
  --rho 0.5 \
  --max-queries 10000 \
  --eta 1e-4 \
  --list-size 4 \
  --seed 0 \
  --out results/calibration_memoryless_mismatched.csv
```

Calibration bins with few samples are treated as diagnostic summaries rather than precise rare-event estimates.

## Additional experiments

### Correlation-strength sweep

```bash
python scripts/run_rho_sweep.py \
  --n 128 --k 116 \
  --frames 5000 \
  --snr-db 3.0 \
  --rho 0 0.25 0.5 0.75 \
  --max-queries 20000 \
  --eta 1e-4 \
  --seed 1 \
  --out results/rho_sweep_ebn0_3.csv \
  --progress-every 500 \
  --include-exact-block-product
```

### Rate sweep

```bash
python scripts/run_rate_sweep.py \
  --n 128 \
  --k 104 110 116 120 \
  --frames 5000 \
  --snr-db 3.0 \
  --rho 0.5 \
  --max-queries 20000 \
  --seed 1 \
  --out results/rate_sweep.csv \
  --include-exact-block-product
```

### Model-mismatch sweep

This experiment fixes the true Gauss–Markov correlation coefficient and varies the coefficient assumed by the Exact-Markov decoder.

```bash
python scripts/run_model_mismatch.py \
  --n 128 --k 116 \
  --frames 5000 \
  --snr-db 3.0 \
  --rho-true 0.5 \
  --rho-model 0 0.25 0.5 0.75 0.9 \
  --max-queries 20000 \
  --seed 2 \
  --out results/model_mismatch.csv
```

### Missing-list stopping sweep

```bash
python scripts/run_eta_sweep.py \
  --n 128 --k 116 \
  --frames 5000 \
  --snr-db 3.0 \
  --rho 0.5 \
  --eta 1e-1 1e-2 1e-3 1e-4 1e-5 \
  --max-queries 20000 \
  --seed 3 \
  --out results/eta_sweep.csv
```

### Query-budget sweep

```bash
python scripts/run_qmax_sweep.py \
  --n 128 --k 116 \
  --frames 5000 \
  --snr-db 3.0 \
  --rho 0.5 \
  --qmax 1000 2000 5000 10000 20000 \
  --seed 4 \
  --out results/qmax_sweep.csv
```

### Binary Markov hard-decision channel

```bash
python scripts/run_binary_markov_rlc.py \
  --n 128 --k 116 \
  --frames 5000 \
  --p01 0.005 0.01 0.02 0.04 \
  --p10 0.30 \
  --max-queries 20000 \
  --seed 5 \
  --out results/binary_markov.csv
```

### Gilbert–Elliott hard-decision channel

```bash
python scripts/run_gilbert_elliott_rlc.py \
  --n 128 --k 116 \
  --frames 5000 \
  --p-good 1e-3 \
  --p-bad 0.05 0.10 0.20 0.30 \
  --p-gb 0.02 \
  --p-bg 0.30 \
  --max-queries 20000 \
  --seed 6 \
  --out results/gilbert_elliott.csv
```

The Gilbert–Elliott experiment uses a fitted first-order Markov approximation to the induced binary noise effect. It is a model-mismatch experiment, not an exact hidden-state posterior decoder.

## Output metrics

Experiment CSV files report a subset of the following quantities:

- `bler`: block error rate.
- `bler_low`, `bler_high`: Wilson score confidence interval for BLER.
- `found_rate`: probability that at least one codeword is found before the query limit; this is not the probability of correct decoding.
- `avg_queries`: average number of codebook membership queries.
- `median_queries`, `p90_queries`, `p99_queries`: query-count quantiles.
- `mean_miss_prob`: mean predicted missing-list probability where available.
- `avg_metric_evals`: average number of posterior-metric evaluations.
- `avg_heap_pops`: average number of priority-queue removals.
- `avg_precompute_ops`: method-specific preprocessing proxy.
- `avg_complexity_units`: unweighted sum `avg_queries + avg_metric_evals + avg_heap_pops + avg_precompute_ops`; it is not a runtime or hardware-complexity measure.

## Reproducibility notes

- The principal Monte Carlo scripts expose an explicit random-seed option.
- Several scripts accept both `--frames` and `--trials`; the examples above use `--frames`.
- BLER estimates at low error probability require a sufficient number of error events. For BLER near `1e-3` or below, increase `--frames` or use `--min-errors` and `--min-frames` in `run_orbgrand_ai_rlc.py`.
- Calibration bins with small counts should be interpreted as diagnostic summaries rather than precise rare-event probability estimates.

## Results and figure regeneration

Archived CSV outputs and figures are provided under `results/`.

The following script regenerates the summary and sweep figures from the archived CSV files:

```bash
python scripts/regenerate_plots_from_csv.py
```

This script uses only the archived CSV files and does not require the source implementation.

## License

The files distributed in this repository are licensed under the BSD 3-Clause License. See [`LICENSE`](LICENSE).

The license does not grant rights under third-party patents. See [`PATENT_NOTICE.md`](PATENT_NOTICE.md).

## Citation

If you use material from this repository, please cite:

```bibtex
@misc{razeghi2026tcsogrand,
  title   = {Tail-Calibrated Soft-Output GRAND for Finite-Memory Noise-Effect Posteriors},
  author  = {Razeghi, Behrooz},
  year    = {2026},
  eprint  = {2608.04068},
  archivePrefix = {arXiv}
}
```

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).
