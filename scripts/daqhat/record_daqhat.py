import numpy as np
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange
import time
import csv
from datetime import datetime

fs = 4000  #SPS
record_duration = 10  #record in seconds
output_file = f"daqhat_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

#MCC DAQ HAT list
board_list = hat_list(filter_by_id=HatIDs.ANY)
if not board_list:
    print("No boards found")
    exit()

board = None
for entry in board_list:
    if entry.id == HatIDs.MCC_128:
        print(f"Board {entry.address}: MCC 128 found")
        board = mcc128(entry.address)
        break

if board is None:
    print("MCC 128 board not found")
    exit()

#config
board.a_in_range_write(AnalogInputRange.BIP_5V)
channels = 8 
channel_mask = sum([1 << i for i in range(channels)])#ENABLE ALL

with open(output_file, mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    header = [f"Channel_{i}" for i in range(channels)]
    writer.writerow(header)

    print(f"Recording data to {output_file} for {record_duration} seconds...")
    board.a_in_scan_start(channel_mask=channel_mask, samples_per_channel=fs, sample_rate_per_channel=fs, options=16)

    #start recording
    start_time = time.time()
    while time.time() - start_time < record_duration:
        result = board.a_in_scan_read_numpy(samples_per_channel=-1, timeout=5)
        if result.hardware_overrun:
            print("Hardware overrun occurred!")
        if result.buffer_overrun:
            print("Buffer overrun occurred!")
        
        if result.data is not None and len(result.data) > 0:
            data = result.data.reshape(-1, channels)
            writer.writerows(data)
    
    print("Recording completed.")

board.a_in_scan_stop()
board.a_in_scan_cleanup()
print("DAQ HAT stopped and cleaned up.")
