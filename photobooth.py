#!/usr/bin/env python
# enc: utf-8

import sys
import time
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
    'fps': 10,

    # controller-related vars
    'save_path': '.',

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
        self.camera = camera

        # surface & positioning
        self.image = pygame.Surface((LiveView.WIDTH, LiveView.HEIGHT)) # previews width/height
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.conf.left_margin, self.conf.top_margin)
        self.image.convert()

        # drawing
        pygame.draw.rect(self.image, (255,0,0), (0, 0, LiveView.WIDTH, LiveView.HEIGHT),1)

    def draw_image(self, image):
        """ starts displaying image instead of empty rect """
        scalled = pygame.transform.scale(image, (LiveView.WIDTH, LiveView.HEIGHT))
        self.image.blit((scalled), (0, 0))

    def update(self):
        #TODO: capture preview in other thread
        self.draw_image(camera.capture_preview())


class PhotoPreview(pygame.sprite.Sprite):
    """
    Small static photo preview, displays empty frame at first, and a small picture afterwards
    """
    WIDTH  = 200
    HEIGHT = 133
    def __init__(self, group, number, conf):
        pygame.sprite.Sprite.__init__(self, group)
        self.conf = conf
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


class PygView(object):
    """
    Main view which handles all of the rendering
    """

    QUIT_KEYS = pygame.K_ESCAPE, pygame.K_q
    BUTTON_KEY= pygame.K_SPACE,

    def __init__(self, controller, conf, camera):
        self.conf = conf
        self.controller = controller
        self.fps = self.conf.fps

        pygame.init()
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        # TODO:
        # self.add_button_listener()

        flags = pygame.DOUBLEBUF | [0, pygame.FULLSCREEN][self.conf.fullscreen]
        self.canvas = pygame.display.set_mode((self.conf.screen_width, self.conf.screen_height), flags)
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size)

        # create drawing components
        self.previews = dict()
        self.allgroup = pygame.sprite.Group()
        for num in xrange(4):
            self.previews[num] = PhotoPreview(self.allgroup, num, conf)
        self.lv = LiveView(self.allgroup, conf, camera)

    def draw_text(self, text):

        fw, fh = self.font.size(text)
        surface = self.font.render(text, True, self.font_color)
        self.canvas.blit(surface, ((self.width - fw) // 2, (self.height - fh) // 2))

    def render_text_centred(self, *text_lines):
        location = self.canvas.get_rect()
        rendered_lines = [self.font.render(text, True, self.conf.font_color) for text in text_lines]
        line_height = font.get_linesize()
        middle_line = len(text_lines) / 2.0 - 0.5

        for i, line in enumerate(rendered_lines):
            line_pos = line.get_rect()
            lines_to_shift = i - middle_line
            line_pos.centerx = location.centerx
            line_pos.centery = location.centery + lines_to_shift * line_height
            self.main_surface.blit(line, line_pos)

    def render_text_bottom(self, text, size=142):
        location = self.canvas.get_rect()
        font = pygame.font.SysFont(pygame.font.get_default_font(), size)
        line = self.font.render(text, True, self.conf.font_color)
        line_height = font.get_linesize()

        line_pos = line.get_rect()
        line_pos.centerx = location.centerx
        line_pos.centery = location.height - 2 * line_height
        self.main_surface.blit(line, line_pos)

    def run(self):
        """Main loop"""

        running = True
        while running:
            self.clock.tick_busy_loop(self.fps)
            running = self.controller.dispatch(self.get_events())

            self.allgroup.update()
            self.allgroup.draw(self.canvas)
            self.flip()
        else:
            self.quit()


    def get_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key in PygView.QUIT_KEYS:
                    return 'quit'
                elif event.key in PygView.BUTTON_KEY:
                    return 'button'
        else:
            return None

    def flip(self):
        pygame.display.update()
        self.canvas.fill(self.conf.back_color)


    def quit(self):
        pygame.quit()


class PhotoBoothController(object):
    def __init__(self, camera, config):
        self.camera = camera
        self.conf = config
        self.is_working = False

        self.count_down_time = 5
        self.image_display_time = 3
        self.montage_display_time = 15
        self.idle_time = 240

        self.current_session = None

        self.view = PygView(self, self.conf, self.camera)


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

    def run(self):
        self.view.run()

    def dispatch(self, event):
        """Control the game state."""

        if event == 'quit':
            #self.game.quit()
            if self.is_working:
                self.model.quit()
            return False

        if event == 'button':
            if not self.is_working:
                self.is_working = True
                self.model = PhotoSessionModel(self)
            else:
                self.model.buttonPushed()

        return True


    def main_loop(self):
        #WARN: not used for now!
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

class SessionState(object):
    def __init__(self, model):
        self.model = model

    def update(self, buttonPressed):
        raise NotImplementedError("Update not implemented")

class WaitingState(SessionState):
    def update(self, button_pressed):
        if button_pressed:
            #TODO: transition to next state
            print("TODO: next state")
        self.session.booth.display_preview()
        self.session.booth.render_text_centred("Push when ready!")
        return self

    def next(self, button_pressed):
        if button_pressed:
            self.session.capture_start = datetime.datetime.now()
            return CountdownState(self.session)
        else:
            return self

class PhotoSessionModel(object):
    """
    Photo session model (holding global attributes) and state machine
    """
    def __init__(self, controller):
        self.controller = controller

        # global model variables used by different states
        self.state = WaitingState(self)
        self.capture_start = None
        self.photo_count = 0
        self.session_start = time.time()

    def update(self, button_pressed):
        self.state = self.state.update(button_pressed)

    def idle(self):
        return not self.capture_start and time.time() - self.session_start > self.booth.idle_time

    def get_image_name(self, count):
        return self.capture_start.strftime('%Y-%m-%d-%H%M%S') + '-' + str(count) + '.jpg'

    def finished(self):
        return self.state is None

class Config(object):
  """Change dictionary to object attributes."""

  def __init__(self, **kwargs):

    self.__dict__.update(kwargs)

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

    if args.dummy:
        camera = DummyCamera()
    else:
        camera = GPhotoCamera()

    booth = PhotoBoothController(camera, conf)
    try:
        booth.run()
    except Exception:
        logger.exception("Unhandled exception!")
        camera.close()
        sys.exit(-1)
    finally:
        logger.info("Finished successfully!")
