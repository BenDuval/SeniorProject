import time
import subprocess
import zmq
#from run_bpsk_tx import run_bpsk_tx
from set_command import set_command
from extract_command import extract_command
#from run_bpsk_rx import run_bpsk_rx
#from file_utils import replace_text_in_file


class AirNode:
    def __init__(self, identifier):
        self.identifier = identifier
        self.state = 'idle'
        self.bpsk_rx_process = None


    def return_to_idle(self):
        self.state = 'idle'
        #print("State changed to: idle")
        
        #run_bpsk_rx("/home/ubuntu/Documents/Senior Project/Communication Protocol/new_bpsk_Rx.py")
        # Start BPSK RX as a subprocess and store handle
        if self.bpsk_rx_process is None or self.bpsk_rx_process.poll() is not None:
            self.bpsk_rx_process = subprocess.Popen(["python3", "/home/ubuntu/Documents/Senior Project/Communication Protocol/new_bpsk_Rx.py"])
        #print("started bpsk rx")
        # Poll for decoded frame in out.txt
        while True:
            got_message = extract_command(
                "/home/ubuntu/Documents/Senior Project/Communication Protocol/out.txt",
                "command.txt"
            )
            if got_message:
                command, identifier, source = self.read_command_from_file("command.txt")
                if command and identifier and source:
                    self.process_command(command, identifier, source)
                    break  # Exit idle once a valid command is received
            time.sleep(1)
        # Read the result
        command, identifier, source = self.read_command_from_file("command.txt")
        #if command and identifier and source:
        #    self.process_command(command, identifier, source)
        


    def set_state(self, new_state):
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

            #run_bpsk_tx("/home/ubuntu/Documents/Senior Project/Communication Protocol/new_bpsk_Tx.py")

            tx_process = subprocess.Popen(["python3", "new_bpsk_Tx.py"])
            print("BPSK TX started. Listening for ACK...")

            # Step 3: Poll ZMQ for ACK (inline, no def)
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect("tcp://localhost:4010")
            socket.setsockopt_string(zmq.SUBSCRIBE, "")
            socket.RCVTIMEO = 100000  # 100 second timeout

            ack_received = False
            for _ in range(10):  # Retry for up to 10 seconds
                try:
                    msg = socket.recv_string()
                    print(f"ACK received: {msg}")
                    ack_received = True
                    break
                except zmq.Again:
                    print("No ACK yet...")

            # Step 4: Stop flowgraph
            tx_process.terminate()
            print("BPSK TX terminated.")
            time.sleep(10000)

            #time.sleep(4)  # Give each slave time to receive & act before moving to the next
        # Step 2: Launch master_mode to handle two-tone TX (430 MHz) and RX (440 MHz)
        #subprocess.run(["python3", "master_mode.py"])
        #process.wait()  # Waits for script to finish 
        # or use time.sleep(duration) if needed
        #process.terminate()

        # Step 3: Return to idle when complete
        #self.return_to_idle()



    def become_slave(self):
        """Handles Slave node setup."""
        if self.bpsk_rx_process and self.bpsk_rx_process.poll() is None:
            self.bpsk_rx_process.terminate()
        print(f"{self.identifier} is now a Slave. Sending ACK...")
        
        ack_process = subprocess.Popen(["python3", "ack_tx.py"])
        print("opened ack_tx")
        time.sleep(5)
        ack_process.terminate()

        process2 = subprocess.Popen(["python3", "slavemode.py"])  # Start slavemode.py
        time.sleep(5)
        #process2.terminate()  # Properly terminate the process
        process2.wait()
        print("slave mode done")
        time.sleep(500000)
        #self.return_to_idle()

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
            print("File not found. Ensure 'command.txt' is available.")
            return None, None, None
        except IndexError:
            print("File format error. Ensure the file contains three lines: Destination, Command, and Source.")
            return None, None, None

    def process_command(self, command, identifier, source):
        """Processes commands and includes the source information."""
        if identifier == self.identifier:

            if command == "Master":
                self.set_state('master')
                #set_command(self.identifier, "Master", source)  # Now stores source properly
            elif command == "Slave":
                self.set_state('slave')
                #set_command(self.identifier, "Slave", source)
            else:
                self.set_state('idle')
        else:
            print(f"Command for another node: {identifier}. Ignored.")


if __name__ == "__main__":
    node = AirNode("Node2")
    while True:
        #command, identifier, source = node.read_command_from_file()
        #if command and identifier and source:
        #    node.process_command(command, identifier, source)
        #time.sleep(5)  # Delay to limit the frequency of file reads
        node.return_to_idle()
