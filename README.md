# gPhotoBooth
[![Code Climate](https://codeclimate.com/github/nalajcie/gPhotoBooth/badges/gpa.svg)](https://codeclimate.com/github/nalajcie/gPhotoBooth)
[![Codacy Badge](https://api.codacy.com/project/badge/grade/9daa6d6c79d74de3b6708c928bc3c723)](https://www.codacy.com/app/nalajcie/gPhotoBooth)
## About
Photobooth using any camera supported with libgphoto2. Using any other camera should be as easy as providing custom impelmentation of `Camera` class.
Features:
* robust live preview (about 18-20 FPS on laptop, 10-12 FPS (with libturbo hack) on Pi)
* fancy UI with shutter animation
* automatic GIF creation
* uploading GIFs to tumblr
* uploading full-size images to Dropbox (and share link via tumblr)
* peripherials: controlling via external led pushbutton, controlling lights
* printing using Thermal Printer

## Prereqisities
Specific commands are for ubuntu/debian based systems.

1. Fetch local submodules
  ```bash
  git submodule sync
  git submodule update
  ```

2. python modules required
  ```bash
  sudo apt-get install imagemagick          # for creating GIFs to upload
  sudo apt-get install python-pygame        # for display
  sudo apt-get install python-yaml          # for parsing config files
  sudo easy_install local_modules/pytumblr  # for uploading to tumblr
  ```

3. Dropbox SDK for full images uploading
  ```bash
  wget https://www.dropbox.com/developers/downloads/sdks/core/python/dropbox-python-sdk-2.2.0.zip
  unzip dropbox-python-sdk-2.2.0.zip
  cd dropbox-python-sdk-2.2.0
  sudo python setup.py install
  ```
  TODO: add info how to get authorization token for Dropbox

4. (for using real camera) libgphoto2 + gPhoto2 for troubleshooting
  ```bash
  sudo apt-get install libgphoto2-6 gphoto2
  ```

5. disable system services grabbing gphoto2. For Pi comment out (using '#') the lines in this file:
  ``` bash
  sudo vim /usr/share/dbus-1/services/org.gtk.Private.GPhoto2VolumeMonitor.service
  ```

6. install WiringPi and Python bindings (for now You have to use my fork which has wiringPiISR function fixed):
  ```bash
  sudo apt-get install wiringpi
  git clone https://github.com/nalajcie/WiringPi2-Python.git
  cd WiringPi2-Python
  git submodule init && git submodule updated
  ./build    # will also install python lib system-wide using sudo
  ```

7. libjpegturbo hack on Raspberry Pi
  pygame uses libSDL, which is linked against `libjpeg.so.8`. On RPi there is only `libjpegturbo.so.6.2` prebuilt. 
  If You rebuild it locally and use `LD_LIBRARY_PATH`, you will experience vast improvement in JPEG reading.

  Because live view is in fact a series of JPEGs, this will result in huge FPS difference (10-12 FPS instead of 2-4).

  TODO: include detailed steps to rebuild libjpegturbo on Pi.

## Configuration
### Configuration format
Configuration is stored in single YAML file. The default configuration is in `events/template/config.yaml`.
Default config file is always read first, then the "event" config file overrides the defaults.

### Event configuration
For creating new "event" (photo session), create the event directory, copy default config file and edit it:
```bash
cp -r events/template events/event_name
vim events/event_name/config.yaml
```

### Tumblr
For uploading posts to tumblr You will need an API key. For doing so
1. You need to register to tumblr
2. You need to register an app (any name fits, only You will be using it anyway)
  It can be done at: https://www.tumblr.com/oauth/register
3. Go to https://api.tumblr.com/console/calls/user/info and provide Your consumer key/secret
4. Copy `token_key` and `token_secret` to YAML config file.


## Running
### Notes
* appliaction shoud be run in X server environment. Using framebuffer is possible but You have to disable double-buffering in code.
* using hardware PWM (for dimming LED pushbutton) requires superuser privileges on Raspberry Pi (on other platforms it's not implemented)
* this is work-in-progress, bear in mind that the code may change quicker then the README :)

### Examples
1. gPhoto2 Live view demo (for testing if Your camera works with gPhoto2) - and other scripts in @dev@ directory
  ```bash
  ./dev/preview-threaded.py
  ```

2. Photobooth application
  ```bash
  cp -r events/template events/tmp
  ./photobooth.py events/tmp
  ```

3. Photobooth application with camera emulation (no gPhoto2 camera attached)
  ```bash
  ./photobooth.py . -d
  ```

4. Note: for dimming button functionality You have to run it with sudo (hardware PWM needs this). You need to
setup necessary ENV variables (or use properly env\_keep/env\_reset in /etc/sudoers)
  ```bash
  sudo DISPLAY=:0 python photobooth.py events/tmp
  ```
  If You do not need dimming button but still want to have "normal button" and launch the app, instruct
  wiringPi to use non-root mode:
  ```bash
  export WIRINGPI_GPIOMEM=1
  ```

## Hardware setup
For now just the schematics of the photobooth, I will add more info when it will be finished.

Note: the software runs fine on any linux computer without additonal hardware.
Moreover, You can attach Thermal Printer using USB\<-\>UART interface.

![Connection schematics](/doc/wiring_bb.png?raw=true "Connection schematics")

