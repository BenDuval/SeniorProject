import subprocess
import time
import zmq
import os

# === Node Configuration ===
nodes = ["Node1", "Node2", "Node3"]

ZMQ_ACK_PORT = 4010  # Must match your BPSK_TX.grc setup


def write_command_file(destination: str, command: str, source: str):
    with open("command.txt", "w") as f:
        f.write(f"{destination}\n{command}\n{source}")


def wait_for_ack_zmq():
    ctx = zmq.Context()
    socket = ctx.socket(zmq.SUB)
    socket.connect(f"tcp://localhost:{ZMQ_ACK_PORT}")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")

    print(f"🟡 Waiting for ACK (ZMQ msg '1') on port {ZMQ_ACK_PORT}...")
    while True:
        try:
            msg = socket.recv_string(flags=zmq.NOBLOCK)
            if msg.strip() == "1":
                print("✅ ACK Detected.")
                break
        except zmq.Again:
            time.sleep(0.1)


def wait_for_2_eof_markers(file_path="out.txt"):
    print(f"⏳ Waiting for 2 EOF_MARKERs in {file_path}...")
    while True:
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                eof_count = content.count(b"EOF_MARKER")
                print(f"🔎 Current EOF_MARKER count: {eof_count}")
                if eof_count >= 2:
                    print("✅ 2 EOF_MARKERs detected.")
                    break
        except FileNotFoundError:
            pass
        time.sleep(0.5)


def extract_valid_transmission(input_file: str, output_file: str, pad_char: str = 'A', min_pad_length: int = 10):
    """
    Extracts the middle (valid) transmission from a file with three padded transmissions.

    Args:
        input_file (str): Path to the input file containing three padded transmissions.
        output_file (str): Path to the output file where the valid middle transmission will be saved.
        pad_char (str): The character used for padding. Default is 'A'.
        min_pad_length (int): Minimum number of padding characters to identify split points. Default is 10.
    """
    with open(input_file, 'r') as f:
        content = f.read()

    segments = content.split(pad_char * min_pad_length)
    cleaned_segments = [s.strip() for s in segments if s.strip()]

    if len(cleaned_segments) < 3:
        raise ValueError("Expected at least three transmissions (padded start, middle, end).")

    middle_transmission = cleaned_segments[1]

    with open(output_file, 'w') as f:
        f.write(middle_transmission)


def run_bpsk_rx_until_2_eof(output_filename):
    rx_proc = subprocess.Popen(["python3", "BPSK_RX.py"])
    wait_for_2_eof_markers()
    rx_proc.terminate()
    rx_proc.wait()
    print("🛑 BPSK_RX terminated after detecting 2 EOF_MARKERs.")
    extract_valid_transmission("out.txt", output_filename)
    print(f"📁 Extracted middle transmission saved to {output_filename}")


def send_ack():
    subprocess.run(["python3", "ack_tx.py"])
    print("📡 Sent ACK back to Master.")


def main():
    # === Main Ground Station Loop ===
    for master in nodes:
        print(f"\n==============================")
        print(f"🎯 Assigning Master: {master}")
        print(f"==============================")

        # Step 1: Write Master command
        write_command_file(master, "Master", "NodeG")

        try:
            # Step 2: Transmit command to Master
            tx_proc = subprocess.Popen(["python3", "BPSK_TX.py"])
            wait_for_ack_zmq()
            tx_proc.terminate()
            tx_proc.wait()
            print("🛑 TX terminated after ACK.")

            # Step 3: Pause briefly before RX
            time.sleep(3)

            # Step 4: RX for first Slave
            slave_targets = [node for node in nodes if node != master]
            slave1 = slave_targets[0]
            run_bpsk_rx_until_2_eof(f"{master}{slave1}.txt")

            # Step 5: RX for second Slave
            time.sleep(1)  # Small pause before second capture
            slave2 = slave_targets[1]
            run_bpsk_rx_until_2_eof(f"{master}{slave2}.txt")

            # Step 6: Send ACK back to Master
            send_ack()

        except Exception as e:
            print(f"❌ Error during subprocess execution: {e}")
            if 'tx_proc' in locals():
                tx_proc.terminate()
            break

    print("🎉 All Master cycles completed successfully.")


if __name__ == "__main__":
    main()
