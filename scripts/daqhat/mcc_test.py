#!/usr/bin/env python
import sys
import numpy as np
from daqhats import hat_list, HatIDs, mcc128
import time
# get hat list of MCC daqhat boards
board_list = hat_list(filter_by_id = HatIDs.ANY)
if not board_list:
    print("No boards found")
    sys.exit()

# Read and display every channel
for entry in board_list:
    if entry.id == HatIDs.MCC_128:
        print("Board {}: MCC 128".format(entry.address))
        board = mcc128(entry.address)
        print(board.info())
        print(board.a_in_scan_start(channel_mask=0xff, samples_per_channel=100, sample_rate_per_channel=100, options=0))
        
        time.sleep(1) # wait for scan to complete
        print(board.a_in_scan_read_numpy(samples_per_channel=-1, timeout=-1).data)
        
        data = np.array([1, 2, 3, 1, 2, 3])
        print(data.reshape(-1, 3))
