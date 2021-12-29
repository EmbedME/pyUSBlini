#!/usr/bin/env python

from usblini import USBlini

ulini = USBlini()
ulini.open()
ulini.start_bootloader()
ulini.close()