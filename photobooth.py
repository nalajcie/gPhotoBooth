#!/usr/bin/env python
# enc: utf-8

import sys
import argparse
import logging

from photobooth import controller, camera



### setup global logger

logger = logging.getLogger('photobooth')

file_log_handler = logging.FileHandler('photobooth.log')
formatter = logging.Formatter('%(asctime)s [%(module)s] %(levelname)s %(message)s')
file_log_handler.setFormatter(formatter)
logger.addHandler(file_log_handler)

stdout_log_handler = logging.StreamHandler(sys.stdout)
#stdout_log_handler.setLevel(logging.WARN)
stdout_log_handler.setLevel(logging.DEBUG)
logger.addHandler(stdout_log_handler)

logger.setLevel(logging.DEBUG)

### CONFGIURATION ###
# this is the default configuration, some values can be changed using commandline parameters
default_config = {
    # display-related consts
    'screen_width': 1280,
    'screen_height': 800,
    'fullscreen': 0,
    'fps': 30,

    # controller-related vars
    'save_path': '.',
    'flip_preview': True,
    'initial_countdown_secs': 3,
    'midphoto_countdown_secs': 3,
    'image_display_secs': 2,

    # whole screen drawing-related consts
    'font_color': (210, 210, 210),
    'font_size': 142,
    'back_color': (230, 180, 40),
    'back_image': 'assets/pixelbackground_02_by_kara1984.jpg',

    'left_margin': 20,
    'left_offset': 48/3,
    'bottom_margin': 20,
    'top_margin': 20,
}




class Config(object):
    """Change dictionary to object attributes."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return str(self.__dict__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("save_path", help="Location to save images")
    parser.add_argument("-d", "--dummy",        help="Use dummy camera instead of GPhoto interface", action="store_true")
    parser.add_argument("-f", "--fullscreen",   help="Use fullscreen mode", action="store_true")
    parser.add_argument("-p", "--print_count",  help="Set number of copies to print", type=int, default=0)
    parser.add_argument("-P", "--printer",      help="Set printer to use", default=None)
    parser.add_argument("-u", "--upload_to",    help="Url to upload images to")
    args = parser.parse_args()

    logger.info("Args were: %s", args)
    conf = Config(**default_config)
    conf.fullscreen = args.fullscreen
    conf.save_path = args.save_path
    logger.info("Full configuration: %s", conf)

    try:
        if args.dummy:
            cam = camera.DummyCamera()
        else:
            cam = cam.GPhotoCamera()
    except ValueError, e:
        logger.exception("Camera could not be initialised, exiting!")
        sys.exit(-1)

    booth = controller.PhotoBoothController(cam, conf)
    try:
        booth.run()
    except Exception:
        logger.exception("Unhandled exception!")
        cam.close()
        sys.exit(-1)
    finally:
        cam.close()
        logger.info("Finished successfully!")
