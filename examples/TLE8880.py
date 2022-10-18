#!/usr/bin/env python

# Set regulator voltage of alternator (controlled by TLE8880) and monitor temperature and battery voltage

from usblini import USBlini
import time


def frame_listener(frame):

    if frame.frameid == 0x15:

        data_indicator = frame.data[2] & 0b111

        if data_indicator == 2:
            voltage = 8 + frame.data[3] * 0.1
            print("Voltage", voltage)

        if data_indicator == 3:
            temperature = -36 + frame.data[3] * 4
            print("Temperature", temperature)



ulini = USBlini()
ulini.open()
ulini.set_baudrate(9600)

# send one frame to wakeup device
ulini.master_write(0x00, USBlini.CHECKSUM_MODE_NONE, [])
time.sleep(0.2)

# add listener and set master sequence
ulini.frame_listener_add(frame_listener)
ulini.master_set_sequence(1000, 200, [0x15])

# Voltage setpoint
setpoint = 14.8

while True:
   ulini.master_write(0x29, USBlini.CHECKSUM_MODE_LIN1, [int((setpoint - 10.6) / 0.025) >> 2, 0, 0, 2])
   time.sleep(5)
   ulini.master_write(0x29, USBlini.CHECKSUM_MODE_LIN1, [int((setpoint - 10.6) / 0.025) >> 2, 0, 0, 3])
   time.sleep(5)
   pass

ulini.close()

