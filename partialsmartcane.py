import cv2
import pyttsx3
import numpy as np
import RPi.GPIO as GPIO
import time

# Load the class names
classNames = []
classFile = "coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Set up model configuration and weights paths
configPath = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "frozen_inference_graph.pb"

# Initialize the neural network for object detection
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Video capture setup
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Function to detect objects
def getObjects(img, thres, nms, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)

    if len(objects) == 0:
        objects = classNames

    objectInfo = []

    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box, className])

            # Speak the detected class name
            engine.say(f"{className} detected")
            engine.runAndWait()

            # Draw a box and label on the image
            cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
            cv2.putText(img, className.upper(), (box[0] + 10, box[1] + 30),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

    return img, objectInfo

# Setup GPIO pins
GPIO.setmode(GPIO.BOARD)
PIN_TRIGGER = 7
PIN_ECHO = 11
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)
GPIO.output(PIN_TRIGGER, GPIO.LOW)

# Function to measure distance
def measure_distance():
    GPIO.output(PIN_TRIGGER, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER, GPIO.LOW)

    pulse_start_time = time.time()
    while GPIO.input(PIN_ECHO) == 0:
        pulse_start_time = time.time()

    pulse_end_time = time.time()
    while GPIO.input(PIN_ECHO) == 1:
        pulse_end_time = time.time()

    pulse_duration = pulse_end_time - pulse_start_time
    distance = round(pulse_duration * 17150, 2)
    return distance

try:
    while True:
        success, img = cap.read()
        result, objectInfo = getObjects(img, 0.60, 0.2)
        cv2.imshow("Output", img)

        # Check for 'q' key press
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

        # Check distance
        distance = measure_distance()
        print("Distance:", distance, "cm")
        if distance <= 100:
            # Perform action when an obstruction is detected
            print("Obstruction detected!")
            # Here you can add any action you want to take upon detecting an obstruction
            # For example, you can trigger an alarm or send a notification

finally:
    # Cleanup GPIO
    GPIO.cleanup()

# Release the video capture object and close the OpenCV window
cap.release()
cv2.destroyAllWindows()
