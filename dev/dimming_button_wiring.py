#!/usr/bin/env python
#NOTE: you have to install wiringpi2 python wrapper
# sudo apt-get install python-dev
# sudo pip install wiringpi2

import wiringpi2
import time

LED_PIN = 18    # GPIO -> board pin 12
LIGHTS_PIN = 13 # GPIO -> board pin 33

LED_DUTY_MAX = 1024
LED_DUTY_MIN = 128
LED_DUTY_STEP= 16

BUTTON_PIN = 23

DEBOUNCE_MS = 20

#WARN: the below line requires root
wiringpi2.wiringPiSetupGpio()
wiringpi2.pinMode(LED_PIN, wiringpi2.GPIO.PWM_OUTPUT)  # hardware PWM mode
wiringpi2.pinMode(LIGHTS_PIN, wiringpi2.GPIO.PWM_OUTPUT)  # hardware PWM mode

count = 0

def button_raw_press():
    # simple debounce with busy-waiting
    time.sleep(DEBOUNCE_MS // 1000)
    if not wiringpi2.digitalRead(BUTTON_PIN):
        global count
        count += 1
        print("BUTTON PRESS: %d" % (count))

wiringpi2.pinMode(BUTTON_PIN, wiringpi2.GPIO.INPUT)
wiringpi2.pullUpDnControl(BUTTON_PIN, wiringpi2.GPIO.PUD_UP)

wiringpi2.wiringPiISR(BUTTON_PIN, wiringpi2.GPIO.INT_EDGE_BOTH, button_raw_press)

try:
    while True:
        for i in xrange(LED_DUTY_MIN, LED_DUTY_MAX + 1, LED_DUTY_STEP):
            wiringpi2.pwmWrite(LED_PIN, i)
            wiringpi2.pwmWrite(LIGHTS_PIN, LED_DUTY_MAX + LED_DUTY_MIN - i)
            time.sleep(0.02)

        time.sleep(0.5)

        for i in xrange(LED_DUTY_MAX, LED_DUTY_MIN - 1, -LED_DUTY_STEP):
            wiringpi2.pwmWrite(LED_PIN, i)
            wiringpi2.pwmWrite(LIGHTS_PIN, LED_DUTY_MAX + LED_DUTY_MIN - i)
            time.sleep(0.02)

        #time.sleep(0.5)
except KeyboardInterrupt:
    pass
