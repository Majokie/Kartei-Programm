from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QToolBar, QToolButton
from pathlib import Path

# folder with the images, relative to this file (independent of the drive)
PICTURES_DIR = Path(__file__).resolve().parent / "pictures"

"""Defines the icons of the tool buttons used when editing the scenes"""
class TextButton(QToolButton):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        qicon = QIcon()
        qicon.addFile(str(PICTURES_DIR / "textbutton.png"))
        self.setIcon(qicon)

class ImageButton(QToolButton):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        qicon = QIcon()
        qicon.addFile(str(PICTURES_DIR / "imagebutton.png"))
        self.setIcon(qicon)

class DrawButton(QToolButton):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        qicon = QIcon()
        qicon.addFile(str(PICTURES_DIR / "penbutton.png"))
        self.setIcon(qicon)


