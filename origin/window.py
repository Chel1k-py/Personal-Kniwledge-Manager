from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QListWidget, QTextEdit, QPushButton, QLabel,
    QMessageBox, QCalendarWidget, QDateTimeEdit, QCheckBox, QListWidgetItem
)
from PyQt6.QtCore import QDateTime, Qt
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current = None

        self.setWindowTitle("Personal Knowledge Manager")
        self.setWindowIcon(QIcon("img/ico.png"))
        self.resize(1000, 700)

        self._build()
        self.load()
        self.check_rems()


    def _build(self):
        master = QWidget()
        self.setCentralWidget(master)
        layout = QHBoxLayout(master)

        left = QVBoxLayout()
        layout.addLayout(left, 30)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск: текст или #тег")
        self.search.textChanged.connect(self.load)
        left.addWidget(self.search)

        self.notes = QListWidget()
        self.notes.itemSelectionChanged.connect(self.on_note_selected)
        left.addWidget(self.notes)

        btns = QHBoxLayout()
        left.addLayout(btns)

        btn_new = QPushButton("Создать")
        btn_new.clicked.connect(self.on_new)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.on_delete)

        btns.addWidget(btn_new)
        btns.addWidget(btn_del)

        right = QVBoxLayout()
        layout.addLayout(right, 70)

        right.addWidget(QLabel("Заголовок:"))
        self.title = QLineEdit()
        right.addWidget(self.title)

        right.addWidget(QLabel("Текст заметки:"))
        self.text_i = QTextEdit()
        right.addWidget(self.text_i, 1)

        right.addWidget(QLabel("Теги:"))
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("тег, тег")
        right.addWidget(self.tags)

        self.checkbox = QCheckBox("Активировать напоминание")
        self.rem_date = QDateTimeEdit()
        self.rem_date.setCalendarPopup(True)
        self.rem_date.setDateTime(QDateTime.currentDateTime())

        right.addWidget(self.checkbox)
        right.addWidget(QLabel("Напоминание:"))
        right.addWidget(self.rem_date)

        self.save = QPushButton("Сохранить")
        self.save.clicked.connect(self.on_save)
        right.addWidget(self.save)

        right.addWidget(QLabel("Фильтр по дате:"))
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.load)
        right.addWidget(self.calendar)

    def load(self):
        self.notes.clear()
        search = self.search.text().strip()
        param = self.calendar.selectedDate().toString("yyyy-MM-dd")

        sql = ("SELECT id, title, created FROM notes "
               "WHERE DATE(created)=DATE(?)")
        params = [param]

        if search:
            if search[0] == "#":
                tag = search[1:].strip()
                sql = """
                SELECT DISTINCT n.id, n.title, n.created FROM notes n
                    LEFT JOIN note_tags nt ON n.id = nt.note_id
                    LEFT JOIN tags t ON nt.tag_id = t.id
                    WHERE t.name LIKE ? AND DATE(n.created)=DATE(?)
                    ORDER BY n.created DESC
                """
                params = [f"%{tag}%", param]
            else:
                sql += " AND (title LIKE ?)"
                like = f"%{search}%"
                print(like)
                params.extend([like])

        cur = self.db.execute(sql, tuple(params))
        rows = cur.fetchall()

        if not rows:
            self.clear()
            return

        for row in rows:
            note_id, title, created = row
            item = QListWidgetItem(f"{title} ({created[:10]})")
            item.setData(Qt.ItemDataRole.UserRole, note_id)
            self.notes.addItem(item)



    def on_note_selected(self):
        item = self.notes.currentItem()
        row = None
        if not item:
            self.current = None
            return


        try:
            note_id = item.data(Qt.ItemDataRole.UserRole)
            row = self.db.get_note(note_id)
        except Exception as e:
            print(e)

        if not row:
            self.current = None
            self.clear()
            return

        self.current = row[0]
        self.title.setText(row[1] or "")
        self.text_i.setPlainText(row[2] or "")

        tags = self.db.get_tags(self.current)
        self.tags.setText(", ".join(tags))

        rems = self.db.get_rem(self.current)
        if rems:
            rem = rems[0]
            dt_str = rem[1]
            dt = QDateTime.fromString(dt_str, "yyyy-MM-dd HH:mm:ss")
            self.rem_date.setDateTime(dt)
            self.checkbox.setChecked(True)
        else:
            self.checkbox.setChecked(False)
            self.rem_date.setDateTime(QDateTime.currentDateTime())

    def on_new(self):
        self.current = None
        self.clear()
        self.notes.clearSelection()

    def clear(self):
        self.title.clear()
        self.text_i.clear()
        self.tags.clear()
        self.checkbox.setChecked(False)
        self.rem_date.setDateTime(QDateTime.currentDateTime())

    def on_delete(self):
        if not self.current:
            QMessageBox.information(
                self,
                "Удаление",
                "Ничего не выбрано."
            )
            return
        reply = QMessageBox.question(
            self,
            "Удаление",
            "Удалить заметку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.execute("DELETE FROM notes "
                            "WHERE id = ?",
                            (self.current,))
            self.db.execute("DELETE FROM note_tags "
                            "WHERE note_id = ?",
                            (self.current,))
            self.db.execute("DELETE FROM reminders "
                            "WHERE note_id = ?",
                            (self.current,))
            self.current = None
            self.clear()
            self.load()

    def check(self, title, date_str):
        return self.db.execute(
            "SELECT id, title FROM notes "
            "WHERE title = ? AND DATE(created) = DATE(?) LIMIT 1",
            (title, date_str)
        ).fetchone()

    def on_save(self):
        title = self.title.text().strip()
        content = self.text_i.toPlainText().strip()
        tags = [i.strip() for i in self.tags.text().split(",") if i.strip()]
        rem_e = self.checkbox.isChecked()
        rem_dt = self.rem_date.dateTime().toString("yyyy-MM-dd HH:mm:ss") if rem_e else None
        sel_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите заголовок.")
            return

        if self.current:
            self.db.execute("UPDATE notes SET title = ?, content = ?"
                            "WHERE id = ?",
                            (title, content, self.current))
            self.db.set_tags(self.current, tags)

            exist_rem = self.db.get_rem(self.current)
            if rem_e:
                if exist_rem:
                    self.db.execute("UPDATE reminders SET remind_at = ?, mail_sent = 0 "
                                    "WHERE id = ?",
                                    (rem_dt, exist_rem[0][0]))
                else:
                    self.db.add_reminder(self.current, rem_dt)
            else:
                for r in exist_rem:
                    self.db.del_rem(r[0])

            QMessageBox.information(self, "Сохранено", "Заметка обновлена.")
            self.load()
            return

        check_tit = self.check(title, sel_date)
        if check_tit:
            reply = QMessageBox.question(
                self,
                "Заметка существует",
                "Заметка с таким названием на эту дату уже есть. Заменить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            self.db.execute("DELETE FROM notes "
                                "WHERE id = ?",
                            (check_tit[0],))
            self.db.execute("DELETE FROM note_tags "
                                "WHERE note_id = ?",
                            (check_tit[0],))
            self.db.execute("DELETE FROM reminders "
                                "WHERE note_id = ?",
                            (check_tit[0],))
        self.db.execute("INSERT INTO notes(title, content, created) "
                            "VALUES(?, ?, datetime('now'))",
                        (title, content))
        cur = self.db.execute("SELECT id FROM notes "
                              "WHERE title = ? AND DATE(created) = DATE(?) "
                              "ORDER BY created DESC LIMIT 1", (title, sel_date))
        note_id = cur.fetchone()[0]
        self.db.set_tags(note_id, tags)
        if rem_e and rem_dt:
            self.db.add_rem(note_id, rem_dt)

        QMessageBox.information(self, "Сохранено", "Заметка создана.")
        self.load()


    def check_rems(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rems = self.db.get_rem(now)
        for rem_id, note_id, remind_at, title in rems:
            msg = QMessageBox()
            msg.setWindowTitle("Напоминание")
            msg.setText(f"Напоминание для заметки:\n{title}\nВремя: {remind_at}")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            self.db.mark_reminder_sent(rem_id)
