import time
import argparse
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


class MidiObject(object):
    def __init__(self, channel=0, status="cc", value=90, data=None):
        self.channel = channel
        self.status = status
        self.value = value
        self.data = data


class MidiObjectTrigger(MidiObject):
    def __init__(self, channel=0, status="cc", value=90, data=None, minActivationThreshold=1,
                 maxActivationThreshold=127):
        self.__init__(channel, status, value, data)
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
    parser = argparse.ArgumentParser(description='Midi Auto Engage/Disenage Program')

    parser.add_argument('-i', dest='inputPortName',
                        default="",
                        help='Name of input Midi port, if empty, will use first one detected')

    parser.add_argument('-o', dest='outputPortName',
                        default="RTMidiOut",
                        help='Name of output Midi port to create, default is RTMidiOut')

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

    parser.add_argument('-t', dest='inputs',
                        nargs="+",
                        default="",
                        help='Directory, list of directories, files, list of files, or mixed to scan for impk files')

    parser.add_argument('-k', dest='output',
                        default="",
                        help='output csv file')

    parser.add_argument('--walk',
                        action='store_true',
                        dest="walk",
                        default=False,
                        help="walk within directories")


    args = parser.parse_args()
    midiout = run()
    del midiout

