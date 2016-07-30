#!/bin/bash
# NOTE: videobooth does not need X server, add this script to run in background in /etc/rc.local

cd /home/pi/src/gPhotoBooth/
while :; do
    sudo python ./videobooth.py events/video_test
    EXIT_CODE=$?
    # shoo, zombie processes
    sudo killall python
    sudo killall picam
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Exited normally, ending loop";
        break;
    fi
done
