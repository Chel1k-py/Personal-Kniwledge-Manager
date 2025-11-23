# ui/password_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtWidgets import QDialogButtonBox


class Password(QDialog):

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Вход")
        self.setFixedSize(360, 150)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel()
        layout.addWidget(self.label)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password)

        self.btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.btns.accepted.connect(self.ok)
        self.btns.rejected.connect(self.reject)
        layout.addWidget(self.btns)

        if self.db.get_password():
            self.mode = "login"
            self.label.setText("Введите пароль для входа:")
            self.password.setPlaceholderText("Пароль")
        else:
            self.mode = "create"
            self.label.setText("Создайте пароль для входа:")
            self.password.setPlaceholderText("Введите новый пароль")


    def ok(self):
        txt = self.password.text().strip()
        if not txt:
            QMessageBox.warning(self, "Ошибка", "Пароль не может быть пустым.")
            return

        if self.mode == "create":
            self.db.set_password(txt)
            QMessageBox.information(self, "Готово", "Пароль создан.")
            self.accept()
            return

        if self.db.verify(txt):
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль.")
