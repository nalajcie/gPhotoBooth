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


class InitState(TimedState):
    """ first state when photobooth is started (only once).
    May be used to some additional graphics show which may take time """
    def __init__(self, model):
        super(InitState, self).__init__(model, model.conf['control']['booth_init_secs'])

        ext_ip = self.model.controller.get_external_ip()
        logger.info("EXTERNAL IP = %s", ext_ip)
        self.model.controller.set_info_text("IP = " + ext_ip)

    def update(self, button_pressed):
        if self.time_up():
            return WaitingState(self.model)
        else:
            return self


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


class VideoBoothModel(object):
    """
    VideoBooth model serving multiple PhotoSessions in it's life
    """
    def __init__(self, controller):
        self.conf = controller.conf
        self.controller = controller
        self.state = InitState(self)

    def update(self, button_pressed):
        """ model updating func - transitins to next states """
        self.state = self.state.update(button_pressed)


    def quit(self):
        """ any cleaning needed - put it here """
        pass

