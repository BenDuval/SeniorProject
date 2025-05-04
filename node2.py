import time
import subprocess
import zmq
import os
import difflib
from set_command import set_command
from extract_command import extract_command


class AirNode:
    def __init__(self, identifier):
        self.identifier = identifier
        self.state = 'idle'
        self.bpsk_rx_process = None
        self.last_source = None  # Cache source from command.txt

    def return_to_idle(self):
        self.state = 'idle'
        print("State changed to: idle")

        try:
            with open("command.txt", "w") as f:
                f.write("")
            print("command.txt cleared.")
        except Exception as e:
            print(f"Error clearing command.txt: {e}")

        if self.bpsk_rx_process is None or self.bpsk_rx_process.poll() is not None:
            self.bpsk_rx_process = subprocess.Popen(["python3", "BPSK_RX_Node2.py"])
        print("started bpsk rx")
        time.sleep(4)

        input_file_path = 'out.txt'
        output_file_path = 'command.txt'

        while self.state == 'idle':
            extract_command(input_file_path, output_file_path)
            command, identifier, source = self.read_command_from_file()

            if command and identifier and source and identifier == self.identifier:
                print("Command found in idle. Exiting idle and processing.")
                self.last_source = source
                self.process_command(command, identifier, source)
                break
            time.sleep(1)

    def set_state(self, new_state):
        if self.bpsk_rx_process and self.bpsk_rx_process.poll() is None:
            print("Terminating BPSK RX before switching state.")
            self.bpsk_rx_process.terminate()
            self.bpsk_rx_process = None
        self.state = new_state
        print(f"State changed to: {self.state}")
        if new_state == 'master':
            self.become_master()
        elif new_state == 'slave':
            self.become_slave()

    def become_master(self):
        subprocess.Popen(["python3", "ack_tx.py"])

        target_nodes = ["Node2", "Node3"]
        for node in target_nodes:
            set_command(node, "Slave", self.identifier)
            print(f"Generated Slave command for {node} from {self.identifier}")
            tx_script = f"BPSK_TX_{node}.py"
            tx_process = subprocess.Popen(["python3", tx_script])
            print(f"{tx_script} started. Listening for ACK...")
            time.sleep(5)

            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect("tcp://localhost:4010")
            socket.setsockopt_string(zmq.SUBSCRIBE, "")
            socket.RCVTIMEO = 100

            ack_received = False
            last_print = time.time()
            while not ack_received:
                try:
                    msg = socket.recv_string(flags=zmq.NOBLOCK)
                    if msg.strip() == "1":
                        print("Ack received")
                        ack_received = True
                except zmq.Again:
                    time.sleep(0.01)
                    if time.time() - last_print > 1:
                        print("No ACK yet...")
                        last_print = time.time()

            tx_process.terminate()
            print(f"{tx_script} terminated.")

            subprocess.run(["python3", "master_mode.py"])
            time.sleep(2)

            self.bpsk_rx_process = subprocess.Popen(["python3", "BPSK_RX_Node1.py"])
            time.sleep(2)

            print("Monitoring out.txt for EOF_MARKER...")
            eof_count = 0
            while eof_count < 2:
                try:
                    with open("out.txt", "rb") as f:
                        text = f.read()
                        eof_count = text.count(b"EOF_MARKER")
                        print(f"Current EOF_MARKER count: {eof_count}")
                except FileNotFoundError:
                    eof_count = 0
                time.sleep(1)

            if self.bpsk_rx_process and self.bpsk_rx_process.poll() is None:
                self.bpsk_rx_process.terminate()
                self.bpsk_rx_process = None

            subprocess.Popen(["python3", "ack_tx.py"]).wait()

            extract_valid_transmission(
                input_file="out.txt",
                output_file=f"{self.identifier}{node}.txt",
                master_file="two_tone_master_data.txt"
            )
            print(f"Saved cleaned transmission to {self.identifier}{node}.txt")
            time.sleep(3)

            tx_data_process = subprocess.Popen(["python3", "BPSK_TX_DATA_GROUND.py"])
            print("BPSK_TX_DATA_GROUND flowgraph started. Waiting for ACK...")

            ack_socket = context.socket(zmq.SUB)
            ack_socket.connect("tcp://localhost:4010")
            ack_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            ack_socket.RCVTIMEO = 100

            ack_received = False
            last_print = time.time()
            while not ack_received:
                try:
                    msg = ack_socket.recv_string(flags=zmq.NOBLOCK)
                    if msg.strip() == "1":
                        print("Ground ACK received!")
                        ack_received = True
                except zmq.Again:
                    time.sleep(0.01)
                    if time.time() - last_print > 1:
                        print("No ACK yet from ground...")
                        last_print = time.time()

            tx_data_process.terminate()
            print("BPSK_TX_DATA_GROUND flowgraph terminated.")

        print("Returning to idle state.")
        self.return_to_idle()

    def become_slave(self):
        ack_process = subprocess.Popen(["python3", "ack_tx.py"])
        print("Sending ack to Master")
        time.sleep(8)
        ack_process.terminate()
        ack_process.wait()
        print("Ack terminated.")

        slave_process = subprocess.run(["python3", "slavemode.py"])
        #slave_process.wait()
        time.sleep(5)

        source = self.last_source
        if source:
            tx_script = f"BPSK_TX_DATA_{source}.py"
            print(f"Transmitting back using TX flowgraph: {tx_script}")
            tx_process = subprocess.Popen(["python3", tx_script])
        else:
            print("Source not available. Cannot launch TX flowgraph.")
            self.return_to_idle()
            return

        print("Slave transmission complete. Listening for ACK from master...")
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:4010")
        socket.setsockopt_string(zmq.SUBSCRIBE, "")
        socket.RCVTIMEO = 100

        ack_received = False
        last_print = time.time()
        while not ack_received:
            try:
                msg = socket.recv_string(flags=zmq.NOBLOCK)
                if msg.strip() == "1":
                    print("ACK received from master.")
                    ack_received = True
            except zmq.Again:
                time.sleep(0.01)
                if time.time() - last_print > 1:
                    print("No ACK yet...")
                    last_print = time.time()

        tx_process.terminate()
        self.return_to_idle()

    def fuzzy_match(self, word, valid_set, cutoff=0.7):
        match = difflib.get_close_matches(word, valid_set, n=1, cutoff=cutoff)
        return match[0] if match else None

    def read_command_from_file(self, path="command.txt"):
        VALID_COMMANDS = {"Master", "Slave", "Idle"}
        try:
            with open(path, 'r') as file:
                lines = [line.strip() for line in file if line.strip()]
            if len(lines) < 3:
                return None, None, None
            identifier = lines[0]
            raw_command = lines[1]
            source = lines[2]
            command = self.fuzzy_match(raw_command, VALID_COMMANDS)
            if not command:
                return None, None, None
            return command, identifier, source
        except FileNotFoundError:
            return None, None, None

    def process_command(self, command, identifier, source):
        if identifier == self.identifier:
            if command == "Master":
                self.set_state('master')
            elif command == "Slave":
                self.set_state('slave')
            else:
                self.set_state('idle')
        else:
            print(f"Command for another node: {identifier}. Ignored.")


def extract_valid_transmission(input_file: str, output_file: str, master_file: str, pad_char: str = 'A', min_pad_length: int = 10):
    with open(input_file, 'r', errors='ignore') as f:
        content = f.read()
    segments = content.split(pad_char * min_pad_length)
    cleaned_segments = [s.strip() for s in segments if s.strip()]
    if len(cleaned_segments) < 3:
        raise ValueError("Expected at least three transmissions.")
    middle_transmission = cleaned_segments[1].replace("EOF_MARKER", "").strip()
    with open(master_file, 'r', errors='ignore') as f_master:
        master_content = f_master.read()
    with open(output_file, 'w') as f_out:
        f_out.write(middle_transmission + "\n" + master_content + "\nEOF_MARKER\n")


if __name__ == "__main__":
    node = AirNode("Node2")
    node.return_to_idle()
