import cv2
import pyttsx3
import http.client
import urllib.request
import urllib.parse
import urllib.error
import time
from GPS_API import *  # Assuming GPS_API module is available in your environment
import serial
from gpiozero import InputDevice, OutputDevice, PWMOutputDevice
import Adafruit_ADS1x15
import pygame

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

# Dictionary to track the counts for each class
class_counts = {}

# Set to store detected classes
detected_classes = set()

# Video capture setup
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

ser = serial.Serial("/dev/ttyACM0")  # Select your Serial Port
ser.baudrate = 9600  # Baud rate
ser.timeout = 0.5
sleep = 2  # how many seconds to sleep between posts to the channel

key = "VQ4O3RCYND2NE9UH"  # Thingspeak Write API Key
msgdata = Message()  # Creates a Message Instance

# GPIO setup for ultrasonic sensor
trig = OutputDevice(4)
echo = InputDevice(17)
motor = PWMOutputDevice(14)

ADC = Adafruit_ADS1x15.ADS1115()
ADC_CHANNEL = 3
GAIN = 1
MIN_ADC_VALUE = 0
MAX_ADC_VALUE = 32767

# Initialize pygame mixer
pygame.mixer.init()

# Load the MP3 file
water_file = "waterdetected.mp3"
pygame.mixer.music.load(water_file)


def get_pulse_time():
    trig.on()
    time.sleep(0.00001)
    trig.off()

    while echo.is_active == False:
        pulse_start = time.time()

    while echo.is_active == True:
        pulse_end = time.time()

    time.sleep(0.06)

    return pulse_end - pulse_start


def calculate_distance(duration):
    speed = 343
    distance = speed * duration / 2
    return distance


def calculate_vibration(distance):
    vibration = (((distance - 0.02) * -1) / (4 - 0.02)) + 1
    return vibration


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


def upload_cloud():
    temp_lat = get_latitude(msgdata)
    temp_lon = get_longitude(msgdata)
    temp_alt = get_altitude(msgdata)
    params = urllib.parse.urlencode({'field1': temp_lat, 'field2': temp_lon, 'field3': temp_alt, 'key': key})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = http.client.HTTPConnection("api.thingspeak.com:80")
    try:
        conn.request("POST", "/update", params, headers)
        response = conn.getresponse()
        print(("Lat:", temp_lat))
        print(("Long:", temp_lon))
        print(("Alt:", temp_alt))
        print((response.status, response.reason))
        conn.close()
    except KeyboardInterrupt:
        print("Connection Failed")


try:
    start_gps_receiver(ser, msgdata)
    time.sleep(2)
    ready_gps_receiver(msgdata)

    last_water_check_time = time.time()

    while True:
        # Water level detection every 2 seconds
        if time.time() - last_water_check_time >= 2:
            adc_value = ADC.read_adc(ADC_CHANNEL, gain=GAIN)
            water_level = (adc_value - MIN_ADC_VALUE) / (MAX_ADC_VALUE - MIN_ADC_VALUE) * 100

            print("ADC Value: {} | Water Level: {:.2f}%".format(adc_value, water_level))

            # If water level is 25% or greater, play the MP3 file
            if water_level >= 25:
                pygame.mixer.music.play()

            last_water_check_time = time.time()

        success, img = cap.read()
        result, objectInfo = getObjects(img, 0.60, 0.2)
        cv2.imshow("Output", img)

        # Ultrasonic sensor distance calculation and vibration control
        duration = get_pulse_time()
        distance = calculate_distance(duration)
        vibration = calculate_vibration(distance)
        motor.value = vibration

        # Upload GPS data to cloud
        upload_cloud()
        time.sleep(sleep)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    # Stop playback and cleanup pygame mixer
    pygame.mixer.music.stop()
    pygame.mixer.quit()

# Release the video capture object and close the OpenCV window
cap.release()
cv2.destroyAllWindows()
