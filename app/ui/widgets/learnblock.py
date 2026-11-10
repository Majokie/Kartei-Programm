"""Display of a learn block in the learn block overview.

LearnBlockWidget is PRELIMINARY: it only draws a simple rectangle with a
green or red border. The real graphic (block with a light bulb) will be
based on the template later; only paintEvent has to be replaced for that.
"""
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from app.models.learnblock import LearnBlock
from app.ui.widgets.deck import DeleteButton

GREEN = QColor(60, 170, 80)    # done for today
RED = QColor(210, 60, 60)      # cards still due today


class LearnBlockWidget(QWidget):
    """The graphic of the learn block (preliminary)."""
    def __init__(self, block: LearnBlock, deck_name: str, parent=None):
        super().__init__(parent)
        self.block = block
        self.deck_name = deck_name
        self.finished = False
        self.setFixedSize(180, 130)   # same size as the decks

    def set_finished(self, finished: bool):
        """green = done for today, red = cards still due today"""
        self.finished = finished
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(4, 4, self.width() - 8, self.height() - 8)

        painter.setPen(QPen(GREEN if self.finished else RED, 4))
        painter.setBrush(QColor(250, 250, 245))
        painter.drawRoundedRect(rect, 12, 12)

        painter.setPen(QColor(30, 30, 30))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(rect.adjusted(8, 10, -8, -40), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                         self.block.name)
        painter.setFont(QFont("Arial", 10))
        painter.setPen(QColor(90, 90, 90))
        painter.drawText(rect.adjusted(8, 70, -8, -8), Qt.AlignmentFlag.AlignCenter, self.deck_name)
        painter.end()


class LearnBlockContainer(QWidget):
    """Learn block with the buttons 'Lernen' and delete (appear on hover)"""
    learn_signal = Signal(object)   # sends the LearnBlock -> open the learning page
    delete_signal = Signal(object)  # sends the LearnBlock -> delete

    def __init__(self, block: LearnBlock, deck_name: str):
        super().__init__()
        self.block = block
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self.block_widget = LearnBlockWidget(block, deck_name)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)
        self.main_layout.addWidget(self.block_widget)

        self.button_layout = QHBoxLayout()
        self.learn_button = QPushButton("Lernen")
        self.delete_button = DeleteButton()
        self.learn_button.hide()
        self.delete_button.hide()
        self.button_layout.addWidget(self.learn_button)
        self.button_layout.addWidget(self.delete_button)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.setStretch(0, 8)
        self.main_layout.setStretch(1, 3)

        self.learn_button.clicked.connect(lambda: self.learn_signal.emit(self.block))
        self.delete_button.clicked.connect(lambda: self.delete_signal.emit(self.block))

    def set_finished(self, finished: bool):
        self.block_widget.set_finished(finished)

    def enterEvent(self, event):
        self.learn_button.show()
        self.delete_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.learn_button.hide()
        self.delete_button.hide()
        super().leaveEvent(event)


"""Test window with two learn blocks"""
if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QGridLayout(window)
    done = LearnBlockContainer(LearnBlock("Klausur", "x"), "Thermodynamik")
    done.set_finished(True)
    layout.addWidget(done, 0, 0)
    layout.addWidget(LearnBlockContainer(LearnBlock("Vokabeln", "y"), "Englisch"), 0, 1)
    window.show()
    app.exec()
