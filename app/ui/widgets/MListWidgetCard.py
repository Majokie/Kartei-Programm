from PySide6.QtCore import QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QListWidgetItem

from app.models.flashcard import Card


class MListWidgetCard(QListWidgetItem):
    """An entry in the card list that remembers its card (model)."""
    def __init__(self, card: Card | None):  # None = new card, not saved yet
        super().__init__()
        self.setSizeHint(QSize(0, 30))
        self.card = card
        font = QFont()
        font.setPointSize(15)
        self.setFont(font)
