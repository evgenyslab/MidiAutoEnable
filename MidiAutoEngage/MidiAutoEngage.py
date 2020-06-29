import time
import argparse
import rtmidi
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)

"""
Program notes:

rtMidi encodes status & Channel into first part of message

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

intToStatus ={
    192: "pc",
    176: "cc",
    144: "noteOn",
    128: "noteOff"
}

statusToInt = {
    "pc": 192,
    "cc": 176,
    "noteOn": 144,
    "noteOff": 128,
}

def statusIsCC(status):
    return intToStatus[status] == 'cc'

def isSysex(msg):
    return msg[0] == 0xF0

def decodeMessageIntoParts(event):
    """
    returns non-SysEx message as [channel, status, data1, data2, timeSinceLastMessage]
    """
    if not event:
        return None

    msg, deltaTimeinS = event

    if isSysex(msg):
        return None

    channel = (msg[0] & 0xF) + 1
    status = msg[0] & 0xF0

    num_bytes = len(msg)
    data1 = data2 = None

    if num_bytes >= 2:
        data1 = msg[1]
    if num_bytes >= 3:
        data2 = msg[2]

    return (channel, status, data1, data2, deltaTimeinS)



class MidiObject(object):
    """
    How to descriminate between Sysex & regular message?
    """
    def __init__(self, channel=0, status="cc", value=90, data=None):
        self.channel = channel
        self.status = status
        self.value = value
        self.data = data


class MidiObjectTrigger(MidiObject):
    def __init__(self, channel=0, status="cc", value=90, data=None, minActivationThreshold=1,
                 maxActivationThreshold=127):
        MidiObject.__init__(self, channel, status, value, data)
        self.minActivationThreshold = minActivationThreshold
        self.minActivationThreshold = maxActivationThreshold

class MidiAutoEngager(object):
    def __abs__(self, activation_message=None, enable_message=None, disable_message=None,
                timeout=0.5):
        self.activation_message = activation_message
        self.enable_message = enable_message
        self.disable_message = disable_message
        self.timeout = timeout



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

        if statusIsCC(status) and self.data1 == 93:
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
    # TODO: Register callback to input port: -> can probably set the call back to an internal class function
    midiInputPort.set_callback(MidiCCAutoEngage())

def run():
    midiInput = rtmidi.MidiIn()
    midiOutput = rtmidi.MidiOut()

    availableInputPorts = midiInput.get_ports()

    # create output port
    outputPort = midiOutput.open_virtual_port("RToutput2")

    inputPortName = 'RToutput1'
    inputPort = midiInput.open_port(availableInputPorts.index(inputPortName))

    inputActivationMessageValue = 90
    pedalActivated = False
    timeSincelastMsg = -1
    timeOfLastMsg = -1
    sendChannel = 1
    lastValidMessage = None


    while True:
        msg = inputPort.get_message()
        parsedMessage = decodeMessageIntoParts(msg)
        if pedalActivated:
            timeSincelastMsg = time.time() - timeOfLastMsg
            if timeSincelastMsg > 0.5 and lastValidMessage[3] < 20:
                outputPort.send_message([CONTROL_CHANGE | sendChannel, 94, 0])
                pedalActivated = False
                print("Deactivating AutoEngage")
        if parsedMessage:
            if statusIsCC(parsedMessage[1]) and parsedMessage[2] == inputActivationMessageValue:
                if not pedalActivated:
                    outputPort.send_message([CONTROL_CHANGE | sendChannel, 94, 127])
                    print("AutoEngage")
                pedalActivated = True
                timeOfLastMsg = time.time()
                lastValidMessage = parsedMessage
        time.sleep(0.01)

    del midiout


if __name__  =="__main__":
    messageTypes = ['noteOn', 'noteOff', 'PC', 'CC']
    parser = argparse.ArgumentParser(description='Midi Auto Engage/Disenage Program')

    parser.add_argument('-i', '--inputPort', dest='inputPortName',
                        default="",
                        help='Name of input Midi port, if empty, will use first one detected')

    parser.add_argument('-o', '--outputPort', dest='outputPortName',
                        default="RTMidiOut",
                        help='Name of output Midi port to create, default is RTMidiOut')

    parser.add_argument('-ch', dest='inputChannel',
                        default=1,
                        metavar="[0,15]",
                        choices=range(0,16),
                        type=int,
                        help="Select input channel for triggering message")

    parser.add_argument('-s', dest='inputStatus',
                        default='noteOn',
                        metavar="[noteOn, noteOff, PC, CC]",
                        choices=messageTypes,
                        type=str,
                        help="Select input message type")

    """
    Configure:
    
    # trigger message:
    input->channel
    input->type {note_on,note_off,program_change,control_change}
    input->value # value of the message type
    
    # OPTIONAL trigger enable message (sends message on trigger)
    trigger_enable->channel
    trigger_enable->type {note_on,note_off,program_change,control_change}
    trigger_enable->value # value of the message type
    trigger_enable->data # only for control_change really, {default=127, range [1, 127]}
    
    # minimum value on which to trigger Enable Action (do not activate if first value below this)
    trigger_enable->minActivationThreshold {default=1, range [1,127] -> only for input->type==control_change}
     
    # max value on which to trigger Enable Action (do not activate if first value above this)
    trigger_enable->maxActivationThreshold {default=127, range [1,127] -> only for input->type==control_change} 

    
    trigger_disable->channel
    trigger_disable->type {note_on,note_off,program_change,control_change}
    trigger_disable->value # value of the message type
    trigger_disable->data # only for control_change really, {default=127, range [1, 127]}
    
    # minimum value on which to trigger Disable Action (do not deactivate if last value below this)
    trigger_disable->minActivationThreshold {default=1, range [1,127] -> only for input->type==control_change}
     
    # max value on which to trigger Disable Action (do not deactivate if last value above this)
    trigger_disable->maxActivationThreshold {default=127, range [1,127] -> only for input->type==control_change} 
    
    trigger_timeout {s to wait on non-activity before sending disable message, default 0.5}
    
    Need to validate that trigger_enable and trigger_disable objects are not the same
    Can create enable and disable objects from a common object
    
    ^^ build an AutoEngage object per requested config.
    AutoEngage{
        activate_message,
        enable_message,
        disable_message,
        timeout
    }
    
    """


    args = parser.parse_args()
    run()
    # del midiout

