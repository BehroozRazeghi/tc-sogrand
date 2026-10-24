"""Plotting utilities for experiment CSV files.

The functions read the CSV summaries produced by the scripts and generate the
figures used in the numerical section. Labels and titles are written in a
publication style consistent with the manuscript notation.
"""
from __future__ import annotations

import csv
import math
import os
import shutil
from pathlib import Path
from typing import Iterable

METHOD_LABELS = {
    "Tail-Calibrated-SOGRAND-exactMarkov": r"TC-SOGRAND (Exact-Markov)",
    "Tail-Calibrated-SOGRAND-exactMarkovTail": r"TC-SOGRAND (Exact-Markov, tail stop)",
    "Tail-Calibrated-SOGRAND-exactMarkov-tailStop": r"TC-SOGRAND (Exact-Markov, tail stop)",
    "Tail-Calibrated-SOGRAND-memoryless": r"TC-SOGRAND (memoryless)",
    "Tail-Calibrated-SOGRAND-binaryMarkov": r"TC-SOGRAND (binary Markov)",
    "Tail-Calibrated-SOGRAND-MarkovApproxGE": r"TC-SOGRAND (Markov approximation)",
    "ORBGRAND-interleaved": r"Random-interleaved ORBGRAND",
    "ORBGRAND-AI-b1": r"ORBGRAND-AI, $b=1$",
    "ORBGRAND-AI-b2": r"ORBGRAND-AI, $b=2$",
    "ORBGRAND-AI-b4": r"ORBGRAND-AI, $b=4$",
    "ORBGRAND-AI-b8": r"ORBGRAND-AI, $b=8$",
    "ExactBlockProduct-b1": r"ExactBlockProduct, $b=1$",
    "ExactBlockProduct-b2": r"ExactBlockProduct, $b=2$",
    "ExactBlockProduct-b4": r"ExactBlockProduct, $b=4$",
    "ExactBlockProduct-b8": r"ExactBlockProduct, $b=8$",
    "GRAND-HW": r"GRAND (Hamming weight)",
}


PARAM_KEYS = ["rho", "p01", "p_bad", "rate", "qmax_sweep", "eta_sweep", "sweep_rho_model"]


def configure_matplotlib(use_tex: bool | None = None) -> None:
    """Configure Matplotlib text rendering for publication figures.

    The default renderer uses Matplotlib mathtext, which does not require a
    local LaTeX installation. Set ``TC_SOGRAND_USE_TEX=1`` or pass
    ``--use-tex`` to the regeneration script to render text through LaTeX.
    """
    import matplotlib as mpl

    if use_tex is None:
        env_value = os.environ.get("TC_SOGRAND_USE_TEX", "0").strip().lower()
        use_tex = env_value in {"1", "true", "yes"}

    if use_tex and shutil.which("latex") is not None:
        mpl.rcParams.update({
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "axes.unicode_minus": False,
        })
    else:
        mpl.rcParams.update({
            "text.usetex": False,
            "font.family": "serif",
            "mathtext.fontset": "cm",
            "axes.unicode_minus": False,
        })


def read_csv_rows(path: str | Path) -> list[dict]:
    """Read a CSV file as a list of dictionary rows."""
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))


def _to_float(row: dict, key: str, default: float = float("nan")) -> float:
    """Read a floating-point field from a CSV row."""
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def _to_int(row: dict, key: str, default: int = 0) -> int:
    """Read an integer field from a CSV row."""
    try:
        return int(float(row.get(key, default)))
    except Exception:
        return default


def _has_finite_metric(rows: list[dict], key: str) -> bool:
    """Return True when at least one row contains a finite value for the requested metric."""
    return any(math.isfinite(_to_float(row, key)) for row in rows)


def _finite_points(sub: list[dict], xkey: str, ykey: str, logy: bool = False) -> tuple[list[dict], list[float], list[float]]:
    """Return rows with finite x and y values for plotting."""
    rows_f: list[dict] = []
    xs_f: list[float] = []
    ys_f: list[float] = []
    for row in sub:
        x = _to_float(row, xkey)
        y = _to_float(row, ykey)
        if not (math.isfinite(x) and math.isfinite(y)):
            continue
        if logy and y < 0:
            continue
        rows_f.append(row)
        xs_f.append(x)
        ys_f.append(y)
    return rows_f, xs_f, ys_f


def _method_label(method: str) -> str:
    """Return a publication-style legend label for the method name."""
    return METHOD_LABELS.get(method, method)


def _secondary_key(rows: list[dict], xkey: str) -> str | None:
    """Return a secondary grouping key when an SNR sweep contains several fixed settings."""
    if xkey != "ebn0_db":
        return None
    for key in PARAM_KEYS:
        vals = {r.get(key, "") for r in rows if r.get(key, "") != ""}
        if len(vals) > 1:
            return key
    return None


def method_groups(rows: list[dict], xkey: str) -> list[tuple[tuple[str, str], list[dict]]]:
    """Group rows into plotted curves."""
    secondary = _secondary_key(rows, xkey)
    if secondary is None:
        keys = sorted({(r.get("method", ""), "") for r in rows}, key=str)
    else:
        keys = sorted({(r.get("method", ""), r.get(secondary, "")) for r in rows}, key=str)

    out = []
    for method, secondary_value in keys:
        if secondary is None:
            sub = [r for r in rows if r.get("method", "") == method]
        else:
            sub = [r for r in rows if r.get("method", "") == method and r.get(secondary, "") == secondary_value]
        sub.sort(key=lambda r: _to_float(r, xkey))
        out.append(((method, secondary_value), sub))
    return out


def _infer_title(rows: list[dict], xkey: str) -> str:
    """Infer a concise figure title from the available metadata."""
    if not rows:
        return ""
    r0 = rows[0]
    n = _to_int(r0, "n")
    k = _to_int(r0, "k")
    nk = rf"$[n,k]=[{n},{k}]$"

    def const(key: str) -> str | None:
        vals = {r.get(key, "") for r in rows if r.get(key, "") != ""}
        return next(iter(vals)) if len(vals) == 1 else None

    if "p01" in r0:
        p10 = const("p10")
        extra = rf", $p_{{10}}={float(p10):g}$" if p10 is not None else ""
        return rf"Binary Markov RLC setting, {nk}{extra}"
    if "p_bad" in r0:
        return rf"Gilbert--Elliott RLC setting, {nk}"
    if xkey == "sweep_rho_model":
        ebn0 = const("ebn0_db")
        rho = const("rho")
        pieces = [rf"Gauss--Markov model-mismatch study, {nk}"]
        if ebn0 is not None:
            pieces.append(rf"$E_b/N_0={float(ebn0):g}\,\mathrm{{dB}}$")
        if rho is not None:
            pieces.append(rf"$\rho={float(rho):g}$")
        return ", ".join(pieces)
    if xkey == "rho":
        ebn0 = const("ebn0_db")
        pieces = [rf"Gauss--Markov RLC setting, {nk}"]
        if ebn0 is not None:
            pieces.append(rf"$E_b/N_0={float(ebn0):g}\,\mathrm{{dB}}$")
        return ", ".join(pieces)
    if xkey == "rate":
        ebn0 = const("ebn0_db")
        rho = const("rho")
        pieces = [rf"Rate sweep, {nk}"]
        if ebn0 is not None:
            pieces.append(rf"$E_b/N_0={float(ebn0):g}\,\mathrm{{dB}}$")
        if rho is not None:
            pieces.append(rf"$\rho={float(rho):g}$")
        return ", ".join(pieces)
    if xkey == "qmax_sweep":
        ebn0 = const("ebn0_db")
        rho = const("rho")
        pieces = [rf"Query-budget sweep, {nk}"]
        if ebn0 is not None:
            pieces.append(rf"$E_b/N_0={float(ebn0):g}\,\mathrm{{dB}}$")
        if rho is not None:
            pieces.append(rf"$\rho={float(rho):g}$")
        return ", ".join(pieces)
    if xkey == "eta_sweep":
        ebn0 = const("ebn0_db")
        rho = const("rho")
        pieces = [rf"Tail-stopping tolerance sweep, {nk}"]
        if ebn0 is not None:
            pieces.append(rf"$E_b/N_0={float(ebn0):g}\,\mathrm{{dB}}$")
        if rho is not None:
            pieces.append(rf"$\rho={float(rho):g}$")
        return ", ".join(pieces)
    if xkey == "ebn0_db":
        rho = const("rho")
        pieces = [rf"Gauss--Markov RLC setting, {nk}"]
        if rho is not None:
            pieces.append(rf"$\rho={float(rho):g}$")
        return ", ".join(pieces)
    return nk


def plot_metric_vs_x(
    rows: list[dict],
    out_path: str | Path,
    xkey: str,
    ykey: str,
    xlabel: str,
    ylabel: str,
    logy: bool = False,
    ci: bool = False,
    title: str | None = None,
) -> None:
    """Plot one metric against the selected x-axis variable and write the figure to disk."""
    configure_matplotlib()
    import matplotlib.pyplot as plt
    import numpy as np

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7.4, 5.2))

    plotted = False
    secondary = _secondary_key(rows, xkey)
    for (method, secondary_value), sub in method_groups(rows, xkey):
        sub_f, xs, ys = _finite_points(sub, xkey=xkey, ykey=ykey, logy=logy)
        if not sub_f:
            continue

        label = _method_label(method)
        if xkey == "ebn0_db" and secondary is not None and secondary_value != "":
            try:
                if secondary == "rho":
                    label = rf"{label}, $\rho={float(secondary_value):g}$"
                elif secondary == "rate":
                    label = rf"{label}, $R_{{\mathrm{{c}}}}={float(secondary_value):g}$"
                else:
                    label = f"{label}, {secondary}={secondary_value}"
            except Exception:
                label = f"{label}, {secondary}={secondary_value}"

        if ci and ykey == "bler" and "bler_low" in sub_f[0]:
            lows = []
            highs = []
            ys_plot = []
            for y, r in zip(ys, sub_f):
                frames = max(1, _to_int(r, "frames", 1))
                display_floor = 1.0 / (2.0 * frames)
                low = _to_float(r, "bler_low")
                high = _to_float(r, "bler_high")

                if logy and y == 0.0:
                    # A zero Monte Carlo estimate cannot be drawn on a log axis.
                    # Display it at 1/(2N) and show only the upper Wilson interval.
                    y_disp = display_floor
                    low_disp = y_disp
                elif logy:
                    y_disp = max(y, display_floor)
                    low_disp = max(low, display_floor) if math.isfinite(low) else y_disp
                else:
                    y_disp = y
                    low_disp = low if math.isfinite(low) else y

                high_disp = high if math.isfinite(high) else y_disp
                if logy:
                    high_disp = max(high_disp, y_disp)
                lows.append(low_disp)
                highs.append(high_disp)
                ys_plot.append(y_disp)

            yerr = [
                np.maximum(0, np.asarray(ys_plot) - np.asarray(lows)),
                np.maximum(0, np.asarray(highs) - np.asarray(ys_plot)),
            ]
            plt.errorbar(xs, ys_plot, yerr=yerr, marker="o", capsize=2, linewidth=1.4, label=label)
        else:
            ys_plot = []
            for y, r in zip(ys, sub_f):
                if logy and y == 0.0:
                    ys_plot.append(1.0 / (2.0 * max(1, _to_int(r, "frames", 1))))
                else:
                    ys_plot.append(max(y, 1e-12) if logy else y)
            plt.plot(xs, ys_plot, marker="o", linewidth=1.4, label=label)
        plotted = True

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title or _infer_title(rows, xkey), fontsize=10)
    if logy:
        plt.yscale("log")
    plt.grid(True, which="both", linewidth=0.5, alpha=0.6)
    if plotted:
        plt.legend(fontsize=8)
    else:
        plt.text(0.5, 0.5, f"No finite data for {ykey}", ha="center", va="center", transform=plt.gca().transAxes)
    plt.tight_layout()
    plt.savefig(out_path, dpi=250)
    plt.close()


def write_standard_plots(rows: list[dict], out_csv: str | Path, xkey: str = "ebn0_db") -> list[Path]:
    """Generate the standard BLER, query-count, calibration, and software-work plots from a summary CSV file."""
    out_csv = Path(out_csv)
    out_dir = out_csv.parent
    xlabel = r"$E_b/N_0$ (dB)" if xkey == "ebn0_db" else xkey
    outputs: list[Path] = []
    specs = [
        ("bler", "BLER", "bler_vs_ebn0.png", True, True),
        ("avg_queries", r"Average membership-query count", "avg_queries_vs_ebn0.png", False, False),
        ("avg_complexity_units", r"Average software-work proxy $C_{\mathrm{sw}}$", "complexity_proxy_vs_ebn0.png", False, False),
        ("p99_queries", r"99th-percentile membership-query count", "p99_queries_vs_ebn0.png", False, False),
        ("mean_miss_prob", r"Mean estimated missing-list probability $\widehat{P}_{\mathrm{miss}}$", "mean_miss_vs_ebn0.png", True, False),
        ("found_rate", r"Found-codeword rate", "found_rate_vs_ebn0.png", False, False),
    ]
    for ykey, ylabel, fname, logy, ci in specs:
        if not _has_finite_metric(rows, ykey):
            continue
        p = out_dir / fname
        plot_metric_vs_x(rows, p, xkey=xkey, ykey=ykey, xlabel=xlabel, ylabel=ylabel, logy=logy, ci=ci)
        outputs.append(p)
    return outputs


def interpolate_snr_at_bler(rows: list[dict], target: float) -> dict[str, float]:
    """Estimate the SNR required to reach a target BLER by log-linear interpolation."""
    out: dict[str, float] = {}
    for (method, secondary_value), sub in method_groups(rows, "ebn0_db"):
        pts = [(_to_float(r, "ebn0_db"), _to_float(r, "bler")) for r in sub]
        pts = [(x, y) for x, y in pts if math.isfinite(x) and math.isfinite(y) and y > 0]
        pts.sort()
        val = float("nan")
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if (y0 - target) * (y1 - target) <= 0 and y0 != y1:
                ly0, ly1, lt = math.log10(y0), math.log10(y1), math.log10(target)
                t = (lt - ly0) / (ly1 - ly0)
                val = x0 + t * (x1 - x0)
                break
        key = _method_label(method) if secondary_value == "" else f"{_method_label(method)} [{secondary_value}]"
        out[key] = val
    return out


def write_gain_table(rows: list[dict], out_path: str | Path, targets: Iterable[float] = (1e-1, 1e-2, 1e-3)) -> None:
    """Write interpolated SNR values at the requested target BLER levels."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        fieldnames = ["target_bler", "method", "snr_db"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for target in targets:
            vals = interpolate_snr_at_bler(rows, target)
            for method, snr in vals.items():
                w.writerow({"target_bler": target, "method": method, "snr_db": snr})
