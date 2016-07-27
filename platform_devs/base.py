
# pure interface - by default does nothing to support Dummy perpherials

class Peripherial(object):
    def __init__(self):
        """ Initialize peripherial. May take some time """
        pass

    def __del__(self):
        """ Peripherial destructor """
        pass

    def start(self):
        """ If there is some long going task (in separathe thread ?), start performing it now. Will never end """
        pass

    def pause(self):
        """ Pause long-running task (for whatever reason) """
        pass

    def register_callback(self, callback):
        """ Register callback for peripherial event """
        pass

    def update_state(self):
        """ Called upon every main loop "update" """
        pass
