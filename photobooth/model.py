import time
import datetime

import logging
logger = logging.getLogger('photobooth.%s' % __name__)

class SessionState(object):
    def __init__(self, model):
        self.model = model

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
            image = self.take_picture()
            return ShowLastCaptureState(self.model, image)
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
        image_name = self.model.get_image_name(self.model.photo_count)
        self.model.controller.capture_image(image_name)
        return image_name

class ShowLastCaptureState(TimedState):
    def __init__(self, model, image_name):
        super(ShowLastCaptureState, self).__init__(model, model.conf.image_display_secs)
        self.model.controller.set_text([])
        self.model.set_captured_image(image_name, self.model.photo_count)

    def update(self, button_pressed):
        if self.time_up():
            if self.model.photo_count == 4:
                #TODO
                return None
                #return ShowSessionMontageState(self.model)
            else:
                self.model.controller.start_live_view()
                return CountdownState(self.model, self.model.conf.midphoto_countdown_secs)
        else:
            return self

class PhotoSessionModel(object):
    """
    Photo session model (holding global attributes) and state machine
    """
    def __init__(self, controller):
        self.conf = controller.conf
        self.controller = controller

        # global model variables used by different states
        self.state = WaitingState(self)
        self.capture_start = None
        self.photo_count = 0
        self.session_start = time.time()

        self.image_names = dict()
        self.images = dict()

    def update(self, button_pressed):
        self.state = self.state.update(button_pressed)

    def quit(self):
        # any cleaning needed - put it here
        yield

    def idle(self):
        return not self.capture_start and time.time() - self.session_start > self.booth.idle_time

    def get_image_name(self, count):
        return self.capture_start.strftime('%Y-%m-%d-%H%M%S') + '-' + str(count) + '.jpg'

    def set_captured_image(self, image_name, image_number):
        img = self.controller.load_captured_image(image_name)

        self.image_names[image_number] = image_name
        self.images[image_number] = img

        self.controller.notify_captured_image(image_number)

    def finished(self):
        return self.state is None
