# Python Midi Auto Engage 

This is a quick and simple python midi tool using python-RTMidi to create an auto-engaging
feature for host-midi functionality.

This project is inspired out of a specific use-case of midi-based expression control.

Specifically, when using a usb-midi expression controller to control the Wah in 
[Positive Grid's Bias](https://www.positivegrid.com/bias-fx/), it was desired to implement an 
auto-engage functionality that would enable the wah with the midi control messages 
that are mapped for the expression pedal. 

In practice, the expression control message was initially mapped in [Ableton](www.ableton.com)
to control two VST parameters, one mapped to 49-100% which controlled the enable/disable of the
wah pedal, while the second parameter was mapped to the actual wah actuator. 

This resulted in abrupt cut-out of the wah with a small pop whenever the pedal was set to 0 position.

Thus, to add a little smoothing action, this project introduces a little bit of midi sauce in the pipeline.

The idea herein is to read the control value for the wah actuation, and use the change in control to 
send a different midi message which will enable the pedal. The function will then maintain an internal
timeout counter that will count how long since the last pedal movement was recorded. Once the timeout 
is reached (maybe 400-600ms), then the `off` control will be sent to disable the wah pedal.

Initial testing resulted in much smoother engaging and disengaging of the wah controller in the Bias
software.

This project was inspired by the Axe-FX's functionality of auto-engaging expression parameters, and
thinking about how this functionality can be useful for midi controllers with limited expression inputs.

## Problem Setup

I wanted to use an expression pedal connected through a USB midi controller to control the wah sweep
on my Positive Grid Bias FX application running in Ableton, and simulatenously auto engage the wah block,
thus removing the need to have one expression pedal take up two expression ports on a midi controller 
(namely, avoid using the built in wah switch).

Expression -> Controller -> USB -> Ableton -> [vst] Bias

To implement a rough auto-engage function, the idea was to assign one Control Change message to the
expression pedal output, and provide some smart mapping in Ableton/Bias. The assigned expression 
controller CC value (i.e. 93) was mapped in Ableton to two different vst object parameters - one 
which will trigger the enabling/disabling of the wah, while the other will sweep the pedal.

**Note**: Bias can't receive Midi through ableton for some reason, so need to use parameter mapping

The first Ableton midi parameter was mapped to the chosen controller value and was set to a limited range 
of `[0.49, 1]` which mapped to the wah engage in bias TODO: add screenshots with arrows.

The second Ableton midi paramter was mapped to the chosen controller value, set to full range `[0, 1]` and
mapped to Bias sweep. TODO: add screen shot with arrows

This configuration disabled the wah block in bias when Ableton received a '0' value CC message from the 
midi interface, since it mapped to 0.49 in the first parameter that caused Bias to shut off the Wah block.

This sudden off behaviour resulted in a non-pleasant cutout of the wah block in the audio chain, and 
at all times resulted in cut-outs when the expression pedal was set to toe-up position, which interrupts 
regular wah usage.

This problem could be remedied by implementation of a timeout-based wah shutoff (the auto-engage functionally
is generally fine to trigger enabling on first detected change in pedal position).

## Proposed Solution

The proposed solution would implement a small piece of python code that would listen on the midi input port
from the midi controller, isolate the designed expression controller value, and then send a secondary (different)
midi message to enable the wah block, and a third message to disable the wah block once the pedal has stopped
moving for a period of time.

# Usage

## Requirements

- python3
- python3-pip
- virtualenvironments

## Usage

Firstly, create a local virtual environment to run the project:
```bash
# create environment in local .venv folder:
virtualenv -p "which python3" .venv
# activate the environment:
source ./venv/bin/activate
# install pip requirements:
pip install -r requirements.txt
```

Then, to run the application:
```bash
python MidiAutoEngage [parameters or --help]
```


# TODO:

- [ ] screenshot of initial ableton configuration
- [ ] mixed screencap video + wah video of operation of initial ableton configuration
- [ ] convert video to gif
- [ ] mixed screencap video + wah video of operation with MidiAutoEngage
- [ ] convert video to gif