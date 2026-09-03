import serial

def parse_frame(frame):
    """
    Parsea una trama HLKLD2420 (hexadecimal) y devuelve si hay deteccin dinmica y la distancia.
    """
    if len(frame) < 12:
        return None

    # Verifica encabezado
    if frame[0] != 0x55 or frame[1] != 0xAA:
        return None

    # Verifica tipo de frame (0x07 tipicamente es de datos)
    if frame[2] != 0x07:
        return None

    try:
        # Byte 9: tipo de presencia (bit 0 = estatica, bit 1 = dinamica)
        presence_type = frame[9]
        dynamic = (presence_type & 0x02) != 0

        # Bytes 10 y 11: distancia en cm (little endian)
        distance_cm = frame[10] + (frame[11] << 8)

        return dynamic, distance_cm
    except IndexError:
        return None

# Cambia '/dev/ttyUSB0' por tu puerto correcto, y ajusta baudrate si es necesario
ser = serial.Serial('/dev/ttyUSB0', 112500, timeout=1)

print("Leyendo datos del HLK-LD2420...")

try:
    buffer = []
    while True:
        byte = ser.read()
        if byte:
            buffer.append(byte[0])  # byte ya es bytes tipo b'\xNN', obtener valor int con byte[0]

            # Limitar tamano del buffer para evitar overflow (mas que suficiente para detectar trama)
            if len(buffer) > 50:
                buffer = buffer[-50:]

            # Buscamos la trama de 12 bytes con encabezado correcto
            if len(buffer) >= 12:
                # Buscar la primera posicion con encabezado 0x55 0xAA
                for i in range(len(buffer) - 11):
                    if buffer[i] == 0x55 and buffer[i+1] == 0xAA:
                        posible_frame = buffer[i:i+12]
                        result = parse_frame(posible_frame)
                        if result:
                            dynamic, distance = result
                            tipo = "Dinamico" if dynamic else "Estatico"
                            print("Objeto" + tipo + "detectado a" + distance/100)
                            # Removemos los bytes del frame procesado
                            buffer = buffer[i+12:]
                            break
                else:
                    # Si no se encontro encabezado, eliminamos el primer byte
                    buffer.pop(0)

except KeyboardInterrupt:
    print("\nFinalizado.")
finally:
    ser.close()
