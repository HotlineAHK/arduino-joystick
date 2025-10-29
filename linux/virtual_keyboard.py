#!/usr/bin/env python3

import time
import serial
from evdev import UInput, ecodes as e

from joystick_manager import JoystickManager

# --- НАСТРОЙКИ ---
SERIAL_PORT = '/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0'
BAUD_RATE = 500000

KEY_DELAY = 0.020  # Высокая частота обработки
# -----------------

joymgr = JoystickManager()

joymgr.find_arduino_port()

SERIAL_PORT = joymgr.port

# Создаём виртуальную клавиатуру
cap = {
    e.EV_KEY: [
        e.KEY_W, e.KEY_A, e.KEY_S, e.KEY_D,
        e.KEY_SPACE
    ]
}

try:
    ui = UInput(cap, name="Arduino Joystick Keyboard", bustype=e.BUS_USB)
    print("✅ Виртуальная клавиатура создана")
except PermissionError:
    print("❌ Ошибка: нет доступа к /dev/uinput")
    print("💡 Выполни: sudo usermod -aG input $USER и перезагрузись")
    exit(1)
except Exception as ex:
    print(f"❌ Ошибка: {ex}")
    exit(1)

# Подключаемся к Arduino
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"🔌 Подключено к {SERIAL_PORT}")
except Exception as e:
    print(f"❌ Не удалось открыть порт: {e}")
    ui.close()
    exit(1)

print("🎮 Диагональное управление активировано. Нажмите Ctrl+C для выхода...\n")

# Коды клавиш
key_map = {
    'w': e.KEY_W,
    'a': e.KEY_A,
    's': e.KEY_S,
    'd': e.KEY_D,
    ' ': e.KEY_SPACE
}

# Текущее состояние: какие клавиши нажаты
active_keys = set()

def press_key(key_char):
    """Нажимает клавишу, если ещё не нажата"""
    if key_char not in active_keys:
        key_code = key_map.get(key_char.lower())
        if key_code:
            ui.write(e.EV_KEY, key_code, 1)
            ui.syn()
            active_keys.add(key_char)
            print(f"⌨️  Нажата: {key_char.upper()}")

def release_key(key_char):
    """Отпускает клавишу, если была нажата"""
    if key_char in active_keys:
        key_code = key_map.get(key_char.lower())
        if key_code:
            ui.write(e.EV_KEY, key_code, 0)
            ui.syn()
            active_keys.remove(key_char)
            print(f"⌨️  Отпущена: {key_char.upper()}")

try:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            # Формируем набор целевых клавиш (например, "wa" → ['w', 'a'])
            target_keys = set()
            if line != "." and len(line) > 0:
                for char in line.lower():
                    if char in key_map:
                        target_keys.add(char)

        else:
            target_keys = set()

        # === Логика диагоналей ===

        # 1. Отпускаем клавиши, которых нет в новой комбинации
        for key in list(active_keys):
            if key not in target_keys:
                release_key(key)

        # 2. Нажимаем новые клавиши
        for key in target_keys:
            if key not in active_keys:
                press_key(key)

        time.sleep(KEY_DELAY)

except KeyboardInterrupt:
    print("\n🛑 Остановлено пользователем.")

except Exception as e:
    print(f"💥 Ошибка: {e}")

finally:
    # Отпускаем все клавиши
    for key in list(active_keys):
        release_key(key)
    ui.close()
    print("🔌 Виртуальная клавиатура отключена.")
