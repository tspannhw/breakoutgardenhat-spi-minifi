#!/usr/bin/env python3

import os
import traceback
import random, string
import base64
import json
import paho.mqtt.client as mqtt
from time import sleep
from time import gmtime, strftime
import time
import sys
from PIL import Image
import ST7735 as ST7735
import sys
import datetime
import subprocess
import base64
import uuid
import datetime
import traceback
import math
import random, string
import socket
import base64
import json
#import cv2
import time
import psutil
import socket
from time import gmtime, strftime
from max30105 import MAX30105, HeartRate

client = mqtt.Client()
client.connect("localhost", 1883, 60)

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
from bmp280 import BMP280

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
from bmp280 import BMP280

bus = SMBus(1)
bmp280 = BMP280(i2c_dev=bus)

# Create ST7735 LCD display class.
disp = ST7735.ST7735(
    port=0,
    cs=ST7735.BG_SPI_CS_BACK,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=9,
    backlight=18,               # 18 for back BG slot, 19 for front BG slot.
    rotation=90,
    spi_speed_hz=4000000
)

WIDTH = disp.width
HEIGHT = disp.height

# Initialize display.
disp.begin()

bus = SMBus(1)
bmp280 = BMP280(i2c_dev=bus)

baseline_values = []
baseline_size = 100

for i in range(baseline_size):
    pressure = bmp280.get_pressure()
    baseline_values.append(pressure)
    time.sleep(1)

baseline = sum(baseline_values[:-25]) / len(baseline_values[:-25])

max30105 = MAX30105()
max30105.setup(leds_enable=3)

max30105.set_led_pulse_amplitude(1, 0.0)
max30105.set_led_pulse_amplitude(2, 0.0)
max30105.set_led_pulse_amplitude(3, 12.5)

max30105.set_slot_mode(1, 'red')
max30105.set_slot_mode(2, 'ir')
max30105.set_slot_mode(3, 'green')
max30105.set_slot_mode(4, 'off')

hr = HeartRate(max30105)

# Smooths wobbly data. Increase to increase smoothing.
mean_size = 20

# Compares current smoothed value to smoothed value x
# readings ago. Decrease this to increase detection
# speed.
delta_size = 10

# The delta threshold at which a change is detected.
# Decrease to make the detection more sensitive to
# fluctuations, increase to make detection less
# sensitive to fluctuations.
threshold = 10

data = []
means = []

def do_nothing(obj):
    pass
    
def IP_address():
        try:
            s = socket.socket(socket_family, socket.SOCK_DGRAM)
            s.connect(external_IP_and_port)
            answer = s.getsockname()
            s.close()
            return answer[0] if answer else None
        except socket.error:
            return None

def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

# - start timing                
starttime = datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S') 
start = time.time()

external_IP_and_port = ('198.41.0.4', 53)  # a.root-servers.net
socket_family = socket.AF_INET

# Ip address
ipaddress = IP_address()

# start camera
# time.sleep(0.5)
# cap = cv2.VideoCapture(0)  
# time.sleep(3)

# loop forever
#try:
while True:
     row = { }
     
     max30105timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
     samples = max30105.get_samples()
     if samples is not None:
         r = samples[2] & 0xff
         d = hr.low_pass_fir(r)
         data.append(d)
         if len(data) > mean_size:
             data.pop(0)
         mean = sum(data) / float(len(data))
         means.append(mean)
         if len(means) > delta_size:
             delta = means[-1] - means[-delta_size]
         else:
             delta = 0
         if delta > threshold:
             detected = True
         else:
             detected = False
         print("Value: {:.2f} // Mean: {:.2f} // Delta: {:.2f} // Change detected: {}".format(d, mean, delta, detected))

         tempmax30105 = max30105.get_temperature()
         row['max30105_temp'] = '{:.2f}'.format(tempmax30105)
         row['max30105_value'] = '{:.2f}'.format(d)
         row['max30105_mean'] = '{:.2f}'.format(mean)
         row['max30105_delta'] = '{:.2f}'.format(delta)
         row['max30105_detected'] = '{}'.format(detected)
         row['max30105timestamp'] = max30105timestamp
                         
     altitude = bmp280.get_altitude(qnh=baseline)
     print('Relative altitude: {:05.2f} metres'.format(altitude))
     row['bme280_altitude'] = '{0:05.2f}'.format(altitude)
     row['bme280_altitude_feet'] = '{0:05.2f}'.format((altitude  / .3048))
         
     bmp280temperature = bmp280.get_temperature()
     bmp280pressure = bmp280.get_pressure()
     print('{:05.2f}*C {:05.2f}hPa'.format(bmp280temperature, bmp280pressure))
     row['bme280_tempc'] = '{0:05.2f}'.format(bmp280temperature)
     row['bme280_tempf'] = '{0:05.2f}'.format((bmp280temperature * 1.8) + 32)
     row['bme280_pressure'] = '{0:05.2f}'.format(bmp280pressure)
    
#     ret, frame = cap.read()
     uuid2 = '{0}_{1}'.format(strftime("%Y%m%d%H%M%S",gmtime()),uuid.uuid4())
     filename = 'images/bog_image_{0}.jpg'.format(uuid2)
     filename2 = 'images/bog_image_p_{0}.jpg'.format(uuid2)
#     cv2.imwrite(filename, frame)
     cpuTemp=int(float(getCPUtemperature()))
     end = time.time()

     row['imgname'] = filename
     row['imgnamep'] = filename2
     row['host'] = os.uname()[1]
     row['cputemp'] = round(cpuTemp,2)
     row['ipaddress'] = ipaddress
     row['end'] = '{0}'.format( str(end ))
     row['te'] = '{0}'.format(str(end-start))
     row['systemtime'] = datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')      
     row['starttime'] = starttime  
     usage = psutil.disk_usage("/")
     row['diskusage'] = "{:.1f}".format(float(usage.free) / 1024 / 1024)
     row['memory'] = psutil.virtual_memory().percent
     row['uuid'] = str(uuid2)
     json_string = json.dumps(row)  
     json_string += str("\n")
     
     # MQTT
     client.publish("garden2", payload=json_string, qos=0, retain=True)

     # image = Image.open(image_file)
     # Resize the image  image = image.resize((WIDTH, HEIGHT))
     # disp.display(image)

     json_string = ""
     
     time.sleep(1)
    
#     with canvas(oled) as draw:
#         draw.rectangle(oled.bounding_box, outline="white", fill="black")
#         draw.text((0, 0), "- Apache NiFi MiniFi -", fill="white")
#         draw.text((0, 10), ipaddress, fill="white")
#         draw.text((0, 20), starttime, fill="white")
#         draw.text((0, 30), 'Temp: {}'.format( sensor.data.temperature ), fill="white")
#         draw.text((0, 40), 'Humidity: {}'.format( sensor.data.humidity ), fill="white")  
#         draw.text((0, 50), 'Pressure: {}'.format( sensor.data.pressure ), fill="white")    
#         draw.text((0, 60), 'Distance: {}'.format(str(distance_in_mm)), fill="white")      
#         draw.text((0, 70), 'CPUTemp: {}'.format( cpuTemp ), fill="white")      
#         draw.text((0, 80), 'TempF: {}'.format( row['bme680_tempf'] ), fill="white") 
#         draw.text((0, 90), 'A: {}'.format(row['lsm303d_accelerometer']), fill="white") 
#         draw.text((0, 100), 'M: {}'.format(row['lsm303d_magnetometer']), fill="white") 
#         draw.text((0, 110), 'DU: {}'.format(row['diskusage']), fill="white") 
#         time.sleep(0.5)
#except:
#     print("Fail to send.") 
