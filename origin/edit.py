from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton
from datetime import datetime




class NoteEditorWidget(QWidget):
    """Простой редактор заметок: заголовок, тело, кнопки сохранить/удалить."""


    def __init__(self, save_callback=None, delete_callback=None, parent=None):
        super().__init__(parent)
        self.save_callback = save_callback
        self.delete_callback = delete_callback
        self._build_ui()


    def _build_ui(self):
        self.layout = QVBoxLayout(self)
        self.title = QLineEdit(self)
        self.body = QTextEdit(self)
        self.save_btn = QPushButton("Save", self)
        self.delete_btn = QPushButton("Delete", self)


        self.save_btn.clicked.connect(self._on_save)
        self.delete_btn.clicked.connect(self._on_delete)


        self.layout.addWidget(self.title)
        self.layout.addWidget(self.body)
        self.layout.addWidget(self.save_btn)
        self.layout.addWidget(self.delete_btn)


    def load_note(self, note):
        self.title.setText(note.title if note else "")
        self.body.setPlainText(note.content if note else "")


    def _on_save(self):
        now = datetime.utcnow().isoformat()
        note = {
        "title": self.title.text(),
        "content": self.body.toPlainText(),
        "updated_at": now,
        }
        if self.save_callback:
            self.save_callback(note)


    def _on_delete(self):
        if self.delete_callback:
            self.delete_callback()