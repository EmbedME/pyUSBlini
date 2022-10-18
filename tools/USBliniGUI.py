# This file is part of the pyUSBlini project.
#
# Copyright(c) 2021 Thomas Fischl (https://www.fischl.de)
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

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import*
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import showinfo
from usblini import USBlini
from usblini import LINFrame
from usblini import USBliniError
import queue
import zipfile


class App(tk.Tk):
    def __init__(self, serial):
        super().__init__()

        title = 'USBliniGUI v1.0'
        if serial != None:
           title = title + ' (' + serial + ')'
        self.title(title)

        tabControl = ttk.Notebook(self)
        tabSettings = ttk.Frame(tabControl)
        tabMaster = ttk.Frame(tabControl)
        tabSlave = ttk.Frame(tabControl)
        tabError = ttk.Frame(tabControl)
        tabLogic = ttk.Frame(tabControl)

        tabControl.add(tabSettings, text='Settings')
        tabControl.add(tabMaster, text='Master')
        tabControl.add(tabSlave, text='Slave')
        tabControl.add(tabLogic, text='Logic')
        tabControl.add(tabError, text='Error')

        tabControl.pack(side = 'right', fill='both')


        topframe = Frame(self)
        clearbutton = tk.Button(topframe, text='Clear', command=self.clear)
        clearbutton.pack(side='left')
        logbutton = tk.Button(topframe, text='Save', command=self.savelog)
        logbutton.pack(side='left')
        self.follow = IntVar(value=1)
        ttk.Checkbutton(topframe, text="Follow", variable=self.follow).pack(side='right')

        topframe.pack(side = 'bottom', fill = 'x', padx='5', pady='5')


        settingframe = Frame(tabSettings)
        lbaudrate = Label(settingframe, text='Baudrate (bps):')
        lbaudrate.grid(row=0, column=0, sticky="W")
        self.baudratecombo = ttk.Combobox(settingframe, values=[1200, 2400, 9600, 19200], width=6)
        self.baudratecombo.current(3)
        self.baudratecombo.grid(row=0, column=1, sticky="W")

        lautobaud = Label(settingframe, text='Baudrate calibration:')
        lautobaud.grid(row=1, column=0, sticky="W")
        self.autobaud = IntVar()
        self.autobaudbutton = ttk.Checkbutton(settingframe, text="Enable slave autobaud", variable=self.autobaud)
        self.autobaudbutton.grid(row=1, column=1, sticky="W")

        setsettingbutton = tk.Button(settingframe, text='Set', command=self.setSettings)
        setsettingbutton.grid(row=2, column=1, sticky="W")

        settingframe.pack(side = 'top', fill = 'x', padx = '5', pady=10)



        columns = ('time', 'id', 'data')
        self.tree = ttk.Treeview(self, columns=columns, show='headings')

        self.tree.heading('time', text='Time (ms)')
        self.tree.heading('id', text='ID')
        self.tree.heading('data', text='Data')

        self.tree.column("time", minwidth=0, width=80, stretch=False)
        self.tree.column("id", minwidth=0, width=50, stretch=False)
        self.tree.column("data", minwidth=0, width=250)

        # scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)



        sendframe = Frame(tabMaster)
        self.identry = tk.Entry(sendframe, width=3)
        self.identry.insert(END, '10')
        self.identry.grid(row=0, column=0)
        self.lengthValue = IntVar()
        self.sbox = Spinbox(sendframe, from_ = 0, to = 8, width=3, textvariable=self.lengthValue)
        self.lengthValue.trace('w', self.updateLength)
        self.sbox.grid(row=0, column=1)
        sendbutton = tk.Button(sendframe, text='Send', command=self.send)
        sendbutton.grid(row=0, column=12)
        self.dataentry = [None] * 8
        for x in range(8):
            self.dataentry[x] = tk.Entry(sendframe, width=3)
            self.dataentry[x].insert(END, x)
            self.dataentry[x].config(state='disable')
            self.dataentry[x].grid(row=0, column=2+x)
        self.checksummode = StringVar()
        self.checksummode.set("LIN2")
        checksummodeOptionMenu = OptionMenu(sendframe, self.checksummode, "None", "LIN1", "LIN2")
        checksummodeOptionMenu.grid(row=0, column=11)

        sequenceframe = Frame(tabMaster)
        lperiod = Label(sequenceframe, text='Period (ms):')
        lperiod.grid(row=0, column=0, sticky="W")
        self.periodentry = tk.Entry(sequenceframe, width=5)
        self.periodentry.insert(END, '1000')
        self.periodentry.grid(row=0, column=1, sticky="W")
        lframetime = Label(sequenceframe, text='Frametime (ms):')
        lframetime.grid(row=1, column=0, sticky="W")
        self.frametimeentry = tk.Entry(sequenceframe, width=5)
        self.frametimeentry.insert(END, '200')
        self.frametimeentry.grid(row=1, column=1, sticky="W")
        lsequence = Label(sequenceframe, text='List of IDs (hex):')
        lsequence.grid(row=2, column=0, sticky="W")
        self.sequence = tk.Entry(sequenceframe, width=3*16)
        self.sequence.insert(END, '10, 11')
        self.sequence.grid(row=2, column=1, sticky="W")
        sequencebuttonframe = Frame(sequenceframe)
        setseqbutton = tk.Button(sequencebuttonframe, text='Set', command=self.setSequence)
        setseqbutton.pack(side='left')
        clearseqbutton = tk.Button(sequencebuttonframe, text='Clear', command=self.clearSequence)
        clearseqbutton.pack(side='left')
        sequencebuttonframe.grid(row=3, column=1, sticky="W")

        lsinglewrite = Label(tabMaster, text="Single master write:")
        lmastersequence = Label(tabMaster, text="Master sequence:")

        lsinglewrite.pack(side='top', anchor='w', padx = '5', pady=(10,0))
        sendframe.pack(side = 'top', fill = 'x', padx = '5')
        lmastersequence.pack(side='top', anchor='w', padx = '5', pady=(10,0))
        sequenceframe.pack(side='top', anchor='w', padx = '20', pady=(0,10))

        scrollbar.pack(side = 'right', fill = 'y', expand = False)
        self.tree.pack(side = 'top', fill = 'both', expand = True)

        slaveTableFrame = Frame(tabSlave)
        Label(slaveTableFrame, text='Id').grid(row=0, column=1)
        Label(slaveTableFrame, text='Len').grid(row=0, column=2)
        for x in range(8):
            Label(slaveTableFrame, text='D{:d}'.format(x)).grid(row=0, column=3+x)
        Label(slaveTableFrame, text='Chksum').grid(row=0, column=12)
        Label(slaveTableFrame, text='Reload').grid(row=0, column=13)
        Label(slaveTableFrame, text='Reset').grid(row=0, column=14)

        self.slaveTableItem = [None] * 16
        for x in range(16):
            self.slaveTableItem[x] = SlaveTableItem(slaveTableFrame, x)
        slaveTableFrame.pack(side='top', padx=5, pady=(10,0))

        slavetablebuttonframe = Frame(tabSlave)
        tk.Button(slavetablebuttonframe, text='Set', command=self.setSlaveTable).pack(side='left')        
        tk.Button(slavetablebuttonframe, text='Clear', command=self.clearSlaveTable).pack(side='left')
        slavetablebuttonframe.pack(side='top', pady=10)


        self.errorlist = ["EP1 Overflow", "Autobaud Overflow", "Missing Echo (check VBat!)"]
        self.errorlabel = [None] * len(self.errorlist)
        for x in range(len(self.errorlist)):
            self.errorlabel[x] = Label(tabError, text=self.errorlist[x], fg='#999')
            self.errorlabel[x].pack(side='top', padx=5, pady=5)
        tk.Button(tabError, text='Clear', command=self.clearErrors).pack(side='top')


        Label(tabLogic, text='Sample logic level on RX pin with 100 ksps and save it in \nPulseView (sigrok project) compatible file for further analysis.', justify=LEFT).pack(side='top', padx=5, pady=10, anchor='w')
        filenameFrame = Frame(tabLogic)
        Label(filenameFrame, text='Filename:').pack(side='left')
        self.logicfilenameentry = tk.Entry(filenameFrame, width=40)
        self.logicfilenameentry.insert(END, 'usblini_la_sampled.sr')
        self.logicfilenameentry.pack(side='left', padx=5)
        tk.Button(filenameFrame, text='Browse', command=self.browseLogicFilename).pack(side='left')
        filenameFrame.pack(side='top')
        logicButtonFrame = Frame(tabLogic)
        self.logicStartButton = tk.Button(logicButtonFrame, text='Start recording', command=self.startRecording)
        self.logicStartButton.grid(row=0, column=0)
        self.logicStopButton = tk.Button(logicButtonFrame, text='Stop recording', command=self.stopRecording, state='disable')
        self.logicStopButton.grid(row=0, column=1)
        logicButtonFrame.pack(side='top')
        self.recordingActive = 0

        self.usblini = USBlini()
        self.usblini.open(serial)
        self.usblini.reset()
        self.usblini.set_baudrate(19200, True)

        self.frame_queue = queue.Queue()
        self.statusreport_queue = queue.Queue()
        self.after(10, self.update_frame)
        self.after(10, self.update_statusreport)
        self.usblini.frame_listener_add(self.frame_listener)
        self.usblini.statusreport_listener_add(self.statusreport_listener)

        Label(tabSettings, text='Firmware version: {}'.format(self.usblini.get_version()), justify=LEFT).pack(side='top', padx=5, pady=(20,5), anchor='w')
        tk.Button(tabSettings, text='Start bootloader and exit GUI', command=self.startBootloader).pack(side='top', padx=5, anchor='w')

    def destroy(self):
        self.stopRecording()
        self.usblini.close()
        tk.Tk.destroy(self)

    def startBootloader(self):
        self.usblini.start_bootloader()
        self.destroy()

    def startRecording(self):
        self.logicoutfile = open("logic-1-1", "wb")
        self.usblini.logic_listener_add(self.logic_listener)
        self.recordingActive = 1
        self.logicStopButton.config(state="normal")
        self.logicStartButton.config(state="disable")
        self.showMessage('Logic level recording started')

    def stopRecording(self):
        if self.recordingActive == 0:
            return
        self.recordingActive = 0
        self.usblini.logic_listener_remove(self.logic_listener)
        self.logicStartButton.config(state="normal")
        self.logicStopButton.config(state="disable")
        self.showMessage('Logic level recording stopped')
        with zipfile.ZipFile(self.logicfilenameentry.get(), 'w', zipfile.ZIP_DEFLATED) as zipped_f:
            zipped_f.write("logic-1-1")
            zipped_f.writestr("version", "2")
            zipped_f.writestr("metadata", "[device 1]\ncapturefile=logic-1\ntotal probes=1\nsamplerate=100 kHz\ntotal analog=0\nprobe1=LIN\nunitsize=1")

    def browseLogicFilename(self):
        file_name = asksaveasfilename()
        self.logicfilenameentry.delete(0, END)
        self.logicfilenameentry.insert(0, file_name)

    def clearErrors(self):
        self.usblini.clear_errorflags()
        self.showMessage('Error flags cleared')

    def setSlaveTable(self):
        for x in range(16):
            self.usblini.slave_set_frame(x, self.slaveTableItem[x].getId(), self.slaveTableItem[x].getChecksummode(), self.slaveTableItem[x].getData(), self.slaveTableItem[x].getReloadvalue(), self.slaveTableItem[x].getResetmask())
        self.showMessage('Slave table set')

    def clearSlaveTable(self):
        for x in range(16):
            self.usblini.slave_set_frame(x, 0, 0, [])
        self.showMessage('Slave table cleared')

    def setSettings(self):
        baudrate = int(self.baudratecombo.get())
        autobaud = self.autobaud.get() == 1
        self.usblini.set_baudrate(baudrate, autobaud)
        self.showMessage('Baudrate set: {:d}, autobaud: {}'.format(baudrate, autobaud))

    def setSequence(self):
        period = int(self.periodentry.get())
        frametime = int(self.frametimeentry.get())
        if len(self.sequence.get()) > 0:
            idlist = [int(e, 16) for e in self.sequence.get().split(',')]
        else:
            idlist = []
        self.usblini.master_set_sequence(period, frametime, idlist)
        self.showMessage('Master sequence set: {:d}/{:d} [{}]'.format(period, frametime, ','.join('{:02x}'.format(x) for x in idlist)))

    def clearSequence(self):
        self.usblini.master_set_sequence(0, 0, [])
        self.showMessage('Master sequence cleared')
    
    def updateLength(self, a, b, c):
        length = int(self.sbox.get())
        for x in range(8):
            if x < length:
                self.dataentry[x].config(state='normal')
            else:
                self.dataentry[x].config(state='disable')
            self.dataentry[x].update_idletasks()

    def showMessage(self, msg):
        self.tree.insert('', tk.END, values=('', '', msg))
        if self.follow.get():
            self.tree.yview_moveto(1)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def savelog(self):
        file_name = asksaveasfilename()
        with open(file_name, 'w') as logfile:
            for child in self.tree.get_children():
                values = self.tree.item(child)["values"]
                logfile.write("{}\t{}\t{}\n".format(values[0], values[1], values[2]))
            logfile.close()
        self.showMessage('Saved messages to file')

    def send(self):
        length = int(self.sbox.get())
        identifier = int(self.identry.get(), 16)
        data = [None] * length
        for x in range(length):
            data[x] = int(self.dataentry[x].get(), 16)
        modes = {"None": self.usblini.CHECKSUM_MODE_NONE, "LIN1": self.usblini.CHECKSUM_MODE_LIN1, "LIN2": self.usblini.CHECKSUM_MODE_LIN2}
        checksummode = modes[self.checksummode.get()]
        try:
           response = self.usblini.master_write(identifier, checksummode, data)
        except USBliniError:
           self.showMessage('Error while sending message')


    def frame_listener(self, frame):
        self.frame_queue.put_nowait(frame)

    def update_frame(self):
        while not self.frame_queue.empty():
            frame = self.frame_queue.get(False)
            self.tree.insert('', tk.END, values=(frame.timestamp, '{:02x}'.format(frame.frameid), '{}'.format(' '.join('{:02x}'.format(x) for x in frame.data))))
            if self.follow.get():
                self.tree.yview_moveto(1)
        self.after(10, self.update_frame)

    def statusreport_listener(self, statusreport):
        self.statusreport_queue.put_nowait(statusreport)

    def update_statusreport(self):
        while not self.statusreport_queue.empty():
            statusreport = self.statusreport_queue.get(False)
            l = statusreport.getSlaveTableStatusList()           
            for x in range(16):
                if l[x]:                    
                    self.slaveTableItem[x].lno.config(bg="green")
                else:
                    self.slaveTableItem[x].lno.config(bg="#d9d9d9")

            for x in range(len(self.errorlist)):
                if statusreport.errorflags & (1<<x):
                    self.errorlabel[x].config(fg="red")
                else:
                    self.errorlabel[x].config(fg="green")
        self.after(10, self.update_statusreport)

    def logic_listener(self, data):
        for d in data:
            for i in range(8):
                if (d & 0x80) == 0:
                    self.logicoutfile.write(b'\x2E')
                else:
                    self.logicoutfile.write(b'\x4F')
                d = d << 1

class SlaveTableItem(object):

    def __init__(self, master, tableid):
        self.master = master
        row = tableid + 1

        self.lno = Label(self.master, text=str(tableid), width=3)
        self.lno.grid(row=row, column=0)

        self.identry = tk.Entry(self.master, width=3)
        self.identry.insert(END, '{:02x}'.format(0x10 + tableid))
        self.identry.grid(row=row, column=1)

        self.lengthValue = IntVar()
        self.sbox = Spinbox(self.master, from_ = 0, to = 8, width=3, textvariable=self.lengthValue)
        self.lengthValue.trace('w', self.updateLength)
        self.sbox.grid(row=row, column=2)

        self.dataentry = [None] * 8
        for x in range(8):
            self.dataentry[x] = tk.Entry(self.master, width=3)
            self.dataentry[x].insert(END, x)
            self.dataentry[x].config(state='disable')
            self.dataentry[x].grid(row=row, column=3+x)
        self.checksummode = StringVar()
        self.checksummode.set("LIN2")
        checksummodeOptionMenu = OptionMenu(self.master, self.checksummode, "None", "LIN1", "LIN2")
        checksummodeOptionMenu.grid(row=row, column=12)

        self.reloadvalueentry = tk.Entry(self.master, width=5)
        self.reloadvalueentry.insert(END, '0')
        self.reloadvalueentry.grid(row=row, column=13)

        self.resetmaskentry = tk.Entry(self.master, width=5)
        self.resetmaskentry.insert(END, '0000')
        self.resetmaskentry.grid(row=row, column=14)

    def updateLength(self, a, b, c):
        length = int(self.sbox.get())
        for x in range(8):
            if x < length:
                self.dataentry[x].config(state='normal')
            else:
                self.dataentry[x].config(state='disable')
            self.dataentry[x].update_idletasks()

    def getId(self):
        return int(self.identry.get(), 16)

    def getData(self):
        length = int(self.sbox.get())
        data = [None] * length
        for x in range(length):
            data[x] = int(self.dataentry[x].get(), 16)
        return data

    def getChecksummode(self):
        modes = {"None": USBlini.CHECKSUM_MODE_NONE, "LIN1": USBlini.CHECKSUM_MODE_LIN1, "LIN2": USBlini.CHECKSUM_MODE_LIN2}
        return modes[self.checksummode.get()]

    def getReloadvalue(self):
        return int(self.reloadvalueentry.get())

    def getResetmask(self):
        return int(self.resetmaskentry.get(), 16)



if __name__ == '__main__':

    if len(sys.argv) > 1:
        serial = sys.argv[1]
    else:
        serial = None

    app = App(serial)
    app.mainloop()
