#!/usr/bin/env python

import serial
import time
import csv
import os
import re

# Puerto y configuracion
SERIAL_PORT = '/dev/ttyUSB0'  # o '/dev/ttyACM0'
BAUD_RATE = 115200
OUTPUT_DIR = '/home/pi/catkin_ws/src/sensor_proximidad/scripts'
FILENAME = 'test2_rangols_2.csv'

# Crear directorio si no existe
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

file_path = os.path.join(OUTPUT_DIR, FILENAME)

# Abrir puerto serial y archivo CSV
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Esperar reinicio del ESP32

    with open(file_path, 'w') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Timestamp', 'Value_mm', 'Value_cm'])

        print "Reading from serial and writing to CSV..."
        while True:
            #time.sleep(0.2)
            if ser.inWaiting() > 0:
                line = ser.readline().strip()

                try:
                    decoded_line = line.decode('utf-8')
                except:
                    decoded_line = line  # Si no se puede decodificar, usar crudo

                #print "Raw serial input:", decoded_line

                match = re.search(r'D=(\d+)mm', decoded_line)
                if match:
                    number_mm = float(match.group(1))  # Usar el grupo capturado
                    number_cm = number_mm / 10.0
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    print(number_cm)
                    csv_writer.writerow([timestamp, number_mm, number_cm])
                    csvfile.flush()

except serial.SerialException as e:
    print "Serial error:", e
except KeyboardInterrupt:
    print "\nLogging stopped by user."
