import numpy as np
from gnuradio import gr
import pmt

class preamble_inserter(gr.sync_block):
    def __init__(self, preamble=0xAAAAAAAAAAAAAAAA, pkt_len=64):
        gr.sync_block.__init__(
            self,
            name='64-bit Preamble Inserter',
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )
        self.preamble = preamble.to_bytes(8, byteorder='big')
        self.pkt_len = pkt_len
        self.preamble_sent = False
        self.tag_position = 0

    def work(self, input_items, output_items):
        if not self.preamble_sent:
            # Insert the preamble
            output_items[0][:8] = np.frombuffer(self.preamble, dtype=np.uint8)
            self.preamble_sent = True
            self.tag_position += 8
            return 8
        
        # Pass the input items after sending the preamble
        output_len = len(input_items[0])
        output_items[0][:output_len] = input_items[0]
        
        # Attach a packet length tag
        tag_key = pmt.intern("packet_len")
        tag_value = pmt.from_long(self.pkt_len)
        self.add_item_tag(0, self.tag_position, tag_key, tag_value)
        self.tag_position += output_len
        
        return output_len
