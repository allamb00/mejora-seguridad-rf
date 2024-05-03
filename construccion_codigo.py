# -*- coding: utf-8 -*-
"""
Created on Mon Jul  3 10:13:02 2023

@author: allam
"""

import time
import keyboard
import random

from rtlsdr import *
import matplotlib as plt

"""
Estructura código UKeeloq
AUTH KEY: 16 Bytes (lesser -> most significant Bytes)

FIJO (32b)
32b - Serial Number: 	Número de serie que comparten cerradura y llave
HOPPING CODE (128b)
24b - Delta time:	Segundos que han pasado desde la última pulsación
24b - Sync counter: 	Cuenta el número de pulsaciones de botones
 8b - Battery: 		Nivel de carga de la batería. 7 bits de % y 1 bit con flag de batería baja
 4b - Function code: 	Cuatro posiciones para la función que se envía
32b - Low speed timestamp: Timestamp. Se realiza con un oscilador externo de 31.768kHz. Resolución de 250ms. RESOLUCION DE SEGUNDOS
16b - Button timer: 	Cuenta la duración de la pulsación del botón actual. Se resetea en cada pulsación. Resolución de 50ms. (264ms = 5)
16b - Resync counter:	Cuenta el número de veces que el mando ha estado sin energía, por lo que el TS no va a estar sincronizado
AUTHENTICATION (32b)
32b - Authorization code: Genera un cifrado AES del resto del código (fijo y hopping) y trunca los primeros 32 bits (lesser)

En total son 
"""

time_res = 250 #Resolución de tiempo de 250ms
btn_res = 50
last_sent_sgn_ts = 0
signals_sent = 0


"""
FIXED
"""
#Serial
serial_number = 123456789
serial_number_len = 32
serial_number_b = format(serial_number, f'0{serial_number_len}b')

"""
HOPPING
"""
hopping_code_len = 124

#Delta time
delta_time = 0
delta_time_len = 24
delta_time_b = format(delta_time, f'0{delta_time_len}b')

last_sent_sgn_ts = 0

#Sync counter
#TODO contar las veces que se envían mensajes
sync_counter = 0
sync_counter_len = 24
sync_counter_b = format(sync_counter, f'0{sync_counter_len}b')

#Battery
bat_percent = 100
low_bat_flag = 0

#Button timer
button_timer = 0
button_timer_len = 16
button_timer_b = format(button_timer, f'0{button_timer_len}b')

#Resync counter
resync_counter = 0
resync_counter_len = 16
resync_counter_b = format(resync_counter, f'0{resync_counter_len}b')

"""
AUTHENTICATION
"""
#Authentication code
auth_code = 0
auth_code_len = 32
auth_code_b = format(auth_code, f'0{auth_code_len}b')


def on_key_press(event):
    if event.name == '1' or event.name == '2' or event.name == '3' or event.name == '4':
        print("Function", event.name, "sent")
        #Enviar el ts, almacenar el delta etc
        #...
        
        
        #Function code
        if event.name=='1':
            function_code = 1
        elif event.name == '2':
            function_code = 2
        elif event.name == '3':
            function_code = 4
        elif event.name == '4':
            function_code = 8
                
        function_code_len = 4
        function_code_b = format(function_code, f'0{function_code_len}b')
        
        #Battery
        #Se concatena el flag de batería baja con el % de batería  
        low_bat_flag_len = 1
        low_bat_flag_b = format(low_bat_flag, f'0{low_bat_flag_len}b')
        
        bat_percent_len = 7
        bat_percent_b = format(bat_percent, f'0{bat_percent_len}b')
        
        battery_b = low_bat_flag_b + bat_percent_b                
        
        #Para la generación de pulsaciones del botón, se va a generar un número aleatorio entre 50 y 1000ms
        #Luego se multiplica por la resolución de tiempo de pulsación
        random_press_time = random.uniform(50, 1000)
        
        # Redondear hacia abajo en múltiplos de 0.050
        random_press_time_rounded = int(random_press_time / 50) * 50
        #TODO La longitud de almacenamiento de los bytes parece variar de unas pulsaciones a otras        
        button_timer = random_press_time_rounded
        button_timer_len = 16
        button_timer_b = format(button_timer, f'0{button_timer_len}b')

        #Low speed timestamp
        global time_res
        
        seconds, millis = divmod(time.time(),1)
        timestamp = int(seconds)        
        low_speed_ts_len = 32
        low_speed_ts_b = format(timestamp, f'0{low_speed_ts_len}b')
        
        
        #Delta time        
        global last_sent_sgn_ts
        delta_time = timestamp - last_sent_sgn_ts #Se calcula la diferencia en segundos desde la última pulsación
        last_sent_sgn_ts = timestamp #Se actualiza la última pulsación
        delta_time_b = format(min(delta_time, 16777215), f'0{delta_time_len}b') #Recoge la diferencia entre timestamps o el valor máximo del campo en caso de superarlo
        
        #Prints
        global sync_counter_b 
        print("Serial number: " + serial_number_b)
        print("Delta time: " + delta_time_b)
        print("Sync counter: " + sync_counter_b)
        print("Battery: " + battery_b)
        print("Function code: " + function_code_b)
        print("Low speed timestamp: " + low_speed_ts_b)
        print("Button timer: " + button_timer_b)
        print("Resync counter: " + resync_counter_b)
        print("Authorization code: " + auth_code_b)
        
        
        #FINAL HOPPING CODE
        plain_hopping_code = (delta_time_b + 
                        sync_counter_b + 
                        battery_b + 
                        function_code_b + 
                        low_speed_ts_b + 
                        button_timer_b +
                        resync_counter_b)
        print("\n" + plain_hopping_code + "\n")
        
        """
        CIPHER
        """      
        key_gen = low_speed_ts_b
        key_len = 124        
        key = ""        
        while len(key) < key_len:
            key += key_gen
        
        key = key[:key_len]
        
        print("\n Key: " + key)
        
        hopping_code = format(int(plain_hopping_code, 2)^int(key,2), f'0{hopping_code_len}b')
        print ("\n Hopping code: " + hopping_code)
        
        rolling_code = (serial_number_b + hopping_code + auth_code_b)
        
        print ("\n FINAL ROLLING CODE: " + rolling_code)
        
        """
        DECIPHER
        """        


        """
        SEND SIGNAL
        """
        
        sdr = RtlSdr()
        
        sdr.sample_rat = 2.048e6
        sample_rate=sdr.sample_rate
        sdr.center_freq = 433e6
        center_freq=sdr.center_freq
        sdr.gain = 'auto'
        
        plt.close()
        NumberOfSamples = sample_rate/1
        
        samples = sdr.read_samples(NumberOfSamples)
        sdr.close()
        
        #print
        
        plt.psd(samples, Fs = sample_rate / 1e6, Fc = center_freq / 1e6)
        plt.xlabel('Frequency (Mhz)')
        plt.ylabel('Relative power (dB)')
        
        del samples
        plt.show()        
        
      
        global signals_sent 
        signals_sent = signals_sent + 1
        sync_counter_b = format(signals_sent, f'0{sync_counter_len}b')
        
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