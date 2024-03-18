import threading
import time
import cv2
import numpy as np
import RPi.GPIO as GPIO
import pygame
import Adafruit_ADS1x15
from GPS_API import Message, start_gps_receiver, ready_gps_receiver, get_latitude, get_longitude

# Initialize GPIO for ultrasonic sensor
GPIO.setmode(GPIO.BOARD)
PIN_TRIGGER = 7
PIN_ECHO = 11
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)
GPIO.output(PIN_TRIGGER, GPIO.LOW)

# Initialize pygame mixer for audio feedback
pygame.mixer.init()

# Load audio files
obstruction_file = "obstructiondetected.mp3"
water_file = "waterdetected.mp3"

# Initialize GPS
msgdata = Message()

# Initialize camera
net = cv2.dnn.readNet('yolov4-tiny.weights', 'yolov4-tiny.cfg')
classes = []
with open("coco.names", "r") as f:
    classes = f.read().splitlines()

# Initialize ADC for water sensor
ADC = Adafruit_ADS1x15.ADS1115()
ADC_CHANNEL = 3
GAIN = 1
MIN_ADC_VALUE = 0
MAX_ADC_VALUE = 32767

# Function for uploading GPS data to cloud
def upload_cloud():
    while True:
        temp = get_latitude(msgdata)
        temp1 = get_longitude(msgdata)
        # Code for uploading to cloud
        time.sleep(2)

# Function for object detection and identification
def detect_identify():
    cap = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_PLAIN
    colors = np.random.uniform(0, 255, size=(100, 3))
    
    while True:
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

    cap.release()
    cv2.destroyAllWindows()

# Function for ultrasonic sensor
def ultrasonic_sensor():
    # Code for ultrasonic sensor
    while True:
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
            pygame.mixer.music.load(obstruction_file)
            pygame.mixer.music.play()
            time.sleep(2) # Wait for 2 seconds before the next measurement

# Function for water sensor
def water_sensor():
    # Code for water sensor
    while True:
        adc_value = ADC.read_adc(ADC_CHANNEL, gain=GAIN)
        water_level = (adc_value - MIN_ADC_VALUE) / (MAX_ADC_VALUE - MIN_ADC_VALUE) * 100
        print("ADC Value: {} | Water Level: {:.2f}%".format(adc_value, water_level))
        if water_level >= 25:
            pygame.mixer.music.load(water_file)
            pygame.mixer.music.play()
            time.sleep(2)

# Create threads for each functionality
thread1 = threading.Thread(target=upload_cloud)
thread2 = threading.Thread(target=detect_identify)
thread3 = threading.Thread(target=ultrasonic_sensor)
thread4 = threading.Thread(target=water_sensor)

# Start threads
thread1.start()
thread2.start()
thread3.start()
thread4.start()

# Join threads to the main thread
thread1.join()
thread2.join()
thread3.join()
thread4.join()
