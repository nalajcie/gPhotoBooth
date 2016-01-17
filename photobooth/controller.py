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

        self.is_running = False
        self.model = model.PhotoBoothModel(self)
        self.view = view.PygView(self, self.conf, self.camera)

    def run(self):
        """Main loop"""

        self.is_running = True
        while self.is_running:
            self.clock.tick_busy_loop(self.conf.fps)
            button_pressed = self.process_events()

            self.view.update()
            self.model.update(button_pressed)

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

    def start_live_view(self):
        self.view.lv.start()

    def set_text(self, text_lines):
        self.view.textbox.draw_text(text_lines)

    def capture_image(self, file_path):
        logger.info("Capturing image to: %s", file_path)
        self.view.lv.pause()
        self.camera.capture_image(file_path)
        #if self.upload_to:
        #    upload_image_async(self.upload_to, file_path)

    def load_captured_image(self, file_path):
        img = pygame.image.load(file_path).convert()
        return img

    def scale_image_for_lv(self, image):
        return pygame.transform.scale(image, (view.LiveView.WIDTH, view.LiveView.HEIGHT))

    def scale_and_save_image_for_preview(self, image, file_path):
        img_prev = pygame.transform.scale(image, (view.PhotoPreview.WIDTH, view.PhotoPreview.HEIGHT))
        pygame.image.save(img_prev, file_path)
        return img_prev

    def notify_captured_image(self, image_number, img, img_prev):
        self.view.previews[image_number].draw_image(img_prev)
        self.view.lv.draw_image(img, False)

    def animate_montage(self, img_list):
        self.view.lv.start_animate(img_list, self.conf.montage_fps)

