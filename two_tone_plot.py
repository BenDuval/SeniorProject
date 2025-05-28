# plot_two_tone.py

import numpy as np
import matplotlib.pyplot as plt

def load_two_tone_data(filename):
    samples = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            parts = line.strip().split()
            if len(parts) == 2:
                try:
                    real = float(parts[0])
                    imag = float(parts[1])
                    samples.append(real + 1j * imag)
                except ValueError:
                    continue
    return np.array(samples, dtype=np.complex64)

def plot_time_and_frequency(samples, sample_rate=5e6):
    # Time domain plot
    time_axis = np.arange(len(samples)) / sample_rate
    plt.figure()
    plt.plot(time_axis * 1e3, np.real(samples), label='Real')
    plt.plot(time_axis * 1e3, np.imag(samples), label='Imag', linestyle='--')
    plt.xlabel('Time (ms)')
    plt.ylabel('Amplitude')
    plt.title('Time Domain')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Frequency domain plot
    N = len(samples)
    freq_axis = np.fft.fftfreq(N, d=1/sample_rate)
    fft_data = np.fft.fft(samples)
    power_spectrum = 10 * np.log10(np.abs(fft_data)**2 + 1e-12)

    plt.figure()
    plt.plot(freq_axis / 1e6, power_spectrum)
    plt.xlabel('Frequency (MHz)')
    plt.ylabel('Power (dB)')
    plt.title('Frequency Domain')
    plt.grid(True)
    plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    filename = "two_tone_master_data.txt"
    data = load_two_tone_data(filename)
    if data.size == 0:
        print("No data found in file.")
    else:
        plot_time_and_frequency(data)
