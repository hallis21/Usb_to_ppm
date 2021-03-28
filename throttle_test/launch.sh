#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home
sleep 5
sudo pigpiod
sleep 30
cd /home/pi/throttle_test
python3 PPM.py > log.txt
