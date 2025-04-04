from gnuradio import gr
import numpy as np
import os

class repeat_packet_file_source(gr.sync_block):
    """
    A block that reads the contents of a file, wraps it with a hardcoded 50-byte ASCII header and footer, 
    and transmits the packet as a stream of bytes, repeated X times.
    """

    def __init__(self, file_path="/home/ubuntu/Documents/Senior Project/Communication Protocol/SeniorProject/command.txt", num_repeats=3):
        gr.sync_block.__init__(
            self,
            name="Repeat Packet File Source",  # Block name
            in_sig=None,                       # No input signal
            out_sig=[np.uint8],                # Output is a stream of bytes
        )

        # Parameters
        self.file_path = file_path
        self.num_repeats = num_repeats

        # Validate and read file
        if not os.path.isfile(self.file_path):
            raise ValueError(f"File not found: {self.file_path}")
        with open(self.file_path, "rb") as f:
            self.file_data = f.read()  # Read entire file into memory

        # Hardcoded ASCII header and footer
        self.header = ("A" * 256).encode("ascii")  # 50 bytes of ASCII 'a'
        self.footer = ("A" * 256).encode("ascii")  # 50 bytes of ASCII 'A'

        # Create the packet (header + file_data + footer)
        self.packet = self.header + self.file_data + self.footer

        # Repeat the packet X times
        self.buffer = self.packet * self.num_repeats

    def work(self, input_items, output_items):
        """
        Outputs the packetized data as a byte stream, repeated X times.
        """
        out = output_items[0]

        # If buffer is empty, stop processing
       # if not self.buffer:
          #  return -1

        # Determine how much data to output
        to_write = min(len(self.buffer), len(out))

        # Write data to the output buffer
        out[:to_write] = np.frombuffer(self.buffer[:to_write], dtype=np.uint8)

        # Remove the transmitted portion from the buffer
        self.buffer = self.buffer[to_write:]

        return to_write
