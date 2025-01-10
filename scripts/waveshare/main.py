import numpy as np
import time
import ADS1263
import RPi.GPIO as GPIO
import csv, sys
from datetime import datetime
REF = 5.08          #REFERENCE VOLTAGE
                    # external AVDD and AVSS(Default), or internal 2.5V
DEBUG_ADC = True
TEST_ADC1_CSV = True
# ADC1 test part
TEST_ADC1       = False
# ADC2 test part
TEST_ADC2       = False
# ADC1 rate test part, For faster speeds use the C program
TEST_ADC1_RATE   = False
# RTD test part 
TEST_RTD        = False     

def preprocess_data(data):
    #remove column 0 and 4, 6
    data = np.delete(data, 0, 1)
    data = np.delete(data, 3, 1) #after removing column 0, column 4 becomes 3
    data = np.delete(data, 4, 1) #after removing column 0, column 6 becomes 4
    return data

try:
    ADC = ADS1263.ADS1263()
    
    #the faster the rate, the worse the stability
    #and the need to choose a suitable digital filter(REG_MODE1)
    if (ADC.ADS1263_init_ADC1('ADS1263_38400SPS') == -1):
        exit()
    ADC.ADS1263_SetMode(0) #0 is singleChannel, 1 is diffChannel

    # ADC.ADS1263_DAC_Test(1, 1)      # Open IN6
    # ADC.ADS1263_DAC_Test(0, 1)      # Open IN7
    if TEST_ADC1_CSV:  # ADC1 Test
        channelList = list(range(10))  #channels 0 through 9
        header = ['ts'] + [f'IN{channel}' for channel in channelList]
        buffer_size = 1000  #num of readings to buffer before writing to file
        buffer = []

        with open('/dev/shm/adc_values_%s.csv'%datetime.now().strftime('%Y-%m-%d-%H-%M-%S'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)  #header row with all channels

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
                        
                        buffer = []
                    else:
                        writer.writerows(buffer)
                        buffer = []
                        break
                
    elif(TEST_ADC1):       #ADC1 Test
        channelList = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]  #channels must be less than 10
        while(1):
            ADC_Value = ADC.ADS1263_GetAll(channelList) 
            for i in channelList:
                if(ADC_Value[i]>>31 ==1):
                    print("ADC1 IN%d = -%lf" %(i, (REF*2 - ADC_Value[i] * REF / 0x80000000)))  
                else:
                    print("ADC1 IN%d = %lf" %(i, (ADC_Value[i] * REF / 0x7fffffff)))   # 32bit
            for i in channelList:
                print("\33[2A")
        
    elif(TEST_ADC2):
        if (ADC.ADS1263_init_ADC2('ADS1263_ADC2_400SPS') == -1):
            exit()
        while(1):
            ADC_Value = ADC.ADS1263_GetAll_ADC2()   # get ADC2 value
            for i in range(0, 10):
                if(ADC_Value[i]>>23 ==1):
                    print("ADC2 IN%d = -%lf"%(i, (REF*2 - ADC_Value[i] * REF / 0x800000)))
                else:
                    print("ADC2 IN%d = %lf"%(i, (ADC_Value[i] * REF / 0x7fffff)))     # 24bit
            print("\33[11A")

    elif(TEST_ADC1_RATE):    # rate test
        time_start = time.time()
        ADC_Value = []
        isSingleChannel = True
        if isSingleChannel:
            while(1):
                ADC_Value.append(ADC.ADS1263_GetChannalValue(0))
                if len(ADC_Value) == 5000:
                    time_end = time.time()
                    print(time_start, time_end)
                    print(time_end - time_start)
                    print('frequency = ', 5000 / (time_end - time_start))
                    break
        else:
            while(1):
                ADC_Value.append(ADC.ADS1263_GetChannalValue(0))
                if len(ADC_Value) == 5000:
                    time_end = time.time()
                    print(time_start, time_end)
                    print(time_end - time_start)
                    print('frequency = ', 5000 / (time_end - time_start))
                    break

    elif(TEST_RTD):     # RTD Test
        while(1):
            ADC_Value = ADC.ADS1263_RTD_Test()
            RES = ADC_Value / 2147483647.0 * 2.0 *2000.0       #2000.0 -- 2000R, 2.0 -- 2*i
            print("RES is %lf"%RES)
            TEMP = (RES/100.0 - 1.0) / 0.00385      #0.00385 -- pt100
            print("TEMP is %lf"%TEMP)
            print("\33[3A")
        
    ADC.ADS1263_Exit()

except IOError as e:
    print(e)
   
except KeyboardInterrupt:
    print("ctrl + c:")
    print("Program end")
    ADC.ADS1263_Exit()
    exit()
   
