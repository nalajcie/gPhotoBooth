# encoding: utf-8
import os
import time
import datetime
import random
import math

from upload import get_stamp_filename

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
        self.model.controller.set_text(self.model.conf['m']['start_pushbutton'])

    def update(self, button_pressed):
        if button_pressed:
            self.model.capture_start = datetime.datetime.now()
            return CountdownState(self.model, self.model.conf['control']['initial_countdown_secs'])
        return self


class TimedState(SessionState):
    """ Base class for state with timeout """
    def __init__(self, model, timer_length_s):
        super(TimedState, self).__init__(model)
        self.timer = time.time() + timer_length_s
        self.duration = timer_length_s

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
            self.model.controller.live_view_hide_arrow()
            return TakePictureState(self.model)
        else:
            self.display_countdown()
            return self

    def display_countdown(self):
        """ as the name says... """
        time_remaining = self.timer - time.time()

        text = u"%d" % int(time_remaining + 1)
        if time_remaining < 2:
            if int(time_remaining * 2) % 2 == 0:
                self.model.controller.live_view_show_arrow()
            else:
                self.model.controller.live_view_hide_arrow()
        self.model.controller.set_text(text, True)


class TakePictureState(SessionState):
    """ taking single picture """
    def __init__(self, model):
        super(TakePictureState, self).__init__(model)
        image_name = self.take_picture()

        # if this is the last image, do not fire up the live view after the shoot
        if self.model.photo_count == 4:
            self.model.controller.schedule_stop_live_view(self.model.images[1][1])

        logger.debug("TakePictureState: taking picutre: %s", image_name)
        self.model.controller.set_text(self.model.conf['m']['after_capture'][self.model.photo_count])

    def update(self, button_pressed):
        if self.model.photo_count == 4:
            if self.model.photo_count in self.model.images: # wait for image to be taken before going futher
                return ShowSessionMontageState(self.model)
            else:
                return self
        else:
            if self.model.controller.is_live_view_overlay_finished():
                # live view will be resumed ASAP by controller after taking the image
                return CountdownState(self.model, self.model.conf['control']['midphoto_countdown_secs'])
            else:
                return self

    def take_picture(self):
        """ as the name says... """
        self.model.photo_count += 1
        image_names = self.booth_model.get_image_names_all(self.model.id, self.model.photo_count)

        self.model.controller.capture_image(self.model.photo_count, image_names)
        return image_names[0]

class ShowSessionMontageState(TimedState):
    """ Showing animation at the end of the session """
    def __init__(self, model):
        super(ShowSessionMontageState, self).__init__(model, model.conf['control']['montage_display_secs'])

        img_lv_list = [sizes[1] for sizes in self.model.images.itervalues()]
        self.model.controller.enqueue_animate_montage(img_lv_list)

        self.text_arr = self.model.conf['m']['during_merge'].strip().split("\n")
        self.single_text_duration = float(self.duration) / len(self.text_arr)

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
        if time_remaining <= 0:
            return

        idx = int(math.ceil(time_remaining / self.single_text_duration))
        self.model.controller.set_text(self.text_arr[-idx])


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

        # start lights
        self.controller.lights.start()

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
        if self.booth_model.is_first_session:
            return False # first session is the setup session, without timeout
        else:
            return not self.capture_start and time.time() - self.session_start > self.conf['control']['idle_secs']

    def get_finished_session_model(self):
        prev_images = [sizes[2] for sizes in self.images.itervalues()]
        medium_images = [sizes[1] for sizes in self.images.itervalues()]
        return FinishedSessionModel(self.booth_model, self.id, prev_images, medium_images, self.conf['random_tags'])

    def finished(self):
        """ returns True if this session is finished """
        return self.state is None

class FinishedSessionModel(object):
    """ finised session previews to be displayed in idle screen """
    def __init__(self, booth_model, sess_id, img_list, medium_img_list, random_tags_conf):
        self.id = sess_id
        self.booth_model = booth_model
        self.img_list = img_list
        self.medium_img_list = medium_img_list
        self.random_tags = []
        if random_tags_conf and random_tags_conf['enabled']:
            self.random_tags = random.sample(random_tags_conf['list'], random_tags_conf['count'])


    def get_medium_img_paths(self):
        return [self.booth_model.get_image_name(self.id, photo_no, 'medium') for photo_no in xrange(1, 5)]

    def get_full_img_paths(self):
        return [self.booth_model.get_image_name(self.id, photo_no, 'full') for photo_no in xrange(1, 5)]

    @classmethod
    def from_dir(cls, booth_model, sess_id, conf):
        """ trying to create FinishedSession from directory """
        img_list = []
        for num in xrange(1, 5):
            img_name = booth_model.get_image_name(sess_id, num, 'prev')
            try:
                img = booth_model.controller.load_captured_image(img_name)
                img_list.append(img)
            except Exception:
                raise ValueError # error while opening/reading file, incomplete photo session

        return cls(booth_model, sess_id, img_list, None, conf['random_tags']) # do not care about medium images


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
        self.is_first_session = True

    def load_from_disk(self):
        """ try to load FinishedSessions from the disk """
        all_sessions = []
        to_upload_sessions = []
        for dirname in os.listdir(self.conf['event_dir']):
            #logger.debug("SCANNING: '%s'" % d)
            path = os.path.join(self.conf['event_dir'], dirname)
            if os.path.isdir(path):
                try:
                    sess_id = int(dirname)
                except ValueError:
                    sess_id = None
                if sess_id:
                    try:
                        sess = FinishedSessionModel.from_dir(self, sess_id, self.conf)
                        all_sessions.append(sess)
                        is_uploaded = os.path.exists(get_stamp_filename(path + "/"))
                        if not is_uploaded:
                            to_upload_sessions.append(sess)
                        logger.info("PHOTO_SESS : '%s' = %s (uploaded: %s)", dirname, sess, is_uploaded)
                    except ValueError:
                        #logger.debug("\t%d: incomplete session" % sess_id)
                        pass
                    # even if it's incompelete, we can't reuse the ID
                    self.next_photo_session = max(self.next_photo_session, sess_id + 1)

        all_sessions.sort(key=lambda x: x.id)
        to_upload_sessions.sort(key=lambda x: x.id)
        self.finished_sessions = all_sessions
        self.update_finished()
        return to_upload_sessions

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
        return os.path.join(self.conf['event_dir'], str(sess_id))

    def get_image_name(self, sess_id, count, img_type):
        """ get image file name for a given type"""
        if img_type == 'full':
            img_filename = str(count) + '.jpg'
        else:
            img_filename = str(count) + '_' + img_type + '.jpg'
        return os.path.join(self.conf['event_dir'], str(sess_id), img_filename)

    def get_image_names_all(self, sess_id, count):
        """ get image file names for all sizes """
        return [self.get_image_name(sess_id, count, img_type) for img_type in ['full', 'medium', 'prev']]

    def start_new_session(self):
        """ work to be done when new session starts """
        logging.debug("PhotoSession START")
        os.mkdir(self.get_session_dir(self.next_photo_session))
        self.current_sess = PhotoSessionModel(self, self.next_photo_session)
        self.next_photo_session += 1
        self.controller.view.idle = False

        # start lights
        self.controller.lights.start()

    def end_session(self):
        """ work to be done when session ends """
        self.is_first_session = False # first session is the setup one, next will timeout in idle
        # stop the lights
        self.controller.lights.pause()

        if self.current_sess.finished():
            self.finished_sessions.append(self.current_sess.get_finished_session_model())
            self.update_finished()
        self.current_sess = None
        self.controller.stop_live_view()
        self.controller.view.idle = True

    def update_finished(self):
        """ update idle previews with finished sessions """
        self.finished_sessions = self.finished_sessions[-self.conf['control']['idle_previews_cnt']:]
        #logger.info("FINISED SESSIONS CNT: %d", len(self.finished_sessions))
        self.controller.notify_idle_previews_changed()

    #generator!
    def get_idle_previews_image_lists(self):
        """ generator for passing images to the view """
        for sess in reversed(self.finished_sessions):
            yield sess.img_list

    def quit(self):
        """ any cleaning needed - put it here """
        pass

