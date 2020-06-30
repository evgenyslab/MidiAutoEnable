from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_ON, NOTE_OFF, PROGRAM_CHANGE)

"""
Midi Utilities

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

def getStatusAsCodeFromStr(status=""):
    try:
        return __charStatusToCode[status.lower()]
    except KeyError as e:
        pass


def generateMidiMessage(status, data1=None, data2=None, ch=None):
    """Generate Midi Message."""
    msg = [(status & 0xF0) | ((ch if ch else 1) - 1 & 0xF)]

    if data1 is not None:
        msg.append(data1 & 0x7F)

        if data2 is not None:
            msg.append(data2 & 0x7F)

    return msg