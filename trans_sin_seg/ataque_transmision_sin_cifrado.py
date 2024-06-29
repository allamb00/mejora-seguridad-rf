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

import crcmod
import hashlib

from Crypto.Cipher import AES



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

"""
Estructura código

FIJO (32b)
32b - Serial Number: 	Número de serie que comparten cerradura y llave
HOPPING CODE (128b) 
 4b - Padding:  Ajusta el tamaño del bloque para el cifrado
24b - Delta time:	Segundos que han pasado desde la última pulsación
24b - Sync counter: 	Cuenta el número de pulsaciones de botones
 8b - Battery: 		Nivel de carga de la batería. 7 bits de % y 1 bit con flag de batería baja
 4b - Function code: 	Cuatro posiciones para la función que se envía
32b - Low speed timestamp: Timestamp. Se realiza con un oscilador externo de 31.768kHz. Resolución de 250ms. RESOLUCION DE SEGUNDOS
16b - Button timer: 	Cuenta la duración de la pulsación del botón actual. Se resetea en cada pulsación. Resolución de 50ms. (264ms = 5)
16b - Resync counter:	Cuenta el número de veces que el mando ha estado sin energía, por lo que el TS no va a estar sincronizado
AUTHENTICATION (32b)
32b - Authorization code: Genera un CRC del resto del código (fijo y hopping) y trunca los primeros 32 bits (lesser)

"""

time_res = 250 #Resolución de tiempo de 250ms
btn_res = 50
last_sent_sgn_ts = 0
signals_sent = 0

#Vector del rolling code para poder ser enviado
rolling_code_v = 0

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
        self.blocks_vector_source_x_0 = blocks.vector_source_c(rolling_code_v, False, 1, [])
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

        

# Función para obtener la clave
def derive_key():
    global sync_counter
    seed_bytes = sync_counter.to_bytes(16, byteorder='big')  # Convierte la seed a bytes
    hash_obj = hashlib.sha256(seed_bytes).digest()  # Deriva un hash SHA-256
    key = hash_obj[:16]  # Toma los primeros 16 bytes para la clave AES-128
    iv = hash_obj[16:32]  # Toma los siguientes 16 bytes para el IV
    return key, iv

def encrypt(bits, key, iv):
    if len(bits) != 128:
        raise ValueError(f"La longitud del texto plano debe ser exactamente 128 bits ({len(bits)})")

    if len(key) not in [16, 24, 32]:
        raise ValueError(f"La clave debe tener una longitud de 16, 24 o 32 bytes ({len(key)})")

    # Se asegura de que el iv cumple los 16 bytes
    iv_bytes = iv.to_bytes(16, byteorder='big')
    cipher = AES.new(key, AES.MODE_CBC, iv_bytes)

    # Convierte la cadena de bits a bytes
    byte_data = int(bits, 2).to_bytes(16, byteorder='big')

    # Cifra los datos
    cipher_text = cipher.encrypt(byte_data)

    # Asegúrate de que el texto cifrado tiene exactamente 16 bytes
    if len(cipher_text) != 16:
        raise ValueError("El texto cifrado no tiene la longitud esperada de 16 bytes")

    # Convierte el texto cifrado a bits
    cipher_bits = ''.join(f'{byte:08b}' for byte in cipher_text)
    
    return cipher_bits


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

#Función para construir el código del envío desde el fichero almacenado
def build_code(func):
        global rolling_code_v
        
        with open("captura", "r") as file:
            captura = file.read().strip()            
        print("Se ha leido el código a enviar: " + captura)        
        
        # Se modifica la función para que abra las puertas
        captura = captura[:92] + '0001' + captura[96:]
        
        # Reelaboracion del CRC
        auth_code_b = calculate_crc(captura[:160])
        nueva_captura = captura[:160]+auth_code_b
        print("Se ha reconstruido el CRC: ")
            
        rolling_code_v = [int(bit) for bit in nueva_captura]         

def main(options=None):
    
    parser = argparse.ArgumentParser(description="Script de envío de códigos")
    parser.add_argument('--func', type=str, help='Código de función: 1-2-3-4')
    args = parser.parse_args()
    build_code(args.func)
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
    # Crear un QTimer para parar el programa después de 2 segundos
    timer = Qt.QTimer()
    timer.timeout.connect(sig_handler)  # Llama a sig_handler después del timeout
    timer.start(2000)  
    
    qapp.exec_()

if __name__ == '__main__':
    main()
