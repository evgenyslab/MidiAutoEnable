import time
import numpy as np
import argparse
import rtmidi
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)

def run():
    """
    Generate expresstion midi on cc on channel 1, at value 90
    """
    sendChannel = 1
    value = 90

    midiOutput = rtmidi.MidiOut()
    outputPort = midiOutput.open_virtual_port("RToutput1")

    dataRange = (np.sin(np.arange(0,np.pi,np.pi/256))*127).astype(int)
    # sweep over cc output:
    while True:
        for data1 in dataRange:
            outputPort.send_message([CONTROL_CHANGE | sendChannel, value, data1])
            time.sleep(0.01)
        time.sleep(1)



if __name__=="__main__":
    run()