# encoding: utf-8
import base
import wiringpi2
import time
import subprocess
from threading import Thread

import logging
logger = logging.getLogger('photobooth.platform.%s' % __name__)

# Note: this is actually a Pi2, see the wiring diagram for the details

def platform_init():
    wiringpi2.wiringPiSetupGpio()
    # enable RTS/CTS pins for ttyAMA0 (needed by ThermalPrinter)
    subprocess.call(["gpio", "-g", "mode", "16", "alt3"])
    subprocess.call(["gpio", "-g", "mode", "17", "alt3"])

def platform_deinit():
    pass

def platform_poweroff():
    """ power off Pi gracefully on long press release """
    subprocess.call(["sudo", "poweroff"])

class Button(base.Peripherial):
    """ Controlling hadware button with LED """
    LED_PIN = 18    # GPIO

    LED_DUTY_MAX = 1024
    LED_DUTY_MIN = 128
    LED_DUTY_STEP= 16

    BUTTON_PIN = 23 # detecting button pushes (GPIO)
    DEBOUNCE_MS = 20
    LONGPRESS_SEC = 7

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
        self.pwm_worker_working = False
        self.button_pressed = 0

    def __del__(self):
        self.pwm_worker_working = False
        wiringpi2.pwmWrite(self.LED_PIN, 0)

    def start(self):
        self.pwm_worker_working = True
        self.thread_pwm_worker.start()

    def pwm_worker(self):
        """ run in different thread """
        while self.pwm_worker_working:
            for i in xrange(self.LED_DUTY_MIN, self.LED_DUTY_MAX + 1, self.LED_DUTY_STEP):
                wiringpi2.pwmWrite(self.LED_PIN, i)
                time.sleep(0.02)

            time.sleep(0.5)

            for i in xrange(self.LED_DUTY_MAX, self.LED_DUTY_MIN - 1, -self.LED_DUTY_STEP):
                wiringpi2.pwmWrite(self.LED_PIN, i)
                time.sleep(0.02)

        #exiting: poweroff the button:
        wiringpi2.pwmWrite(self.LED_PIN, 0)


    def pause(self):
        """ Pause long-running task (for whatever reason) """
        pass

    def update_state(self):
        if self.button_pressed > 0:
            if not wiringpi2.digitalRead(self.BUTTON_PIN):
                # button is still pressed
                if time.time() - self.button_pressed > self.LONGPRESS_SEC:
                    logger.info("LONG BUTTON PRESS - POWEROFF")
                    platform_poweroff()
            else: # button is released
                self.button_pressed = -1

    def button_raw_press(self):
        if not self.button_callback:
            return

        time.sleep(self.DEBOUNCE_MS // 1000)
        if not wiringpi2.digitalRead(self.BUTTON_PIN):
            logger.info("button press detected!")
            self.button_pressed = time.time()
            self.button_callback()

    def register_callback(self, callback_f):
        """ Register callback for peripherial event """
        self.button_callback = callback_f

class Lights(base.Peripherial):
    """ Controlling moddeling POWER LED lights """

    LIGHTS_PIN = 13 # GPIO -> board pin 33

    PWM_VAL_DEFAULT = 512
    PWM_VAL_MAX = 1024

    def __init__(self):
        # hardware PWM led
        wiringpi2.pinMode(self.LIGHTS_PIN, wiringpi2.GPIO.PWM_OUTPUT)

    def __del__(self):
        wiringpi2.pwmWrite(self.LIGHTS_PIN, 0)

    def start(self):
        wiringpi2.pwmWrite(self.LIGHTS_PIN, self.PWM_VAL_DEFAULT)

    def set_brightness(self, b):
        if b > self.PWM_VAL_MAX:
            b = self.PWM_VAL_MAX

        wiringpi2.pwmWrite(self.LIGHTS_PIN, b)

    def pause(self):
        wiringpi2.pwmWrite(self.LIGHTS_PIN, 0)


