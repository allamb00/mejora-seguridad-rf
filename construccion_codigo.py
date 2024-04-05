# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 10:13:02 2023

@author: allam
"""

import struct
import time
import keyboard
import random

"""
Estructura código UKeeloq
AUTH KEY: 16 bytes (lesser -> most significant bytes)

FIJO (32b)
32b - Serial Number: 	Número de serie que comparten cerradura y llave
HOPPING CODE (128b)
24b - Delta time:	Segundos que han pasado desde la última pulsación
24b - Sync counter: 	Cuenta el número de pulsaciones de botones
 8b - Battery: 		Nivel de carga de la batería. 7 bits de % y 1 bit con flag de batería baja
 8b - Function code: 	Cuatro posiciones para la función que se envía
32b - Low speed timestamp: Timestamp. Se realiza con un oscilador externo de 31.768kHz. Resolución de 250ms
16b - Button timer: 	Cuenta la duración de la pulsación del botón actual. Se resetea en cada pulsación. Resolución de 50ms. (264ms = 5)
16b - Resync counter:	Cuenta el número de veces que el mando ha estado sin energía, por lo que el TS no va a estar sincronizado
AUTHENTICATION (32b)
32b - Authorization code: Genera un cifrado AES del resto del código (fijo y hopping) y trunca los primeros 32 bits (lesser)
"""

time_res = 250 #Resolución de tiempo de 250ms
btn_res = 50
last_sent_sgn_ts_rounded = 0
signals_sent = 0


"""
FIXED
"""
#Serial
serial_number = (1234567890).to_bytes(32, byteorder='big')

"""
HOPPING
"""
#Delta time
delta_time = 0

#Sync counter
#TODO contar las veces que se envían mensajes
sync_counter= (0).to_bytes(24, byteorder='big')

#Battery
bat_percent = 100
low_bat_flag = 0

#Button timer
button_timer = (0).to_bytes(16, byteorder='big')

#Resync counter
resync_counter = (0).to_bytes(16, byteorder='big')

"""
AUTHENTICATION
"""
#Authentication code
auth_code = (0).to_bytes(32, byteorder='big')


#TODO pasar los bytes a little endian si tal
def on_key_press(event):
    if event.name == '1' or event.name == '2' or event.name == '3' or event.name == '4':
        print("Function", event.name, "sent")
        #Enviar el ts, almacenar el delta etc
        #...
        
        
        #Function code
        if event.name=='1':
            function_code = b'\x00\x01'
        elif event.name == '2':
            function_code = b'\x00\x10'
        elif event.name == '3':
            function_code = b'\x01\x00'
        elif event.name == '4':
            function_code = b'\x10\x00'
                
        
        #Battery
        #Se concatena el flag de batería baja con el % de batería
        battery = low_bat_flag.to_bytes(1, byteorder='big') + bat_percent.to_bytes(7, byteorder='big')
        
        #Para la generación de pulsaciones del botón, se va a generar un número aleatorio entre 50 y 1000ms
        #Luego se multiplica por la resolución de tiempo de pulsación
        random_press_time = random.uniform(50, 1000)
        
        # Redondear hacia abajo en múltiplos de 0.050
        random_press_time_rounded = int(random_press_time / 50) * 50
        #TODO La longitud de almacenamiento de los bytes parece variar de unas pulsaciones a otras
        button_timer = (random_press_time_rounded).to_bytes(16, byteorder='big') 

        
        #Low speed timestamp
        global time_res
        timestamp = int(time.time() * 1000) #Se recogen los milis
        timestamp_rounded = (timestamp // time_res) * time_res  #Se pasa por la resolución de 250ms
        low_speed_ts = struct.pack('d', timestamp_rounded) #Se almacena como bytes
        
        
        #Delta time        
        global last_sent_sgn_ts_rounded
        delta_time = timestamp_rounded - last_sent_sgn_ts_rounded #Se calcula la diferencia en milis desde la última pulsación
        last_sent_sgn_ts_rounded = timestamp_rounded #Se actualiza la última pulsación
        delta_time = struct.pack('d', delta_time) #Se empaqueta como bytes
        
        #Prints
        global sync_counter 
        print("Serial number:" + str(serial_number))
        print("Delta time:" + str(delta_time))
        print("Sync counter:" + str(sync_counter))
        print("Battery:" + str(battery))
        print("Function code:" + str(function_code))
        print("Low speed timestamp:" + str(low_speed_ts))
        print("Button timer:" + str(button_timer))
        print("Resync counter:" + str(resync_counter))
        print("Authorization code:" + str(auth_code))
        
        
        #FINAL HOPPING CODE
        hopping_code = (serial_number + 
                        delta_time + 
                        sync_counter + 
                        battery + 
                        function_code + 
                        low_speed_ts + 
                        button_timer +
                        resync_counter + 
                        auth_code )
        print(hopping_code)
        
        """
        SEND SIGNAL
        """
        
        
        
        
        
      
        global signals_sent 
        signals_sent = signals_sent + 1
        sync_counter= (signals_sent).to_bytes(24, byteorder='big')
        
    elif event.name == 'q':
        global should_break
        should_break = True
    

keyboard.on_press(on_key_press)

should_break = False
while not should_break:
    pass


print("Ejecución finalizada")



""" Proceso inverso para resolver el timestamp en bytes
bytes_timestamp = b'\x40\x09\x21\xfb\x4d\x2b\x5f\x09'  # Ejemplo de secuencia de bytes

# Desempaquetar los bytes en un flotante de doble precisión
timestamp_flotante = struct.unpack('d', bytes_timestamp)[0]

# Obtener el timestamp utilizando time.mktime()
timestamp = time.mktime(time.gmtime()) + (timestamp_flotante - time.time())

print(timestamp)
"""