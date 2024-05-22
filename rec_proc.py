# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import socket
import struct
import keyboard
import time

def replace_control_bytes(input_bytes):
    # Reemplaza \x00 por '0' y \x01 por '1'
    replaced_bytes = input_bytes.replace(b'\x00\x01', b'1').replace(b'\x00\x00', b'0')
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
BUFFER_SIZE = 10240

# Crea el socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

preamble = b'1001'
def main():
    # Bucle para recibir datos continuamente
    print("Escuchando...")
    try:
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)  # Recibe datos del socket
            # Procesa los datos recibidos (aquí puedes trabajar con los caracteres uchar)
            replaced = replace_control_bytes(data)
            reduced = reduce_control_bytes(replaced)
            # TEST
            # print("data", data ) # Datos originales
            # print("replaced", replaced ) # Datos convertidos a 0s y 1s
            # print("reduced", reduced ) # Repeticiones reducidas. Mejora de consistencia
            
            if reduced != b'0':                
                print("Data: ", reduced)
                                
                if reduced.find(preamble):
                    print("Código válido")
            """
            DECIPHER
            """
    
            """ Proceso inverso para resolver el timestamp en bytes
            bytes_timestamp = b'\x40\x09\x21\xfb\x4d\x2b\x5f\x09'  # Ejemplo de secuencia de bytes
    
            # Desempaquetar los bytes en un flotante de doble precisión
            timestamp_flotante = struct.unpack('d', bytes_timestamp)[0]
    
            # Obtener el timestamp utilizando time.mktime()
            timestamp = time.mktime(time.gmtime()) + (timestamp_flotante - time.time())
    
            print(timestamp)
            """
            
            
            
            
            
            
            
            
            
            
    finally:
        sock.close()  # Cierra el socket al finalizar el script
        print("\nEjecución finalizada correctamente\n")
        

if __name__ == '__main__':
    main()
