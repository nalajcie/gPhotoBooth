from local_modules import Adafruit_Thermal
from StringIO import StringIO
from PIL import Image

import pygame

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class ThermalPrinter(object):

    MAX_WIDTH = 384
    MAX_HEIGHT = 4096

    def __init__(self):
        """ Printer initialisation """
        self.printer = Adafruit_Thermal.Adafruit_Thermal(timeout=5, config="printer.cfg")

    def print_image(self, img_pygame):
        logger.info("ThermalPrinter: printing image")

        # from PyGame to PIL.Image
        im = Image.frombuffer("RGB", img_pygame.get_size(), pygame.image.tostring(img_pygame, "RGB"), 'raw', "RGB", 0, 1)
        im = im.transpose(Image.ROTATE_90)#.transpose(Image.FLIP_TOP_BOTTOM)

        logger.debug("OLDSIZE: (%d, %d)" % (im.size[0], im.size[1]))
        if im.size[0] > self.MAX_WIDTH:
            newsize = (self.MAX_WIDTH, int(float(im.size[1]) / (float(im.size[0]) / self.MAX_WIDTH)))
            logger.debug("NEWSIZE: (%d, %d)" % (newsize[0], newsize[1]))
            im = im.resize(newsize, Image.ANTIALIAS)

        # PIL algorithm: convert to greyscale then convert to mono with dithering
        im = im.convert('1')

        self.printer.printImage(im, False)
        self.printer.feed(3)

class NullPrinter(object):
    def __init__(self):
        self.print_cnt = 0

    def print_image(self, img):
        file_name = "print-" + str(self.print_cnt) + ".jpg"
        pygame.image.save(img, file_name)
        logger.info("NullPrinter: image saved to: " + file_name)
        self.print_cnt += 1
