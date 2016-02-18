#!/usr/bin/env python
# enc: utf-8

import sys
import argparse
import logging

from photobooth import controller, camera, config, printer


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("save_path", help="Location to save images")
    parser.add_argument("-d", "--dummy",        help="Use dummy camera instead of GPhoto interface", action="store_true")
    parser.add_argument("-D", "--debug",        help="Use debug configuration for easier development", action="store_true")
    parser.add_argument("-f", "--fullscreen",   help="Use fullscreen mode", action="store_true")
    parser.add_argument("-P", "--printer",      help="Use Thermal printer (default: NullPrinter)", action="store_true")
    parser.add_argument("-u", "--upload",       help="Upload images to Tumblr", action="store_true")
    args = parser.parse_args()

    logger.info("Args were: %s", args)
    if args.debug:
        conf = config.Config.debug()
    else:
        conf = config.Config.default()

    conf.fullscreen = args.fullscreen
    conf.save_path = args.save_path
    conf.thermal_printer = args.printer
    if args.upload or config.upload:
        conf.upload = True
        conf.read_tumblr_config()
    logger.info("Full configuration: %s", conf)

    # setup CAMERA
    try:
        if args.dummy:
            cam = camera.DummyCamera()
        else:
            cam = camera.GPhotoCamera()
    except ValueError, e:
        logger.exception("Camera could not be initialised, exiting!")
        sys.exit(-1)

    # setup PRINTER
    if conf.thermal_printer:
        printer = printer.ThermalPrinter()
    else:
        printer = printer.NullPrinter()

    try:
        booth = controller.PhotoBoothController(conf, cam, printer)
        booth.run()
    except Exception:
        logger.exception("Unhandled exception!")
        cam.close()
        sys.exit(-1)
    finally:
        cam.close()
        logger.info("Finished successfully!")
