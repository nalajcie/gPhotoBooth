from local_modules import Adafruit_Thermal
from PIL import Image
import multiprocessing
import time
import pygame
import sys

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class PrinterProxy(object):
    """ setups printer thread and communications with it """
    REQ_SINGLE_IMG = 1
    REQ_FULL_SESS = 2

    def __init__(self, config):
        self.conf = config

        # setup PRINTER
        printer_driver_class = getattr(sys.modules[__name__], self.conf['printer']['driver'])
        self.printer_inst = printer_driver_class(self.conf)

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

    def print_session(self, sess_id, sess_imgs, sess_tags):
        """ pretty-print the whole photosession """
        img_objs = [(img.get_size(), pygame.image.tostring(img, "RGB")) for img in sess_imgs]
        self.printer_pipe.send((PrinterProxy.REQ_FULL_SESS, (sess_id, img_objs, sess_tags)))

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
            except IOError:
                break

            try:
                start = time.time()
                logger.info("printer request: %d", req_id)
                if req_id == PrinterProxy.REQ_SINGLE_IMG:
                    self.print_image(req_data)
                elif req_id == PrinterProxy.REQ_FULL_SESS:
                    sess_id, sess_imgs, sess_tags = req_data
                    self.print_session(sess_id, sess_imgs, sess_tags)
                else:
                    logger.error("unknown printer request: %d", req_id)
                logger.info("printer request finished: %d, time: %f seconds", req_id, (time.time() - start))
            except Exception:
                logger.exception("Printer worker exception!")

    def print_image(self, img_pygame):
        """ debug: printing single image """
        raise NotImplementedError

    def print_session(self, sess_id, sess_imgs, sess_tags):
        """ pretty-print the whole photosession """
        raise NotImplementedError


class ThermalPrinter(AbstractPrinter):
    """ Printing B&W images on thermal paper """

    MAX_WIDTH = 384
    MAX_HEIGHT = 4096

    def __init__(self, config):
        """ Printer initialisation """
        super(ThermalPrinter, self).__init__(config)

        self.printer = Adafruit_Thermal.Adafruit_Thermal(
                self.conf['printer']['thermal']['device_name'],
                self.conf['printer']['thermal']['baudrate'],
                **self.conf['printer']['thermal']['kwargs']
        )
        self.logo = Image.open(self.conf['printer']['logo'])

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

    def println(self, arg):
        """ encode and print  arg as iso8859-2 string, as this is the codepage enabled on the printer """
        self.printer.println(arg.encode('iso8859-2'))


    def print_session(self, sess_id, sess_imgs, sess_tags):
        """ pretty-print the whole photosession """
        # (0) wake the printer
        self.printer.wake()

        # (1) print logo as RAW IMAGE
        self.printer.printImage(self.logo, False)
        #self.printer.feed(1)

        # (2) add header text
        self.printer.justify('C')
        self.printer.setSize('L')
        self.println(self.conf['printer']['name'])
        self.printer.setSize('s')
        self.println(self.conf['printer']['url'])
        self.printer.justify('L')
        self.printer.feed(2)

        # reset the printer, otherwise it spills out garbage
        self.printer.sleep()
        self.printer.wake()

        # (3) scale and print all the images
        if self.conf['printer']['print_all_imgs']:
            for img in sess_imgs:
                self.print_image(img)

                # print session tags sequentally
                #if len(sess_tags):
                #    self.println(u'#'+sess_tags.pop())
                #    self.printer.feed(1)
        else:
            # we're printing only the last image, because the printer heats too much and darkens the images
            self.print_image(sess_imgs[3])

        # print session tags all at once
        while len(sess_tags):
            self.println(u'#'+sess_tags.pop())
        self.printer.feed(1)

        # (4) add some final text
        self.println(time.strftime("%Y-%m-%d %H:%M:%S"))
        self.println(self.conf['m']['print_session_no'] % sess_id)

        # (5) add 'end_text' if provided
        if 'end_text' in self.conf['printer'] and len(self.conf['printer']['end_text']) > 0:
            self.printer.feed(1)
            self.printer.justify('C')
            for line in self.conf['printer']['end_text'].strip().split('\n'):
                self.println(line)
            self.printer.justify('L')

        # (6) feed out and put printer back to sleep
        self.printer.feed(3)
        self.printer.sleep()

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

    def print_session(self, sess_id, sess_imgs, sess_tags):
        """ pretty-print the whole photosession """
        #no-op
        pass

