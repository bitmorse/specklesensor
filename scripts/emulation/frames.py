import numpy as np
import cv2
import csv
import time

filename = '10Hz_IRbandpass850_laser1point_30fps_3ondisc.raw'
w = 640  #(6.287mm)
h = 480  #(4.712mm)
w_mm = 6.287
h_mm = 4.712

pd_wh_mm = 1.229
pd_wh_px = int((w / w_mm) * pd_wh_mm)

pd_margin_mm = 0.771
pd_margin_px = int((w / w_mm) * pd_margin_mm)

width = (w + 31) // 32 * 32
height = (h + 15) // 16 * 16
frame_size = width * height + width * height // 4 + width * height // 4  #size of each frame in bytes

def read_frame(f):
    #Y, U, and V color component extraction
    Y = np.frombuffer(f.read(width * height), dtype=np.uint8).reshape((height, width))
    U = np.frombuffer(f.read(width * height // 4), dtype=np.uint8).reshape((height // 2, width // 2))
    V = np.frombuffer(f.read(width * height // 4), dtype=np.uint8).reshape((height // 2, width // 2))
    #just need intensity
    return Y

def process_video(filename):
    try:
        with open('virtual_photodiodes_%s.csv' % filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Frame', 'TopLeft_Avg', 'TopCenter_Avg', 'TopRight_Avg'])

            frame_count = 0
            with open(filename, 'rb') as f:
                while True:
                    #single frame of data
                    frame = read_frame(f)
                    if frame.size == 0: #end of file
                        break

                    #region def for virtual photodiodes
                    topleft = frame[pd_margin_px:pd_wh_px + pd_margin_px, 0:pd_wh_px]
                    topcenter = frame[pd_margin_px:pd_wh_px + pd_margin_px, pd_wh_px + pd_margin_px:pd_margin_px + 2 * pd_wh_px]
                    topright = frame[pd_margin_px:pd_wh_px + pd_margin_px, 2 * pd_wh_px + 2 * pd_margin_px:3 * pd_wh_px + 2 * pd_margin_px]

                    topleft_avg = np.mean(topleft)
                    topcenter_avg = np.mean(topcenter)
                    topright_avg = np.mean(topright)

                    csvwriter.writerow([
                        frame_count,
                        topleft_avg,
                        topcenter_avg,
                        topright_avg
                    ])

                    frame_count += 1

                    #DISPLAY FRAME
                    cv2.imshow('Frame', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'): 
                        break
    except Exception as e:
        print(e)
    finally:
        cv2.destroyAllWindows()

process_video(filename)
