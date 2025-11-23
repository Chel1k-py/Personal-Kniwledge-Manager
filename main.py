import sys
from PyQt6.QtWidgets import QApplication, QDialog
from db import Database
from origin.window import MainWindow
from origin.dialog import Password
from reminders import Reminder


def main():
    app = QApplication(sys.argv)
    db = Database()
    check = Password(db)
    if check.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)


    window = MainWindow(db)
    window.show()
    rem = Reminder(db, window)

    app.exec()


if __name__ == "__main__":
    main()