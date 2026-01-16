#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск графического интерфейса ROI Assistant
"""

import sys
import os
import traceback
import logging
import time


def exception_hook(exctype, value, traceback_obj):
    """Функция для перехвата необработанных исключений"""
    # Выводим полный traceback
    print("\n" + "="*60)
    print("ПРОИЗОШЛА ОШИБКА:")
    print("="*60)
    traceback.print_exception(exctype, value, traceback_obj)
    print("="*60 + "\n")
    
    # Вызываем стандартный обработчик
    sys.__excepthook__(exctype, value, traceback_obj)

# Устанавливаем наш обработчик
sys.excepthook = exception_hook


# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    # Проверяем зависимости
    try:
        from PyQt5.QtWidgets import QApplication
        import sqlite3
    except ImportError as e:
        print(f"Ошибка: {e}")
        print("\nУстановите необходимые библиотеки:")
        print("pip install PyQt5==5.12.3")
        input("\nНажмите Enter для выхода...")
        return
    
    # Проверяем базу данных
    if not os.path.exists('data/roi.db'):
        print("База данных не найдена!")
        print("Сначала запустите main.py и добавьте тестовые данные.")
        input("\nНажмите Enter для выхода...")
        return
    
    # Запускаем GUI
    from gui.main_window import main as gui_main
    gui_main()

if __name__ == "__main__":
    main()