import numpy as np
import zmq
from gnuradio import gr
import pmt  # Import PMT for message passing

class blk(gr.sync_block):  
    """Embedded Python Block for detecting two specific tones, with ZMQ and PMT output"""

    def __init__(self, threshold=0.1, zmq_port=7040):  
        gr.sync_block.__init__(
            self,
            name='detect_two_tone',  
            in_sig=[np.float32, np.float32],  # Two input signals (RMS values)
            out_sig=[np.float32]  # Single output (binary detection result)
        )
        self.threshold = threshold
        self.last_sent = None  # Track last sent value to avoid redundant messages

        # Set up ZMQ PUB socket
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{zmq_port}")

        # Register PMT message output
        self.message_port_register_out(pmt.intern("detected_flag"))

    def work(self, input_items, output_items):
        """Check if both tones are present and send ZMQ + PMT messages if detected"""
        rms_430 = input_items[0]  # RMS of first frequency
        rms_435 = input_items[1]  # RMS of second frequency
        out = output_items[0]

        # Check if the RMS values exceed the threshold
        if np.mean(rms_430) > self.threshold and np.mean(rms_435) > self.threshold:
            tone_value = 1  # Detected the correct combination
        else:
            tone_value = 0  # No detection

        # Send ZMQ message **only if the value has changed** to avoid unnecessary messages
        if tone_value != self.last_sent:
            self.socket.send_string(str(tone_value))  # Send updated detection status over ZMQ
            self.last_sent = tone_value  # Update last sent value

        # Send PMT message
        self.message_port_pub(pmt.intern("detected_flag"), pmt.from_long(tone_value))

        # Pass the value to the GNU Radio output
        out[:] = float(tone_value)

        return len(output_items[0])
