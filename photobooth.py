#!/usr/bin/env python
# encoding: utf-8
""" Photobooth main file """

import sys
import argparse
import logging
import importlib

from photobooth import controller, config



def setup_logger():
    """ setup global logger """
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
    return logger


def parse_args():
    """ commandline args parsing and config reading """
    parser = argparse.ArgumentParser()
    parser.add_argument("event_dir", help="Event directory - place to read config and store images")
    parser.add_argument("-d", "--dummy", help="Force dummy camera instead of GPhoto interface", action="store_true")
    parser.add_argument("-D", "--debug", help="Use debug configuration for easier development", action="store_true")
    parser.add_argument("-f", "--fullscreen", help="Force fullscreen mode", action="store_true")
    parser.add_argument("-u", "--upload", help="Force images upload to Tumblr", action="store_true")
    parser.add_argument("-s", "--setup", help="Use this mode to setup the camera", action="store_true")
    args = parser.parse_args()

    conf = config.read_config(args.event_dir)

    conf['event_dir'] = args.event_dir
    if args.dummy:
        conf['camera']['driver'] = "DummyCamera"

    conf['display']['fullscreen'] |= args.fullscreen
    conf['control']['save_path'] = args.event_dir
    conf['upload']['enabled'] |= args.upload

    # TODO: how to make setup mode using pushbutton?
    if args.setup:
        conf['control']['idle_secs'] = 360
        conf['devices']['lights_default'] = conf['devices']['lights_full']

    return conf


def main():
    """ main function """
    logger = setup_logger()
    conf = parse_args()
    logger.info("Full configuration: %s", conf)

    # setup CAMERA
    # this is done here to be able to close the camera in case of any excepion
    try:
        # setup PRINTER
        camera_class = getattr(importlib.import_module("photobooth.camera"), conf['camera']['driver'])
        cam = camera_class()
    except ValueError:
        logger.exception("Camera could not be initialised, exiting!")
        sys.exit(-1)

    try:
        booth = controller.PhotoBoothController(conf, cam)
        booth.run()
    except Exception:
        logger.exception("MAIN: Unhandled exception!")
        if booth:
            booth.quit()
            booth = None
    finally:
        logger.error("MAIN: Finally: closing camera!")
        if booth:
            booth.quit()
        #cam.close()
        logger.info("Finished successfully!")

if __name__ == '__main__':
    main()
