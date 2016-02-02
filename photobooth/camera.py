from local_modules import piggyphoto
from StringIO import StringIO
from threading import Thread,Lock,Condition
from Queue import Queue

import pygame
import shutil

import logging
logger = logging.getLogger('photobooth.%s' % __name__)


class GPhotoCamera(object):
    def __init__(self):
        """ Camera initialisation """
        try:
            self.cam = piggyphoto.Camera()
        except piggyphoto.libgphoto2error, e:
            raise ValueError("GPhotoCamera could not be initialised: %s" % e.message)
        print "CAMERA: %s " % self.cam.abilities

        self.preview_jpegs = Queue(maxsize=0)
        self.preview_surfaces = Queue(maxsize=0)

        self.thread_capture = Thread(target=self.capture_worker)
        self.thread_capture.setDaemon(True)
        self.thread_capture_running = True
        self.paused = Condition()
        self.is_paused = True
        self.camera_lock = Lock()
        #self.camera_lock.acquire()
        self.thread_capture.start()
        logger.debug("init done")

    def capture_worker(self):
        while self.thread_capture_running:
            with self.paused:
                while self.is_paused and self.thread_capture_running:
                    self.paused.wait()

                if not self.thread_capture_running:
                    return

                with self.camera_lock:
                    cfile = self.cam.capture_preview()
                    picture = StringIO(cfile.get_data())
                    #picture = pygame.image.load(StringIO(cfile.get_data())).convert()
                    self.preview_jpegs.put(picture)
                    logger.debug("capture_worker: preview captured!")


    def start_preview(self):
        """ LiveView initialistation if needed """
        logger.debug("start preview")
        with self.paused:
            self.is_paused = False
            self.paused.notify()
        logger.debug("start_preview END")

    def stop_preview(self):
        """ LiveView deinit if needed """
        logger.debug("start_preview")
        with self.paused:
            self.is_paused = True
        with self.camera_lock:
            # gPhoto2: not nice, we have to close and reopen the camera to get the mirror down
            self.cam.close()
            self.cam = piggyphoto.Camera()
        logger.debug("stop_preview END")

    def capture_preview(self):
        """ Single LiveView frame """
        file = self.preview_jpegs.get()
        picture = pygame.image.load(file).convert()
        self.preview_jpegs.task_done()
        return picture

    def capture_image(self, file_path):
        """ Full-size image capture and save to destination """
        with self.camera_lock:
            self.cam.capture_image(file_path)

    def close(self):
        """ Camera closing """
        with self.paused:
            self.thread_capture_running = False
            self.paused.notify()
        self.thread_capture.join()

        with self.camera_lock:
            self.cam.close()


class DummyCamera(object):
    def __init__(self):
        print "CAMERA: DummyCamera serving only static JPEGs"
        pass

    def start_preview(self):
        pass

    def stop_preview(self):
        pass

    def capture_preview(self):
        picture = pygame.image.load("dummy-preview.jpg").convert()
        return picture

    def capture_image(self, file_path):
        shutil.copyfile("dummy-preview.jpg", file_path)

    def close(self):
        pass

