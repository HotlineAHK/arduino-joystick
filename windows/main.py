import sys
import time
import serial
import serial.tools.list_ports
import ctypes
from datetime import datetime

# === НАСТРОЙКИ ===
BAUD_RATE = 115200
KEY_DELAY = 0.005  # КРИТИЧЕСКО ВАЖНО: 5 мс вместо 20
# ----------------

# Windows API константы
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
MAPVK_VK_TO_VSC = 0x00

# Сопоставление клавиш с виртуальными кодами Windows
VK_CODES = {
    'w': 0x57,  # 'W'
    'a': 0x41,  # 'A'
    's': 0x53,  # 'S'
    'd': 0x44,  # 'D'
    ' ': 0x20   # Пробел
}

# Функция для отправки нажатий напрямую через Windows API
def send_key(vk_code, is_down):
    scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)
    flags = 0
    if not is_down:
        flags |= KEYEVENTF_KEYUP
    ctypes.windll.user32.keybd_event(vk_code, scan_code, flags, 0)

def find_arduino_port():
    """Умное определение порта через сравнение до/после подключения"""
    print("\n🔍 Поиск порта Arduino через сравнение устройств")
    
    # Получаем список портов ДО любых действий
    ports_initial = [p.device for p in serial.tools.list_ports.comports()]
    print(f"   • Найдено устройств изначально: {len(ports_initial)}")
    
    # Проверяем, подключена ли Arduino
    if ports_initial:
        print("\n⚠️ Arduino обнаружена в списке устройств:")
        for i, port in enumerate(ports_initial, 1):
            print(f"   {i}. {port}")
        
        print("\n1. Отключите Arduino от компьютера")
        input("   → Нажмите Enter, когда отключите...")
        
        # Ждём стабилизации
        time.sleep(2)
        ports_after_disconnect = [p.device for p in serial.tools.list_ports.comports()]
        
        # Определяем, какое устройство исчезло
        disconnected = list(set(ports_initial) - set(ports_after_disconnect))
        
        if disconnected:
            print(f"\n✅ Устройство отключено: {disconnected[0]}")
            print("2. Подключите Arduino к компьютеру")
            input("   → Нажмите Enter, когда подключите...")
            
            # Ждём стабилизации
            time.sleep(2)
            ports_after_connect = [p.device for p in serial.tools.list_ports.comports()]
            
            # Определяем, какое устройство появилось
            connected = list(set(ports_after_connect) - set(ports_after_disconnect))
            
            if connected:
                print(f"\n✅ Arduino найдена на порту: {connected[0]}")
                return connected[0]
    
    # Альтернативный режим поиска
    print("\n🔄 Альтернативный режим поиска...")
    print("1. Отключите Arduino от компьютера (если подключена)")
    input("   → Нажмите Enter, когда отключите...")
    
    # Список портов ДО подключения
    ports_before = [p.device for p in serial.tools.list_ports.comports()]
    print(f"   • Устройств без Arduino: {len(ports_before)}")
    
    print("\n2. Подключите Arduino к компьютеру")
    input("   → Нажмите Enter, когда подключите...")
    
    # Список портов ПОСЛЕ подключения
    time.sleep(2)
    ports_after = [p.device for p in serial.tools.list_ports.comports()]
    
    # Находим новый порт
    new_ports = list(set(ports_after) - set(ports_before))
    
    if not new_ports:
        print("\n❌ Arduino не обнаружена!")
        return None
        
    elif len(new_ports) == 1:
        print(f"\n✅ Arduino найдена на порту: {new_ports[0]}")
        return new_ports[0]
        
    else:
        print("\n⚠️ Найдено несколько новых устройств:")
        for i, port in enumerate(new_ports, 1):
            print(f"   {i}. {port}")
        
        print("\nДоступные порты:")
        for i, port in enumerate(new_ports, 1):
            print(f"   {i}. {port}")
            
        while True:
            try:
                choice = int(input("Введите номер порта Arduino: "))
                if 1 <= choice <= len(new_ports):
                    print(f"\n✅ Выбран порт: {new_ports[choice-1]}")
                    return new_ports[choice-1]
                else:
                    print(f"❌ Нет порта с номером {choice}")
            except ValueError:
                print("❌ Введите число")

def main():
    print("="*50)
    print("🎮 Сверхбыстрый джойстик для Arduino (Windows)")
    print("="*50)
    
    # Поиск порта
    port = find_arduino_port()
    if not port:
        print("❌ Не удалось определить порт Arduino")
        return
    
    # Подключение к Arduino
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
        print(f"\n🔌 Подключено к {port}")
        time.sleep(2)  # Даем время Arduino перезагрузиться
    except Exception as e:
        print(f"❌ Не удалось открыть порт: {e}")
        return
    
    print("\n🎮 Запуск с минимальной задержкой...")
    print("Нажмите Ctrl+C для выхода\n")
    
    # Текущее состояние клавиш
    active_keys = set()
    
    try:
        while True:
            # Чтение данных без блокировки
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Формируем целевые клавиши
                target_keys = set()
                if line != "." and len(line) > 0:
                    for char in line.lower():
                        if char in VK_CODES:
                            target_keys.add(char)
            
            else:
                target_keys = set()
            
            # Отпускаем ненужные клавиши
            for key in list(active_keys):
                if key not in target_keys:
                    send_key(VK_CODES[key], False)
                    active_keys.remove(key)
            
            # Нажимаем новые клавиши
            for key in target_keys:
                if key not in active_keys:
                    send_key(VK_CODES[key], True)
                    active_keys.add(key)
            
            # КРИТИЧЕСКИ ВАЖНО: минимальная задержка
            time.sleep(KEY_DELAY)
    
    except KeyboardInterrupt:
        print("\n🛑 Остановлено пользователем.")
    
    finally:
        # Отпускаем все клавиши
        for key in active_keys:
            send_key(VK_CODES[key], False)
        print("🔌 Все клавиши отпущены.")

if __name__ == "__main__":
    main()
