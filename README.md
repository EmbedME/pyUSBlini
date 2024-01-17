# pyUSBlini

pyUSBlini is a Python library for the [USBlini - USB to LIN Interface](https://www.fischl.de/usblini/) which allows easy access to LIN bus devices and can act as both master and slave. It features a logic analyzer function to sample the logic levels on the LIN RX line.

## Installation

```bash
pip install git+https://github.com/EmbedME/pyUSBlini
```

## Usage
USBlini can act as both master and slave.

### Master

This example shows a single master write:

```python
from usblini import USBlini
usblini = USBlini()
usblini.open()
data = usblini.master_write(0x10, USBlini.CHECKSUM_MODE_LIN2, [])
print(data) # print out response
usblini.close()
```
In this example a master polling sequence with listener function is set up:

```python
from usblini import USBlini
usblini = USBlini()
usblini.open()

def frame_listener(frame):
    if frame.frameid == 0x10 and frame.data[1] & 1 == 1:
        print("Button is pressed")

usblini.frame_listener_add(frame_listener)
usblini.master_set_sequence(1000, 200, [0x10])

while True:
   pass

usblini.close()
```

The USBliniGUI also offers master functions:

![](https://raw.githubusercontent.com/EmbedME/pyUSBlini/main/docs/USBliniGUI_Master.png)

### Slave
The USBlini operates in slave mode with 16 internal slots, each holding a response. When a master requests data, values from the matching slot with the lowest slot ID are sent. Each slot has a counter initialized with a reload value. When the counter reaches zero, the slot is deactivated, and a reset mask is applied. The reset mask determines which slots are reset (activated) based on the set bits (bit0 -> tableid=0, bit1 -> tableid=1, and so on). The internal counter is then loaded with the reload value.

This setup allows for the implementation of slave sequences. For example, if the slave should respond three times with 0x01, once with 0x02, twice with 0x03, and then repeat:
```python
usblini.slave_set_frame(tableid=0, frameid=0x10, checksummode=USBlini.CHECKSUM_MODE_LIN2, data=[0x01], reloadvalue=3, resetmask=0x0002)
usblini.slave_set_frame(tableid=1, frameid=0x10, checksummode=USBlini.CHECKSUM_MODE_LIN2, data=[0x02], reloadvalue=1, resetmask=0x0004)
usblini.slave_set_frame(tableid=2, frameid=0x10, checksummode=USBlini.CHECKSUM_MODE_LIN2, data=[0x03], reloadvalue=2, resetmask=0x0001)
```
Same example using USBliniGUI:

![](https://raw.githubusercontent.com/EmbedME/pyUSBlini/main/docs/USBliniGUI_Slave.png)

With a reload value of 0, the internal counter is ignored, and the slot is always active. For example:
```python
usblini.slave_set_frame(3, 0x11, USBlini.CHECKSUM_MODE_LIN2, [0x04])
```
