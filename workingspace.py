from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QToolButton, QCalendarWidget, 
                             QWidgetAction, QMenu, QComboBox, QSizePolicy, QCheckBox, QPushButton,
                             QTextEdit, QGridLayout, QDialog, QDialogButtonBox, QWidget,
                             QStylePainter, QStyleOptionComboBox, QStyle, QRadioButton, QButtonGroup,
                             QScrollArea, QMessageBox, QInputDialog, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QSize, QRect, QPoint, QTimer
from PyQt6.QtGui import QAction, QCursor, QIcon, QColor, QPalette
import os
import json

# Импортируем новые блоки
from examinationextra import SurdologyBlock, SickLeaveBlock, AdditionalBlock, DateInput, TimeInput, SymbolComboBox, EditableButton, NormButton, AutoResizingTextEdit, TemplateManagerDialog
from examination import ExaminationPanel

class WorkingSpacePanel(QFrame):
    # Сигналы, которые пробрасываются из ExaminationPanel
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
    repeatChanged = pyqtSignal(bool, str, str)
    
    sickLeaveChanged = pyqtSignal(dict)
    
    signatureChanged = pyqtSignal(str)
    
    surdologyChanged = pyqtSignal(dict)
    
    operationDataChanged = pyqtSignal(dict)
    operationModeChanged = pyqtSignal(bool)
    
    # Новый сигнал для персонала операции
    operationStaffChanged = pyqtSignal(str, str)
    
    # Сигнал видимости подписи
    signatureVisibleChanged = pyqtSignal(bool)
    
    # Сигналы для нижней панели
    saveRequested = pyqtSignal(bool) # Изменено: передает состояние чекбокса открытия
    copyRequested = pyqtSignal()
    printRequested = pyqtSignal()

    def __init__(self, undo_stack=None):
        super().__init__()
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Создаем и добавляем ExaminationPanel, передавая стек
        self.examination_panel = ExaminationPanel(undo_stack=undo_stack)
        main_layout.addWidget(self.examination_panel)
        
        # --- Нижняя панель с кнопками ---
        self.bottom_panel = QFrame()
        self.bottom_panel.setStyleSheet("""
            QFrame {
                background-color: #3c3f41; 
                border-top: 1px solid #555;
            }
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #606364;
            }
            QPushButton:pressed {
                background-color: #4a90e2;
            }
            QCheckBox {
                color: #e0e0e0;
            }
        """)
        self.bottom_panel.setFixedHeight(50)
        bottom_layout = QHBoxLayout(self.bottom_panel)
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        
        # Кнопка Сохранить
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.on_save_clicked)
        bottom_layout.addWidget(self.btn_save)
        
        # Чекбокс "Открыть после сохранения"
        self.chk_open_after_save = QCheckBox("Открыть после сохранения")
        self.chk_open_after_save.setToolTip("Открыть файл после сохранения")
        self.chk_open_after_save.setStyleSheet("margin-left: 5px;")
        bottom_layout.addWidget(self.chk_open_after_save)
        
        bottom_layout.addStretch()
        
        # Кнопка Копировать
        self.btn_copy = QPushButton("Копировать")
        self.btn_copy.clicked.connect(self.copyRequested.emit)
        bottom_layout.addWidget(self.btn_copy)
        
        # Кнопка Печать
        self.btn_print = QPushButton("Печать")
        self.btn_print.clicked.connect(self.printRequested.emit)
        bottom_layout.addWidget(self.btn_print)
        
        main_layout.addWidget(self.bottom_panel)
        
        # Пробрасываем все сигналы от examination_panel
        self.examination_panel.dateChanged.connect(self.dateChanged)
        self.examination_panel.specialtyChanged.connect(self.specialtyChanged)
        self.examination_panel.timeChanged.connect(self.timeChanged)
        self.examination_panel.timeEnabledChanged.connect(self.timeEnabledChanged)
        self.examination_panel.citoChanged.connect(self.citoChanged)
        self.examination_panel.noCardChanged.connect(self.noCardChanged)
        self.examination_panel.adChanged.connect(self.adChanged)
        self.examination_panel.tempChanged.connect(self.tempChanged)
        self.examination_panel.weightChanged.connect(self.weightChanged)
        self.examination_panel.complaintsChanged.connect(self.complaintsChanged)
        self.examination_panel.anamnesisChanged.connect(self.anamnesisChanged)
        self.examination_panel.noComplaintsChanged.connect(self.noComplaintsChanged)
        self.examination_panel.showAnamnesisLabelChanged.connect(self.showAnamnesisLabelChanged)
        self.examination_panel.paidServiceChanged.connect(self.paidServiceChanged)
        self.examination_panel.consentChanged.connect(self.consentChanged)
        self.examination_panel.objectiveChanged.connect(self.objectiveChanged)
        self.examination_panel.diagnosisChanged.connect(self.diagnosisChanged)
        self.examination_panel.showDiagnosisLabelChanged.connect(self.showDiagnosisLabelChanged)
        self.examination_panel.noAcutePathologyChanged.connect(self.noAcutePathologyChanged)
        self.examination_panel.recommendationsChanged.connect(self.recommendationsChanged)
        self.examination_panel.showRecommendationsLabelChanged.connect(self.showRecommendationsLabelChanged)
        self.examination_panel.repeatChanged.connect(self.repeatChanged)
        self.examination_panel.sickLeaveChanged.connect(self.sickLeaveChanged)
        self.examination_panel.signatureChanged.connect(self.signatureChanged)
        self.examination_panel.surdologyChanged.connect(self.surdologyChanged)
        self.examination_panel.operationDataChanged.connect(self.operationDataChanged)
        self.examination_panel.operationModeChanged.connect(self.operationModeChanged)
        self.examination_panel.operationStaffChanged.connect(self.operationStaffChanged)
        self.examination_panel.signatureVisibleChanged.connect(self.signatureVisibleChanged)

        # Делаем дочерние виджеты доступными для MainWindow
        self.date_input = self.examination_panel.date_input
        self.time_input = self.examination_panel.time_input
        self.time_checkbox = self.examination_panel.time_checkbox
        self.specialty_combo = self.examination_panel.specialty_combo
        self.ad_input = self.examination_panel.ad_input
        self.temp_input = self.examination_panel.temp_input
        self.weight_input = self.examination_panel.weight_input
        self.complaints_input = self.examination_panel.complaints_input
        self.anamnesis_input = self.examination_panel.anamnesis_input
        self.no_complaints_checkbox = self.examination_panel.no_complaints_checkbox
        self.show_anamnesis_label_checkbox = self.examination_panel.show_anamnesis_label_checkbox
        self.additional_block = self.examination_panel.additional_block
        self.cito_checkbox = self.examination_panel.cito_checkbox
        self.no_card_checkbox = self.examination_panel.no_card_checkbox
        self.ad_ear_input = self.examination_panel.ad_ear_input
        self.as_ear_input = self.examination_panel.as_ear_input
        self.ad_as_combined_input = self.examination_panel.ad_as_combined_input
        self.nasi_input = self.examination_panel.nasi_input
        self.pharynx_input = self.examination_panel.pharynx_input
        self.nasi_pharynx_combined_input = self.examination_panel.nasi_pharynx_combined_input
        self.larynx_input = self.examination_panel.larynx_input
        self.other_input = self.examination_panel.other_input
        self.ad_ear_chk = self.examination_panel.ad_ear_chk
        self.as_ear_chk = self.examination_panel.as_ear_chk
        self.ad_as_combined_chk = self.examination_panel.ad_as_combined_chk
        self.chk_merge_ears = self.examination_panel.chk_merge_ears
        self.nasi_chk = self.examination_panel.nasi_chk
        self.pharynx_chk = self.examination_panel.pharynx_chk
        self.nasi_pharynx_combined_chk = self.examination_panel.nasi_pharynx_combined_chk
        self.chk_merge_nose_throat = self.examination_panel.chk_merge_nose_throat
        self.larynx_chk = self.examination_panel.larynx_chk
        self.other_chk = self.examination_panel.other_chk
        self.diagnosis_input = self.examination_panel.diagnosis_input
        self.show_diagnosis_label_checkbox = self.examination_panel.show_diagnosis_label_checkbox
        self.no_acute_pathology_checkbox = self.examination_panel.no_acute_pathology_checkbox
        self.rec_input = self.examination_panel.rec_input
        self.repeat_chk = self.examination_panel.repeat_chk
        self.repeat_date_input = self.examination_panel.repeat_date_input
        self.repeat_time_input = self.examination_panel.repeat_time_input
        self.doctor_name_input = self.examination_panel.doctor_name_input
        self.surdology_block = self.examination_panel.surdology_block
        self.sick_leave_block = self.examination_panel.sick_leave_block
        self.show_recommendations_label_checkbox = self.examination_panel.show_recommendations_label_checkbox
        self.operation_block = self.examination_panel.operation_block
        self.operation_checkbox = self.examination_panel.operation_checkbox

    def on_save_clicked(self):
        self.saveRequested.emit(self.chk_open_after_save.isChecked())

    def update_operation_ui(self, data):
        self.examination_panel.operation_block.set_data(data)

    def update_operation_staff_ui(self, operator, nurse):
        self.examination_panel.update_operation_staff_ui(operator, nurse)
