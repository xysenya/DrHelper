from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QSizePolicy,
                             QCheckBox, QHBoxLayout, QLineEdit, QPushButton,
                             QRadioButton, QButtonGroup, QWidget, QToolButton)
from PyQt6.QtCore import Qt, pyqtSignal
from examinationextra import AutoResizingTextEdit, NormButton
import random

class OperationBlock(QWidget):
    # Сигнал передает словарь данных
    operationDataChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        # Основной layout контейнера
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10) # Отступ между блоками
        
        # Стиль для внутренних блоков (QFrame)
        block_style = """
            QFrame#StyledBlock {
                background-color: #333333;
                border: 1px solid #555;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background-color: transparent;
                color: #e0e0e0;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
                color: #e0e0e0;
            }
            QCheckBox {
                color: #e0e0e0;
                background-color: transparent;
                border: none;
            }
            QRadioButton {
                color: #e0e0e0;
                spacing: 5px;
                background-color: transparent;
                border: none;
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

        # ==========================================
        # БЛОК 1: ПРЕДОПЕРАЦИОННЫЙ ОСМОТР
        # ==========================================
        self.preop_frame = QFrame()
        self.preop_frame.setObjectName("StyledBlock")
        self.preop_frame.setStyleSheet(block_style)
        
        preop_layout = QVBoxLayout(self.preop_frame)
        preop_layout.setContentsMargins(10, 10, 10, 10)
        preop_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Заголовок
        preop_label = QLabel("ПРЕДОПЕРАЦИОННЫЙ ОСМОТР")
        preop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preop_label.setStyleSheet("color: #a0a0a0; font-size: 10pt; letter-spacing: 1px;")
        preop_layout.addWidget(preop_label)

        # 1. Текстовое поле "Жалобы и анамнез"
        complaints_anamnesis_label = QLabel("Жалобы и анамнез:")
        preop_layout.addWidget(complaints_anamnesis_label)
        self.complaints_anamnesis_input = AutoResizingTextEdit()
        self.complaints_anamnesis_input.setPlaceholderText("Введите жалобы и анамнез...")
        self.complaints_anamnesis_input.textChanged.connect(self.emit_data_changed)
        preop_layout.addWidget(self.complaints_anamnesis_input)

        # 2. Чекбокс "Пациент информирован"
        self.informed_checkbox = QCheckBox("Пациент информирован")
        self.informed_checkbox.setChecked(True) 
        self.informed_checkbox.stateChanged.connect(self.emit_data_changed)
        preop_layout.addWidget(self.informed_checkbox)

        # 3. Надпись "Общее состояние:" и радиокнопки
        general_condition_layout = QHBoxLayout()
        general_condition_layout.addWidget(QLabel("Общее состояние:"))
        
        self.general_condition_group = QButtonGroup(self)
        self.rb_satisfactory = QRadioButton("Удовлетворительное")
        self.rb_medium = QRadioButton("Средней степени тяжести")
        self.rb_severe = QRadioButton("Тяжелое")

        self.general_condition_group.addButton(self.rb_satisfactory)
        self.general_condition_group.addButton(self.rb_medium)
        self.general_condition_group.addButton(self.rb_severe)

        self.rb_satisfactory.setChecked(True)
        
        self.general_condition_group.buttonClicked.connect(self.emit_data_changed)

        general_condition_layout.addWidget(self.rb_satisfactory)
        general_condition_layout.addWidget(self.rb_medium)
        general_condition_layout.addWidget(self.rb_severe)
        general_condition_layout.addStretch()
        preop_layout.addLayout(general_condition_layout)

        # 4. Надпись "Показатели:" и текстовые поля с кнопками "N"
        indicators_layout = QHBoxLayout()
        indicators_layout.addWidget(QLabel("Показатели:"))
        
        # АД
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderText("АД (120/80)")
        self.ad_input.setFixedWidth(80)
        self.ad_input.textChanged.connect(self.emit_data_changed)
        btn_ad_norm = NormButton("130/80")
        btn_ad_norm.insertTextChanged.connect(self.ad_input.setText)
        indicators_layout.addWidget(self.ad_input)
        indicators_layout.addWidget(btn_ad_norm)

        # Пульс
        self.pulse_input = QLineEdit()
        self.pulse_input.setPlaceholderText("Пульс (80)")
        self.pulse_input.setFixedWidth(60)
        self.pulse_input.textChanged.connect(self.emit_data_changed)
        btn_pulse_norm = NormButton("") 
        btn_pulse_norm.insertTextChanged.connect(self.pulse_input.setText)
        btn_pulse_norm.clicked.connect(lambda: self.pulse_input.setText(random.choice(["70", "75", "80"])))
        indicators_layout.addWidget(self.pulse_input)
        indicators_layout.addWidget(btn_pulse_norm)

        # t°
        self.temp_input = QLineEdit()
        self.temp_input.setPlaceholderText("t° (36,6)")
        self.temp_input.setFixedWidth(60)
        self.temp_input.textChanged.connect(self.emit_data_changed)
        btn_temp_norm = NormButton("36,7")
        btn_temp_norm.insertTextChanged.connect(self.temp_input.setText)
        indicators_layout.addWidget(self.temp_input)
        indicators_layout.addWidget(btn_temp_norm)
        
        indicators_layout.addStretch()
        preop_layout.addLayout(indicators_layout)

        # 5. Текстовое поле "Объективный осмотр:"
        objective_examination_label = QLabel("Объективный осмотр:")
        preop_layout.addWidget(objective_examination_label)
        self.objective_examination_input = AutoResizingTextEdit()
        self.objective_examination_input.setPlaceholderText("Введите данные объективного осмотра...")
        self.objective_examination_input.textChanged.connect(self.emit_data_changed)
        preop_layout.addWidget(self.objective_examination_input)

        # 6. Надпись "Показанное вмешательство:" и текстовое поле
        intervention_layout = QHBoxLayout()
        intervention_layout.addWidget(QLabel("Показанное вмешательство:"))
        self.intervention_input = AutoResizingTextEdit()
        self.intervention_input.setPlaceholderText("Введите название вмешательства...")
        self.intervention_input.textChanged.connect(self.emit_data_changed)
        intervention_layout.addWidget(self.intervention_input)
        preop_layout.addLayout(intervention_layout)

        # 7. Чекбокс "Согласие получено"
        self.intervention_consent_checkbox = QCheckBox("Согласие получено")
        self.intervention_consent_checkbox.setChecked(True)
        self.intervention_consent_checkbox.stateChanged.connect(self.emit_data_changed)
        preop_layout.addWidget(self.intervention_consent_checkbox)

        main_layout.addWidget(self.preop_frame)

        # ==========================================
        # БЛОК 2: ОПЕРАТИВНОЕ ВМЕШАТЕЛЬСТВО
        # ==========================================
        self.intervention_frame = QFrame()
        self.intervention_frame.setObjectName("StyledBlock")
        self.intervention_frame.setStyleSheet(block_style)
        
        interv_layout = QVBoxLayout(self.intervention_frame)
        interv_layout.setContentsMargins(10, 10, 10, 10)
        interv_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Номер операции (Центрирование: Stretch + Label + Input + Stretch)
        op_num_layout = QHBoxLayout()
        op_num_layout.addStretch() # Толкаем слева
        
        op_num_label = QLabel("Оперативное вмешательство №")
        op_num_layout.addWidget(op_num_label)
        
        self.op_number_input = QLineEdit()
        self.op_number_input.setFixedWidth(50)
        self.op_number_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.op_number_input.textChanged.connect(self.emit_data_changed)
        op_num_layout.addWidget(self.op_number_input)
        
        op_num_layout.addStretch() # Толкаем справа
        
        interv_layout.addLayout(op_num_layout)

        # Название операции
        self.op_name_input = QLineEdit()
        self.op_name_input.setPlaceholderText("Название оперативного вмешательства")
        self.op_name_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.op_name_input.textChanged.connect(self.emit_data_changed)
        interv_layout.addWidget(self.op_name_input)

        # Описание операции
        interv_layout.addWidget(QLabel("Описание операции:"))
        self.op_description_input = AutoResizingTextEdit()
        self.op_description_input.setPlaceholderText("Ход операции...")
        self.op_description_input.textChanged.connect(self.emit_data_changed)
        interv_layout.addWidget(self.op_description_input)

        main_layout.addWidget(self.intervention_frame)
        main_layout.addStretch()
        
    def emit_data_changed(self):
        # Блокируем сигналы, чтобы избежать зацикливания при обновлении извне
        self.operationDataChanged.emit(self.get_data())

    def get_data(self):
        general_condition = ""
        if self.rb_satisfactory.isChecked():
            general_condition = self.rb_satisfactory.text()
        elif self.rb_medium.isChecked():
            general_condition = self.rb_medium.text()
        elif self.rb_severe.isChecked():
            general_condition = self.rb_severe.text()

        return {
            "complaints_anamnesis": self.complaints_anamnesis_input.toPlainText(),
            "informed_consent": self.informed_checkbox.isChecked(),
            "general_condition": general_condition,
            "ad": self.ad_input.text(),
            "pulse": self.pulse_input.text(),
            "temp": self.temp_input.text(),
            "objective_examination": self.objective_examination_input.toPlainText(),
            "intervention": self.intervention_input.toPlainText(),
            "intervention_consent": self.intervention_consent_checkbox.isChecked(),
            # Новые поля
            "op_number": self.op_number_input.text(),
            "op_name": self.op_name_input.text(),
            "op_description": self.op_description_input.toPlainText()
        }

    def set_data(self, data):
        # Блокируем сигналы всех виджетов ввода, чтобы предотвратить рекурсию
        widgets = [
            self.complaints_anamnesis_input,
            self.informed_checkbox,
            self.ad_input,
            self.pulse_input,
            self.temp_input,
            self.objective_examination_input,
            self.intervention_input,
            self.intervention_consent_checkbox,
            self.op_number_input,
            self.op_name_input,
            self.op_description_input
        ]
        
        # Также блокируем радиокнопки
        for btn in self.general_condition_group.buttons():
            widgets.append(btn)
            
        for w in widgets:
            w.blockSignals(True)
            
        try:
            self.complaints_anamnesis_input.setPlainText(data.get("complaints_anamnesis", ""))
            self.informed_checkbox.setChecked(data.get("informed_consent", True))
            
            general_condition = data.get("general_condition", "Удовлетворительное")
            if general_condition == "Удовлетворительное":
                self.rb_satisfactory.setChecked(True)
            elif general_condition == "Средней степени тяжести":
                self.rb_medium.setChecked(True)
            elif general_condition == "Тяжелое":
                self.rb_severe.setChecked(True)
            
            self.ad_input.setText(data.get("ad", ""))
            self.pulse_input.setText(data.get("pulse", ""))
            self.temp_input.setText(data.get("temp", ""))
            self.objective_examination_input.setPlainText(data.get("objective_examination", ""))
            self.intervention_input.setPlainText(data.get("intervention", ""))
            self.intervention_consent_checkbox.setChecked(data.get("intervention_consent", True))
            
            # Новые поля
            self.op_number_input.setText(data.get("op_number", ""))
            self.op_name_input.setText(data.get("op_name", ""))
            self.op_description_input.setPlainText(data.get("op_description", ""))
        finally:
            for w in widgets:
                w.blockSignals(False)

    def clear(self):
        # Блокируем сигналы всех виджетов ввода
        widgets = [
            self.complaints_anamnesis_input,
            self.informed_checkbox,
            self.ad_input,
            self.pulse_input,
            self.temp_input,
            self.objective_examination_input,
            self.intervention_input,
            self.intervention_consent_checkbox,
            self.op_number_input,
            self.op_name_input,
            self.op_description_input
        ]
        
        for btn in self.general_condition_group.buttons():
            widgets.append(btn)
            
        for w in widgets:
            w.blockSignals(True)
            
        try:
            self.complaints_anamnesis_input.clear()
            self.informed_checkbox.setChecked(True)
            self.rb_satisfactory.setChecked(True)
            self.ad_input.clear()
            self.pulse_input.clear()
            self.temp_input.clear()
            self.objective_examination_input.clear()
            self.intervention_input.clear()
            self.intervention_consent_checkbox.setChecked(True)
            
            # Новые поля
            self.op_number_input.clear()
            self.op_name_input.clear()
            self.op_description_input.clear()
        finally:
            for w in widgets:
                w.blockSignals(False)
