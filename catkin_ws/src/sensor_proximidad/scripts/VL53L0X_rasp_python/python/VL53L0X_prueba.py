#!/usr/bin/env python
import time
import csv
import io
import datetime
import VL53L0X

# Crear objeto VL53L0X
tof = VL53L0X.VL53L0X(i2c_bus=1, i2c_address=0x29)

# Abrir el sensor
tof.open()

# Iniciar el modo de medicion
tof.start_ranging(VL53L0X.Vl53l0xAccuracyMode.BETTER)

# Obtener el tiempo de muestreo
timing = tof.get_timing()
if timing < 20000:
    timing = 20000
print "Timing %d ms" % (timing / 1000)

# Abrir archivo CSV para guardar los datos
with open("distancias.csv", mode="wb") as file:
    writer = csv.writer(file)
    writer.writerow(["Conteo", "Distancia (mm)", "Distancia (cm)", "Timestamp (s)", "Fecha y Hora"])  # Cabecera

    try:
        count = 1
        while True:
            distance = tof.get_distance()
            if distance > 0:
                timestamp = time.time()
                fecha_hora = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                print "%d mm, %d cm, %d - %s" % (distance, (distance / 10), count, fecha_hora)
                writer.writerow([count, distance, distance / 10.0, timestamp, fecha_hora])
                count += 1
            time.sleep(timing / 1000000.00)
    except KeyboardInterrupt:
        print "\nLectura interrumpida por el usuario."

# Detener y cerrar el sensor
tof.stop_ranging()
tof.close()