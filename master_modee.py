import subprocess
import zmq
import time
import numpy as np

# === Paths ===
flowgraph_path = "/home/ubuntu/Documents/Senior Project/Communication Protocol/SeniorProject/TwoToneTransciever.py"
ZMQ_DATA_PORT = 5020
ZMQ_DETECT_PORT = 8040
MAX_SAMPLES = 30000

# === Start Flowgraph ===
first_process = subprocess.Popen(['python3', flowgraph_path])
print("Two-Tone Receive Flowgraph started successfully.")

transmission_time = time.time()

# === ZMQ Setup ===
context = zmq.Context()

detect_socket = context.socket(zmq.SUB)
detect_socket.connect(f"tcp://127.0.0.1:{ZMQ_DETECT_PORT}")
detect_socket.setsockopt_string(zmq.SUBSCRIBE, "")

data_socket = context.socket(zmq.SUB)
data_socket.connect(f"tcp://127.0.0.1:{ZMQ_DATA_PORT}")
data_socket.setsockopt_string(zmq.SUBSCRIBE, "")

poller = zmq.Poller()
poller.register(detect_socket, zmq.POLLIN)
poller.register(data_socket, zmq.POLLIN)

# === Capture Logic ===
print("Monitoring for two-tone detection and data collection...")
detected = False
data_buffer = []
sample_count = 0

try:
    while sample_count < MAX_SAMPLES:
        socks = dict(poller.poll(timeout=100))

        if detect_socket in socks and socks[detect_socket] == zmq.POLLIN:
            signal = detect_socket.recv_string()
            if signal == "1" and not detected:
                detection_time = time.time()
                detected = True
                print(f"Tone detected. Starting sample capture.")

        if detected and data_socket in socks and socks[data_socket] == zmq.POLLIN:
            msg = data_socket.recv()
            samples = np.frombuffer(msg, dtype=np.complex64)
            remaining = MAX_SAMPLES - sample_count

            if len(samples) > remaining:
                samples = samples[:remaining]

            data_buffer.extend(samples)
            sample_count += len(samples)

    # === Save Samples ===
    filename = f"captured_{int(time.time())}.txt"
    with open(filename, "w") as f:
        for s in data_buffer:
            f.write(f"{s.real:.6f} {s.imag:.6f}\n")

    print(f"Captured {len(data_buffer)} samples. Saved to {filename}")

    # === Cleanup ===
    detect_socket.close()
    data_socket.close()
    context.term()
    first_process.terminate()
    first_process.wait()
    print("Flowgraph terminated.")

except KeyboardInterrupt:
    first_process.terminate()
    first_process.wait()
    print("Interrupted and terminated.")
