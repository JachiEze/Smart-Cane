import threading
import pynmea2
import sys

class Message:
    def __init__(self):
        self.msg =''

# Gps Receiver thread funcion, check gps value for infinte times
def get_gps_data(serial, dmesg):
    print("Initializing GPS\n")
    while True:
        strRead = serial.readline()
        if sys.version_info[0] == 3:
            strRead = strRead.decode("utf-8","ignore")
            if strRead[0:6] == '$GPGGA':
                dmesg.msg = pynmea2.parse(strRead)
        else:
            if strRead.find('GGA') > 0:
                dmesg.msg = pynmea2.parse(strRead)

# API to call start the GPS Receiver
def start_gps_receiver(serial, dmesg):
    t2 = threading.Thread(target=get_gps_data, args=(serial, dmesg))
    t2.start()
    print("GPS Receiver started")

# API to fix the GPS Revceiver
def ready_gps_receiver(msg):
    print("Please wait fixing GPS .....")
    dmesg = msg.msg
    while(dmesg.gps_qual != 1):
        pass
    print("GPS Fix available")

# API to get latitude from the GPS Receiver
def get_latitude(msg):
    dmesg = msg.msg
    return dmesg.latitude

# API to get longitude from the GPS Receiver
def get_longitude(msg):
    dmesg = msg.msg
    return dmesg.longitude
