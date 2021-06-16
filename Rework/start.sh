#!/bin/bash
# /home/pi/.config/autostart/myautostart.sh
# this will not do anything unless called by a .desktop file

env sleep 10
sudo pigpiod
python3 JoyRead.py