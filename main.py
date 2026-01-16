#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI Assistant - Программа для работы с roi.ru
"""

import sys
import os
import sqlite3
from datetime import datetime

class ROIAssistant:
    def fetch_federal_initiatives(self):
        """Получение федеральных инициатив с roi.ru"""
        print("\n" + "=" * 60)
        print("ЗАГРУЗКА ФЕДЕРАЛЬНЫХ ИНИЦИАТИВ С ROI.RU")
        print("=" * 60)
        
        try:
            from browser.roi_parser import ROIParser
            
            parser = ROIParser()
            print("Парсинг федеральных инициатив...")
            print("(Это может занять некоторое время)")
            print("-" * 40)
            
            # Получаем инициативы (только первую страницу для теста)
            initiatives = parser.parse_federal_initiatives(max_pages=1)
            
            if not initiatives:
                print("Не удалось получить инициативы.")
                print("Проверьте интернет-соединение или структуру сайта.")
                input("\nНажмите Enter для продолжения...")
                return
            
            print(f"Получено инициатив: {len(initiatives)}")
            
            added_count = 0
            duplicate_count = 0
            
            for i, initiative in enumerate(initiatives, 1):
                # Проверяем, есть ли уже такая инициатива
                self.cursor.execute(
                    "SELECT id FROM initiatives WHERE external_id = ? OR url = ?",
                    (initiative['external_id'], initiative['url'])
                )
                
                if not self.cursor.fetchone():
                    # Добавляем новую инициативу
                    self.cursor.execute('''
                        INSERT INTO initiatives 
                        (external_id, title, description, url, category, 
                         created_date, status, level, votes, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        initiative['external_id'],
                        initiative['title'],
                        initiative.get('description', ''),
                        initiative['url'],
                        initiative.get('category', 'Федеральные'),
                        initiative.get('created_date', datetime.now().strftime('%Y-%m-%d')),
                        'new',
                        initiative.get('level', 'Федеральный'),
                        initiative.get('votes', '0'),
                        initiative.get('source', 'roi.ru')
                    ))
                    added_count += 1
                    print(f"✓ [{i}] Добавлена: {initiative['title'][:60]}...")
                else:
                    duplicate_count += 1
                    print(f"  [{i}] Уже есть: {initiative['title'][:60]}...")
            
            self.conn.commit()
            
            # Сохраняем также в JSON для резервной копии
            import json
            import os
            os.makedirs('exports', exist_ok=True)
            json_file = f"exports/federal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(initiatives, f, ensure_ascii=False, indent=2)
            
            print(f"\n{'='*60}")
            print("ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
            print(f"{'='*60}")
            print(f"Добавлено новых: {added_count}")
            print(f"Пропущено (уже есть): {duplicate_count}")
            print(f"Всего в базе: {self.cursor.execute('SELECT COUNT(*) FROM initiatives').fetchone()[0]}")
            print(f"JSON сохранен: {json_file}")
            
            # Логируем действие
            self.cursor.execute(
                "INSERT INTO logs (level, message) VALUES (?, ?)",
                ('INFO', f'Загрузка федеральных инициатив: добавлено {added_count}, дубликатов {duplicate_count}')
            )
            self.conn.commit()
            
        except ImportError:
            print("✗ Модуль парсера не найден. Убедитесь что файл browser/roi_parser.py существует")
        except Exception as e:
            print(f"✗ Ошибка загрузки: {e}")
            import traceback
            traceback.print_exc()
        
    input("\nНажмите Enter для продолжения...")



    def update_from_roi(self):
        """Обновление данных с сайта roi.ru"""
        print("\n" + "=" * 60)
        print("ОБНОВЛЕНИЕ С ROI.RU")
        print("=" * 60)
        
        try:
            from browser.roi_parser import ROIParser
            
            parser = ROIParser()
            print("Парсинг сайта roi.ru...")
            
            initiatives = parser.parse_initiatives_list()
            
            if not initiatives:
                print("Не удалось получить инициативы. Используем тестовые данные.")
                initiatives = parser._get_test_initiatives()
            
            added_count = 0
            for initiative in initiatives:
                # Проверяем, есть ли уже такая инициатива
                self.cursor.execute(
                    "SELECT id FROM initiatives WHERE external_id = ? OR url = ?",
                    (initiative['external_id'], initiative['url'])
                )
                
                if not self.cursor.fetchone():
                    # Добавляем новую инициативу
                    self.cursor.execute('''
                        INSERT INTO initiatives 
                        (external_id, title, description, url, category, created_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        initiative['external_id'],
                        initiative['title'],
                        initiative['description'],
                        initiative['url'],
                        initiative['category'],
                        initiative['created_date'],
                        'new'
                    ))
                    added_count += 1
                    print(f"✓ Добавлена: {initiative['title'][:50]}...")
            
            self.conn.commit()
            
            print(f"\nОбновление завершено!")
            print(f"Добавлено новых инициатив: {added_count}")
            print(f"Всего в базе: {self.cursor.execute('SELECT COUNT(*) FROM initiatives').fetchone()[0]}")
            
            # Логируем действие
            self.cursor.execute(
                "INSERT INTO logs (level, message) VALUES (?, ?)",
                ('INFO', f'Обновление с ROI.ru: добавлено {added_count} инициатив')
            )
            self.conn.commit()
            
        except ImportError:
            print("✗ Модуль парсера не найден. Убедитесь что файл browser/roi_parser.py существует")
        except Exception as e:
            print(f"✗ Ошибка обновления: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nНажмите Enter для продолжения...")

    def __init__(self):
        print("=" * 60)
        print("ROI Assistant - Инициализация")
        print("=" * 60)
        
        # Создаем структуру папок
        self.create_folders()
        
        # СОЕДИНЕНИЕ С БД ДОЛЖНО БЫТЬ ЗДЕСЬ
        self.conn = sqlite3.connect('data/roi.db')
        self.cursor = self.conn.cursor()

        # Инициализируем базу данных
        self.init_database()
        
        # Тест библиотек
        self.test_libraries()
        
    def create_folders(self):
        """Создание структуры папок проекта"""
        folders = ['data', 'logs', 'exports', 'screenshots']
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"✓ Создана папка: {folder}")
    
    def init_database(self):
        """Инициализация базы данных"""
        try:
            # self.conn = sqlite3.connect('data/roi.db')
            # self.cursor = self.conn.cursor()
                        
            # Таблица инициатив
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS initiatives (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        external_id TEXT UNIQUE,
                        title TEXT NOT NULL,
                        description TEXT,
                        url TEXT,
                        category TEXT,
                        level TEXT DEFAULT 'Федеральный',
                        votes TEXT DEFAULT '0',
                        anti_votes TEXT DEFAULT '0',
                        status TEXT DEFAULT 'new',
                        vote TEXT,
                        vote_date TEXT,
                        source TEXT DEFAULT 'roi.ru',
                        full_text TEXT,
                        proposal_text TEXT,
                        result_text TEXT,
                        end_date TEXT,
                        combined_text TEXT,
                        author TEXT,
                        initiative_status TEXT,
                        created_date TEXT,  
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            # ПРОВЕРКА: какие таблицы созданы
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = self.cursor.fetchall()
                print(f"Таблицы в базе: {tables}")

            # Таблица логов
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        level TEXT,
                        message TEXT,
                        details TEXT
                    )
                ''')
            
            # Таблица пользовательских настроек
                self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
            
            # Начальные настройки
                default_settings = [
                    ('check_interval', '300'),  # 5 минут
                    ('auto_vote', 'false'),
                    ('browser_type', 'firefox'),
                    ('language', 'ru')
                ]
            
                self.cursor.executemany(
                    'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                    default_settings
                )
                
                self.conn.commit()
                print("✓ База данных инициализирована")
            
            # Показываем статистику
                self.cursor.execute("SELECT COUNT(*) FROM initiatives")
                count = self.cursor.fetchone()[0]
                print(f"  Всего инициатив в базе: {count}")
            
        except Exception as e:
            print(f"✗ Ошибка инициализации БД: {e}")
            import traceback
            traceback.print_exc()  # ← Добавьте эту строку
    
    def __del__(self):
        """Деструктор - закрываем соединение с БД"""
        if hasattr(self, 'conn'):
            self.conn.close()
            
    def test_libraries(self):
        """Тест установленных библиотек"""
        print("\nПроверка библиотек:")
        print("-" * 40)
        
        libraries = [
            ('sqlite3', 'Встроена в Python'),
            ('requests', 'Для HTTP запросов'),
            ('BeautifulSoup', 'Для парсинга HTML'),
            ('PyQt5', 'Для графического интерфейса'),
            ('selenium', 'Для автоматизации браузера')
        ]
        
        for lib_name, description in libraries:
            try:
                if lib_name == 'sqlite3':
                    import sqlite3
                    status = "✓"
                elif lib_name == 'requests':
                    import requests
                    status = "✓"
                elif lib_name == 'BeautifulSoup':
                    from bs4 import BeautifulSoup
                    status = "✓"
                elif lib_name == 'PyQt5':
                    from PyQt5.QtCore import Qt
                    status = "✓"
                elif lib_name == 'selenium':
                    from selenium import webdriver
                    status = "✓"
                print(f"{status} {lib_name:20} - {description}")
            except ImportError:
                print(f"✗ {lib_name:20} - НЕ УСТАНОВЛЕНА")
    
    def add_sample_data(self):
        """Добавление тестовых данных"""
        try:
            # ПРОВЕРКА: существует ли таблица
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='initiatives'")
            if not self.cursor.fetchone():
                print("✗ Таблица 'initiatives' не найдена!")
                print("Создаю таблицу...")
                # Создаем таблицу здесь же
                self.cursor.execute('''
                    CREATE TABLE initiatives (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        external_id TEXT UNIQUE,
                        title TEXT NOT NULL,
                        description TEXT,
                        url TEXT,
                        category TEXT,
                        created_date TEXT
                    )
                ''')
                self.conn.commit()
                print("✓ Таблица создана")

            sample_initiatives = [
                {
                    'external_id': 'test_001',
                    'title': 'Введение цифровых пропусков для посещения общественных мест',
                    'description': 'Предлагается внедрить систему цифровых пропусков для контроля посещения общественных мест в период эпидемий.',
                    'category': 'Здравоохранение',
                    'url': 'https://roi.ru/test1'
                },
                {
                    'external_id': 'test_002',
                    'title': 'Снижение НДС для малого бизнеса до 10%',
                    'description': 'Снижение налога на добавленную стоимость для предприятий малого бизнеса с целью поддержки предпринимательства.',
                    'category': 'Экономика',
                    'url': 'https://roi.ru/test2'
                },
                {
                    'external_id': 'test_003',
                    'title': 'Бесплатный Wi-Fi в общественном транспорте',
                    'description': 'Организация точек бесплатного беспроводного интернета в общественном транспорте крупных городов.',
                    'category': 'Транспорт',
                    'url': 'https://roi.ru/test3'
                }
            ]
            
            for initiative in sample_initiatives:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO initiatives 
                    (external_id, title, description, category, url, created_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    initiative['external_id'],
                    initiative['title'],
                    initiative['description'],
                    initiative['category'],
                    initiative['url'],
                    datetime.now().strftime('%Y-%m-%d'),
                    'new'
                ))
            
            self.conn.commit()
            print(f"\n✓ Добавлено {len(sample_initiatives)} тестовых инициатив")
            
        except Exception as e:
            print(f"✗ Ошибка добавления тестовых данных: {e}")
            import traceback
            traceback.print_exc()  # ← Добавьте эту строку
    
    def show_statistics(self):
        """Показать статистику"""
        print("\nСтатистика:")
        print("-" * 40)
        
        queries = [
            ("Всего инициатив:", "SELECT COUNT(*) FROM initiatives"),
            ("Новых для голосования:", "SELECT COUNT(*) FROM initiatives WHERE status = 'new'"),
            ("Уже проголосовано:", "SELECT COUNT(*) FROM initiatives WHERE status = 'voted'"),
            ("Игнорировано:", "SELECT COUNT(*) FROM initiatives WHERE status = 'ignored'"),
            ("За последние 7 дней:", "SELECT COUNT(*) FROM initiatives WHERE date(added_date) > date('now', '-7 days')")
        ]
        
        for label, query in queries:
            self.cursor.execute(query)
            count = self.cursor.fetchone()[0]
            print(f"{label:25} {count}")
    
    def show_recent_initiatives(self):
        """Показать последние инициативы"""
        print("\nПоследние инициативы:")
        print("-" * 60)
        
        self.cursor.execute('''
            SELECT id, title, status, added_date 
            FROM initiatives 
            ORDER BY added_date DESC 
            LIMIT 5
        ''')
        
        initiatives = self.cursor.fetchall()
        
        if not initiatives:
            print("Нет инициатив в базе данных")
            return
        
        for init in initiatives:
            status_icons = {
                'new': '🆕',
                'voted': '✅',
                'ignored': '🚫'
            }
            status_icon = status_icons.get(init[2], '❓')
            print(f"{status_icon} [{init[0]}] {init[1][:50]}...")
            print(f"    Добавлено: {init[3]}")
    
    def run(self):
        """Основной цикл программы"""
        print("\n" + "=" * 60)
        print("ROI ASSISTANT - ГЛАВНОЕ МЕНЮ")
        print("=" * 60)
        
        while True:
            print("\nВыберите действие:")
            print("1. Добавить тестовые данные")
            print("2. Показать статистику")
            print("3. Показать последние инициативы")
            print("4. Экспорт инициатив в CSV")
            print("5. Очистить базу данных")
            print("6. Обновить с сайта roi.ru")
            print("7. Запустить графический интерфейс")
            print("8. Настройки базы данных")
            print("0. Выход")
            
            choice = input("\nВаш выбор: ").strip()
            
            if choice == '1':
                self.add_sample_data()
            elif choice == '2':
                self.show_statistics()
            elif choice == '3':
                self.show_recent_initiatives()
            elif choice == '4':
                self.export_to_csv()
            elif choice == '5':
                self.clear_database()
            elif choice == '6':
                self.fetch_federal_initiatives()  # Изменено название
            elif choice == '7':
                self.launch_gui()
            elif choice == '8':
                self.database_settings()
            elif choice == '0':
                print("\nДо свидания!")
                break
            else:
                print("Неверный выбор, попробуйте снова.")

    def database_settings(self):
        """Настройки базы данных"""
        print("\n" + "=" * 60)
        print("НАСТРОЙКИ БАЗЫ ДАННЫХ")
        print("=" * 60)
        
        print("\nТекущая база данных: data/roi.db")
        print(f"Размер файла: {os.path.getsize('data/roi.db') / 1024:.1f} KB")
        
        self.cursor.execute("PRAGMA database_list")
        dbs = self.cursor.fetchall()
        print(f"Подключенные базы: {len(dbs)}")
        
        print("\nДействия:")
        print("1. Оптимизировать базу данных")
        print("2. Создать резервную копию")
        print("3. Проверить целостность")
        print("4. Вернуться в меню")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == '1':
            self.cursor.execute("VACUUM")
            self.conn.commit()
            print("✓ База данных оптимизирована")
        elif choice == '2':
            import shutil
            import datetime
            backup_name = f"data/roi_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2('data/roi.db', backup_name)
            print(f"✓ Резервная копия создана: {backup_name}")
        elif choice == '3':
            self.cursor.execute("PRAGMA integrity_check")
            result = self.cursor.fetchone()
            print(f"✓ Проверка целостности: {result[0]}")
        
        input("\nНажмите Enter для продолжения...")
    
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        try:
            import csv
            from datetime import datetime
            
            filename = f"exports/initiatives_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            self.cursor.execute('''
                SELECT id, title, description, category, status, vote, added_date
                FROM initiatives
                ORDER BY added_date DESC
            ''')
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                # Заголовки
                writer.writerow(['ID', 'Название', 'Описание', 'Категория', 'Статус', 'Голос', 'Дата добавления'])
                # Данные
                for row in self.cursor.fetchall():
                    writer.writerow(row)
            
            print(f"✓ Данные экспортированы в {filename}")
            
        except Exception as e:
            print(f"✗ Ошибка экспорта: {e}")
    
    def clear_database(self):
        """Очистка базы данных"""
        confirm = input("\n⚠️  ВНИМАНИЕ: Вы уверены что хотите очистить ВСЮ базу данных? (да/НЕТ): ")
        if confirm.lower() == 'да':
            self.cursor.execute("DELETE FROM initiatives")
            self.cursor.execute("DELETE FROM logs")
            self.conn.commit()
            print("✓ База данных очищена")
    
    def launch_gui(self):
        """Запуск графического интерфейса"""
        print("\nЗапуск графического интерфейса...")
        print("(Для возврата в консоль закройте окно GUI)")
        
        try:
            import sys
            from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
            from PyQt5.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
            from PyQt5.QtWidgets import QComboBox, QLineEdit, QTextEdit, QMessageBox, QStatusBar
            from PyQt5.QtCore import Qt, QTimer
            from PyQt5.QtGui import QFont, QColor
            
            class ROI_GUI(QMainWindow):
                def __init__(self, db_conn):
                    super().__init__()
                    self.db_conn = db_conn
                    self.initUI()
                    self.load_data()
                    
                    # Автообновление каждые 30 секунд
                    self.timer = QTimer()
                    self.timer.timeout.connect(self.load_data)
                    self.timer.start(30000)  # 30 секунд
                
                def initUI(self):
                    # Настройка главного окна
                    self.setWindowTitle('ROI Assistant - Федеральные инициативы')
                    self.setGeometry(50, 50, 1400, 800)  # Большое окно
                    
                    # Центральный виджет
                    central_widget = QWidget()
                    self.setCentralWidget(central_widget)
                    
                    main_layout = QVBoxLayout()
                    central_widget.setLayout(main_layout)
                    
                    # 1. Верхняя панель с заголовком и кнопками
                    top_panel = QWidget()
                    top_layout = QHBoxLayout()
                    
                    # Заголовок
                    title = QLabel('📋 ROI Assistant - Федеральные инициативы')
                    title_font = QFont()
                    title_font.setPointSize(16)
                    title_font.setBold(True)
                    title.setFont(title_font)
                    title.setStyleSheet("color: #2c3e50; padding: 10px;")
                    top_layout.addWidget(title)
                    
                    top_layout.addStretch()
                    
                    # Кнопки управления
                    btn_refresh = QPushButton('🔄 Обновить')
                    btn_refresh.setStyleSheet("""
                        QPushButton {
                            background-color: #3498db;
                            color: white;
                            padding: 8px 15px;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #2980b9;
                        }
                    """)
                    btn_refresh.clicked.connect(self.load_data)
                    
                    btn_export = QPushButton('📊 Экспорт CSV')
                    btn_export.setStyleSheet("""
                        QPushButton {
                            background-color: #27ae60;
                            color: white;
                            padding: 8px 15px;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #229954;
                        }
                    """)
                    btn_export.clicked.connect(self.export_csv)
                    
                    btn_stats = QPushButton('📈 Статистика')
                    btn_stats.setStyleSheet("""
                        QPushButton {
                            background-color: #8e44ad;
                            color: white;
                            padding: 8px 15px;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #7d3c98;
                        }
                    """)
                    btn_stats.clicked.connect(self.show_stats)
                    
                    top_layout.addWidget(btn_refresh)
                    top_layout.addWidget(btn_export)
                    top_layout.addWidget(btn_stats)
                    
                    top_panel.setLayout(top_layout)
                    main_layout.addWidget(top_panel)
                    
                    # 2. Панель фильтров
                    filter_panel = QWidget()
                    filter_layout = QHBoxLayout()
                    
                    filter_label = QLabel('Фильтр:')
                    filter_layout.addWidget(filter_label)
                    
                    # Фильтр по статусу
                    self.status_filter = QComboBox()
                    self.status_filter.addItems(['Все', 'Новые', 'Голосованные', 'Игнорированные'])
                    self.status_filter.currentTextChanged.connect(self.apply_filters)
                    filter_layout.addWidget(self.status_filter)
                    
                    # Поиск
                    self.search_input = QLineEdit()
                    self.search_input.setPlaceholderText('Поиск по названию...')
                    self.search_input.textChanged.connect(self.apply_filters)
                    filter_layout.addWidget(self.search_input)
                    
                    filter_layout.addStretch()
                    
                    # Показано/всего
                    self.count_label = QLabel('Загружается...')
                    filter_layout.addWidget(self.count_label)
                    
                    filter_panel.setLayout(filter_layout)
                    main_layout.addWidget(filter_panel)
                    
                    # 3. Таблица с данными
                    self.table = QTableWidget()
                    self.table.setColumnCount(10)  # Увеличим количество колонок
                    self.table.setHorizontalHeaderLabels([
                        'ID', 'Название', 'Категория', 'Уровень', 'Голоса',
                        'Статус', 'Голос', 'Дата создания', 'Дата добавления', 'URL'
                    ])
                    
                    # Настройка таблицы
                    self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Название растягивается
                    self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID по содержимому
                    self.table.setAlternatingRowColors(True)
                    self.table.setStyleSheet("""
                        QTableWidget {
                            alternate-background-color: #f8f9fa;
                        }
                        QTableWidget::item {
                            padding: 5px;
                        }
                    """)
                    
                    # Двойной клик по строке
                    self.table.cellDoubleClicked.connect(self.show_details)
                    
                    main_layout.addWidget(self.table, 1)  # 1 = растягиваемое
                    
                    # 4. Нижняя панель с кнопками голосования
                    bottom_panel = QWidget()
                    bottom_layout = QHBoxLayout()
                    
                    btn_for = QPushButton('👍 ЗА')
                    btn_for.setStyleSheet("""
                        QPushButton {
                            background-color: #27ae60;
                            color: white;
                            padding: 12px 25px;
                            border-radius: 8px;
                            font-size: 14pt;
                            font-weight: bold;
                            margin: 5px;
                        }
                        QPushButton:hover {
                            background-color: #229954;
                        }
                        QPushButton:pressed {
                            background-color: #1e8449;
                        }
                    """)
                    btn_for.clicked.connect(lambda: self.vote_selected('for'))
                    
                    btn_against = QPushButton('👎 ПРОТИВ')
                    btn_against.setStyleSheet("""
                        QPushButton {
                            background-color: #e74c3c;
                            color: white;
                            padding: 12px 25px;
                            border-radius: 8px;
                            font-size: 14pt;
                            font-weight: bold;
                            margin: 5px;
                        }
                        QPushButton:hover {
                            background-color: #c0392b;
                        }
                        QPushButton:pressed {
                            background-color: #a93226;
                        }
                    """)
                    btn_against.clicked.connect(lambda: self.vote_selected('against'))
                    
                    btn_ignore = QPushButton('➖ ИГНОРИРОВАТЬ')
                    btn_ignore.setStyleSheet("""
                        QPushButton {
                            background-color: #95a5a6;
                            color: white;
                            padding: 12px 25px;
                            border-radius: 8px;
                            font-size: 14pt;
                            font-weight: bold;
                            margin: 5px;
                        }
                        QPushButton:hover {
                            background-color: #7f8c8d;
                        }
                        QPushButton:pressed {
                            background-color: #707b7c;
                        }
                    """)
                    btn_ignore.clicked.connect(lambda: self.vote_selected('ignore'))
                    
                    bottom_layout.addWidget(btn_for)
                    bottom_layout.addWidget(btn_against)
                    bottom_layout.addWidget(btn_ignore)
                    
                    bottom_panel.setLayout(bottom_layout)
                    main_layout.addWidget(bottom_panel)
                    
                    # Статус бар
                    self.statusBar().showMessage('Готово')
                
                def load_data(self):
                    """Загрузка данных из базы"""
                    try:
                        cursor = self.db_conn.cursor()
                        
                        # Получаем все колонки таблицы
                        cursor.execute("PRAGMA table_info(initiatives)")
                        columns_info = cursor.fetchall()
                        columns = [col[1] for col in columns_info]
                        
                        # Формируем SQL запрос с ВСЕМИ полями
                        columns_str = ', '.join(columns)
                        sql = f'''
                            SELECT {columns_str}
                            FROM initiatives 
                            ORDER BY added_date DESC
                        '''
                        
                        cursor.execute(sql)
                        data = cursor.fetchall()
                        
                        # Настраиваем таблицу
                        self.table.setColumnCount(len(columns))
                        self.table.setHorizontalHeaderLabels(columns)
                        
                        # Заполняем данные
                        self.table.setRowCount(len(data))
                        
                        for row_idx, row_data in enumerate(data):
                            for col_idx, cell_data in enumerate(row_data):
                                item = QTableWidgetItem(str(cell_data) if cell_data is not None else '')
                                
                                # Цветовые маркеры для статусов
                                if columns[col_idx] == 'status':
                                    if cell_data == 'new':
                                        item.setBackground(QColor(173, 216, 230))  # голубой
                                    elif cell_data == 'voted':
                                        item.setBackground(QColor(144, 238, 144))  # зеленый
                                    elif cell_data == 'ignored':
                                        item.setBackground(QColor(255, 182, 193))  # розовый
                                
                                # Для голосов - выделяем жирным если много
                                if columns[col_idx] == 'votes' and cell_data:
                                    try:
                                        if int(cell_data) > 1000:
                                            font = item.font()
                                            font.setBold(True)
                                            item.setFont(font)
                                            item.setForeground(QColor(0, 100, 0))  # темно-зеленый
                                    except:
                                        pass
                                
                                self.table.setItem(row_idx, col_idx, item)
                        
                        # Автоматически подгоняем ширину колонок
                        self.table.resizeColumnsToContents()
                        
                        # Обновляем счетчик
                        self.count_label.setText(f"Показано: {len(data)} записей")
                        self.statusBar().showMessage(f'Загружено записей: {len(data)}')
                        
                    except Exception as e:
                        QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить данные: {e}')
                
                def apply_filters(self):
                    """Применение фильтров"""
                    try:
                        status_filter = self.status_filter.currentText()
                        search_text = self.search_input.text().lower()
                        
                        cursor = self.db_conn.cursor()
                        
                        # Базовый запрос
                        sql = "SELECT * FROM initiatives WHERE 1=1"
                        params = []
                        
                        # Фильтр по статусу
                        if status_filter == 'Новые':
                            sql += " AND status = 'new'"
                        elif status_filter == 'Голосованные':
                            sql += " AND status = 'voted'"
                        elif status_filter == 'Игнорированные':
                            sql += " AND status = 'ignored'"
                        
                        # Поиск по тексту
                        if search_text:
                            sql += " AND LOWER(title) LIKE ?"
                            params.append(f'%{search_text}%')
                        
                        sql += " ORDER BY added_date DESC"
                        
                        cursor.execute(sql, params)
                        data = cursor.fetchall()
                        
                        # Обновляем таблицу
                        self.table.setRowCount(len(data))
                        
                        for row_idx, row_data in enumerate(data):
                            for col_idx, cell_data in enumerate(row_data):
                                self.table.setItem(row_idx, col_idx, 
                                                 QTableWidgetItem(str(cell_data) if cell_data is not None else ''))
                        
                        self.count_label.setText(f"Показано: {len(data)} записей (фильтровано)")
                        
                    except Exception as e:
                        print(f"Ошибка фильтрации: {e}")
                
                def show_details(self, row, column):
                    """Показать детали выбранной записи"""
                    try:
                        cursor = self.db_conn.cursor()
                        
                        # Получаем ID из первого столбца
                        item_id = self.table.item(row, 0).text()
                        
                        cursor.execute("SELECT * FROM initiatives WHERE id = ?", (item_id,))
                        record = cursor.fetchone()
                        
                        cursor.execute("PRAGMA table_info(initiatives)")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        # Создаем окно с деталями
                        detail_dialog = QMessageBox()
                        detail_dialog.setWindowTitle(f'Детали инициативы #{item_id}')
                        
                        # Формируем текст
                        text = ""
                        for col_name, value in zip(columns, record):
                            if value and col_name not in ['id', 'added_date']:
                                text += f"<b>{col_name}:</b> {value}<br>"
                        
                        detail_dialog.setTextFormat(Qt.RichText)
                        detail_dialog.setText(text)
                        detail_dialog.setStandardButtons(QMessageBox.Ok)
                        detail_dialog.exec_()
                        
                    except Exception as e:
                        QMessageBox.warning(self, 'Ошибка', f'Не удалось показать детали: {e}')
                
                def vote_selected(self, vote_type):
                    """Голосование за выбранную инициативу"""
                    try:
                        current_row = self.table.currentRow()
                        if current_row < 0:
                            QMessageBox.warning(self, 'Предупреждение', 'Выберите инициативу из таблицы')
                            return
                        
                        item_id = self.table.item(current_row, 0).text()
                        
                        # Обновляем в базе
                        cursor = self.db_conn.cursor()
                        cursor.execute('''
                            UPDATE initiatives 
                            SET vote = ?, status = 'voted', vote_date = datetime('now')
                            WHERE id = ?
                        ''', (vote_type, item_id))
                        self.db_conn.commit()
                        
                        # Обновляем отображение
                        status_item = self.table.item(current_row, 5)  # статус
                        vote_item = self.table.item(current_row, 6)   # голос
                        
                        if status_item:
                            status_item.setText('voted')
                            status_item.setBackground(QColor(144, 238, 144))
                        
                        if vote_item:
                            vote_text = {'for': 'За', 'against': 'Против', 'ignore': 'Игнорировать'}.get(vote_type, '')
                            vote_item.setText(vote_text)
                        
                        self.statusBar().showMessage(f'Голос сохранен: {vote_text} для инициативы #{item_id}', 3000)
                        
                    except Exception as e:
                        QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить голос: {e}')
                
                def export_csv(self):
                    """Экспорт в CSV"""
                    try:
                        from datetime import datetime
                        import csv
                        
                        filename = f"exports/gui_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        
                        cursor = self.db_conn.cursor()
                        cursor.execute("SELECT * FROM initiatives ORDER BY added_date DESC")
                        
                        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile, delimiter=';')
                            
                            # Заголовки
                            cursor.execute("PRAGMA table_info(initiatives)")
                            headers = [col[1] for col in cursor.fetchall()]
                            writer.writerow(headers)
                            
                            # Данные
                            for row in cursor.fetchall():
                                writer.writerow(row)
                        
                        QMessageBox.information(self, 'Экспорт', f'Данные экспортированы в:\n{filename}')
                        self.statusBar().showMessage(f'Экспорт завершен: {filename}', 3000)
                        
                    except Exception as e:
                        QMessageBox.critical(self, 'Ошибка', f'Не удалось экспортировать: {e}')
                
                def show_stats(self):
                    """Показать статистику"""
                    try:
                        cursor = self.db_conn.cursor()
                        
                        queries = [
                            ("Всего инициатив:", "SELECT COUNT(*) FROM initiatives"),
                            ("Новых:", "SELECT COUNT(*) FROM initiatives WHERE status = 'new'"),
                            ("Голосованных:", "SELECT COUNT(*) FROM initiatives WHERE status = 'voted'"),
                            ("Игнорированных:", "SELECT COUNT(*) FROM initiatives WHERE status = 'ignored'"),
                            ("Федеральных:", "SELECT COUNT(*) FROM initiatives WHERE level = 'Федеральный'"),
                            ("За сегодня:", "SELECT COUNT(*) FROM initiatives WHERE date(added_date) = date('now')")
                        ]
                        
                        stats_text = "<b>Статистика:</b><br><br>"
                        for label, query in queries:
                            cursor.execute(query)
                            count = cursor.fetchone()[0]
                            stats_text += f"{label} <b>{count}</b><br>"
                        
                        msg = QMessageBox()
                        msg.setWindowTitle('Статистика')
                        msg.setTextFormat(Qt.RichText)
                        msg.setText(stats_text)
                        msg.setStandardButtons(QMessageBox.Ok)
                        msg.exec_()
                        
                    except Exception as e:
                        QMessageBox.critical(self, 'Ошибка', f'Не удалось получить статистику: {e}')
                
                def closeEvent(self, event):
                    """Обработка закрытия окна"""
                    self.timer.stop()
                    event.accept()
            
            # Запускаем приложение
            app = QApplication(sys.argv)
            
            # Устанавливаем стиль
            app.setStyle('Fusion')
            
            window = ROI_GUI(self.conn)
            window.showMaximized()  # ← ВОТ ЭТО ВАЖНО: развернуть на весь экран!
            
            sys.exit(app.exec_())
            
        except ImportError as e:
            print(f"✗ Ошибка импорта PyQt5: {e}")
            print("Установите: pip install PyQt5==5.12.3")
            input("Нажмите Enter для продолжения...")
        except Exception as e:
            print(f"✗ Ошибка запуска GUI: {e}")
            import traceback
            traceback.print_exc()
            input("Нажмите Enter для продолжения...")

def main():
    """Точка входа в программу"""
    try:
        assistant = ROIAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
    except Exception as e:
        print(f"\n⚠️  Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()