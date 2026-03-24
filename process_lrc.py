import csv
import os

# Sig gen frequencies in display order (matches screenshot)
SIG_GEN_FREQS = [10, 13, 16, 20, 25, 30, 40, 50, 60, 75, 90, 115, 145, 180, 225, 300]

COL_CURRENT = "Latest: Current (A)"
COL_FFT_FREQ = "FFT: Time - Frequency (Hz)"
COL_FFT_MAG = "FFT: Potential - FFT"


def process_file(path):
    """Return (measured_freq, freq_uncertainty, peak_current, current_uncertainty)."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if rows and COL_FFT_MAG not in rows[0]:
        rows = [{k.strip(): v for k, v in row.items()} for row in rows]

    fft_rows = [r for r in rows if r.get(COL_FFT_MAG, "").strip() != ""]
    if not fft_rows:
        return None, None, None, None

    # Find row with max FFT magnitude → measured frequency
    peak_row = max(fft_rows, key=lambda r: float(r[COL_FFT_MAG]))
    measured_freq = float(peak_row[COL_FFT_FREQ])

    # Frequency uncertainty: spacing between consecutive FFT frequency bins
    fft_freqs = [float(r[COL_FFT_FREQ]) for r in fft_rows]
    freq_uncertainty = fft_freqs[1] - fft_freqs[0] if len(fft_freqs) >= 2 else None

    # Current values from time-domain column
    current_rows = [r for r in rows if r.get(COL_CURRENT, "").strip() != ""]
    current_values = [abs(float(r[COL_CURRENT])) for r in current_rows]
    peak_current = max(current_values) if current_values else None

    # Current uncertainty: spacing between consecutive current readings
    raw_currents = [float(r[COL_CURRENT]) for r in current_rows]
    if len(raw_currents) >= 2:
        steps = [abs(raw_currents[i + 1] - raw_currents[i]) for i in range(len(raw_currents) - 1)]
        # Use the minimum non-zero step as the resolution
        non_zero = [s for s in steps if s > 0]
        current_uncertainty = min(non_zero) if non_zero else None
    else:
        current_uncertainty = None

    return measured_freq, freq_uncertainty, peak_current, current_uncertainty


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results = []

    lab_data_dir = os.path.join(script_dir, "lab_data")
    for i, freq in enumerate(SIG_GEN_FREQS, start=1):
        nc_path = os.path.join(lab_data_dir, f"{freq}nc.csv")
        wc_path = os.path.join(lab_data_dir, f"{freq}wc.csv")

        nc_mf, nc_mf_unc, nc_peak, nc_peak_unc = (
            process_file(nc_path) if os.path.exists(nc_path) else (None, None, None, None)
        )
        wc_mf, wc_mf_unc, wc_peak, wc_peak_unc = (
            process_file(wc_path) if os.path.exists(wc_path) else (None, None, None, None)
        )

        meas_freq = nc_mf if nc_mf is not None else wc_mf
        freq_unc = nc_mf_unc if nc_mf_unc is not None else wc_mf_unc

        pct_error = (
            abs(meas_freq - freq) / freq * 100 if meas_freq is not None else None
        )

        results.append({
            "row": i,
            "sig_gen_freq": freq,
            "meas_freq": meas_freq,
            "freq_unc": freq_unc,
            "nc_peak": nc_peak,
            "nc_peak_unc": nc_peak_unc,
            "wc_peak": wc_peak,
            "wc_peak_unc": wc_peak_unc,
            "pct_error": pct_error,
        })

    out_path = os.path.join(script_dir, "output.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "",
            "Sig. Gen. Freq. (Hz)",
            "Measured Frequency", "±", "Uncertainty", "Units",
            "",
            "Peak Current - No Core", "±", "Uncertainty", "Units",
            "",
            "Peak Current - With Core", "±", "Uncertainty", "Units",
            "",
            "% Error (Freq)",
        ])
        for r in results:
            mf  = f"{r['meas_freq']:.4f}"  if r["meas_freq"]  is not None else ""
            mfu = f"{r['freq_unc']:.4f}"   if r["freq_unc"]   is not None else ""
            nc  = f"{r['nc_peak']:.6f}"    if r["nc_peak"]    is not None else ""
            ncu = f"{r['nc_peak_unc']:.6f}" if r["nc_peak_unc"] is not None else ""
            wc  = f"{r['wc_peak']:.6f}"    if r["wc_peak"]    is not None else ""
            wcu = f"{r['wc_peak_unc']:.6f}" if r["wc_peak_unc"] is not None else ""
            pct = f"{r['pct_error']:.4f}"  if r["pct_error"]  is not None else ""
            writer.writerow([
                r["row"],
                r["sig_gen_freq"],
                mf, "±", mfu, "Hz",
                "",
                nc, "±", ncu, "A",
                "",
                wc, "±", wcu, "A",
                "",
                pct,
            ])

    print(f"Written to {out_path}")
    print(
        f"\n{'Row':<4} {'SigGen':>8} {'MeasFreq':>12} {'±Freq':>10} "
        f"{'NC Peak I':>14} {'±NC':>12} {'WC Peak I':>14} {'±WC':>12} {'%Err':>8}"
    )
    print("-" * 100)
    for r in results:
        mf  = f"{r['meas_freq']:.4f}"   if r["meas_freq"]   is not None else "N/A"
        mfu = f"{r['freq_unc']:.4f}"    if r["freq_unc"]    is not None else "N/A"
        nc  = f"{r['nc_peak']:.6f}"     if r["nc_peak"]     is not None else "N/A"
        ncu = f"{r['nc_peak_unc']:.6f}" if r["nc_peak_unc"] is not None else "N/A"
        wc  = f"{r['wc_peak']:.6f}"     if r["wc_peak"]     is not None else "N/A"
        wcu = f"{r['wc_peak_unc']:.6f}" if r["wc_peak_unc"] is not None else "N/A"
        pct = f"{r['pct_error']:.4f}%"  if r["pct_error"]   is not None else "N/A"
        print(
            f"{r['row']:<4} {r['sig_gen_freq']:>8} {mf:>12} {mfu:>10} "
            f"{nc:>14} {ncu:>12} {wc:>14} {wcu:>12} {pct:>8}"
        )


if __name__ == "__main__":
    main()
