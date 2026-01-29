import sys
import os
import configparser
import faulthandler
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter, 
                             QFrame, QLineEdit, QTextEdit, QDialog, QVBoxLayout, 
                             QTextBrowser, QPushButton)
from PyQt6.QtCore import Qt, QEvent, QUrl
from PyQt6.QtGui import QAction, QIcon, QUndoStack, QKeySequence, QKeyEvent

# Включаем обработчик ошибок для отладки крашей
faulthandler.enable()

# Импортируем наши новые модули
from paperspace import EditorPanel, A4Editor
from workingspace import WorkingSpacePanel

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: #2b2b2b; color: #e0e0e0;")

        layout = QVBoxLayout(self)

        text_browser = QTextBrowser()
        text_browser.setStyleSheet("background-color: #3c3f41; border: 1px solid #555;")
        
        # Загрузка контента из файла
        signa_path = os.path.join(os.path.dirname(__file__), "Hints", "signa.html")
        if os.path.exists(signa_path):
            try:
                # Сначала пробуем utf-8
                with open(signa_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                text_browser.setHtml(html_content)
            except UnicodeDecodeError:
                try:
                    # Если не вышло, пробуем cp1251
                    with open(signa_path, 'r', encoding='cp1251') as f:
                        html_content = f.read()
                    text_browser.setHtml(html_content)
                except Exception as e:
                    text_browser.setText(f"Ошибка при чтении файла справки (cp1251): {e}")
            except Exception as e:
                text_browser.setText(f"Ошибка при чтении файла справки: {e}")
        else:
            text_browser.setText("Файл справки 'signa.html' не найден.")
            
        layout.addWidget(text_browser)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Спасибо!")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #606364;
            }
        """)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DrHelper")
        self.resize(1200, 800)
        
        # Установка иконки окна
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # --- Инициализация стека отмены ---
        self.undo_stack = QUndoStack(self)
        
        # --- Создание верхнего меню ---
        self.create_menu_bar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель (Рабочая область)
        # Передаем undo_stack в WorkingSpacePanel
        self.work_area = WorkingSpacePanel(undo_stack=self.undo_stack)
        self.splitter.addWidget(self.work_area)
        
        # Правая панель (Редактор документов)
        self.editor_panel = EditorPanel()
        self.splitter.addWidget(self.editor_panel)
        
        # Связываем сигналы (UI -> Editor)
        self.work_area.dateChanged.connect(self.editor_panel.set_date)
        self.work_area.timeChanged.connect(self.editor_panel.set_time)
        self.work_area.timeEnabledChanged.connect(self.editor_panel.set_time_enabled)
        self.work_area.specialtyChanged.connect(self.editor_panel.set_specialty)
        
        self.work_area.adChanged.connect(self.editor_panel.set_ad)
        self.work_area.tempChanged.connect(self.editor_panel.set_temp)
        self.work_area.weightChanged.connect(self.editor_panel.set_weight)
        self.work_area.complaintsChanged.connect(self.editor_panel.set_complaints)
        self.work_area.anamnesisChanged.connect(self.editor_panel.set_anamnesis)
        
        self.work_area.noComplaintsChanged.connect(self.editor_panel.set_no_complaints)
        self.work_area.showAnamnesisLabelChanged.connect(self.editor_panel.set_show_anamnesis_label)
        
        self.work_area.paidServiceChanged.connect(self.editor_panel.set_paid_service)
        self.work_area.consentChanged.connect(self.editor_panel.set_consent)
        
        self.work_area.citoChanged.connect(self.editor_panel.set_cito)
        self.work_area.noCardChanged.connect(self.editor_panel.set_no_card)
        
        self.work_area.objectiveChanged.connect(self.editor_panel.set_objective)
        self.work_area.surdologyChanged.connect(self.editor_panel.set_surdology)
        self.work_area.diagnosisChanged.connect(self.editor_panel.set_diagnosis)
        self.work_area.showDiagnosisLabelChanged.connect(self.editor_panel.set_show_diagnosis_label)
        self.work_area.noAcutePathologyChanged.connect(self.editor_panel.set_no_acute_pathology)
        self.work_area.recommendationsChanged.connect(self.editor_panel.set_recommendations)
        self.work_area.showRecommendationsLabelChanged.connect(self.editor_panel.set_show_recommendations_label)
        self.work_area.repeatChanged.connect(self.editor_panel.set_repeat)
        self.work_area.sickLeaveChanged.connect(self.editor_panel.set_sick_leave)
        self.work_area.signatureChanged.connect(self.editor_panel.set_signature)
        
        self.work_area.operationModeChanged.connect(self.editor_panel.set_operation_mode)
        self.work_area.operationDataChanged.connect(self.editor_panel.set_operation_data)
        
        # Связываем новый сигнал для персонала операции
        self.work_area.operationStaffChanged.connect(self.editor_panel.set_operation_staff)
        
        # Связываем сигнал видимости подписи
        self.work_area.signatureVisibleChanged.connect(self.editor_panel.set_signature_visible)
        
        # Связываем сигналы для нижней панели
        self.work_area.saveRequested.connect(self.editor_panel.save_to_file)
        self.work_area.copyRequested.connect(self.editor_panel.copy_content)
        self.work_area.printRequested.connect(self.editor_panel.print_preview)
        
        # Связываем сигналы (Editor -> UI)
        self.editor_panel.dateChangedFromEditor.connect(self.update_date_ui)
        self.editor_panel.indicatorsChangedFromEditor.connect(self.update_indicators_ui)
        self.editor_panel.complaintsAnamnesisChangedFromEditor.connect(self.update_complaints_anamnesis_ui)
        self.editor_panel.objectiveChangedFromEditor.connect(self.update_objective_ui)
        self.editor_panel.diagnosisChangedFromEditor.connect(self.update_diagnosis_ui)
        self.editor_panel.recommendationsChangedFromEditor.connect(self.update_recommendations_ui)
        self.editor_panel.repeatChangedFromEditor.connect(self.update_repeat_ui)
        self.editor_panel.sickLeaveChangedFromEditor.connect(self.update_sick_leave_ui) # Добавлено
        self.editor_panel.signatureChangedFromEditor.connect(self.update_signature_ui)
        self.editor_panel.operationDataChangedFromEditor.connect(self.work_area.update_operation_ui)
        self.editor_panel.operationStaffChangedFromEditor.connect(self.work_area.update_operation_staff_ui) # Добавлено
        
        main_layout.addWidget(self.splitter)
        
        # Инициализация
        self.editor_panel.set_date(self.work_area.date_input.text())
        self.editor_panel.set_time(self.work_area.time_input.text())
        self.editor_panel.set_time_enabled(self.work_area.time_checkbox.isChecked())
        self.editor_panel.set_specialty(self.work_area.specialty_combo.currentText())
        
        self.editor_panel.set_ad("")
        self.editor_panel.set_temp("")
        self.editor_panel.set_weight("")
        self.editor_panel.set_complaints("")
        self.editor_panel.set_anamnesis("")
        
        self.editor_panel.set_objective({
            "ad_ear": "", "ad_vis": True,
            "as_ear": "", "as_vis": True,
            "ad_as_comb": "", "ad_as_vis": True,
            "merge_ears": False,
            "nasi": "", "nasi_vis": True,
            "pharynx": "", "pharynx_vis": True,
            "nasi_pharynx_comb": "", "nasi_pharynx_vis": True,
            "merge_nose_throat": False,
            "larynx": "", "larynx_vis": False,
            "other": "", "other_vis": False
        })
        
        self.editor_panel.set_surdology({
            "enabled": False
        })
        
        self.editor_panel.set_diagnosis("")
        self.editor_panel.set_recommendations("")
        self.editor_panel.set_repeat(False, "", "")
        
        # Инициализация флагов
        self.editor_panel.set_no_complaints(self.work_area.no_complaints_checkbox.isChecked())
        self.editor_panel.set_show_anamnesis_label(self.work_area.show_anamnesis_label_checkbox.isChecked())
        self.editor_panel.set_paid_service(self.work_area.additional_block.paid_checkbox.isChecked())
        self.editor_panel.set_consent(self.work_area.additional_block.consent_checkbox.isChecked())
        self.editor_panel.set_cito(self.work_area.cito_checkbox.isChecked())
        self.editor_panel.set_no_card(self.work_area.no_card_checkbox.isChecked())
        self.editor_panel.set_signature(self.work_area.doctor_name_input.text())
        self.editor_panel.set_show_recommendations_label(self.work_area.show_recommendations_label_checkbox.isChecked())
        
        # Инициализация видимости блоков
        self.work_area.surdology_block.setVisible(self.work_area.additional_block.surdology_checkbox.isChecked())
        
        # Исправленная строка: обращаемся к чекбоксу через examination_panel
        self.work_area.sick_leave_block.setVisible(self.work_area.examination_panel.sick_leave_checkbox.isChecked())
        
        # Инициализация режима операции
        self.editor_panel.set_operation_mode(self.work_area.operation_checkbox.isChecked())
        self.editor_panel.set_operation_data(self.work_area.operation_block.get_data())
        
        # Загрузка настроек
        self.load_settings()
        
        # Устанавливаем фильтр событий на приложение для перехвата клавиш
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if key == Qt.Key.Key_Z:
                    # Если фокус в текстовом поле (включая редактор), пропускаем событие
                    # чтобы виджет сам его обработал
                    if self.is_text_input_focused():
                        return False 
                    
                    # Иначе обрабатываем нашим стеком
                    self.undo_stack.undo()
                    return True
                    
                elif key == Qt.Key.Key_Y:
                    if self.is_text_input_focused():
                        return False
                    
                    self.undo_stack.redo()
                    return True
                    
        return super().eventFilter(obj, event)

    def is_text_input_focused(self):
        focus_widget = QApplication.focusWidget()
        if focus_widget and isinstance(focus_widget, (QLineEdit, QTextEdit)):
            return True
        return False

    def update_date_ui(self, date):
        self.work_area.date_input.blockSignals(True)
        self.work_area.date_input.setText(date)
        self.work_area.date_input.blockSignals(False)

    def update_signature_ui(self, text):
        self.work_area.doctor_name_input.blockSignals(True)
        self.work_area.doctor_name_input.setText(text)
        self.work_area.doctor_name_input.blockSignals(False)

    def update_indicators_ui(self, ad, temp, weight):
        # Блокируем сигналы, чтобы не вызвать зацикливание
        self.work_area.ad_input.blockSignals(True)
        self.work_area.temp_input.blockSignals(True)
        self.work_area.weight_input.blockSignals(True)
        
        self.work_area.ad_input.setText(ad)
        self.work_area.temp_input.setText(temp)
        self.work_area.weight_input.setText(weight)
        
        self.work_area.ad_input.blockSignals(False)
        self.work_area.temp_input.blockSignals(False)
        self.work_area.weight_input.blockSignals(False)

    def update_complaints_anamnesis_ui(self, complaints, anamnesis):
        self.work_area.complaints_input.blockSignals(True)
        self.work_area.anamnesis_input.blockSignals(True)
        
        self.work_area.complaints_input.setText(complaints)
        self.work_area.anamnesis_input.setText(anamnesis)
        
        self.work_area.complaints_input.blockSignals(False)
        self.work_area.anamnesis_input.blockSignals(False)
        
    def update_objective_ui(self, data):
        # Блокируем сигналы текстовых полей
        self.work_area.ad_ear_input.blockSignals(True)
        self.work_area.as_ear_input.blockSignals(True)
        self.work_area.ad_as_combined_input.blockSignals(True)
        self.work_area.nasi_input.blockSignals(True)
        self.work_area.pharynx_input.blockSignals(True)
        self.work_area.nasi_pharynx_combined_input.blockSignals(True)
        self.work_area.larynx_input.blockSignals(True)
        self.work_area.other_input.blockSignals(True)
        
        # Блокируем сигналы чекбоксов
        self.work_area.ad_ear_chk.blockSignals(True)
        self.work_area.as_ear_chk.blockSignals(True)
        self.work_area.ad_as_combined_chk.blockSignals(True)
        self.work_area.chk_merge_ears.blockSignals(True)
        
        self.work_area.nasi_chk.blockSignals(True)
        self.work_area.pharynx_chk.blockSignals(True)
        self.work_area.nasi_pharynx_combined_chk.blockSignals(True)
        self.work_area.chk_merge_nose_throat.blockSignals(True)
        
        self.work_area.larynx_chk.blockSignals(True)
        self.work_area.other_chk.blockSignals(True)
        
        # Обновляем текст
        self.work_area.ad_ear_input.setPlainText(data.get("ad_ear", ""))
        self.work_area.as_ear_input.setPlainText(data.get("as_ear", ""))
        self.work_area.ad_as_combined_input.setPlainText(data.get("ad_as_comb", ""))
        self.work_area.nasi_input.setPlainText(data.get("nasi", ""))
        self.work_area.pharynx_input.setPlainText(data.get("pharynx", ""))
        self.work_area.nasi_pharynx_combined_input.setPlainText(data.get("nasi_pharynx_comb", ""))
        self.work_area.larynx_input.setPlainText(data.get("larynx", ""))
        self.work_area.other_input.setPlainText(data.get("other", ""))
        
        # Обновляем чекбоксы
        self.work_area.ad_ear_chk.setChecked(data.get("ad_vis", False))
        self.work_area.as_ear_chk.setChecked(data.get("as_vis", False))
        self.work_area.ad_as_combined_chk.setChecked(data.get("ad_as_vis", False))
        self.work_area.chk_merge_ears.setChecked(data.get("merge_ears", False))
        
        self.work_area.nasi_chk.setChecked(data.get("nasi_vis", False))
        self.work_area.pharynx_chk.setChecked(data.get("pharynx_vis", False))
        self.work_area.nasi_pharynx_combined_chk.setChecked(data.get("nasi_pharynx_vis", False))
        self.work_area.chk_merge_nose_throat.setChecked(data.get("merge_nose_throat", False))
        
        self.work_area.larynx_chk.setChecked(data.get("larynx_vis", False))
        self.work_area.other_chk.setChecked(data.get("other_vis", False))
        
        # Разблокируем сигналы
        self.work_area.ad_ear_input.blockSignals(False)
        self.work_area.as_ear_input.blockSignals(False)
        self.work_area.ad_as_combined_input.blockSignals(False)
        self.work_area.nasi_input.blockSignals(False)
        self.work_area.pharynx_input.blockSignals(False)
        self.work_area.nasi_pharynx_combined_input.blockSignals(False)
        self.work_area.larynx_input.blockSignals(False)
        self.work_area.other_input.blockSignals(False)
        
        self.work_area.ad_ear_chk.blockSignals(False)
        self.work_area.as_ear_chk.blockSignals(False)
        self.work_area.ad_as_combined_chk.blockSignals(False)
        self.work_area.chk_merge_ears.blockSignals(False)
        
        self.work_area.nasi_chk.blockSignals(False)
        self.work_area.pharynx_chk.blockSignals(False)
        self.work_area.nasi_pharynx_combined_chk.blockSignals(False)
        self.work_area.chk_merge_nose_throat.blockSignals(False)
        
        self.work_area.larynx_chk.blockSignals(False)
        self.work_area.other_chk.blockSignals(False)

    def update_diagnosis_ui(self, diagnosis):
        self.work_area.diagnosis_input.blockSignals(True)
        # Используем setHtml для поддержки форматирования, если оно есть
        # Но для диагноза мы пока не добавляли кнопки, так что можно оставить setText или setHtml
        # Если diagnosis содержит HTML теги, лучше setHtml
        if "<html>" in diagnosis or "<p>" in diagnosis:
             self.work_area.diagnosis_input.setHtml(diagnosis)
        else:
             self.work_area.diagnosis_input.setText(diagnosis)
        self.work_area.diagnosis_input.blockSignals(False)
        
    def update_recommendations_ui(self, recommendations):
        self.work_area.rec_input.blockSignals(True)
        # Используем setHtml для поддержки форматирования (списков)
        self.work_area.rec_input.setHtml(recommendations)
        self.work_area.rec_input.blockSignals(False)
        
    def update_repeat_ui(self, enabled, date, time):
        self.work_area.repeat_chk.blockSignals(True)
        self.work_area.repeat_date_input.blockSignals(True)
        self.work_area.repeat_time_input.blockSignals(True)
        
        self.work_area.repeat_chk.setChecked(enabled)
        self.work_area.repeat_date_input.setText(date)
        self.work_area.repeat_time_input.setText(time)
        
        self.work_area.repeat_chk.blockSignals(False)
        self.work_area.repeat_date_input.blockSignals(False)
        self.work_area.repeat_time_input.blockSignals(False)

    def update_sick_leave_ui(self, data):
        # Блокируем сигналы виджета больничного листа
        self.work_area.sick_leave_block.blockSignals(True)
        self.work_area.sick_leave_block.set_data(data)
        self.work_area.sick_leave_block.blockSignals(False)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 1. Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 2. Меню "Правка" (для Undo/Redo)
        edit_menu = menubar.addMenu("Правка")
        
        self.undo_action = QAction("Отменить", self)
        self.undo_action.triggered.connect(self.dispatch_undo)
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("Повторить", self)
        self.redo_action.triggered.connect(self.dispatch_redo)
        edit_menu.addAction(self.redo_action)
        
        # 3. Пункт "О программе" (прямо в меню баре)
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        menubar.addAction(about_action)

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def dispatch_undo(self):
        # Проверяем, имеет ли фокус редактор или его дочерние элементы
        if self.is_text_input_focused():
            fw = QApplication.focusWidget()
            if isinstance(fw, (QLineEdit, QTextEdit)):
                fw.undo()
        else:
            self.undo_stack.undo()

    def dispatch_redo(self):
        # Проверяем, имеет ли фокус редактор или его дочерние элементы
        if self.is_text_input_focused():
            fw = QApplication.focusWidget()
            if isinstance(fw, (QLineEdit, QTextEdit)):
                fw.redo()
        else:
            self.undo_stack.redo()

    def load_settings(self):
        config = configparser.ConfigParser()
        ini_path = os.path.join(os.path.dirname(__file__), "Templates", "prefabs.ini")
        
        if os.path.exists(ini_path):
            config.read(ini_path, encoding='utf-8')
            
            if 'Window' in config:
                width = config.getint('Window', 'width', fallback=1200)
                height = config.getint('Window', 'height', fallback=800)
                self.resize(width, height)
                
                sizes_str = config.get('Window', 'splitter_sizes', fallback=None)
                if sizes_str:
                    try:
                        sizes = [int(s) for s in sizes_str.split(',')]
                        self.splitter.setSizes(sizes)
                    except ValueError:
                        pass
            
            if 'Doctor' in config:
                doctor_name = config.get('Doctor', 'name', fallback="")
                self.work_area.doctor_name_input.setText(doctor_name)

    def save_settings(self):
        config = configparser.ConfigParser()
        ini_path = os.path.join(os.path.dirname(__file__), "Templates", "prefabs.ini")
        
        # Создаем папку Templates, если её нет
        os.makedirs(os.path.dirname(ini_path), exist_ok=True)
        
        config['Window'] = {
            'width': str(self.width()),
            'height': str(self.height()),
            'splitter_sizes': ",".join(map(str, self.splitter.sizes()))
        }
        
        config['Doctor'] = {
            'name': self.work_area.doctor_name_input.text()
        }
        
        with open(ini_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Установка иконки приложения
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
