# Usb_to_ppm
Convert USB HOTAS events into PPM signals

Allows the user to create signals applicable to all PPM recivers. Using a Futaba (or similar) RC-transmitter, you can attache the RasperryPi with a trainercord (or a just two wires) to then allow you to control what is transmitted.

## Usage
Requires PIGPIOD for the raspberry and inputs.py (available on PIP)

Simply start the python program with the USB devices connected. If it is the first time running the program then you will be promted in the terminal to select the correct devices.
The program will then start listening and outputting a signal, hit ENTER/RETURN to kill the program.

If you add a second argument to the run command you will be presented with a GUI that show the values read by the program. This will not output a signal

Note: This is setup for the X-55 HOTAS system, you might have to change event codes for your joystick to work. This can be done on line 27.
