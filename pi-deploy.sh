#!/bin/bash

scp photobooth/platform/*.py pi@photobooth.local:src/gPhotoBooth/photobooth/platform/
scp photobooth/*.py pi@photobooth.local:src/gPhotoBooth/photobooth/
#scp assets/* pi@photobooth.local:src/gPhotoBooth/assets/
scp msg/* pi@photobooth.local:src/gPhotoBooth/msg/
scp photobooth.py pi@photobooth.local:src/gPhotoBooth/
#scp events/template/config.yaml pi@photobooth.local:src/gPhotoBooth/events/template/
scp events/red_guardian/config.yaml pi@photobooth.local:src/gPhotoBooth/events/xxx/


