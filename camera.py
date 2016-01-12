from local_modules import piggyphoto
from StringIO import StringIO

import pygame

class GPhotoCamera():
    def __init__(self):
        self.cam = piggyphoto.Camera()

    def capture_preview(self):
        cfile = self.cam.capture_preview()
        picture = pygame.image.load(StringIO(cfile.get_data()))
        cfile.clean()
        return picture

    def close(self):
        self.cam.close()

class DummyCamera():
    def __init__(self):
        return

    def capture_preview(self):
        picture = pygame.image.load("dummy-preview.jpg")
        return picture

    def close(self):
        return

