#!/bin/bash

scp photobooth/platform/*.py pi@raspberrypi.local:src/gPhotoBooth/photobooth/platform/
scp photobooth/*.py pi@raspberrypi.local:src/gPhotoBooth/photobooth/
scp photobooth.py pi@raspberrypi.local:src/gPhotoBooth/
scp events/template/config.yaml pi@raspberrypi.local:src/gPhotoBooth/events/template/
scp events/pi/config.yaml pi@raspberrypi.local:src/gPhotoBooth/events/xxx/


