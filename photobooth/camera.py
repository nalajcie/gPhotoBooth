# encoding: utf-8
from local_modules.piggyphoto import piggyphoto
from StringIO import StringIO
from threading import Thread, Lock, Condition
import thread # for interrupt_main
from Queue import Queue

import pygame

import logging
logger = logging.getLogger('photobooth.%s' % __name__)


class GPhotoCamera(object):
    def __init__(self):
        """ Camera initialisation """
        try:
            self.cam = piggyphoto.Camera()
        except piggyphoto.libgphoto2error, exc:
            raise ValueError("GPhotoCamera could not be initialised: %s" % exc.message)
        print "CAMERA: %s " % self.cam.abilities

        # sync camera time with host
        cc = self.cam.config
        syncdate = cc.get_child_by_name("syncdatetime")
        syncdate.value = 1
        self.cam.config = cc

        self.preview_jpegs = Queue(maxsize=0)
        self.preview_surfaces = Queue(maxsize=0)
        self.curr_preview = pygame.Surface((1, 1)) # will be overriden by real image

        # thread-safe objects
        self.paused = Condition()
        self.is_paused = True
        self.camera_lock = Lock()

        # start the worker threads
        self.threads_running = True
        self.thread_capture = Thread(target=self.capture_worker)
        self.thread_capture.setDaemon(True)
        self.thread_capture.start()

        self.thread_loadpreview = Thread(target=self.loadpreview_worker)
        self.thread_loadpreview.setDaemon(True)
        self.thread_loadpreview.start()

        logger.debug("init done")

    def capture_worker(self):
        """
        Thread: captures new JPEG preview via gphoto in separate thread
        """
        while self.threads_running:
            with self.paused:
                while self.is_paused and self.threads_running:
                    self.paused.wait()

            if not self.threads_running:
                return

            with self.camera_lock:
                try:
                    cfile = self.cam.capture_preview()
                except piggyphoto.libgphoto2error:
                    logger.error("CAMERA EXCEPTION, EXITING!")
                    thread.interrupt_main()
                picture = StringIO(cfile.get_data())
                self.preview_jpegs.put(picture)
                #logger.debug("capture_worker: preview captured!, queue size: %d" % self.preview_jpegs.qsize())

    def loadpreview_worker(self):
        """
        Thread: gets new JPEGs data from queue, loads them into surface and converts
        """
        # drop frames
        while self.threads_running:
            while self.preview_jpegs.qsize() > 1:
                logger.info("DROPPING FRAME!")
                self.preview_jpegs.get()
                self.preview_jpegs.task_done()

            file_io = self.preview_jpegs.get()
            #logger.debug("LOADPREVIEW: loading frame")
            picture = pygame.image.load(file_io).convert()
            self.preview_jpegs.task_done()
            self.curr_preview = picture

    def pause_preview(self):
        self.is_paused = True

    def start_preview(self):
        """ LiveView initialistation if needed """
        logger.debug("start_preview")
        with self.paused:
            self.is_paused = False
            self.paused.notify()
        logger.debug("start_preview END")

    def stop_preview(self):
        """ LiveView deinit if needed """
        logger.debug("stop_preview")
        with self.paused:
            self.is_paused = True
        with self.camera_lock:
            # gPhoto2: not nice, we have to close and reopen the camera to get the mirror down
            self.cam.close()
            self.cam = piggyphoto.Camera()
        logger.debug("stop_preview END")

    def capture_preview(self):
        """ Single LiveView frame """
        return self.curr_preview

    def capture_image(self, file_path):
        """ Full-size image capture and save to destination """
        logger.debug("capture_image")
        with self.camera_lock:
            try:
                self.cam.capture_image(file_path)
            except piggyphoto.libgphoto2error:
                logger.error("CAMERA EXCEPTION, EXITING!")
                thread.interrupt_main()
        logger.debug("capture_image END")

    def close(self):
        """ Camera closing """
        with self.paused:
            self.threads_running = False
            self.paused.notify()
        self.thread_capture.join()
        #self.thread_loadpreview.join()

        with self.camera_lock:
            self.cam.close()


class DummyCamera(object):
    """
    this is only for ease of development, assume always taking 4 pictures
    """
    CAPTURE_COUNT = 4

    def __init__(self):
        print "CAMERA: DummyCamera serving only static JPEGs"
        self.curr_capture = 0

    def start_preview(self):
        """ initiate grabbing previews """
        pass

    def stop_preview(self):
        """ stop grabbing previews """
        pass

    def pause_preview(self):
        """ stop grabbing previews, but do not deinit """
        pass

    @staticmethod
    def capture_preview():
        """ return single preview frame """
        picture = pygame.image.load("dev/dummy-preview.jpg").convert()
        return picture

    def capture_image(self, file_path):
        """
        Captures the image, for better testing this is a full-size img.
        Apply some simple transformation to differ the 4 captured images (GussianBlur in here
        """
        from PIL import Image, ImageFilter
        import platform_devs

        # gaussian blur is really slow on Pi, hack to be able to use DummyCamera
        if platform_devs.get_platform() == platform_devs.PI:
            image = Image.open("dev/dummy-preview.jpg")
            gaussian_scaler = 5
        else:
            image = Image.open("dev/dummy-capture.jpg")
            gaussian_scaler = 20

        radius = (self.CAPTURE_COUNT - self.curr_capture - 1) * gaussian_scaler
        image = image.filter(ImageFilter.GaussianBlur(radius))
        image.save(file_path)

        self.curr_capture = (self.curr_capture + 1) % self.CAPTURE_COUNT
        logger.debug("(6)")

        # the old way, for reference:
        # import shutil
        # shutil.copyfile("dev/dummy-capture.jpg", file_path)

    def close(self):
        """ deinit camera """
        pass

