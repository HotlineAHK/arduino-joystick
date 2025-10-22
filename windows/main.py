import sys
import time
import serial
import serial.tools.list_ports
import ctypes
from datetime import datetime

# === НАСТРОЙКИ ===
BAUD_RATE = 115200
KEY_DELAY = 0.005  # 5 мс — минимальная задержка для плавности
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

# Функция для отправки события клавиши через Windows API
def send_key(vk_code, is_down):
    scan_code = ctypes.windll.user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)
    flags = KEYEVENTF_KEYUP if not is_down else 0
    ctypes.windll.user32.keybd_event(vk_code, scan_code, flags, 0)

def find_arduino_port():
    """Умное определение порта Arduino через сравнение подключений"""
    print("\n🔍 Поиск порта Arduino через сравнение устройств")

    # Исходный список портов
    ports_initial = [p.device for p in serial.tools.list_ports.comports()]
    print(f"   • Изначально найдено устройств: {len(ports_initial)}")
    
    if ports_initial:
        print("\n⚠️ Обнаружены устройства:")
        for i, port in enumerate(ports_initial, 1):
            print(f"   {i}. {port}")
        
        print("\n1. Отключите Arduino и нажмите Enter...")
        input("   → ")
        time.sleep(2)

        ports_after_disconnect = [p.device for p in serial.tools.list_ports.comports()]
        disconnected = set(ports_initial) - set(ports_after_disconnect)

        print("\n2. Подключите Arduino и нажмите Enter...")
        input("   → ")
        time.sleep(2)

        ports_after_connect = [p.device for p in serial.tools.list_ports.comports()]
        connected = set(ports_after_connect) - set(ports_after_disconnect)

        if connected:
            print(f"\n✅ Arduino найдена на порту: {list(connected)[0]}")
            return list(connected)[0]
        else:
            print("\n❌ Не удалось обнаружить новое устройство после подключения.")
    
    # Альтернативный режим: до/после подключения
    print("\n🔄 Альтернативный режим поиска...")
    print("1. Убедитесь, что Arduino отключена, и нажмите Enter...")
    input("   → ")
    time.sleep(1)
    ports_before = [p.device for p in serial.tools.list_ports.comports()]

    print("\n2. Подключите Arduino и нажмите Enter...")
    input("   → ")
    time.sleep(2)
    ports_after = [p.device for p in serial.tools.list_ports.comports()]

    new_ports = set(ports_after) - set(ports_before)
    if not new_ports:
        print("\n❌ Arduino не обнаружена.")
        return None
    elif len(new_ports) == 1:
        port = list(new_ports)[0]
        print(f"\n✅ Arduino найдена: {port}")
        return port
    else:
        print("\n⚠️ Найдено несколько новых устройств:")
        for i, p in enumerate(new_ports, 1):
            print(f"   {i}. {p}")
        while True:
            try:
                choice = int(input("Выберите номер порта: "))
                port_list = list(new_ports)
                if 1 <= choice <= len(port_list):
                    return port_list[choice - 1]
                else:
                    print("❌ Неверный номер.")
            except ValueError:
                print("❌ Введите число.")

def main():
    print("="*50)
    print("🎮 Джойстик Arduino → Клавиатура (Windows)")
    print("   Режим: точное управление зажатием клавиш")
    print("="*50)

    port = find_arduino_port()
    if not port:
        print("❌ Не удалось найти порт Arduino.")
        return

    # Подключение к Arduino
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
        print(f"\n🔌 Подключено к {port} @ {BAUD_RATE} baud")
        time.sleep(2)  # Время на перезагрузку Arduino
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return

    print("\n🎮 Готов к работе. Используйте джойстик.")
    print("ℹ️  Центр — ничего не нажато. Отклонение — движение.")
    print("🛑 Нажмите Ctrl+C для выхода.\n")

    active_keys = set()  # Множество зажатых клавиш

    try:
        while True:
            # Чтение строки из Arduino
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                except:
                    line = ""
                
                # Парсим активные клавиши
                current_keys = set()
                if line and line != ".":
                    for char in line.lower():
                        if char in VK_CODES:
                            current_keys.add(char)
            else:
                current_keys = set()

            # === УПРАВЛЕНИЕ ЗАЖАТИЕМ ===
            # 1. Отпустить клавиши, которые больше не активны
            for key in active_keys - current_keys:
                send_key(VK_CODES[key], False)
                print(f"📤 Отпущено: '{key.upper()}'")  # Лог (по желанию можно убрать)

            # 2. Нажать новые клавиши
            for key in current_keys - active_keys:
                send_key(VK_CODES[key], True)
                print(f"📥 Нажато: '{key.upper()}'")  # Лог (по желанию)

            # Обновляем состояние
            active_keys = current_keys

            # Минимальная задержка для стабильности
            time.sleep(KEY_DELAY)

    except KeyboardInterrupt:
        print("\n\n🛑 Остановлено пользователем.")

    except Exception as e:
        print(f"\n❌ Ошибка в основном цикле: {e}")

    finally:
        # Гарантированно отпускаем все клавиши
        for key in active_keys:
            send_key(VK_CODES[key], False)
        print("🔌 Все клавиши отпущены.")
        try:
            ser.close()
        except:
            pass
        print("🔌 Последовательный порт закрыт.")

if __name__ == "__main__":
    main()
