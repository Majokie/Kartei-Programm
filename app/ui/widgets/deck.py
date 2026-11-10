"""Display of a deck in the deck overview. Further down is the container with the buttons."""
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt, Signal, Slot
from PySide6.QtGui import QColor, QDrag, QFont, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QStackedLayout, QVBoxLayout, QWidget)

from app.models.deck import Deck

# folder with the images, relative to this file (independent of the drive)
PICTURES_DIR = Path(__file__).resolve().parent / "pictures"


class DeckWidget(QWidget):
    """Shows a deck (model) as an image with its name. Double click renames it."""
    renamed_signal = Signal(object)  # sends the deck (model) after renaming

    def __init__(self, deck: Deck, parent=None):
        super().__init__(parent)
        self.deck = deck
        self.setStyleSheet("background-color: transparent;")
        self.setFixedSize(180, 130)  # several decks side by side -> fixed size

        # label and input field are stacked so the name can be edited "live"
        self.layout = QStackedLayout()
        font = QFont("Arial", 16)

        self.name = QLabel(deck.name)  # 0 = label
        self.name.setFont(font)
        self.name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name)

        self.label_input = QLineEdit(deck.name)  # 1 = input
        self.label_input.setFont(font)
        self.label_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_input.editingFinished.connect(self.editing_finished)
        self.layout.addWidget(self.label_input)

        self.layout.setCurrentIndex(0)
        self.setLayout(self.layout)

        """Image used to display the decks"""
        pixmap = QPixmap(str(PICTURES_DIR / "card-deck.png"))
        self.representation = pixmap.scaled(180, 130, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)

    """Drag and drop"""
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            drag.setHotSpot(event.pos())
            drag.setMimeData(self.mimeData())
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec(Qt.DropAction.MoveAction)
        else:
            super().mousePressEvent(event)

    """Rename via double click"""
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.label_input.setText(self.deck.name)
            self.layout.setCurrentIndex(1)
            self.label_input.selectAll()
            self.label_input.setFocus()
        else:
            super().mouseDoubleClickEvent(event)

    def mimeData(self):
        mime_data = QMimeData()
        mime_data.setText(self.deck.id)
        return mime_data

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.representation)
        painter.end()

    @Slot()
    def editing_finished(self):
        new_name = self.label_input.text().strip()
        self.layout.setCurrentIndex(0)
        if not new_name or new_name == self.deck.name:
            return
        self.deck.name = new_name
        self.name.setText(new_name)
        self.renamed_signal.emit(self.deck)


class DeleteButton(QPushButton):
    """Narrow button that only shows a red cross made of two diagonals."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(24)                      # much narrower than Lernen/Bearbeiten
        self.setToolTip("Deck löschen")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        super().paintEvent(event)                   # draw the normal button background
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(200, 30, 30))
        pen.setWidthF(2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        size = min(self.width(), self.height()) - 10  # square cross with a small margin
        left = (self.width() - size) / 2
        top = (self.height() - size) / 2
        painter.drawLine(int(left), int(top), int(left + size), int(top + size))
        painter.drawLine(int(left + size), int(top), int(left), int(top + size))
        painter.end()


class DeckContainer(QWidget):
    """Deck with the buttons 'Lernen' and 'Bearbeiten' (appear on hover)"""
    edit_signal = Signal(object)     # sends the deck (model) -> open the card editor
    learn_signal = Signal(object)    # sends the deck (model) -> learning
    renamed_signal = Signal(object)  # deck was renamed -> save
    delete_signal = Signal(object)   # deck should be deleted

    def __init__(self, deck: Deck):
        super().__init__()
        self.deck = deck
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.deck_widget = DeckWidget(deck)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)
        self.main_layout.addWidget(self.deck_widget)

        self.button_layout = QHBoxLayout()
        self.learn_button = QPushButton("Lernen")
        self.edit_button = QPushButton("Bearbeiten")
        self.delete_button = DeleteButton()
        self.learn_button.hide()
        self.edit_button.hide()
        self.delete_button.hide()
        self.button_layout.addWidget(self.learn_button)
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.delete_button)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.setStretch(0, 8)
        self.main_layout.setStretch(1, 3)

        self.edit_button.clicked.connect(lambda: self.edit_signal.emit(self.deck))
        self.learn_button.clicked.connect(lambda: self.learn_signal.emit(self.deck))
        self.delete_button.clicked.connect(lambda: self.delete_signal.emit(self.deck))
        self.deck_widget.renamed_signal.connect(self.renamed_signal.emit)

    def enterEvent(self, event):
        self.learn_button.show()
        self.edit_button.show()
        self.delete_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.learn_button.hide()
        self.edit_button.hide()
        self.delete_button.hide()
        super().leaveEvent(event)


"""Test window with two decks"""
if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QGridLayout(window)
    layout.addWidget(DeckContainer(Deck("Elektrotechnik")), 0, 0)
    layout.addWidget(DeckContainer(Deck("Thermodynamik")), 0, 1)
    window.show()
    app.exec()
