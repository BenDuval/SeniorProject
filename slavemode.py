import subprocess
import zmq
import time
import numpy as np
import matplotlib.pyplot as plt

# ---- Path to Flowgraph ----
flowgraph_path = "/home/ubuntu/Documents/Senior Project/Communication Protocol/SeniorProject/two_tone_slave.py"

# ---- Start the GRC Flowgraph ----
first_process = subprocess.Popen(['python3', flowgraph_path])
print("Two-Tone Receive Flowgraph started successfully.")

# ---- Set Up ZMQ Subscribers ----
context = zmq.Context()

# Subscriber for detecting two-tone flag (port 8040)
detect_socket = context.socket(zmq.SUB)
detect_socket.connect("tcp://127.0.0.1:8040")
detect_socket.setsockopt_string(zmq.SUBSCRIBE, '')

# Subscriber for receiving data samples (port 5020)
data_socket = context.socket(zmq.SUB)
data_socket.connect("tcp://127.0.0.1:5020")
data_socket.setsockopt_string(zmq.SUBSCRIBE, '')

# ---- Poller to Monitor Both ZMQ Sockets ----
poller = zmq.Poller()
poller.register(detect_socket, zmq.POLLIN)  # Listen for two-tone detection
poller.register(data_socket, zmq.POLLIN)    # Listen for incoming data

# ---- Monitoring ZMQ for Events ----
print("Monitoring for two-tone detection and data collection...")
detected = False
data_buffer = []
detection_time = None  # To store the timestamp of detection

try:
    while True:
        # Poll both sockets for events
        socks = dict(poller.poll(timeout=100))  # Check every 100 ms

        # Check if a message was received on the detect_socket
        if detect_socket in socks and socks[detect_socket] == zmq.POLLIN:
            detect_signal = detect_socket.recv_string()

            if detect_signal == "1" and not detected:
                # Record detection time
                detection_time = time.time()
                print(f"Two-Tone Detected at: {detection_time:.6f} seconds since epoch")
                detected = True  # Mark as detected
                print("Polling ZMQ for data...")

            if detect_signal == "0" and detected:
                print("Two-tone no longer detected. Stopping data collection.")
                break  # Exit loop when tone disappears

        # If detected, check for new data on data_socket
        if detected and data_socket in socks and socks[data_socket] == zmq.POLLIN:
            data_msg = data_socket.recv()

            # Convert binary data to numpy complex values
            raw_data = np.frombuffer(data_msg, dtype=np.complex64)
            data_buffer.extend(raw_data)  # Store received samples

    # ---- Convert Data to Numpy Array ----
    data_buffer = np.array(data_buffer)
    if len(data_buffer) == 0:
        print("No data received. Exiting.")
        exit()

    # ---- FFT Processing ----
    sample_rate = 5e6  # 
    N = len(data_buffer)
    freq_axis = np.fft.fftfreq(N, d=1/sample_rate)  # Frequency bins
    fft_data = np.fft.fft(data_buffer)  # Compute FFT
    power_spectrum = np.abs(fft_data)**2  # Power spectrum
    
    # Ignore frequencies below 1000 Hz
    valid_indices = np.where(np.abs(freq_axis) > 500e3)[0]  # Find indices where |freq| > 1000 Hz
    filtered_power_spectrum = power_spectrum[valid_indices]  # Filter power spectrum
    filtered_freq_axis = freq_axis[valid_indices]  # Filter corresponding frequencies

    # Find peaks sorted by power (descending order)
    sorted_indices = np.argsort(filtered_power_spectrum)[::-1]  # Sort in descending order
    sorted_freqs = np.abs(filtered_freq_axis[sorted_indices])  # Sorted frequencies by power

    # Select two distinct peaks with at least 10000 Hz separation
    detected_freqs = []
    for freq in sorted_freqs:
        if not detected_freqs or all(abs(freq - f) > 10000 for f in detected_freqs):
            detected_freqs.append(freq)
        if len(detected_freqs) == 2:
            break

    # Ensure we found two valid peaks
    if len(detected_freqs) < 2:
        print("Warning: Could not find two distinct peaks that meet the 500 Hz separation requirement.")
        detected_freqs = np.array([0, 0])  # Default to zero if detection fails
    else:
        detected_freqs = np.array(detected_freqs)

    # Expected baseband frequencies
    expected_tones = np.array([1e6, 2e6])  # Expected 1 MHz and 10 MHz tones
    actual_tone_shift = np.mean(detected_freqs - expected_tones)

    # Estimate actual carrier frequency
    expected_carrier = 440e6  # Expected carrier frequency
    actual_carrier = expected_carrier + actual_tone_shift

    # ---- Save Data to File in MATLAB-Compatible Format ----
    timestamp = int(time.time())
    filename = f"collected_data_{timestamp}.txt"
    
 

    with open(filename, "w") as f:
        for sample in data_buffer:
            f.write(f"{sample.real:.6f} {sample.imag:.6f}\n")  # Save in ASCII format

        # Append recorded timestamps and frequency analysis
        f.write(f"# Two-Tone Detected at: {detection_time:.6f} seconds since epoch\n")
        f.write(f"# Detected Baseband Frequencies: {detected_freqs[0]:.2f} Hz, {detected_freqs[1]:.2f} Hz\n")
        f.write(f"# Expected Baseband Frequencies: {expected_tones[0]:.2f} Hz, {expected_tones[1]:.2f} Hz\n")
        f.write(f"# Frequency Shift: {actual_tone_shift:.2f} Hz\n")
        f.write(f"# Estimated Carrier Frequency: {actual_carrier:.2f} Hz\n")

    print(f"Captured {len(data_buffer)} samples. Data saved to {filename}")
    print(f"Detected baseband frequencies: {detected_freqs[0]:.2f} Hz, {detected_freqs[1]:.2f} Hz")
    print(f"Estimated carrier frequency: {actual_carrier:.2f} Hz")

    # ---- Terminate the Flowgraph ----
    detect_socket.close()
    data_socket.close()
    context.term()
    first_process.terminate()
    first_process.wait()
    print("Flowgraph terminated successfully.")

except KeyboardInterrupt:
    print("\nInterrupted by user. Shutting down...")

    # Ensure all processes are terminated
    first_process.terminate()
    first_process.wait()

    print("Flowgraph terminated.")
