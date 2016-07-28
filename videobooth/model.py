# encoding: utf-8
import os
import time
import datetime
import random
import math

import logging
logger = logging.getLogger('videobooth.%s' % __name__)

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
        self.model.controller.set_info_text(self.model.conf['m']['start_pushbutton'])

    def update(self, button_pressed):
        if button_pressed:
            self.model.capture_start = datetime.datetime.now()
            return CountdownState(self.model)
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
        """ state update & transition method """
        raise NotImplementedError("Update not implemented")

class CountdownState(TimedState):
    """ counting down to the movie recording start """
    def __init__(self, model):
        super(CountdownState, self).__init__(model, model.conf['control']['initial_countdown_secs'])
        self.model.controller.lights.start()

    def update(self, button_pressed):
        if self.time_up():
            return RecordMovieState(self.model)
        else:
            self.display_countdown()
            return self

    def display_countdown(self):
        """ as the name says... """
        time_remaining = self.timer - time.time()
        text = u"%d" % int(time_remaining + 1)
        self.model.controller.set_info_text(text, big=True)

class RecordMovieState(TimedState):
    """ counting down to the first/next photo """
    def __init__(self, model):
        super(RecordMovieState, self).__init__(model, model.conf['control']['movie_length_secs'])
        self.model.controller.start_recording()

    def update(self, button_pressed):
        if self.time_up():
            return FinishMovieState(self.model)
        else:
            self.display_countdown()
            return self

    def display_countdown(self):
        """ as the name says... """
        time_remaining = self.timer - time.time()
        text = u"0:%02d" % int(time_remaining + 1)
        self.model.controller.set_rec_text(text)

class FinishMovieState(TimedState):
    """ waiting for button push """
    def __init__(self, model):
        super(FinishMovieState, self).__init__(model, model.conf['control']['movie_finish_secs'])
        self.model.controller.stop_recording()
        self.model.controller.set_info_text(self.model.conf['m']['movie_finish_text'])
        self.model.controller.lights.pause()

    def update(self, button_pressed):
        if self.time_up():
            return WaitingState(self.model)
        return self



class VideoSessionModel(object):
    """
    Single Photo Session model (holding global attributes) and state machine
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, video_booth_model, sess_id):
        logger.info("Starting new photo session, id=%d", sess_id)
        self.booth_model = video_booth_model
        self.controller = self.booth_model.controller
        self.conf = self.controller.conf
        self.id = sess_id

        # start lights
        self.controller.lights.start()

        # global model variables used by different states
        self.state = WaitingState(self)
        self.capture_start = None
        self.session_start = time.time()

        self.images = dict()
        self.href = None

    def update(self, button_pressed):
        """ model updating func - transitins to next states """
        self.state = self.state.update(button_pressed)

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


class VideoBoothModel(object):
    """
    VideoBooth model serving multiple PhotoSessions in it's life
    """
    def __init__(self, controller):
        self.conf = controller.conf
        self.controller = controller
        self.current_sess = None
        self.next_photo_session = 1
        self.finished_sessions = []
        self.is_first_session = True

    def update(self, button_pressed):
        """ updates current session """
        if self.current_sess:
            self.current_sess.update(button_pressed)
            if self.current_sess.finished():
                self.end_session()

        else:
            if button_pressed:
                self.start_new_session()

    def start_new_session(self):
        """ work to be done when new session starts """
        logging.debug("PhotoSession START")
        self.current_sess = VideoSessionModel(self, self.next_photo_session)
        self.next_photo_session += 1

        # start lights
        #self.controller.lights.start()

    def end_session(self):
        """ work to be done when session ends """
        # stop the lights
        self.controller.lights.pause()

        if self.current_sess.finished():
            self.finished_sessions.append(self.current_sess.get_finished_session_model())
        self.current_sess = None


    def quit(self):
        """ any cleaning needed - put it here """
        pass

