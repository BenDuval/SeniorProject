import subprocess
import time
import zmq
import os

# === Node Configuration ===
nodes = ["Node1", "Node2", "Node3"]

# Expected output files from communication cycles
required_files = {
    "Node1Node2", "Node1Node3",
    "Node2Node1", "Node2Node3",
    "Node3Node1", "Node3Node2"
}

ZMQ_ACK_PORT = 4010  # Must match custom python block setup in BPSK_TX.grc

def write_command_file(destination: str, command: str, source: str):
    """Generate the 3-line command.txt file"""
    with open("command.txt", "w") as f:
        f.write(f"{destination}\n{command}\n{source}")

def wait_for_ack_zmq():
    """Wait for tone detection via ZMQ port (indicating ACK)"""
    ctx = zmq.Context()
    socket = ctx.socket(zmq.SUB)
    socket.connect(f"tcp://localhost:{ZMQ_ACK_PORT}")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    print(f"🟡 Waiting for ACK (ZMQ msg '1') on port {ZMQ_ACK_PORT}...")
    while True:
        try:
            msg = socket.recv_string(flags=zmq.NOBLOCK)
            print(f"[ZMQ] Received: {msg}")
            if msg.strip() == "1":
                print("✅ ACK Detected.")
                break
        except zmq.Again:
            time.sleep(0.1)

def wait_until_all_data_files_exist(expected_set):
    """Block until all 6 expected directional data files are present"""
    print("🟡 Waiting for all 6 data files...")
    existing = set()
    while existing != expected_set:
        for name in expected_set - existing:
            if os.path.exists(f"{name}.txt"):
                print(f"✔ File detected: {name}.txt")
                existing.add(name)
        time.sleep(0.5)

# === Main Ground Station Loop ===
for master in nodes:
    print(f"\n==============================")
    print(f"🎯 Assigning Master: {master}")
    print(f"==============================")

    write_command_file(master, "Master", "NodeG")

    try:
        tx_proc = subprocess.Popen(["python3", "BPSK_TX.py"])
        wait_for_ack_zmq()
        tx_proc.terminate()
        tx_proc.wait()
        print("🛑 TX terminated. Starting RX...")

        rx_proc = subprocess.Popen(["python3", "BPSK_RX.py"])
        wait_until_all_data_files_exist(required_files)
        rx_proc.terminate()
        rx_proc.wait()
        print("✅ RX complete. Moving to next node.\n")

    except Exception as e:
        print(f"❌ Error during subprocess execution: {e}")
        if 'tx_proc' in locals():
            tx_proc.terminate()
        if 'rx_proc' in locals():
            rx_proc.terminate()
        break

print("🎉 All Master cycles completed successfully.")
