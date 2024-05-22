#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Transmission
# Author: cascades
# GNU Radio version: 3.10.10.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import blocks
from gnuradio import filter
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from gnuradio import network
import osmosdr
import sip
import argparse

import time
import keyboard
import random
import matplotlib as plt


final_code = 0

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



class Transmission(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Transmission", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Transmission")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "Transmission")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate_0 = samp_rate_0 = 2e6
        self.samp_rate = samp_rate = 2e6
        self.center_freq = center_freq = 433e6

        ##################################################
        # Blocks
        ##################################################

        self.rtlsdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + ""
        )
        self.rtlsdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.rtlsdr_source_0.set_sample_rate(samp_rate)
        self.rtlsdr_source_0.set_center_freq(center_freq, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(True, 0)
        self.rtlsdr_source_0.set_gain(10, 0)
        self.rtlsdr_source_0.set_if_gain(20, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna('', 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_fff(
                interpolation=1,
                decimation=20,
                taps=[],
                fractional_bw=0)
        self.qtgui_time_sink_x_0_0_0_0 = qtgui.time_sink_f(
            1024, #size
            samp_rate, #samp_rate
            "Signal", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0_0_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0_0_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0_0_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_0_0_0.enable_tags(True)
        self.qtgui_time_sink_x_0_0_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0_0_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0_0_0_0.enable_grid(False)
        self.qtgui_time_sink_x_0_0_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_0_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0_0_0_0.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_0_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_0_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_0_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0_0_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_0_0_0_0_win)
        self.qtgui_sink_x_0_0_0 = qtgui.sink_c(
            1024, #fftsize
            window.WIN_BLACKMAN_hARRIS, #wintype
            center_freq, #fc
            samp_rate, #bw
            "RTL-SDR", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            True, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0_0_0.set_update_time(1.0/10)
        self._qtgui_sink_x_0_0_0_win = sip.wrapinstance(self.qtgui_sink_x_0_0_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0_0_0.enable_rf_freq(False)

        self.top_layout.addWidget(self._qtgui_sink_x_0_0_0_win)
        self.qtgui_sink_x_0_0 = qtgui.sink_c(
            1024, #fftsize
            window.WIN_BLACKMAN_hARRIS, #wintype
            center_freq, #fc
            samp_rate, #bw
            "HackRF", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            True, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0_0.set_update_time(1.0/10)
        self._qtgui_sink_x_0_0_win = sip.wrapinstance(self.qtgui_sink_x_0_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0_0.enable_rf_freq(False)

        self.top_layout.addWidget(self._qtgui_sink_x_0_0_win)
        self.osmosdr_sink_0 = osmosdr.sink(
            args="numchan=" + str(1) + " " + "hackrf=0"
        )
        self.osmosdr_sink_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.osmosdr_sink_0.set_sample_rate(samp_rate)
        self.osmosdr_sink_0.set_center_freq(center_freq, 0)
        self.osmosdr_sink_0.set_freq_corr(0, 0)
        self.osmosdr_sink_0.set_gain(10, 0)
        self.osmosdr_sink_0.set_if_gain(20, 0)
        self.osmosdr_sink_0.set_bb_gain(20, 0)
        self.osmosdr_sink_0.set_antenna('', 0)
        self.osmosdr_sink_0.set_bandwidth(0, 0)
        self.network_udp_sink_0 = network.udp_sink(gr.sizeof_short, 1, '127.0.0.1', 2000, 0, 1472, False)
        self.blocks_vector_source_x_0 = blocks.vector_source_c(final_code, False, 1, [])
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_threshold_ff_0 = blocks.threshold_ff(0.025, 0.075, 0)
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_gr_complex*1, 600)
        self.blocks_float_to_short_0 = blocks.float_to_short(1, 1)
        self.blocks_add_const_vxx_0 = blocks.add_const_ff(0.5)
        self.analog_am_demod_cf_0 = analog.am_demod_cf(
        	channel_rate=samp_rate,
        	audio_decim=1,
        	audio_pass=10e3,
        	audio_stop=100e3,
        )


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_am_demod_cf_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.blocks_add_const_vxx_0, 0), (self.blocks_threshold_ff_0, 0))
        self.connect((self.blocks_float_to_short_0, 0), (self.network_udp_sink_0, 0))
        self.connect((self.blocks_repeat_0, 0), (self.osmosdr_sink_0, 0))
        self.connect((self.blocks_repeat_0, 0), (self.qtgui_sink_x_0_0, 0))
        self.connect((self.blocks_threshold_ff_0, 0), (self.blocks_float_to_short_0, 0))
        self.connect((self.blocks_threshold_ff_0, 0), (self.qtgui_time_sink_x_0_0_0_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.analog_am_demod_cf_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.qtgui_sink_x_0_0_0, 0))
        self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_repeat_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_add_const_vxx_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.blocks_throttle2_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "Transmission")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate_0(self):
        return self.samp_rate_0

    def set_samp_rate_0(self, samp_rate_0):
        self.samp_rate_0 = samp_rate_0

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.osmosdr_sink_0.set_sample_rate(self.samp_rate)
        self.qtgui_sink_x_0_0.set_frequency_range(self.center_freq, self.samp_rate)
        self.qtgui_sink_x_0_0_0.set_frequency_range(self.center_freq, self.samp_rate)
        self.qtgui_time_sink_x_0_0_0_0.set_samp_rate(self.samp_rate)
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.osmosdr_sink_0.set_center_freq(self.center_freq, 0)
        self.qtgui_sink_x_0_0.set_frequency_range(self.center_freq, self.samp_rate)
        self.qtgui_sink_x_0_0_0.set_frequency_range(self.center_freq, self.samp_rate)
        self.rtlsdr_source_0.set_center_freq(self.center_freq, 0)


def build_code(func):
    if func == '1' or func == '2' or func == '3' or func == '4':
        print("Function", func, "sent")
        #Enviar el ts, almacenar el delta etc
        #...
                
        #Function code
        if func=='1':
            function_code = 1
        elif func == '2':
            function_code = 2
        elif func == '3':
            function_code = 4
        elif func == '4':
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
        plain_hopping_code = (serial_number_b + 
                        delta_time_b + 
                        sync_counter_b + 
                        battery_b + 
                        function_code_b + 
                        low_speed_ts_b + 
                        button_timer_b +
                        resync_counter_b +
                        auth_code_b)
        
        print("\n" + plain_hopping_code + "\n")
        
        """
        CIPHER
        """      
        # key_gen = low_speed_ts_b
        # key_len = 124        
        # key = ""        
        # while len(key) < key_len:
        #     key += key_gen
        
        # key = key[:key_len]
        
        # print("\n Key: " + key)
        
        # hopping_code = format(int(plain_hopping_code, 2)^int(key,2), f'0{hopping_code_len}b')
        # print ("\n Hopping code: " + hopping_code)
        
        # rolling_code = (serial_number_b + hopping_code + auth_code_b)
        
        # print ("\n FINAL ROLLING CODE: " + rolling_code)
        #SENDING
        
        #TODO cifrado simétrico del codigo
        

        
        
        final_code_b = plain_hopping_code
        
        global final_code
        final_code = [int(bit) for bit in final_code_b]
        print("Array de números:", final_code)        
        
      
        global signals_sent 
        signals_sent = signals_sent + 1
        sync_counter_b = format(signals_sent, f'0{sync_counter_len}b')    



def main(options=None):
    
    parser = argparse.ArgumentParser(description="Script de envío de códigos")
    parser.add_argument('--func', type=str, help='Código de función: 1-2-3-4')
    args = parser.parse_args()
    build_code(args.func)
    top_block_cls=Transmission
    
    top_block_cls = Transmission
    qapp = Qt.QApplication(sys.argv)
    tb = top_block_cls()
    tb.start()
    tb.show()
    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        Qt.QApplication.quit()
        
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    # Crear un QTimer para parar el programa después de 3 segundos
    timer = Qt.QTimer()
    timer.timeout.connect(sig_handler)  # Llama a sig_handler después del timeout
    timer.start(3000)  # 3000 ms = 3 segundos
    
    
    qapp.exec_()
    
    # should_break = False
    # while not should_break:
    #     pass

if __name__ == '__main__':
    main()
