# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import socket
import time
import crcmod

key = b'0123456789abcdef0123456789abcdef'  # 32 bytes para AES-256

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
sync_counter_local = 0

#Configuración de la ventana de tiempo válida para la recepción
window_seconds = 5




def is_all_zeros(bit_data):
    return all(bit == '0' for bit in bit_data)
           
# Definición de la función para convertir varios tipos de valores a bits
def to_bits(value, length=None):
    if not isinstance(value, int):
        raise TypeError("El valor debe ser un entero")
    
    # Convertir el entero a su representación en bits
    bits = format(value, 'b')
    
    # Completar con ceros a la izquierda
    if length is not None:
        if length < len(bits):
            raise ValueError("La longitud especificada es menor que la longitud de bits del valor")
        bits = bits.zfill(length)
    
    return bits
 
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
            for _ in range(round(count/30)): #Soluciona la inconsistencia de 0s y 1s
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

    delta_time = code[4:28]
    sync_counter = code[28:52]
    battery = code[52:60]
    function_code = code[60:64]
    low_sp_ts = code[64:96]
    btn_timer = code[96:112]
    resync_counter = code[112:128]

    return delta_time, sync_counter, battery, function_code, low_sp_ts, btn_timer, resync_counter

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
    
    
def is_sync_valid(sync_counter_keyfob_b, sync_counter = None):
    # Convertir el sync counter a entero
    sync_counter_keyfob = int(sync_counter_keyfob_b, 2)
    
    # Si no se recibe un segundo argumento, se compara con el contador local
    if sync_counter is None:
        global sync_counter_local
        sync_counter = sync_counter_local
        
    # Comparar el contador local con el del mando
    if sync_counter == sync_counter_keyfob:
        return True
    else:
        return False

def handle_received_data(data):
    replaced = replace_control_bytes(data)
    reduced = reduce_control_bits(replaced)
    rolling_code = process_bits(reduced)  # Busca el preámbulo en la entrada

    if rolling_code:
        print(f"\nCodigo recibido ({len(rolling_code)}b): {rolling_code}\n")
        process_rolling_code(rolling_code)

def process_rolling_code(rolling_code):
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
        handle_valid_crc(hopping_code, rolling_code)
    else:
        print("CRC no coincide.\n" +
              f"Esperado: {computed_crc}\n" +
              f"Original: {crc_code}")
    print("\nEscuchando...")

def handle_valid_crc(hopping_code, rolling_code):
    global sync_counter_local

    # Se separa la parte dinámica en cada uno de sus campos
    (delta_time, sync_counter, battery, function_code, low_sp_ts, btn_timer, resync_counter
    ) = split_hopping_code_segments(hopping_code)

    # Se comprueba si el código está sincronizado
    if is_sync_valid(sync_counter):
        handle_synchronized_code(delta_time, sync_counter, battery, function_code, low_sp_ts, btn_timer, resync_counter, rolling_code)
    else:
        handle_unsynchronized_code(hopping_code)

def handle_synchronized_code(delta_time, sync_counter, battery, function_code, low_sp_ts, btn_timer, resync_counter, rolling_code):
    global sync_counter_local

    # Los dispositivos están sincronizados  
    if is_timestamp_valid(low_sp_ts):
        print("TS coincide.")
        print("¡Código válido!\n")
        print(f"delta_time: {delta_time}")
        print(f"sync_counter: {sync_counter}")
        print(f"battery: {battery}")
        print(f"function_code: {function_code}")
        print(f"low_sp_ts: {low_sp_ts}")
        print(f"btn_timer: {btn_timer}")
        print(f"resync_counter: {resync_counter}")

        execute_function(function_code)

        # Se apunta al siguiente código
        sync_counter_local = sync_counter_local + 1

        # Se guarda el valor del código capturado
        save_captured_code(rolling_code)
    else:
        print("El código ha sido enviado fuera de tiempo.")
        print("Se ignora el código")

def handle_unsynchronized_code(hopping_code):
    global sync_counter_local

    # Los dispositivos NO están sincronizados
    # Se comprueba si están en un rango admisible de sincronía
    for i in range(10):
        (delta_time, sync_counter, battery, function_code, low_sp_ts, btn_timer, resync_counter
        ) = split_hopping_code_segments(hopping_code)
        if is_sync_valid(sync_counter, i):
            # El mando está ligeramente desfasado
            # Se actualiza en local
            sync_counter_local = int(sync_counter, 2) + 1
            print("Mando desfasado")
            print("Se ha resincronizado")
            return

    # El mando está demasiado desfasado
    # Se ignora
    print("Mando desfasado")
    print("Se ignora el código")

def execute_function(function_code):
    function_b = int(function_code, 2)

    if function_b == 1:
        print('Apertura de puertas')
    elif function_b == 2:
        print('Bloqueo de puertas')
    elif function_b == 4:
        print('Apertura de maletero')
    elif function_b == 8:
        print('Encendido de motor')

def save_captured_code(rolling_code):
    with open("captura", "w") as file:
        file.write(rolling_code)


def main():
    # Bucle para recibir datos continuamente
    print("Escuchando...")
    
    try:
        while True:
            data, _ = sock.recvfrom(UDP_BUFFER_SIZE)  # Recibe datos del socket
            handle_received_data(data)
    finally:
        sock.close()  # Cierra el socket al finalizar el script
        print("\nEjecución finalizada correctamente\n")
if __name__ == '__main__':
    main()
