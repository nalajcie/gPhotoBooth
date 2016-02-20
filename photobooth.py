#!/usr/bin/env python
# enc: utf-8
""" Photobooth main file """

import sys
import argparse
import logging

from photobooth import controller, camera, config, printer



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
    parser.add_argument("save_path", help="Location to save images")
    parser.add_argument("-d", "--dummy", help="Use dummy camera instead of GPhoto interface", action="store_true")
    parser.add_argument("-D", "--debug", help="Use debug configuration for easier development", action="store_true")
    parser.add_argument("-f", "--fullscreen", help="Use fullscreen mode", action="store_true")
    parser.add_argument("-P", "--printer", help="Use Thermal printer (default: NullPrinter)", action="store_true")
    parser.add_argument("-u", "--upload", help="Upload images to Tumblr", action="store_true")
    args = parser.parse_args()

    if args.debug:
        conf = config.Config.debug()
    else:
        conf = config.Config.default()

    conf.fullscreen |= args.fullscreen
    conf.save_path = args.save_path
    conf.thermal_printer |= args.printer
    conf.dummy_camera |= args.dummy
    conf.upload |= args.upload

    if conf.upload:
        conf.read_tumblr_config()

    return conf


def main():
    """ main function """
    logger = setup_logger()
    conf = parse_args()
    logger.info("Full configuration: %s", conf)

    # setup CAMERA
    try:
        if conf.dummy_camera:
            cam = camera.DummyCamera()
        else:
            cam = camera.GPhotoCamera()
    except ValueError:
        logger.exception("Camera could not be initialised, exiting!")
        sys.exit(-1)

    # setup PRINTER
    if conf.thermal_printer:
        printer_inst = printer.ThermalPrinter()
    else:
        printer_inst = printer.NullPrinter()

    try:
        booth = controller.PhotoBoothController(conf, cam, printer_inst)
        booth.run()
    except Exception:
        logger.exception("Unhandled exception!")
        cam.close()
        sys.exit(-1)
    finally:
        cam.close()
        logger.info("Finished successfully!")

if __name__ == '__main__':
    main()
