#!/usr/bin/env python

# Detect devices on LIN bus
#
# USBlini:
#     https://www.fischl.de/usblini/

from __future__ import print_function
from usblini import USBlini
import time

# open and initialize usblini
ulini = USBlini()
ulini.open()
ulini.set_baudrate(19200)

# send one frame to wakeup devices
ulini.master_write(0x00, USBlini.CHECKSUM_MODE_NONE, [])
time.sleep(0.2)

# travel through all ids
print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
for i in range(0, 64, 16):
    print('{0:02x}: '.format(i), end='')
    for j in range(0, 16):
        address = i + j
        response = ulini.master_write(address, USBlini.CHECKSUM_MODE_NONE, [])
        if len(response) > 0:
            print('{0:02x} '.format(address), end='')
        else:
            print('-- ', end='')
    print('')

# cleanup
ulini.close()