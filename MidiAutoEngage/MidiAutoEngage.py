import time
import argparse
import rtmidi
from rtmidi.midiconstants import *
try:
    from MidiUtilities import *
except Exception as e:
    pass
try:
    from MidiAutoEngage.MidiUtilities import *
except Exception as e:
    pass

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



def charStatusToCode(status=""):
    return __charStatusToCode[status.lower()]



def doMessagesMatch(msgA=None, msgB=None):
    try:
        minMessageLength = min([len(msgA), len(msgB)])
        return msgA[:minMessageLength] == msgB[:minMessageLength]
    except Exception as e:
        print(e)

def run(args):
    midiInput = rtmidi.MidiIn()
    midiOutput = rtmidi.MidiOut()

    availableInputPorts = midiInput.get_ports()


    # create output port
    outputPort = midiOutput.open_virtual_port(args.outputPortName)



    if args.inputPortName and args.inputPortName in availableInputPorts:
        while args.inputPortName not in availableInputPorts:
            time.sleep(0.5)
            availableInputPorts = midiInput.get_ports()
        inputPort = midiInput.open_port(availableInputPorts.index(args.inputPortName))
    else:
        while len(availableInputPorts) == 0:
            time.sleep(0.5)
            availableInputPorts = midiInput.get_ports()
        inputPort = midiInput.open_port(0)




    inputActivationMessageChannel = args.inputActivationChannel
    inputActivationMessageStatus = args.inputActivationStatus
    inputActivationMessageValue = args.inputActivationValue
    autoEngageMessageChannel = args.triggerChannel
    autoEngageMessageStatus = args.triggerStatus
    autoEngageMessageValue = args.triggerValue
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
                    (autoDisenageLowThreshold <= lastValidMessage[2] <= autoDisenageHighThreshold):
                outputPort.send_message(disableMessage)
                pedalActivated = False
                print("Deactivating AutoEngage")

        # decode & check msg filter:
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

    parser.add_argument('-i', '--inputPort',
                        dest='inputPortName',
                        help='Name of input Midi port, if empty, will use first one detected')

    parser.add_argument('-o', '--outputPort',
                        dest='outputPortName',
                        default="RTMidiOut2",
                        help='Name of output Midi port to create, default is RTMidiOut')

    parser.add_argument('-c', '--inputActivationChannel',
                        dest='inputActivationChannel',
                        default=2,
                        metavar="[0,15]",
                        choices=range(0,16),
                        type=int,
                        help="Select input channel for triggering message")

    parser.add_argument('-s', '--inputActivationStatus',
                        dest='inputActivationStatus',
                        default='cc',
                        metavar="[noteOn, noteOff, PC, CC]",
                        choices=messageTypes,
                        type=str,
                        help="Select input message type")

    parser.add_argument('-v', '--inputActivationValue',
                        dest='inputActivationValue',
                        default=93,
                        type=int,
                        choices=range(0,128),
                        help="Select input activation message value")

    parser.add_argument('-t', '--triggerChannel',
                        dest='triggerChannel',
                        default=2,
                        metavar="[0,15]",
                        choices=range(0, 16),
                        type=int,
                        help="Select trigger channel")

    parser.add_argument('-g', '--triggerStatus',
                        dest='triggerStatus',
                        default='CC',
                        metavar="[noteOn, noteOff, PC, CC]",
                        choices=messageTypes,
                        type=str,
                        help="Select trigger message type")

    parser.add_argument('-u', '--triggerValue',
                        dest='triggerValue',
                        default=94,
                        type=int,
                        choices=range(0, 128),
                        help="Select trigger message value")


    args = parser.parse_args()
    # validate activation and trigger status
    try:
        args.inputActivationStatus = getStatusAsCodeFromStr(args.inputActivationStatus)
        args.triggerStatus = getStatusAsCodeFromStr(args.triggerStatus)
    except Exception as e:
        pass
    run(args)
    # del midiout

