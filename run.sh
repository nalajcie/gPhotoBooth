#!/bin/bash
# NOTE: for auto-start add this script to ~/.config/lxsession/LXDE-pi/autostart

cd ~/src/gPhotoBooth/
while :; do
    sudo DISPLAY=:0 LD_LIBRARY_PATH=/home/pi/turbo/optimized/lib/ python ./photobooth.py -f events/xxx
    EXIT_CODE=$?
    # shoo, zombie processes
    sudo killall python
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Exited normally, ending loop";
        break;
    fi
done
