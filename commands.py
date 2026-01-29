from PyQt6.QtGui import QUndoCommand
from PyQt6.QtWidgets import QLineEdit, QTextEdit, QCheckBox, QComboBox, QRadioButton

class TextChangeCommand(QUndoCommand):
    def __init__(self, widget, old_text, new_text, description):
        super().__init__(description)
        self.widget = widget
        self.old_text = old_text
        self.new_text = new_text
        self.is_programmatic = False

    def undo(self):
        self.is_programmatic = True
        # Определяем тип виджета для правильной установки текста
        if isinstance(self.widget, QLineEdit):
            self.widget.setText(self.old_text)
        elif isinstance(self.widget, QTextEdit):
            self.widget.setPlainText(self.old_text) # или setHtml, если используется форматирование
        self.is_programmatic = False

    def redo(self):
        # При первом запуске (когда команда только создана) текст уже изменен пользователем,
        # поэтому мы не должны его менять снова, иначе курсор прыгнет.
        # Но QUndoStack вызывает redo() сразу при push().
        # Мы будем обновлять текст только если это повторный вызов (Ctrl+Y)
        
        # Однако, для простоты в Qt redo вызывается сразу. 
        # Чтобы избежать лишних сигналов, мы просто устанавливаем текст.
        # Блокировка сигналов здесь опасна, так как EditorPanel не обновится.
        # Мы полагаемся на то, что ExaminationPanel будет игнорировать создание новых команд
        # во время выполнения undo/redo.
        
        if self.widget_text() != self.new_text:
            if isinstance(self.widget, QLineEdit):
                self.widget.setText(self.new_text)
            elif isinstance(self.widget, QTextEdit):
                self.widget.setPlainText(self.new_text)

    def widget_text(self):
        if isinstance(self.widget, QLineEdit):
            return self.widget.text()
        elif isinstance(self.widget, QTextEdit):
            return self.widget.toPlainText()
        return ""

class CheckBoxCommand(QUndoCommand):
    def __init__(self, widget, new_state, description):
        super().__init__(description)
        self.widget = widget
        self.new_state = new_state
        self.old_state = not new_state # Если мы переключили, значит было наоборот

    def undo(self):
        self.widget.setChecked(self.old_state)

    def redo(self):
        if self.widget.isChecked() != self.new_state:
            self.widget.setChecked(self.new_state)

class ComboBoxCommand(QUndoCommand):
    def __init__(self, widget, old_index, new_index, description):
        super().__init__(description)
        self.widget = widget
        self.old_index = old_index
        self.new_index = new_index

    def undo(self):
        self.widget.setCurrentIndex(self.old_index)

    def redo(self):
        if self.widget.currentIndex() != self.new_index:
            self.widget.setCurrentIndex(self.new_index)

class RadioButtonCommand(QUndoCommand):
    def __init__(self, widget, description):
        super().__init__(description)
        self.widget = widget
        # Для радиокнопок сложнее, так как включение одной выключает другую.
        # Мы сохраняем ту кнопку в группе, которая БЫЛА включена до этого.
        self.group = widget.group()
        self.previous_checked = None
        
        # Ищем, какая кнопка была включена (это нужно делать ДО того, как эта команда сработает, 
        # но так как мы создаем команду ПОСЛЕ клика, логика должна быть внешней)
        # Упростим: мы будем просто включать целевую кнопку при redo.
        # А при undo нам нужно знать, кого включить обратно.
        # Эту информацию мы должны получить извне при создании команды.
        self.previous_checked = None 

    def set_previous(self, prev_widget):
        self.previous_checked = prev_widget

    def undo(self):
        if self.previous_checked:
            self.previous_checked.setChecked(True)
        else:
            # Если ничего не было выбрано (редко), выключаем текущую
            # Но в QButtonGroup обычно одна всегда выбрана, если exclusive
            pass

    def redo(self):
        self.widget.setChecked(True)
