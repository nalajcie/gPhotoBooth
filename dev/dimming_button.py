#!/usr/bin/env python
import RPi.GPIO as GPIO
import time

LED_PIN = 12    # board pin no
LED_FREQ = 100  # in Hz

LED_DUTY_MAX = 100
LED_DUTY_MIN = 10

BUTTON_PIN = 16


GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button_raw_press(channel):
    print "BUTTON PRESS!"

GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_raw_press, bouncetime=500)

pwm = GPIO.PWM(LED_PIN, LED_FREQ)

pwm.start(0)

try:
    while True:
        for i in xrange(LED_DUTY_MIN, LED_DUTY_MAX + 1):
            pwm.ChangeDutyCycle(i)
            time.sleep(0.02)

        time.sleep(0.5)

        for i in xrange(LED_DUTY_MAX, LED_DUTY_MIN - 1, -1):
            pwm.ChangeDutyCycle(i)
            time.sleep(0.02)

        #time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    pwm.stop()
    GPIO.cleanup()
