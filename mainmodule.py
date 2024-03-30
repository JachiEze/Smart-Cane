import http.client
import urllib.request
import urllib.parse
import urllib.error
import time
import serial
import cv2
import os
import pyttsx3
import pygame
from ultrasonicsensor import distance

from GPS_API import *
from detectidentify import append_objs_to_img, get_objects, make_interpreter, read_label_file, run_inference

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Initialize pygame for audio playback
pygame.mixer.init()

# Load the obstruction sound
obstruction_sound = pygame.mixer.Sound("obstruction.mp3")

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

if __name__ == "__main__":
    ser = serial.Serial("/dev/ttyACM0")  # Select your Serial Port
    ser.baudrate = 9600  # Baud rate
    ser.timeout = 0.5
    sleep = 2  # how many seconds to sleep between posts to the channel

    key = "VQ4O3RCYND2NE9UH"  # Thingspeak Write API Key
    msgdata = Message()  # Creates a Message Instance

    start_gps_receiver(ser, msgdata)
    time.sleep(2)
    ready_gps_receiver(msgdata)

    default_model_dir = '/home/group26/Documents/all_models'
    default_model = 'ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite'
    default_labels = 'coco_labels.txt'

    print('Loading {} with {} labels.'.format(default_model, default_labels))
    interpreter = make_interpreter(os.path.join(default_model_dir, default_model))
    interpreter.allocate_tensors()
    labels = read_label_file(os.path.join(default_model_dir, default_labels))
    inference_size = input_size(interpreter)

    cap = cv2.VideoCapture(0)  # Adjust camera index as needed

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        cv2_im_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cv2_im_rgb = cv2.resize(cv2_im_rgb, inference_size)
        run_inference(interpreter, cv2_im_rgb.tobytes())
        objs = get_objects(interpreter, threshold=0.1)
        frame = append_objs_to_img(frame, inference_size, objs, labels)

        # Speak detected and identified objects
        for obj in objs:
            label = labels.get(obj.id, obj.id)
            percent = int(100 * obj.score)
            text = f"{label}"
            engine.say(text)
            engine.runAndWait()

        # Check distance and play obstruction sound if distance is <= 100 cm
        dist = distance()
        if dist <= 100:
            obstruction_sound.play()

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

