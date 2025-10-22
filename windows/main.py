#!/usr/bin/env python3
import sys
import os
import time
import json
import serial
import serial.tools.list_ports
import platform
import re
from datetime import datetime
from pynput.keyboard import Controller, Key
import keyboard  # Для проверки состояния клавиш

class JoystickManager:
    def __init__(self):
        self.os_name = platform.system()
        self.port = None
        self.ser = None

    def get_serial_ports(self):
        """Возвращает список всех последовательных портов"""
        return [p.device for p in serial.tools.list_ports.comports()]

    def find_arduino_port(self):
        """Умное определение порта через сравнение до/после подключения"""
        print("\n🔍 Поиск порта Arduino через сравнение устройств")
        
        # Шаг 1: Получаем список портов ДО любых действий
        ports_initial = self.get_serial_ports()
        print(f"   • Найдено устройств изначально: {len(ports_initial)}")
        
        # Шаг 2: Проверяем, подключена ли Arduino
        if ports_initial:
            print("\n⚠️ Arduino обнаружена в списке устройств:")
            for i, port in enumerate(ports_initial, 1):
                print(f"   {i}. {port}")
            
            print("\n1. Отключите Arduino от компьютера")
            input("   → Нажмите Enter, когда отключите...")
            
            # Ждём стабилизации
            time.sleep(2)
            ports_after_disconnect = self.get_serial_ports()
            
            # Определяем, какое устройство исчезло
            disconnected = list(set(ports_initial) - set(ports_after_disconnect))
            
            if disconnected:
                print(f"\n✅ Устройство отключено: {disconnected[0]}")
                print("2. Подключите Arduino к компьютеру")
                input("   → Нажмите Enter, когда подключите...")
                
                # Ждём стабилизации
                time.sleep(2)
                ports_after_connect = self.get_serial_ports()
                
                # Определяем, какое устройство появилось
                connected = list(set(ports_after_connect) - set(ports_after_disconnect))
                
                if connected:
                    self.port = connected[0]
                    print(f"\n✅ Arduino найдена на порту: {self.port}")
                    return self.port
            
            print("\n❌ Не удалось определить Arduino через отключение/подключение")
        
        # Шаг 3: Если не было изначально или не сработало
        print("\n🔄 Альтернативный режим поиска...")
        print("1. Отключите Arduino от компьютера (если подключена)")
        input("   → Нажмите Enter, когда отключите...")
        
        # Список портов ДО подключения
        ports_before = self.get_serial_ports()
        print(f"   • Устройств без Arduino: {len(ports_before)}")
        
        print("\n2. Подключите Arduino к компьютеру")
        input("   → Нажмите Enter, когда подключите...")
        
        # Список портов ПОСЛЕ подключения
        time.sleep(2)  # Даем время для определения
        ports_after = self.get_serial_ports()
        
        # Находим новый порт
        new_ports = list(set(ports_after) - set(ports_before))
        
        if not new_ports:
            print("\n❌ Arduino не обнаружена!")
            print("💡 Проверьте:")
            print("   • Кабель подключен правильно")
            print("   • Драйверы установлены (особенно для CH340/CH341)")
            print("   • Плата включена")
            return self.manual_port_selection()
            
        elif len(new_ports) == 1:
            self.port = new_ports[0]
            print(f"\n✅ Arduino найдена на порту: {self.port}")
            return self.port
            
        else:
            print("\n⚠️ Найдено несколько новых устройств:")
            for i, port in enumerate(new_ports, 1):
                print(f"   {i}. {port}")
            return self.manual_port_selection(new_ports)

    def manual_port_selection(self, ports=None):
        """Ручной выбор порта"""
        if ports is None:
            ports = self.get_serial_ports()
            
        if not ports:
            print("\n❌ Нет доступных последовательных портов")
            return None
            
        print("\nДоступные порты:")
        for i, port in enumerate(ports, 1):
            print(f"   {i}. {port}")
            
        while True:
            try:
                choice = int(input("Введите номер порта Arduino: "))
                if 1 <= choice <= len(ports):
                    self.port = ports[choice-1]
                    print(f"\n✅ Выбран порт: {self.port}")
                    return self.port
                else:
                    print(f"❌ Нет порта с номером {choice}")
            except ValueError:
                print("❌ Введите число")

def main():
    print("="*50)
    print("🎮 Универсальный джойстик для Arduino (Windows)")
    print("="*50)
    
    # Проверяем, установлены ли зависимости
    try:
        import pynput
        print("✅ pynput установлен")
    except ImportError:
        print("❌ pynput не установлен!")
        print("💡 Выполни: pip install pynput")
        return
    
    # Инициализируем менеджер
    joymgr = JoystickManager()
    
    # Ищем порт Arduino
    port = joymgr.find_arduino_port()
    if not port:
        print("❌ Не удалось определить порт Arduino")
        return
    
    SERIAL_PORT = port
    BAUD_RATE = 115200
    KEY_DELAY = 0.020  # Высокая частота обработки
    
    print(f"\n🔌 Подключаемся к {SERIAL_PORT} @ {BAUD_RATE} бод")
    
    # Подключаемся к Arduino
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("✅ Подключение установлено")
        time.sleep(2)  # Даем время Arduino перезагрузиться
    except Exception as e:
        print(f"❌ Не удалось открыть порт: {e}")
        print("💡 Проверьте драйверы и подключение")
        return
    
    print("\n🎮 Диагональное управление активировано. Нажмите Ctrl+C для выхода...\n")
    
    # Создаем контроллер клавиатуры
    keyboard_controller = Controller()
    
    # Коды клавиш
    key_map = {
        'w': 'w',
        'a': 'a',
        's': 's',
        'd': 'd',
        ' ': Key.space
    }
    
    # Текущее состояние: какие клавиши нажаты
    active_keys = set()
    
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
                    # Проверяем, не нажата ли клавиша другим способом
                    if key != ' ' and not keyboard.is_pressed(key):
                        keyboard_controller.release(key_map[key])
                        print(f"⌨️  Отпущена: {key.upper()}")
                    active_keys.remove(key)
    
            # 2. Нажимаем новые клавиши
            for key in target_keys:
                if key not in active_keys:
                    keyboard_controller.press(key_map[key])
                    active_keys.add(key)
                    print(f"⌨️  Нажата: {key.upper()}")
    
            time.sleep(KEY_DELAY)
    
    except KeyboardInterrupt:
        print("\n🛑 Остановлено пользователем.")
    
    except Exception as e:
        print(f"💥 Ошибка: {e}")
    
    finally:
        # Отпускаем все клавиши
        for key in list(active_keys):
            try:
                keyboard_controller.release(key_map[key])
                print(f"⌨️  Отпущена: {key.upper()}")
            except:
                pass
        print("🔌 Все клавиши отпущены.")

if __name__ == "__main__":
    main()
