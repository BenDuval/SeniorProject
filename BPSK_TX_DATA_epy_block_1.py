import numpy as np
import numpy as np
import zmq
from gnuradio import gr
import pmt

class blk(gr.sync_block):  
    """Detect single tone using RMS input; output via ZMQ, PMT, and GNU Radio stream"""

    def __init__(self, threshold=0.1, zmq_port=7040):  
        gr.sync_block.__init__(
            self,
            name='detect_single_tone',  
            in_sig=[np.float32],  # Only one RMS input now
            out_sig=[np.float32]  # Single output (binary detection result)
        )
        self.threshold = threshold
        self.last_sent = None

        # ZMQ PUB setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{zmq_port}")

        # PMT output port
        self.message_port_register_out(pmt.intern("detected_flag"))

    def work(self, input_items, output_items):
        """Check if tone is present and send detection status"""
        rms = input_items[0]
        out = output_items[0]

        tone_value = 1 if np.mean(rms) > self.threshold else 0

        if tone_value != self.last_sent:
            self.socket.send_string(str(tone_value))
            self.last_sent = tone_value

        self.message_port_pub(pmt.intern("detected_flag"), pmt.from_long(tone_value))
        out[:] = float(tone_value)

        return len(output_items[0])

