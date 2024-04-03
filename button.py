import RPi.GPIO as GPIO
import subprocess
import time

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 15 to be an input pin and set initial value to be pulled low (off)

# Define a variable to store the last time a button press was detected
last_pressed_time = 0

# Define the debounce interval (in seconds)
debounce_interval = 0.5

while True:
    input_state = GPIO.input(15)
    
    # Check if the button is pressed and debounce time has elapsed since the last press
    if input_state == GPIO.HIGH and (time.time() - last_pressed_time) > debounce_interval:
        last_pressed_time = time.time() # Update the last pressed time
        
        # Execute connectionv3.py
        subprocess.Popen(["python3", "/home/pi/Documents/Smart-Cane-main/connectionv3.py"])
        # Execute newdetide.py
        subprocess.Popen(["python3", "/home/pi/Documents/Smart-Cane-main/newdetide.py"])
        # Execute ultrasonicsensor.py
        subprocess.Popen(["python3", "/home/pi/Documents/Smart-Cane-main/ultrasonicsensor.py"])
