#!/usr/bin/env python
import rospy
import serial
import time
import csv
import os
import re
from std_msgs.msg import String

def main():
    rospy.init_node('rfid_node', anonymous=True)
    pub = rospy.Publisher('/sensor_prox_rfid', String, queue_size=10)

    SERIAL_PORT = '/dev/ttyUSB0'   # Ajusta si es necesario
    BAUD_RATE = 115200

    # Ruta para guardar el archivo CSV
    output_dir = os.path.expanduser('~/catkin_ws/src/sensor_proximidad/scripts/')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = os.path.join(output_dir, 'test1_luz_1.csv')

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Esperar que el ESP32 reinicie

        rospy.loginfo("Nodo sensor_prox_node iniciado.")
        rospy.loginfo("Leyendo datos del puerto serial y publicando en /sensor_prox_rfid")

        with open(filename, 'w') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Timestamp', 'Value'])  # Cabecera del CSV

            while not rospy.is_shutdown():
                if ser.in_waiting > 0:
                    line = ser.readline().strip()
                    match = re.search(r'\b\d+\b', line)
                    if match:
                        number = match.group()
                        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                        msg = (str(number))

                        #rospy.loginfo(msg)
                        pub.publish(msg)

                        csv_writer.writerow([timestamp, number])
                        csvfile.flush()

    except serial.SerialException as e:
        rospy.logerr("Error de conexion serial: %s", e)
    except rospy.ROSInterruptException:
        pass
    except KeyboardInterrupt:
        rospy.loginfo("Nodo interrumpido por el usuario.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            rospy.loginfo("Puerto serial cerrado.")

if __name__ == '__main__':
    main()
