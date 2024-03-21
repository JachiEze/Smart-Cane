import cv2
import pyttsx3
import http.client
import urllib.request
import urllib.parse
import urllib.error
import time
from GPS_API import *  # Assuming GPS_API module is available in your environment
import serial

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
        success, img = cap.read()
        result, objectInfo = getObjects(img, 0.60, 0.2)
        cv2.imshow("Output", img)
        
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
