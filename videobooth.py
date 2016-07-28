#!/usr/bin/env python
# encoding: utf-8
""" Videobooth main file """

import sys
import argparse
import logging
import importlib

from common import config
from videobooth import controller



def setup_logger():
    """ setup global logger """
    logger = logging.getLogger('videobooth')

    file_log_handler = logging.FileHandler('videobooth.log')
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
    #TODO
    args = parser.parse_args()

    conf = config.read_config(args.event_dir)

    conf['event_dir'] = args.event_dir
    return conf


def main():
    """ main function """
    logger = setup_logger()
    conf = parse_args()
    logger.info("Full configuration: %s", conf)
    finished_normally = False

    try:
        booth = None # guard against exception in constructor
        booth = controller.VideoBoothController(conf)
        booth.run()
        finished_normally = True
    except Exception:
        logger.exception("MAIN: Unhandled exception!")
        if booth:
            booth.quit()
            booth = None
    finally:
        if booth:
            booth.quit()

        logger.info("EXIT")
        if not finished_normally:
            logger.info("exited with error code: 1")
            sys.exit(1)

if __name__ == '__main__':
    main()
