import time
import rtmidi
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)

"""
Program notes:

RTMIDI channel/status map:
    192: "Program Change",
    176: "Control Change",
    144: "Note On",
    128: "Note Off"
    
    
This program will take

this program will add a second controller value with delay when it 
senses a midi input, i.e. if an expression pedal midi is detected, 
it can trigger a separte cc or note on command to enable pedal, and 
will automatically disable the device after a short inactivity timeout

[midi-port] [ch] [msg-type] [msg-data1] -> [midi-out-port] [ch] [msg-type] [value] [timeout] [0-threshold]

Trigger Message -> [channel, type, data1, data2] (if CC) or [channel, type, data1] if PC/Note On/Off
Activation Message -> [channel, type, data1, data2] for CC or [channel, type, data1] if PC/ Note On/Off
Deactivation Message -> [channel, type, data1, data2] for CC or [channel, type, data1] if PC/ Note On/Off

Deactivation minimum threshold (only if trigger is type cc) -> will not deactivate on timeout above this value
Deactivation maximum threshold (only if trigger is type cc) -> will not deactivate on timeout below this value
Deactivation timeout (s)

"""

typeMap = {
    192: "Program Change",
    176: "Control Change",
    144: "Note On",
    128: "Note Off"
}

class MidiCCAutoEngage(object):
    def __init__(self):
        self.pedalActivated = False
        self.timeSincelastMsg = -1
        self.timeOfLastMsg = -1
        self.sendChannel = 1
        self.data1 = None
        self.data2 = None
        self.timeOutInS = 0.5
        self.deactivationThreshold = 20
        self.activationChannel = 1
        self.activationMessageValue = 93
        self.sendChannel = 1
        self.sendMessageValue = 94
        self.midiOutputPort = None


    def __call__(self, event, data=None):
        # this is only activated if message has been received...
        if self.pedalActivated:
            self.timeSincelastMsg = time.time() - self.timeOfLastMsg
            if self.timeSincelastMsg > self.timeOutInS and self.data2 < self.deactivationThreshold:
                self.midiOutputPort.send_message([CONTROL_CHANGE | self.sendChannel, self.sendMessageValue, 0])
                self.pedalActivated = False

        msg, deltatime = event
        if msg[0] < 0xF0:
            channel = (msg[0] & 0xF) + 1
            status = msg[0] & 0xF0
        else:
            status = msg[0]
            channel = None

        num_bytes = len(msg)

        if num_bytes >= 2:
            self.data1 = msg[1]
        if num_bytes >= 3:
            self.data2 = msg[2]

        if status == 176 and self.data1 == 93:
            if not self.pedalActivated:
                self.midiOutputPort.send_message([CONTROL_CHANGE | self.sendChannel, self.sendMessageValue, 127])
            self.pedalActivated = True
            self.timeOfLastMsg = time.time()

    def validate(self):
        """
        Returns true if input message matches activation message
        """
        return True


class MidiInputHandler(object):
    def __init__(self, port, config=""):
        self.port = port
        self._wallclock = time.time()
        self.commands = dict()
        # self.load_config(config)

    def __call__(self, event, data=None):
        event, deltatime = event
        self._wallclock += deltatime

        if event[0] < 0xF0:
            channel = (event[0] & 0xF) + 1
            status = event[0] & 0xF0
        else:
            status = event[0]
            channel = None

        data1 = data2 = None
        num_bytes = len(event)

        if num_bytes >= 2:
            data1 = event[1]
        if num_bytes >= 3:
            data2 = event[2]



def main():
    midiInput = rtmidi.MidiIn()
    midiOutput = rtmidi.MidiOut()
    # TODO: generate auto port or get input from argument list:
    midiInputPort = midiInput.open_port(1)
    # TODO: Register callback:
    midiInputPort.set_callback(MidiCCAutoEngage())

def run():
    midiInput = rtmidi.MidiIn()
    midiOutput = rtmidi.MidiOut()

    availableInputPorts = midiInput.get_ports()
    availableOutputPorts = midiOutput.get_ports()

    # create output port
    outputPort = midiOutput.open_virtual_port("rtoutput")

    inputPort = midiInput.open_port(1)
    # inputPort.set_callback(MidiInputHandler(1))

    pedalActivated = False
    timeSincelastMsg = -1
    timeOfLastMsg = -1
    sendChannel = 1


    while True:
        msg = inputPort.get_message()
        if pedalActivated:
            timeSincelastMsg = time.time() - timeOfLastMsg
            if timeSincelastMsg > 0.5 and data2 < 20:
                outputPort.send_message([CONTROL_CHANGE | sendChannel, 94, 0])
                pedalActivated = False
        if msg:
            msg, deltatime = msg
            if msg[0] < 0xF0:
                channel = (msg[0] & 0xF) + 1
                status = msg[0] & 0xF0
            else:
                status = msg[0]
                channel = None

            data1 = data2 = None
            num_bytes = len(msg)

            if num_bytes >= 2:
                data1 = msg[1]
            if num_bytes >= 3:
                data2 = msg[2]

            if status == 176 and data1 == 93:
                if not pedalActivated:
                    outputPort.send_message([CONTROL_CHANGE | sendChannel, 94, 127])
                pedalActivated = True
                timeOfLastMsg = time.time()


            print("{:s}, {:s}, {:d}, {:s}, {:f}".format(str(channel) or '-', typeMap[status], data1, str(data2) or '', timeSincelastMsg))
        time.sleep(0.01)


    return midiout


if __name__  =="__main__":
    midiout = run()
    del midiout

