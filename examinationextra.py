from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QCheckBox, QPushButton, QWidget,
                             QGridLayout, QRadioButton, QButtonGroup, QSizePolicy,
                             QStylePainter, QStyleOptionComboBox, QStyle, QComboBox,
                             QMenu, QWidgetAction, QCalendarWidget, QTextEdit, QDialog,
                             QListWidget, QListWidgetItem, QToolButton, QMessageBox, QInputDialog,
                             QTextBrowser, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint, QSize, QUrl
from PyQt6.QtGui import QPalette, QColor, QIcon, QAction, QPixmap
import os
import json

class SymbolComboBox(QComboBox):
    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        
        if not self.isEditable():
            opt.currentText = ""
            opt.palette.setColor(QPalette.ColorRole.Text, QColor(0,0,0,0))
            opt.palette.setColor(QPalette.ColorRole.ButtonText, QColor(0,0,0,0))
        
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, opt)
        
        if self.currentIndex() != -1 and not self.isEditable():
            rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxEditField, self)
            painter.setPen(QColor("#e0e0e0"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.currentText())
        
        rect = self.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, opt, QStyle.SubControl.SC_ComboBoxArrow, self)
        painter.setPen(QColor("#e0e0e0"))
        f = painter.font()
        f.setPointSize(8)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "▼")

class DateInput(QLineEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, lambda: self.setCursorPosition(0))

class TimeInput(QLineEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, lambda: self.setCursorPosition(0))

class AutoResizingTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet("""
            AutoResizingTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                color: #e0e0e0;
            }
        """)
        self.document().documentLayout().documentSizeChanged.connect(self.resize_height)
        self.setFixedHeight(30)
        self._resizing = False

    def resize_height(self):
        if self._resizing:
            return
        self._resizing = True
        try:
            doc_height = self.document().size().height()
            new_height = int(doc_height + 10)
            if new_height < 30: new_height = 30
            if self.height() != new_height:
                self.setFixedHeight(new_height)
        finally:
            self._resizing = False

class ButtonEditDialog(QDialog):
    def __init__(self, button_text, insert_text, default_text, default_insert_text, parent=None, allow_name_edit=True):
        super().__init__(parent)
        self.setWindowTitle("Настройка кнопки")
        self.setFixedWidth(400)
        
        self.default_text = default_text
        self.default_insert_text = default_insert_text
        
        layout = QVBoxLayout(self)
        
        # Название кнопки
        layout.addWidget(QLabel("Название кнопки:"))
        self.name_input = QLineEdit(button_text)
        self.name_input.setStyleSheet("background-color: #3c3f41; color: #e0e0e0; border: 1px solid #555; padding: 4px;")
        if not allow_name_edit:
            self.name_input.setEnabled(False)
            self.name_input.setStyleSheet("background-color: #2b2b2b; color: #808080; border: 1px solid #555; padding: 4px;")
        layout.addWidget(self.name_input)
        
        # Вставляемый текст
        layout.addWidget(QLabel("Вставляемый текст:"))
        self.text_input = QTextEdit()
        self.text_input.setPlainText(insert_text)
        self.text_input.setFixedHeight(100)
        self.text_input.setStyleSheet("background-color: #3c3f41; color: #e0e0e0; border: 1px solid #555; padding: 4px;")
        layout.addWidget(self.text_input)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        self.btn_reset = QPushButton("Сбросить")
        self.btn_reset.clicked.connect(self.reset_to_default)
        btn_layout.addWidget(self.btn_reset)
        
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
        
        # Стилизация кнопок диалога
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #606364; }
            QPushButton:pressed { background-color: #4a90e2; }
        """)

    def reset_to_default(self):
        self.name_input.setText(self.default_text)
        self.text_input.setPlainText(self.default_insert_text)

    def get_data(self):
        return self.name_input.text(), self.text_input.toPlainText()

class EditableButton(QPushButton):
    insertTextChanged = pyqtSignal(str) # Сигнал для вставки текста
    changed = pyqtSignal() # Сигнал о том, что кнопка была изменена

    def __init__(self, text, insert_text, default_text=None, default_insert_text=None, parent=None):
        super().__init__(text, parent)
        self.default_text = default_text if default_text is not None else text
        self.default_insert_text = default_insert_text if default_insert_text is not None else insert_text
        self.current_insert_text = insert_text
        
        # Устанавливаем политику размера, чтобы кнопка растягивалась
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 2px 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #606364;
            }
        """)
        
        self.clicked.connect(lambda: self.insertTextChanged.emit(self.current_insert_text))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: #3c3f41; 
                color: white; 
                border: 1px solid #555; 
            } 
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected { 
                background-color: #4a90e2; 
            }
        """)
        
        edit_action = QAction("Изменить кнопку", self)
        edit_action.triggered.connect(self.open_edit_dialog)
        menu.addAction(edit_action)
        
        menu.exec(self.mapToGlobal(pos))

    def open_edit_dialog(self):
        dialog = ButtonEditDialog(self.text(), self.current_insert_text, self.default_text, self.default_insert_text, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, new_text = dialog.get_data()
            self.setText(new_name)
            self.current_insert_text = new_text
            self.changed.emit()

class NormButton(QPushButton):
    insertTextChanged = pyqtSignal(str)
    changed = pyqtSignal() # Сигнал о том, что кнопка была изменена

    def __init__(self, insert_text, default_insert_text=None, parent=None):
        super().__init__("N", parent)
        self.default_text = "N"
        self.default_insert_text = default_insert_text if default_insert_text is not None else insert_text
        self.current_insert_text = insert_text
        
        self.setFixedWidth(20)
        self.setStyleSheet("""
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 2px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #606364;
            }
        """)
        
        self.clicked.connect(lambda: self.insertTextChanged.emit(self.current_insert_text))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: #3c3f41; 
                color: white; 
                border: 1px solid #555; 
            } 
            QMenu::item {
                padding: 5px 20px 5px 20px;
            }
            QMenu::item:selected { 
                background-color: #4a90e2; 
            }
        """)
        
        edit_action = QAction("Настроить кнопку", self)
        edit_action.triggered.connect(self.open_edit_dialog)
        menu.addAction(edit_action)
        
        menu.exec(self.mapToGlobal(pos))

    def open_edit_dialog(self):
        dialog = ButtonEditDialog(self.text(), self.current_insert_text, self.default_text, self.default_insert_text, self, allow_name_edit=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            _, new_text = dialog.get_data()
            self.current_insert_text = new_text
            self.changed.emit()

class TemplateManagerDialog(QDialog):
    templatesChanged = pyqtSignal()

    def __init__(self, exam_dir, icons_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Список шаблонов")
        self.setFixedWidth(500)
        self.setFixedHeight(400)
        self.exam_dir = exam_dir
        self.icons_path = icons_path
        
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #555;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #3c3f41;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #3c3f41;
            }
        """)
        layout.addWidget(self.list_widget)
        
        self.refresh_list()
        
        # Стилизация диалога
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #e0e0e0; }
            QLabel { color: #e0e0e0; }
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #606364; }
            QPushButton:pressed { background-color: #4a90e2; }
        """)

    def refresh_list(self):
        self.list_widget.clear()
        if os.path.exists(self.exam_dir):
            files = [f for f in os.listdir(self.exam_dir) if f.endswith('.json')]
            for f in files:
                self.add_template_row(f)

    def add_template_row(self, filename):
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(0, 40))
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # Получаем имя шаблона из файла
        template_name = filename.replace(".json", "")
        try:
            with open(os.path.join(self.exam_dir, filename), 'r', encoding='utf-8') as file:
                data = json.load(file)
                template_name = data.get("template_name", template_name)
        except:
            pass
            
        name_label = QLabel(template_name)
        name_label.setStyleSheet("color: #e0e0e0; font-size: 14px;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Кнопка редактирования
        btn_edit = QToolButton()
        btn_edit.setIcon(QIcon(os.path.join(self.icons_path, "edit.png")))
        btn_edit.setToolTip("Редактировать название")
        btn_edit.setStyleSheet("background-color: transparent; border: none;")
        btn_edit.clicked.connect(lambda: self.edit_template(filename, template_name))
        layout.addWidget(btn_edit)
        
        # Кнопка удаления
        btn_delete = QToolButton()
        btn_delete.setIcon(QIcon(os.path.join(self.icons_path, "delete.png")))
        btn_delete.setToolTip("Удалить шаблон")
        btn_delete.setStyleSheet("background-color: transparent; border: none;")
        btn_delete.clicked.connect(lambda: self.delete_template(filename))
        layout.addWidget(btn_delete)
        
        self.list_widget.setItemWidget(item, widget)

    def edit_template(self, filename, current_name):
        new_name, ok = QInputDialog.getText(self, "Редактировать шаблон", "Введите новое название:", text=current_name)
        if ok and new_name and new_name != current_name:
            old_path = os.path.join(self.exam_dir, filename)
            new_filename = f"{new_name}.json"
            new_path = os.path.join(self.exam_dir, new_filename)
            
            if os.path.exists(new_path):
                QMessageBox.warning(self, "Ошибка", "Шаблон с таким именем уже существует!")
                return
            
            try:
                # Обновляем имя внутри JSON
                with open(old_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data["template_name"] = new_name
                
                with open(old_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                # Переименовываем файл
                os.rename(old_path, new_path)
                
                self.refresh_list()
                self.templatesChanged.emit()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось переименовать шаблон: {e}")

    def delete_template(self, filename):
        reply = QMessageBox.question(self, "ВНИМАНИЕ", "Вы уверены, что хотите удалить шаблон?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(os.path.join(self.exam_dir, filename))
                self.refresh_list()
                self.templatesChanged.emit()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить шаблон: {e}")

class ImageHintDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подсказка")
        self.setStyleSheet("background-color: #2b2b2b; color: #e0e0e0;")
        
        layout = QVBoxLayout(self)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            label.setPixmap(pixmap)
            # Устанавливаем размер окна по размеру изображения + отступы
            self.resize(pixmap.width() + 50, pixmap.height() + 100)
        else:
            label.setText(f"Изображение не найдено:\n{image_path}")
            self.resize(400, 200)
            
        content_layout.addWidget(label)
        scroll_area.setWidget(content_widget)
        
        layout.addWidget(scroll_area)
        
        btn_close = QPushButton("Закрыть")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #606364; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignRight)

class TimpHintDialog(QDialog):
    def __init__(self, image_path, html_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Тимпанометрия - Подсказка")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #2b2b2b; color: #e0e0e0;")
        
        layout = QHBoxLayout(self)
        
        # Левая часть - Изображение
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # Масштабируем, если слишком большое, но сохраняем пропорции
            if pixmap.width() > 500:
                pixmap = pixmap.scaledToWidth(500, Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(pixmap)
        else:
            img_label.setText(f"Изображение не найдено:\n{image_path}")
            
        left_layout.addWidget(img_label)
        left_layout.addStretch()
        
        # Правая часть - Текст
        right_widget = QTextBrowser()
        right_widget.setStyleSheet("""
            QTextBrowser {
                background-color: #333333;
                border: 1px solid #555;
                color: #e0e0e0;
                padding: 10px;
                font-size: 14px;
            }
        """)
        if os.path.exists(html_path):
            right_widget.setSource(QUrl.fromLocalFile(html_path))
        else:
            right_widget.setText(f"Файл справки не найден:\n{html_path}")
            
        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget, 1)

class AdditionalBlock(QFrame):
    paidServiceChanged = pyqtSignal(bool)
    consentChanged = pyqtSignal(bool)
    surdologyVisibilityChanged = pyqtSignal(bool)
    # sickLeaveVisibilityChanged удален

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 1px solid #555;
                border-radius: 8px;
            }
            QCheckBox {
                color: #e0e0e0;
                background-color: transparent;
                border: none;
            }
        """)
        self.setFixedWidth(180)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.paid_checkbox = QCheckBox("Платный прием")
        self.paid_checkbox.stateChanged.connect(lambda state: self.paidServiceChanged.emit(state == Qt.CheckState.Checked.value))
        layout.addWidget(self.paid_checkbox)
        
        self.consent_checkbox = QCheckBox("Получено согласие")
        self.consent_checkbox.setChecked(True)
        self.consent_checkbox.stateChanged.connect(lambda state: self.consentChanged.emit(state == Qt.CheckState.Checked.value))
        layout.addWidget(self.consent_checkbox)
        
        self.surdology_checkbox = QCheckBox("Сурдология")
        self.surdology_checkbox.stateChanged.connect(lambda state: self.surdologyVisibilityChanged.emit(state == Qt.CheckState.Checked.value))
        layout.addWidget(self.surdology_checkbox)
        
        # Чекбокс больничного листа удален отсюда
        
        layout.addStretch()

    def get_data(self):
        return {
            "paid": self.paid_checkbox.isChecked(),
            "consent": self.consent_checkbox.isChecked(),
            "surdology_visible": self.surdology_checkbox.isChecked()
        }

    def set_data(self, data):
        self.paid_checkbox.setChecked(data.get("paid", False))
        self.consent_checkbox.setChecked(data.get("consent", True))
        self.surdology_checkbox.setChecked(data.get("surdology_visible", False))

    def clear(self):
        self.paid_checkbox.setChecked(False)
        self.consent_checkbox.setChecked(True)
        self.surdology_checkbox.setChecked(False)

class SurdologyBlock(QFrame):
    surdologyChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logical_enabled = False # Флаг логической видимости (от чекбокса Сурдология)
        
        # Путь к папке Hints
        self.hints_dir = os.path.join(os.path.dirname(__file__), "Hints")
        
        self.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 1px solid #555;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background-color: transparent;
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
                color: #e0e0e0;
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
            QToolButton {
                background-color: #505354;
                border: 1px solid #606364;
                border-radius: 10px;
                color: #e0e0e0;
                font-weight: bold;
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
            }
            QToolButton:hover {
                background-color: #606364;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        label = QLabel("Сурдологические данные")
        label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        layout.addWidget(label)
        
        # Row 1: Hearing Table Checkbox + Help Button
        row1_layout = QHBoxLayout()
        self.chk_add_hearing_table = QCheckBox("Добавить таблицу исследования слуха")
        self.chk_add_hearing_table.stateChanged.connect(self.toggle_hearing_table)
        row1_layout.addWidget(self.chk_add_hearing_table)
        
        btn_audio_help = QToolButton()
        btn_audio_help.setText("?")
        btn_audio_help.setToolTip("Показать подсказку (Аудиограмма)")
        btn_audio_help.clicked.connect(self.show_audio_hint)
        row1_layout.addWidget(btn_audio_help)
        
        row1_layout.addStretch()
        layout.addLayout(row1_layout)
        
        # Container for hidden elements
        self.hearing_table_container = QWidget()
        self.hearing_table_container.setStyleSheet("background-color: transparent; border: none;")
        hearing_table_layout = QVBoxLayout(self.hearing_table_container)
        hearing_table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Table
        table_grid = QGridLayout()
        table_grid.setSpacing(5)
        
        headers = ["Ш.Р., м.", "Р.Р., м.", "Wc128", "Wc512", "Rn", "Fd"]
        for i, header in enumerate(headers):
            lbl = QLabel(header)
            lbl.setStyleSheet("color: #e0e0e0; border: 1px solid #555; padding: 2px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            table_grid.addWidget(lbl, 0, i)
            
        # 1. SR
        sr_widget = QWidget()
        sr_widget.setObjectName("tableCell")
        sr_widget.setStyleSheet("#tableCell { border: 1px solid #555; }")
        sr_layout = QHBoxLayout(sr_widget)
        sr_layout.setContentsMargins(2, 2, 2, 2)
        sr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sr_input = QLineEdit()
        self.sr_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.sr_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sr_input.setStyleSheet("border: 1px solid #777;")
        self.sr_input.textChanged.connect(self.emit_changed)
        btn_sr_norm = QPushButton("N")
        btn_sr_norm.setFixedWidth(20)
        btn_sr_norm.clicked.connect(lambda: self.sr_input.setText("6/6"))
        sr_layout.addWidget(self.sr_input)
        sr_layout.addWidget(btn_sr_norm)
        table_grid.addWidget(sr_widget, 1, 0)
        
        # 2. RR
        rr_widget = QWidget()
        rr_widget.setObjectName("tableCell")
        rr_widget.setStyleSheet("#tableCell { border: 1px solid #555; }")
        rr_layout = QHBoxLayout(rr_widget)
        rr_layout.setContentsMargins(2, 2, 2, 2)
        rr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rr_input = QLineEdit()
        self.rr_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.rr_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rr_input.setStyleSheet("border: 1px solid #777;")
        self.rr_input.textChanged.connect(self.emit_changed)
        btn_rr_norm = QPushButton("N")
        btn_rr_norm.setFixedWidth(20)
        btn_rr_norm.clicked.connect(lambda: self.rr_input.setText(">6/>6"))
        rr_layout.addWidget(self.rr_input)
        rr_layout.addWidget(btn_rr_norm)
        table_grid.addWidget(rr_widget, 1, 1)
        
        # 3. Wc128
        wc128_widget = QWidget()
        wc128_widget.setObjectName("tableCell")
        wc128_widget.setStyleSheet("#tableCell { border: 1px solid #555; }")
        wc128_layout = QHBoxLayout(wc128_widget)
        wc128_layout.setContentsMargins(2, 2, 2, 2)
        wc128_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.wc128_group = QButtonGroup(self)
        self.wc128_group.setExclusive(False)
        self.rb_wc128_left = QRadioButton()
        self.rb_wc128_center = QRadioButton()
        self.rb_wc128_right = QRadioButton()
        
        self.add_wc_pair(wc128_layout, self.rb_wc128_left, "←")
        self.add_wc_pair(wc128_layout, self.rb_wc128_center, "↔")
        self.add_wc_pair(wc128_layout, self.rb_wc128_right, "→")
        
        for rb in [self.rb_wc128_left, self.rb_wc128_center, self.rb_wc128_right]:
            self.wc128_group.addButton(rb)
            rb.clicked.connect(lambda checked, b=rb, g=self.wc128_group: self.handle_radio_toggle(b, g))
            
        table_grid.addWidget(wc128_widget, 1, 2)
        
        # 4. Wc512
        wc512_widget = QWidget()
        wc512_widget.setObjectName("tableCell")
        wc512_widget.setStyleSheet("#tableCell { border: 1px solid #555; }")
        wc512_layout = QHBoxLayout(wc512_widget)
        wc512_layout.setContentsMargins(2, 2, 2, 2)
        wc512_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.wc512_group = QButtonGroup(self)
        self.wc512_group.setExclusive(False)
        self.rb_wc512_left = QRadioButton()
        self.rb_wc512_center = QRadioButton()
        self.rb_wc512_right = QRadioButton()
        
        self.add_wc_pair(wc512_layout, self.rb_wc512_left, "←")
        self.add_wc_pair(wc512_layout, self.rb_wc512_center, "↔")
        self.add_wc_pair(wc512_layout, self.rb_wc512_right, "→")
        
        for rb in [self.rb_wc512_left, self.rb_wc512_center, self.rb_wc512_right]:
            self.wc512_group.addButton(rb)
            rb.clicked.connect(lambda checked, b=rb, g=self.wc512_group: self.handle_radio_toggle(b, g))
        
        table_grid.addWidget(wc512_widget, 1, 3)
        
        # 5. Rn
        rn_widget = QWidget()
        rn_widget.setObjectName("tableCell")
        rn_widget.setStyleSheet("#tableCell { border: 1px solid #555; }")
        rn_layout = QVBoxLayout(rn_widget)
        rn_layout.setContentsMargins(2, 2, 2, 2)
        rn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        rn_row1 = QHBoxLayout()
        rn_row1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chk_rn_plus_left = QCheckBox()
        self.chk_rn_plus_right = QCheckBox()
        rn_row1.addWidget(self.chk_rn_plus_left)
        rn_row1.addWidget(QLabel("+"))
        rn_row1.addWidget(self.chk_rn_plus_right)
        rn_layout.addLayout(rn_row1)
        
        rn_row2 = QHBoxLayout()
        rn_row2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chk_rn_minus_left = QCheckBox()
        self.chk_rn_minus_right = QCheckBox()
        rn_row2.addWidget(self.chk_rn_minus_left)
        rn_row2.addWidget(QLabel("-"))
        rn_row2.addWidget(self.chk_rn_minus_right)
        rn_layout.addLayout(rn_row2)
        
        self.chk_rn_plus_left.stateChanged.connect(lambda s: self.handle_rn_fd_toggle(s, self.chk_rn_minus_left))
        self.chk_rn_minus_left.stateChanged.connect(lambda s: self.handle_rn_fd_toggle(s, self.chk_rn_plus_left))
        self.chk_rn_plus_right.stateChanged.connect(lambda s: self.handle_rn_fd_toggle(s, self.chk_rn_minus_right))
        self.chk_rn_minus_right.stateChanged.connect(lambda s: self.handle_rn_fd_toggle(s, self.chk_rn_plus_right))
        
        table_grid.addWidget(rn_widget, 1, 4)
        
        # 6. Fd
        fd_widget = QWidget()
        fd_widget.setObjectName("tableCell")
        fd_widget.setStyleSheet("#tableCell { border: 1px solid #555; }")
        fd_layout = QVBoxLayout(fd_widget)
        fd_layout.setContentsMargins(2, 2, 2, 2)
        fd_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        fd_row1 = QHBoxLayout()
        fd_row1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chk_fd_plus_left = QCheckBox()
        self.chk_fd_plus_right = QCheckBox()
        fd_row1.addWidget(self.chk_fd_plus_left)
        fd_row1.addWidget(QLabel("+"))
        fd_row1.addWidget(self.chk_fd_plus_right)
        fd_layout.addLayout(fd_row1)
        
        fd_row2 = QHBoxLayout()
        fd_row2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chk_fd_minus_left = QCheckBox()
        self.chk_fd_minus_right = QCheckBox()
        fd_row2.addWidget(self.chk_fd_minus_left)
        fd_row2.addWidget(QLabel("-"))
        fd_row2.addWidget(self.chk_fd_minus_right)
        fd_layout.addLayout(fd_row2)
        
        self.chk_fd_plus_left.stateChanged.connect(lambda s: self.handle_rn_fd_toggle(s, self.chk_fd_minus_left))
        self.chk_fd_minus_left.stateChanged.connect(lambda s: self.handle_rn_fd_toggle(s, self.chk_fd_plus_left))
        self.chk_fd_plus_right.stateChanged.connect(lambda s: self.handle_rn_fd_toggle(s, self.chk_fd_minus_right))
        self.chk_fd_minus_right.stateChanged.connect(lambda s: self.handle_rn_fd_toggle(s, self.chk_fd_plus_right))
        
        table_grid.addWidget(fd_widget, 1, 5)
        
        hearing_table_layout.addLayout(table_grid)
        
        self.hearing_table_container.setVisible(False)
        layout.addWidget(self.hearing_table_container)
        
        # Timpanometry
        timp_layout = QHBoxLayout()
        self.chk_timpanometry = QCheckBox("Тимпанометрия")
        self.chk_timpanometry.stateChanged.connect(self.toggle_timpanometry)
        timp_layout.addWidget(self.chk_timpanometry)
        
        btn_timp_help = QToolButton()
        btn_timp_help.setText("?")
        btn_timp_help.setToolTip("Показать подсказку (Тимпанометрия)")
        btn_timp_help.clicked.connect(self.show_timp_hint)
        timp_layout.addWidget(btn_timp_help)
        
        self.timp_widget = QWidget()
        self.timp_widget.setStyleSheet("background-color: transparent; border: none;")
        timp_inner_layout = QHBoxLayout(self.timp_widget)
        timp_inner_layout.setContentsMargins(0, 0, 0, 0)
        
        timp_types = ["Тип А", "Тип B", "Тип С", "Тип D", "Тип E", "Тип Ad", "Утечка воздуха"]
        
        timp_inner_layout.addWidget(QLabel("AD"))
        self.combo_timp_ad = SymbolComboBox()
        self.combo_timp_ad.setStyleSheet("""
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
        self.combo_timp_ad.addItems(timp_types)
        self.combo_timp_ad.currentTextChanged.connect(self.emit_changed)
        timp_inner_layout.addWidget(self.combo_timp_ad)
        
        timp_inner_layout.addWidget(QLabel("AS"))
        self.combo_timp_as = SymbolComboBox()
        self.combo_timp_as.setStyleSheet("""
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
        self.combo_timp_as.addItems(timp_types)
        self.combo_timp_as.currentTextChanged.connect(self.emit_changed)
        timp_inner_layout.addWidget(self.combo_timp_as)
        
        self.timp_widget.setVisible(False)
        timp_layout.addWidget(self.timp_widget)
        timp_layout.addStretch()
        
        layout.addLayout(timp_layout)
        
        # Average Frequency
        avg_layout = QVBoxLayout()
        self.chk_avg_freq = QCheckBox("Среднее арифметическое речевых частот")
        self.chk_avg_freq.stateChanged.connect(self.toggle_avg_freq)
        avg_layout.addWidget(self.chk_avg_freq)
        
        self.avg_freq_widget = QWidget()
        self.avg_freq_widget.setStyleSheet("background-color: transparent; border: none;")
        avg_freq_inner_layout = QVBoxLayout(self.avg_freq_widget)
        avg_freq_inner_layout.setContentsMargins(0, 0, 0, 0)
        
        # AD
        ad_freq_layout = QHBoxLayout()
        ad_freq_layout.addWidget(QLabel("AD:"))
        self.ad_freq_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setFixedWidth(40)
            inp.setMaxLength(3)
            inp.setPlaceholderText(["500", "1000", "2000", "4000"][i])
            inp.textChanged.connect(self.calculate_avg_ad)
            self.ad_freq_inputs.append(inp)
            ad_freq_layout.addWidget(inp)
        
        ad_freq_layout.addSpacing(10)
        self.ad_avg_result = QLineEdit()
        self.ad_avg_result.setFixedWidth(50)
        self.ad_avg_result.setReadOnly(True)
        self.ad_avg_result.setPlaceholderText("Итог")
        ad_freq_layout.addWidget(self.ad_avg_result)
        ad_freq_layout.addStretch()
        avg_freq_inner_layout.addLayout(ad_freq_layout)
        
        # AS
        as_freq_layout = QHBoxLayout()
        as_freq_layout.addWidget(QLabel("AS:"))
        self.as_freq_inputs = []
        for i in range(4):
            inp = QLineEdit()
            inp.setFixedWidth(40)
            inp.setMaxLength(3)
            inp.setPlaceholderText(["500", "1000", "2000", "4000"][i])
            inp.textChanged.connect(self.calculate_avg_as)
            self.as_freq_inputs.append(inp)
            as_freq_layout.addWidget(inp)
            
        as_freq_layout.addSpacing(10)
        self.as_avg_result = QLineEdit()
        self.as_avg_result.setFixedWidth(50)
        self.as_avg_result.setReadOnly(True)
        self.as_avg_result.setPlaceholderText("Итог")
        as_freq_layout.addWidget(self.as_avg_result)
        as_freq_layout.addStretch()
        avg_freq_inner_layout.addLayout(as_freq_layout)
        
        self.avg_freq_widget.setVisible(False)
        avg_layout.addWidget(self.avg_freq_widget)
        
        layout.addLayout(avg_layout)

    def show_audio_hint(self):
        image_path = os.path.join(self.hints_dir, "Audio.png")
        dialog = ImageHintDialog(image_path, self)
        dialog.exec()

    def show_timp_hint(self):
        image_path = os.path.join(self.hints_dir, "Tymp.png")
        html_path = os.path.join(self.hints_dir, "tymp.html")
        dialog = TimpHintDialog(image_path, html_path, self)
        dialog.exec()

    def add_wc_pair(self, layout, rb, text):
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)
        v_layout.addWidget(rb, 0, Qt.AlignmentFlag.AlignHCenter)
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #e0e0e0; border: none;")
        v_layout.addWidget(lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(v_layout)

    def toggle_hearing_table(self, state):
        visible = (state == Qt.CheckState.Checked.value)
        self.hearing_table_container.setVisible(visible)
        self.emit_changed()

    def toggle_timpanometry(self, state):
        visible = (state == Qt.CheckState.Checked.value)
        self.timp_widget.setVisible(visible)
        self.emit_changed()

    def toggle_avg_freq(self, state):
        visible = (state == Qt.CheckState.Checked.value)
        self.avg_freq_widget.setVisible(visible)
        self.emit_changed()

    def handle_radio_toggle(self, button, group):
        if button.isChecked():
            for btn in group.buttons():
                if btn is not button:
                    btn.blockSignals(True)
                    btn.setChecked(False)
                    btn.blockSignals(False)
        self.emit_changed()

    def handle_rn_fd_toggle(self, state, other_checkbox):
        if state == Qt.CheckState.Checked.value:
            other_checkbox.setChecked(False)
        self.emit_changed()

    def calculate_avg_ad(self):
        try:
            values = [int(inp.text()) for inp in self.ad_freq_inputs if inp.text().isdigit()]
            if len(values) == 4:
                avg = sum(values) / 4
                self.ad_avg_result.setText(f"{avg:.1f}")
            else:
                self.ad_avg_result.clear()
        except:
            self.ad_avg_result.clear()
        self.emit_changed()

    def calculate_avg_as(self):
        try:
            values = [int(inp.text()) for inp in self.as_freq_inputs if inp.text().isdigit()]
            if len(values) == 4:
                avg = sum(values) / 4
                self.as_avg_result.setText(f"{avg:.1f}")
            else:
                self.as_avg_result.clear()
        except:
            self.as_avg_result.clear()
        self.emit_changed()

    def emit_changed(self):
        self.surdologyChanged.emit(self.get_data())

    def set_logical_enabled(self, enabled):
        self._logical_enabled = enabled
        self.emit_changed()

    def get_data(self):
        return {
            "enabled": self._logical_enabled,
            "table_enabled": self.chk_add_hearing_table.isChecked(),
            "sr": self.sr_input.text(),
            "rr": self.rr_input.text(),
            "wc128": {
                "left": self.rb_wc128_left.isChecked(),
                "center": self.rb_wc128_center.isChecked(),
                "right": self.rb_wc128_right.isChecked()
            },
            "wc512": {
                "left": self.rb_wc512_left.isChecked(),
                "center": self.rb_wc512_center.isChecked(),
                "right": self.rb_wc512_right.isChecked()
            },
            "rn": {
                "plus_left": self.chk_rn_plus_left.isChecked(),
                "plus_right": self.chk_rn_plus_right.isChecked(),
                "minus_left": self.chk_rn_minus_left.isChecked(),
                "minus_right": self.chk_rn_minus_right.isChecked()
            },
            "fd": {
                "plus_left": self.chk_fd_plus_left.isChecked(),
                "plus_right": self.chk_fd_plus_right.isChecked(),
                "minus_left": self.chk_fd_minus_left.isChecked(),
                "minus_right": self.chk_fd_minus_right.isChecked()
            },
            "timp": {
                "enabled": self.chk_timpanometry.isChecked(),
                "ad": self.combo_timp_ad.currentText(),
                "as": self.combo_timp_as.currentText()
            },
            "avg": {
                "enabled": self.chk_avg_freq.isChecked(),
                "ad_inputs": [inp.text() for inp in self.ad_freq_inputs],
                "as_inputs": [inp.text() for inp in self.as_freq_inputs],
                "ad": self.ad_avg_result.text(),
                "as": self.as_avg_result.text()
            }
        }

    def set_data(self, data):
        # Восстанавливаем состояние чекбокса таблицы
        if "table_enabled" in data:
             self.chk_add_hearing_table.setChecked(data["table_enabled"])
        else:
             # Обратная совместимость: раньше "enabled" отвечал за чекбокс таблицы
             self.chk_add_hearing_table.setChecked(data.get("enabled", False))
             
        # Восстанавливаем логическую видимость
        self._logical_enabled = data.get("enabled", False)

        self.sr_input.setText(data.get("sr", ""))
        self.rr_input.setText(data.get("rr", ""))
        
        wc128 = data.get("wc128", {})
        self.rb_wc128_left.setChecked(wc128.get("left", False))
        self.rb_wc128_center.setChecked(wc128.get("center", False))
        self.rb_wc128_right.setChecked(wc128.get("right", False))
        
        wc512 = data.get("wc512", {})
        self.rb_wc512_left.setChecked(wc512.get("left", False))
        self.rb_wc512_center.setChecked(wc512.get("center", False))
        self.rb_wc512_right.setChecked(wc512.get("right", False))
        
        rn = data.get("rn", {})
        self.chk_rn_plus_left.setChecked(rn.get("plus_left", False))
        self.chk_rn_plus_right.setChecked(rn.get("plus_right", False))
        self.chk_rn_minus_left.setChecked(rn.get("minus_left", False))
        self.chk_rn_minus_right.setChecked(rn.get("minus_right", False))
        
        fd = data.get("fd", {})
        self.chk_fd_plus_left.setChecked(fd.get("plus_left", False))
        self.chk_fd_plus_right.setChecked(fd.get("plus_right", False))
        self.chk_fd_minus_left.setChecked(fd.get("minus_left", False))
        self.chk_fd_minus_right.setChecked(fd.get("minus_right", False))
        
        timp = data.get("timp", {})
        self.chk_timpanometry.setChecked(timp.get("enabled", False))
        self.combo_timp_ad.setCurrentText(timp.get("ad", ""))
        self.combo_timp_as.setCurrentText(timp.get("as", ""))
        
        avg = data.get("avg", {})
        self.chk_avg_freq.setChecked(avg.get("enabled", False))
        ad_inputs = avg.get("ad_inputs", ["", "", "", ""])
        for i, text in enumerate(ad_inputs):
            if i < len(self.ad_freq_inputs): self.ad_freq_inputs[i].setText(text)
            
        as_inputs = avg.get("as_inputs", ["", "", "", ""])
        for i, text in enumerate(as_inputs):
            if i < len(self.as_freq_inputs): self.as_freq_inputs[i].setText(text)

    def clear(self):
        self.chk_add_hearing_table.setChecked(False)
        self.sr_input.clear()
        self.rr_input.clear()
        
        self.wc128_group.setExclusive(False)
        self.rb_wc128_left.setChecked(False)
        self.rb_wc128_center.setChecked(False)
        self.rb_wc128_right.setChecked(False)
        
        self.wc512_group.setExclusive(False)
        self.rb_wc512_left.setChecked(False)
        self.rb_wc512_center.setChecked(False)
        self.rb_wc512_right.setChecked(False)
        
        self.chk_rn_plus_left.setChecked(False)
        self.chk_rn_plus_right.setChecked(False)
        self.chk_rn_minus_left.setChecked(False)
        self.chk_rn_minus_right.setChecked(False)
        
        self.chk_fd_plus_left.setChecked(False)
        self.chk_fd_plus_right.setChecked(False)
        self.chk_fd_minus_left.setChecked(False)
        self.chk_fd_minus_right.setChecked(False)
        
        self.chk_timpanometry.setChecked(False)
        self.combo_timp_ad.setCurrentIndex(-1)
        self.combo_timp_as.setCurrentIndex(-1)
        
        self.chk_avg_freq.setChecked(False)
        for inp in self.ad_freq_inputs: inp.clear()
        for inp in self.as_freq_inputs: inp.clear()

class SickLeaveBlock(QFrame):
    sickLeaveChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 1px solid #555;
                border-radius: 8px;
            }
            QLabel {
                border: none;
                background-color: transparent;
                color: #e0e0e0;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px;
                color: #e0e0e0;
            }
            QLineEdit:disabled {
                color: #808080;
                background-color: #2b2b2b;
            }
            QCheckBox {
                color: #e0e0e0;
                background-color: transparent;
                border: none;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        label = QLabel("Листок нетрудоспособности")
        label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        layout.addWidget(label)
        
        # Checkboxes
        checkboxes_layout = QHBoxLayout()
        
        self.chk_sl_issued = QCheckBox("Выдан листок")
        self.chk_sl_issued.stateChanged.connect(self.toggle_fields)
        checkboxes_layout.addWidget(self.chk_sl_issued)
        
        self.chk_sl_continued = QCheckBox("Продолжение л/н")
        self.chk_sl_continued.setEnabled(False)
        self.chk_sl_continued.stateChanged.connect(self.toggle_fields)
        checkboxes_layout.addWidget(self.chk_sl_continued)
        
        self.chk_sl_parent = QCheckBox("Выдан родителю")
        self.chk_sl_parent.setEnabled(False)
        self.chk_sl_parent.stateChanged.connect(self.toggle_fields)
        checkboxes_layout.addWidget(self.chk_sl_parent)
        
        checkboxes_layout.addStretch()
        layout.addLayout(checkboxes_layout)
        
        # Row 1
        row1_layout = QHBoxLayout()
        
        self.sl_number_input = QLineEdit()
        self.sl_number_input.setPlaceholderText("Номер листка")
        self.sl_number_input.setEnabled(False)
        self.sl_number_input.textChanged.connect(self.emit_changed)
        row1_layout.addWidget(QLabel("№"))
        row1_layout.addWidget(self.sl_number_input)
        
        self.sl_date_from_input = DateInput()
        self.sl_date_from_input.setPlaceholderText("С")
        self.sl_date_from_input.setInputMask("00.00.0000;_")
        self.sl_date_from_input.setEnabled(False)
        self.sl_date_from_input.textChanged.connect(self.emit_changed)
        row1_layout.addWidget(QLabel("С"))
        row1_layout.addWidget(self.sl_date_from_input)
        
        self.sl_date_to_input = DateInput()
        self.sl_date_to_input.setPlaceholderText("По")
        self.sl_date_to_input.setInputMask("00.00.0000;_")
        self.sl_date_to_input.setEnabled(False)
        self.sl_date_to_input.textChanged.connect(self.emit_changed)
        row1_layout.addWidget(QLabel("По"))
        row1_layout.addWidget(self.sl_date_to_input)
        
        layout.addLayout(row1_layout)
        
        # Row 1.5 (Previous SL)
        self.row_prev_sl_widget = QWidget()
        self.row_prev_sl_widget.setStyleSheet("background-color: transparent; border: none;")
        row_prev_sl_layout = QHBoxLayout(self.row_prev_sl_widget)
        row_prev_sl_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sl_prev_number_input = QLineEdit()
        self.sl_prev_number_input.setPlaceholderText("Предыдущий листок")
        self.sl_prev_number_input.setEnabled(False)
        self.sl_prev_number_input.textChanged.connect(self.emit_changed)
        
        row_prev_sl_layout.addWidget(QLabel("Пред. л/н"))
        row_prev_sl_layout.addWidget(self.sl_prev_number_input)
        
        self.row_prev_sl_widget.setVisible(False)
        layout.addWidget(self.row_prev_sl_widget)
        
        # Row 2 (Parent)
        self.row2_sl_widget = QWidget()
        self.row2_sl_widget.setStyleSheet("background-color: transparent; border: none;")
        row2_sl_layout = QHBoxLayout(self.row2_sl_widget)
        row2_sl_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sl_parent_fio_input = QLineEdit()
        self.sl_parent_fio_input.setPlaceholderText("ФИО родителя")
        self.sl_parent_fio_input.textChanged.connect(self.emit_changed)
        row2_sl_layout.addWidget(QLabel("ФИО"))
        row2_sl_layout.addWidget(self.sl_parent_fio_input)
        
        self.sl_parent_dob_input = DateInput()
        self.sl_parent_dob_input.setPlaceholderText("Дата рождения")
        self.sl_parent_dob_input.setInputMask("00.00.0000;_")
        self.sl_parent_dob_input.textChanged.connect(self.emit_changed)
        row2_sl_layout.addWidget(QLabel("Д.Р."))
        row2_sl_layout.addWidget(self.sl_parent_dob_input)
        
        self.row2_sl_widget.setVisible(False)
        layout.addWidget(self.row2_sl_widget)
        
        # Row 3 (Address and Job)
        self.row3_sl_widget = QWidget()
        self.row3_sl_widget.setStyleSheet("background-color: transparent; border: none;")
        row3_sl_layout = QHBoxLayout(self.row3_sl_widget)
        row3_sl_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sl_address_input = QLineEdit()
        self.sl_address_input.setPlaceholderText("Адрес")
        self.sl_address_input.textChanged.connect(self.emit_changed)
        row3_sl_layout.addWidget(QLabel("Адрес"))
        row3_sl_layout.addWidget(self.sl_address_input)
        
        self.sl_job_input = QLineEdit()
        self.sl_job_input.setPlaceholderText("Место работы, должность")
        self.sl_job_input.textChanged.connect(self.emit_changed)
        row3_sl_layout.addWidget(QLabel("Работа"))
        row3_sl_layout.addWidget(self.sl_job_input)
        
        self.row3_sl_widget.setVisible(False)
        layout.addWidget(self.row3_sl_widget)

    def toggle_fields(self):
        issued = self.chk_sl_issued.isChecked()
        continued = self.chk_sl_continued.isChecked()
        parent = self.chk_sl_parent.isChecked()
        
        self.chk_sl_continued.setEnabled(issued)
        self.chk_sl_parent.setEnabled(issued)
        
        self.sl_number_input.setEnabled(issued)
        self.sl_date_from_input.setEnabled(issued)
        self.sl_date_to_input.setEnabled(issued)
        
        show_prev = issued and continued
        self.row_prev_sl_widget.setVisible(show_prev)
        self.sl_prev_number_input.setEnabled(show_prev)
        
        show_parent = issued and parent
        self.row2_sl_widget.setVisible(show_parent)
        self.row3_sl_widget.setVisible(show_parent)
        
        self.emit_changed()

    def emit_changed(self):
        self.sickLeaveChanged.emit(self.get_data())

    def get_data(self):
        return {
            "issued": self.chk_sl_issued.isChecked(),
            "continued": self.chk_sl_continued.isChecked(),
            "parent": self.chk_sl_parent.isChecked(),
            "number": self.sl_number_input.text(),
            "date_from": self.sl_date_from_input.text(),
            "date_to": self.sl_date_to_input.text(),
            "prev_number": self.sl_prev_number_input.text(),
            "parent_fio": self.sl_parent_fio_input.text(),
            "parent_dob": self.sl_parent_dob_input.text(),
            "address": self.sl_address_input.text(),
            "job": self.sl_job_input.text()
        }

    def set_data(self, data):
        self.chk_sl_issued.setChecked(data.get("issued", False))
        self.chk_sl_continued.setChecked(data.get("continued", False))
        self.chk_sl_parent.setChecked(data.get("parent", False))
        
        self.sl_number_input.setText(data.get("number", ""))
        self.sl_date_from_input.setText(data.get("date_from", ""))
        self.sl_date_to_input.setText(data.get("date_to", ""))
        self.sl_prev_number_input.setText(data.get("prev_number", ""))
        self.sl_parent_fio_input.setText(data.get("parent_fio", ""))
        self.sl_parent_dob_input.setText(data.get("parent_dob", ""))
        self.sl_address_input.setText(data.get("address", ""))
        self.sl_job_input.setText(data.get("job", ""))
        
        self.toggle_fields()

    def clear(self):
        self.chk_sl_issued.setChecked(False)
        self.chk_sl_continued.setChecked(False)
        self.chk_sl_parent.setChecked(False)
        
        self.sl_number_input.clear()
        self.sl_date_from_input.clear()
        self.sl_date_to_input.clear()
        self.sl_prev_number_input.clear()
        self.sl_parent_fio_input.clear()
        self.sl_parent_dob_input.clear()
        self.sl_address_input.clear()
        self.sl_job_input.clear()
        
        self.toggle_fields()
