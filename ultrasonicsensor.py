#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import pygame

try:
    GPIO.setmode(GPIO.BOARD)

    PIN_TRIGGER = 7
    PIN_ECHO = 11

    GPIO.setup(PIN_TRIGGER, GPIO.OUT)
    GPIO.setup(PIN_ECHO, GPIO.IN)

    GPIO.output(PIN_TRIGGER, GPIO.LOW)

    print("Waiting for sensor to settle")
    time.sleep(2)

    # Initialize pygame mixer
    pygame.mixer.init()

    # Load the MP3 file
    mp3_file = "your_mp3_file.mp3"
    pygame.mixer.music.load(mp3_file)

    while True:  # Run continuously
        print("Calculating distance")

        GPIO.output(PIN_TRIGGER, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(PIN_TRIGGER, GPIO.LOW)

        while GPIO.input(PIN_ECHO) == 0:
            pulse_start_time = time.time()
        while GPIO.input(PIN_ECHO) == 1:
            pulse_end_time = time.time()

        pulse_duration = pulse_end_time - pulse_start_time
        distance = round(pulse_duration * 17150, 2)
        print("Distance:", distance, "cm")

        if distance <= 100:
            print("Distance is 100cm or less. Playing MP3 file.")
            pygame.mixer.music.play()

        time.sleep(2)  # Wait for 2 seconds before the next measurement

finally:
    GPIO.cleanup()
