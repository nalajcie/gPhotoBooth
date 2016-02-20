from local_modules import Adafruit_Thermal
from PIL import Image

import pygame

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class ThermalPrinter(object):
    """ Printing B&W images on thermal paper """

    MAX_WIDTH = 384
    MAX_HEIGHT = 4096

    def __init__(self):
        """ Printer initialisation """
        #TODO: get uart connection from platform and config from our one file
        self.printer = Adafruit_Thermal.Adafruit_Thermal(timeout=5, config="printer.cfg")

    def print_image(self, img_pygame):
        """ debug: printing single image """
        logger.info("ThermalPrinter: printing image")

        # from PyGame to PIL.Image
        img = Image.frombuffer("RGB", img_pygame.get_size(), pygame.image.tostring(img_pygame, "RGB"), 'raw', "RGB", 0, 1)
        img = img.transpose(Image.ROTATE_90)#.transpose(Image.FLIP_TOP_BOTTOM)

        logger.debug("OLDSIZE: (%d, %d)", img.size[0], img.size[1])
        if img.size[0] > self.MAX_WIDTH:
            newsize = (self.MAX_WIDTH, int(float(img.size[1]) / (float(img.size[0]) / self.MAX_WIDTH)))
            logger.debug("NEWSIZE: (%d, %d)", newsize[0], newsize[1])
            img = img.resize(newsize, Image.ANTIALIAS)

        # PIL algorithm: convert to greyscale then convert to mono with dithering
        img = img.convert('1')

        self.printer.printImage(img, False)
        self.printer.feed(3)

    def print_session(self, sess):
        """ pretty-print the whole photosession """
        #TODO
        pass

class NullPrinter(object):
    """ dummy no-op printer """
    def __init__(self):
        self.print_cnt = 0

    def print_image(self, img):
        """ debug: printing single image """
        file_name = "print-" + str(self.print_cnt) + ".jpg"
        pygame.image.save(img, file_name)
        logger.info("NullPrinter: image saved to: " + file_name)
        self.print_cnt += 1

    def print_session(self, sess):
        """ pretty-print the whole photosession """
        # no-op
        pass

