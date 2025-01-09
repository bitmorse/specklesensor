# specklesensor
A photodiode array for laser speckle sensing and vibrometry.


## RPI Camera Bench Setup
![RPI Camera Bench Setup](videos/red_laser_rpi_cam/setup.png)

Side by side comparison of the speckle pattern captured by a Raspberry Pi camera with
one red laser

![1 Red Laser](videos/red_laser_rpi_cam/1_red_laser.gif)

and three red lasers.

![3 Red Lasers](videos/red_laser_rpi_cam/3_red_lasers.gif)

## Hardware
The PCBs used for the experiments are in the `hardware` folder. The PCBs are designed using KiCad, an open source schematics and layout editor. The PCBs were manufactured by JLCPCB and hand assembled using hot air reflow.

- `speckle_pcb_rev1`: The 3x3 photodiode array.
- `speckle_amp_pcb_rev1`: The amplifier PCB for 3x3 array.

Careful attention must be paid to cleaning the PCBs after soldering, as any residue flux can lead to leakage currents and noise in the measurements.