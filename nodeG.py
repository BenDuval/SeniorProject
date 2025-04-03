import time
import subprocess
import zmq
from set_command import set_command
from extract_command import extract_command

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
         #   with open("command.txt", "w") as f:
          #      f.write("")
           # print("command.txt cleared.")
        #except Exception as e:
         #   print(f"Error clearing command.txt: {e}")        
        
        # Step 2: Start RX  
        if self.bpsk_rx_process is None or self.bpsk_rx_process.poll() is not None:
         self.bpsk_rx_process = subprocess.Popen(["python3", "/home/ubuntu/Documents/Senior Project/Communication Protocol/BPSK_RX.py"])
        print("started bpsk rx")
        time.sleep(4)
        # Step 3: Idle polling loop
        while self.state == 'idle':
            #extract_command()
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
        self.state = new_state
        print(f"State changed to: {self.state}")
        if new_state == 'master':
            self.become_master()
        elif new_state == 'slave':
            self.become_slave()
            
    def become_master(self):
        """Handles Master node setup and starts transmission."""
        air_nodes = ["Node1", "Node2", "Node3"]  # All known nodes
        for node in air_nodes:
            if node == self.identifier:
                continue  # Skip itself
            # Step 1: Set command and transmit it over BPSK
            set_command(node, "Slave", self.identifier)
            print(f"Generated Slave command for {node} from {self.identifier}")
            tx_process = subprocess.Popen(["python3", "BPSK_TX.py"])
            print("BPSK TX started. Listening for ACK...")
            time.sleep(5)
            # Step 2: Poll ZMQ for ACK (inline, no def)
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
            # Step 3: Stop flowgraph
            tx_process.terminate()
            print("BPSK TX terminated.")
            # Step 4: Launch master_mode to handle two-tone TX and RX
            print("master mode up next")
            master_process = subprocess.run(["python3", "master_mode.py"])
            time.sleep(.3)
            master_process.wait()  # Waits for script to finish 
            print("master mode finished")

            # Step 5: Transmit to ground


    def become_slave(self):
        """Handles Slave node setup."""
        time.sleep(.3)
        print(f"{self.identifier} is now a Slave. Sending ACK...")
        ack_process = subprocess.Popen(["python3", "ack_tx.py"])
        time.sleep(20)
        ack_process.terminate()
        slave_process = subprocess.Popen(["python3", "two_tone_slave.py"])  # Start two_tone_slave.py
        slave_process.wait()  # Properly terminate the slave_process
        self.return_to_idle()

    def read_command_from_file(self, path="command.txt"):
        """Reads the command file and extracts destination, command, and source."""
        try:
            with open(path, 'r') as file:
                lines = file.readlines()
                if len(lines) < 3:
                    raise IndexError  # Ensure all three lines exist
                identifier = lines[0].strip()  # Destination Node
                command = lines[1].strip()  # Command Type
                source = lines[2].strip()  # Source Node
                return command, identifier, source
        except FileNotFoundError:
            #print("File not found. Ensure 'command.txt' is available.")
            return None, None, None
        except IndexError:
            #print("File format error. Ensure the file contains three lines: Destination, Command, and Source.")
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


if __name__ == "__main__":
    node = AirNode("Node1")
    node.return_to_idle()  # Start in IDLE State

