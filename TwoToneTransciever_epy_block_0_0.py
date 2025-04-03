import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):  
    """Custom Block to multiply complex signal source by a message-controlled value"""

    def __init__(self, default_value=1.0):  
        gr.sync_block.__init__(
            self,
            name='amplitude_control_complex',  
            in_sig=[np.complex64],  # Complex input
            out_sig=[np.complex64]  # Complex output
        )
        self.amplitude = default_value  # Default amplitude ON (1.0)
        self.amplitude_locked = False  # Track if amplitude has been turned off

        self.message_port_register_in(pmt.intern("in"))  # Register message input
        self.set_msg_handler(pmt.intern("in"), self.handle_msg)  # Set handler for incoming messages

    def handle_msg(self, msg):
        """Handle incoming messages to update amplitude"""
        if pmt.is_integer(msg) or pmt.is_real(msg):  # Ensure the message is numeric
            flag = pmt.to_long(msg)  # Convert PMT message to integer
            if flag == 1 and not self.amplitude_locked:
                self.amplitude = 0.0  # Turn OFF amplitude when dual tone detected
                self.amplitude_locked = True  # Lock the state to OFF

    def work(self, input_items, output_items):
        """Multiply the complex input signal by the amplitude"""
        signal = input_items[0]
        output_items[0][:] = self.amplitude * signal  # Apply amplitude to the complex signal

        return len(output_items[0])
