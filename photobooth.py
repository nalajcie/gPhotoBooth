#!/usr/bin/env python
# enc: utf-8

import sys
import argparse
import logging
import pygame

from camera import *


### setup global logger

logger = logging.getLogger('photobooth')

file_log_handler = logging.FileHandler('photobooth.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_log_handler.setFormatter(formatter)
logger.addHandler(file_log_handler)

stdout_log_handler = logging.StreamHandler(sys.stdout)
stdout_log_handler.setLevel(logging.WARN)
logger.addHandler(stdout_log_handler)

logger.setLevel(logging.DEBUG)

### CONFGIURATION ###
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 800


class PhotoBooth(object):
    def __init__(self, camera, image_dest, fullscreen, print_count, printer, upload_to):
        self.camera = camera

        self.count_down_time = 5
        self.image_display_time = 3
        self.montage_display_time = 15
        self.idle_time = 240

        self.print_count = print_count
        self.printer = printer
        self.upload_to = upload_to
        self.output_dir = image_dest
        self.size = None
        self.fullscreen = fullscreen
        self.events = []
        self.current_session = None

    def capture_preview(self):
        picture = self.camera.capture_preview()

        if self.size:
            picture = pygame.transform.scale(picture, self.size)
        picture = pygame.transform.flip(picture, True, False)
        return picture

    def display_preview(self):
        picture = self.capture_preview()
        self.main_surface.blit(picture, (0, 0))

    def display_image(self, image_name):
        picture = self.load_image(image_name)
        picture = pygame.transform.scale(picture, self.size)
        self.main_surface.blit(picture, (0, 0))

    def start(self):
        pygame.init()
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        # TODO:
        # self.add_button_listener()

        if self.fullscreen:
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


        self.main_surface = pygame.display.get_surface()

        self.size = self.main_surface.get_size()

        while self.main_loop():
            pass
        self.camera.sleep()

    def main_loop(self):
        pygame.event.clear()
        self.clock.tick(25)
        if len(self.events) > 10:
            self.events = self.events[:10]
        pygame.display.flip()

        # TODO
        button_press = self.space_pressed() #or self.button.is_pressed()

        if self.current_session:
            self.current_session.do_frame(button_press)
            if self.current_session.idle():
                self.current_session = None
                self.camera.sleep()
            elif self.current_session.finished():
                # Start a new session
                self.current_session = PhotoSession(self)
        elif button_press:
            # Start a new session
            self.current_session = PhotoSession(self)
        else:
            self.wait()

        return self.check_for_quit_event()

    def wait(self):
        self.main_surface.fill((0, 0, 0))
        self.render_text_centred('Press the button to start!')

    def render_text_centred(self, *text_lines):
        location = self.main_surface.get_rect()
        font = pygame.font.SysFont(pygame.font.get_default_font(), 142)
        rendered_lines = [font.render(text, 1, (210, 210, 210)) for text in text_lines]
        line_height = font.get_linesize()
        middle_line = len(text_lines) / 2.0 - 0.5

        for i, line in enumerate(rendered_lines):
            line_pos = line.get_rect()
            lines_to_shift = i - middle_line
            line_pos.centerx = location.centerx
            line_pos.centery = location.centery + lines_to_shift * line_height
            self.main_surface.blit(line, line_pos)

    def render_text_bottom(self, text, size=142):
        location = self.main_surface.get_rect()
        font = pygame.font.SysFont(pygame.font.get_default_font(), size)
        line = font.render(text, 1, (210, 210, 210))
        line_height = font.get_linesize()

        line_pos = line.get_rect()
        line_pos.centerx = location.centerx
        line_pos.centery = location.height - 2 * line_height
        self.main_surface.blit(line, line_pos)

    def capture_image(self, file_name):
        file_path = os.path.join(self.output_dir, file_name)
        logger.info("Capturing image to: %s", file_path)
        self.camera.capture_image(file_path)
        if self.upload_to:
            upload_image_async(self.upload_to, file_path)

    def check_key_event(self, *keys):
        self.events += pygame.event.get(pygame.KEYUP)
        for event in self.events:
            if event.dict['key'] in keys:
                self.events = []
                return True
        return False

    def space_pressed(self):
        return self.check_key_event(pygame.K_SPACE)

    def check_for_quit_event(self):
        return not self.check_key_event(pygame.K_q, pygame.K_ESCAPE) \
            and not pygame.event.peek(pygame.QUIT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("save_to", help="Location to save images")
    parser.add_argument("-d", "--dummy",        help="Use dummy camera instead of GPhoto interface", action="store_true")
    parser.add_argument("-f", "--fullscreen",   help="Use fullscreen mode", action="store_true")
    parser.add_argument("-p", "--print_count",  help="Set number of copies to print", type=int, default=0)
    parser.add_argument("-P", "--printer",      help="Set printer to use", default=None)
    parser.add_argument("-u", "--upload_to",    help="Url to upload images to")
    args = parser.parse_args()

    logger.info("Args were: %s", args)


    if args.dummy:
        camera = DummyCamera()
    else:
        camera = GPhotoCamera()

    booth = PhotoBooth(camera,
                       args.save_to,
                       fullscreen=(args.fullscreen),
                       print_count=args.print_count,
                       printer=args.printer,
                       upload_to=args.upload_to)
    try:
        booth.start()
    except Exception:
        logger.exception("Unhandled exception!")
        camera.close()
        sys.exit(-1)
    finally:
        logger.info("Finished successfully!")
