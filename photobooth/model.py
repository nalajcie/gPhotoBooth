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
        image_name = self.booth_model.get_image_name(self.model.id, self.model.photo_count)
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
        img_prev = self.controller.scale_and_save_image_for_preview(img_lv, self.booth_model.get_image_prev_name(self.id, self.photo_count))

        self.images[self.photo_count] = (img, img_lv, img_prev)
        self.controller.notify_captured_image(self.photo_count, img, img_prev)

    def get_finished_session_model(self):
        return FinishedSessionModel(self.booth_model, self.id, [ sizes[2] for k, sizes in self.images.items() ])

    def finished(self):
        return self.state is None

class FinishedSessionModel(object):
    """ finised session previews to be displayed in idle screen """
    def __init__(self, booth_model, sess_id, img_list):
        self.id = sess_id
        self.booth_model = booth_model
        self.img_list = img_list

    @classmethod
    def fromDir(cls, booth_model, sess_id):
        img_list = []
        for num in xrange(1, 5):
            img_name = booth_model.get_image_prev_name(sess_id, num)
            try:
                img = booth_model.controller.load_captured_image(img_name)
                img_list.append(img)
            except Exception, e:
                logger.exception(e)
                raise ValueError # error while opening/reading file, incomplete photo session

        return cls(booth_model, sess_id, img_list)


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
        all_sessions = []
        for d in os.listdir(self.conf.save_path):
            logger.debug("SCANNING: '%s'" % d)
            path = os.path.join(self.conf.save_path, d)
            if os.path.isdir(path):
                try:
                    sess_id = int(d)
                except ValueError:
                    sess_id = None
                if sess_id:
                    try:
                        sess = FinishedSessionModel.fromDir(self, sess_id)
                        all_sessions.append(sess)
                        logger.debug("PHOTO_SESS : '%s' = %s" % (d, sess))
                    except ValueError:
                        logger.info("\t%d: incomplete session" % sess_id)
                    # even if it's incompelete, we can't reuse the ID
                    self.next_photo_session = max(self.next_photo_session, sess_id + 1)

        all_sessions.sort(key=lambda x: x.id)
        self.finished_sessions = all_sessions
        self.update_finished()

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

    def get_image_name(self, sess_id, count):
        return os.path.join(self.conf.save_path, str(sess_id), str(count) + '.jpg')

    def get_image_prev_name(self, sess_id, count):
        return os.path.join(self.conf.save_path, str(sess_id), str(count) + '_prev.jpg')
        #self.capture_start.strftime('%Y-%m-%d-%H%M%S') + '-' + str(count) + '.jpg'

    def start_new_session(self):
        logging.debug("PhotoSession START")
        os.mkdir(self.get_session_dir(self.next_photo_session))
        self.current_sess = PhotoSessionModel(self, self.next_photo_session)
        self.next_photo_session += 1;
        self.controller.view.idle = False

    def end_session(self):
        logging.debug("PhotoSession END")
        if self.current_sess.finished():
            self.finished_sessions.append(self.current_sess.get_finished_session_model())
            self.update_finished()
        self.current_sess = None
        self.controller.view.idle = True

    def update_finished(self):
        """ update idle previews with finished sessions """
        self.finished_sessions = self.finished_sessions[-self.conf.idle_previews_cnt:]
        logger.info("FINISED SESSIONS CNT: %d" % len(self.finished_sessions))
        self.controller.notify_idle_previews_changed()

    #generator!
    def get_idle_previews_image_lists(self):
        for sess in reversed(self.finished_sessions):
            yield sess.img_list

    def quit(self):
        # any cleaning needed - put it here
        pass

