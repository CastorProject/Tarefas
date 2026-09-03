import serial
import time
import csv
import os
import re


# Replace with your actual serial port
SERIAL_PORT = '/dev/ttyUSB0'  # or '/dev/ttyACM0'
BAUD_RATE = 112500  # Match this with the ESP32's baud rate
OUTPUT_DIR = '/home/pi/catkin_ws/src/sensor_prox'
FILENAME = 'sensor_prox.csv'

# Ensure the output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
file_path = os.path.join(OUTPUT_DIR, FILENAME)

# Open the serial port and CSV file
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for ESP32 to reset

    with open(file_path, 'wb') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Timestamp', 'Value'])  # Optional header

        print("Reading from serial and writing to CSV...")
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().strip()
                match = re.search(r'\b\d+\b', line)
                if match:
                    number = match.group()
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    print("%s - %s" % (timestamp, number))
                    csv_writer.writerow([timestamp, number])
                    csvfile.flush()
except serial.SerialException as e:
    print("Serial error:", e)
except KeyboardInterrupt:
    print("\nLogging stopped by user.")