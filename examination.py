from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QToolButton, QCalendarWidget, 
                             QWidgetAction, QMenu, QComboBox, QSizePolicy, QCheckBox, QPushButton,
                             QTextEdit, QGridLayout, QDialog, QDialogButtonBox, QWidget,
                             QStylePainter, QStyleOptionComboBox, QStyle, QRadioButton, QButtonGroup,
                             QScrollArea, QMessageBox, QInputDialog, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QSize, QRect, QPoint, QTimer, QEvent
from PyQt6.QtGui import QAction, QCursor, QIcon, QColor, QPalette
import os
import sys
import json
import re

# Импортируем новые блоки
from examinationextra import SurdologyBlock, SickLeaveBlock, AdditionalBlock, DateInput, TimeInput, SymbolComboBox, EditableButton, NormButton, AutoResizingTextEdit, TemplateManagerDialog
from operation import OperationBlock
from commands import TextChangeCommand, CheckBoxCommand

# --- Вспомогательные функции путей ---
def get_resource_path(relative_path):
    """ Получает путь к ресурсам (внутри EXE или в папке исходников) """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

def get_user_path(relative_path):
    """ Получает путь для пользовательских файлов (рядом с EXE или исходником) """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
# -------------------------------------

class ExaminationPanel(QFrame):
    dateChanged = pyqtSignal(str)
    specialtyChanged = pyqtSignal(str)
    timeChanged = pyqtSignal(str)
    timeEnabledChanged = pyqtSignal(bool)
    citoChanged = pyqtSignal(bool)
    noCardChanged = pyqtSignal(bool)
    
    adChanged = pyqtSignal(str)
    tempChanged = pyqtSignal(str)
    weightChanged = pyqtSignal(str)
    complaintsChanged = pyqtSignal(str)
    anamnesisChanged = pyqtSignal(str)
    
    noComplaintsChanged = pyqtSignal(bool)
    showAnamnesisLabelChanged = pyqtSignal(bool)
    
    paidServiceChanged = pyqtSignal(bool)
    consentChanged = pyqtSignal(bool)
    
    objectiveChanged = pyqtSignal(dict)
    
    diagnosisChanged = pyqtSignal(str)
    showDiagnosisLabelChanged = pyqtSignal(bool)
    noAcutePathologyChanged = pyqtSignal(bool)
    
    recommendationsChanged = pyqtSignal(str)
    showRecommendationsLabelChanged = pyqtSignal(bool)
    repeatChanged = pyqtSignal(bool, str, str) # enabled, date, time
    
    sickLeaveChanged = pyqtSignal(dict)
    
    signatureChanged = pyqtSignal(str) # doctor_name
    
    # Сигнал для сурдологических данных
    surdologyChanged = pyqtSignal(dict)
    
    # Сигнал для операционного блока
    operationDataChanged = pyqtSignal(dict)
    operationModeChanged = pyqtSignal(bool)
    
    # Новый сигнал для персонала операции
    operationStaffChanged = pyqtSignal(str, str) # operator, nurse
    
    # Сигнал видимости подписи
    signatureVisibleChanged = pyqtSignal(bool)

    def __init__(self, undo_stack=None):
        super().__init__()
        self.undo_stack = undo_stack
        self.last_focused_widget = None
        self.last_focused_text = ""
        
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Иконки берем из ресурсов (внутри EXE)
        self.icons_path = get_resource_path("Buttons")
        
        # Шаблоны берем из пользовательской папки (рядом с EXE)
        self.templates_dir = get_user_path("Templates")
        self.specialty_dir = os.path.join(self.templates_dir, "Otorhinolaryngologist")
        self.exam_dir = os.path.join(self.specialty_dir, "Examination")
        self.operation_dir = os.path.join(self.specialty_dir, "Operation")
        self.buttons_dir = os.path.join(self.specialty_dir, "Buttons")
        
        self.init_template_dirs()
        
        # Кэш для хранения данных режимов
        self.mode_cache = {
            "examination": {}, # Данные режима осмотра
            "operation": {}    # Данные режима операции
        }
        
        # Список кнопок анамнеза для сохранения/загрузки
        self.anamnesis_buttons = []
        self.default_anamnesis_buttons = [
            {"name": "Н. дней", "text": "Со слов, беспокоит несколько дней (около 2х-3х)."},
            {"name": "Н. месяцев", "text": "Беспокоит несколько месяцев."},
            {"name": "Н. лет", "text": "Беспокоит несколько лет."},
            {"name": "Неделя", "text": "Беспокоит около недели."},
            {"name": "Месяц", "text": "Беспокоит около месяца."},
            {"name": "Год", "text": "Беспокоит около года."},
            {"name": "Улучшение", "text": "Отмечает улучшение."},
            {"name": "Операция", "text": "На плановое оперативное лечение."},
            {"name": "Профосмотр", "text": "Обращение в порядке профосмотра."},
            {"name": "Д. учет", "text": "Состоит на диспансерном учете."}
        ]
        self.buttons_json_path = os.path.join(self.buttons_dir, "anamnesis_buttons.json")
        
        # Список кнопок объективного осмотра для сохранения/загрузки
        self.objective_buttons = {}
        self.default_objective_buttons = {
            "ad": "НСП свободен, кожа физиологична, б/п серая, контуры четкие",
            "as": "НСП свободен, кожа физиологична, б/п серая, контуры четкие",
            "ad_as": "НСП свободны, кожа физиологична, б/п серые, с контуром",
            "nasi": "Носовые ходы свободные, с/о розовая, чистая, отделяемого нет",
            "pharynx": "С/о оболочка розовая, чистая, без признаков катарального воспаления",
            "nasi_pharynx": "С/о розовые, чистые, без признаков катарального воспаления",
            "larynx": "С/о розовая, чистая. Голосовые складки белесые, смыкание при фонации полное"
        }
        self.objective_buttons_json_path = os.path.join(self.buttons_dir, "objective_buttons.json")
        
        # Основной layout для QFrame
        frame_layout = QVBoxLayout(self)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаем ScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4d4d4d;
                min-height: 20px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6e6e6e;
            }
            QScrollBar::handle:vertical:pressed {
                background: #808080;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            
            /* Горизонтальный скроллбар */
            QScrollBar:horizontal {
                border: none;
                background: #2b2b2b;
                height: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #4d4d4d;
                min-width: 20px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #6e6e6e;
            }
            QScrollBar::handle:horizontal:pressed {
                background: #808080;
            }
            QScrollBar::add-line:horizontal {
                width: 0px;
            }
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # Контейнер для содержимого
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        self.scroll_area.setWidget(self.content_widget)
        
        frame_layout.addWidget(self.scroll_area)
        
        # Layout для содержимого
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- Верхняя панель с датой и специальностью ---
        date_layout = QHBoxLayout()
        
        self.date_input = DateInput()
        self.date_input.setFixedWidth(100)
        self.date_input.setPlaceholderText("ДД.ММ.ГГГГ")
        self.date_input.setInputMask("00.00.0000;_")
        self.date_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        self.date_input.textChanged.connect(self.dateChanged.emit)
        
        self.calendar_btn = QToolButton()
        self.calendar_btn.setText("📅")
        self.calendar_btn.setToolTip("Выбрать дату")
        self.calendar_btn.setStyleSheet("""
            QToolButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #606364;
            }
            QToolButton:pressed {
                background-color: #4a90e2;
            }
        """)
        self.calendar_btn.clicked.connect(self.show_calendar)
        
        date_layout.addWidget(self.date_input)
        date_layout.addWidget(self.calendar_btn)
        
        # Используем SymbolComboBox
        self.specialty_combo = SymbolComboBox()
        self.specialty_combo.addItems(["Врач-оториноларинголог"])
        self.specialty_combo.setStyleSheet("""
            QComboBox {
                background-color: #3c3f41;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
            QComboBox::drop-down {
                border: none;
                background: #505354;
                width: 20px;
                border-left: 1px solid #606364;
            }
            /* Скрываем стандартную стрелку */
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3f41;
                color: #e0e0e0;
                selection-background-color: #4a90e2;
            }
        """)
        self.specialty_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.specialty_combo.currentTextChanged.connect(self.on_specialty_changed)
        
        date_layout.addWidget(self.specialty_combo)
        
        main_layout.addLayout(date_layout)
        
        # --- Панель времени и доп. опций ---
        time_layout = QHBoxLayout()
        
        self.time_checkbox = QCheckBox()
        self.time_checkbox.stateChanged.connect(self.on_time_checkbox_changed)
        
        self.time_input = TimeInput()
        self.time_input.setFixedWidth(60)
        self.time_input.setPlaceholderText("ЧЧ:ММ")
        self.time_input.setInputMask("00:00;_")
        self.time_input.setEnabled(False)
        self.time_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
            QLineEdit:disabled {
                color: #808080;
                background-color: #2b2b2b;
            }
        """)
        self.time_input.textChanged.connect(self.timeChanged.emit)
        
        time_layout.addWidget(self.time_checkbox)
        time_layout.addWidget(self.time_input)
        
        time_layout.addSpacing(20)
        
        self.cito_checkbox = QCheckBox("Осмотр по cito!")
        self.cito_checkbox.setStyleSheet("color: #e0e0e0;")
        self.cito_checkbox.stateChanged.connect(lambda state: self.citoChanged.emit(state == Qt.CheckState.Checked.value))
        time_layout.addWidget(self.cito_checkbox)
        
        time_layout.addSpacing(10)
        
        self.no_card_checkbox = QCheckBox("На приеме без амбулаторной карты")
        self.no_card_checkbox.setStyleSheet("color: #e0e0e0;")
        self.no_card_checkbox.stateChanged.connect(lambda state: self.noCardChanged.emit(state == Qt.CheckState.Checked.value))
        time_layout.addWidget(self.no_card_checkbox)
        
        time_layout.addSpacing(10)
        
        self.operation_checkbox = QCheckBox("Операция")
        self.operation_checkbox.setStyleSheet("color: #e0e0e0;")
        self.operation_checkbox.stateChanged.connect(self.toggle_operation_mode)
        time_layout.addWidget(self.operation_checkbox)
        
        time_layout.addStretch()
        
        main_layout.addLayout(time_layout)
        
        # --- Панель шаблонов ---
        template_layout = QHBoxLayout()
        
        template_label = QLabel("Выберите шаблон:")
        template_label.setStyleSheet("color: #e0e0e0;")
        template_layout.addWidget(template_label)
        
        # Используем SymbolComboBox
        self.template_combo = SymbolComboBox()
        self.template_combo.addItems(["Пустой"])
        self.template_combo.setStyleSheet("""
            QComboBox {
                background-color: #3c3f41;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
            QComboBox::drop-down {
                border: none;
                background: #505354;
                width: 20px;
                border-left: 1px solid #606364;
            }
            /* Скрываем стандартную стрелку */
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3f41;
                color: #e0e0e0;
                selection-background-color: #4a90e2;
            }
        """)
        self.template_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.template_combo.currentTextChanged.connect(self.load_template)
        template_layout.addWidget(self.template_combo)
        
        btn_style = """
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #606364;
            }
            QPushButton:pressed {
                background-color: #4a90e2;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #707070;
                border: 1px solid #444444;
            }
        """
        
        self.btn_blank_template = QPushButton()
        self.btn_blank_template.setIcon(QIcon(os.path.join(self.icons_path, "blank.png")))
        self.btn_blank_template.setToolTip("Пустой шаблон")
        self.btn_blank_template.setStyleSheet(btn_style)
        self.btn_blank_template.clicked.connect(self.load_blank_template)
        template_layout.addWidget(self.btn_blank_template)
        
        self.btn_save_template = QPushButton()
        self.btn_save_template.setIcon(QIcon(os.path.join(self.icons_path, "Save.png")))
        self.btn_save_template.setToolTip("Сохранить как шаблон")
        self.btn_save_template.setStyleSheet(btn_style)
        self.btn_save_template.clicked.connect(self.save_as_template)
        template_layout.addWidget(self.btn_save_template)
        
        self.btn_create_template = QPushButton()
        self.btn_create_template.setIcon(QIcon(os.path.join(self.icons_path, "update.png")))
        self.btn_create_template.setToolTip("Обновить шаблон")
        self.btn_create_template.setStyleSheet(btn_style)
        self.btn_create_template.clicked.connect(self.update_template)
        template_layout.addWidget(self.btn_create_template)
        
        self.btn_template_list = QPushButton()
        self.btn_template_list.setIcon(QIcon(os.path.join(self.icons_path, "list.png")))
        self.btn_template_list.setToolTip("Список шаблонов")
        self.btn_template_list.setStyleSheet(btn_style)
        self.btn_template_list.clicked.connect(self.open_template_manager)
        template_layout.addWidget(self.btn_template_list)
        
        main_layout.addLayout(template_layout)
        
        # --- Радиокнопки типа и стороны ---
        radio_style = """
            QRadioButton {
                color: #e0e0e0;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 12px;
                height: 12px;
                border-radius: 7px;
                border: 1px solid #555;
                background-color: #3c3f41;
            }
            QRadioButton::indicator:checked {
                background-color: #4a90e2;
                border: 1px solid #4a90e2;
            }
        """
        
        # Вторая строка
        row2_layout = QHBoxLayout()
        self.side_group = QButtonGroup(self)
        
        self.rb_right = QRadioButton("Справа")
        self.rb_right.setStyleSheet(radio_style)
        self.rb_left = QRadioButton("Слева")
        self.rb_left.setStyleSheet(radio_style)
        self.rb_bilateral = QRadioButton("Двухсторонний")
        self.rb_bilateral.setStyleSheet(radio_style)
        self.rb_convalescence = QRadioButton("Реконвалесценция")
        self.rb_convalescence.setStyleSheet(radio_style)
        self.rb_side_other = QRadioButton("Другое")
        self.rb_side_other.setStyleSheet(radio_style)
        self.rb_side_other.setChecked(True)
        
        self.side_group.addButton(self.rb_right)
        self.side_group.addButton(self.rb_left)
        self.side_group.addButton(self.rb_bilateral)
        self.side_group.addButton(self.rb_convalescence)
        self.side_group.addButton(self.rb_side_other)
        
        # Подключаем сигнал изменения радиокнопки для перезагрузки шаблона
        self.side_group.buttonClicked.connect(lambda: self.load_template(self.template_combo.currentText()))
        
        row2_layout.addWidget(self.rb_right)
        row2_layout.addWidget(self.rb_left)
        row2_layout.addWidget(self.rb_bilateral)
        row2_layout.addWidget(self.rb_convalescence)
        row2_layout.addWidget(self.rb_side_other)
        row2_layout.addStretch()
        
        main_layout.addLayout(row2_layout)
        
        # ... (Indicators, Complaints, Objective blocks remain unchanged)
        # --- Блок показателей и жалоб ---
        # Используем QHBoxLayout для разделения на левую и правую части
        self.indicators_complaints_layout = QHBoxLayout()
        self.indicators_complaints_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.indicators_complaints_layout.setContentsMargins(0, 0, 0, 0)
        self.indicators_complaints_layout.setSpacing(10)
        
        # Левая колонка (Показатели + Дополнительно)
        left_column_layout = QVBoxLayout()
        left_column_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_column_layout.setSpacing(10)
        
        block_style = """
            QFrame {
                background-color: #333333;
                border: 1px solid #555;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background-color: transparent;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
            }
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 2px 6px;
                min-width: 15px;
            }
            QPushButton:hover {
                background-color: #606364;
            }
        """
        
        # 1. Блок "Показатели"
        self.indicators_frame = QFrame()
        self.indicators_frame.setStyleSheet(block_style)
        self.indicators_frame.setFixedWidth(180)
        self.indicators_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        indicators_layout = QVBoxLayout(self.indicators_frame)
        indicators_layout.setContentsMargins(10, 10, 10, 10)
        indicators_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        label_width = 30
        
        # АД
        ad_layout = QHBoxLayout()
        ad_label = QLabel("АД:")
        ad_label.setFixedWidth(label_width)
        ad_label.setStyleSheet("color: #e0e0e0;")
        self.ad_input = QLineEdit()
        self.ad_input.setFixedWidth(80)
        self.ad_input.setPlaceholderText("120/80")
        self.ad_input.textChanged.connect(self.adChanged.emit)
        
        self.btn_ad_norm = QPushButton("N")
        self.btn_ad_norm.clicked.connect(lambda: self.ad_input.setText("130/80"))
        
        ad_layout.addWidget(ad_label)
        ad_layout.addWidget(self.ad_input)
        ad_layout.addWidget(self.btn_ad_norm)
        indicators_layout.addLayout(ad_layout)
        
        # Температура
        temp_layout = QHBoxLayout()
        temp_label = QLabel("t°:")
        temp_label.setFixedWidth(label_width)
        temp_label.setStyleSheet("color: #e0e0e0;")
        self.temp_input = QLineEdit()
        self.temp_input.setFixedWidth(80)
        self.temp_input.setPlaceholderText("36,6")
        self.temp_input.textChanged.connect(self.tempChanged.emit)
        
        self.btn_temp_norm = QPushButton("N")
        self.btn_temp_norm.clicked.connect(lambda: self.temp_input.setText("36,7"))
        
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temp_input)
        temp_layout.addWidget(self.btn_temp_norm)
        indicators_layout.addLayout(temp_layout)
        
        indicators_layout.addSpacing(10)
        
        # Вес
        weight_layout = QHBoxLayout()
        weight_label = QLabel("Вес:")
        weight_label.setFixedWidth(label_width)
        weight_label.setStyleSheet("color: #e0e0e0;")
        self.weight_input = QLineEdit()
        self.weight_input.setFixedWidth(80)
        self.weight_input.setPlaceholderText("кг")
        self.weight_input.textChanged.connect(self.weightChanged.emit)
        
        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self.weight_input)
        weight_layout.addStretch()
        indicators_layout.addLayout(weight_layout)
        
        left_column_layout.addWidget(self.indicators_frame)
        
        # 2. Блок "Дополнительно"
        self.additional_block = AdditionalBlock()
        self.additional_block.paidServiceChanged.connect(self.paidServiceChanged.emit)
        self.additional_block.consentChanged.connect(self.consentChanged.emit)
        self.additional_block.surdologyVisibilityChanged.connect(self.toggle_surdology_visibility)
        # self.additional_block.sickLeaveVisibilityChanged.connect(self.toggle_sick_leave_visibility) # Удалено
        left_column_layout.addWidget(self.additional_block)
        
        # Добавляем растяжку в левую колонку, чтобы поджать блоки вверх
        left_column_layout.addStretch()
        
        # Добавляем левую колонку в основной горизонтальный лейаут
        self.indicators_complaints_layout.addLayout(left_column_layout)
        
        # 3. Правый блок ("Жалобы и анамнез")
        self.complaints_frame = QFrame()
        self.complaints_frame.setStyleSheet(block_style)
        self.complaints_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        complaints_anamnesis_layout = QVBoxLayout(self.complaints_frame)
        complaints_anamnesis_layout.setContentsMargins(10, 10, 10, 10)
        complaints_anamnesis_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Жалобы
        complaints_header_layout = QHBoxLayout()
        complaints_label = QLabel("Жалобы:")
        complaints_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        complaints_header_layout.addWidget(complaints_label)
        
        self.no_complaints_checkbox = QCheckBox("Не предъявляет")
        self.no_complaints_checkbox.setStyleSheet("color: #e0e0e0;")
        self.no_complaints_checkbox.stateChanged.connect(lambda state: self.noComplaintsChanged.emit(state == Qt.CheckState.Checked.value))
        complaints_header_layout.addWidget(self.no_complaints_checkbox)
        complaints_header_layout.addStretch()
        
        # Кнопка очистки жалоб
        self.btn_clear_complaints = QToolButton()
        self.btn_clear_complaints.setIcon(QIcon(os.path.join(self.icons_path, "erase.png")))
        self.btn_clear_complaints.setToolTip("Очистить поле")
        self.btn_clear_complaints.setStyleSheet("background-color: transparent; border: none;")
        
        complaints_header_layout.addWidget(self.btn_clear_complaints)
        
        complaints_anamnesis_layout.addLayout(complaints_header_layout)
        
        self.complaints_input = AutoResizingTextEdit()
        self.complaints_input.setStyleSheet("""
            AutoResizingTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        self.complaints_input.textChanged.connect(lambda: self.complaintsChanged.emit(self.complaints_input.toPlainText()))
        complaints_anamnesis_layout.addWidget(self.complaints_input)
        
        # Подключаем кнопку очистки после создания поля
        self.btn_clear_complaints.clicked.connect(self.complaints_input.clear)
        
        # Анамнез
        anamnesis_header_layout = QHBoxLayout()
        
        self.show_anamnesis_label_checkbox = QCheckBox()
        self.show_anamnesis_label_checkbox.setChecked(True)
        self.show_anamnesis_label_checkbox.stateChanged.connect(lambda state: self.showAnamnesisLabelChanged.emit(state == Qt.CheckState.Checked.value))
        anamnesis_header_layout.addWidget(self.show_anamnesis_label_checkbox)
        
        anamnesis_label = QLabel("Анамнез:")
        anamnesis_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        anamnesis_header_layout.addWidget(anamnesis_label)
        anamnesis_header_layout.addStretch()
        
        # Кнопка очистки анамнеза
        self.btn_clear_anamnesis = QToolButton()
        self.btn_clear_anamnesis.setIcon(QIcon(os.path.join(self.icons_path, "erase.png")))
        self.btn_clear_anamnesis.setToolTip("Очистить поле")
        self.btn_clear_anamnesis.setStyleSheet("background-color: transparent; border: none;")
        
        anamnesis_header_layout.addWidget(self.btn_clear_anamnesis)
        
        complaints_anamnesis_layout.addLayout(anamnesis_header_layout)
        
        self.anamnesis_input = AutoResizingTextEdit()
        self.anamnesis_input.setStyleSheet("""
            AutoResizingTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        self.anamnesis_input.textChanged.connect(lambda: self.anamnesisChanged.emit(self.anamnesis_input.toPlainText()))
        complaints_anamnesis_layout.addWidget(self.anamnesis_input)
        
        # Подключаем кнопку очистки после создания поля
        self.btn_clear_anamnesis.clicked.connect(self.anamnesis_input.clear)
        
        # Кнопки быстрого ввода анамнеза (QGridLayout)
        self.anamnesis_buttons_layout = QGridLayout()
        self.anamnesis_buttons_layout.setSpacing(5)
        
        # Растягиваем колонки, чтобы кнопки занимали все место
        for i in range(4): # У нас 4 колонки
            self.anamnesis_buttons_layout.setColumnStretch(i, 1)
        
        # Загружаем и создаем кнопки
        self.load_anamnesis_buttons()
        
        complaints_anamnesis_layout.addLayout(self.anamnesis_buttons_layout)
        
        complaints_anamnesis_layout.addStretch()
        
        self.indicators_complaints_layout.addWidget(self.complaints_frame, 1, Qt.AlignmentFlag.AlignTop)
        
        # Создаем контейнер для indicators_complaints_layout, чтобы можно было его скрывать
        self.indicators_complaints_container = QWidget()
        self.indicators_complaints_container.setLayout(self.indicators_complaints_layout)
        main_layout.addWidget(self.indicators_complaints_container)
        
        # --- Блок Операция ---
        self.operation_block = OperationBlock()
        self.operation_block.operationDataChanged.connect(self.operationDataChanged.emit)
        self.operation_block.setVisible(False)
        main_layout.addWidget(self.operation_block)
        
        # --- Блок объективного осмотра ---
        self.objective_frame = QFrame()
        self.objective_frame.setStyleSheet(block_style)
        self.objective_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        objective_layout = QVBoxLayout(self.objective_frame)
        objective_layout.setContentsMargins(10, 10, 10, 10)
        objective_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        objective_label = QLabel("ОБЪЕКТИВНЫЙ ОСМОТР")
        objective_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        objective_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        objective_layout.addWidget(objective_label)
        
        # Чекбоксы объединения
        merge_layout = QHBoxLayout()
        self.chk_merge_ears = QCheckBox("Объединить AD/AS")
        self.chk_merge_ears.setStyleSheet("color: #e0e0e0;")
        self.chk_merge_ears.stateChanged.connect(self.toggle_ears_merge)
        merge_layout.addWidget(self.chk_merge_ears)
        
        self.chk_merge_nose_throat = QCheckBox("Объединить Nasi/pharynx")
        self.chk_merge_nose_throat.setStyleSheet("color: #e0e0e0;")
        self.chk_merge_nose_throat.stateChanged.connect(self.toggle_nose_throat_merge)
        merge_layout.addWidget(self.chk_merge_nose_throat)
        
        merge_layout.addStretch()
        objective_layout.addLayout(merge_layout)
        
        # Загружаем кнопки объективного осмотра
        self.load_objective_buttons()

        def create_objective_row(label_text, default_checked=True, norm_key=None):
            container = QWidget()
            container.setStyleSheet("background-color: transparent;")
            row_layout = QHBoxLayout(container)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            # 1. Чекбокс (слева)
            chk = QCheckBox()
            chk.setChecked(default_checked)
            chk.setStyleSheet("QCheckBox { background-color: transparent; color: #e0e0e0; }")
            
            # 2. Метка
            lbl = QLabel(label_text)
            lbl.setFixedWidth(60)
            lbl.setStyleSheet("QLabel { background-color: transparent; color: #e0e0e0; border: none; }")
            
            # 3. Поле ввода
            txt = AutoResizingTextEdit()
            txt.setStyleSheet("""
                AutoResizingTextEdit {
                    background-color: #2b2b2b;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 4px;
                    color: #e0e0e0;
                }
            """)
            
            # Логика: если чекбокс выключен, и мы начинаем писать, он включается
            txt.textChanged.connect(lambda: self.auto_check(chk, txt))
            
            row_layout.addWidget(chk)
            row_layout.addWidget(lbl)
            row_layout.addWidget(txt)
            
            # 4. Кнопка "N" (справа)
            if norm_key:
                # Получаем текущее значение и дефолтное значение
                current_text = self.objective_buttons.get(norm_key, "")
                default_text = self.default_objective_buttons.get(norm_key, "")
                
                btn_norm = NormButton(current_text, default_insert_text=default_text)
                btn_norm.insertTextChanged.connect(lambda text: txt.setPlainText(text))
                btn_norm.changed.connect(lambda: self.save_objective_button(norm_key, btn_norm))
                row_layout.addWidget(btn_norm)
            
            # 5. Кнопка "Очистить" (справа)
            btn_clear = QToolButton()
            btn_clear.setIcon(QIcon(os.path.join(self.icons_path, "erase.png")))
            btn_clear.setStyleSheet("background-color: transparent; border: none;")
            btn_clear.clicked.connect(txt.clear)
            row_layout.addWidget(btn_clear)
            
            return container, txt, chk

        # AD
        self.row_ad, self.ad_ear_input, self.ad_ear_chk = create_objective_row(
            "AD - ", True, "ad"
        )
        objective_layout.addWidget(self.row_ad)
        
        # AS
        self.row_as, self.as_ear_input, self.as_ear_chk = create_objective_row(
            "AS - ", True, "as"
        )
        objective_layout.addWidget(self.row_as)
        
        # AD/AS Combined
        self.row_ad_as_combined, self.ad_as_combined_input, self.ad_as_combined_chk = create_objective_row(
            "AD/AS - ", True, "ad_as"
        )
        self.row_ad_as_combined.setVisible(False)
        objective_layout.addWidget(self.row_ad_as_combined)
        
        # Nasi
        self.row_nasi, self.nasi_input, self.nasi_chk = create_objective_row(
            "Nasi - ", True, "nasi"
        )
        objective_layout.addWidget(self.row_nasi)
        
        # Pharynx
        self.row_pharynx, self.pharynx_input, self.pharynx_chk = create_objective_row(
            "Pharynx - ", True, "pharynx"
        )
        objective_layout.addWidget(self.row_pharynx)
        
        # Nasi/Pharynx Combined
        self.row_nasi_pharynx_combined, self.nasi_pharynx_combined_input, self.nasi_pharynx_combined_chk = create_objective_row(
            "Nasi, pharynx - ", True, "nasi_pharynx"
        )
        self.row_nasi_pharynx_combined.setVisible(False)
        objective_layout.addWidget(self.row_nasi_pharynx_combined)
        
        # Larynx
        self.row_larynx, self.larynx_input, self.larynx_chk = create_objective_row(
            "Larynx - ", False, "larynx"
        )
        objective_layout.addWidget(self.row_larynx)
        
        # Other
        self.row_other, self.other_input, self.other_chk = create_objective_row(
            "Прочее - ", False, None
        )
        objective_layout.addWidget(self.row_other)
        
        # Подключаем сигналы изменения текста и чекбоксов
        self.ad_ear_input.textChanged.connect(self.emit_objective_changed)
        self.ad_ear_chk.stateChanged.connect(self.emit_objective_changed)
        
        self.as_ear_input.textChanged.connect(self.emit_objective_changed)
        self.as_ear_chk.stateChanged.connect(self.emit_objective_changed)
        
        self.ad_as_combined_input.textChanged.connect(self.emit_objective_changed)
        self.ad_as_combined_chk.stateChanged.connect(self.emit_objective_changed)
        
        self.nasi_input.textChanged.connect(self.emit_objective_changed)
        self.nasi_chk.stateChanged.connect(self.emit_objective_changed)
        
        self.pharynx_input.textChanged.connect(self.emit_objective_changed)
        self.pharynx_chk.stateChanged.connect(self.emit_objective_changed)
        
        self.nasi_pharynx_combined_input.textChanged.connect(self.emit_objective_changed)
        self.nasi_pharynx_combined_chk.stateChanged.connect(self.emit_objective_changed)
        
        self.larynx_input.textChanged.connect(self.emit_objective_changed)
        self.larynx_chk.stateChanged.connect(self.emit_objective_changed)
        
        self.other_input.textChanged.connect(self.emit_objective_changed)
        self.other_chk.stateChanged.connect(self.emit_objective_changed)
        
        self.chk_merge_ears.stateChanged.connect(self.emit_objective_changed)
        self.chk_merge_nose_throat.stateChanged.connect(self.emit_objective_changed)
        
        main_layout.addWidget(self.objective_frame)
        
        # --- Блок Сурдологические данные ---
        self.surdology_block = SurdologyBlock()
        self.surdology_block.surdologyChanged.connect(self.surdologyChanged.emit)
        self.surdology_block.setVisible(False) # Скрыт по умолчанию
        main_layout.addWidget(self.surdology_block)
        
        # ... (Diagnosis, Recs, Sick Leave, Signature blocks remain unchanged)
        # --- Блок Диагноз ---
        self.diagnosis_frame = QFrame()
        self.diagnosis_frame.setStyleSheet(block_style)
        self.diagnosis_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        diagnosis_layout = QVBoxLayout(self.diagnosis_frame)
        diagnosis_layout.setContentsMargins(10, 10, 10, 10)
        diagnosis_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Заголовок диагноза с чекбоксами
        diagnosis_header_layout = QHBoxLayout()
        
        self.show_diagnosis_label_checkbox = QCheckBox()
        self.show_diagnosis_label_checkbox.setChecked(True)
        self.show_diagnosis_label_checkbox.stateChanged.connect(lambda state: self.showDiagnosisLabelChanged.emit(state == Qt.CheckState.Checked.value))
        diagnosis_header_layout.addWidget(self.show_diagnosis_label_checkbox)
        
        diagnosis_label = QLabel("Диагноз:")
        diagnosis_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        diagnosis_header_layout.addWidget(diagnosis_label)
        
        self.no_acute_pathology_checkbox = QCheckBox("Острой ЛОР патологии не выявлено")
        self.no_acute_pathology_checkbox.setStyleSheet("color: #e0e0e0;")
        self.no_acute_pathology_checkbox.stateChanged.connect(lambda state: self.noAcutePathologyChanged.emit(state == Qt.CheckState.Checked.value))
        diagnosis_header_layout.addWidget(self.no_acute_pathology_checkbox)
        
        diagnosis_header_layout.addStretch()
        
        # Кнопка очистки диагноза
        self.btn_clear_diagnosis = QToolButton()
        self.btn_clear_diagnosis.setIcon(QIcon(os.path.join(self.icons_path, "erase.png")))
        self.btn_clear_diagnosis.setToolTip("Очистить поле")
        self.btn_clear_diagnosis.setStyleSheet("background-color: transparent; border: none;")
        
        diagnosis_header_layout.addWidget(self.btn_clear_diagnosis)
        
        diagnosis_layout.addLayout(diagnosis_header_layout)
        
        self.diagnosis_input = AutoResizingTextEdit()
        self.diagnosis_input.setStyleSheet("""
            AutoResizingTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        self.diagnosis_input.textChanged.connect(lambda: self.diagnosisChanged.emit(self.diagnosis_input.toHtml()))
        diagnosis_layout.addWidget(self.diagnosis_input)
        
        # Подключаем кнопку очистки
        self.btn_clear_diagnosis.clicked.connect(self.diagnosis_input.clear)
        
        # --- Новые поля для Оператора и Медсестры ---
        self.op_staff_container = QWidget()
        op_staff_layout = QHBoxLayout(self.op_staff_container)
        op_staff_layout.setContentsMargins(0, 5, 0, 0)
        
        op_staff_layout.addWidget(QLabel("Оператор:"))
        self.operator_input = QLineEdit()
        self.operator_input.setPlaceholderText("ФИО оператора")
        self.operator_input.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555; border-radius: 3px; padding: 2px; color: #e0e0e0;")
        self.operator_input.textChanged.connect(lambda: self.operationStaffChanged.emit(self.operator_input.text(), self.nurse_input.text()))
        op_staff_layout.addWidget(self.operator_input)
        
        op_staff_layout.addSpacing(10)
        
        op_staff_layout.addWidget(QLabel("Операционная м/с:"))
        self.nurse_input = QLineEdit()
        self.nurse_input.setPlaceholderText("ФИО медсестры")
        self.nurse_input.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555; border-radius: 3px; padding: 2px; color: #e0e0e0;")
        self.nurse_input.textChanged.connect(lambda: self.operationStaffChanged.emit(self.operator_input.text(), self.nurse_input.text()))
        op_staff_layout.addWidget(self.nurse_input)
        
        self.op_staff_container.setVisible(False) # Скрыто по умолчанию
        diagnosis_layout.addWidget(self.op_staff_container)
        
        main_layout.addWidget(self.diagnosis_frame)
        
        # --- Блок Рекомендации и Прочие данные ---
        rec_other_layout = QHBoxLayout()
        rec_other_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        rec_other_layout.setSpacing(10)
        
        # 1. Левый блок (Прочие данные)
        self.other_data_frame = QFrame()
        self.other_data_frame.setStyleSheet(block_style)
        self.other_data_frame.setFixedWidth(180)
        self.other_data_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        
        other_data_layout = QVBoxLayout(self.other_data_frame)
        other_data_layout.setContentsMargins(10, 10, 10, 10)
        other_data_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Заголовок блока
        other_data_label = QLabel("Повторный осмотр")
        other_data_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        other_data_layout.addWidget(other_data_label)
        
        self.repeat_chk = QCheckBox("Повторный прием")
        self.repeat_chk.setStyleSheet("color: #e0e0e0;")
        self.repeat_chk.stateChanged.connect(self.toggle_repeat_fields)
        other_data_layout.addWidget(self.repeat_chk)
        
        # Дата повторного приема
        repeat_date_layout = QHBoxLayout()
        self.repeat_date_input = DateInput()
        self.repeat_date_input.setPlaceholderText("ДД.ММ.ГГГГ")
        self.repeat_date_input.setInputMask("00.00.0000;_")
        self.repeat_date_input.setEnabled(False)
        self.repeat_date_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
            QLineEdit:disabled {
                color: #808080;
                background-color: #2b2b2b;
            }
        """)
        self.repeat_date_input.textChanged.connect(lambda text: self.repeatChanged.emit(self.repeat_chk.isChecked(), text, self.repeat_time_input.text()))
        
        self.repeat_calendar_btn = QToolButton()
        self.repeat_calendar_btn.setText("📅")
        self.repeat_calendar_btn.setEnabled(False)
        self.repeat_calendar_btn.setStyleSheet("""
            QToolButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #606364;
            }
            QToolButton:pressed {
                background-color: #4a90e2;
            }
            QToolButton:disabled {
                background-color: #2b2b2b;
                color: #808080;
                border: 1px solid #444;
            }
        """)
        self.repeat_calendar_btn.clicked.connect(self.show_repeat_calendar)
        
        repeat_date_layout.addWidget(self.repeat_date_input)
        repeat_date_layout.addWidget(self.repeat_calendar_btn)
        other_data_layout.addLayout(repeat_date_layout)
        
        # Время повторного приема
        self.repeat_time_input = TimeInput()
        self.repeat_time_input.setPlaceholderText("ЧЧ:ММ")
        self.repeat_time_input.setInputMask("00:00;_")
        self.repeat_time_input.setEnabled(False)
        self.repeat_time_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
            QLineEdit:disabled {
                color: #808080;
                background-color: #2b2b2b;
            }
        """)
        self.repeat_time_input.textChanged.connect(lambda text: self.repeatChanged.emit(self.repeat_chk.isChecked(), self.repeat_date_input.text(), text))
        other_data_layout.addWidget(self.repeat_time_input)
        
        other_data_layout.addSpacing(10)
        
        # Чекбокс Больничный лист
        self.sick_leave_checkbox = QCheckBox("Больничный лист")
        self.sick_leave_checkbox.setStyleSheet("color: #e0e0e0;")
        self.sick_leave_checkbox.stateChanged.connect(lambda state: self.toggle_sick_leave_visibility(state == Qt.CheckState.Checked.value))
        other_data_layout.addWidget(self.sick_leave_checkbox)
        
        other_data_layout.addStretch()
        rec_other_layout.addWidget(self.other_data_frame)
        
        # 2. Правый блок (Рекомендации)
        self.rec_frame = QFrame()
        self.rec_frame.setStyleSheet(block_style)
        self.rec_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        rec_layout = QVBoxLayout(self.rec_frame)
        rec_layout.setContentsMargins(10, 10, 10, 10)
        rec_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        rec_header_layout = QHBoxLayout()
        
        self.show_recommendations_label_checkbox = QCheckBox()
        self.show_recommendations_label_checkbox.setChecked(True)
        self.show_recommendations_label_checkbox.stateChanged.connect(lambda state: self.showRecommendationsLabelChanged.emit(state == Qt.CheckState.Checked.value))
        rec_header_layout.addWidget(self.show_recommendations_label_checkbox)
        
        rec_label = QLabel("Рекомендации:")
        rec_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        rec_header_layout.addWidget(rec_label)
        rec_header_layout.addStretch()
        
        # Кнопка очистки рекомендаций
        self.btn_clear_recommendations = QToolButton()
        self.btn_clear_recommendations.setIcon(QIcon(os.path.join(self.icons_path, "erase.png")))
        self.btn_clear_recommendations.setToolTip("Очистить поле")
        self.btn_clear_recommendations.setStyleSheet("background-color: transparent; border: none;")
        
        rec_header_layout.addWidget(self.btn_clear_recommendations)
        
        rec_layout.addLayout(rec_header_layout)
        
        self.rec_input = AutoResizingTextEdit()
        self.rec_input.document().setDefaultStyleSheet("ul { margin-top: 0px; margin-bottom: 0px; margin-left: 10px; -qt-list-indent: 0; } ol { margin-top: 0px; margin-bottom: 0px; margin-left: 10px; -qt-list-indent: 0; }")
        self.rec_input.setStyleSheet("""
            AutoResizingTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        self.rec_input.textChanged.connect(lambda: self.recommendationsChanged.emit(self.rec_input.toHtml()))
        rec_layout.addWidget(self.rec_input)
        
        # Подключаем кнопку очистки
        self.btn_clear_recommendations.clicked.connect(self.rec_input.clear)
        
        rec_other_layout.addWidget(self.rec_frame)
        
        main_layout.addLayout(rec_other_layout)
        
        # --- Блок Листок нетрудоспособности ---
        self.sick_leave_block = SickLeaveBlock()
        self.sick_leave_block.sickLeaveChanged.connect(self.sickLeaveChanged.emit)
        self.sick_leave_block.setVisible(False) # Скрыт по умолчанию
        main_layout.addWidget(self.sick_leave_block)
        
        # --- Блок Подпись ---
        self.signature_frame = QFrame()
        self.signature_frame.setStyleSheet(block_style)
        self.signature_frame.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        signature_layout = QHBoxLayout(self.signature_frame)
        signature_layout.setContentsMargins(10, 10, 10, 10)
        signature_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Чекбокс видимости подписи (для режима операции)
        self.signature_visible_checkbox = QCheckBox("Врач-оториноларинголог")
        self.signature_visible_checkbox.setStyleSheet("color: #e0e0e0;")
        self.signature_visible_checkbox.setChecked(False) # По умолчанию отключен
        self.signature_visible_checkbox.setVisible(False) # Скрыт по умолчанию (только для режима операции)
        self.signature_visible_checkbox.stateChanged.connect(lambda state: self.signatureVisibleChanged.emit(state == Qt.CheckState.Checked.value))
        
        # Сначала чекбокс, потом stretch, потом остальное
        signature_layout.addWidget(self.signature_visible_checkbox)
        
        self.signature_label = QLabel("Врач-оториноларинголог")
        self.signature_label.setStyleSheet("color: #e0e0e0;")
        signature_layout.addWidget(self.signature_label)
        
        signature_layout.addStretch()
        
        self.btn_add_signature = QPushButton("Добавить личную подпись")
        self.btn_add_signature.setStyleSheet("""
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #606364;
            }
        """)
        signature_layout.addWidget(self.btn_add_signature)
        
        self.doctor_name_input = QLineEdit()
        self.doctor_name_input.setPlaceholderText("ФИО врача")
        self.doctor_name_input.setFixedWidth(200)
        self.doctor_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        self.doctor_name_input.textChanged.connect(lambda text: self.signatureChanged.emit(text))
        signature_layout.addWidget(self.doctor_name_input)
        
        main_layout.addWidget(self.signature_frame)
        
        # Добавляем растяжку в основной макет, чтобы все блоки прижимались к верху
        main_layout.addStretch()
        
        # Устанавливаем текущую дату и время по умолчанию
        self.set_current_date()
        self.set_current_time()
        
        # Загружаем список шаблонов
        self.refresh_template_list()
        
        # Устанавливаем начальное состояние (Пустой шаблон)
        self.load_template("Пустой")
        
        # Устанавливаем фильтры событий для Undo/Redo
        self.install_event_filters()

    def init_template_dirs(self):
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        if not os.path.exists(self.specialty_dir):
            os.makedirs(self.specialty_dir)
        if not os.path.exists(self.exam_dir):
            os.makedirs(self.exam_dir)
        if not os.path.exists(self.operation_dir):
            os.makedirs(self.operation_dir)
        if not os.path.exists(self.buttons_dir):
            os.makedirs(self.buttons_dir)

    def load_anamnesis_buttons(self):
        # Очищаем текущие кнопки
        for i in reversed(range(self.anamnesis_buttons_layout.count())): 
            self.anamnesis_buttons_layout.itemAt(i).widget().setParent(None)
        self.anamnesis_buttons = []

        # Загружаем данные из JSON или используем дефолтные
        buttons_data = self.default_anamnesis_buttons
        if os.path.exists(self.buttons_json_path):
            try:
                with open(self.buttons_json_path, 'r', encoding='utf-8') as f:
                    buttons_data = json.load(f)
            except Exception as e:
                print(f"Error loading buttons: {e}")

        # Создаем кнопки
        for i, btn_data in enumerate(buttons_data):
            # Determine defaults
            if i < len(self.default_anamnesis_buttons):
                def_name = self.default_anamnesis_buttons[i]["name"]
                def_text = self.default_anamnesis_buttons[i]["text"]
            else:
                def_name = btn_data["name"]
                def_text = btn_data["text"]

            btn = EditableButton(btn_data["name"], btn_data["text"], default_text=def_name, default_insert_text=def_text)
            btn.insertTextChanged.connect(self.append_anamnesis_text)
            btn.changed.connect(self.save_anamnesis_buttons)
            
            row = i // 4
            col = i % 4
            self.anamnesis_buttons_layout.addWidget(btn, row, col)
            self.anamnesis_buttons.append(btn)

    def save_anamnesis_buttons(self):
        buttons_data = []
        for btn in self.anamnesis_buttons:
            buttons_data.append({
                "name": btn.text(),
                "text": btn.current_insert_text
            })
        
        try:
            with open(self.buttons_json_path, 'w', encoding='utf-8') as f:
                json.dump(buttons_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить кнопки: {e}")

    def load_objective_buttons(self):
        # Загружаем данные из JSON или используем дефолтные
        if os.path.exists(self.objective_buttons_json_path):
            try:
                with open(self.objective_buttons_json_path, 'r', encoding='utf-8') as f:
                    self.objective_buttons = json.load(f)
            except Exception as e:
                print(f"Error loading objective buttons: {e}")
                self.objective_buttons = self.default_objective_buttons.copy()
        else:
            self.objective_buttons = self.default_objective_buttons.copy()

    def save_objective_button(self, key, btn):
        self.objective_buttons[key] = btn.current_insert_text
        try:
            with open(self.objective_buttons_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.objective_buttons, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить кнопку: {e}")

    def open_template_manager(self):
        # Передаем текущую директорию шаблонов
        current_dir = self.get_current_template_dir()
        dialog = TemplateManagerDialog(current_dir, self.icons_path, self)
        dialog.templatesChanged.connect(self.refresh_template_list)
        dialog.exec()

    def get_current_template_dir(self):
        if self.operation_checkbox.isChecked():
            return self.operation_dir
        else:
            return self.exam_dir

    def refresh_template_list(self):
        current = self.template_combo.currentText()
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        self.template_combo.addItem("Пустой")
        
        current_dir = self.get_current_template_dir()
        
        if os.path.exists(current_dir):
            files = [f for f in os.listdir(current_dir) if f.endswith('.json')]
            for f in files:
                try:
                    with open(os.path.join(current_dir, f), 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        name = data.get("template_name", f.replace(".json", ""))
                        self.template_combo.addItem(name)
                except:
                    continue
        
        index = self.template_combo.findText(current)
        if index != -1:
            self.template_combo.setCurrentIndex(index)
        else:
            self.template_combo.setCurrentIndex(0)
            
        self.template_combo.blockSignals(False)

    def get_current_side_key(self):
        if self.rb_right.isChecked(): return "right"
        if self.rb_left.isChecked(): return "left"
        if self.rb_bilateral.isChecked(): return "bilateral"
        if self.rb_convalescence.isChecked(): return "convalescence"
        return "other"

    def collect_current_data(self):
        # Собираем данные в зависимости от режима
        if self.operation_checkbox.isChecked():
            # Режим операции
            return {
                "operation_data": self.operation_block.get_data(),
                "diagnosis": {
                    "text": self.diagnosis_input.toHtml(),
                    "show_label": self.show_diagnosis_label_checkbox.isChecked(),
                    "no_acute_pathology": self.no_acute_pathology_checkbox.isChecked()
                },
                "recommendations": {
                    "text": self.rec_input.toHtml(),
                    "show_label": self.show_recommendations_label_checkbox.isChecked()
                },
                "op_staff": {
                    "operator": self.operator_input.text(),
                    "nurse": self.nurse_input.text()
                },
                "signature_visible": self.signature_visible_checkbox.isChecked()
            }
        else:
            # Режим осмотра
            surdology_data = self.surdology_block.get_data()
            sick_leave_data = self.sick_leave_block.get_data()
            additional_data = self.additional_block.get_data()

            return {
                "indicators": {
                    "ad": self.ad_input.text(),
                    "temp": self.temp_input.text(),
                    "weight": self.weight_input.text()
                },
                "additional": additional_data,
                "complaints_anamnesis": {
                    "complaints": self.complaints_input.toPlainText(),
                    "no_complaints": self.no_complaints_checkbox.isChecked(),
                    "anamnesis": self.anamnesis_input.toPlainText(),
                    "show_anamnesis_label": self.show_anamnesis_label_checkbox.isChecked()
                },
                "objective": {
                    "ad_ear": self.ad_ear_input.toPlainText(), "ad_vis": self.ad_ear_chk.isChecked(),
                    "as_ear": self.as_ear_input.toPlainText(), "as_vis": self.as_ear_chk.isChecked(),
                    "ad_as_comb": self.ad_as_combined_input.toPlainText(), "ad_as_vis": self.ad_as_combined_chk.isChecked(),
                    "merge_ears": self.chk_merge_ears.isChecked(),
                    
                    "nasi": self.nasi_input.toPlainText(), "nasi_vis": self.nasi_chk.isChecked(),
                    "pharynx": self.pharynx_input.toPlainText(), "pharynx_vis": self.pharynx_chk.isChecked(),
                    "nasi_pharynx_comb": self.nasi_pharynx_combined_input.toPlainText(), "nasi_pharynx_vis": self.nasi_pharynx_combined_chk.isChecked(),
                    "merge_nose_throat": self.chk_merge_nose_throat.isChecked(),
                    
                    "larynx": self.larynx_input.toPlainText(), "larynx_vis": self.larynx_chk.isChecked(),
                    "other": self.other_input.toPlainText(), "other_vis": self.other_chk.isChecked()
                },
                "surdology": surdology_data,
                "sick_leave": sick_leave_data,
                "diagnosis": {
                    "text": self.diagnosis_input.toHtml(),
                    "show_label": self.show_diagnosis_label_checkbox.isChecked(),
                    "no_acute_pathology": self.no_acute_pathology_checkbox.isChecked()
                },
                "other_data": {
                    "repeat": self.repeat_chk.isChecked(),
                    "repeat_date": self.repeat_date_input.text(),
                    "repeat_time": self.repeat_time_input.text()
                },
                "recommendations": {
                    "text": self.rec_input.toHtml(),
                    "show_label": self.show_recommendations_label_checkbox.isChecked()
                },
                "signature_visible": self.signature_visible_checkbox.isChecked()
            }

    def save_as_template(self):
        name, ok = QInputDialog.getText(self, "Сохранить шаблон", "Введите название шаблона:")
        if ok and name:
            filename = f"{name}.json"
            current_dir = self.get_current_template_dir()
            filepath = os.path.join(current_dir, filename)
            
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                except:
                    template_data = {"template_name": name, "data": {}}
            else:
                template_data = {"template_name": name, "data": {}}
            
            side_key = self.get_current_side_key()
            template_data["data"][side_key] = self.collect_current_data()
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, ensure_ascii=False, indent=4)
                
                self.refresh_template_list()
                self.template_combo.setCurrentText(name)
                QMessageBox.information(self, "Успех", "Шаблон успешно сохранен!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить шаблон: {str(e)}")

    def update_template(self):
        current_template_name = self.template_combo.currentText()
        if current_template_name == "Пустой":
            QMessageBox.warning(self, "Внимание", "Не выбран шаблон для обновления!")
            return

        reply = QMessageBox.question(self, "ВНИМАНИЕ", 
                                     "Вы уверены, что хотите перезаписать сохраненный шаблон?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        
        if reply == QMessageBox.StandardButton.Yes:
            filename = f"{current_template_name}.json"
            current_dir = self.get_current_template_dir()
            filepath = os.path.join(current_dir, filename)
            
            if not os.path.exists(filepath):
                 found = False
                 for f in os.listdir(current_dir):
                     if f.endswith('.json'):
                         try:
                             with open(os.path.join(current_dir, f), 'r', encoding='utf-8') as file:
                                 data = json.load(file)
                                 if data.get("template_name") == current_template_name:
                                     filepath = os.path.join(current_dir, f)
                                     found = True
                                     break
                         except: continue
                 if not found:
                     QMessageBox.critical(self, "Ошибка", "Файл шаблона не найден!")
                     return

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                side_key = self.get_current_side_key()
                template_data["data"][side_key] = self.collect_current_data()
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, ensure_ascii=False, indent=4)
                
                QMessageBox.information(self, "Успех", "Шаблон успешно обновлен!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить шаблон: {str(e)}")

    def clear_fields(self):
        if self.operation_checkbox.isChecked():
            # Очистка полей операции
            self.operation_block.clear()
            self.diagnosis_input.clear()
            self.rec_input.clear()
            self.operator_input.clear()
            self.nurse_input.clear()
            self.signature_visible_checkbox.setChecked(False)
        else:
            # Очистка полей осмотра
            self.ad_input.clear()
            self.temp_input.clear()
            self.weight_input.clear()
            self.additional_block.clear()
            self.complaints_input.clear()
            self.no_complaints_checkbox.setChecked(False)
            self.anamnesis_input.clear()
            self.show_anamnesis_label_checkbox.setChecked(True)
            self.ad_ear_input.clear()
            self.ad_ear_chk.setChecked(True)
            self.as_ear_input.clear()
            self.as_ear_chk.setChecked(True)
            self.ad_as_combined_input.clear()
            self.ad_as_combined_chk.setChecked(True)
            self.chk_merge_ears.setChecked(False)
            self.nasi_input.clear()
            self.nasi_chk.setChecked(True)
            self.pharynx_input.clear()
            self.pharynx_chk.setChecked(True)
            self.nasi_pharynx_combined_input.clear()
            self.nasi_pharynx_combined_chk.setChecked(True)
            self.chk_merge_nose_throat.setChecked(False)
            self.larynx_input.clear()
            self.larynx_chk.setChecked(False)
            self.other_input.clear()
            self.other_chk.setChecked(False)
            self.surdology_block.clear()
            self.sick_leave_block.clear()
            self.diagnosis_input.clear()
            self.show_diagnosis_label_checkbox.setChecked(True)
            self.no_acute_pathology_checkbox.setChecked(False)
            self.rec_input.clear()
            self.show_recommendations_label_checkbox.setChecked(True)
            self.repeat_chk.setChecked(False)
            self.repeat_date_input.clear()
            self.repeat_time_input.clear()
            self.signature_visible_checkbox.setChecked(False)

    def load_blank_template(self):
        self.load_template("Пустой")
        self.template_combo.setCurrentText("Пустой")

    def load_template(self, template_name):
        if template_name == "Пустой":
            self.btn_create_template.setEnabled(False)
            self.clear_fields()
            return

        self.btn_create_template.setEnabled(True)

        current_dir = self.get_current_template_dir()
        filepath = os.path.join(current_dir, f"{template_name}.json")
        if not os.path.exists(filepath):
             for f in os.listdir(current_dir):
                 if f.endswith('.json'):
                     try:
                         with open(os.path.join(current_dir, f), 'r', encoding='utf-8') as file:
                             data = json.load(file)
                             if data.get("template_name") == template_name:
                                 filepath = os.path.join(current_dir, f)
                                 break
                     except: continue
        
        if not os.path.exists(filepath): return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            side_key = self.get_current_side_key()
            data = template_data.get("data", {}).get(side_key)
            
            if data:
                self.apply_template_data(data)
            else:
                pass
                
        except Exception as e:
            print(f"Error loading template: {e}")

    def apply_template_data(self, data):
        if self.operation_checkbox.isChecked():
            # Применение данных операции
            self.operation_block.set_data(data.get("operation_data", {}))
            
            diag_data = data.get("diagnosis", {})
            if isinstance(diag_data, str):
                self.diagnosis_input.setHtml(diag_data)
            else:
                self.diagnosis_input.setHtml(diag_data.get("text", ""))
                self.show_diagnosis_label_checkbox.setChecked(diag_data.get("show_label", True))
                self.no_acute_pathology_checkbox.setChecked(diag_data.get("no_acute_pathology", False))
            
            rec_data = data.get("recommendations", {})
            if isinstance(rec_data, str):
                self.rec_input.setHtml(rec_data)
            else:
                self.rec_input.setHtml(rec_data.get("text", ""))
                self.show_recommendations_label_checkbox.setChecked(rec_data.get("show_label", True))
            
            op_staff = data.get("op_staff", {})
            self.operator_input.setText(op_staff.get("operator", ""))
            self.nurse_input.setText(op_staff.get("nurse", ""))
            
            self.signature_visible_checkbox.setChecked(data.get("signature_visible", False))
        else:
            # Применение данных осмотра
            ind = data.get("indicators", {})
            self.ad_input.setText(ind.get("ad", ""))
            self.temp_input.setText(ind.get("temp", ""))
            self.weight_input.setText(ind.get("weight", ""))
            
            add = data.get("additional", {})
            self.additional_block.set_data(add)
            
            comp = data.get("complaints_anamnesis", {})
            self.complaints_input.setPlainText(comp.get("complaints", ""))
            self.no_complaints_checkbox.setChecked(comp.get("no_complaints", False))
            self.anamnesis_input.setPlainText(comp.get("anamnesis", ""))
            self.show_anamnesis_label_checkbox.setChecked(comp.get("show_anamnesis_label", True))
            
            obj = data.get("objective", {})
            self.ad_ear_input.setPlainText(obj.get("ad_ear", ""))
            self.ad_ear_chk.setChecked(obj.get("ad_vis", True))
            self.as_ear_input.setPlainText(obj.get("as_ear", ""))
            self.as_ear_chk.setChecked(obj.get("as_vis", True))
            self.ad_as_combined_input.setPlainText(obj.get("ad_as_comb", ""))
            self.ad_as_combined_chk.setChecked(obj.get("ad_as_vis", True))
            self.chk_merge_ears.setChecked(obj.get("merge_ears", False))
            
            self.nasi_input.setPlainText(obj.get("nasi", ""))
            self.nasi_chk.setChecked(obj.get("nasi_vis", True))
            self.pharynx_input.setPlainText(obj.get("pharynx", ""))
            self.pharynx_chk.setChecked(obj.get("pharynx_vis", True))
            self.nasi_pharynx_combined_input.setPlainText(obj.get("nasi_pharynx_comb", ""))
            self.nasi_pharynx_combined_chk.setChecked(obj.get("nasi_pharynx_vis", True))
            self.chk_merge_nose_throat.setChecked(obj.get("merge_nose_throat", False))
            
            self.larynx_input.setPlainText(obj.get("larynx", ""))
            self.larynx_chk.setChecked(obj.get("larynx_vis", False))
            self.other_input.setPlainText(obj.get("other", ""))
            self.other_chk.setChecked(obj.get("other_vis", False))
            
            surd = data.get("surdology", {})
            self.surdology_block.set_data(surd)
            
            sl = data.get("sick_leave", {})
            self.sick_leave_block.set_data(sl)
            
            diag_data = data.get("diagnosis", {})
            if isinstance(diag_data, str):
                self.diagnosis_input.setHtml(diag_data)
                self.show_diagnosis_label_checkbox.setChecked(True)
                self.no_acute_pathology_checkbox.setChecked(False)
            else:
                self.diagnosis_input.setHtml(diag_data.get("text", ""))
                self.show_diagnosis_label_checkbox.setChecked(diag_data.get("show_label", True))
                self.no_acute_pathology_checkbox.setChecked(diag_data.get("no_acute_pathology", False))
            
            oth = data.get("other_data", {})
            self.repeat_chk.setChecked(oth.get("repeat", False))
            self.repeat_date_input.setText(oth.get("repeat_date", ""))
            self.repeat_time_input.setText(oth.get("repeat_time", ""))
            
            rec_data = data.get("recommendations", {})
            if isinstance(rec_data, str):
                self.rec_input.setHtml(rec_data)
                self.show_recommendations_label_checkbox.setChecked(True)
            else:
                self.rec_input.setHtml(rec_data.get("text", ""))
                self.show_recommendations_label_checkbox.setChecked(rec_data.get("show_label", True))
                
            self.signature_visible_checkbox.setChecked(data.get("signature_visible", False))

    def on_specialty_changed(self, text):
        self.specialtyChanged.emit(text)
        self.signature_label.setText(text)
        self.signature_visible_checkbox.setText(text)

    def toggle_ears_merge(self, state):
        merged = (state == Qt.CheckState.Checked.value)
        self.row_ad.setVisible(not merged)
        self.row_as.setVisible(not merged)
        self.row_ad_as_combined.setVisible(merged)

    def toggle_nose_throat_merge(self, state):
        merged = (state == Qt.CheckState.Checked.value)
        self.row_nasi.setVisible(not merged)
        self.row_pharynx.setVisible(not merged)
        self.row_nasi_pharynx_combined.setVisible(merged)

    def auto_check(self, checkbox, text_edit):
        if not checkbox.isChecked() and text_edit.toPlainText().strip():
            checkbox.setChecked(True)

    def emit_objective_changed(self):
        data = {
            "ad_ear": self.ad_ear_input.toPlainText(), "ad_vis": self.ad_ear_chk.isChecked(),
            "as_ear": self.as_ear_input.toPlainText(), "as_vis": self.as_ear_chk.isChecked(),
            "ad_as_comb": self.ad_as_combined_input.toPlainText(), "ad_as_vis": self.ad_as_combined_chk.isChecked(),
            "merge_ears": self.chk_merge_ears.isChecked(),
            
            "nasi": self.nasi_input.toPlainText(), "nasi_vis": self.nasi_chk.isChecked(),
            "pharynx": self.pharynx_input.toPlainText(), "pharynx_vis": self.pharynx_chk.isChecked(),
            "nasi_pharynx_comb": self.nasi_pharynx_combined_input.toPlainText(), "nasi_pharynx_vis": self.nasi_pharynx_combined_chk.isChecked(),
            "merge_nose_throat": self.chk_merge_nose_throat.isChecked(),
            
            "larynx": self.larynx_input.toPlainText(), "larynx_vis": self.larynx_chk.isChecked(),
            "other": self.other_input.toPlainText(), "other_vis": self.other_chk.isChecked()
        }
        self.objectiveChanged.emit(data)

    def toggle_repeat_fields(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.repeat_date_input.setEnabled(enabled)
        self.repeat_calendar_btn.setEnabled(enabled)
        self.repeat_time_input.setEnabled(enabled)
        self.repeatChanged.emit(enabled, self.repeat_date_input.text(), self.repeat_time_input.text())

    def show_repeat_calendar(self):
        menu = QMenu(self)
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.clicked.connect(lambda date: self.set_repeat_date_from_calendar(date, menu))
        
        action = QWidgetAction(menu)
        action.setDefaultWidget(calendar)
        menu.addAction(action)
        
        menu.exec(self.repeat_calendar_btn.mapToGlobal(QPoint(0, self.repeat_calendar_btn.height())))

    def set_repeat_date_from_calendar(self, date, menu):
        self.repeat_date_input.setText(date.toString("dd.MM.yyyy"))
        menu.close()

    def show_calendar(self):
        menu = QMenu(self)
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        calendar.clicked.connect(lambda date: self.set_date_from_calendar(date, menu))
        
        action = QWidgetAction(menu)
        action.setDefaultWidget(calendar)
        menu.addAction(action)
        
        menu.exec(self.calendar_btn.mapToGlobal(QPoint(0, self.calendar_btn.height())))

    def set_date_from_calendar(self, date, menu):
        self.date_input.setText(date.toString("dd.MM.yyyy"))
        menu.close()

    def on_time_checkbox_changed(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.time_input.setEnabled(enabled)
        self.timeEnabledChanged.emit(enabled)
        if enabled and not self.time_input.text():
             self.set_current_time()

    def append_anamnesis_text(self, text):
        current_text = self.anamnesis_input.toPlainText()
        if current_text:
            new_text = current_text + " " + text
        else:
            new_text = text
        self.anamnesis_input.setPlainText(new_text)

    def set_current_date(self):
        self.date_input.setText(QDate.currentDate().toString("dd.MM.yyyy"))

    def set_current_time(self):
        self.time_input.setText(QTime.currentTime().toString("HH:mm"))

    def toggle_surdology_visibility(self, visible):
        self.surdology_block.setVisible(visible)
        self.surdology_block.set_logical_enabled(visible)

    def toggle_sick_leave_visibility(self, visible):
        self.sick_leave_block.setVisible(visible)

    def save_mode_data(self, mode):
        """Сохраняет данные текущего режима в кэш."""
        data = {
            "diagnosis": {
                "text": self.diagnosis_input.toHtml(),
                "show_label": self.show_diagnosis_label_checkbox.isChecked(),
                "no_acute_pathology": self.no_acute_pathology_checkbox.isChecked()
            },
            "recommendations": {
                "text": self.rec_input.toHtml(),
                "show_label": self.show_recommendations_label_checkbox.isChecked()
            },
            "repeat": {
                "enabled": self.repeat_chk.isChecked(),
                "date": self.repeat_date_input.text(),
                "time": self.repeat_time_input.text()
            },
            "sick_leave": self.sick_leave_block.get_data(),
            # Сохраняем состояние видимости больничного листа
            "sick_leave_visible": self.sick_leave_checkbox.isChecked(),
            # Сохраняем данные персонала операции
            "op_staff": {
                "operator": self.operator_input.text(),
                "nurse": self.nurse_input.text()
            },
            # Сохраняем состояние видимости подписи
            "signature_visible": self.signature_visible_checkbox.isChecked()
        }
        self.mode_cache[mode] = data

    def load_mode_data(self, mode):
        """Загружает данные режима из кэша."""
        data = self.mode_cache.get(mode, {})
        
        # Диагноз
        diag = data.get("diagnosis", {})
        self.diagnosis_input.setHtml(diag.get("text", ""))
        self.show_diagnosis_label_checkbox.setChecked(diag.get("show_label", True))
        self.no_acute_pathology_checkbox.setChecked(diag.get("no_acute_pathology", False))
        
        # Рекомендации
        rec = data.get("recommendations", {})
        self.rec_input.setHtml(rec.get("text", ""))
        self.show_recommendations_label_checkbox.setChecked(rec.get("show_label", True))
        
        # Повторный прием
        rep = data.get("repeat", {})
        self.repeat_chk.setChecked(rep.get("enabled", False))
        self.repeat_date_input.setText(rep.get("date", ""))
        self.repeat_time_input.setText(rep.get("time", ""))
        
        # Больничный лист
        sl = data.get("sick_leave", {})
        self.sick_leave_block.set_data(sl)
        
        # Восстанавливаем видимость больничного листа
        sick_leave_visible = data.get("sick_leave_visible", False)
        self.sick_leave_checkbox.blockSignals(True)
        self.sick_leave_checkbox.setChecked(sick_leave_visible)
        self.sick_leave_checkbox.blockSignals(False)
        self.sick_leave_block.setVisible(sick_leave_visible)
        
        # Персонал операции
        op_staff = data.get("op_staff", {})
        self.operator_input.setText(op_staff.get("operator", ""))
        self.nurse_input.setText(op_staff.get("nurse", ""))
        
        # Видимость подписи
        signature_visible = data.get("signature_visible", False)
        self.signature_visible_checkbox.blockSignals(True)
        self.signature_visible_checkbox.setChecked(signature_visible)
        self.signature_visible_checkbox.blockSignals(False)

    def update_operation_staff_ui(self, operator, nurse):
        self.operator_input.blockSignals(True)
        self.nurse_input.blockSignals(True)
        self.operator_input.setText(operator)
        self.nurse_input.setText(nurse)
        self.operator_input.blockSignals(False)
        self.nurse_input.blockSignals(False)

    def toggle_operation_mode(self, state):
        is_operation = (state == Qt.CheckState.Checked.value)
        
        # Определяем текущий и предыдущий режимы
        current_mode = "operation" if is_operation else "examination"
        previous_mode = "examination" if is_operation else "operation"
        
        # 1. Сохраняем данные предыдущего режима
        self.save_mode_data(previous_mode)
        
        # 2. Загружаем данные текущего режима
        self.load_mode_data(current_mode)
        
        # Скрываем/показываем блоки
        self.indicators_complaints_container.setVisible(not is_operation)
        self.objective_frame.setVisible(not is_operation)
        self.operation_block.setVisible(is_operation)
        
        # Управление видимостью элементов блока Диагноз
        self.show_diagnosis_label_checkbox.setVisible(not is_operation)
        self.no_acute_pathology_checkbox.setVisible(not is_operation)
        self.op_staff_container.setVisible(is_operation)
        
        # Управление видимостью чекбокса подписи
        self.signature_visible_checkbox.setVisible(is_operation)
        self.signature_label.setVisible(not is_operation)
        
        # Если включена сурдология, скрываем её в режиме операции
        if is_operation:
             self.surdology_block.setVisible(False)
        else:
             # Восстанавливаем видимость сурдологии, если она была включена
             self.surdology_block.setVisible(self.additional_block.surdology_checkbox.isChecked())

        # Обновляем список шаблонов
        self.refresh_template_list()

        self.operationModeChanged.emit(is_operation)
        if is_operation:
            self.operationDataChanged.emit(self.operation_block.get_data())
            # Также эмитируем данные персонала
            self.operationStaffChanged.emit(self.operator_input.text(), self.nurse_input.text())
            # Эмитируем сигнал видимости подписи
            self.signatureVisibleChanged.emit(self.signature_visible_checkbox.isChecked())
            
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            self.last_focused_widget = obj
            if isinstance(obj, (QLineEdit, QTextEdit)):
                self.last_focused_text = obj.toPlainText() if isinstance(obj, QTextEdit) else obj.text()
        elif event.type() == QEvent.Type.FocusOut:
            if self.last_focused_widget == obj and isinstance(obj, (QLineEdit, QTextEdit)):
                new_text = obj.toPlainText() if isinstance(obj, QTextEdit) else obj.text()
                if self.last_focused_text != new_text:
                    if self.undo_stack:
                        command = TextChangeCommand(obj, self.last_focused_text, new_text, f"Изменение '{obj.objectName()}'")
                        self.undo_stack.push(command)
            self.last_focused_widget = None
        return super().eventFilter(obj, event)
        
    def install_event_filters(self):
        # Устанавливаем фильтры событий для отслеживания изменений
        widgets_to_track = [
            self.ad_input, self.temp_input, self.weight_input,
            self.complaints_input, self.anamnesis_input,
            self.ad_ear_input, self.as_ear_input, self.ad_as_combined_input,
            self.nasi_input, self.pharynx_input, self.nasi_pharynx_combined_input,
            self.larynx_input, self.other_input,
            self.diagnosis_input, self.rec_input,
            self.repeat_date_input, self.repeat_time_input,
            self.doctor_name_input,
            self.operator_input, self.nurse_input
        ]
        
        for widget in widgets_to_track:
            if widget:
                widget.installEventFilter(self)
                
        # Для чекбоксов используем stateChanged
        checkboxes = {
            self.time_checkbox: "Время",
            self.cito_checkbox: "Cito",
            self.no_card_checkbox: "Без карты",
            self.operation_checkbox: "Операция",
            self.no_complaints_checkbox: "Нет жалоб",
            self.show_anamnesis_label_checkbox: "Показывать 'Анамнез'",
            self.chk_merge_ears: "Объединить уши",
            self.chk_merge_nose_throat: "Объединить нос/глотку",
            self.show_diagnosis_label_checkbox: "Показывать 'Диагноз'",
            self.no_acute_pathology_checkbox: "Нет острой патологии",
            self.show_recommendations_label_checkbox: "Показывать 'Рекомендации'",
            self.repeat_chk: "Повторный прием",
            self.sick_leave_checkbox: "Больничный лист",
            self.signature_visible_checkbox: "Видимость подписи"
        }
        
        for chk, name in checkboxes.items():
            if chk:
                chk.stateChanged.connect(lambda state, w=chk, n=name: self.create_checkbox_command(w, state, n))

    def create_checkbox_command(self, widget, state, name):
        # Игнорируем, если стек неактивен (например, во время undo/redo)
        if self.undo_stack and self.undo_stack.isActive():
            # state - это Qt.CheckState.Checked.value или Qt.CheckState.Unchecked.value
            is_checked = (state == Qt.CheckState.Checked.value)
            command = CheckBoxCommand(widget, is_checked, f"Переключение '{name}'")
            self.undo_stack.push(command)
