from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCalendarWidget




class CalendarWidget(QWidget):
    def __init__(self, date_selected_callback=None, parent=None):
        super().__init__(parent)
        self.date_selected_callback = date_selected_callback
        self.calendar = QCalendarWidget(self)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.calendar)
        self.calendar.clicked.connect(self._on_date_selected)


    def _on_date_selected(self, qdate):
        if self.date_selected_callback:
            self.date_selected_callback(qdate.toPyDate())