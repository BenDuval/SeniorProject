"""
process_iq_cleaned.py

1. Extract IQ from 'extracted_data.txt'
2. Remove flat/no-signal regions
3. Apply DC block (mean subtraction)
4. Save to 'IQData_cleaned.txt'
5. Plot time-domain and FFT spectrum
"""

import numpy as np
import matplotlib.pyplot as plt

RAW_FILE = "extracted_data.txt"
CLEANED_FILE = "IQData_cleaned.txt"
WINDOW = 50
VAR_THRESHOLD = 1e-6  # tune this to match flatness detection sensitivity

def load_iq(filepath):
    iq = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                i, q = float(parts[0]), float(parts[1])
                iq.append(i + 1j*q)
            except ValueError:
                continue
    return np.array(iq)

def save_iq(iq, filepath):
    with open(filepath, 'w') as f:
        for s in iq:
            f.write(f"{s.real:.6f} {s.imag:.6f}\n")

def remove_flat_regions(iq, window=WINDOW, threshold=VAR_THRESHOLD):
    mask = np.ones(len(iq), dtype=bool)
    for i in range(len(iq) - window):
        chunk = iq[i:i+window]
        if np.var(chunk.real) < threshold and np.var(chunk.imag) < threshold:
            mask[i:i+window] = False
    return iq[mask]

def plot_results(iq, title_prefix=""):
    plt.figure(figsize=(10,4))
    plt.plot(iq.real, label='I')
    plt.plot(iq.imag, label='Q')
    plt.title(f"{title_prefix}Time-Domain IQ Samples")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.tight_layout()

    n = len(iq)
    fft_vals = np.fft.fftshift(np.fft.fft(iq))
    freqs = np.fft.fftshift(np.fft.fftfreq(n, d=1))

    plt.figure(figsize=(10,4))
    plt.plot(freqs, np.abs(fft_vals))
    plt.title(f"{title_prefix}Magnitude Spectrum (FFT)")
    plt.xlabel("Normalized Frequency")
    plt.ylabel("Magnitude")
    plt.tight_layout()
    plt.show()

def main():
    print("🔍 Loading extracted_data.txt...")
    raw_iq = load_iq(RAW_FILE)
    print(f"Loaded {len(raw_iq)} samples.")

    print("✂️ Removing flat regions...")
    filtered_iq = remove_flat_regions(raw_iq)
    print(f"Retained {len(filtered_iq)} samples after flat region removal.")

    print("🧹 Applying DC block...")
    dc_blocked_iq = filtered_iq - np.mean(filtered_iq)

    print(f"💾 Saving cleaned IQ to {CLEANED_FILE}")
    save_iq(dc_blocked_iq, CLEANED_FILE)

    print("📊 Plotting results...")
    plot_results(dc_blocked_iq, title_prefix="Cleaned + DC Blocked: ")

if __name__ == "__main__":
    main()
