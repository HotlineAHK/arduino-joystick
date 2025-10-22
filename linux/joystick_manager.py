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
            return False
            
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