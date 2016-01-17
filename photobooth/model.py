import os
import time
import datetime

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class SessionState(object):
    def __init__(self, model):
        self.model = model
        self.booth_model = model.booth_model

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
            image_name = self.take_picture()
            return ShowLastCaptureState(self.model, image_name)
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
        image_name = self.booth_model.get_image_name(self.model, self.model.photo_count)
        self.model.controller.capture_image(image_name)
        return image_name

class ShowLastCaptureState(TimedState):
    def __init__(self, model, image_name):
        super(ShowLastCaptureState, self).__init__(model, model.conf.image_display_secs)
        self.model.controller.set_text([])
        self.model.set_captured_image(image_name)

    def update(self, button_pressed):
        if self.time_up():
            if self.model.photo_count == 4:
                #TODO
                #return None
                return ShowSessionMontageState(self.model)
            else:
                self.model.controller.start_live_view()
                return CountdownState(self.model, self.model.conf.midphoto_countdown_secs)
        else:
            return self

class ShowSessionMontageState(TimedState):
    def __init__(self, model):
        super(ShowSessionMontageState, self).__init__(model, model.conf.montage_display_secs)

        img_lv_list = [ sizes[1] for num, sizes in self.model.images.items()  ]
        self.model.controller.animate_montage(img_lv_list)

    def update(self, button_pressed):
        if self.time_up():
            return None
        else:
            return self

class PhotoSessionModel(object):
    """
    Single Photo Session model (holding global attributes) and state machine
    """
    def __init__(self, photo_booth_model, id):
        logger.info("Starting new photo session, id=%d" % id)
        self.booth_model = photo_booth_model
        self.controller = self.booth_model.controller
        self.conf = self.controller.conf
        self.id = id

        # global model variables used by different states
        self.state = WaitingState(self)
        self.capture_start = None
        self.photo_count = 0
        self.session_start = time.time()

        self.images = dict()

    def update(self, button_pressed):
        self.state = self.state.update(button_pressed)

    def idle(self):
        return not self.capture_start and time.time() - self.session_start > self.conf.idle_secs

    def set_captured_image(self, image_name):
        img = self.controller.load_captured_image(image_name)
        img_lv = self.controller.scale_image_for_lv(img)
        img_prev = self.controller.scale_and_save_image_for_preview(img_lv, self.booth_model.get_image_prev_name(self, self.photo_count))

        self.images[self.photo_count] = (img, img_lv, img_prev)
        self.controller.notify_captured_image(self.photo_count, img, img_prev)

    def finished(self):
        return self.state is None

class PhotoBoothModel(object):
    """
    PhotoBooth model serving multiple PhotoSessions in it's life
    """
    def __init__(self, controller):
        self.conf = controller.conf
        self.controller = controller
        self.current_sess = None
        self.next_photo_session = 1
        self.load_from_disk()

    def load_from_disk(self):
        for d in os.listdir(self.conf.save_path):
            logger.debug("SCANNING: '%s'" % d)
            try:
                sess_id = int(d)
            except ValueError:
                sess_id = None
            if sess_id:
                logger.debug("PHOTO_SESS : '%s' = %d" % (d, sess_id))
                # TODO: load from disk for previews in idle screen
                self.next_photo_session = max(self.next_photo_session, sess_id + 1)
            pass


    def update(self, button_pressed):
        if self.current_sess:
            self.current_sess.update(button_pressed)
            if self.current_sess.finished():
                self.end_session()
                self.start_new_session() # if previous session ended succsesfully, we will immediately start a new one
            elif self.current_sess.idle():
                self.end_session()

        else:
            if button_pressed:
                self.start_new_session()

    def get_session_dir(self, sess_id):
        return os.path.join(self.conf.save_path, str(sess_id))

    def get_image_name(self, photo_sess, count):
        return os.path.join(self.conf.save_path, str(photo_sess.id), str(count) + '.jpg')

    def get_image_prev_name(self, photo_sess, count):
        return os.path.join(self.conf.save_path, str(photo_sess.id), str(count) + '_prev.jpg')
        #self.capture_start.strftime('%Y-%m-%d-%H%M%S') + '-' + str(count) + '.jpg'

    def start_new_session(self):
        logging.debug("PhotoSession START")
        os.mkdir(self.get_session_dir(self.next_photo_session))
        self.current_sess = PhotoSessionModel(self, self.next_photo_session)
        self.next_photo_session += 1;
        self.controller.view.idle = False

    def end_session(self):
        logging.debug("PhotoSession END")
        self.controller.view.idle = True
        self.current_sess = None

    def quit(self):
        # any cleaning needed - put it here
        pass

