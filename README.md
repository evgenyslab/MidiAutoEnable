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