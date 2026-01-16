#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главное окно ROI Assistant
"""

import sys
import sqlite3
import logging
import time
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QSettings

import traceback

def exception_hook(exctype, value, traceback_obj):
    """Функция для перехвата необработанных исключений"""
    print("\n" + "="*60)
    print("ПРОИЗОШЛА ОШИБКА:")
    print("="*60)
    traceback.print_exception(exctype, value, traceback_obj)
    print("="*60 + "\n")
    sys.__excepthook__(exctype, value, traceback_obj)

sys.excepthook = exception_hook

class InitiativeListItem(QWidget):
    """Виджет элемента списка инициатив"""
    clicked = pyqtSignal(int)  # id инициативы
    voted = pyqtSignal(int, str)  # id, vote_type
    
    def __init__(self, initiative_data):
        super().__init__()
        self.initiative = initiative_data
        self.initiative_id = initiative_data[0]
        self.user_vote = initiative_data[8]  # Сохраняем текущий выбор пользователя
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Заголовок (кликабельный)
        title = QLabel(f"<b>{self.initiative[2]}</b>")
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 12pt; padding: 5px; color: #2196F3;")
        title.setCursor(Qt.PointingHandCursor)
        title.mousePressEvent = lambda e: self.clicked.emit(self.initiative_id)
        layout.addWidget(title)
        
        # Инфо строка с голосами
        info_layout = QHBoxLayout()
        
        # Голоса ЗА
        votes_for = self.initiative[6] if len(self.initiative) > 6 else '0'
        anti_votes = self.initiative[7] if len(self.initiative) > 7 else '0'  # Новое поле anti_votes
        
        votes_label = QLabel(f"👍 {votes_for} | 👎 {anti_votes}")
        votes_label.setStyleSheet("color: #666; font-size: 10pt; font-weight: bold;")
        info_layout.addWidget(votes_label)
        
        info_layout.addStretch()
        
        # ID
        id_label = QLabel(f"#{self.initiative[0]}")
        id_label.setStyleSheet("color: #999; font-size: 9pt;")
        info_layout.addWidget(id_label)
        
        layout.addLayout(info_layout)
        
        # Кнопки голосования (компактные)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        
        # Кнопка "За"
        self.btn_for = QPushButton(" 👍 ")  # 👍   btn_for = QPushButton("👍")
        self.btn_for.setToolTip("Проголосовать ЗА")
        self.btn_for.setFixedSize(60, 44)
        self.btn_for.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_for.clicked.connect(lambda: self.vote('for'))
        self.btn_for.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(self.btn_for)
        
        # Кнопка "Против"
        self.btn_against = QPushButton("👎")
        self.btn_against.setToolTip("Проголосовать ПРОТИВ")
        self.btn_against.setFixedSize(60, 44)
        self.btn_against.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.btn_against.clicked.connect(lambda: self.vote('against'))
        self.btn_against.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(self.btn_against)
        
        # Кнопка "Игнорировать"
        self.btn_ignore = QPushButton("в игнор")
        self.btn_ignore.setToolTip("Игнорировать")
        self.btn_ignore.setFixedSize(120, 44)
        self.btn_ignore.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                border-radius: 6px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        self.btn_ignore.clicked.connect(lambda: self.vote('ignore'))
        self.btn_ignore.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(self.btn_ignore)
        
        layout.addLayout(btn_layout)
        
        # Статус голосования
        if self.initiative[8]:  # Если есть статус голосования
            status_text = {
                'for': '✅ Ваш голос: ЗА',
                'against': '❌ Ваш голос: ПРОТИВ',
                'ignore': '➖ Игнорировано'
            }.get(self.initiative[8], '')
            
            if status_text:
                status_label = QLabel(status_text)
                status_label.setStyleSheet("color: #2196F3; font-size: 9pt; padding: 2px;")
                layout.addWidget(status_label)
                
                # Обновляем внешний вид кнопок в соответствии с выбором
                self.update_buttons_appearance(self.initiative[8])
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #eee;")
        layout.addWidget(line)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 8px;
                margin: 3px;
            }
            QWidget:hover {
                background: #f5f5f5;
                border-color: #2196F3;
            }
        """)
    
    def update_buttons_appearance(self, vote_type):
        """Обновление внешнего вида кнопок в зависимости от типа голоса"""
        if vote_type == 'for':
            # Выделить кнопку "За", остальные сделать неактивными
            self.btn_for.setStyleSheet("""
                QPushButton {
                    background-color: #2E7D32;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.8;
                }
            """)
            self.btn_against.setStyleSheet("""
                QPushButton {
                    background-color: #bdbdbd;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.5;
                }
            """)
            self.btn_ignore.setStyleSheet("""
                QPushButton {
                    background-color: #bdbdbd;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.5;
                }
            """)
        elif vote_type == 'against':
            # Выделить кнопку "Против", остальные сделать неактивными
            self.btn_for.setStyleSheet("""
                QPushButton {
                    background-color: #bdbdbd;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.5;
                }
            """)
            self.btn_against.setStyleSheet("""
                QPushButton {
                    background-color: #C62828;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.8;
                }
            """)
            self.btn_ignore.setStyleSheet("""
                QPushButton {
                    background-color: #bdbdbd;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.5;
                }
            """)
        elif vote_type == 'ignore':
            # Выделить кнопку "Игнорировать", остальные сделать неактивными
            self.btn_for.setStyleSheet("""
                QPushButton {
                    background-color: #bdbdbd;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.5;
                }
            """)
            self.btn_against.setStyleSheet("""
                QPushButton {
                    background-color: #bdbdbd;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.5;
                }
            """)
            self.btn_ignore.setStyleSheet("""
                QPushButton {
                    background-color: #616161;
                    border-radius: 6px;
                    font-size: 11pt;
                    opacity: 0.8;
                }
            """)
    
    def vote(self, vote_type):
        """Обработка голосования"""
        # Если пользователь нажимает ту же кнопку дважды, это отменяет выбор
        if self.user_vote == vote_type:
            # Отменить выбор
            self.user_vote = None
            # Сбросить стиль кнопок к нормальному состоянию
            self.btn_for.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border-radius: 6px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.btn_against.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    border-radius: 6px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            self.btn_ignore.setStyleSheet("""
                QPushButton {
                    background-color: #9E9E9E;
                    border-radius: 6px;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #757575;
                }
            """)
            # Отправить сигнал об отмене голоса
            self.voted.emit(self.initiative_id, None)
        else:
            # Обновить текущий выбор
            self.user_vote = vote_type
            # Обновляем внешний вид кнопок
            self.update_buttons_appearance(vote_type)
            # Отправить сигнал о новом голосе
            self.voted.emit(self.initiative_id, vote_type)
    
    def mousePressEvent(self, event):
        """Обработка клика по виджету"""
        self.clicked.emit(self.initiative_id)
        super().mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self, db_path='data/roi.db'):
        super().__init__()
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.current_initiative_id = None  # ID текущей выбранной инициативы
        
        # начальный URL для парсинга
        self.start_url = "https://www.roi.ru/poll/last/?level=1"

        # НОВОЕ: Загружаем сохраненные настройки
        settings = QSettings('ROI_Assistant', 'Settings')
        self.start_url = settings.value('start_url', "https://www.roi.ru/poll/last/?level=1")
        self.max_pages = int(settings.value('max_pages', 1))
        self.initUI()
        self.load_initiatives()
    
    def initUI(self):
        self.setWindowTitle('ROI Assistant - Голосование за инициативы')
        self.setGeometry(100, 50, 1400, 900)  # Увеличили ширину
        
        # Центральный виджет с раздельным интерфейсом
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Верхняя панель
        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)
        
        # Панель статистики
        stats_panel = self.create_stats_panel()
        main_layout.addWidget(stats_panel)
        
        # Основная рабочая область (две колонки)
        work_area = QSplitter(Qt.Horizontal)
        work_area.setHandleWidth(5)
        work_area.setStyleSheet("QSplitter::handle { background-color: #ddd; }")
        
        # ЛЕВАЯ КОЛОНКА - Полный текст инициативы
        self.initiative_detail_widget = QWidget()
        detail_layout = QVBoxLayout()
        
        # Заголовок детальной информации
        detail_header = QLabel("Текст инициативы")
        detail_header.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px; background: #f0f0f0;")
        detail_header.setAlignment(Qt.AlignCenter)
        detail_layout.addWidget(detail_header)
        
        # Виджет для отображения полного текста
        self.initiative_text_display = QTextEdit()
        self.initiative_text_display.setReadOnly(True)
        self.initiative_text_display.setStyleSheet("""
            QTextEdit {
                font-size: 11pt;
                line-height: 1.4;
                padding: 10px;
                border: 1px solid #ddd;
                background: #fafafa;
            }
        """)
        detail_layout.addWidget(self.initiative_text_display, 1)  # 1 = растягиваем
        
        # Панель информации о выбранной инициативе
        self.detail_info_panel = QWidget()
        detail_info_layout = QHBoxLayout()
        
        self.detail_votes_label = QLabel("Голосов: 👍 0 | 👎 0")
        self.detail_votes_label.setStyleSheet("font-size: 11pt; font-weight: bold; color: #333;")
        detail_info_layout.addWidget(self.detail_votes_label)
        
        detail_info_layout.addStretch()

        # кнопка "Открыть на сайте"
        self.btn_open_detail = QPushButton('🌐 Открыть на сайте')
        self.btn_open_detail.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10pt;
                margin-left: 10px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        self.btn_open_detail.clicked.connect(self.open_current_in_browser)
        self.btn_open_detail.setCursor(Qt.PointingHandCursor)
        self.btn_open_detail.hide()  # Скрываем пока нет выбранной инициативы
        detail_info_layout.addWidget(self.btn_open_detail)
        
        self.detail_date_label = QLabel("Дата окончания: не выбрано")
        self.detail_date_label.setStyleSheet("color: #666; font-size: 10pt;")
        detail_info_layout.addWidget(self.detail_date_label)
        
        self.detail_info_panel.setLayout(detail_info_layout)
        self.detail_info_panel.setStyleSheet("background: #f5f5f5; padding: 8px; border-top: 1px solid #ddd;")
        self.detail_info_panel.hide()  # Скрываем пока не выбрана инициатива
        
        detail_layout.addWidget(self.detail_info_panel)
        
        self.initiative_detail_widget.setLayout(detail_layout)
        work_area.addWidget(self.initiative_detail_widget)
        
        # ПРАВАЯ КОЛОНКА - Список инициатив
        list_widget = QWidget()
        list_layout = QVBoxLayout()
        
        # Заголовок списка
        list_header = QLabel("Список инициатив")
        list_header.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px; background: #f0f0f0;")
        list_header.setAlignment(Qt.AlignCenter)
        list_layout.addWidget(list_header)
        
        # Поле поиска
        search_layout = QHBoxLayout()
        search_label = QLabel("Поиск:")
        search_label.setStyleSheet("font-size: 10pt;")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.setStyleSheet("padding: 5px; border: 1px solid #ddd; border-radius: 3px;")
        self.search_input.textChanged.connect(self.filter_initiatives)
        search_layout.addWidget(self.search_input, 1)  # 1 = растягиваем
        
        list_layout.addLayout(search_layout)
        
        # Список инициатив с прокруткой
        self.initiatives_scroll = QScrollArea()
        self.initiatives_scroll.setWidgetResizable(True)
        self.initiatives_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.initiatives_container = QWidget()
        self.initiatives_layout = QVBoxLayout()
        self.initiatives_layout.setAlignment(Qt.AlignTop)
        self.initiatives_layout.setSpacing(2)
        self.initiatives_container.setLayout(self.initiatives_layout)
        
        self.initiatives_scroll.setWidget(self.initiatives_container)
        list_layout.addWidget(self.initiatives_scroll, 1)  # 1 = растягиваем
        
        # Информация о количестве
        self.count_label = QLabel("Инициатив: 0")
        self.count_label.setStyleSheet("color: #666; font-size: 10pt; padding: 5px;")
        self.count_label.setAlignment(Qt.AlignCenter)
        list_layout.addWidget(self.count_label)
        
        list_widget.setLayout(list_layout)
        work_area.addWidget(list_widget)
        
        # Устанавливаем начальные размеры колонок
        work_area.setSizes([700, 700])  # Равные колонки
        
        main_layout.addWidget(work_area, 1)  # 1 = растягиваем
        
        # Нижняя панель
        bottom_panel = self.create_bottom_panel()
        main_layout.addWidget(bottom_panel)
        
        # Статус бар
        self.statusBar().showMessage('Готово')
    
    def load_initiatives(self):
        """Загрузка инициатив из базы данных"""
        # Очищаем текущий список
        for i in reversed(range(self.initiatives_layout.count())): 
            widget = self.initiatives_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Загружаем из БД ВСЕ поля
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Запрашиваем все поля, включая новые
        cursor.execute('''
            SELECT id, external_id, title, description, url, category, 
                   votes, anti_votes, status, vote, vote_date, added_date,
                   full_text, proposal_text, result_text, end_date, combined_text,
                   author, initiative_status, level, created_date, source
            FROM initiatives 
            ORDER BY added_date DESC
        ''')
        
        initiatives = cursor.fetchall()
        conn.close()
        
        # Добавляем в интерфейс
        for initiative in initiatives:
            item = InitiativeListItem(initiative)
            item.clicked.connect(self.on_initiative_selected)
            item.voted.connect(self.on_vote)
            self.initiatives_layout.addWidget(item)
        
        # Обновляем статистику
        self.update_stats()
        
        # Обновляем счетчик
        self.count_label.setText(f"Инициатив: {len(initiatives)}")
        
        # Обновляем статус
        self.statusBar().showMessage(f'Загружено инициатив: {len(initiatives)}')
        
        # Если есть инициативы, выбираем первую
        if initiatives:
            self.on_initiative_selected(initiatives[0][0])
    
    def on_initiative_selected(self, initiative_id):
        """Обработка выбора инициативы из списка"""
        self.current_initiative_id = initiative_id
        
        # Загружаем детальную информацию из БД
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, votes, anti_votes, full_text, proposal_text, result_text, 
                   combined_text, end_date, author, initiative_status, url
            FROM initiatives WHERE id = ?
        ''', (initiative_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            title, votes, anti_votes, full_text, proposal_text, result_text, \
            combined_text, end_date, author, status, url = result
            
            # Формируем полный текст для отображения
            display_text = ""
            
            if full_text:
                display_text += f"<h3>{title}</h3>"
                display_text += f"<div style='margin-bottom: 20px;'>{full_text}</div>"
            
            if result_text:
                display_text += f"<h4>Практический результат:</h4>"
                display_text += f"<div style='margin-bottom: 20px; padding: 10px; background: #f0f7ff; border-radius: 5px;'>{result_text}</div>"
            
            if proposal_text:
                display_text += f"<h4>Решение:</h4>"
                display_text += f"<div style='margin-bottom: 20px; padding: 10px; background: #f0fff0; border-radius: 5px;'>{proposal_text}</div>"
            
            if not display_text and combined_text:
                display_text = f"<h3>{title}</h3><div>{combined_text}</div>"
            
            if not display_text:
                display_text = f"<h3>{title}</h3><p>Полный текст инициативы отсутствует в базе данных.</p>"
            
            # Устанавливаем текст
            self.initiative_text_display.setHtml(display_text)
            
            # Обновляем панель информации
            self.detail_votes_label.setText(f"Голосов: 👍 {votes} | 👎 {anti_votes}")
            
            if end_date:
                self.detail_date_label.setText(f"Дата окончания: {end_date}")
            else:
                self.detail_date_label.setText("Дата окончания: не указана")
            
            # Показываем панель информации
            self.detail_info_panel.show()
            self.btn_open_detail.show()  # Показываем кнопку
            
            # Прокручиваем к началу
            self.initiative_text_display.moveCursor(QTextCursor.Start)
            
            # Обновляем статус
            self.statusBar().showMessage(f'Выбрана инициатива: {title[:50]}...', 3000)
    
    def filter_initiatives(self, search_text):
        """Фильтрация инициатив по поисковому запросу"""
        search_text = search_text.strip().lower()
        
        # Получаем все виджеты инициатив
        for i in range(self.initiatives_layout.count()):
            widget = self.initiatives_layout.itemAt(i).widget()
            if widget:
                # Ищем текст в заголовке
                title = widget.initiative[2].lower()
                if search_text == '' or search_text in title:
                    widget.show()
                else:
                    widget.hide()
        
        # Подсчитываем видимые
        visible_count = 0
        for i in range(self.initiatives_layout.count()):
            widget = self.initiatives_layout.itemAt(i).widget()
            if widget and widget.isVisible():
                visible_count += 1
        
        self.count_label.setText(f"Инициатив: {visible_count} (отфильтровано)")
    
    def create_top_panel(self):
        """Создание верхней панели"""
        panel = QWidget()
        panel.setFixedHeight(80)
        panel.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2196F3, stop:1 #1976D2);")
        
        layout = QHBoxLayout()
        
        # Логотип и заголовок
        title_layout = QVBoxLayout()
        
        title = QLabel('ROI Assistant')
        title.setStyleSheet("color: white; font-size: 24pt; font-weight: bold;")
        
        subtitle = QLabel('Программа для голосования за инициативы на roi.ru')
        subtitle.setStyleSheet("color: #BBDEFB; font-size: 10pt;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        # Кнопки
        btn_update = QPushButton('🔄 Обновить список')
        btn_update.setStyleSheet("""
            QPushButton {
                background: white;
                color: #2196F3;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 11pt;
                margin: 5px;
            }
            QPushButton:hover {
                background: #E3F2FD;
            }
        """)
        btn_update.clicked.connect(self.update_initiatives)
        btn_update.setCursor(Qt.PointingHandCursor)
        
        btn_open_web = QPushButton('🌐 Открыть на сайте')
        btn_open_web.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 11pt;
                margin: 5px;
                border: 1px solid rgba(255,255,255,0.3);
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        btn_open_web.clicked.connect(self.open_current_in_browser)
        btn_open_web.setCursor(Qt.PointingHandCursor)
        
        btn_settings = QPushButton('⚙ Настройки')
        btn_settings.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 11pt;
                margin: 5px;
                border: 1px solid rgba(255,255,255,0.3);
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        btn_settings.clicked.connect(self.show_settings)
        btn_settings.setCursor(Qt.PointingHandCursor)
        
        layout.addWidget(btn_update)
        layout.addWidget(btn_open_web)
        layout.addWidget(btn_settings)
        
        panel.setLayout(layout)
        return panel
    
    def create_stats_panel(self):
        """Создание панели статистики"""
        panel = QWidget()
        panel.setFixedHeight(60)
        panel.setStyleSheet("background: #f5f5f5; border-bottom: 1px solid #ddd;")
        
        layout = QHBoxLayout()
        
        stats = [
            ("🆕 Новые", "0", "#2196F3"),
            ("👍 За", "0", "#4CAF50"),
            ("👎 Против", "0", "#f44336"),
            ("➖ Игнорировано", "0", "#9E9E9E"),
            ("📊 Всего", "0", "#607D8B")
        ]
        
        for text, value, color in stats:
            stat_widget = self.create_stat_widget(text, value, color)
            layout.addWidget(stat_widget)
        
        layout.addStretch()
        
        # Фильтры
        filter_combo = QComboBox()
        filter_combo.addItems(['Все инициативы', 'Только новые', 'Только голосованные', 'Только игнорированные'])
        filter_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 150px;
            }
        """)
        filter_combo.currentTextChanged.connect(self.filter_by_status)
        layout.addWidget(filter_combo)
        
        panel.setLayout(layout)
        return panel
    
    def create_stat_widget(self, text, value, color):
        """Создание виджета статистики"""
        widget = QWidget()
        widget.setStyleSheet(f"border-left: 3px solid {color}; padding: 5px;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 16pt; font-weight: bold;")
        
        text_label = QLabel(text)
        text_label.setStyleSheet("color: #666; font-size: 9pt;")
        
        layout.addWidget(value_label)
        layout.addWidget(text_label)
        
        widget.setLayout(layout)
        return widget
    
    def create_bottom_panel(self):
        """Создание нижней панели"""
        panel = QWidget()
        panel.setFixedHeight(70)
        panel.setStyleSheet("background: #f5f5f5; border-top: 1px solid #ddd;")
        
        layout = QHBoxLayout()
        
        # Прогресс голосования
        progress_label = QLabel("Прогресс голосования:")
        progress_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        # Кнопка отправки голосов
        btn_submit = QPushButton('📤 Отправить голоса на сайт')
        btn_submit.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:disabled {
                background: #cccccc;
            }
        """)
        btn_submit.clicked.connect(self.submit_votes)
        btn_submit.setCursor(Qt.PointingHandCursor)
        layout.addWidget(btn_submit)
        
        panel.setLayout(layout)
        return panel
    
    def open_current_in_browser(self):
        """Открытие текущей выбранной инициативы в браузере"""
        if self.current_initiative_id:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT url FROM initiatives WHERE id = ?', (self.current_initiative_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                import webbrowser
                webbrowser.open(result[0])
                self.statusBar().showMessage('Открываю в браузере...', 2000)
            else:
                QMessageBox.warning(self, 'Ошибка', 'URL инициативы не найден')
        else:
            QMessageBox.information(self, 'Информация', 'Выберите инициативу из списка')
    
    def filter_by_status(self, filter_text):
        """Фильтрация инициатив по статусу"""
        self.statusBar().showMessage(f'Фильтр: {filter_text}', 2000)
        # TODO: Реализовать фильтрацию по статусу
    
    def on_vote(self, initiative_id, vote_type):
        """Обработка голосования"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if vote_type is None:
                # Отмена голоса - сбросить значения в БД
                cursor.execute('''
                    UPDATE initiatives 
                    SET vote = NULL, status = 'new', vote_date = NULL
                    WHERE id = ?
                ''', (initiative_id,))
            else:
                # Обновляем в БД
                cursor.execute('''
                    UPDATE initiatives 
                    SET vote = ?, status = 'voted', vote_date = ?
                    WHERE id = ?
                ''', (vote_type, datetime.now().isoformat(), initiative_id))
            
            conn.commit()
            conn.close()
            
            # Обновляем статистику
            self.update_stats()
            
            # Показываем сообщение
            if vote_type is None:
                self.statusBar().showMessage('Голос отменен', 3000)
            else:
                self.statusBar().showMessage(f'Голос сохранен: {vote_type}', 3000)
            
            # Обновляем отображение текущей инициативы
            if self.current_initiative_id == initiative_id:
                self.on_initiative_selected(initiative_id)
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить голос: {e}')
    
    def update_stats(self):
        """Обновление статистики"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'new': cursor.execute("SELECT COUNT(*) FROM initiatives WHERE status = 'new'").fetchone()[0],
            'for': cursor.execute("SELECT COUNT(*) FROM initiatives WHERE vote = 'for'").fetchone()[0],
            'against': cursor.execute("SELECT COUNT(*) FROM initiatives WHERE vote = 'against'").fetchone()[0],
            'ignore': cursor.execute("SELECT COUNT(*) FROM initiatives WHERE vote = 'ignore'").fetchone()[0],
            'total': cursor.execute("SELECT COUNT(*) FROM initiatives").fetchone()[0]
        }
        
        conn.close()
        
        # Обновляем виджеты статистики
        stats_panel = self.findChild(QWidget).findChild(QWidget).findChild(QWidget)
        if stats_panel:
            stat_widgets = stats_panel.findChildren(QWidget)
            for i, (key, widget) in enumerate(zip(['new', 'for', 'against', 'ignore', 'total'], stat_widgets)):
                value_label = widget.findChild(QLabel)
                if value_label:
                    value_label.setText(str(stats[key]))
        
        # Обновляем прогресс бар
        total_voted = stats['for'] + stats['against'] + stats['ignore']
        if stats['total'] > 0:
            progress = int((total_voted / stats['total']) * 100)
            self.progress_bar.setValue(progress)
    
    def update_initiatives(self):
        """Обновление списка инициатив с сайта ROI.ru"""
        reply = QMessageBox.question(
            self, 'Обновление',
            'Обновить список федеральных инициатив с сайта roi.ru?\n\n'
            'Программа загрузит свежие инициативы с первой страницы.\n'
            'Это может занять несколько секунд.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.statusBar().showMessage('Загрузка данных с ROI.ru...')
            QApplication.processEvents()
            
            added_count, duplicate_count = self.fetch_federal_initiatives()
            
            if added_count > 0 or duplicate_count > 0:
                result_msg = f"""
                Обновление завершено!
                
                Загружено инициатив: {added_count + duplicate_count}
                Добавлено новых: {added_count}
                Пропущено (уже есть): {duplicate_count}
                
                Таблица будет обновлена автоматически.
                """
                
                QMessageBox.information(self, 'Результат', result_msg)
                
                self.load_initiatives()
                
                self.statusBar().showMessage(f'Добавлено {added_count} новых инициатив', 5000)
            else:
                self.statusBar().showMessage('Нет новых инициатив', 3000)
    
    def submit_votes(self):
        """Отправка голосов на сайт"""
        reply = QMessageBox.question(
            self, 'Отправка голосов',
            'Отправить все сохраненные голоса на сайт roi.ru?\n\n'
            'Программа автоматически зайдет на сайт и проголосует '
            'за выбранные вами инициативы.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.statusBar().showMessage('Начата отправка голосов...')
            QMessageBox.information(
                self, 'В разработке',
                'Функция автоматической отправки голосов на сайт\n'
                'будет реализована в следующей версии.\n\n'
                'Пока голоса сохраняются только локально.'
            )
    
    def show_settings(self):
        """Показать настройки"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Настройки')
        dialog.setFixedSize(450, 350)  # Увеличили высоту
        
        layout = QVBoxLayout()
        
        # НОВОЕ: Начальный URL для парсинга
        url_layout = QHBoxLayout()
        url_label = QLabel('Начальный URL для парсинга:')
        url_label.setStyleSheet("font-weight: bold;")
        url_layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setText(self.start_url)  # Устанавливаем текущее значение
        self.url_input.setStyleSheet("padding: 5px; border: 1px solid #ddd; border-radius: 3px;")
        url_layout.addWidget(self.url_input, 1)  # 1 = растягиваем
        
        layout.addLayout(url_layout)
        
        # НОВОЕ: Количество страниц для парсинга
        pages_layout = QHBoxLayout()
        pages_label = QLabel('Макс. страниц для парсинга:')
        pages_label.setStyleSheet("font-weight: bold;")
        pages_layout.addWidget(pages_label)
        
        self.pages_spinbox = QSpinBox()
        self.pages_spinbox.setRange(1, 50)
        self.pages_spinbox.setValue(self.max_pages)
        self.pages_spinbox.setStyleSheet("padding: 5px;")
        pages_layout.addWidget(self.pages_spinbox)
        
        layout.addLayout(pages_layout)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Интервал проверки (существующий)
        interval_layout = QHBoxLayout()
        interval_label = QLabel('Интервал проверки новых инициатив:')
        interval_label.setStyleSheet("font-weight: bold;")
        interval_layout.addWidget(interval_label)
        
        interval_combo = QComboBox()
        interval_combo.addItems(['5 минут', '15 минут', '30 минут', '1 час', '3 часа', '12 часов', '1 день'])
        interval_layout.addWidget(interval_combo)
        layout.addLayout(interval_layout)
        
        # Авто-голосование (существующий)
        auto_vote = QCheckBox('Автоматически отправлять голоса на сайт')
        layout.addWidget(auto_vote)
        
        layout.addStretch()
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_settings(dialog, self.url_input.text(), self.pages_spinbox.value()))
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def save_settings(self, dialog, new_url, max_pages):
        """Сохранение настроек"""
        # Сохраняем новый URL
        self.start_url = new_url
        self.max_pages = max_pages
        
        # Сохраняем в файл настроек (опционально)
        settings = QSettings('ROI_Assistant', 'Settings')
        settings.setValue('start_url', new_url)
        settings.setValue('max_pages', max_pages)
        settings.sync()
        
        dialog.accept()
        self.statusBar().showMessage(f'Настройки сохранены. URL: {new_url[:50]}...', 3000)
    
    def fetch_federal_initiatives(self):
        """Получение федеральных инициатив с roi.ru"""
        try:
            from browser.roi_parser import ROIParser
            
            parser = ROIParser()
            
            initiatives = parser.parse_federal_initiatives(
            start_url=self.start_url,  # Передаем сохраненный URL
            max_pages=self.max_pages if hasattr(self, 'max_pages') else 1
            )
            
            if not initiatives:
                QMessageBox.warning(self, 'Внимание',
                                  'Не удалось получить инициативы.\n'
                                  'Проверьте интернет-соединение или структуру сайта.')
                return 0, 0
            
            added_count = 0
            duplicate_count = 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for i, initiative in enumerate(initiatives):
                cursor.execute(
                    "SELECT id FROM initiatives WHERE external_id = ? OR url = ?",
                    (initiative['external_id'], initiative['url'])
                )
                
                if not cursor.fetchone():
                    self.logger.info(f"Получение полного текста для новой инициативы: {initiative['title'][:50]}...")
                    
                    try:
                        details = parser.parse_initiative_details(initiative['url'])
                        
                        all_text_parts = []
                        if details.get('full_text'):
                            all_text_parts.append(details['full_text'])
                        if details.get('result_text'):
                            all_text_parts.append(f"Практический результат: {details['result_text']}")
                        if details.get('proposal_text'):
                            all_text_parts.append(f"Решение: {details['proposal_text']}")
                        
                        combined_text = '\n\n'.join(all_text_parts)
                        
                        cursor.execute('''
                            INSERT INTO initiatives 
                            (external_id, title, description, url, category, 
                            created_date, status, level, votes, anti_votes, source,
                            full_text, proposal_text, result_text, end_date, 
                            combined_text, author, initiative_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            initiative['external_id'],
                            initiative['title'],
                            initiative.get('description', ''),
                            initiative['url'],
                            initiative.get('category', 'Федеральные'),
                            initiative.get('created_date', datetime.now().strftime('%Y-%m-%d')),
                            'new',
                            initiative.get('level', 'Федеральный'),
                            details.get('votes', initiative.get('votes', '0')),
                            details.get('anti_votes', '0'),
                            initiative.get('source', 'roi.ru'),
                            details.get('full_text', ''),
                            details.get('proposal_text', ''),
                            details.get('result_text', ''),
                            details.get('end_date', ''),
                            combined_text,
                            details.get('author', ''),
                            details.get('status', 'на голосовании')
                        ))
                        
                        added_count += 1
                        time.sleep(0.5)
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка получения полного текста: {e}")
                        cursor.execute('''
                            INSERT INTO initiatives 
                            (external_id, title, description, url, category, 
                            created_date, status, level, votes, anti_votes, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            '0',
                            initiative.get('source', 'roi.ru')
                        ))
                        added_count += 1
                else:
                    duplicate_count += 1
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Итог: добавлено {added_count} новых, пропущено {duplicate_count}")
            return added_count, duplicate_count
            
        except ImportError:
            QMessageBox.critical(self, 'Ошибка',
                               'Модуль парсера не найден.\n'
                               'Убедитесь что файл browser/roi_parser.py существует')
            return 0, 0
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка',
                               f'Ошибка загрузки:\n{str(e)}')
            return 0, 0

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()