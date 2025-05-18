import os
import subprocess
import zmq
import time
import numpy as np
import matplotlib.pyplot as plt

# === Trim Text File Function (Overwrites Same File) ===
def trim_text_file(input_file, x, y):
    with open(input_file, 'r') as f:
        lines = f.read().splitlines()

    first_lines = lines[:x]
    last_lines = lines[-y:] if y != 0 else []

    with open(input_file, 'w') as f:
        for line in first_lines + last_lines:
            f.write(line + '\n')

    print(f"Trimmed and overwritten: {input_file}")


# ---- Paths to Flowgraph ----
flowgraph_path = "TwoToneTransciever.py"

# ---- Start the GRC Flowgraph ----
first_process = subprocess.Popen(['python3', flowgraph_path])
print("Two-Tone Receive Flowgraph started successfully.")

# ---- Record the Time of Two-Tone Transmission ----
transmission_time = time.time()
print(f"Two-Tone originally transmitted at: {transmission_time:.6f} seconds since epoch")

# ---- Set Up ZMQ Subscribers ----
context = zmq.Context()

detect_socket = context.socket(zmq.SUB)
detect_socket.connect("tcp://127.0.0.1:8040")
detect_socket.setsockopt_string(zmq.SUBSCRIBE, '')

data_socket = context.socket(zmq.SUB)
data_socket.connect("tcp://127.0.0.1:5020")
data_socket.setsockopt_string(zmq.SUBSCRIBE, '')

poller = zmq.Poller()
poller.register(detect_socket, zmq.POLLIN)
poller.register(data_socket, zmq.POLLIN)

print("Monitoring for two-tone detection and data collection...")
detected = False
data_buffer = []

try:
    while True:
        socks = dict(poller.poll(timeout=100))

        if detect_socket in socks and socks[detect_socket] == zmq.POLLIN:
            detect_signal = detect_socket.recv_string()

            if detect_signal == "1" and not detected:
                detection_time = time.time()
                print(f"Two-Tone Detected at: {detection_time:.6f} seconds since epoch")
                detected = True
                print("Polling ZMQ for data...")

            if detect_signal == "0" and detected:
                print("Two-tone no longer detected. Stopping data collection.")
                break

        if detected and data_socket in socks and socks[data_socket] == zmq.POLLIN:
            data_msg = data_socket.recv()
            raw_data = np.frombuffer(data_msg, dtype=np.complex64)
            data_buffer.extend(raw_data)

    data_buffer = np.array(data_buffer)
    if len(data_buffer) == 0:
        print("No data received. Exiting.")
        exit()

    # ---- FFT Processing ----
    sample_rate = 5e6
    N = len(data_buffer)
    freq_axis = np.fft.fftfreq(N, d=1/sample_rate)
    fft_data = np.fft.fft(data_buffer)
    power_spectrum = np.abs(fft_data)**2

    valid_indices = np.where(np.abs(freq_axis) > 500e3)[0]
    filtered_power_spectrum = power_spectrum[valid_indices]
    filtered_freq_axis = freq_axis[valid_indices]

    sorted_indices = np.argsort(filtered_power_spectrum)[::-1]
    sorted_freqs = np.abs(filtered_freq_axis[sorted_indices])

    detected_freqs = []
    for freq in sorted_freqs:
        if not detected_freqs or all(abs(freq - f) > 10000 for f in detected_freqs):
            detected_freqs.append(freq)
        if len(detected_freqs) == 2:
            break

    if len(detected_freqs) < 2:
        print("Warning: Could not find two distinct peaks that meet the 500 Hz separation requirement.")
        detected_freqs = np.array([0, 0])
    else:
        detected_freqs = np.array(detected_freqs)

    expected_tones = np.array([1e6, 2e6])
    actual_tone_shift = np.mean(detected_freqs - expected_tones)

    expected_carrier = 440e6
    actual_carrier = expected_carrier + actual_tone_shift

    # ---- Save to Generic File (Overwritten Each Run) ----
    filename = "two_tone_master_data.txt"

    with open(filename, "w") as f:
        for sample in data_buffer:
            f.write(f"{sample.real:.6f} {sample.imag:.6f}\n")

        f.write(f"\n# Two-Tone Originally Transmitted at: {transmission_time:.6f} seconds since epoch\n")
        f.write(f"# Two-Tone Detected at: {detection_time:.6f} seconds since epoch\n")
        f.write(f"# Detected Baseband Frequencies: {detected_freqs[0]:.2f} Hz, {detected_freqs[1]:.2f} Hz\n")
        f.write(f"# Expected Baseband Frequencies: {expected_tones[0]:.2f} Hz, {expected_tones[1]:.2f} Hz\n")
        f.write(f"# Frequency Shift: {actual_tone_shift:.2f} Hz\n")
        f.write(f"# Estimated Carrier Frequency: {actual_carrier:.2f} Hz\n")

    print(f"Captured {len(data_buffer)} samples. Data saved to {filename}")
    print(f"Detected baseband frequencies: {detected_freqs[0]:.2f} Hz, {detected_freqs[1]:.2f} Hz")
    print(f"Estimated carrier frequency: {actual_carrier:.2f} Hz")

    # ---- Trim the Output File In-Place ----
    try:
        trim_text_file(filename, 10000, 7)
    except Exception as e:
        print(f"Trimming failed: {e}")

    detect_socket.close()
    data_socket.close()
    context.term()
    first_process.terminate()
    first_process.wait()
    print("Flowgraph terminated successfully.")

except KeyboardInterrupt:
    print("\nInterrupted by user. Shutting down...")
    first_process.terminate()
    first_process.wait()
    print("Flowgraph terminated.")
