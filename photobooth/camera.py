from local_modules import piggyphoto
from StringIO import StringIO

import pygame
import shutil

class GPhotoCamera():
    def __init__(self):
        """ Camera initialisation """
        try:
            self.cam = piggyphoto.Camera()
        except piggyphoto.libgphoto2error, e:
            raise ValueError("GPhotoCamera could not be initialised: %s" % e.message)
        print "CAMERA: %s " % self.cam.abilities

    def start_preview(self):
        """ LiveView initialistation if needed """
        pass

    def stop_preview(self):
        """ LiveView deinit if needed """
        # gPhoto2: not nice, we have to close and reopen the camera
        self.cam.close()
        self.cam = piggyphoto.Camera()

    def capture_preview(self):
        """ Single LiveView frame """
        cfile = self.cam.capture_preview()
        picture = pygame.image.load(StringIO(cfile.get_data()))
        return picture

    def capture_image(self, file_path):
        """ Full-size image capture and save to destination """
        self.cam.capture_image(file_path)
        return

    def close(self):
        """ Camera closing """
        self.cam.close()

class DummyCamera():
    def __init__(self):
        print "CAMERA: DummyCamera serving only static JPEGs"
        return

    def start_preview(self):
        pass

    def stop_preview(self):
        pass

    def capture_preview(self):
        picture = pygame.image.load("dummy-preview.jpg")
        return picture

    def capture_image(self, file_path):
        shutil.copyfile("dummy-preview.jpg", file_path)
        return

    def close(self):
        return

