from local_modules import Adafruit_Thermal
from PIL import Image
import multiprocessing
import time
import pygame

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class PrinterProxy(object):
    """ setups printer thread and communications with it """
    REQ_SINGLE_IMG = 1
    REQ_FULL_SESS = 2

    def __init__(self, config):
        self.conf = config

        # setup PRINTER
        if self.conf.thermal_printer:
            self.printer_inst = ThermalPrinter(self.conf)
        else:
            self.printer_inst = NullPrinter(self.conf)

        # init and start printer process
        pipe = multiprocessing.Pipe()
        self.printer_pipe = pipe[0]
        self.process_printer = multiprocessing.Process(target=self.printer_inst.run, args=(pipe,))
        self.process_printer.daemon = True
        self.process_printer.start()

    def print_image(self, img_pygame):
        """ debug: printing single image """
        obj = (img_pygame.get_size(), pygame.image.tostring(img_pygame, "RGB"))
        self.printer_pipe.send((PrinterProxy.REQ_SINGLE_IMG, obj))

    def print_session(self, sess):
        """ pretty-print the whole photosession """
        self.printer_pipe.send((PrinterProxy.REQ_FULL_SESS, sess))

    def __del__(self):
        self.printer_pipe.close()


class AbstractPrinter(object):
    def __init__(self, config):
        self.conf = config

    def run(self, pipe):
        """ run in separate process, dispatcher - do not override in subclass """
        logger.info("printer process has started")
        serv_pipe, client_pipe = pipe
        serv_pipe.close()
        while True:
            try:
                req_id, req_data = client_pipe.recv()
            except EOFError:
                break

            try:
                start = time.time()
                logger.info("printer request: %d", req_id)
                if req_id == PrinterProxy.REQ_SINGLE_IMG:
                    self.print_image(req_data)
                elif req_id == PrinterProxy.REQ_FULL_SESS:
                    self.print_session(req_data)
                else:
                    logger.error("unknown printer request: %d", req_id)
                logger.info("printer request finished: %d, time: %f seconds", req_id, (time.time() - start))
            except Exception:
                logger.exception("Printer worker exception!")

    def print_image(self, img_pygame):
        """ debug: printing single image """
        raise NotImplementedError

    def print_session(self, sess):
        """ pretty-print the whole photosession """
        raise NotImplementedError


class ThermalPrinter(AbstractPrinter):
    """ Printing B&W images on thermal paper """

    MAX_WIDTH = 384
    MAX_HEIGHT = 4096

    def __init__(self, config):
        """ Printer initialisation """
        super(ThermalPrinter, self).__init__(config)

        #TODO: get uart connection from platform and config from our one file
        self.printer = Adafruit_Thermal.Adafruit_Thermal(timeout=5, config="printer.cfg")

    def print_image(self, img_obj):
        logger.info("ThermalPrinter: printing image")
        img_size, img_string = img_obj

        # from PyGame to PIL.Image
        img = Image.frombuffer("RGB", img_size, img_string, 'raw', "RGB", 0, 1)
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
        #TODO: decide how to print the whole session
        pass

class NullPrinter(AbstractPrinter):
    """ dummy no-op printer """
    MAX_WIDTH = 384
    MAX_HEIGHT = 4096

    def __init__(self, config):
        super(NullPrinter, self).__init__(config)
        self.print_cnt = 0

    def print_image(self, img_obj):
        """ debug: printing single image """
        img_size, img_string = img_obj

        # from PyGame to PIL.Image
        img = Image.frombuffer("RGB", img_size, img_string, 'raw', "RGB", 0, 1)
        img = img.transpose(Image.ROTATE_90)#.transpose(Image.FLIP_TOP_BOTTOM)

        logger.debug("OLDSIZE: (%d, %d)", img.size[0], img.size[1])
        #if img.size[0] > self.MAX_WIDTH:
        #    newsize = (self.MAX_WIDTH, int(float(img.size[1]) / (float(img.size[0]) / self.MAX_WIDTH)))
        #    logger.debug("NEWSIZE: (%d, %d)", newsize[0], newsize[1])
        #    img = img.resize(newsize, Image.ANTIALIAS)

        # PIL algorithm: convert to greyscale then convert to mono with dithering
        # img = img.convert('1')

        file_name = "print-" + str(self.print_cnt) + ".jpg"
        img.save(file_name)
        logger.info("NullPrinter: image saved to: " + file_name)
        self.print_cnt += 1
        time.sleep(3) # simulate printing time

    def print_session(self, sess):
        """ pretty-print the whole photosession """
        # no-op
        pass

