#!/bin/bash
ssh pi@raspberrypi.local "killall python; cd src/gPhotoBooth; DISPLAY=:0 LD_LIBRARY_PATH=/home/pi/turbo/optimized/lib/ python ./photobooth.py -f xxx"

