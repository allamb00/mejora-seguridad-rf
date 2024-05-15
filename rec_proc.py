# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import socket

def replace_control_bytes(input_bytes):
    # Reemplaza \x00 por '0' y \x01 por '1'
    replaced_bytes = input_bytes.replace(b'\x01\x00', b'1').replace(b'\x00\x00', b'0')
    return replaced_bytes

def reduce_control_bytes(input_bytes):
    output_bytes = b''
    current_char = input_bytes[0]  # Inicializa el primer carácter
    count = 0
    for char in input_bytes:
        if char == current_char:
            count += 1
        else:
            for i in range(round(count/30)): #Soluciona la inconsistencia de 0s y 1s
                output_bytes += bytes([current_char])
            current_char = char
            count = 1
    # Agrega el último carácter al string reducido
    output_bytes += bytes([current_char])
    return output_bytes

# Configura el socket UDP
UDP_IP = "127.0.0.1"  # Dirección IP a la que GNU Radio está enviando los datos
UDP_PORT = 2000  # Puerto al que GNU Radio está enviando los datos
BUFFER_SIZE = 1024

# Crea el socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Bucle para recibir datos continuamente
try:
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)  # Recibe datos del socket
        # Procesa los datos recibidos (aquí puedes trabajar con los caracteres uchar)
        replaced = replace_control_bytes(data)
        reduced = reduce_control_bytes(replaced)
        print("data", data ) # Convierte los datos a una cadena y muestra en la consola
        print("replaced", replaced ) # Convierte los datos a una cadena y muestra en la consola
        print("reduced", reduced ) # Convierte los datos a una cadena y muestra en la consola
finally:
    sock.close()  # Cierra el socket al finalizar el script