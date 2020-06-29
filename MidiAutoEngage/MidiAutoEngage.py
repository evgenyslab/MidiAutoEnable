import time
import argparse
import rtmidi
from rtmidi.midiconstants import *

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

__charStatusToCode = {
    'pc': PROGRAM_CHANGE,
    'programchange': PROGRAM_CHANGE,
    'program change': PROGRAM_CHANGE,
    'program_change': PROGRAM_CHANGE,
    'cc': CONTROL_CHANGE,
    'controlchange': CONTROL_CHANGE,
    'control change': CONTROL_CHANGE,
    'control_change': CONTROL_CHANGE,
    'on': NOTE_ON,
    'noteon': NOTE_ON,
    'note on': NOTE_ON,
    'note_on': NOTE_ON,
    'off': NOTE_OFF,
    'noteoff': NOTE_OFF,
    'note off': NOTE_OFF,
    'note_off': NOTE_OFF,
}

def charStatusToCode(status=""):
    return __charStatusToCode[status.lower()]


def generateMidiMessage(status, data1=None, data2=None, ch=None):
        """Generate Midi Message."""
        msg = [(status & 0xF0) | ((ch if ch else 1) - 1 & 0xF)]

        if data1 is not None:
            msg.append(data1 & 0x7F)

            if data2 is not None:
                msg.append(data2 & 0x7F)

        return msg




def doMessagesMatch(msgA=None, msgB=None):
    try:
        minMessageLength = min([len(msgA), len(msgB)])
        return msgA[:minMessageLength] == msgB[:minMessageLength]
    except Exception as e:
        print(e)

def run():
    midiInput = rtmidi.MidiIn()
    midiOutput = rtmidi.MidiOut()

    availableInputPorts = midiInput.get_ports()

    # create output port
    outputPort = midiOutput.open_virtual_port("RToutput2")

    inputPortName = 'RToutput1'
    while inputPortName not in availableInputPorts:
        time.sleep(0.5)
        availableInputPorts = midiInput.get_ports()

    inputPort = midiInput.open_port(availableInputPorts.index(inputPortName))

    inputActivationMessageChannel = 2
    inputActivationMessageStatus = CONTROL_CHANGE
    inputActivationMessageValue = 90
    autoEngageMessageChannel = 2
    autoEngageMessageStatus = CONTROL_CHANGE
    autoEngageMessageValue = 94
    autoDisengageMessageStatus = NOTE_OFF if autoEngageMessageStatus == NOTE_ON else autoEngageMessageStatus
    autoDisenageLowThreshold = 0
    autoDisenageHighThreshold = 20
    pedalActivated = False
    timeSincelastMsg = -1
    timeOfLastMsg = -1
    lastValidMessage = None

    activationMessage = generateMidiMessage(inputActivationMessageStatus, data1=inputActivationMessageValue,
                                            ch=inputActivationMessageChannel)

    enableMessage = generateMidiMessage(autoEngageMessageStatus, data1=autoEngageMessageValue,
                                        data2=127, ch=autoEngageMessageChannel)
    disableMessage = generateMidiMessage(autoDisengageMessageStatus, data1=autoEngageMessageValue,
                                        data2=0, ch=autoEngageMessageChannel)

    while True:
        msg = inputPort.get_message()
        # check timout:
        if pedalActivated:
            timeSincelastMsg = time.time() - timeOfLastMsg
            if timeSincelastMsg > 0.5 and \
                    (autoDisenageLowThreshold < lastValidMessage[2] < autoDisenageHighThreshold):
                outputPort.send_message(disableMessage)
                pedalActivated = False
                print("Deactivating AutoEngage")

        # decode & check msg filteR:
        if msg:
            if doMessagesMatch(activationMessage, msg[0]):
                if not pedalActivated:
                    outputPort.send_message(enableMessage)
                    print("AutoEngage")
                pedalActivated = True
                timeOfLastMsg = time.time()
                lastValidMessage = msg[0]
            time.sleep(0.01)
        """
        TODO: if the port is closed externally, this program has no knowledge, there should be
        testing done by querying availble ports...
        """

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

    parser.add_argument('-c', '--inputActivationChannel',
                        dest='inputActivationChannel',
                        default=1,
                        metavar="[0,15]",
                        choices=range(0,16),
                        type=int,
                        help="Select input channel for triggering message")

    parser.add_argument('-s', '--inputActivationStatus',
                        dest='inputActivationStatus',
                        default='noteOn',
                        metavar="[noteOn, noteOff, PC, CC]",
                        choices=messageTypes,
                        type=str,
                        help="Select input message type")

    parser.add_argument('-v', dest='inputActivationValue',
                        default=90,
                        type=int,
                        choices=range(0,128),
                        help="Select input activation message value")

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

