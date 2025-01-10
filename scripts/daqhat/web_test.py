import numpy as np
from scipy.signal import butter, filtfilt
from scipy import signal
import threading
import time
import queue
import sys
from daqhats import hat_list, HatIDs, mcc128, AnalogInputRange
from datetime import datetime
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import layout
from bokeh.io import show

fs = 4000
nfft = 100
buffer_size = 20000

board_list = hat_list(filter_by_id = HatIDs.ANY)
if not board_list:
    print("No boards found")
    sys.exit()
    
for entry in board_list:
    if entry.id == HatIDs.MCC_128:
        print("Board {}: MCC 128".format(entry.address))
        board = mcc128(entry.address)
        board.a_in_range_write(AnalogInputRange.BIP_5V)
        board.a_in_scan_start(channel_mask=0xff, samples_per_channel=fs, sample_rate_per_channel=fs, options=16)
        time.sleep(1) 
        
real_time_source = ColumnDataSource(data=dict(x=[],y2=[], y=[]))
spec_source = ColumnDataSource(data=dict(x=[], y=[]))
diff_source = ColumnDataSource(data=dict(x=[], y=[]))

real_time_plot = figure(width=1400,title="Real-Time ADC Data", x_axis_label='Sample Index', y_axis_label='Voltage (V)')
real_time_plot.line('x', 'y', source=real_time_source, line_width=1, color='blue')
real_time_plot.line('x', 'y2', source=real_time_source, line_width=1, color='green')

diff_plot = figure(width=1400,title="diff", x_axis_label='f', y_axis_label='au')
diff_plot.line('x', 'y', source=diff_source, line_width=1, color='red')

spec_plot = figure(width=1400,title="psd", x_axis_label='f', y_axis_label='db')
spec_plot.line('x', 'y', source=spec_source, line_width=1, color='green')

def preprocess_data(data):
    data = data.reshape(-1, 8)
    # remove 8 channel mean from each channel
    data = data - np.mean(data, axis=1).reshape(-1, 1)
    return data

#LPF
def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

#plot updater
x_offset = 0
psd=[]
def update_plot():
    global x_offset
    global psd
    buffer = board.a_in_scan_read_numpy(samples_per_channel=-1, timeout=-1).data
    data = np.array(buffer)
    data = preprocess_data(data)
    
    diff = np.zeros_like(data[:, 0])
    for i in range(7):
        data[:, i] = data[:, i] - np.mean(data[:, i])
        
        for j in range(i + 1, 7):
            diff += np.abs(data[:, i] - data[:, j])
            
    diff = diff / (7*7-7)
    
    
    # outlier filtering
    new_diff = []
    prev = 0
    for i in range(len(diff)):
        median = np.median(diff[max(0, i - 5):i + 5])
        if diff[i] / median > 1:
            new_diff.append(prev)
        else:
            new_diff.append(diff[i])
        prev = new_diff[-1]

    #update plot
    x_values = np.arange(len(new_diff)) + x_offset
    x_offset += len(new_diff)
    real_time_source.stream({'x': x_values, 'y': data[:,0],'y2': data[:,1]}, rollover=buffer_size)
    
    
    diff_source.stream({'x': x_values, 'y': diff}, rollover=buffer_size)

    #psd
    f, psd_now = signal.welch(data[:,0], fs, nperseg=nfft)
    psd_now_db = 10 * np.log10(psd_now)

    
    #rollover psd
    if len(psd) > 2:
        psd = psd[1:]
        
    psd.append(psd_now_db)
    psd_avg = np.mean(np.array(psd), axis=0)
    spec_source.stream({'x': f, 'y': psd_avg}, rollover=f.size)

#plot every 200 milliseconds
curdoc().add_periodic_callback(update_plot, 500)
curdoc().add_root(layout([real_time_plot, diff_plot, spec_plot]))
