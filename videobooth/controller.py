# encoding: utf-8
""" Controlls the logic flow around the whole application """
import platform_devs
import videobooth.model as model
import videobooth.picam as picam
from videobooth.upload import UploadProxy
from common.printer import PrinterProxy

import time


import logging
logger = logging.getLogger('videobooth.%s' % __name__)

class VideoBoothController(object):
    """ controlling the logic flow around the whole application """

    def __init__(self, config):
        self.conf = config
        self.cam = picam.PiCam(config)
        self.printer = PrinterProxy(self.conf)

        # platform and picam
        logger.info("PLATFORM: %s" % platform_devs.running_platform)
        platform_devs.platform_init()
        self.cam.start()

        # peripherials
        self.button = platform_devs.Button()
        self.button_pressed = False
        self.lights = platform_devs.Lights(self.conf['devices']['lights_external'])
        self.button.register_callback(self.button_callback)

        # uploader
        self.upload = UploadProxy(self.conf)

        # model
        self.is_running = False
        self.model = model.VideoBoothModel(self)


    def run(self):
        """Main loop"""

        self.is_running = True
        self.button.start()
        self.upload.start()

        while self.is_running:
            # if camera stopped working, exit
            if not self.cam.update():
                break

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

    def set_info_text(self, text_arg, big=False, color="ffffff"):
        text = text_arg.strip().replace("\n", "\\n")
        if big:
            self.cam.set_text(text, pt=140, layout_align="center,center", color=color)
        else:
            self.cam.set_text(text, pt=60, color=color)

    def set_rec_text(self, time):
        text = "\\n".join([u"●REC", time])
        self.cam.set_text(text, layout_align="top,right", horizontal_margin=30, vertical_margin=30, color="ff0000")


    def start_recording(self):
        self.cam.start_recording()

    def stop_recording(self):
        self.cam.stop_recording()

    def check_recording_state(self, post_res):
        if not self.cam.is_recording():
            new_movie_fn = self.cam.last_rec_filename()
            logger.info("NEW MOVIE: %s", new_movie_fn)

            (upload_url, frontend_url) = post_res or ("", "")
            self.upload.async_process(upload_url, new_movie_fn)

            if len(frontend_url) > 0:
                logger.info("frontend URL: %s", frontend_url)
                self.printer.print_video(frontend_url)
            return True

        return False
