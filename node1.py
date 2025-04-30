import subprocess
import zmq
import os
import difflib
import time
from set_command import set_command
from extract_command import extract_command
# from extract_valid_command_from_file_stream import extract_valid_command_from_file_stream


class AirNode:
    def __init__(self, identifier):
        self.identifier = identifier
        self.state = 'idle'
        self.bpsk_rx_process = None

    def return_to_idle(self):
        self.state = 'idle'
        print("State changed to: idle")

        # Step 1: Clear command.txt or reset it
        #try:
           # with open("command.txt", "w") as f:
            #    f.write("")
           # print("command.txt cleared.")
        #except Exception as e:
            #print(f"Error clearing command.txt: {e}")

        # Step 2: Start RX  
        if self.bpsk_rx_process is None or self.bpsk_rx_process.poll() is not None:
            self.bpsk_rx_process = subprocess.Popen(["python3", "BPSK_RX_GROUND.py"])
        print("started bpsk rx")
        time.sleep(4)

        input_file_path = 'out.txt'
        output_file_path = 'command.txt'

        # Step 3: Idle polling loop
        while self.state == 'idle':
            extract_command(input_file_path, output_file_path)
            command, identifier, source = self.read_command_from_file()

            if command and identifier and source and identifier == self.identifier:
                print("Command found in idle. Exiting idle and processing.")
                self.process_command(command, identifier, source)
                break  # Exit idle loop, move into Master/Slave/etc
            time.sleep(1)  # Poll every second

    def set_state(self, new_state):
        # Terminate RX if running before switching roles
        if self.bpsk_rx_process and self.bpsk_rx_process.poll() is None:
            print("Terminating BPSK RX before switching state.")
            self.bpsk_rx_process.terminate()
            self.bpsk_rx_process = None
         
            time.sleep(5)
            
        self.state = new_state
        print(f"State changed to: {self.state}")
        if new_state == 'master':
            self.become_master()
        elif new_state == 'slave':
            self.become_slave()

    def become_master(self):
        """Handles Master node setup and starts transmission."""
        ack_process = subprocess.Popen(["python3", "ack_tx.py"])
        time.sleep(3)
        ack_process.terminate()
        air_nodes = ["Node1", "Node2", "Node3"]  # All known nodes
        for node in air_nodes:
            if node == self.identifier:
                continue  # Skip itself
            set_command(node, "Slave", self.identifier)
            print(f"Generated Slave command for {node} from {self.identifier}")
            tx_process = subprocess.Popen(["python3", "BPSK_TX.py"])
            print("BPSK TX started. Listening for ACK...")
            time.sleep(5)

            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect("tcp://localhost:4010")
            socket.setsockopt_string(zmq.SUBSCRIBE, "")
            socket.RCVTIMEO = 100  # 100 ms timeout

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
            print("BPSK TX terminated.")
            print("master mode up next")
            master_process = subprocess.run(["python3", "master_mode.py"])
            time.sleep(2)

            print("Restarting BPSK_RX for EOF monitoring.")
            self.bpsk_rx_process = subprocess.Popen(["python3", "BPSK_RX.py"])
            time.sleep(2)

            print("Monitoring out.txt for EOF_MARKER...")
            eof_count = 0
            while eof_count < 2:
                try:
                    with open("out.txt", "rb") as f:
                        text = f.read()
                        eof_count = text.count(b"EOF_MARKER")
                        print(f"Current EOF_MARKER count : {eof_count}")
                except FileNotFoundError:
                    eof_count = 0
                time.sleep(1)

            print("2 EOF_MARKERs found. Terminating BPSK_RX.")
            if self.bpsk_rx_process and self.bpsk_rx_process.poll() is None:
                self.bpsk_rx_process.terminate()
                self.bpsk_rx_process = None

            time.sleep(2)
            ack_process = subprocess.Popen(["python3", "ack_tx.py"])
            time.sleep(5)
            ack_process.terminate()

            print("Extracting valid data from out.txt...")
            extract_valid_transmission(
                input_file="out.txt",
                output_file=f"{self.identifier}{node}.txt",
                master_file="two_tone_master_data.txt"
            )
            print(f"Saved cleaned transmission to {self.identifier}{node}.txt")
            time.sleep(3)

            print(f"Transmitting {self.identifier}{node}.txt to the ground...")
            tx_data_process = subprocess.Popen(["python3", "BPSK_TX_DATA_GROUND.py"])
            print("BPSK_TX_DATA_GROUND flowgraph started. Waiting for ACK...")

            context = zmq.Context()
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
        """Handles Slave node setup."""
        time.sleep(.3)
        # Step 1: Send ack to master 
        print(f"{self.identifier} is now a Slave. Sending ACK...")
        ack_process = subprocess.Popen(["python3", "ack_tx.py"])
        time.sleep(5) # wait 20 seconds
        ack_process.terminate()
        time.sleep(.3)
        # Step 2: Start slavemode.py
        slave_process = subprocess.Popen(["python3", "slavemode.py"])  
        slave_process.wait()  # Properly terminate the slave_process
        time.sleep(5)
        
        # Step 3: Transmit using BPSK_TX
        tx_process = subprocess.Popen(["python3", "BPSK_TX_DATA.py"])
        print("Slave data transmitted to master. Listening for ACK")
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect("tcp://localhost:4010")
        socket.setsockopt_string(zmq.SUBSCRIBE, "")
        socket.RCVTIMEO = 100  # 100 ms timeout
        ack_received = False
        last_print = time.time()
        while not ack_received:
            try:
                msg = socket.recv_string(flags=zmq.NOBLOCK)
                if msg.strip() == "1":
                    print("Ack received")
                    ack_received = True
            except zmq.Again:
                time.sleep(0.01)  # now this actually executes
                if time.time() - last_print > 1:
                    print("No ACK yet...")
                    last_print = time.time()
            
        tx_process.terminate()
        self.return_to_idle()

    def fuzzy_match(self, word, valid_set, cutoff=0.7):
        """Returns closest match in valid_set if above cutoff score."""
        match = difflib.get_close_matches(word, valid_set, n=1, cutoff=cutoff)
        return match[0] if match else None

    def read_command_from_file(self, path="command.txt"):
        """Reads the command file and extracts destination, command, and source."""
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
        """Processes commands and includes the source information."""
        if identifier == self.identifier:
            if command == "Master":
                self.set_state('master')
            elif command == "Slave":
                self.set_state('slave')
            else:
                self.set_state('idle')
        else:
            print(f"Command for another node: {identifier}. Ignored.")

# === Corrected Extract Function ===

def extract_valid_transmission(input_file: str, output_file: str, master_file: str, pad_char: str = 'A', min_pad_length: int = 10):
    """
    Extracts the middle transmission from a padded file, removes EOF_MARKERs from it,
    appends the master file contents, and then appends a final EOF_MARKER at the end.
    """
    with open(input_file, 'r') as f:
        content = f.read()

    segments = content.split(pad_char * min_pad_length)
    cleaned_segments = [s.strip() for s in segments if s.strip()]

    if len(cleaned_segments) < 3:
        raise ValueError("Expected at least three transmissions (padded start, middle, end).")

    middle_transmission = cleaned_segments[1].replace("EOF_MARKER", "").strip()

    with open(master_file, 'r') as f_master_read:
        master_content = f_master_read.read()

    with open(output_file, 'w') as f_out:
        f_out.write(middle_transmission)
        f_out.write("\n")
        f_out.write(master_content)
        f_out.write("\nEOF_MARKER\n")

# === Start Node ===

if __name__ == "__main__":
    node = AirNode("Node1")
    node.return_to_idle()
    

 
