#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 10 07:14:03 2024

@author: allamb00
"""

def replace_control_bytes(input_bytes):
    # Reemplaza \x00 por '0' y \x01 por '1'
    replaced_bytes = input_bytes.replace(b'\x00', b'0').replace(b'\x01', b'1')
    return replaced_bytes

# def reduce_control_bytes(input_bytes):
#     output_bytes = b''
#     for i in range(len(input_bytes)):
#         if (i + 1) % 30 == 0:  # Verifica si la posición es un múltiplo de 30
#             output_bytes += bytes([input_bytes[i]])
#     return output_bytes

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


def main():
    # Ruta al archivo binario
    file_path = 'received_uchar.bin'

    try:
        # Lee el contenido del archivo binario en modo de lectura de bytes ('rb')
        with open(file_path, 'rb') as file:
            file_content = file.read()

        # Reemplaza los bytes de control
        replaced_content = replace_control_bytes(file_content)
        
        #Reduce los bytes de 30 a 1
        reduced_content = reduce_control_bytes(replaced_content)

        # Escribe el contenido modificado en un nuevo archivo binario
        with open('reduced_signal.bin', 'wb') as new_file:
            new_file.write(reduced_content)

        print("Bytes de control reemplazados correctamente.")
    except FileNotFoundError:
        print(f"El archivo '{file_path}' no fue encontrado.")

if __name__ == "__main__":
    main()
