#!/usr/bin/env python
#NOTE: you have to install wiringpi2 python wrapper
# sudo apt-get install python-dev
# sudo pip install wiringpi2

import wiringpi2
import time

LED_PIN = 18    # GPIO -> board pin 12
LED_FREQ = 100  # in Hz

LED_DUTY_MAX = 1024
LED_DUTY_MIN = 128
LED_DUTY_STEP= 16

BUTTON_PIN = 16

#WARN: the below line requires root
wiringpi2.wiringPiSetupGpio()
wiringpi2.pinMode(LED_PIN, 2)  # hardware PWM mode


def button_raw_press(channel):
    print "BUTTON PRESS!"

#GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_raw_press, bouncetime=500)

try:
    while True:
        for i in xrange(LED_DUTY_MIN, LED_DUTY_MAX + 1, LED_DUTY_STEP):
            wiringpi2.pwmWrite(LED_PIN, i)
            time.sleep(0.02)

        time.sleep(0.5)

        for i in xrange(LED_DUTY_MAX, LED_DUTY_MIN - 1, -LED_DUTY_STEP):
            wiringpi2.pwmWrite(LED_PIN, i)
            time.sleep(0.02)

        #time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    pass
