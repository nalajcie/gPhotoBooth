# gPhotoBooth
## About
Photobooth using any camera supported with libgphoto2. Using any other camera should be as easy as providing custom impelmentation of `Camera` class.

## Prereqisities
Specific commands are for ubuntu/debian based systems.

1. Fetch local submodules
  ```bash
  ~$ git submodule sync
  ~$ git submodule update
  ```

2. python pygame
  ```bash
  ~$ sudo apt-get install python-pygame
  ```

3. (for using real camera) libgphoto2 + gPhoto2 for troubleshooting
  ```bash
  ~$ sudo apt-get install libgphoto2-6
  ```

## Configuration
TODO
For now configuration is hardcoded at the beginning of photobooth.py or provided as commandline params (see usage).

## Running
1. gPhoto2 Live view demo (for testing if Your camera works with gPhoto2)
  ```bash
  ~$ ./preview.py
  ```

2. Photobooth application
  ```bash
  ~$ ./photobooth.py .
  ```

3. Photobooth application with camera emulation (no gPhoto2 camera attached)
  ```bash
  ~$ ./photobooth.py . -d
  ```
