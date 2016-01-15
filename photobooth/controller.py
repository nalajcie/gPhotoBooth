import os
import sys
import pygame
import model, view

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

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
        self.view = view.PygView(self, self.conf, self.camera)

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
                if self.model.finished():
                    self.end_session()

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
        logging.debug("PhotoSession START")
        self.view.idle = False
        self.model = model.PhotoSessionModel(self)

    def end_session(self):
        logging.debug("PhotoSession END")
        self.view.idle = True
        self.model = None


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

    def load_captured_image(self, file_name):
        file_path = os.path.join(self.conf.save_path, file_name)
        img = pygame.image.load(file_path)
        img.convert()
        return img

    def notify_captured_image(self, image_number):
        #TODO: big display on LV?
        self.view.lv.pause()
        self.view.previews[image_number - 1].draw_image(self.model.images[image_number])
        self.view.lv.draw_image(self.model.images[image_number], False)

