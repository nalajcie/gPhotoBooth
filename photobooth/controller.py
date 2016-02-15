import os
import sys
import pygame
import model, view
import platform
from threading import Thread,Lock,Condition
from Queue import Queue


import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class PhotoBoothController(object):

    QUIT_KEYS = pygame.K_ESCAPE, pygame.K_q
    BUTTON_KEY= pygame.K_SPACE,

    BUTTONPUSHEVENT = pygame.USEREVENT + 2

    def __init__(self, config, camera, printer):
        self.conf = config
        self.camera = camera
        self.printer = printer

        # platform and pygame
        logger.info("PLATFORM: %s" % platform.running_platform)
        platform.platform_init()
        pygame.init()
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        # peripherials
        self.button = platform.Button()
        self.lights = platform.Lights()
        self.button.register_callback(self.button_callback)

        # view nad model
        self.is_running = False
        self.view = view.PygView(self, self.conf, self.camera)
        self.model = model.PhotoBoothModel(self)
        self.model.load_from_disk()

        # capture thread
        self.capture_names = Queue(maxsize=0)
        self.thread_capture = Thread(target=self.capture_image_worker)
        self.thread_capture.setDaemon(True)

        self.next_fps_update_ticks = 0

    def __del__(self):
        platform.platform_deinit()

    def run(self):
        """Main loop"""

        self.is_running = True
        self.thread_capture.start()
        self.button.start()
        self.lights.start()

        while self.is_running:
            self.clock.tick(self.view.fps)
            button_pressed = self.process_events()

            self.view.update()
            self.model.update(button_pressed)

            if self.next_fps_update_ticks < pygame.time.get_ticks():
                fps_str = "[FPS]: %.2f" % (self.clock.get_fps())
                pygame.display.set_caption(fps_str)
                logger.debug(fps_str)
                self.next_fps_update_ticks = pygame.time.get_ticks() + self.conf.fps_update_ms
        else:
            self.quit()

    def quit(self):
        if self.model:
            self.model.quit()
        pygame.quit()

    def button_callback(self):
        button_event = pygame.event.Event(self.BUTTONPUSHEVENT)
        pygame.event.post(button_event)

    def process_events(self):
        """ Returns wheter "THE BUTTON" has been pressed """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == self.BUTTONPUSHEVENT:
                return True
            elif event.type == pygame.KEYDOWN:
                if event.key in PhotoBoothController.QUIT_KEYS:
                    self.is_running = False
                elif event.key in PhotoBoothController.BUTTON_KEY:
                    return True
                elif event.key == pygame.K_p: # for debugging
                    self.print_camera_preview()
                    return False
                # TODO: add our userevent for external button
        else:
            return False

    def start_live_view(self):
        self.camera.start_preview()
        self.view.lv.start()

    def resume_live_view(self):
        self.view.lv.start()

    def stop_live_view(self):
        self.camera.stop_preview()
        self.view.lv.stop()

    def set_text(self, text_lines):
        self.view.textbox.draw_text(text_lines)

    def capture_image_worker(self):
        while self.is_running:
            image_number, image_name, prev_name = self.capture_names.get()

            # (1) capture the image
            logger.info("capture_image_worker: capturing image to: %s", image_name)
            self.camera.pause_preview()
            #self.view.lv.pause() # stop updating LV
            self.camera.capture_image(image_name)
            self.camera.start_preview() # resume previews ASAP

            # (2) load captured images and scale them
            logger.debug("capture_image_worker: reading and scalling images")
            img = pygame.image.load(image_name).convert()
            img_lv = pygame.transform.scale(img, (view.LivePreview.WIDTH, view.LivePreview.HEIGHT))
            img_prev = pygame.transform.scale(img_lv, (view.SmallPhotoPreview.WIDTH, view.SmallPhotoPreview.HEIGHT))

            # (3) view: start the 'end animation overlay' and resume LV
            self.view.lv.start()
            self.view.lv.end_overlay()
            self.view.main_previews[image_number].set_image(img_prev)
            self.view.main_previews[image_number].end_overlay()

            # (4) save the scalled preview
            pygame.image.save(img_prev, prev_name)

            # (5) finish the task and send the results
            logger.debug("capture_image_worker: DONE")
            self.capture_names.task_done()
            self.model.set_current_session_imgs(image_number, (img, img_lv, img_prev))

    def capture_image(self, image_number, full_file_path, prev_file_path):
        # view: capture begin animation
        self.view.lv.pause()
        self.view.lv.begin_overlay()
        self.view.main_previews[image_number].begin_overlay()

        # schedule worker thread to capture image
        self.capture_names.put((image_number, full_file_path, prev_file_path))

    def print_camera_preview(self):
        img = self.view.lv.image
        self.printer.print_image(img)

    def load_captured_image(self, file_path):
        img = pygame.image.load(file_path).convert()
        return img

    def enqueue_animate_montage(self, img_list):
        self.view.lv.enqueue_animate_montage(img_list, self.conf.montage_fps)

    def notify_idle_previews_changed(self):
        prev_num = 1
        for img_list in self.model.get_idle_previews_image_lists():
            #logger.debug("preview[%d] = %s <- %s" % (prev_num, self.view.idle_previews[prev_num], img_list))
            self.view.idle_previews[prev_num].start_animate(img_list, 0) # if fps == 0 -> sync whith display FPS
            prev_num += 1
