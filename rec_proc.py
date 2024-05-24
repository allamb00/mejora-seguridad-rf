# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import socket
import struct
import keyboard
import time

from collections import deque

# Configura el socket UDP
UDP_IP = "127.0.0.1"  # Dirección IP a la que GNU Radio está enviando los datos
UDP_PORT = 2000  # Puerto al que GNU Radio está enviando los datos
BUFFER_SIZE = 1472

# Crea el socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

preamble = b'1001'

# Inicializa un deque con una longitud máxima de 188 caracteres
max_length = 200
buffer = deque(maxlen=max_length)

preamble = b'00000111010110111100110100010101' #Serial del fabricante para distinguir el código
preamble_len = len(preamble)
code_len = 188 #Tamaño total del código


max_length = 200
buffer = deque(maxlen=max_length)
count = 0 #Variable global para que no se corte la cuenta entre payloads

def process_bytes(byte_data):
    code = b''
    buffer.extend(byte_data)
    if len(buffer) == max_length:
        current_bytes = bytes(buffer)
        
        # Busca la subcadena que empieza con el preámbulo
        for i in range(len(current_bytes) - preamble_len + 1):
            if current_bytes[i:i+preamble_len] == preamble:
                # Verifica si la cadena de 188 bytes está completa
                if i + code_len <= len(current_bytes):
                    code = current_bytes[i:i+code_len]
                    print("\nCódigo válido encontrado:", code)
                else:
                    print(".", end = "")
                break
        else:
            print(".", end = "")
    return code

def is_all_zeros(byte_data):
    return all(b == ord('0') for b in byte_data)
            
def replace_control_bytes(input_bytes):
    # Reemplaza \x00 por '0' y \x01 por '1'
    replaced_bytes = input_bytes.replace(b'\x01\x00', b'1').replace(b'\x00\x00', b'0')
    return replaced_bytes

def reduce_control_bytes(input_bytes):
    output_bytes = b''
    current_char = input_bytes[0]  # Inicializa el primer carácter
    global count
    count = 0
    for char in input_bytes:
        
        if char != current_char or count >= 30:                     
            for i in range(round(count/30)): #Soluciona la inconsistencia de 0s y 1s
                output_bytes += bytes([current_char])
            current_char = char
            count = 1
        else:
            count += 1
    # Agrega el último carácter al string reducido  
    if round(count/30) == 1 :
        output_bytes += bytes([current_char])
    
    return output_bytes

def main():
    # Bucle para recibir datos continuamente
    print("Escuchando...")
    for a in range(0):
        print(round(2/30))
    try:
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)  # Recibe datos del socket
            # Procesa los datos recibidos (aquí puedes trabajar con los caracteres uchar)
            replaced = replace_control_bytes(data)
            reduced = reduce_control_bytes(replaced)            
             
            code = process_bytes(reduced) #Busca el preámbulo en la entrada
            #TODO ya tenemos el código completo que se ha enviado. Ahora hay que procesarlo
            
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
