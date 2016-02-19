# gPhotoBooth
## About
Photobooth using any camera supported with libgphoto2. Using any other camera should be as easy as providing custom impelmentation of `Camera` class.

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

3. (for using real camera) libgphoto2 + gPhoto2 for troubleshooting
  ```bash
  sudo apt-get install libgphoto2-6
  ```

4. disabling system services grabbing gphoto2. For Pi comment out (using '#') the lines in this file:
  ``` bash
  sudo vim /usr/share/dbus-1/services/org.gtk.Private.GPhoto2VolumeMonitor.service
  ```

5. install WiringPi and Python bindings (for now You have to use my fork which has wiringPiISR function fixed):
  ```bash
  sudo apt-get install wiringpi
  git clone https://github.com/nalajcie/WiringPi2-Python.git
  cd WiringPi2-Python
  git submodule init && git submodule updated
  ./build    # will also install python lib system-wide using sudo
  ```

## Configuration
For now configuration is hardcoded in photobooth/config.py and/or provided as commandline params (see usage).
TODO: create neat yaml configuration file

## Running
### Notes
* appliaction shoud be run in X server environment. Using framebuffer is possible but You have to disable double-buffering in code.
* using hardware PWM (for dimming LED pushbutton) requires superuser privileges on Raspberry Pi (on other platforms it's not implemented)
* this is work-in-progress, bear in mind that the code may change quicker then the README :)

### Examples
1. gPhoto2 Live view demo (for testing if Your camera works with gPhoto2)
  ```bash
  ./preview.py
  ```

2. Photobooth application
  ```bash
  ./photobooth.py .
  ```

3. Photobooth application with camera emulation (no gPhoto2 camera attached)
  ```bash
  ./photobooth.py . -d
  ```

4. Note: for dimming button functionality You have to run it with sudo (hardware PWM needs this). You need to
setup necessary ENV variables (or use properly env\_keep/env\_reset in /etc/sudoers)
  ```bash
  sudo DISPLAY=:0 python photobooth.py -d tmp/
  ```
  If You do not need dimming button but still want to have "normal button" and launch the app, instruct
  wiringPi to use non-root mode:
  ```bash
  export WIRINGPI_GPIOMEM=1
  ```
