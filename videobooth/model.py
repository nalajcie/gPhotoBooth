# encoding: utf-8
import time
import math

import logging
logger = logging.getLogger('videobooth.%s' % __name__)

# this is the model, allow few public methods
# pylint: disable=too-few-public-methods

class SessionState(object):
    """ Base class for PhotoSession state """
    def __init__(self, model):
        self.model = model
        self.controller = model.controller

    def update(self, button_pressed):
        """ state update & transitin method """
        raise NotImplementedError("Update not implemented")

class WaitingState(SessionState):
    """ waiting for button push """
    def __init__(self, model):
        super(WaitingState, self).__init__(model)
        self.controller.set_info_text(self.model.conf['m']['movie_idle_pushbutton'])

    def update(self, button_pressed):
        if button_pressed:
            return CountdownState(self.model)
        return self


class TimedState(SessionState):
    """ Base class for state with timeout """
    def __init__(self, model, timer_length_s):
        super(TimedState, self).__init__(model)
        self.timer = time.time() + timer_length_s
        self.duration = timer_length_s

    def running_secs(self):
        return self.duration - (self.timer - time.time())

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

        self.ext_ip = self.controller.get_external_ip() or "UNKNOWN"
        self.ext_ip_shown = False

    def update(self, button_pressed):
        # show external IF 2 secs after startup to let everything settle down
        if not self.ext_ip_shown and self.running_secs() > 2:
            self.controller.set_info_text("IP = " + self.ext_ip)
            self.ext_ip_shown = True

        if self.time_up():
            return WaitingState(self.model)
        else:
            return self


class CountdownState(TimedState):
    """ counting down to the movie recording start """
    def __init__(self, model):
        super(CountdownState, self).__init__(model, model.conf['control']['initial_countdown_secs'])
        self.controller.lights.start()

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
        self.controller.set_info_text(text, big=True)

class RecordMovieState(TimedState):
    """ counting down to the first/next photo """
    def __init__(self, model):
        super(RecordMovieState, self).__init__(model, model.conf['control']['movie_length_secs'])
        self.controller.start_recording()

        # create new post for uploading in the meantime
        mov_name = time.strftime("%Y-%m-%d %H:%M:%S")
        self.controller.upload.async_create_post(mov_name)
        self.create_post_res = None

    def update(self, button_pressed):
        if self.create_post_res is None:
            self.create_post_res = self.controller.upload.async_create_post_result()

        if self.time_up():
            return FinishMovieState(self.model, self.create_post_res)
        else:
            self.display_countdown()
            return self

    def display_countdown(self):
        """ as the name says... """
        time_remaining = self.timer - time.time()
        text = u"0:%02d" % int(time_remaining + 1)
        self.controller.set_rec_text(text)

class FinishMovieState(TimedState):
    """ waiting for button push """
    def __init__(self, model, create_post_res):
        super(FinishMovieState, self).__init__(model, model.conf['control']['movie_finish_secs'])
        self.create_post_res = create_post_res

        # asynchronously stop recording
        self.controller.stop_recording()
        self.recording_finished = False
        self.stop_rec_time = time.time()
        self.controller.lights.pause()

        # get correct ending message
        is_upload_possible = create_post_res is not None and len(create_post_res[0]) > 0
        if is_upload_possible:
            self.text_arr = self.model.conf['m']['movie_finish_text'].strip().split("\n")
        else:
            self.text_arr = self.model.conf['m']['movie_finish_text_no_upload'].strip().split("\n")
        self.single_text_duration = float(self.duration) / len(self.text_arr)

    def update(self, button_pressed):
        self.update_text()

        if not self.recording_finished:
            self.recording_finished = self.controller.check_recording_state(self.create_post_res)
            if self.recording_finished: # for DEBUG
                logger.debug("stop_recording time: %f seconds", (time.time() - self.stop_rec_time))

        if self.time_up():
            if not self.recording_finished:
                logger.warn("THE RECORDING HAS NOT BEEN FINISHED: display error")
                return ErrorState(self.model.conf['m']['error_camera_rec_stop'])
            return WaitingState(self.model)
        return self

    def update_text(self):
        """ updating funny text in the textarea """
        time_remaining = self.timer - time.time()
        if time_remaining <= 0:
            return

        idx = int(math.ceil(time_remaining / self.single_text_duration))
        self.controller.set_info_text(self.text_arr[-idx])


class ErrorState(TimedState):
    """ in case we've encountered some error, additionally notify the end-user """
    def __init__(self, model, text):
        super(ErrorState, self).__init__(model, model.conf['control']['error_info_secs'])
        self.model.set_info_text(text, color="ff0000")

    def update(self, button_pressed):
        if self.time_up():
            return WaitingState(self.model)
        else:
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

