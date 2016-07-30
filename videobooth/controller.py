# encoding: utf-8
""" Controlls the logic flow around the whole application """
import videobooth.model as model
import videobooth.picam as picam
import platform_devs
#from photobooth.printer import PrinterProxy

from threading import Thread
from Queue import Queue

import multiprocessing
import time


import logging
logger = logging.getLogger('videobooth.%s' % __name__)

class VideoBoothController(object):
    """ controlling the logic flow around the whole application """

    def __init__(self, config):
        self.conf = config
        self.cam = picam.PiCam(config)
        self.cam.start()
        #self.printer = PrinterProxy(self.conf)

        # platform and picam
        logger.info("PLATFORM: %s" % platform_devs.running_platform)
        platform_devs.platform_init()
        self.cam.start()

        # peripherials
        self.button = platform_devs.Button()
        self.button_pressed = False
        self.lights = platform_devs.Lights(self.conf['devices']['lights_external'])
        self.button.register_callback(self.button_callback)


        # model at the end (may want to show something already
        self.is_running = False
        self.model = model.VideoBoothModel(self)


    def run(self):
        """Main loop"""

        self.is_running = True
        self.button.start()

        while self.is_running:
            button_pressed = self.process_events()
            # detecting LONG PRESS for poweroff:
            self.button.update_state()

            self.model.update(button_pressed)
            # TODO: polling/fps instead of this?
            time.sleep(0.3)

        self.quit()

    def __del__(self):
        self.cam.stop()
        platform_devs.platform_deinit()

    def quit(self):
        self.is_running = False
        if self.model:
            self.model.quit()
            self.model = None

        self.lights.pause()
        self.cam.stop()

    def button_callback(self):
        self.button_pressed = True

    def process_events(self):
        button_pressed = self.button_pressed
        self.button_pressed = False
        return button_pressed

    def get_external_ip(self):
        return platform_devs.get_ip()

    def set_info_text(self, text_lines, big=False):
        if isinstance(text_lines, list):
            text = "\\n".join(text_lines)
        else:
            text = text_lines
        if big:
            self.cam.set_text(text, pt=140, layout_align="center,center")
        else:
            self.cam.set_text(text, pt=60)

    def set_rec_text(self, time):
        text = "\\n".join([u"●REC", time])
        self.cam.set_text(text, layout_align="top,right", horizontal_margin=30, vertical_margin=30, color="ff0000")


    def start_recording(self):
        self.cam.start_recording()

    def stop_recording(self):
        self.cam.stop_recording()

