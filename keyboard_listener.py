import keyboard

def on_press(event):
    print(f'Tecla presionada: {event.name}')

def on_release(event):
    print(f'Tecla liberada: {event.name}')
    if event.name == 'esc':
        # Detener la detección de teclas
        keyboard.unhook_all()

# Registrar los manejadores de eventos de teclado
keyboard.on_press(on_press)
keyboard.on_release(on_release)

# Mantener el script en ejecución
keyboard.wait('esc')
