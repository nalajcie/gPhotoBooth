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
    'left_offset': 12,
    'bottom_margin': 20,
}


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
        self.rect.bottomleft = (self.conf.left_margin + self.number * (PhotoPreview.WIDTH + self.conf.left_offset), self.conf.screen_height - self.conf.bottom_margin)

        # drawing
        pygame.draw.rect(self.image, (0,255,0), (0,0,PhotoPreview.WIDTH,PhotoPreview.HEIGHT),1)
        #TODO: draw (number + 1)

class PygView(object):
    """
    Main view which handles all of the rendering
    """

    CURSORKEYS = slice(273, 277)
    QUIT_KEYS = pygame.K_ESCAPE, pygame.K_q
    EVENTS = 'up', 'down', 'right', 'left'

    def __init__(self, controller, conf):
        self.conf = conf
        self.controller = controller
        self.fps = self.conf.fps

        # create drawing components
        self.previews_group = pygame.sprite.Group()
        for num in xrange(4):
            PhotoPreview(self.previews_group, num, conf)

        pygame.init()
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        # TODO:
        # self.add_button_listener()

        flags = pygame.DOUBLEBUF | [0, pygame.FULLSCREEN][self.conf.fullscreen]
        self.canvas = pygame.display.set_mode((self.conf.screen_width, self.conf.screen_height), flags)
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), self.conf.font_size)

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
            self.previews_group.draw(self.canvas)
            self.flip()
        else:
            self.quit()


    def get_events(self):

        keys = pygame.key.get_pressed()[PygView.CURSORKEYS]
        move_events = [e for e, k in zip(PygView.EVENTS, keys) if k]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit', move_events
            if event.type == pygame.KEYDOWN:
                if event.key in PygView.QUIT_KEYS:
                    return 'quit', move_events
                else:
                    return 'other_key', move_events
        else:
            return None, move_events

    def flip(self):
        pygame.display.flip()
        self.canvas.fill(self.conf.back_color)


    def quit(self):
        pygame.quit()


class PhotoBoothController(object):
    def __init__(self, camera, config):
        self.camera = camera
        self.conf = config
        self.state = 'playing'

        self.count_down_time = 5
        self.image_display_time = 3
        self.montage_display_time = 15
        self.idle_time = 240

        self.current_session = None

        self.view = PygView(self, self.conf)


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

    def dispatch(self, all_events):
        """Control the game state."""

        event, move_events = all_events
        if event == 'quit':
            #self.game.quit()
            return False

        if self.state == 'playing':
            #self.state = self.game.process(self.view, move_events)
            return True

        if self.state == 'ending':
            self.game.wait(self.view)
            if event == 'other_key':
                self.state = 'playing'
                #self.game.reset(START)

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
