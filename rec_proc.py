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

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# Definir clave y IV fijos
key = b'0123456789abcdef0123456789abcdef'  # 32 bytes para AES-256
iv = b'0123456789abcdef'  # 16 bytes para el IV

# Configura el socket UDP
UDP_IP = "127.0.0.1"  # Dirección IP a la que GNU Radio está enviando los datos
UDP_PORT = 2000  # Puerto al que GNU Radio está enviando los datos
UDP_BUFFER_SIZE = 1472

# Crea el socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Inicializa un buffer con una longitud máxima de 188+25 caracteres para que
# quepa el código entero y no quede cortado por un cambio de 
buffer_max_length = 213
buffer = []
count = 0 #Variable global para que no se corte la cuenta entre payloads

#Serial del fabricante para distinguir el código
preamble = '00000111010110111100110100010101' 
preamble_len = len(preamble)
code_len = 188 #Tamaño total del código




def is_all_zeros(bit_data):
    return all(bit == '0' for bit in bit_data)
            
def replace_control_bytes(data):
    # Reemplaza \x00 por '0' y \x01 por '1'
    bits = data.replace(b'\x01\x00', b'1').replace(b'\x00\x00', b'0')
    return bits.decode()

def reduce_control_bits(input_bits):
    output_bits = ''
    current_bit = input_bits[0]  # Inicializa el primer bit
    
    global count
    count = 0
    for bit in input_bits:
        if bit != current_bit or count >= 30:
            for i in range(round(count/30)): #Soluciona la inconsistencia de 0s y 1s
                output_bits += current_bit
            current_bit = bit
            count = 1
        else:
            count += 1
    # Agrega el último bit al string reducido
    if round(count/30) == 1 :
        output_bits += current_bit

    return output_bits

#Función que procesa los datos en un buffer a medida que llegan
def process_bits(bit_data):   
    global buffer
    
    # Agregar los nuevos bits al buffer
    buffer.extend(bit_data)

    # Si el buffer tiene suficientes bits, buscar el preámbulo
    if len(buffer) >= buffer_max_length:
        # Convertir el buffer a una cadena de bits
        buffer_bits = ''.join(buffer)

        # Buscar el preámbulo en el buffer
        preamble_index = buffer_bits.find(preamble)
        
        if preamble_index != -1:
            # Verificar si la cadena de 188 bits está completa
            if preamble_index + code_len <= len(buffer_bits):
                # Extraer la cadena de 188 bits
                code = buffer_bits[preamble_index:preamble_index+code_len]
                print("\nCódigo válido encontrado")
                buffer = []
                return code
            else:
                print(".", end="")
        
        # Eliminar los bits antiguos del buffer
        buffer = buffer[-buffer_max_length:]

#Función que separa los segmentos del rolling code
def split_code_segments(code):
    if len(code) != 188:
        raise ValueError(f"La longitud del código no es de 188 caracteres ({len(code)})")

    fixed = code[:32]
    hopping = code[32:155]
    crc = code[156:188]

    return fixed, hopping, crc

# Función para descifrar
def decrypt(cipher_bits, key):
    # Verificar que la longitud del texto cifrado sea exactamente 124 bits
    if len(cipher_bits) != 124:
        raise ValueError("La longitud del texto cifrado debe ser exactamente 124 bits")

    # Convertir la cadena de bits cifrados en una cadena de bytes
    cipher_bytes = bytes(int(cipher_bits[i:i+8], 2) for i in range(0, len(cipher_bits), 8))

    # Crear un objeto de cifrado
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())

    # Descifrar el texto cifrado
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(cipher_bytes) + decryptor.finalize()

    # Convertir los bytes descifrados a bits
    decrypted_bits = ''.join(format(byte, '08b') for byte in decrypted_bytes)

    return decrypted_bits

def main():
    # Bucle para recibir datos continuamente
    print("Escuchando...")
    for a in range(0):
        print(round(2/30))
    try:
        while True:
            data, addr = sock.recvfrom(UDP_BUFFER_SIZE)  # Recibe datos del socket
            replaced = replace_control_bytes(data)
            reduced = reduce_control_bits(replaced)  
            
            rolling_code = 0
            rolling_code = process_bits(reduced) #Busca el preámbulo en la entrada
            if rolling_code:
                #Separar el código en parte fija, dinámica y CRC32
                fixed_code, hopping_code, crc = split_code_segments(rolling_code)
                print(f'Parte fija: {fixed_code}')
                print(f'Hopping code: {hopping_code}')
                print(f'CRC-32: {crc}')
            
            # """
            # DECIPHER
            # """
            # # Descifrar el hopping_code
            # plain_hopping_code = decrypt(hopping_code, key)
            # print("Hopping code descifrado:", plain_hopping_code)
    
            # """ Proceso inverso para resolver el timestamp en bytes
            # bytes_timestamp = b'\x40\x09\x21\xfb\x4d\x2b\x5f\x09'  # Ejemplo de secuencia de bytes
    
            # # Desempaquetar los bytes en un flotante de doble precisión
            # timestamp_flotante = struct.unpack('d', bytes_timestamp)[0]
    
            # # Obtener el timestamp utilizando time.mktime()
            # timestamp = time.mktime(time.gmtime()) + (timestamp_flotante - time.time())
    
            # print(timestamp)
            # """

            
            
            
            
            
            
            
            
    finally:
        sock.close()  # Cierra el socket al finalizar el script
        print("\nEjecución finalizada correctamente\n")
        

if __name__ == '__main__':
    main()
