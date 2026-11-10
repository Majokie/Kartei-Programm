# -*- coding: utf-8 -*-
import sys

################################################################################
## Form generated from reading UI file 'mainmenu.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)
#from Scripts.mainmenu import Ui_MainWindow

"""Creates the main menu page. Most of it was taken from the PySide Designer"""
class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(600, 600) # the window must not get smaller


    
        self.main_Layout = QVBoxLayout(self)
        self.main_Layout.setSpacing(10)
        self.main_Layout.setContentsMargins(0, 20, 0, 20)
    
        self.upper_horizontal_Layout = QHBoxLayout()
        self.upper_horizontal_Layout.setSpacing(6)
        self.upper_horizontal_Layout.setContentsMargins(100, 0, 100, 0)
        """Adds the title at the very top of the window and sets its properties"""
        self.title_label = QLabel(self)
        self.title_label.setText("Karteikartenprogramm")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.title_label.sizePolicy().hasHeightForWidth())
        self.title_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(25)
        self.title_label.setFont(font)
    
        self.upper_horizontal_Layout.addWidget(self.title_label)
    
    
        self.main_Layout.addLayout(self.upper_horizontal_Layout)
        """Layout that limits the buttons on the left and right"""
        self.lower_horizontal_Layout = QHBoxLayout()
        self.lower_horizontal_Layout.setContentsMargins(200, -1, 200, -1)
        """Layout that controls the vertical arrangement of the buttons"""
        self.vertical_button_layout = QVBoxLayout()
        self.vertical_button_layout.setSpacing(30)
        self.vertical_button_layout.setContentsMargins(-1, 60, -1, 80)

        """Adds the three buttons of the main menu"""
        self.learning_button = QPushButton(self)
        self.learning_button.setText("Learning")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.learning_button.sizePolicy().hasHeightForWidth())
        self.learning_button.setSizePolicy(sizePolicy1)
    
        self.vertical_button_layout.addWidget(self.learning_button)
    
        self.decks_button = QPushButton(self)
        self.decks_button.setText("Decks")
        sizePolicy1.setHeightForWidth(self.decks_button.sizePolicy().hasHeightForWidth())
        self.decks_button.setSizePolicy(sizePolicy1)
    
        self.vertical_button_layout.addWidget(self.decks_button)
    
        self.exit_button = QPushButton(self)
        self.exit_button.setText("Exit")
        sizePolicy1.setHeightForWidth(self.exit_button.sizePolicy().hasHeightForWidth())
        self.exit_button.setSizePolicy(sizePolicy1)
    
        self.vertical_button_layout.addWidget(self.exit_button)
    
    
        self.lower_horizontal_Layout.addLayout(self.vertical_button_layout)
    
    
        self.main_Layout.addLayout(self.lower_horizontal_Layout)
        """Sets the size ratios of the layout contents"""
        self.main_Layout.setStretch(0, 1)
        self.main_Layout.setStretch(1, 2)






