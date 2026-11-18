"""Display of a study folder in the folder overview, plus the container with the buttons.

The image is loaded from pictures/study-folder.png. As long as that file does not
exist, a simple folder shape is drawn instead.
"""
from pathlib import Path

from PySide6.QtCore import QRectF, Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QStackedLayout, QVBoxLayout, QWidget)

from app.models.study import StudyFolder
from app.ui.widgets.deck import DeleteButton

PICTURES_DIR = Path(__file__).resolve().parent / "pictures"
FOLDER_IMAGE = PICTURES_DIR / "study-folder.png"
WIDGET_WIDTH, WIDGET_HEIGHT = 180, 130   # same size as the decks


class FolderWidget(QWidget):
    """Shows a study folder (model) as an image with its name. Double click renames it."""
    renamed_signal = Signal(object)  # sends the folder (model) after renaming

    def __init__(self, folder: StudyFolder, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.setFixedSize(WIDGET_WIDTH, WIDGET_HEIGHT)

        # label and input field are stacked so the name can be edited "live"
        self.layout = QStackedLayout()
        font = QFont("Arial", 16)
        self.name = QLabel(folder.name)          # 0 = label
        self.name.setFont(font)
        self.name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name.setStyleSheet("background-color: transparent;")
        self.layout.addWidget(self.name)
        self.name_input = QLineEdit(folder.name)  # 1 = input
        self.name_input.setFont(font)
        self.name_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_input.editingFinished.connect(self.editing_finished)
        self.layout.addWidget(self.name_input)
        self.layout.setCurrentIndex(0)
        self.setLayout(self.layout)

        pixmap = QPixmap(str(FOLDER_IMAGE))
        self.representation = None if pixmap.isNull() else pixmap.scaled(
            WIDGET_WIDTH, WIDGET_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Rename via double click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.name_input.setText(self.folder.name)
            self.layout.setCurrentIndex(1)
            self.name_input.selectAll()
            self.name_input.setFocus()
        else:
            super().mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.representation is not None:
            painter.drawPixmap(0, 0, self.representation)
        else:
            # placeholder until study-folder.png exists: a simple folder shape
            painter.setPen(QPen(QColor(150, 110, 40), 2))
            painter.setBrush(QColor(240, 200, 110))
            painter.drawRoundedRect(QRectF(10, 8, 70, 30), 6, 6)                 # tab
            painter.drawRoundedRect(QRectF(10, 22, WIDGET_WIDTH - 20, WIDGET_HEIGHT - 32), 8, 8)
        painter.end()

    @Slot()
    def editing_finished(self):
        new_name = self.name_input.text().strip()
        self.layout.setCurrentIndex(0)
        if not new_name or new_name == self.folder.name:
            return
        self.folder.name = new_name
        self.name.setText(new_name)
        self.renamed_signal.emit(self.folder)


class FolderContainer(QWidget):
    """Study folder with the buttons 'Edit' and delete (appear on hover)"""
    edit_signal = Signal(object)     # sends the folder (model) -> open the study sheet editor
    renamed_signal = Signal(object)  # folder was renamed -> save
    delete_signal = Signal(object)   # folder should be deleted

    def __init__(self, folder: StudyFolder):
        super().__init__()
        self.folder = folder
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.folder_widget = FolderWidget(folder)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)
        self.main_layout.addWidget(self.folder_widget)

        self.button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit")
        self.delete_button = DeleteButton()
        self.delete_button.setToolTip("Delete folder")
        self.edit_button.hide()
        self.delete_button.hide()
        self.button_layout.addWidget(self.edit_button)
        self.button_layout.addWidget(self.delete_button)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.setStretch(0, 8)
        self.main_layout.setStretch(1, 3)

        self.edit_button.clicked.connect(lambda: self.edit_signal.emit(self.folder))
        self.delete_button.clicked.connect(lambda: self.delete_signal.emit(self.folder))
        self.folder_widget.renamed_signal.connect(self.renamed_signal.emit)

    def enterEvent(self, event):
        self.edit_button.show()
        self.delete_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.edit_button.hide()
        self.delete_button.hide()
        super().leaveEvent(event)


"""Test window with two folders"""
if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QGridLayout(window)
    layout.addWidget(FolderContainer(StudyFolder("Physics")), 0, 0)
    layout.addWidget(FolderContainer(StudyFolder("Mathematics")), 0, 1)
    window.show()
    app.exec()
