from PyQt6.QtGui import (QTextCursor, QTextCharFormat, QFont, QTextBlockFormat, 
                         QTextTableFormat, QTextLength, QTextFrameFormat, QTextTable)
from PyQt6.QtCore import Qt
import re

class OperMixin:
    """
    Миксин, отвечающий за логику Режима Операции (Operation Mode).
    """

    def _build_operation_structure(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        # Calculate indices
        r = 0
        self.row_map['header'] = r; r+=1
        self.row_map['operation'] = r; r+=1
        self.row_map['op_description'] = r; r+=1 
        self.row_map['diagnosis'] = r; r+=1 
        self.row_map['op_staff'] = r; r+=1 
        self.row_map['op_recommendations'] = r; r+=1 
        
        # Добавляем строку для доп. информации (повторный прием / больничный), если нужно
        if self._repeat_visible or self._sick_leave_visible:
            self.row_map['op_extra'] = r; r+=1
        else:
            self.row_map['op_extra'] = -1
            
        # Добавляем строку подписи, если она видима
        if self._signature_visible:
            self.row_map['signature'] = r; r+=1
        else:
            self.row_map['signature'] = -1
            
        total_rows = r

        available_width, constraints = self._get_table_constraints()
        table_fmt = self._get_table_format(available_width, constraints)
        
        self.main_table = cursor.insertTable(total_rows, 2, table_fmt)
        
        # Merge cells
        self.main_table.mergeCells(self.row_map['operation'], 0, 1, 2)
        self.main_table.mergeCells(self.row_map['op_description'], 0, 1, 2) 
        self.main_table.mergeCells(self.row_map['diagnosis'], 0, 1, 2)
        self.main_table.mergeCells(self.row_map['op_staff'], 0, 1, 2)
        self.main_table.mergeCells(self.row_map['op_recommendations'], 0, 1, 2)
        
        if self.row_map['op_extra'] != -1:
            self.main_table.mergeCells(self.row_map['op_extra'], 0, 1, 2)
            
        if self.row_map['signature'] != -1:
            self.main_table.mergeCells(self.row_map['signature'], 0, 1, 2)

        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()

    # --- Update Methods (Operation) ---

    def update_operation_from_ui(self, data):
        self._cached_data['operation'] = (data,)
        if self._updating_operation or self._checking_content: return
        self._updating_operation = True
        self.blockSignals(True)
        try:
            # 1. Предоперационный осмотр
            self._update_preop_exam(data)

            # 2. Оперативное вмешательство (описание)
            self._update_op_description(data)

        finally:
            self.blockSignals(False)
            self._updating_operation = False
            self.paginate()

    def _update_preop_exam(self, data):
        cell = self.get_cell('operation', 0, 0)
        if not cell: return

        first_cursor = cell.firstCursorPosition()
        last_cursor = cell.lastCursorPosition()
        first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
        first_cursor.removeSelectedText()
        
        font = QFont("Times New Roman", 10)
        char_fmt_base = QTextCharFormat()
        char_fmt_base.setFont(font)
        
        char_fmt_bold = QTextCharFormat(char_fmt_base)
        char_fmt_bold.setFontWeight(QFont.Weight.Bold)
        
        char_fmt_normal = QTextCharFormat(char_fmt_base)
        char_fmt_normal.setFontWeight(QFont.Weight.Normal)
        
        char_fmt_small = QTextCharFormat(char_fmt_base)
        char_fmt_small.setFontPointSize(7)
        
        block_fmt_left = QTextBlockFormat()
        block_fmt_left.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        block_fmt_center = QTextBlockFormat()
        block_fmt_center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Заголовок
        first_cursor.setBlockFormat(block_fmt_center)
        first_cursor.setCharFormat(char_fmt_bold)
        first_cursor.insertText("Показания к оперативному вмешательству:\n")
        
        # Жалобы
        first_cursor.setBlockFormat(block_fmt_left)
        first_cursor.setCharFormat(char_fmt_normal)
        complaints_html = data.get("complaints_anamnesis", "")
        if complaints_html:
            complaints_html = f'<span style="font-family: \'Times New Roman\';">{complaints_html}</span>'
            first_cursor.insertHtml(complaints_html)
            first_cursor.insertText("\n")

        # Согласие
        if data.get("informed_consent", False):
            block_fmt_small = QTextBlockFormat()
            block_fmt_small.setTopMargin(0)
            block_fmt_small.setBottomMargin(0)
            first_cursor.setBlockFormat(block_fmt_small)
            char_fmt_tiny = QTextCharFormat(char_fmt_base)
            char_fmt_tiny.setFontPointSize(1)
            first_cursor.setCharFormat(char_fmt_tiny)
            first_cursor.insertText("\n")
            
            informed_text = 'На основании частей первой и второй статьи 44 закона Республики Беларусь от 18 июня 1993 года N 2435-XII "О здравоохранении" пациент устно проинформирован о необходимости проведения простых диагностических исследований, консультаций и от пациента получено устное информированное добровольное согласие на проведение диагностических исследований, консультаций.'
            first_cursor.setBlockFormat(block_fmt_left)
            first_cursor.setCharFormat(char_fmt_small)
            first_cursor.insertText(informed_text)
            
            first_cursor.setBlockFormat(block_fmt_small)
            first_cursor.setCharFormat(char_fmt_tiny)
            first_cursor.insertText("\n")
        
        # Показатели
        first_cursor.setBlockFormat(block_fmt_left)
        general_condition = data.get("general_condition", "")
        ad = data.get("ad", "").strip()
        pulse = data.get("pulse", "").strip()
        temp = data.get("temp", "").strip()
        
        line_parts = []
        if general_condition:
            first_cursor.setCharFormat(char_fmt_bold)
            first_cursor.insertText("Общее состояние: ")
            first_cursor.setCharFormat(char_fmt_normal)
            first_cursor.insertText(general_condition)
            if ad or pulse or temp:
                first_cursor.insertText("; ")
        
        if ad:
            first_cursor.setCharFormat(char_fmt_bold)
            first_cursor.insertText("АД: ")
            first_cursor.setCharFormat(char_fmt_normal)
            first_cursor.insertText(f"{ad} мм.рт.ст")
            line_parts.append("")
            
        if pulse:
            if line_parts or (general_condition and ad): first_cursor.insertText("; ")
            first_cursor.setCharFormat(char_fmt_bold)
            first_cursor.insertText("Пульс: ")
            first_cursor.setCharFormat(char_fmt_normal)
            first_cursor.insertText(f"{pulse} в минуту")
            line_parts.append("")

        if temp:
            if line_parts or (general_condition and (ad or pulse)): first_cursor.insertText("; ")
            first_cursor.setCharFormat(char_fmt_bold)
            first_cursor.insertText("Т. тела: ")
            first_cursor.setCharFormat(char_fmt_normal)
            first_cursor.insertText(f"{temp} С°")
            line_parts.append("")
        
        if general_condition or line_parts:
            first_cursor.insertText("\n")

        # St. localis
        objective_examination = data.get("objective_examination", "")
        
        first_cursor.setCharFormat(char_fmt_bold)
        first_cursor.insertText("St. localis:")
        
        first_cursor.setCharFormat(char_fmt_normal)
        first_cursor.insertText(" ")
        
        if objective_examination:
            clean_obj_text = re.sub(r'</?p[^>]*>', '', objective_examination).strip()
            if clean_obj_text:
                obj_html = f'<span style="font-family: \'Times New Roman\'; font-weight: normal;">{clean_obj_text}</span>'
                first_cursor.insertHtml(obj_html)
        
        first_cursor.insertText("\n")

        # Показано
        intervention = data.get("intervention", "")
        
        first_cursor.insertText("\n")
        first_cursor.setCharFormat(char_fmt_bold)
        first_cursor.insertText("С лечебно-диагностической целью показано:")
        
        first_cursor.setCharFormat(char_fmt_normal)
        first_cursor.insertText(" ")
        
        if intervention:
            clean_intervention = re.sub(r'</?p[^>]*>', '', intervention).strip()
            if clean_intervention:
                int_html = f'<span style="font-family: \'Times New Roman\'; font-weight: normal;">{clean_intervention}</span>'
                first_cursor.insertHtml(int_html)
        
        first_cursor.insertText("\n")

        # Согласие на вмешательство
        if data.get("intervention_consent", False):
            first_cursor.setCharFormat(char_fmt_normal)
            first_cursor.insertText("Суть вмешательства разъяснена. Получено письменное согласие пациента.")
            first_cursor.insertText("\n")

    def _update_op_description(self, data):
        cell_desc = self.get_cell('op_description', 0, 0)
        if not cell_desc: return

        first_cursor = cell_desc.firstCursorPosition()
        last_cursor = cell_desc.lastCursorPosition()
        first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
        first_cursor.removeSelectedText()
        
        font = QFont("Times New Roman", 10)
        char_fmt_base = QTextCharFormat()
        char_fmt_base.setFont(font)
        char_fmt_bold = QTextCharFormat(char_fmt_base)
        char_fmt_bold.setFontWeight(QFont.Weight.Bold)
        char_fmt_normal = QTextCharFormat(char_fmt_base)
        char_fmt_normal.setFontWeight(QFont.Weight.Normal)
        
        block_fmt_center = QTextBlockFormat()
        block_fmt_center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        block_fmt_left = QTextBlockFormat()
        block_fmt_left.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Номер
        first_cursor.setBlockFormat(block_fmt_center)
        first_cursor.setCharFormat(char_fmt_bold)
        first_cursor.insertText("Оперативное вмешательство № ")
        first_cursor.insertText(data.get("op_number", ""))
        first_cursor.insertText("\n")
        
        # Название
        op_name = data.get("op_name", "")
        if op_name:
            first_cursor.setCharFormat(char_fmt_bold)
            first_cursor.insertText(op_name)
            first_cursor.insertText("\n")
        
        # Описание
        op_desc = data.get("op_description", "")
        if op_desc:
            first_cursor.setBlockFormat(block_fmt_left)
            first_cursor.setCharFormat(char_fmt_normal)
            clean_desc = re.sub(r'</?p[^>]*>', '', op_desc).strip()
            desc_html = f'<span style="font-family: \'Times New Roman\';">{clean_desc}</span>'
            first_cursor.insertHtml(desc_html)

    def _update_op_diagnosis(self, diagnosis):
        """Логика обновления диагноза для режима операции"""
        try:
            cell = self.get_cell('diagnosis', 0, 0)
            if cell:
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                char_fmt_bold = QTextCharFormat()
                char_fmt_bold.setFontWeight(QFont.Weight.Bold)
                char_fmt_normal = QTextCharFormat()
                char_fmt_normal.setFontWeight(QFont.Weight.Normal)
                
                text_val = ""
                if isinstance(diagnosis, dict):
                    text_val = diagnosis.get("text", "")
                else:
                    text_val = diagnosis
                
                first_cursor.setCharFormat(char_fmt_bold)
                first_cursor.insertText("ДИАГНОЗ: ")
                
                # Сбрасываем форматирование на обычное и добавляем пробел
                first_cursor.setCharFormat(char_fmt_normal)
                first_cursor.insertText(" ")
                
                if text_val:
                    styled_html = text_val
                    styled_html = styled_html.replace("font-family:'Segoe UI';", "font-family:'Times New Roman';")
                    styled_html = styled_html.replace('font-family:"Segoe UI";', 'font-family:"Times New Roman";')
                    styled_html = f'<span style="font-family: \'Times New Roman\'; font-weight: normal;">{styled_html}</span>'
                    first_cursor.insertHtml(styled_html)
        except Exception as e:
            print(f"Error updating op diagnosis: {e}")

    def update_operation_staff_from_ui(self, operator, nurse):
        self._cached_data['op_staff'] = (operator, nurse)
        if self._checking_content: return
        self.blockSignals(True)
        try:
            cell = self.get_cell('op_staff', 0, 0)
            if cell:
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                block_fmt = QTextBlockFormat()
                block_fmt.setAlignment(Qt.AlignmentFlag.AlignRight)
                first_cursor.setBlockFormat(block_fmt)
                
                char_fmt = QTextCharFormat()
                char_fmt.setFontWeight(QFont.Weight.Normal)
                first_cursor.setCharFormat(char_fmt)
                
                text = f"Оператор: {operator}\nОпер. м/с.: {nurse}"
                first_cursor.insertText(text)
        finally:
            self.blockSignals(False)
            self.paginate()

    def _update_op_recommendations(self, recommendations, show_label):
        """Логика обновления рекомендаций для режима операции"""
        try:
            cell = self.get_cell('op_recommendations', 0, 0)
            if cell:
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                # Если чекбокс не отмечен, очищаем и выходим
                if not show_label:
                    return

                # Сбрасываем форматирование блока
                block_fmt = QTextBlockFormat()
                first_cursor.setBlockFormat(block_fmt)
                first_cursor.setCharFormat(QTextCharFormat())

                # Заголовок
                char_fmt_bold = QTextCharFormat()
                char_fmt_bold.setFontWeight(QFont.Weight.Bold)
                first_cursor.setCharFormat(char_fmt_bold)
                first_cursor.insertText("РЕКОМЕНДОВАНО:")
                
                # Текст рекомендаций
                # Устанавливаем обычный шрифт для текста рекомендаций (и пробела)
                char_fmt_normal = QTextCharFormat()
                char_fmt_normal.setFontWeight(QFont.Weight.Normal)
                first_cursor.setCharFormat(char_fmt_normal)
                first_cursor.insertText(" ") # Insert space with normal format

                if recommendations:
                    html_rec = recommendations
                    styled_html = html_rec
                    
                    styled_html = styled_html.replace("font-family:'Segoe UI';", "font-family:'Times New Roman';")
                    styled_html = styled_html.replace('font-family:"Segoe UI";', 'font-family:"Times New Roman";')
                    
                    styled_html = re.sub(r'<p[^>]*>\s*<br\s*/?>\s*</p>\s*(?=<ul|<ol)', '', styled_html, flags=re.IGNORECASE)

                    style = "margin-top: 0px; margin-bottom: 0px; margin-left: 10px; -qt-list-indent: 0;"
                    styled_html = re.sub(r'<ul\b[^>]*>', f'<ul style="{style}">', styled_html)
                    styled_html = re.sub(r'<ol\b[^>]*>', f'<ol style="{style}">', styled_html)
                    
                    # Игнорируем пустой HTML
                    if not (recommendations == "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\np, li { white-space: pre-wrap; }\nhr { height: 1px; border-width: 0; }\nli.unchecked::marker { content: \"\\2610\"; }\nli.checked::marker { content: \"\\2612\"; }\n</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"):
                         if styled_html.startswith("<p style=\"-qt-paragraph-type:empty"):
                             pass 
                         
                         first_cursor.insertHtml(styled_html)

        except Exception as e:
            print(f"Error updating op recommendations: {e}")

    def _update_op_extra_content(self):
        """Обновление ячейки с дополнительной информацией (повторный прием, больничный) в режиме операции"""
        cell = self.get_cell('op_extra', 0, 0)
        if not cell: return
        
        self.blockSignals(True)
        try:
            first_cursor = cell.firstCursorPosition()
            last_cursor = cell.lastCursorPosition()
            first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
            first_cursor.removeSelectedText()
            
            block_fmt = QTextBlockFormat()
            block_fmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
            first_cursor.setBlockFormat(block_fmt)
            
            char_fmt_bold = QTextCharFormat()
            char_fmt_bold.setFontWeight(QFont.Weight.Bold)
            
            char_fmt_normal = QTextCharFormat()
            char_fmt_normal.setFontWeight(QFont.Weight.Normal)
            
            has_content = False
            
            # 1. Повторный прием
            if self._repeat_visible:
                enabled, date, time = self._cached_data['repeat']
                if enabled:
                    first_cursor.setCharFormat(char_fmt_bold)
                    first_cursor.insertText("Повторный прием ")
                    
                    first_cursor.setCharFormat(char_fmt_normal)
                    text = date
                    if time:
                        text += f" {time}"
                    first_cursor.insertText(text)
                    has_content = True
            
            # 2. Больничный лист
            if self._sick_leave_visible:
                data = self._cached_data['sick_leave'][0]
                if data.get("issued"):
                    if has_content:
                        first_cursor.insertText("\n")
                        
                    text = ""
                    if data.get("parent") and data.get("continued"):
                        text = f"Родителю/опекуну ребенка выдано продолжение листка нетрудоспособности {data.get('prev_number')}: Л/Н № {data.get('number')} с {data.get('date_from')} по {data.get('date_to')}."
                        text += f"\n{data.get('parent_fio')}, {data.get('parent_dob')} г.р.; Проживает: {data.get('address')}; Место работы, должность: {data.get('job')}"
                    elif data.get("parent"):
                        text = f"Родителю/опекуну ребенка выдан листок нетрудоспособности № {data.get('number')} с {data.get('date_from')} по {data.get('date_to')}."
                        text += f"\n{data.get('parent_fio')}, {data.get('parent_dob')} г.р.; Проживает: {data.get('address')}; Место работы, должность: {data.get('job')}"
                    elif data.get("continued"):
                        text = f"Пациенту выдано продолжение листка нетрудоспособности {data.get('prev_number')}: Л/Н № {data.get('number')} с {data.get('date_from')} по {data.get('date_to')}."
                    else:
                        text = f"Пациенту выдан листок нетрудоспособности № {data.get('number')} с {data.get('date_from')} по {data.get('date_to')}."
                    
                    first_cursor.setCharFormat(char_fmt_normal)
                    first_cursor.insertText(text)
                    
        finally:
            self.blockSignals(False)
            self.paginate()

    def check_op_content(self):
        """Проверка содержимого для режима операции"""
        try:
            # Инициализируем data один раз
            data = self._cached_data['operation'][0].copy()
            data_changed = False

            # 1. Предоперационный осмотр
            cell_preop = self.get_cell('operation', 0, 0)
            if cell_preop:
                cursor = cell_preop.firstCursorPosition()
                cursor.setPosition(cell_preop.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_preop = cursor.selection().toPlainText()
                
                # Парсинг жалоб (текст до "Общее состояние:" или "Пациент информирован")
                # Убираем заголовок "Показания к оперативному вмешательству:"
                text_preop = text_preop.replace("Показания к оперативному вмешательству:", "").strip()
                
                # Ищем начало следующего блока
                end_complaints = len(text_preop)
                for marker in ["Общее состояние:", "На основании частей первой", "АД:"]:
                    idx = text_preop.find(marker)
                    if idx != -1 and idx < end_complaints:
                        end_complaints = idx
                
                data["complaints_anamnesis"] = text_preop[:end_complaints].strip()
                
                # Парсинг показателей
                match_ad = re.search(r"АД:\s*(.*?)\s*мм\.рт\.ст", text_preop)
                if match_ad: data["ad"] = match_ad.group(1).strip()
                
                match_pulse = re.search(r"Пульс:\s*(.*?)\s*в минуту", text_preop)
                if match_pulse: data["pulse"] = match_pulse.group(1).strip()
                
                match_temp = re.search(r"Т\. тела:\s*(.*?)\s*С°", text_preop)
                if match_temp: data["temp"] = match_temp.group(1).strip()
                
                # Парсинг St. localis
                if "St. localis:" in text_preop:
                    start = text_preop.find("St. localis:") + len("St. localis:")
                    end = len(text_preop)
                    
                    # Ищем следующую метку
                    for marker in ["С лечебно-диагностической", "Суть вмешательства"]:
                        idx = text_preop.find(marker, start)
                        if idx != -1 and idx < end:
                            end = idx
                    
                    data["objective_examination"] = text_preop[start:end].strip()
                
                # Парсинг вмешательства
                if "С лечебно-диагностической целью показано:" in text_preop:
                    start = text_preop.find("С лечебно-диагностической целью показано:") + len("С лечебно-диагностической целью показано:")
                    end = len(text_preop)
                    
                    if "Суть вмешательства" in text_preop:
                        idx = text_preop.find("Суть вмешательства", start)
                        if idx != -1: end = idx
                        
                    data["intervention"] = text_preop[start:end].strip()
                
                data_changed = True

            # 2. Ход операции
            cell_desc = self.get_cell('op_description', 0, 0)
            if cell_desc:
                cursor = cell_desc.firstCursorPosition()
                cursor.setPosition(cell_desc.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_desc = cursor.selection().toPlainText()
                
                match_num = re.search(r"Оперативное вмешательство №\s*(.*)", text_desc)
                if match_num:
                    data["op_number"] = match_num.group(1).strip()
                    
                    # Название операции обычно на следующей строке
                    lines = text_desc.split('\n')
                    for i, line in enumerate(lines):
                        if "Оперативное вмешательство №" in line:
                            if i + 1 < len(lines):
                                data["op_name"] = lines[i+1].strip()
                                # Описание - все остальное
                                data["op_description"] = "\n".join(lines[i+2:]).strip()
                            break
                
                data_changed = True
            
            # Emit ONCE
            if data_changed:
                self.operationDataChangedFromEditor.emit(data)
            
            # 3. Диагноз
            cell_diag = self.get_cell('diagnosis', 0, 0)
            if cell_diag:
                cursor = cell_diag.firstCursorPosition()
                cursor.setPosition(cell_diag.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                html_diag = cursor.selection().toHtml()
                html_diag = re.sub(r'(>)\s*ДИАГНОЗ:\s*', r'\1', html_diag)
                self.diagnosisChangedFromEditor.emit(html_diag)
            
            # 4. Рекомендации
            cell_rec = self.get_cell('op_recommendations', 0, 0)
            if cell_rec:
                cursor = cell_rec.firstCursorPosition()
                cursor.setPosition(cell_rec.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                html_rec = cursor.selection().toHtml()
                
                html_rec = re.sub(r'<p[^>]*>\s*<br\s*/?>\s*</p>\s*(?=<ul|<ol)', '', html_rec, flags=re.IGNORECASE)
                style = "margin-top: 0px; margin-bottom: 0px; margin-left: 10px; -qt-list-indent: 0;"
                html_rec = re.sub(r'<ul\b[^>]*>', f'<ul style="{style}">', html_rec)
                html_rec = re.sub(r'<ol\b[^>]*>', f'<ol style="{style}">', html_rec)
                html_rec = re.sub(r'(>)\s*РЕКОМЕНДОВАНО:\s*', r'\1', html_rec)
                
                self.recommendationsChangedFromEditor.emit(html_rec)

            # 5. Персонал
            cell_staff = self.get_cell('op_staff', 0, 0)
            if cell_staff:
                cursor = cell_staff.firstCursorPosition()
                cursor.setPosition(cell_staff.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_staff = cursor.selection().toPlainText()
                
                operator = ""
                nurse = ""
                
                match_op = re.search(r"Оператор:\s*(.*)", text_staff)
                if match_op: operator = match_op.group(1).strip()
                
                match_nurse = re.search(r"Опер\. м/с\.:\s*(.*)", text_staff)
                if match_nurse: nurse = match_nurse.group(1).strip()
                
                self.operationStaffChangedFromEditor.emit(operator, nurse)

            # 6. Дополнительно (больничный, повторный прием)
            cell_extra = self.get_cell('op_extra', 0, 0)
            if cell_extra:
                cursor = cell_extra.firstCursorPosition()
                cursor.setPosition(cell_extra.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_extra = cursor.selection().toPlainText()
                
                # Повторный прием
                if "Повторный прием" in text_extra:
                    lines = text_extra.split('\n')
                    for line in lines:
                        if "Повторный прием" in line:
                            # Remove the label
                            content = line.replace("Повторный прием", "").strip()
                            # Remove optional colon
                            if content.startswith(":"):
                                content = content[1:].strip()
                            
                            parts = content.split()
                            date = parts[0] if len(parts) > 0 else ""
                            time = parts[1] if len(parts) > 1 else ""
                            
                            self.repeatChangedFromEditor.emit(True, date, time)
                            break
                
                # Больничный
                data_sl = self._cached_data.get('sick_leave', ({},))[0].copy()
                
                match_num = re.search(r"№\s*(\S+)", text_extra)
                if match_num:
                    data_sl["number"] = match_num.group(1)
                
                match_date_from = re.search(r"с\s+([\d\.]+)", text_extra, re.IGNORECASE)
                if match_date_from:
                    data_sl["date_from"] = match_date_from.group(1).rstrip('.')
                    
                match_date_to = re.search(r"по\s+([\d\.]+)", text_extra, re.IGNORECASE)
                if match_date_to:
                    data_sl["date_to"] = match_date_to.group(1).rstrip('.')
                
                if match_num or match_date_from or match_date_to:
                    self.sickLeaveChangedFromEditor.emit(data_sl)

        except Exception as e:
            print(f"Error checking op content: {e}")
