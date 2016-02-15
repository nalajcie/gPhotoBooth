import base
import wiringpi2
import time
import subprocess
from threading import Thread

import logging
logger = logging.getLogger('platform.%s' % __name__)

# Note: this is actually a Pi2, see the wiring diagram for the details

def platform_init():
    wiringpi2.wiringPiSetupGpio()
    # enable RTS/CTS pins for ttyAMA0 (needed by ThermalPrinter)
    subprocess.call(["gpio", "-g", "mode", "16", "alt3"])
    subprocess.call(["gpio", "-g", "mode", "17", "alt3"])

def platform_deinit():
    GPIO.cleanup()

class Button(base.Peripherial):
    LED_PIN = 18    # GPIO

    LED_DUTY_MAX = 1024
    LED_DUTY_MIN = 128
    LED_DUTY_STEP= 16

    BUTTON_PIN = 23 # detecting button pushes (GPIO)
    DEBOUNCE_MS = 20

    def __init__(self):
        # button
        wiringpi2.pinMode(self.BUTTON_PIN, wiringpi2.GPIO.INPUT)
        wiringpi2.pullUpDnControl(self.BUTTON_PIN, wiringpi2.GPIO.PUD_UP)
        wiringpi2.wiringPiISR(self.BUTTON_PIN, wiringpi2.GPIO.INT_EDGE_BOTH, self.button_raw_press)
        self.button_callback = None

        # hardware PWM led
        wiringpi2.pinMode(self.LED_PIN, wiringpi2.GPIO.PWM_OUTPUT)
        self.thread_pwm_worker = Thread(target=self.pwm_worker)
        self.thread_pwm_worker.setDaemon(True)

    def __del__(self):
        wiringpi2.pwmWrite(self.LED_PIN, 0)

    def start(self):
        self.thread_pwm_worker.start()

    def pwm_worker(self):
        """ run in different thread """
        while True:
            for i in xrange(self.LED_DUTY_MIN, self.LED_DUTY_MAX + 1, self.LED_DUTY_STEP):
                wiringpi2.pwmWrite(self.LED_PIN, i)
                time.sleep(0.02)

            time.sleep(0.5)

            for i in xrange(self.LED_DUTY_MAX, self.LED_DUTY_MIN - 1, -self.LED_DUTY_STEP):
                wiringpi2.pwmWrite(self.LED_PIN, i)
                time.sleep(0.02)


    def pause(self):
        """ Pause long-running task (for whatever reason) """
        pass

    def button_raw_press(self):
        if not self.button_callback:
            return

        time.sleep(self.DEBOUNCE_MS // 1000)
        if not wiringpi2.digitalRead(self.BUTTON_PIN):
            logger.info("button press detected!")
            self.button_callback()

    def register_callback(self, callback_f):
        """ Register callback for peripherial event """
        self.button_callback = callback_f

class Lights(base.Peripherial):
    #TODO
    pass


