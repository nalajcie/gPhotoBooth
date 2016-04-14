#!/bin/bash
# NOTE: for auto-start add this script to ~/.config/lxsession/LXDE-pi/autostart

cd ~/src/gPhotoBooth/
while :; do
    sudo DISPLAY=:0 LD_LIBRARY_PATH=/home/pi/turbo/optimized/lib/ python ./photobooth.py -s -f events/xxx
done
