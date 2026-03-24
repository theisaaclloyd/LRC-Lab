"""
lrc_fit.py  —  Python translation of lrc_fit.R
Fits a nonlinear least-squares LRC current model to measured frequency/current data.

Model:  I(f) = alpha / sqrt( beta^2 * (f - f0^2/f)^2 + 1 ) + io
  p[0] = f0     resonance frequency (Hz)
  p[1] = alpha  peak current (A)
  p[2] = beta   curve width parameter (proportional to L/R)
  p[3] = io     current offset (A)

Usage:
  python lrc_fit.py                      # reads output_simple.csv in same directory
  python lrc_fit.py my_data.csv          # specify a different input file
"""

import sys
import os
import csv
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_simple.csv")
MAX_ROWS = 20   # mirrors the R script's cap of 20 rows


# ---------------------------------------------------------------------------
# Model  (direct translation of R's lrccurve)
# ---------------------------------------------------------------------------
def lrc_model(f, p):
    """LRC current magnitude model."""
    f0, alpha, beta, io = p
    return alpha / np.sqrt(beta**2 * (f - f0**2 / f)**2 + 1) + io


def least_squares(p, freq, current):
    """Sum of squared residuals."""
    return np.sum((current - lrc_model(freq, p))**2)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    freq     = np.array([float(r["freq"])     for r in rows])
    nocore   = np.array([float(r["nocore"])   for r in rows])
    withcore = np.array([float(r["withcore"]) for r in rows])
    # cap at MAX_ROWS like the R script
    return freq[:MAX_ROWS], nocore[:MAX_ROWS], withcore[:MAX_ROWS]


# ---------------------------------------------------------------------------
# Fit
# ---------------------------------------------------------------------------
def fit(freq, current, p0, label):
    result = minimize(least_squares, p0, args=(freq, current), method="Nelder-Mead",
                      options={"xatol": 1e-9, "fatol": 1e-12, "maxiter": 100_000})
    p = result.x
    print(f"\n{'='*40}")
    print(f"  Fit results — {label}")
    print(f"{'='*40}")
    print(f"  f0    = {p[0]:.4f} Hz   (resonance frequency)")
    print(f"  alpha = {p[1]:.6f} A   (peak current)")
    print(f"  beta  = {p[2]:.6f}     (width / L·R parameter)")
    print(f"  io    = {p[3]:.6f} A   (current offset)")
    return p


# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
def plot_fit(freq, nocore, withcore, p_nc, p_wc):
    freq_dense = np.linspace(freq[0], freq[-1], 1000)

    fig = plt.figure(figsize=(8, 8))
    gs  = gridspec.GridSpec(2, 1, hspace=0.4)

    # --- With Core ---
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(freq, withcore, "o", color="steelblue", label="Data")
    ax1.plot(freq_dense, lrc_model(freq_dense, p_wc), "-", color="tomato", label="Fit")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Current (A)")
    ax1.set_title("LRC Circuit — With Core")
    ax1.legend()
    ax1.annotate(f"f₀ = {p_wc[0]:.2f} Hz", xy=(p_wc[0], lrc_model(np.array([p_wc[0]]), p_wc)[0]),
                 xytext=(p_wc[0] * 1.1, p_wc[1] * 0.85),
                 arrowprops=dict(arrowstyle="->", color="gray"), fontsize=9)

    # --- No Core ---
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(freq, nocore, "o", color="steelblue", label="Data")
    ax2.plot(freq_dense, lrc_model(freq_dense, p_nc), "-", color="tomato", label="Fit")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Current (A)")
    ax2.set_title("LRC Circuit — No Core")
    ax2.legend()
    ax2.annotate(f"f₀ = {p_nc[0]:.2f} Hz", xy=(p_nc[0], lrc_model(np.array([p_nc[0]]), p_nc)[0]),
                 xytext=(p_nc[0] * 1.1, p_nc[1] * 0.85),
                 arrowprops=dict(arrowstyle="->", color="gray"), fontsize=9)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lrc_fit.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to: {out_path}")
    plt.show()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    if not os.path.exists(csv_path):
        print(f"ERROR: file not found: {csv_path}")
        sys.exit(1)

    freq, nocore, withcore = load_csv(csv_path)
    print(f"Loaded {len(freq)} rows from {csv_path}")

    # Initial guesses — mirrors R script
    p0_wc = [60.0,  0.16, 0.013, 0.00]   # with core
    p0_nc = [90.0,  0.16, 0.005, 0.00]   # no core

    p_wc = fit(freq, withcore, p0_wc, "With Core")
    p_nc = fit(freq, nocore,   p0_nc, "No Core")

    plot_fit(freq, nocore, withcore, p_nc, p_wc)


if __name__ == "__main__":
    main()
