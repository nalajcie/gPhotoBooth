import base
import RPi.GPIO as GPIO
import time
from threading import Thread

# Note: this is actually a Pi2, see the wiring diagram for the details


def platform_init():
    GPIO.setmode(GPIO.BOARD)
    #TODO: set GPIO 16/17 to alt3

def platform_deinit():
    GPIO.cleanup()

class Button(base.Peripherial):
    LED_PIN = 12    # board pin no
    LED_FREQ = 100  # in Hz

    LED_DUTY_MAX = 100
    LED_DUTY_MIN = 10

    BUTTON_PIN = 16 # detecting button pushes

    def __init__(self):
        GPIO.setup(self.LED_PIN, GPIO.OUT)
        GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.pwm = GPIO.PWM(self.LED_PIN, self.LED_FREQ)

        self.thread_pwm_worker = Thread(target=self.pwm_worker)
        self.thread_pwm_worker.setDaemon(True)

    def __del__(self):
        self.pwm.stop()

    def start(self):
        self.pwm.start(0)
        self.thread_pwm_worker.start()

    def pwm_worker(self):
        """ run in different thread """
        while True:
            for i in xrange(self.LED_DUTY_MIN, self.LED_DUTY_MAX + 1):
                self.pwm.ChangeDutyCycle(i)
                time.sleep(0.02)

            time.sleep(0.5)

            for i in xrange(self.LED_DUTY_MAX, self.LED_DUTY_MIN - 1, -1):
                self.pwm.ChangeDutyCycle(i)
                time.sleep(0.02)


    def pause(self):
        """ Pause long-running task (for whatever reason) """
        pass

    def register_callback(self, callback_f):
        """ Register callback for peripherial event """
        GPIO.add_event_detect(self.BUTTON_PIN, GPIO.FALLING, callback=callback_f, bouncetime=500)

class Lights(base.Peripherial):
    #TODO
    pass


