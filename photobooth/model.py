import os
import time
import datetime

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

# this is the model, allow few public methods
# pylint: disable=too-few-public-methods

class SessionState(object):
    """ Base class for PhotoSession state """
    def __init__(self, model):
        self.model = model
        self.booth_model = model.booth_model

    def update(self, button_pressed):
        """ state update & transitin method """
        raise NotImplementedError("Update not implemented")

class WaitingState(SessionState):
    """ waiting for button push """
    def __init__(self, model):
        super(WaitingState, self).__init__(model)
        self.model.controller.start_live_view()
        self.model.controller.set_text("Push when ready!")

    def update(self, button_pressed):
        if button_pressed:
            self.model.capture_start = datetime.datetime.now()
            return CountdownState(self.model, self.model.conf.initial_countdown_secs)
        return self


class TimedState(SessionState):
    """ Base class for state with timeout """
    def __init__(self, model, timer_length_s):
        super(TimedState, self).__init__(model)
        self.timer = time.time() + timer_length_s

    def time_up(self):
        """ helper to check for timeout """
        return self.timer <= time.time()

    def update(self, button_pressed):
        """ state update & transitin method """
        raise NotImplementedError("Update not implemented")

class CountdownState(TimedState):
    """ counting down to the first/next photo """
    def __init__(self, session, countdown_time):
        super(CountdownState, self).__init__(session, countdown_time)
        self.capture_start = datetime.datetime.now()

    def update(self, button_pressed):
        if self.time_up():
            return TakePictureState(self.model)
        else:
            self.display_countdown()
            return self

    def display_countdown(self):
        """ as the name says... """
        time_remaining = self.timer - time.time()

        if time_remaining <= 0:
            # TODO
            #self.session.booth.display_camera_arrow(clear_screen=True)
            pass
        else:
            text = "Taking picture %d / 4 in: %d" % ((self.model.photo_count + 1), int(time_remaining + 1))
            if time_remaining < 2:
                if int(time_remaining * 2) % 2 == 1:
                    #lines = ["Look at the camera!", ""] + lines
                    # TODO: show arrow + "LOOK"
                    #self.session.booth.display_camera_arrow()
                    pass
                else:
                    # TODO: do not show arrow + "LOOK"
                    pass
            self.model.controller.set_text(text)


class TakePictureState(TimedState):
    """ taking single picture """
    def __init__(self, model):
        super(TakePictureState, self).__init__(model, model.conf.image_display_secs)
        image_name = self.take_picture()
        logger.debug("TakePictureState: taking picutre: %s", image_name)
        self.model.controller.set_text("Nice!")

    def update(self, button_pressed):
        if self.model.photo_count in self.model.images:
            if self.model.photo_count == 4:
                return ShowSessionMontageState(self.model)
            else:
                self.model.controller.resume_live_view()
                return CountdownState(self.model, self.model.conf.midphoto_countdown_secs)
        else:
            return self

    def take_picture(self):
        """ as the name says... """
        self.model.photo_count += 1
        image_name = self.booth_model.get_image_name(self.model.id, self.model.photo_count)
        image_medium_name = self.booth_model.get_image_medium_name(self.model.id, self.model.photo_count)
        image_prev_name = self.booth_model.get_image_prev_name(self.model.id, self.model.photo_count)

        self.model.controller.capture_image(self.model.photo_count, image_name, image_medium_name, image_prev_name)
        return image_name

class ShowSessionMontageState(TimedState):
    """ Showing animation at the end of the session """
    def __init__(self, model):
        super(ShowSessionMontageState, self).__init__(model, model.conf.montage_display_secs)

        img_lv_list = [sizes[1] for sizes in self.model.images.itervalues()]
        self.model.controller.stop_live_view()
        self.model.controller.enqueue_animate_montage(img_lv_list)

        # start work on finished session
        finished_sess = self.model.get_finished_session_model()
        self.model.controller.notify_finished_session(finished_sess)

    def update(self, button_pressed):
        if self.time_up():
            return None
        else:
            self.update_text()
            return self

    def update_text(self):
        """ updating funny text in the textarea """
        time_remaining = self.timer - time.time()

        int_time = int(time_remaining)
        if int_time == 4:
            self.model.controller.set_text("Generating GIF...")
        elif int_time == 3:
            self.model.controller.set_text("Uploading...")
        elif int_time == 2:
            self.model.controller.set_text("Printing...")
        elif int_time == 1:
            self.model.controller.set_text("Enjoying time with You...")

class PhotoSessionModel(object):
    """
    Single Photo Session model (holding global attributes) and state machine
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, photo_booth_model, sess_id):
        logger.info("Starting new photo session, id=%d", sess_id)
        self.booth_model = photo_booth_model
        self.controller = self.booth_model.controller
        self.conf = self.controller.conf
        self.id = sess_id

        # global model variables used by different states
        self.state = WaitingState(self)
        self.capture_start = None
        self.photo_count = 0
        self.session_start = time.time()

        self.images = dict()
        self.href = None

    def update(self, button_pressed):
        """ model updating func - transitins to next states """
        self.state = self.state.update(button_pressed)

    def idle(self):
        """ true/false idle timeout check """
        return not self.capture_start and time.time() - self.session_start > self.conf.idle_secs

    def get_finished_session_model(self):
        medium_image_names = [self.booth_model.get_image_medium_name(self.id, photo_no) for photo_no in xrange(1, 5)]
        lv_images = [sizes[2] for sizes in self.images.itervalues()]
        return FinishedSessionModel(self.booth_model, self.id, lv_images, medium_image_names)

    def finished(self):
        """ returns True if this session is finished """
        return self.state is None

class FinishedSessionModel(object):
    """ finised session previews to be displayed in idle screen """
    def __init__(self, booth_model, sess_id, img_list, medium_img_paths):
        self.id = sess_id
        self.booth_model = booth_model
        self.img_list = img_list
        self.medium_img_paths = medium_img_paths

    @classmethod
    def from_dir(cls, booth_model, sess_id):
        """ trying to create FinishedSession from directory """
        img_list = []
        for num in xrange(1, 5):
            img_name = booth_model.get_image_prev_name(sess_id, num)
            try:
                img = booth_model.controller.load_captured_image(img_name)
                img_list.append(img)
            except Exception:
                raise ValueError # error while opening/reading file, incomplete photo session

        return cls(booth_model, sess_id, img_list, None) # do not care about medium image paths


class PhotoBoothModel(object):
    """
    PhotoBooth model serving multiple PhotoSessions in it's life
    """
    def __init__(self, controller):
        self.conf = controller.conf
        self.controller = controller
        self.current_sess = None
        self.next_photo_session = 1
        self.finished_sessions = []

    def load_from_disk(self):
        """ try to load FinishedSessions from the disk """
        all_sessions = []
        for dirname in os.listdir(self.conf.save_path):
            #logger.debug("SCANNING: '%s'" % d)
            path = os.path.join(self.conf.save_path, dirname)
            if os.path.isdir(path):
                try:
                    sess_id = int(dirname)
                except ValueError:
                    sess_id = None
                if sess_id:
                    try:
                        sess = FinishedSessionModel.from_dir(self, sess_id)
                        all_sessions.append(sess)
                        logger.info("PHOTO_SESS : '%s' = %s", dirname, sess)
                    except ValueError:
                        #logger.debug("\t%d: incomplete session" % sess_id)
                        pass
                    # even if it's incompelete, we can't reuse the ID
                    self.next_photo_session = max(self.next_photo_session, sess_id + 1)

        all_sessions.sort(key=lambda x: x.id)
        self.finished_sessions = all_sessions
        self.update_finished()

    def update(self, button_pressed):
        """ updates current session """
        if self.current_sess:
            self.current_sess.update(button_pressed)
            if self.current_sess.finished():
                self.end_session()
            elif self.current_sess.idle():
                self.end_session()

        else:
            if button_pressed:
                self.start_new_session()

    def set_current_session_imgs(self, image_number, images):
        """ add new images to the current session
        (used by the controller after image capture) """
        self.current_sess.images[image_number] = images

    def get_session_dir(self, sess_id):
        """ get session dir name """
        return os.path.join(self.conf.save_path, str(sess_id))

    def get_image_name(self, sess_id, count):
        """ get full image file name """
        return os.path.join(self.conf.save_path, str(sess_id), str(count) + '.jpg')

    def get_image_medium_name(self, sess_id, count):
        """ get medium image file name """
        return os.path.join(self.conf.save_path, str(sess_id), str(count) + '_medium.jpg')

    def get_image_prev_name(self, sess_id, count):
        """ get preview file name """
        return os.path.join(self.conf.save_path, str(sess_id), str(count) + '_prev.jpg')

    def start_new_session(self):
        """ work to be done when new session starts """
        logging.debug("PhotoSession START")
        os.mkdir(self.get_session_dir(self.next_photo_session))
        self.current_sess = PhotoSessionModel(self, self.next_photo_session)
        self.next_photo_session += 1
        self.controller.view.idle = False

    def end_session(self):
        """ work to be done when session ends """
        logging.debug("PhotoSession END")
        if self.current_sess.finished():
            self.finished_sessions.append(self.current_sess.get_finished_session_model())
            self.update_finished()
        self.current_sess = None
        self.controller.stop_live_view()
        self.controller.view.idle = True

    def update_finished(self):
        """ update idle previews with finished sessions """
        self.finished_sessions = self.finished_sessions[-self.conf.idle_previews_cnt:]
        logger.info("FINISED SESSIONS CNT: %d", len(self.finished_sessions))
        self.controller.notify_idle_previews_changed()

    #generator!
    def get_idle_previews_image_lists(self):
        """ generator for passing images to the view """
        for sess in reversed(self.finished_sessions):
            yield sess.img_list

    def quit(self):
        """ any cleaning needed - put it here """
        pass

