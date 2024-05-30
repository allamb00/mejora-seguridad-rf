# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import socket
import struct
import keyboard
import time
import crcmod

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import hashes
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
buffer_max_length = 216
buffer = []
count = 0 #Variable global para que no se corte la cuenta entre payloads

#Serial del fabricante para distinguir el código
preamble = '00000111010110111100110100010101' 
preamble_len = len(preamble)
code_len = 192 #Tamaño total del código

#Configuración de la ventana de tiempo válida para la recepción
window_seconds = 5




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

# Función que procesa los datos en un buffer a medida que llegan
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
                # Código válido encontrado
                # Extraer la cadena de 188 bits
                code = buffer_bits[preamble_index:preamble_index+code_len]
                buffer = []
                return code
        
        # Eliminar los bits antiguos del buffer
        buffer = buffer[-buffer_max_length:]

# Función que separa los segmentos del rolling code
def split_code_segments(code):
    if len(code) != 192:
        raise ValueError(f"La longitud del código no es de 192 caracteres ({len(code)})")

    fixed = code[:32]
    hopping = code[32:32+128]
    crc = code[32+128:32+128+32]

    return fixed, hopping, crc

# Función que separa los segmentos del rolling code
def split_hopping_code_segments(code):
    if len(code) != 128:
        raise ValueError(f"La longitud del texto cifrado debe ser exactamente 124 bits ({len(code)})")

    padding = code[:4]
    delta_time = code[4:28]
    sync_counter = code[28:52]
    battery = code[52:60]
    function_code = code[60:64]
    low_sp_ts = code[64:96]
    btn_timer = code[96:112]
    resync_counter = code[112:128]

    return delta_time, sync_counter, battery, function_code, low_sp_ts, btn_timer, resync_counter

# Función para descifrar
def decrypt(cipher_bits, key):
    # Verificar que la longitud del texto cifrado sea exactamente 128 bits
    if len(cipher_bits) != 128:
        raise ValueError(f"La longitud del texto cifrado debe ser exactamente 128 bits ({cipher_bits})")

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

def calculate_crc(data, polynomial=0x104C11DB7, init_value=0):
    # Convertir la cadena de bits en bytes
    byte_data = int(data, 2).to_bytes((len(data) + 7) // 8, byteorder='big')

    # Crear la función CRC utilizando crcmod
    crc_func = crcmod.mkCrcFun(polynomial, initCrc=init_value, rev=False)

    # Calcular el CRC
    crc_value = crc_func(byte_data)

    # Convertir el CRC calculado a una cadena de bits de 32 bits
    crc_bits = f'{crc_value:032b}'

    return crc_bits

def is_timestamp_valid(bin_timestamp):
    # Convertir el timestamp binario a un entero
    timestamp = int(bin_timestamp, 2)
    
    # Obtener el timestamp actual
    current_timestamp = int(time.time())

    # Verificar si el timestamp está dentro de la ventana de tiempo
    if current_timestamp - window_seconds <= timestamp <= current_timestamp + window_seconds:
        return True
    else:
        return False


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
            rolling_code = process_bits(reduced) # Busca el preámbulo en la entrada
            if rolling_code:
                # Separar el código en parte fija, dinámica y CRC32
                fixed_code, hopping_code, crc_code = split_code_segments(rolling_code)
                print(f'Parte fija: {fixed_code}')
                print(f'Hopping code: {hopping_code}')
                print(f'CRC-32: {crc_code}')
                
                # Concatenar los bits y calcular el CRC
                combined_code = fixed_code + hopping_code
                computed_crc = calculate_crc(combined_code)
                
                # Comparar con el CRC esperado
                if computed_crc == crc_code:
                    print("CRC coincide. ", end='')
                    
                    # Separamos la parte dinámica en cada uno de sus campos
                    plain_hopping_code = decrypt(hopping_code, key)                    
                    (delta_time, 
                    sync_counter, 
                    battery, 
                    function_code, 
                    low_sp_ts, 
                    btn_timer, 
                    resync_counter
                    ) = split_hopping_code_segments(plain_hopping_code)
                    
                    if is_timestamp_valid(low_sp_ts) :
                        
                        print("TS coincide.")
                        print("¡Código válido!\n")
                        print(f"delta_time: {delta_time}")
                        print(f"sync_counter: {sync_counter}")
                        print(f"battery: {battery}")
                        print(f"function_code: {function_code}")
                        print(f"low_sp_ts: {low_sp_ts}")
                        print(f"btn_timer: {btn_timer}")
                        print(f"resync_counter: {resync_counter}")


                    else:
                        print("El código ha sido enviado fuera de tiempo.")
                    
                else:
                    print(f"CRC no coincide.\n" + 
                          f"Esperado: {computed_crc}\n" +
                          f"Original: {crc_code}")
                
                print("\nEscuchando...")
            
    finally:
        sock.close()  # Cierra el socket al finalizar el script
        print("\nEjecución finalizada correctamente\n")
        

if __name__ == '__main__':
    main()
