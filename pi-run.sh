#!/bin/bash
ssh pi@photobooth.local "sudo killall python; cd src/gPhotoBooth; sudo DISPLAY=:0 LD_LIBRARY_PATH=/home/pi/turbo/optimized/lib/ python ./photobooth.py -f events/xxx"

