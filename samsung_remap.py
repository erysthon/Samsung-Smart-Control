import evdev
from evdev import ecodes
import time
import subprocess
import sys

# --- CONFIGURAÇÕES ---
DEVICE_NAME = "Smart Control"
DEBOUNCE_TIME = 0.2  # Timeout de 0.2s para evitar cliques duplos do Bluetooth

# --- FUNÇÕES DE COMANDO ---
def power_off():
    # Desliga o computador imediatamente
    subprocess.run(["systemctl", "poweroff"])

# --- MAPEAMENTO (Valor REL_MISC : Ação) ---
# Se for um número: envia tecla de teclado virtual
# Se for uma função: executa o comando Python
mapping = {
    2:   power_off,			# Botão de Ligar
    160: ecodes.KEY_A,			# Botão Microfone (Exemplo: tecla 'A')
    210: ecodes.KEY_KBDILLUMTOGGLE,	# Botão 123 (Mapeado para toggle de luz de teclado ou livre)
    246: ecodes.KEY_B,			# Botão Paisagem (Exemplo: tecla 'B')
    96:  ecodes.KEY_UP,         	# Cima
    97:  ecodes.KEY_DOWN,       	# Baixo
    101: ecodes.KEY_LEFT,       	# Esquerda
    98:  ecodes.KEY_RIGHT,      	# Direita
    104: ecodes.KEY_ENTER,      	# Centro (OK)
    88:  ecodes.KEY_ESC,        	# Botão Voltar (Mapeado como ESC para sair de menus)
    121: ecodes.KEY_LEFTMETA,   	# Botão Home (Mapeado para a tecla 'Super/Windows' para abrir o menu)
    185: ecodes.KEY_PLAYPAUSE,  	# Play/Pause
    7:   ecodes.KEY_VOLUMEUP,   	# Vol +
    11:  ecodes.KEY_VOLUMEDOWN, 	# Vol -
    15:  ecodes.KEY_MUTE,       	# Mudo
    18:  ecodes.KEY_NEXTSONG,   	# Channel + (Próxima Mídia)
    16:  ecodes.KEY_PREVIOUSSONG, 	# Channel - (Mídia Anterior)
    79:  ecodes.KEY_C,          	# Channel Central (Exemplo: tecla 'C')
    243: ecodes.KEY_D,    		# Botão Netflix (Exemplo: tecla 'D')
    244: ecodes.KEY_E, 			# Botão Prime Video (Exemplo: tecla 'F')
    191: ecodes.KEY_F, 			# Botão Globo Play (Exemplo: tecla 'G')
}

def find_correct_instance():
    """
    Procura entre todas as instâncias do Smart Control aquela 
    que suporta eventos do tipo EV_REL e o código REL_MISC (9).
    """
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if DEVICE_NAME in device.name:
            capabilities = device.capabilities()
            # Verifica se o dispositivo tem suporte a EV_REL (tipo 2)
            if ecodes.EV_REL in capabilities:
                # Verifica se dentro de EV_REL existe o código 9 (REL_MISC)
                rel_events = capabilities[ecodes.EV_REL]
                if 9 in rel_events:
                    return device
    return None

def main():
    print(f"Aguardando conexão do {DEVICE_NAME}...")
    
    device = None
    while device is None:
        device = find_correct_instance()
        if device is None:
            time.sleep(2)
    
    # Grab garante que o sistema não tente interpretar o REL_MISC de outra forma
    # enquanto o script estiver rodando.
    try:
        device.grab()
    except IOError:
        pass 

    print(f"Conectado com sucesso ao {device.name} em {device.path}")

    # Criação do dispositivo virtual
    registered_keys = [v for v in mapping.values() if isinstance(v, int)]
    ui = evdev.UInput({ecodes.EV_KEY: registered_keys})

    last_event_time = 0
    last_value = None

    try:
        for event in device.read_loop():
            if event.type == ecodes.EV_REL and event.code == 9:
                current_time = time.time()
                
                # Lógica de Debounce e Valor Exato
                if (current_time - last_event_time) > DEBOUNCE_TIME or event.value != last_value:
                    action = mapping.get(event.value)
                    
                    if action:
                        if callable(action):
                            action()
                        else:
                            ui.write(ecodes.EV_KEY, action, 1)
                            ui.write(ecodes.EV_KEY, action, 0)
                            ui.syn()
                        print(f"Botão processado -> {event.value}")
                    
                    last_event_time = current_time
                    last_value = event.value

    except (OSError, evdev.IOError):
        print("Dispositivo desconectado.")
        sys.exit(1)

if __name__ == "__main__":
    main()
