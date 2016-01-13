from local_modules import piggyphoto
from StringIO import StringIO

import pygame
import shutil

class GPhotoCamera():
    def __init__(self):
        try:
            self.cam = piggyphoto.Camera()
        except piggyphoto.libgphoto2error, e:
            raise ValueError("GPhotoCamera could not be initialised: %s" % e.message)
        print "CAMERA: %s " % self.cam.abilities

    def capture_preview(self):
        cfile = self.cam.capture_preview()
        picture = pygame.image.load(StringIO(cfile.get_data()))
        cfile.clean()
        return picture

    def capture_image(self, file_path):
        self.cam.capture_image(file_path)
        return

    def close(self):
        self.cam.close()

class DummyCamera():
    def __init__(self):
        print "CAMERA: DummyCamera serving only static JPEGs"
        return

    def capture_preview(self):
        picture = pygame.image.load("dummy-preview.jpg")
        return picture

    def capture_image(self, file_path):
        shutil.copyfile("dummy-preview.jpg", file_path)
        return

    def close(self):
        return

