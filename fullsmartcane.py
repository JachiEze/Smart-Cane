import http.client
import urllib.request
import urllib.parse
import urllib.error
import time
import cv2
import numpy as np
import pyttsx3
import RPi.GPIO as GPIO
import pygame
import Adafruit_ADS1x15
from GPS_API import *
import serial

# GPS Setup
ser = serial.Serial("/dev/ttyACM0") # Select your Serial Port
ser.baudrate = 9600 # Baud rate
ser.timeout = 0.5
sleep = 2 # how many seconds to sleep between posts to the channel
key = "VQ4O3RCYND2NE9UH" # Thingspeak Write API Key
msgdata = Message() # Creates a Message Instance

# Object Detection Setup
net = cv2.dnn.readNet('yolov4-tiny.weights', 'yolov4-tiny.cfg')
classes = []
with open("coco.names", "r") as f:
    classes = f.read().splitlines()
cap = cv2.VideoCapture(0)
font = cv2.FONT_HERSHEY_PLAIN
colors = np.random.uniform(0, 255, size=(100, 3))

# Ultrasonic Sensor Setup
GPIO.setmode(GPIO.BOARD)
PIN_TRIGGER = 7
PIN_ECHO = 11
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)
GPIO.output(PIN_TRIGGER, GPIO.LOW)
pygame.mixer.init()
obstruction_file = "obstructiondetected.mp3"
pygame.mixer.music.load(obstruction_file)

# Water Sensor Setup
ADC = Adafruit_ADS1x15.ADS1115()
ADC_CHANNEL = 3
GAIN = 1
MIN_ADC_VALUE = 0
MAX_ADC_VALUE = 32767
water_file = "waterdetected.mp3"
pygame.mixer.music.load(water_file)

def upload_cloud():
    temp = get_latitude(msgdata)
    temp1 = get_longitude(msgdata)
    params = urllib.parse.urlencode({'field1': temp, 'field2': temp1, 'key': key})
    headers = {"Content-typZZe": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = http.client.HTTPConnection("api.thingspeak.com:80")
    try:
        conn.request("POST", "/update", params, headers)
        response = conn.getresponse()
        print(("Lat:", temp))
        print(("Long:", temp1))
        print((response.status, response.reason))
        conn.close()
    except KeyboardInterrupt:
        print("Connection Failed")

try:
    start_gps_receiver(ser, msgdata)
    time.sleep(2)
    ready_gps_receiver(msgdata)
    while True:
        upload_cloud()
        _, img = cap.read()
        height, width, _ = img.shape
        blob = cv2.dnn.blobFromImage(img, 1/255, (416, 416), (0,0,0), swapRB=True, crop=False)
        net.setInput(blob)
        output_layers_names = net.getUnconnectedOutLayersNames()
        layerOutputs = net.forward(output_layers_names)
        boxes = []
        confidences = []
        class_ids = []
        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.2:
                    center_x = int(detection[0]*width)
                    center_y = int(detection[1]*height)
                    w = int(detection[2]*width)
                    h = int(detection[3]*height)
                    x = int(center_x - w/2)
                    y = int(center_y - h/2)
                    boxes.append([x, y, w, h])
                    confidences.append((float(confidence)))
                    class_ids.append(class_id)
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.2, 0.4)
        if len(indexes) > 0:
            for i in indexes.flatten():
                x, y, w, h = boxes[i]
                label = str(classes[class_ids[i]])
                confidence = str(round(confidences[i], 2))
                color = colors[i]
                cv2.rectangle(img, (x,y), (x+w, y+h), color, 2)
                cv2.putText(img, label + " " + confidence, (x, y+20), font, 2, (255,255,255), 2)
                engine = pyttsx3.init()
                engine.say(label)
                engine.runAndWait()
        cv2.imshow('Image', img)
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'): # Press q to quit
            break

        # Ultrasonic Sensor
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
            pygame.mixer.music.play()

        # Water Sensor
        adc_value = ADC.read_adc(ADC_CHANNEL, gain=GAIN)
        water_level = (adc_value - MIN_ADC_VALUE) / (MAX_ADC_VALUE - MIN_ADC_VALUE) * 100
        print("ADC Value: {} | Water Level: {:.2f}%".format(adc_value, water_level))
        if water_level >= 25:
            pygame.mixer.music.play()

        time.sleep(2) # Wait for 2 seconds before the next measurement

finally:
    cap.release()
    GPIO.cleanup()
    pygame.mixer.music.stop()
    pygame.mixer.quit()

