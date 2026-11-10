# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'learning_site.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
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
from PySide6.QtWidgets import (QApplication, QGraphicsView, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_card_learner(object):
    def setupUi(self, card_learner):
        if not card_learner.objectName():
            card_learner.setObjectName(u"card_learner")
        card_learner.setEnabled(True)
        card_learner.resize(1149, 698)
        self.verticalLayoutWidget = QWidget(card_learner)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(-1, -1, 1151, 701))
        self.central_layout = QVBoxLayout(self.verticalLayoutWidget)
        self.central_layout.setObjectName(u"central_layout")
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_horizontal_layout = QHBoxLayout()
        self.central_horizontal_layout.setObjectName(u"central_horizontal_layout")
        self.left_layout = QVBoxLayout()
        self.left_layout.setObjectName(u"left_layout")

        self.central_horizontal_layout.addLayout(self.left_layout)

        self.central_vertical_layout = QVBoxLayout()
        self.central_vertical_layout.setObjectName(u"central_vertical_layout")
        self.deck_title = QLabel(self.verticalLayoutWidget)
        self.deck_title.setObjectName(u"deck_title")
        self.deck_title.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.deck_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.central_vertical_layout.addWidget(self.deck_title)

        self.upper_card_layout = QVBoxLayout()
        self.upper_card_layout.setObjectName(u"upper_card_layout")
        self.upper_card_scene = QGraphicsView(self.verticalLayoutWidget)
        self.upper_card_scene.setObjectName(u"upper_card_scene")

        self.upper_card_layout.addWidget(self.upper_card_scene)


        self.central_vertical_layout.addLayout(self.upper_card_layout)

        self.upper_button_layout = QHBoxLayout()
        self.upper_button_layout.setObjectName(u"upper_button_layout")
        self.next_card_button = QPushButton(self.verticalLayoutWidget)
        self.next_card_button.setObjectName(u"next_card_button")

        self.upper_button_layout.addWidget(self.next_card_button)

        self.edit_button = QPushButton(self.verticalLayoutWidget)
        self.edit_button.setObjectName(u"edit_button")

        self.upper_button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton(self.verticalLayoutWidget)
        self.delete_button.setObjectName(u"delete_button")

        self.upper_button_layout.addWidget(self.delete_button)


        self.central_vertical_layout.addLayout(self.upper_button_layout)

        self.lower_button_layout = QHBoxLayout()
        self.lower_button_layout.setObjectName(u"lower_button_layout")
        self.unknown = QPushButton(self.verticalLayoutWidget)
        self.unknown.setObjectName(u"unknown")

        self.lower_button_layout.addWidget(self.unknown)

        self.partially_known_button = QPushButton(self.verticalLayoutWidget)
        self.partially_known_button.setObjectName(u"partially_known_button")

        self.lower_button_layout.addWidget(self.partially_known_button)

        self.easily_known_button = QPushButton(self.verticalLayoutWidget)
        self.easily_known_button.setObjectName(u"easily_known_button")

        self.lower_button_layout.addWidget(self.easily_known_button)


        self.central_vertical_layout.addLayout(self.lower_button_layout)

        self.lower_card_scene = QVBoxLayout()
        self.lower_card_scene.setObjectName(u"lower_card_scene")
        self.graphicsView = QGraphicsView(self.verticalLayoutWidget)
        self.graphicsView.setObjectName(u"graphicsView")

        self.lower_card_scene.addWidget(self.graphicsView)


        self.central_vertical_layout.addLayout(self.lower_card_scene)

        self.central_vertical_layout.setStretch(0, 1)
        self.central_vertical_layout.setStretch(1, 10)
        self.central_vertical_layout.setStretch(2, 1)
        self.central_vertical_layout.setStretch(3, 1)
        self.central_vertical_layout.setStretch(4, 10)

        self.central_horizontal_layout.addLayout(self.central_vertical_layout)

        self.right_layout = QVBoxLayout()
        self.right_layout.setObjectName(u"right_layout")

        self.central_horizontal_layout.addLayout(self.right_layout)

        self.central_horizontal_layout.setStretch(0, 1)
        self.central_horizontal_layout.setStretch(1, 2)
        self.central_horizontal_layout.setStretch(2, 1)

        self.central_layout.addLayout(self.central_horizontal_layout)


        self.retranslateUi(card_learner)

        QMetaObject.connectSlotsByName(card_learner)
    # setupUi

    def retranslateUi(self, card_learner):
        card_learner.setWindowTitle(QCoreApplication.translate("card_learner", u"Form", None))
        self.deck_title.setText(QCoreApplication.translate("card_learner", u"<Deck>", None))
        self.next_card_button.setText(QCoreApplication.translate("card_learner", u"show solution", None))
        self.edit_button.setText(QCoreApplication.translate("card_learner", u"edit", None))
        self.delete_button.setText(QCoreApplication.translate("card_learner", u"delete button", None))
        self.unknown.setText(QCoreApplication.translate("card_learner", u"unknown", None))
        self.partially_known_button.setText(QCoreApplication.translate("card_learner", u"known but difficult", None))
        self.easily_known_button.setText(QCoreApplication.translate("card_learner", u"easily known", None))
    # retranslateUi

