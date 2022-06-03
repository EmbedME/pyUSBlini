#!/usr/bin/env python

# Retrieve status from audio control panel 8W1919616.

from usblini import USBlini
import time

def byte2uint(val):
    if val > 127:
        return -(256-val)
    else:
        return val


def frame_listener(frame):

    if frame.frameid == 0x10:

        if frame.data[0] != 0:
            print('Encoder steps: {}'.format(byte2uint(frame.data[0])))

        if frame.data[1] & 1 == 1:
            print("Button is pressed")



ulini = USBlini()
ulini.open()
ulini.set_baudrate(19200)

# send one frame to wakeup devices
ulini.master_write(0x00, USBlini.CHECKSUM_MODE_NONE, [])
time.sleep(0.2)

# add listener and set master sequence
ulini.frame_listener_add(frame_listener)
ulini.master_set_sequence(1000, 200, [0x10])

while True:
   pass

ulini.close()
