import subprocess
import time
import zmq

nodes = ["Node1", "Node2", "Node3"]
ZMQ_ACK_PORT = 4010

def write_command_file(destination: str, command: str, source: str):
    with open("command.txt", "w") as f:
        f.write(f"{destination}\n{command}\n{source}")
    print(f"📄 Command file written: {destination} ← {command} from {source}")

def wait_for_ack():
    print(f"🟡 Waiting for ACK on port {ZMQ_ACK_PORT}...")
    ctx = zmq.Context()
    socket = ctx.socket(zmq.SUB)
    socket.connect(f"tcp://localhost:{ZMQ_ACK_PORT}")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
    while True:
        try:
            msg = socket.recv_string(flags=zmq.NOBLOCK)
            if msg.strip() == "1":
                print("✅ ACK received.")
                break
        except zmq.Again:
            time.sleep(0.1)

def wait_for_eof_markers(file_path="out.txt"):
    print(f"⏳ Waiting for 2 EOF_MARKERs in {file_path}...")
    while True:
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                count = content.count(b"EOF_MARKER")
                print(f"🔍 EOF_MARKER count: {count}")
                if count >= 2:
                    print("✅ 2 EOF_MARKERs detected.")
                    break
        except FileNotFoundError:
            print("⚠️  out.txt not found yet...")
        time.sleep(0.5)

def extract_middle_segment(input_file: str, output_file: str, pad_char='A', pad_len=10):
    with open(input_file, 'rb') as f:
        content = f.read()

    decoded = content.decode('ascii', errors='ignore')
    parts = [s.strip() for s in decoded.split(pad_char * pad_len) if s.strip()]
    if len(parts) < 3:
        raise ValueError("Expected at least 3 padded sections in the file.")

    with open(output_file, 'w') as f:
        f.write(parts[1])
    print(f"📁 Extracted segment saved to {output_file}")

def send_ack():
    print("📡 Sending ACK to Master...")
    ack_proc = subprocess.Popen(["python3", "ack_tx.py"])
    time.sleep(3)
    ack_proc.terminate()
    ack_proc.wait()
    print("✅ ACK sent.")

def receive_slave_data(rx_script: str, master: str, slave: str):
    open("out.txt", "w").close()
    print("🧹 Cleared out.txt before recieving data.")
    
    print(f"🔻 Receiving from {master} → {slave}...")
    rx_proc = subprocess.Popen(["python3", rx_script])
    wait_for_eof_markers()
    rx_proc.terminate()
    rx_proc.wait()
    output_file = f"{master}{slave}.txt"
    extract_middle_segment("out.txt", output_file)
    send_ack()
    
    open("out.txt", "w").close()
    print("🧹 Cleared out.txt after saving data.")

def main():
    for master in nodes:
        print(f"\n==============================")
        print(f"🎯 Assigning Master: {master}")
        print(f"==============================")

        write_command_file(master, "Master", "NodeG")

        tx_script = f"BPSK_TX_{master}.py"
        print(f"🚀 Launching {tx_script}...")
        tx_proc = subprocess.Popen(["python3", tx_script])
        wait_for_ack()
        tx_proc.terminate()
        tx_proc.wait()
        print(f"🛑 TX {tx_script} terminated after ACK.")

        slave_targets = [n for n in nodes if n != master]
        for slave in slave_targets:
            time.sleep(35)
            receive_slave_data("BPSK_RX_DATA_GROUND.py", master, slave)

    print("\n🎉 All Master cycles completed successfully.")

if __name__ == "__main__":
    # Clear out.txt at startup
    open("out.txt", "w").close()
    print("🧹 Cleared out.txt at startup.")
    main()
