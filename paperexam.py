from PyQt6.QtGui import (QTextCursor, QTextCharFormat, QFont, QTextBlockFormat, 
                         QTextTableFormat, QTextLength, QTextFrameFormat, QTextTable)
from PyQt6.QtCore import Qt
import re

class ExamMixin:
    """
    Миксин, отвечающий за логику Режима Осмотра (Examination Mode).
    """

    def _build_single_structure(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        
        # Calculate indices
        r = 0
        self.row_map['header'] = r; r+=1
        self.row_map['indicators'] = r; r+=1
        self.row_map['consent'] = r; r+=1
        self.row_map['objective'] = r; r+=1

        if self._surdology_visible:
            self.row_map['surdology'] = r; r+=1
        else:
            self.row_map['surdology'] = -1

        self.row_map['diagnosis'] = r; r+=1

        self.row_map['recommendations'] = r
        if self._repeat_visible:
            self.row_map['repeat'] = r + 1
            r += 2 
        else:
            self.row_map['repeat'] = -1
            r += 1 

        if self._sick_leave_visible:
            self.row_map['sick_leave'] = r; r+=1
        else:
            self.row_map['sick_leave'] = -1

        self.row_map['signature'] = r; r+=1
        total_rows = r

        available_width, constraints = self._get_table_constraints()
        table_fmt = self._get_table_format(available_width, constraints)
        
        self.main_table = cursor.insertTable(total_rows, 2, table_fmt)
        
        # Merge cells
        if self.row_map['consent'] != -1: self.main_table.mergeCells(self.row_map['consent'], 0, 1, 2)
        if self.row_map['objective'] != -1: self.main_table.mergeCells(self.row_map['objective'], 0, 1, 2)
        if self.row_map['surdology'] != -1: self.main_table.mergeCells(self.row_map['surdology'], 0, 1, 2)
        if self.row_map['diagnosis'] != -1: self.main_table.mergeCells(self.row_map['diagnosis'], 0, 1, 2)
        
        if self._repeat_visible:
            self.main_table.mergeCells(self.row_map['recommendations'], 1, 2, 1)
        
        if self.row_map['sick_leave'] != -1: self.main_table.mergeCells(self.row_map['sick_leave'], 0, 1, 2)
        if self.row_map['signature'] != -1: self.main_table.mergeCells(self.row_map['signature'], 0, 1, 2)

        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()

    def _build_split_structure(self):
        cursor = self.textCursor()
        available_width, constraints = self._get_table_constraints()
        
        def create_table(name, rows, cols):
            fmt = self._get_table_format(available_width, constraints)
            
            table = cursor.insertTable(rows, cols, fmt)
            self.tables[name] = table
            
            cursor.movePosition(QTextCursor.MoveOperation.End)
            
            # Spacer block
            cursor.insertBlock()
            block_fmt = cursor.blockFormat()
            block_fmt.setTopMargin(0)
            block_fmt.setBottomMargin(0)
            block_fmt.setLineHeight(1, QTextBlockFormat.LineHeightTypes.FixedHeight.value) 
            cursor.setBlockFormat(block_fmt)
            char_fmt = QTextCharFormat()
            char_fmt.setFontPointSize(1) 
            cursor.setCharFormat(char_fmt)
            
            return table

        create_table('header', 1, 2)
        create_table('indicators', 1, 2)
        
        t = create_table('consent', 1, 2)
        t.mergeCells(0, 0, 1, 2)
        
        t = create_table('objective', 1, 2)
        t.mergeCells(0, 0, 1, 2)
        
        if self._surdology_visible:
            t = create_table('surdology', 1, 2)
            t.mergeCells(0, 0, 1, 2)
            
        t = create_table('diagnosis', 1, 2)
        t.mergeCells(0, 0, 1, 2)
        
        if self._repeat_visible:
            t = create_table('recs_repeat', 2, 2)
            t.mergeCells(0, 1, 2, 1)
        else:
            t = create_table('recs_repeat', 1, 2)
            
        if self._sick_leave_visible:
            t = create_table('sick_leave', 1, 2)
            t.mergeCells(0, 0, 1, 2)
            
        t = create_table('signature', 1, 2)
        t.mergeCells(0, 0, 1, 2)

    # --- Update Methods (Exam) ---

    def update_indicators_from_ui(self, ad, temp, weight, paid_service):
        self._cached_data['indicators'] = (ad, temp, weight, paid_service)
        if self._updating_indicators or self._checking_content: return
        self._updating_indicators = True
        self.blockSignals(True)
        try:
            cell = self.get_cell('indicators', 0, 0)
            if cell:
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                lines = []
                ad_val = ad if ad else "_______"
                lines.append(f"АД: {ad_val} мм. рт. ст.")
                
                temp_val = temp if temp else "_______"
                lines.append(f"t° тела: {temp_val} С°")
                
                if weight:
                    lines.append(f"Вес: {weight} кг")
                
                text = "\n".join(lines)
                
                if paid_service:
                    text += "\n\nПациент осмотрен на платной основе."
                
                first_cursor.insertText(text)
        finally:
            self.blockSignals(False)
            self._updating_indicators = False
            self.paginate()

    def update_complaints_anamnesis_from_ui(self, complaints, anamnesis, no_complaints, show_anamnesis_label, no_card):
        self._cached_data['complaints'] = (complaints, anamnesis, no_complaints, show_anamnesis_label, no_card)
        if self._updating_complaints or self._checking_content: return
        self._updating_complaints = True
        self.blockSignals(True)
        try:
            cell = self.get_cell('indicators', 0, 1)
            if cell:
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                text = ""
                if no_complaints:
                    text += "Жалоб на момент осмотра не предъявляет.\n"
                else:
                    complaints_val = complaints if complaints else ""
                    text += f"Жалобы: {complaints_val}\n"
                
                anamnesis_val = anamnesis if anamnesis else ""
                if show_anamnesis_label:
                    text += f"Анамнез: {anamnesis_val}"
                else:
                    text += f"{anamnesis_val}"
                
                if no_card:
                    first_cursor.insertText(text)
                    first_cursor.insertText("\n")
                    char_fmt = QTextCharFormat()
                    char_fmt.setFontWeight(QFont.Weight.Bold)
                    first_cursor.setCharFormat(char_fmt)
                    first_cursor.insertText("Пациент на приеме без амбулаторной карты!")
                else:
                    first_cursor.insertText(text)

        finally:
            self.blockSignals(False)
            self._updating_complaints = False
            self.paginate()

    def update_consent_from_ui(self, consent_enabled):
        self._cached_data['consent'] = (consent_enabled,)
        if self._updating_consent or self._checking_content: return
        self._updating_consent = True
        self.blockSignals(True)
        try:
            cell = self.get_cell('consent', 0, 0)
            if cell:
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                if consent_enabled:
                    text = 'На основании частей первой и второй статьи 44 закона Республики Беларусь от 18 июня 1993 года N 2435-XII "О здравоохранении" пациент устно проинформирован о необходимости проведения простых диагностических исследований, консультаций и от пациента получено устное информированное добровольное согласие на проведение диагностических исследований, консультаций.'
                    
                    char_fmt = QTextCharFormat()
                    char_fmt.setFontPointSize(7)
                    first_cursor.setCharFormat(char_fmt)
                    first_cursor.insertText(text)
        finally:
            self.blockSignals(False)
            self._updating_consent = False
            self.paginate()

    def update_objective_from_ui(self, data):
        self._cached_data['objective'] = (data,)
        if self._updating_objective or self._checking_content: return
        self._updating_objective = True
        self.blockSignals(True)
        try:
            cell = self.get_cell('objective', 0, 0)
            if cell:
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                # Заголовок
                char_fmt_bold = QTextCharFormat()
                char_fmt_bold.setFontWeight(QFont.Weight.Bold)
                
                block_fmt_center = QTextBlockFormat()
                block_fmt_center.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                first_cursor.setBlockFormat(block_fmt_center)
                first_cursor.setCharFormat(char_fmt_bold)
                first_cursor.insertText("ОБЪЕКТИВНЫЙ ОСМОТР\n")
                
                # Обычный текст
                char_fmt_normal = QTextCharFormat()
                char_fmt_normal.setFontWeight(QFont.Weight.Normal)
                
                block_fmt_left = QTextBlockFormat()
                block_fmt_left.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
                first_cursor.setBlockFormat(block_fmt_left)
                
                has_content = False

                def insert_row(label, value, is_visible):
                    nonlocal has_content
                    if not is_visible: return
                    
                    if has_content:
                        first_cursor.insertText("\n")

                    first_cursor.setCharFormat(char_fmt_bold)
                    first_cursor.insertText(label.rstrip())
                    
                    first_cursor.setCharFormat(char_fmt_normal)
                    first_cursor.insertText(" " + value)
                    
                    first_cursor.insertText("\u200B") 
                    has_content = True

                if data.get("merge_ears"):
                    insert_row("AD/AS - ", data.get("ad_as_comb", ""), data.get("ad_as_vis", False))
                else:
                    insert_row("AD - ", data.get("ad_ear", ""), data.get("ad_vis", False))
                    insert_row("AS - ", data.get("as_ear", ""), data.get("as_vis", False))
                
                if data.get("merge_nose_throat"):
                    insert_row("Nasi, pharynx - ", data.get("nasi_pharynx_comb", ""), data.get("nasi_pharynx_vis", False))
                else:
                    insert_row("Nasi - ", data.get("nasi", ""), data.get("nasi_vis", False))
                    insert_row("Pharynx - ", data.get("pharynx", ""), data.get("pharynx_vis", False))
                
                insert_row("Larynx - ", data.get("larynx", ""), data.get("larynx_vis", False))
                
                # Обработка поля "Прочее"
                other = data.get("other", "")
                other_vis = data.get("other_vis", False)
                
                if other_vis:
                    # Если есть контент выше, добавляем перенос строки, чтобы "Прочее" начиналось с новой строки
                    if has_content:
                        first_cursor.insertText("\n")
                    
                    # Вставляем маркер "Прочего"
                    first_cursor.insertText("\u200C")
                    
                    # Вставляем текст "Прочее"
                    if other:
                        first_cursor.insertText(other)
                else:
                    # Если "Прочее" скрыто, просто вставляем маркер в конец (inline),
                    # чтобы не нарушать структуру, но он не будет создавать новую строку.
                    first_cursor.insertText("\u200C")
                
        finally:
            self.blockSignals(False)
            self._updating_objective = False
            self.paginate()

    def update_surdology_from_ui(self, data):
        self._cached_data['surdology'] = (data,)

        enabled = data.get("enabled", False)
        if enabled != self._surdology_visible:
            self._surdology_visible = enabled
            self.rebuild_document()
            return

        if self._updating_surdology or self._checking_content: return
        self._updating_surdology = True
        self.blockSignals(True)
        try:
            cell = self.get_cell('surdology', 0, 0)
            if cell:
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                if not enabled:
                    return

                char_fmt_normal = QTextCharFormat()
                char_fmt_normal.setFontWeight(QFont.Weight.Normal)
                first_cursor.setCharFormat(char_fmt_normal)
                
                text_parts = []
                
                # Ш.Р.
                sr = data.get("sr", "")
                if sr:
                    text_parts.append(f"Ш.Р. AD/AS = {sr} м")
                
                # Р.Р.
                rr = data.get("rr", "")
                if rr:
                    text_parts.append(f"Р.Р. AD/AS = {rr} м")
                
                # Wc128
                wc128 = data.get("wc128", {})
                wc128_sym = ""
                if wc128.get("left"): wc128_sym = "←"
                elif wc128.get("center"): wc128_sym = "↔"
                elif wc128.get("right"): wc128_sym = "→"
                
                if wc128_sym:
                    text_parts.append(f"Wc128 {wc128_sym}")
                    
                # Wc512
                wc512 = data.get("wc512", {})
                wc512_sym = ""
                if wc512.get("left"): wc512_sym = "←"
                elif wc512.get("center"): wc512_sym = "↔"
                elif wc512.get("right"): wc512_sym = "→"
                
                if wc512_sym:
                    text_parts.append(f"Wc512 {wc512_sym}")
                    
                # Rn
                rn = data.get("rn", {})
                rn_text = ""
                if rn.get("plus_left"): rn_text += "+"
                elif rn.get("minus_left"): rn_text += "-"
                
                rn_text += "Rn"
                
                if rn.get("plus_right"): rn_text += "+"
                elif rn.get("minus_right"): rn_text += "-"
                
                # Проверяем, выбрано ли хоть что-то
                if len(rn_text) > 2: # "Rn" length is 2
                     text_parts.append(rn_text)
                     
                # Fd
                fd = data.get("fd", {})
                fd_text = ""
                if fd.get("plus_left"): fd_text += "+"
                elif fd.get("minus_left"): fd_text += "-"
                
                fd_text += "Fd"
                
                if fd.get("plus_right"): fd_text += "+"
                elif fd.get("minus_right"): fd_text += "-"
                
                if len(fd_text) > 2:
                     text_parts.append(fd_text)
                
                # Собираем первую строку
                full_text = "; ".join(text_parts)
                if full_text:
                    first_cursor.insertText(full_text)
                
                # Тимпанометрия
                timp = data.get("timp", {})
                if timp.get("enabled"):
                    if full_text: first_cursor.insertText("\n")
                    first_cursor.insertText(f"Тимпанометрия: AD - {timp.get('ad', '')}; AS - {timp.get('as', '')}.")
                    
                # Среднее арифметическое
                avg = data.get("avg", {})
                if avg.get("enabled"):
                    if full_text or timp.get("enabled"): first_cursor.insertText("\n")
                    first_cursor.insertText(f"Среднее арифметическое на речевых частотах: AD={avg.get('ad', '')} Дб; AS={avg.get('as', '')} Дб")

        finally:
            self.blockSignals(False)
            self._updating_surdology = False
            self.paginate()

    def _update_exam_diagnosis(self, diagnosis):
        """Логика обновления диагноза для режима осмотра"""
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
                char_fmt_normal.setFontFamily("Times New Roman") # Явно задаем шрифт
                
                text_val = ""
                show_label = True
                no_acute_pathology = False
                
                if isinstance(diagnosis, dict):
                    text_val = diagnosis.get("text", "")
                    show_label = diagnosis.get("show_label", True)
                    no_acute_pathology = diagnosis.get("no_acute_pathology", False)
                else:
                    text_val = diagnosis
                
                if no_acute_pathology:
                    first_cursor.setCharFormat(char_fmt_bold)
                    first_cursor.insertText("Острой ЛОР патологии на момент осмотра не выявлено.")
                    
                    if show_label or text_val:
                        first_cursor.insertText("\n")
                
                if show_label:
                    first_cursor.setCharFormat(char_fmt_bold)
                    first_cursor.insertText("ДИАГНОЗ: ")
                
                # Вставляем пробел с обычным форматированием
                first_cursor.setCharFormat(char_fmt_normal)
                first_cursor.insertText(" ")
                
                if text_val:
                    # Принудительно оборачиваем в span с нужным шрифтом
                    styled_html = text_val
                    if "font-family" not in styled_html:
                        styled_html = f'<span style="font-family: \'Times New Roman\'; font-weight: normal;">{styled_html}</span>'
                    else:
                        # Заменяем другие шрифты на Times New Roman
                        styled_html = styled_html.replace("font-family:'Segoe UI';", "font-family:'Times New Roman';")
                        styled_html = styled_html.replace('font-family:"Segoe UI";', 'font-family:"Times New Roman";')
                    
                    first_cursor.insertHtml(styled_html)
        except Exception as e:
            print(f"Error updating exam diagnosis: {e}")

    def _update_exam_recommendations(self, recommendations, show_label):
        """Логика обновления рекомендаций для режима осмотра"""
        try:
            # Рекомендации в правой колонке (0,1)
            cell = self.get_cell('recommendations', 0, 1)
            if cell:
                # Полностью очищаем ячейку перед вставкой
                first_cursor = cell.firstCursorPosition()
                last_cursor = cell.lastCursorPosition()
                first_cursor.setPosition(last_cursor.position(), QTextCursor.MoveMode.KeepAnchor)
                first_cursor.removeSelectedText()
                
                # Сбрасываем форматирование блока
                block_fmt = QTextBlockFormat()
                first_cursor.setBlockFormat(block_fmt)
                first_cursor.setCharFormat(QTextCharFormat())

                # Добавляем CSS
                html_rec = recommendations
                styled_html = html_rec
                
                styled_html = styled_html.replace("font-family:'Segoe UI';", "font-family:'Times New Roman';")
                styled_html = styled_html.replace('font-family:"Segoe UI";', 'font-family:"Times New Roman";')
                
                styled_html = re.sub(r'<p[^>]*>\s*<br\s*/?>\s*</p>\s*(?=<ul|<ol)', '', styled_html, flags=re.IGNORECASE)

                style = "margin-top: 0px; margin-bottom: 0px; margin-left: 10px; -qt-list-indent: 0;"
                styled_html = re.sub(r'<ul\b[^>]*>', f'<ul style="{style}">', styled_html)
                styled_html = re.sub(r'<ol\b[^>]*>', f'<ol style="{style}">', styled_html)
                
                if not recommendations or recommendations == "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\np, li { white-space: pre-wrap; }\nhr { height: 1px; border-width: 0; }\nli.unchecked::marker { content: \"\\2610\"; }\nli.checked::marker { content: \"\\2612\"; }\n</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>":
                     pass 
                else:
                     if styled_html.startswith("<p style=\"-qt-paragraph-type:empty"):
                         pass 
                     
                     first_cursor.insertHtml(styled_html)
                     
                     first_cursor.setPosition(cell.firstCursorPosition().position())
                     if first_cursor.block().text().strip() == "" and first_cursor.block().next().isValid():
                         first_cursor.movePosition(QTextCursor.MoveOperation.NextBlock, QTextCursor.MoveMode.KeepAnchor)
                         first_cursor.removeSelectedText()
                
                # Обновляем метку в левой верхней ячейке (0,0)
                cell_label = self.get_cell('recommendations', 0, 0)
                cursor_label = cell_label.firstCursorPosition()
                cursor_label.setPosition(cell_label.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                cursor_label.removeSelectedText()
                
                if show_label:
                    char_fmt_bold = QTextCharFormat()
                    char_fmt_bold.setFontWeight(QFont.Weight.Bold)
                    cursor_label.setCharFormat(char_fmt_bold)
                    cursor_label.insertText("РЕКОМЕНДОВАНО:")
        except Exception as e:
            print(f"Error updating exam recommendations: {e}")

    def check_exam_content(self):
        """Обратный парсинг содержимого для режима осмотра"""
        try:
            # 1. Показатели (AD, Temp, Weight)
            cell_ind = self.get_cell('indicators', 0, 0)
            if cell_ind:
                cursor = cell_ind.firstCursorPosition()
                cursor.setPosition(cell_ind.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_ind = cursor.selection().toPlainText()
                
                ad = ""
                temp = ""
                weight = ""
                
                match_ad = re.search(r"АД: (.*?) мм\. рт\. ст\.", text_ind)
                if match_ad:
                    ad = match_ad.group(1).strip()
                    if ad == "_______": ad = ""
                
                match_temp = re.search(r"t° тела: (.*?) С°", text_ind)
                if match_temp:
                    temp = match_temp.group(1).strip()
                    if temp == "_______": temp = ""
                
                match_weight = re.search(r"Вес: (.*?) кг", text_ind)
                if match_weight:
                    weight = match_weight.group(1).strip()
                
                self.indicatorsChangedFromEditor.emit(ad, temp, weight)

            # 2. Жалобы и анамнез
            cell_complaints = self.get_cell('indicators', 0, 1)
            if cell_complaints:
                cursor = cell_complaints.firstCursorPosition()
                cursor.setPosition(cell_complaints.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_complaints = cursor.selection().toPlainText()
                
                complaints = ""
                anamnesis = ""
                
                if "Жалобы: " in text_complaints:
                    parts = text_complaints.split("Жалобы: ")
                    if len(parts) > 1:
                        rest = parts[1]
                        if "Анамнез: " in rest:
                            comp_part, anam_part = rest.split("Анамнез: ")
                            complaints = comp_part.strip()
                            anamnesis = anam_part.strip()
                        else:
                            complaints = rest.strip()
                elif "Жалоб на момент осмотра не предъявляет." in text_complaints:
                    if "Анамнез: " in text_complaints:
                        anamnesis = text_complaints.split("Анамнез: ")[1].strip()
                
                if complaints or anamnesis:
                    self.complaintsAnamnesisChangedFromEditor.emit(complaints, anamnesis)

            # 3. Объективный осмотр
            cell_objective = self.get_cell('objective', 0, 0)
            if cell_objective:
                cursor = cell_objective.firstCursorPosition()
                cursor.setPosition(cell_objective.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_obj = cursor.selection().toPlainText()
                
                data = self._cached_data['objective'][0].copy()
                
                # Карта меток и ключей данных
                labels_map = {
                    "ad_as_comb": "AD/AS - ",
                    "ad_ear": "AD - ",
                    "as_ear": "AS - ",
                    "nasi_pharynx_comb": "Nasi, pharynx - ",
                    "nasi": "Nasi - ",
                    "pharynx": "Pharynx - ",
                    "larynx": "Larynx - ",
                    "other": "\u200C"
                }
                
                # Если поле "Прочее" скрыто, мы не должны искать его метку,
                # чтобы текст не "утекал" в него.
                if not data.get("other_vis", False):
                    if "other" in labels_map:
                        del labels_map["other"]

                # Фильтруем метки в зависимости от режима объединения
                if data.get("merge_ears"):
                    # Если объединено, удаляем отдельные метки
                    if "ad_ear" in labels_map: del labels_map["ad_ear"]
                    if "as_ear" in labels_map: del labels_map["as_ear"]
                else:
                    # Если не объединено, удаляем объединенную метку
                    if "ad_as_comb" in labels_map: del labels_map["ad_as_comb"]
                    
                if data.get("merge_nose_throat"):
                    if "nasi" in labels_map: del labels_map["nasi"]
                    if "pharynx" in labels_map: del labels_map["pharynx"]
                else:
                    if "nasi_pharynx_comb" in labels_map: del labels_map["nasi_pharynx_comb"]

                # Находим позиции всех существующих меток
                found_labels = []
                for key, label in labels_map.items():
                    pos = text_obj.find(label)
                    if pos != -1:
                        found_labels.append((pos, label, key))
                
                # Сортируем по позиции в тексте
                found_labels.sort(key=lambda x: x[0])
                
                # Очищаем данные перед заполнением
                for key in labels_map.keys():
                    if key in data:
                        data[key] = ""

                # Извлекаем значения
                for i, (pos, label, key) in enumerate(found_labels):
                    start = pos + len(label)
                    
                    # Конец текущего значения - это начало следующей метки или конец текста
                    if i + 1 < len(found_labels):
                        end = found_labels[i+1][0]
                    else:
                        end = len(text_obj)
                    
                    value = text_obj[start:end].strip()
                    # Удаляем ZWSP (\u200B) и ZWNJ (\u200C), если они попали в значение
                    value = value.replace("\u200B", "").replace("\u200C", "")
                    
                    data[key] = value
                    
                    # Если мы нашли метку, значит поле должно быть видимым
                    vis_key = key.replace("_ear", "_vis").replace("_comb", "_vis").replace("nasi", "nasi_vis").replace("pharynx", "pharynx_vis").replace("larynx", "larynx_vis").replace("other", "other_vis")
                    if key == "nasi_pharynx_comb": vis_key = "nasi_pharynx_vis"
                    if key == "ad_as_comb": vis_key = "ad_as_vis"
                    
                    if vis_key in data:
                        data[vis_key] = True

                self.objectiveChangedFromEditor.emit(data)

            # 4. Сурдология
            cell_surd = self.get_cell('surdology', 0, 0)
            if cell_surd:
                cursor = cell_surd.firstCursorPosition()
                cursor.setPosition(cell_surd.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_surd = cursor.selection().toPlainText()
                
                data = self._cached_data['surdology'][0].copy()
                
                match_sr = re.search(r"Ш\.Р\. AD/AS = (.*?) м", text_surd)
                if match_sr:
                    data["sr"] = match_sr.group(1).strip()
                    
                match_rr = re.search(r"Р\.Р\. AD/AS = (.*?) м", text_surd)
                if match_rr:
                    data["rr"] = match_rr.group(1).strip()
                
                # self.surdologyChangedFromEditor.emit(data) 

            # 5. Диагноз
            cell_diag = self.get_cell('diagnosis', 0, 0)
            if cell_diag:
                cursor = cell_diag.firstCursorPosition()
                cursor.setPosition(cell_diag.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                html_diag = cursor.selection().toHtml()
                
                # Remove Times New Roman font family to prevent it from affecting the UI input
                # Use regex to be more robust against spaces
                html_diag = re.sub(r'font-family:\s*[\'"]?Times New Roman[\'"]?;?', '', html_diag, flags=re.IGNORECASE)
                
                # Удаляем "Острой ЛОР патологии..." из текста диагноза
                html_diag = re.sub(r'Острой ЛОР патологии на момент осмотра не выявлено\.', '', html_diag)
                html_diag = re.sub(r'(>)\s*ДИАГНОЗ:\s*', r'\1', html_diag)

                self.diagnosisChangedFromEditor.emit(html_diag)

            # 6. Рекомендации
            cell_rec = self.get_cell('recommendations', 0, 1)
            if cell_rec:
                cursor = cell_rec.firstCursorPosition()
                cursor.setPosition(cell_rec.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                html_rec = cursor.selection().toHtml()
                
                html_rec = re.sub(r'<p[^>]*>\s*<br\s*/?>\s*</p>\s*(?=<ul|<ol)', '', html_rec, flags=re.IGNORECASE)
                style = "margin-top: 0px; margin-bottom: 0px; margin-left: 10px; -qt-list-indent: 0;"
                html_rec = re.sub(r'<ul\b[^>]*>', f'<ul style="{style}">', html_rec)
                html_rec = re.sub(r'<ol\b[^>]*>', f'<ol style="{style}">', html_rec)
                
                self.recommendationsChangedFromEditor.emit(html_rec)

            # 7. Повторный прием
            cell_rep = self.get_cell('repeat', 0, 0)
            if cell_rep:
                cursor = cell_rep.firstCursorPosition()
                cursor.setPosition(cell_rep.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_rep = cursor.selection().toPlainText()
                
                if "Повторный прием" in text_rep:
                    lines = text_rep.split('\n')
                    if len(lines) > 1:
                        date_time = lines[1].strip()
                        parts = date_time.split(' ')
                        date = parts[0] if len(parts) > 0 else ""
                        time = parts[1] if len(parts) > 1 else ""
                        self.repeatChangedFromEditor.emit(True, date, time)

            # 8. Больничный лист
            cell_sl = self.get_cell('sick_leave', 0, 0)
            if cell_sl:
                cursor = cell_sl.firstCursorPosition()
                cursor.setPosition(cell_sl.lastCursorPosition().position(), QTextCursor.MoveMode.KeepAnchor)
                text_sl = cursor.selection().toPlainText()
                
                data = self._cached_data['sick_leave'][0].copy()
                
                # Парсинг номера: ищем "№" и берем следующее слово
                match_num = re.search(r"№\s*(\S+)", text_sl)
                if match_num:
                    data["number"] = match_num.group(1)
                
                # Парсинг дат: ищем "с ... по ..."
                # Используем более жадный поиск для дат, чтобы ловить неполные вводы
                # Добавляем re.IGNORECASE и удаляем завершающую точку
                match_date_from = re.search(r"с\s+([\d\.]+)", text_sl, re.IGNORECASE)
                if match_date_from:
                    data["date_from"] = match_date_from.group(1).rstrip('.')
                    
                match_date_to = re.search(r"по\s+([\d\.]+)", text_sl, re.IGNORECASE)
                if match_date_to:
                    data["date_to"] = match_date_to.group(1).rstrip('.')
                
                if match_num or match_date_from or match_date_to:
                    self.sickLeaveChangedFromEditor.emit(data)

        except Exception as e:
            print(f"Error checking exam content: {e}")
