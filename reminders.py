from PyQt6.QtCore import QTimer, QObject, QUrl
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtWidgets import QMessageBox
from datetime import datetime


class Reminder(QObject):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent = parent

        self.sound = QSoundEffect()
        self.sound.setSource(QUrl.fromLocalFile("sounds/notify.wav"))
        self.sound.setVolume(1.0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
        self.timer.start(60_000)

        QTimer.singleShot(2000, self.check)

    def check(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql = """
        SELECT r.id, r.note_id, r.remind_at, n.title
        FROM reminders r
        LEFT JOIN notes n ON r.note_id = n.id
        WHERE r.mail_sent = 0 AND r.remind_at <= ?
        ORDER BY r.remind_at ASC
        """

        rows = self.db.execute(sql, (now,)).fetchall()

        for rem_id, note_id, remind_at, title in rows:
            self._alert(title, remind_at)
            self._mark_sent(rem_id)

    def _alert(self, title: str, remind_at: str):
        self.sound.play()

        msg = QMessageBox(self.parent)
        msg.setWindowTitle("Напоминание")
        msg.setText(
                    f"Напоминание по заметке:\n\n"
                    f"{title}\n\n"
                    f"Время: {remind_at}"
                )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _mark_sent(self, rem_id: int):
        self.db.execute("UPDATE reminders "
                        "SET mail_sent = 1 "
                        "WHERE id = ?",
                        (rem_id,)
                        )
