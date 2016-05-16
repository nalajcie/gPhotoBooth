#!/bin/bash

scp photobooth/platform/*.py pi@raspberrypi.local:src/gPhotoBooth/photobooth/platform/
scp photobooth/*.py pi@raspberrypi.local:src/gPhotoBooth/photobooth/
#scp assets/* pi@raspberrypi.local:src/gPhotoBooth/assets/
scp msg/* pi@raspberrypi.local:src/gPhotoBooth/msg/
scp photobooth.py pi@raspberrypi.local:src/gPhotoBooth/
#scp events/template/config.yaml pi@raspberrypi.local:src/gPhotoBooth/events/template/
scp events/red_guardian/config.yaml pi@raspberrypi.local:src/gPhotoBooth/events/xxx/


