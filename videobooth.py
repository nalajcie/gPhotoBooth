#!/usr/bin/env python
# encoding: utf-8
""" Videobooth main file """

import sys
import argparse
import logging
import pprint
import time

from common import config, webserver
from videobooth import controller
from platform_devs import get_ip



def setup_global_logger():
    """ setup global logger """
    logger = logging.getLogger()

    file_log_handler = logging.FileHandler('videobooth.log')
    formatter = logging.Formatter('%(asctime)s [%(module)s] %(levelname)s %(message)s')
    file_log_handler.setFormatter(formatter)
    logger.addHandler(file_log_handler)

    stdout_log_handler = logging.StreamHandler(sys.stdout)
#stdout_log_handler.setLevel(logging.WARN)
    stdout_log_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_log_handler)

    logger.setLevel(logging.DEBUG)

setup_global_logger()
logger = logging.getLogger('videobooth')


def parse_args():
    """ commandline args parsing and config reading """
    parser = argparse.ArgumentParser()
    parser.add_argument("event_dir", help="Event directory - place to read config")
    parser.add_argument("-w", "--webserver", help="Start webserver to serve videos locally", action="store_true")
    args = parser.parse_args()

    conf = config.read_config(args.event_dir, default_config=config.DEFAULT_CONFIG_FILE_VIDEO)

    conf['event_dir'] = args.event_dir
    conf['webserver']['enabled'] |= args.webserver
    return conf

def wait_for_ip(max_retries):
    """ waits indefinately for external IP """
    for retry in xrange(1, max_retries):
        ext_ip = get_ip()
        if len(ext_ip) > 0:
            break

        logger.info("(%d/%d) waiting for external IP", retry, max_retries)
        time.sleep(1)

    logger.info("EXT IP: %s", ext_ip)


def main():
    """ main function """
    conf = parse_args()
    logger.info("Full configuration: %s", pprint.pformat(conf))
    finished_normally = False
    booth = None # guard against exception in constructor

    wait_for_ip(conf['control']['get_ip_retries_cnt'])

    try:
        webserver.try_start_background(conf)
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
