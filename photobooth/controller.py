""" Controlls the logic flow around the whole application """
import pygame
import photobooth.model as model
import photobooth.view as view
import photobooth.upload as upload
import photobooth.platform as platform
from photobooth.printer import PrinterProxy
from threading import Thread
from Queue import Queue
import multiprocessing


import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class PhotoBoothController(object):
    """ controlling the logic flow around the whole application """

    QUIT_KEYS = pygame.K_ESCAPE, pygame.K_q
    BUTTON_KEY= pygame.K_SPACE,

    BUTTONPUSHEVENT = pygame.USEREVENT + 2

    def __init__(self, config, camera):
        self.conf = config
        self.camera = camera
        self.printer = PrinterProxy(self.conf)

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

        # view and model
        self.is_running = False
        self.view = view.PygView(self, self.conf, self.camera)
        self.model = model.PhotoBoothModel(self)
        self.model.load_from_disk()

        # capture thread
        self.capture_names = Queue(maxsize=0)
        self.thread_capture = Thread(target=self.capture_image_worker)
        self.thread_capture.setDaemon(True)

        # upload background process (creating GIF is cpu-intensive, make it happen in other process to bypass GIL)
        self.upload_pipe = None
        if self.conf['upload']['enabled']:
            pipe = multiprocessing.Pipe()
            self.upload_pipe = pipe[0]
            self.process_upload = multiprocessing.Process(target=upload.run, args=(self.conf, pipe))
            self.process_upload.daemon = True


        self.next_fps_update_ticks = 0

    def __del__(self):
        platform.platform_deinit()

    def run(self):
        """Main loop"""

        self.is_running = True
        self.thread_capture.start()
        self.button.start()

        if self.conf['upload']['enabled']:
            self.process_upload.start()

        while self.is_running:
            self.clock.tick(self.view.fps)
            button_pressed = self.process_events()
            self.button.update_state()

            self.view.update()
            self.model.update(button_pressed)

            if self.next_fps_update_ticks < pygame.time.get_ticks():
                fps_str = "[FPS]: %.2f" % (self.clock.get_fps())
                pygame.display.set_caption(fps_str)
                #logger.debug(fps_str)
                self.next_fps_update_ticks = pygame.time.get_ticks() + self.conf['debug']['fps_update_ms']

        self.quit()

    def quit(self):
        self.is_running = False
        if self.model:
            self.model.quit()
            self.model = None
        if self.upload_pipe:
            self.upload_pipe.close()
            self.upload_pipe = None

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

        return False

    def start_live_view(self):
        self.camera.start_preview()
        self.view.lv.start()

    def resume_live_view(self):
        self.view.lv.start()

    def stop_live_view(self):
        self.camera.stop_preview()
        self.view.lv.stop()

    def live_view_show_arrow(self):
        self.view.lv.show_arrow = True

    def live_view_hide_arrow(self):
        self.view.lv.show_arrow = False

    def set_text(self, text_lines, big_font=False):
        self.view.textbox.draw_text(text_lines, big_font)

    def capture_image_worker(self):
        while self.is_running:
            image_number, image_name, medium_name, prev_name = self.capture_names.get()

            # (1) capture the image
            logger.info("capture_image_worker: capturing image to: %s", image_name)
            self.camera.pause_preview()
            #self.view.lv.pause() # stop updating LV
            self.camera.capture_image(image_name)
            self.camera.start_preview() # resume previews ASAP

            # (2) lights - default brightness
            self.lights.set_brightness(self.conf["devices"]["lights_default"])

            # (3) load captured images and scale them
            logger.debug("capture_image_worker: reading and scalling images")
            img = pygame.image.load(image_name).convert()
            img_lv = pygame.transform.scale(img, (view.LivePreview.WIDTH, view.LivePreview.HEIGHT))
            img_prev = pygame.transform.scale(img_lv, (view.SmallPhotoPreview.WIDTH, view.SmallPhotoPreview.HEIGHT))

            # (4) view: start the 'end animation overlay' and resume LV
            self.view.lv.start()
            self.view.lv.end_overlay()
            self.view.main_previews[image_number].set_image(img_prev)
            self.view.main_previews[image_number].end_overlay()

            # (5) save the scalled images
            pygame.image.save(img_prev, prev_name)
            pygame.image.save(img_lv, medium_name)

            # (6) finish the task and send the results
            logger.debug("capture_image_worker: DONE")
            self.capture_names.task_done()
            self.model.set_current_session_imgs(image_number, (img, img_lv, img_prev))

    def capture_image(self, image_number, file_paths):
        # lights - maximum brightness
        self.lights.set_brightness(self.conf["devices"]["lights_full"])

        # view: capture begin animation
        self.view.lv.pause()
        self.view.lv.begin_overlay()
        self.view.main_previews[image_number].begin_overlay()

        # schedule worker thread to capture image
        obj = (image_number, file_paths[0], file_paths[1], file_paths[2])
        self.capture_names.put(obj)

    def print_camera_preview(self):
        img = self.view.lv.image
        self.printer.print_image(img)

    @staticmethod
    def load_captured_image(file_path):
        img = pygame.image.load(file_path).convert()
        return img

    def enqueue_animate_montage(self, img_list):
        self.view.lv.enqueue_animate_montage(img_list, self.conf["control"]["montage_fps"])

    def notify_idle_previews_changed(self):
        prev_num = 1
        for img_list in self.model.get_idle_previews_image_lists():
            #logger.debug("preview[%d] = %s <- %s" % (prev_num, self.view.idle_previews[prev_num], img_list))
            self.view.idle_previews[prev_num].start_animate(img_list, 0) # if fps == 0 -> sync whith display FPS
            prev_num += 1

    def notify_finished_session(self, sess):
        """ Start work related with finished session processing - uploading and printing"""
        self.printer.print_session(sess.id, sess.medium_img_list)
        if self.conf["upload"]["enabled"]:
            self.upload_pipe.send((sess.id, sess.get_medium_img_paths(), sess.get_full_img_paths()))
