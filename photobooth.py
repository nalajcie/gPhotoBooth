#!/usr/bin/env python
# enc: utf-8

import os
import sys
import time
import datetime
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
# this is the default configuration, some values can be changed using commandline parameters
default_config = {
    # display-related consts
    'screen_width': 1280,
    'screen_height': 800,
    'fullscreen': 0,
    'fps': 30,

    # controller-related vars
    'save_path': '.',
    'flip_preview': True,
    'initial_countdown_secs': 3,
    'midphoto_countdown_secs': 3,
    'image_display_secs': 2,

    # whole screen drawing-related consts
    'font_color': (210, 210, 210),
    'font_size': 142,
    'back_color': (230, 180, 40),

    'left_margin': 20,
    'left_offset': 48/3,
    'bottom_margin': 20,
    'top_margin': 20,
}

class LiveView(pygame.sprite.Sprite):
    """
    LiveView display from the camera
    """
    WIDTH  = 848
    HEIGHT = 560

    def __init__(self, group, conf, camera):
        pygame.sprite.Sprite.__init__(self, group)
        self.conf = conf
        self._layer = 5
        self.camera = camera

        # surface & positioning
        self.image = pygame.Surface((LiveView.WIDTH, LiveView.HEIGHT)) # previews width/height
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.conf.left_margin, self.conf.top_margin)
        self.image.convert()
        self.stop()


    def draw_image(self, image, flip_image):
        """ starts displaying image instead of empty rect """
        scalled = pygame.transform.scale(image, (LiveView.WIDTH, LiveView.HEIGHT))
        if flip_image:
            scalled = pygame.transform.flip(scalled, True, False)
        self.image.blit((scalled), (0, 0))

    def start(self):
        self.is_started = True

    def stop(self):
        self.is_started = False

        # draw empty rect
        pygame.draw.rect(self.image, (255,0,0), (0, 0, LiveView.WIDTH, LiveView.HEIGHT),1)

    def pause(self):
        self.is_started = False
        # do not overwrite with black rectangle

    def update(self):
        #TODO: capture preview in other thread
        if (self.is_started):
            self.draw_image(camera.capture_preview(), self.conf.flip_preview)



class PhotoPreview(pygame.sprite.Sprite):
    """
    Small static photo preview, displays empty frame at first, and a small picture afterwards
    """
    WIDTH  = 200
    HEIGHT = 133
    def __init__(self, group, number, conf):
        pygame.sprite.Sprite.__init__(self, group)
        self.conf = conf
        self._layer = 4
        self.number = number
        # surface & positioning
        self.image = pygame.Surface((PhotoPreview.WIDTH, PhotoPreview.HEIGHT)) # previews width/height
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.conf.left_margin + self.number * (PhotoPreview.WIDTH + self.conf.left_offset), self.conf.top_margin + LiveView.HEIGHT + self.conf.bottom_margin)
        self.image.convert()
        self.draw_empty_rect()

    def draw_empty_rect(self):
        """ draws empty rectangle with the number in the middle of it"""
        pygame.draw.rect(self.image, (0,255,0), (0,0,PhotoPreview.WIDTH,PhotoPreview.HEIGHT),1)
        font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size)
        fw, fh = font.size(str(self.number +1 ))
        surface = font.render(str(self.number + 1), True, self.conf.font_color)
        self.image.blit(surface, ((self.rect.width - fw) // 2, (self.rect.height - fh) // 2))

    def draw_image(self, image):
        """ starts displaying image instead of empty rect """
        scalled = pygame.transform.scale(image, (PhotoPreview.WIDTH, PhotoPreview.HEIGHT))
        self.image.blit((scalled), (0, 0))

class TextBox(pygame.sprite.Sprite):
    def __init__(self, group, conf, size, center):
        pygame.sprite.Sprite.__init__(self, group)
        self.conf = conf
        self._layer = 99 # on top of everything
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size/2)

        # surface & positioning
        self.image = pygame.Surface(size)
        self.image.set_colorkey((0,0,0)) # black transparent
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.image.convert_alpha()
        self.current_text = [""]

    def update(self):
        pass

    #def draw_text(self, text):
    #    fw, fh = self.font.size(text)
    #    surface = self.font.render(text, True, self.conf.font_color)
    #    self.image.blit(surface, ((self.rect.width - fw) // 2, (self.rect.height - fh) // 2))

    def draw_text(self, text_lines):
        if self.current_text == text_lines:
            return

        self.current_text = text_lines
        self.image.fill((0,0,0))
        location = self.image.get_rect()
        rendered_lines = [self.font.render(text, True, self.conf.font_color) for text in text_lines]
        line_height = self.font.get_linesize()
        middle_line = len(text_lines) / 2.0 - 0.5

        for i, line in enumerate(rendered_lines):
            line_pos = line.get_rect()
            lines_to_shift = i - middle_line
            line_pos.centerx = location.centerx
            line_pos.centery = location.centery + lines_to_shift * line_height
            self.image.blit(line, line_pos)

    def render_text_bottom(self, text, size=142):
        #FIXME
        location = self.canvas.get_rect()
        line = self.font.render(text, True, self.conf.font_color)
        line_height = font.get_linesize()

        line_pos = line.get_rect()
        line_pos.centerx = location.centerx
        line_pos.centery = location.height - 2 * line_height
        self.canvas.blit(line, line_pos)


class PygView(object):
    """
    Main view which handles all of the rendering
    """

    def __init__(self, controller, conf, camera):
        self.conf = conf
        self.controller = controller

        flags = pygame.DOUBLEBUF | [0, pygame.FULLSCREEN][self.conf.fullscreen]
        self.canvas = pygame.display.set_mode((self.conf.screen_width, self.conf.screen_height), flags)
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size)

        # create drawing components
        self.previews = dict()
        self.allgroup = pygame.sprite.LayeredUpdates()
        for num in xrange(4):
            self.previews[num] = PhotoPreview(self.allgroup, num, conf)
        self.lv = LiveView(self.allgroup, conf, camera)
        self.textbox = TextBox(self.allgroup, conf, self.lv.rect.size, self.lv.rect.center)


    def update(self):
        self.allgroup.update()
        self.allgroup.draw(self.canvas)
        self.flip()


    def flip(self):
        pygame.display.update()
        self.canvas.fill(self.conf.back_color)



class PhotoBoothController(object):

    QUIT_KEYS = pygame.K_ESCAPE, pygame.K_q
    BUTTON_KEY= pygame.K_SPACE,

    def __init__(self, camera, config):
        self.camera = camera
        self.conf = config

        pygame.init()
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        #TODO: add hardware button listener

        #TODO: move to Configuration
        self.count_down_time = 5
        self.image_display_time = 3
        self.montage_display_time = 15
        self.idle_time = 240

        self.is_running = False
        self.model = None
        self.view = PygView(self, self.conf, self.camera)

    def run(self):
        """Main loop"""

        self.is_running = True
        while self.is_running:
            self.clock.tick_busy_loop(self.conf.fps)
            button_pressed = self.process_events()

            self.view.update()

            # photo session in progress
            if self.model:
                self.model.update(button_pressed)

            else:
                if button_pressed:
                    self.start_new_session()

            pygame.display.set_caption("[FPS]: %.2f" % (self.clock.get_fps()))
        else:
            self.quit()

    def quit(self):
        if self.model:
            self.model.quit()
        pygame.quit()

    def process_events(self):
        """ Returns wheter "THE BUTTON" has been pressed """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            if event.type == pygame.KEYDOWN:
                if event.key in PhotoBoothController.QUIT_KEYS:
                    self.is_running = False
                elif event.key in PhotoBoothController.BUTTON_KEY:
                    return True
                # TODO: add our userevent for external button
        else:
            return False

    def start_new_session(self):
        #TODO: change view from mosaics to photobooth view
        self.model = PhotoSessionModel(self)


    def start_live_view(self):
        self.view.lv.start()

    def set_text(self, text_lines):
        self.view.textbox.draw_text(text_lines)

    def capture_image(self, file_name):
        file_path = os.path.join(self.conf.save_path, file_name)
        logger.info("Capturing image to: %s", file_path)
        self.camera.capture_image(file_path)
        #if self.upload_to:
        #    upload_image_async(self.upload_to, file_path)

    def notify_captured_image(self, image_number):
        #TODO: big display on LV?
        self.view.lv.pause()
        self.view.previews[image_number - 1].draw_image(self.model.images[image_number])
        self.view.lv.draw_image(self.model.images[image_number], False)


class SessionState(object):
    def __init__(self, model):
        self.model = model

    def update(self, buttonPressed):
        raise NotImplementedError("Update not implemented")

class WaitingState(SessionState):
    def __init__(self, model):
        super(WaitingState, self).__init__(model)
        self.model.controller.start_live_view()
        self.model.controller.set_text(["Push when ready!"])

    def update(self, button_pressed):
        if button_pressed:
            self.model.capture_start = datetime.datetime.now()
            return CountdownState(self.model, self.model.conf.initial_countdown_secs)
        return self


class TimedState(SessionState):
    def __init__(self, model, timer_length_s):
        super(TimedState, self).__init__(model)
        self.timer = time.time() + timer_length_s

    def time_up(self):
        return self.timer <= time.time()


class CountdownState(TimedState):
    def __init__(self, session, countdown_time):
        super(CountdownState, self).__init__(session, countdown_time)
        self.capture_start = datetime.datetime.now()

    def update(self, button_pressed):
        if self.time_up():
            image = self.take_picture()
            return ShowLastCaptureState(self.model, image)
        else:
            self.display_countdown()
            return self

        self.model.controller.start_live_view()
        self.model.controller.set_text(["Push when ready!"])
        return self

    def display_countdown(self):
        time_remaining = self.timer - time.time()

        if time_remaining <= 0:
            # TODO
            #self.session.booth.display_camera_arrow(clear_screen=True)
            pass
        else:
            lines = [u'Taking picture %d of 4 in:' %
                     (self.model.photo_count + 1), str(int(time_remaining))]
            if time_remaining < 2 and int(time_remaining * 2) % 2 == 1:
                lines = ["Look at the camera!", ""] + lines
            elif time_remaining < 2:
                lines = ["", ""] + lines
                #self.session.booth.display_camera_arrow()
            else:
                lines = ["", ""] + lines
            self.model.controller.set_text(lines)

    def take_picture(self):
        self.model.photo_count += 1
        image_name = self.model.get_image_name(self.model.photo_count)
        self.model.controller.capture_image(image_name)
        return image_name

class ShowLastCaptureState(TimedState):
    def __init__(self, model, image_name):
        super(ShowLastCaptureState, self).__init__(model, model.conf.image_display_secs)
        self.model.controller.set_text([])
        self.model.set_captured_image(image_name, self.model.photo_count)

    def update(self, button_pressed):
        if self.time_up():
            if self.model.photo_count == 4:
                #TODO
                return None
                #return ShowSessionMontageState(self.model)
            else:
                self.model.controller.start_live_view()
                return CountdownState(self.model, self.model.conf.midphoto_countdown_secs)
        else:
            return self

class PhotoSessionModel(object):
    """
    Photo session model (holding global attributes) and state machine
    """
    def __init__(self, controller):
        self.conf = controller.conf
        self.controller = controller

        # global model variables used by different states
        self.state = WaitingState(self)
        self.capture_start = None
        self.photo_count = 0
        self.session_start = time.time()

        self.image_names = dict()
        self.images = dict()

    def update(self, button_pressed):
        self.state = self.state.update(button_pressed)

    def quit(self):
        # any cleaning needed - put it here
        yield

    def idle(self):
        return not self.capture_start and time.time() - self.session_start > self.booth.idle_time

    def get_image_name(self, count):
        return self.capture_start.strftime('%Y-%m-%d-%H%M%S') + '-' + str(count) + '.jpg'

    def set_captured_image(self, image_name, image_number):
        img = pygame.image.load(image_name)
        img.convert()

        self.image_names[image_number] = image_name
        self.images[image_number] = img

        self.controller.notify_captured_image(image_number)

    def finished(self):
        return self.state is None

class Config(object):
    """Change dictionary to object attributes."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __str__(self):
        return str(self.__dict__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("save_path", help="Location to save images")
    parser.add_argument("-d", "--dummy",        help="Use dummy camera instead of GPhoto interface", action="store_true")
    parser.add_argument("-f", "--fullscreen",   help="Use fullscreen mode", action="store_true")
    parser.add_argument("-p", "--print_count",  help="Set number of copies to print", type=int, default=0)
    parser.add_argument("-P", "--printer",      help="Set printer to use", default=None)
    parser.add_argument("-u", "--upload_to",    help="Url to upload images to")
    args = parser.parse_args()

    logger.info("Args were: %s", args)
    conf = Config(**default_config)
    conf.fullscreen = args.fullscreen
    conf.save_path = args.save_path
    logger.info("Full configuration: %s", conf)

    try:
        if args.dummy:
            camera = DummyCamera()
        else:
            camera = GPhotoCamera()
    except ValueError, e:
        logger.exception("Camera could not be initialised, exiting!")
        sys.exit(-1)

    booth = PhotoBoothController(camera, conf)
    try:
        booth.run()
    except Exception:
        logger.exception("Unhandled exception!")
        camera.close()
        sys.exit(-1)
    finally:
        camera.close()
        logger.info("Finished successfully!")
