# encoding: utf-8
""" Controlls the logic flow around the whole application """
import videobooth.model as model
import platform_devs
from photobooth.printer import PrinterProxy

from threading import Thread
from Queue import Queue

import multiprocessing
import subprocess
import time
import os
import io


import logging
logger = logging.getLogger('videobooth.%s' % __name__)

class VideoBoothController(object):
    """ controlling the logic flow around the whole application """

    def __init__(self, config):
        self.conf = config
        self.printer = PrinterProxy(self.conf)

        # platform and pygame
        logger.info("PLATFORM: %s" % platform_devs.running_platform)
        platform_devs.platform_init()
        self.spawn_picam()

        # peripherials
        self.button = platform_devs.Button()
        self.button_pressed = False
        self.lights = platform_devs.Lights(self.conf['devices']['lights_external'])
        self.button.register_callback(self.button_callback)

        # view and model
        self.is_running = False
        self.model = model.VideoBoothModel(self)

        # picam shortcuts
        self.hooks_dir = os.path.join(self.conf['picam']['workdir'], "hooks")
        self.last_text = ""

    def spawn_picam(self):
        # setup dirs
        if not os.path.exists(self.conf['picam']['workdir']):
            os.makedirs(self.conf['picam']['workdir'])
        if not os.path.exists(self.conf['picam']['archive_dir']):
            os.makedirs(self.conf['picam']['archive_dir'])

        for dirname in ["rec", "hooks", "state"]:
            realdir = os.path.join(self.conf['picam']['shmdir'], dirname)
            symname = os.path.join(self.conf['picam']['workdir'], dirname)
            if not os.path.exists(realdir):
                os.makedirs(realdir)

            # always regenerate symlinks
            if os.path.lexists(symname):
                os.remove(symname)
            os.symlink(realdir, symname)

        archive_symname = os.path.join(self.conf['picam']['workdir'], "rec/archive")
        if os.path.lexists(archive_symname):
            os.remove(archive_symname)
        os.symlink(self.conf['picam']['archive_dir'], archive_symname)

        # prepare command line
        args = [ self.conf['picam']['binary'] ]
        for (k, v) in self.conf['picam']['params'].iteritems():
            args.append("--" + k)
            if v != True:
                args.append(str(v))

        # spawn!
        logger.info("spawning PICAM: %s", args)
        subprocess.Popen(args, cwd=self.conf['picam']['workdir'])

    def kill_picam(self):
        cmd = [ 'killall', self.conf['picam']['binary'] ]
        logger.info("trying to kill PICAM: %s", cmd)
        subprocess.Popen(cmd)

    def __del__(self):
        self.kill_picam()
        platform_devs.platform_deinit()

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

    def quit(self):
        self.is_running = False
        if self.model:
            self.model.quit()
            self.model = None

        self.lights.pause()
        self.kill_picam()

    def button_callback(self):
        self.button_pressed = True

    def process_events(self):
        button_pressed = self.button_pressed
        self.button_pressed = False
        return button_pressed

    def set_info_text(self, text_lines, big=False):
        if isinstance(text_lines, list):
            text = "\\n".join(text_lines)
        else:
            text = text_lines
        if big:
            self.set_text(text, pt=140, layout_align="middle,middle")
        else:
            self.set_text(text, pt=60)

    def set_rec_text(self, time):
        text = "\\n".join([u"●REC", time])
        self.set_text(text, layout_align="top,right", horizontal_margin=30, vertical_margin=30, color="ff0000")


    def set_text(self, text, **kwargs):
        if self.last_text == text:
            return
        self.last_text = text
        params = {
                "text": text,
                "in_video": 0,
                "duration": 0,
                "pt": 40,
                }
        for (k, v) in kwargs.iteritems():
            params[k] = v
        param_strings = [ u"=".join([unicode(k), unicode(v)]) for (k, v) in params.iteritems() ]
        logger.debug("SUBTITLE: %s", param_strings)

        dest_file = os.path.join(self.hooks_dir, "subtitle")
        with io.open(dest_file, "w", encoding="utf-8") as f:
            f.write(u"\n".join(param_strings))

    def start_recording(self):
        dest_file = os.path.join(self.hooks_dir, "start_record")
        with io.open(dest_file, "w") as f:
            f.write(u"")

    def stop_recording(self):
        dest_file = os.path.join(self.hooks_dir, "stop_record")
        with io.open(dest_file, "w") as f:
            f.write(u"")
