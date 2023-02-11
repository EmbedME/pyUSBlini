# This file is part of the pyUSBlini project.
#
# Copyright(c) 2021-2022 Thomas Fischl (https://www.fischl.de)
# 
# pyUSBlini is free software: you can redistribute it and/or modify
# it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyUSBlini is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
# along with pyUSBlini.  If not, see <http://www.gnu.org/licenses/>

import usb1
import threading

class USBlini(object):

    USB_VID = 0x04D8
    USB_PID = 0xE870

    CHECKSUM_MODE_NONE = 0x0000
    CHECKSUM_MODE_LIN1 = 0x0100
    CHECKSUM_MODE_LIN2 = 0x0200    

    MASK_REPORT_TYPE = 0x0f
    REPORT_TYPE_STATUS = 0x00
    REPORT_TYPE_ERROR = 0x01
    REPORT_TYPE_FRAME = 0x02

    MASK_REPORT_SOURCE = 0xf0
    REPORT_SOURCE_COMMON = 0x00
    REPORT_SOURCE_MASTER = 0x10
    REPORT_SOURCE_SLAVE = 0x20
    REPORT_SOURCE_USER = 0x30

    CMD_ECHO =                  0x01
    CMD_START_BOOTLOADER =      0x02
    CMD_RESET =                 0x03
    CMD_SET_BAUDRATE =          0x04
    CMD_CLEAR_ERRORFLAGS =      0x05 
    CMD_MASTER_WRITE =          0x11
    CMD_MASTER_SET_SEQUENCE =   0x12 
    CMD_SLAVE_SET_FRAME =       0x21
    CMD_SLAVE_SET_RELOADVALUE = 0x22
    CMD_SLAVE_SET_RESETMASK =   0x23

    def __init__(self):
        """ Initialze """
       
        self.frame_listeners = []
        self.statusreport_listeners = []
        self.logic_listeners = []
        self.ctx = usb1.USBContext()

    def open(self, serialnumber = None):
        """
        Open connection to USBlini.
        :param serialnumber: USB serial number
        :type serialnumber: string
        """

        self.ctx.open()

        self.usbdev = self.get_usb_device(serialnumber)
        if self.usbdev is None:
            raise USBliniNotFoundError()

        self.usbhandle = self.usbdev.open()
        self.usbhandle.claimInterface(0)        

        self.receiveevent = threading.Event()

        th1 = usb1.USBTransferHelper()
        th1.setEventCallback(usb1.TRANSFER_COMPLETED, self.usbtransfer_ep1_callback)
        t1 = self.usbhandle.getTransfer()
        t1.setInterrupt(0x81, 64, th1)
        t1.submit()

        th2 = usb1.USBTransferHelper()
        th2.setEventCallback(usb1.TRANSFER_COMPLETED, self.usbtransfer_ep2_callback)
        t2 = self.usbhandle.getTransfer()
        t2.setInterrupt(0x82, 64, th2)
        t2.submit()

        self.eventthread = USBliniUSBEventHandler(self)
        self.eventthread.start()

    def close(self):
        """
        Close connection to USBlini.
        """
        self.eventthread.stop()
        self.eventthread.join()
        self.usbdev.close()
        self.ctx.close()

    def get_usb_device(self, serialnumber = None):
        """
        Get USB device matching VID and PID and if given also check the USB serial number.
        :rtype: USBDeviceHandle
        :param serialnumber: USB serial number
        :type serialnumber: string       
        """
        for device in self.ctx.getDeviceIterator():
            if device.getVendorID() == self.USB_VID and device.getProductID() == self.USB_PID:
                
                if serialnumber is None:
                    return device

                try:
                    if device.getSerialNumber() == serialnumber:
                        return device
                except usb1.USBErrorAccess:
                    pass

    def usbtransfer_ep1_callback(self, t):
        data = t.getBuffer()[:t.getActualLength()]
        for i in range(0, len(data), 16):
            report = data[i:i+16]
            if report[0] & self.MASK_REPORT_SOURCE == self.REPORT_SOURCE_USER:
                self.response = report
                self.receiveevent.set()
            if report[0] & self.MASK_REPORT_TYPE == self.REPORT_TYPE_FRAME:
                f = LINFrame.from_report(report)
                for listener in self.frame_listeners:
                    listener(f)
            if report[0] & self.MASK_REPORT_TYPE == self.REPORT_TYPE_STATUS:
                f = StatusReport.from_report(report)
                for listener in self.statusreport_listeners:
                    listener(f)
        return True

    def usbtransfer_ep2_callback(self, t):
        data = t.getBuffer()[:t.getActualLength()]
        for listener in self.logic_listeners:
            listener(data)
        return True

    def get_version(self):
        version = '{:04x}'.format(self.usbdev.getbcdDevice())
        return version[:2] + '.' + version[2:]

    def start_bootloader(self):
        """
        Jump to bootloader.
        """
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_START_BOOTLOADER, 0x5237, 0, [])

    def echo_test(self):
        """
        Echo test. Send code to device and check response.
        """
        response = self.usbhandle.controlRead(usb1.TYPE_CLASS, self.CMD_ECHO, 0x1234, 0, 2)
        return (response[0] == 0x34) and (response[1] == 0x12) 

    def reset(self):
        """
        Reset the device: clear master and slave tables and set default configuration.
        """
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_RESET, 0, 0, [])


    def set_baudrate(self, baudrate, autobaud = False):
        """
        Set baudrate.
        :param baudrate: Baudrate in Hz
        :type baudrate: integer
        :param autobaud: Set autobaud feature (only slave functions use it)
        :type autobaud: bool
        """
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_SET_BAUDRATE, baudrate, int(autobaud), [])

    def slave_set_frame(self, tableid, frameid, checksummode, data, reloadvalue = 0, resetmask = 0):
        """
        Set frame in slave table.
        :param tableid: Table identifier (row)
        :type tableid: integer
        :param frameid: LIN frame identifier
        :type frameid: integer
        :param checksummode: Checksum mode (none/LIN1/LIN2)
        :type checksummode: integer
        :param data: Frame data
        :type data: list(int)
        :param reloadvalue: Counter reload value
        :type reloadvalue: integer
        :param resetmask: Bit mask for resetting slave table items (bit0 -> tableid=0, bit1 -> tableid=1, ...)
        :type resetmask: integer
        """
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_SLAVE_SET_FRAME, frameid | checksummode, tableid, data)
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_SLAVE_SET_RELOADVALUE, reloadvalue, tableid, [])
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_SLAVE_SET_RESETMASK, resetmask, tableid, [])

    def master_write(self, frameid, checksummode, data):
        """
        Master write. Blocks until response.
        :type tableid: integer
        :param frameid: LIN frame identifier
        :type frameid: integer
        :param checksummode: Checksum mode (none/LIN1/LIN2)
        :type checksummode: integer
        :param data: Frame data
        :type data: list(int)
        """
        self.receiveevent.clear()
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_MASTER_WRITE, frameid | checksummode, 0, data)
        self.receiveevent.wait()
        # TODO: check report id, check pid, check checksum

        if self.response[0] & self.MASK_REPORT_TYPE == self.REPORT_TYPE_ERROR:
            raise USBliniError()

        return self.response[3:3+self.response[2]]

    def clear_errorflags(self, clearmask = 0xff):
        """
        Clear errorflags.
        :param clearmask: Bit mask of errors to clear
        :type baudrate: integer
        """
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_CLEAR_ERRORFLAGS, clearmask, 0, [])


    def master_set_sequence(self, period, frametime, sequence):
        """
        Set master sequence.
        :param period: Period of complete sequence in milliseconds
        :type period: integer
        :param frametime: Time of one frame slot (time between start of two frames)
        :type frametime: integer
        :param sequence: Sequence of LIN identifiers the master should request periodically
        :type sequence: list(int)
        """
        self.usbhandle.controlWrite(usb1.TYPE_CLASS, self.CMD_MASTER_SET_SEQUENCE, period, frametime, sequence)

    def frame_listener_add(self, func):
        """
        Add a frame listener (callback)
        :param func: Function to add to listener list
        :type func: function
        """
        self.frame_listeners.append(func)

    def frame_listener_remove(self, func):
        """
        Remove given function from listeners list
        :param func: Function to remove from listener list
        :type func: function
        """
        if func in self.frame_listeners:
            self.frame_listeners.remove(func)
        else:
            raise USBliniError("ERROR: failed to remove frame listener")

    def statusreport_listener_add(self, func):
        """
        Add a statusreport listener (callback)
        :param func: Function to add to listener list
        :type func: function
        """
        self.statusreport_listeners.append(func)

    def statusreport_listener_remove(self, func):
        """
        Remove given function from listeners list
        :param func: Function to remove from listener list
        :type func: function
        """
        if func in self.statusreport_listeners:
            self.statusreport_listeners.remove(func)
        else:
            raise USBliniError("ERROR: failed to remove status report listener")

    def logic_listener_add(self, func):
        """
        Add a logic listener (callback)
        :param func: Function to add to listener list
        :type func: function
        """
        self.logic_listeners.append(func)

    def logic_listener_remove(self, func):
        """
        Remove given function from listeners list
        :param func: Function to remove from listener list
        :type func: function
        """
        if func in self.logic_listeners:
            self.logic_listeners.remove(func)
        else:
            raise USBliniError("ERROR: failed to remove logic listener")


class LINFrame(object):

    def __init__(self, frameid, data=None, checksum = None, timestamp = None, autobaudvalue = None):
        self.frameid = frameid
        self.data = data
        self.checksum = checksum
        self.timestamp = timestamp
        self.autobaudvalue = autobaudvalue

    def __repr__(self):
        if len(self.data) > 0:
            return '{} [{}] {}'.format(hex(self.frameid), ', '.join(hex(x) for x in self.data), hex(self.checksum))
        else:
            return '{} []'.format(hex(self.frameid))

    @classmethod
    def from_report(cls, r):
        pid = r[1]
        frameid = pid & 0x3f
        length = r[2]
        if length > 1:
            length = length - 1
            checksum = r[3 + length] 
        else:
            checksum = None    
        data = r[3:3 + length]   
        timestamp = r[13]<<8 | r[12]
        autobaudvalue = r[15]<<8 | r[14]
        return cls(frameid, data, checksum, timestamp, autobaudvalue)

class StatusReport(object):

    def __init__(self, errorflags, slaveTableStatus):
        self.errorflags = errorflags
        self.slaveTableStatus = slaveTableStatus

    def getSlaveTableStatusList(self):
        return [True if self.slaveTableStatus & (1 << n) else False for n in range(16)]

    @classmethod
    def from_report(cls, r):
        errorflags = r[1]
        slaveTableStatus = r[3]<<8 | r[2]
        return cls(errorflags, slaveTableStatus)

class USBliniUSBEventHandler(threading.Thread):
    def __init__(self, lini):
        threading.Thread.__init__(self)
        self.lini = lini
        self.running = True

    def run(self):
        while self.running:
            self.lini.ctx.handleEvents()
    def stop(self):
        self.running = False
        self.lini.echo_test()

class USBliniError(Exception):
    def __init__(self):
        Exception.__init__(self)

class USBliniNotFoundError(USBliniError):
    def __init__(self):
        Exception.__init__(self)
