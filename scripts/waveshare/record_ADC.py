#!/usr/bin/python
# -*- coding:utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

import time
import ADS1263
import RPi.GPIO as GPIO
import csv, sys
from datetime import datetime
REF = 5.08          #REFERENCE VOLTAGE
DEBUG_ADC = True
TEST_ADC1_CSV = True

channelList = list(range(10))
header = ['ts'] + [f'IN{channel}' for channel in channelList]
buffer_size = 3*150  #num of readings to buffer before writing to file
nfft=64
fs=66
noverlap=63

plt.ion()
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=False)
colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'orange', 'purple', 'brown'] #channel colors

lines = [ax1.plot([], [], color=color, label=f'IN{channel}')[0] for channel, color in zip(channelList, colors)]
ax1.set_xlim(0, buffer_size)
ax1.set_ylim(-0.01, 0.01)
ax1.set_xlabel('Sample Index')
ax1.set_ylabel('Voltage (V)')
ax1.set_title('Real-Time ADC Data')
ax1.legend(loc='upper right')

Pxx, freqs, bins, im = ax2.specgram([], NFFT=nfft, Fs=fs, noverlap=noverlap, cmap='viridis')
ax2.set_ylabel('Frequency (Hz)')
ax2.set_xlabel('Time (s)')
ax2.set_title('Spectrogram of Diff')


def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

def update_plot(buffer, diff):
    buffer_array = np.array(buffer)
    for i, line in enumerate(lines):
        if i < buffer_array.shape[1] - 1:
            line.set_xdata(np.arange(len(buffer_array)))
            line.set_ydata(buffer_array[:, i + 1])
    ax1.relim()
    ax1.autoscale_view(True, True, True)

    ax2.cla()

    ax2.specgram(diff, NFFT=nfft, Fs=fs, noverlap=noverlap, cmap='viridis')
    ax2.set_ylabel('Frequency (Hz)')
    ax2.set_xlabel('Time (s)')
    ax2.set_title('Spectrogram of Diff')

    fig.canvas.draw()
    fig.canvas.flush_events()

def preprocess_data(data):
    mean_diff = np.mean(np.diff(data[:,0]))
    std_dev = np.std(np.diff(data[:,0]))
    sample_rate = 1000/mean_diff 
    print("Sample rate [Hz]: ", sample_rate)
    print("Mean difference [ms]: ", mean_diff)
    print("Standard deviation [ms]: ", std_dev)
    
    #remove column 0 and 4, 6
    data = np.delete(data, 0, 1)
    data = np.delete(data, 3, 1) #after removing column 0, column 4 becomes 3
    data = np.delete(data, 4, 1) #after removing column 0, column 6 becomes 4
    return data

try:
    ADC = ADS1263.ADS1263()
    
    if (ADC.ADS1263_init_ADC1('ADS1263_4800SPS') == -1):
        exit()
    ADC.ADS1263_SetMode(0)

    buffer = []

    with open('/dev/shm/adc_values_%s.csv'%datetime.now().strftime('%Y-%m-%d-%H-%M-%S'), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header) 

        start_time = time.time() * 1000  #start time in milliseconds
        while True:
            current_time = time.time() * 1000  #current time in milliseconds
            elapsed_time = int(current_time - start_time)
            ADC_Value = ADC.ADS1263_GetAll(channelList)
            for i in channelList: #this doesnt make things slower
                if(ADC_Value[i]>>23 ==1):
                    ADC_Value[i] = (REF*2 - ADC_Value[i] * REF / 0x80000000)
                else:
                    ADC_Value[i] = (ADC_Value[i] * REF / 0x7fffffff)     #32bit
            
            
            buffer.append([elapsed_time] + ADC_Value)  
            
            if len(buffer) >= buffer_size: 

                if DEBUG_ADC:
                    data = np.array(buffer)
                    data = preprocess_data(data)
                    rms_i = np.std(data, axis=0)
                    mean_i = np.mean(data, axis=0)
                    print("Mean RMS: %s" %np.mean(rms_i))
                    print("Mean Voltage: %s"%mean_i)
                    
                    data -= np.mean(data, axis=1).reshape(-1,1)
                    data = np.abs(data)
                    
                    data -= np.mean(data, axis=0)
                    
                    diff = np.zeros_like(data[:,0])
                    for i in range(7):
                        for j in range(i + 1, 7):
                            diff += np.abs(data[:, i] - data[:, j])
                    
                    new_diff = []
                    prev=0
                    
                    #outlier filtering 
                    for i in range(len(diff)):
                        median = np.median(diff[i:i+5])
                        
                        if diff[i]/median > 1:
                            new_diff.append(prev)
                        else:
                            new_diff.append(diff[i])
                        
                        prev = new_diff[-1]
                        
                        
                    update_plot(data, new_diff)

                    buffer = [] 
                else:
                    writer.writerows(buffer) 
                    buffer = [] 
                    break
            

    ADC.ADS1263_Exit()

except IOError as e:
    print(e)
   
except KeyboardInterrupt:
    ADC.ADS1263_Exit()
    exit()
   
