"""Custom confirmation dialog (e.g. for 'delete deck').

The dialog sets its own colors. That way it does not inherit the
'background-color: transparent' of the deck overview, which made
QMessageBox show a black, unreadable background.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

STYLE = """
QDialog#confirmDialog {
    background-color: #ffffff;
}
QLabel {
    background-color: transparent;
    color: #222222;
}
QPushButton {
    background-color: #eeeeee;
    color: #222222;
    border: 1px solid #bbbbbb;
    border-radius: 4px;
    padding: 6px 18px;
}
QPushButton:hover {
    background-color: #e0e0e0;
}
QPushButton#confirmButton {
    background-color: #c81e1e;
    color: #ffffff;
    border: 1px solid #a01818;
}
QPushButton#confirmButton:hover {
    background-color: #a01818;
}
"""


class ConfirmDialog(QDialog):
    def __init__(self, title: str, text: str, confirm_text: str = "Löschen",
                 cancel_text: str = "Abbrechen", parent=None):
        super().__init__(parent)
        self.setObjectName("confirmDialog")
        self.setWindowTitle(title)
        self.setStyleSheet(STYLE)
        self.setMinimumWidth(380)

        font = QFont()
        font.setPointSize(11)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 15)
        layout.setSpacing(20)

        self.label = QLabel(text)
        self.label.setFont(font)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = QPushButton(cancel_text)
        self.confirm_button = QPushButton(confirm_text)
        self.confirm_button.setObjectName("confirmButton")   # for the red color in the stylesheet
        for button in (self.cancel_button, self.confirm_button):
            button.setFont(font)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button_layout.addWidget(button)
        layout.addLayout(button_layout)

        # Cancel is preselected: Enter or Escape never delete by accident
        self.confirm_button.setAutoDefault(False)
        self.cancel_button.setDefault(True)
        self.cancel_button.setFocus()

        self.cancel_button.clicked.connect(self.reject)
        self.confirm_button.clicked.connect(self.accept)

    @staticmethod
    def ask(parent, title: str, text: str, confirm_text: str = "Löschen",
            cancel_text: str = "Abbrechen") -> bool:
        """Shows the dialog and returns True if it was confirmed."""
        dialog = ConfirmDialog(title, text, confirm_text, cancel_text, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted


"""Test window"""
if __name__ == "__main__":
    app = QApplication([])
    print(ConfirmDialog.ask(None, "Deck löschen",
                            'Soll das Deck "Thermodynamik" mit 12 Karte(n) endgültig gelöscht werden?'))
