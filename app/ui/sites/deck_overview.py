"""The deck overview, in which the individual decks are displayed in containers."""
import sys

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton,
                               QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from app.models.deck import Deck
from app.storage.repository import DeckRepository
from app.ui.widgets.confirm_dialog import ConfirmDialog
from app.ui.widgets.deck import DeckContainer
from app.ui.widgets.deck_grid import DeckGrid


class DeckOverview(QWidget):
    edit_deck_signal = Signal(object)   # deck (model) should be opened in the card editor
    learn_deck_signal = Signal(object)  # deck (model) should be learned
    deck_deleting_signal = Signal(object)  # deck is about to be deleted (e.g. close an open editor)

    def __init__(self, repository: DeckRepository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.setStyleSheet("background-color: transparent;")
        self.name_window = NameWindow()

        self.resize(1111, 839)
        self.setMinimumSize(600, 450)

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)

        """Title"""
        self.label = QLabel("Deckübersicht", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Comic Sans MS", 20))
        self.verticalLayout.addWidget(self.label)

        self.deck_overview = DeckGrid(self)  # grid for the deck containers
        self.verticalLayout.addWidget(self.deck_overview)

        """Buttons at the bottom of the window"""
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(2)

        self.back_button = QPushButton("zurück", self)
        self.back_button.setFont(QFont("Comic Sans MS", 15))
        self.horizontalLayout.addWidget(self.back_button)

        self.horizontalLayout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.new_Deck_button = QPushButton("neues Deck", self)
        self.new_Deck_button.setFont(QFont("Comic Sans MS", 15))
        self.horizontalLayout.addWidget(self.new_Deck_button)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 4)
        self.horizontalLayout.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.new_Deck_button.clicked.connect(self.new_deck)
        self.name_window.ok_button.clicked.connect(self.create_deck)
        self.name_window.input.returnPressed.connect(self.create_deck)

        self.load_decks()

    def all_decks(self) -> list[Deck]:
        """The decks currently shown in the overview (the same objects as in the editor)."""
        return [container.deck for container in self.deck_overview.decks]

    def load_decks(self):
        for deck in self.repository.load_all():
            self.add_deck_widget(deck)

    def add_deck_widget(self, deck: Deck):
        container = DeckContainer(deck)
        container.edit_signal.connect(self.edit_deck_signal.emit)
        container.learn_signal.connect(self.learn_deck_signal.emit)
        container.renamed_signal.connect(self.repository.save_deck)  # renaming is saved immediately
        container.delete_signal.connect(self.delete_deck)
        self.deck_overview.add_deck(container)

    @Slot(object)
    def delete_deck(self, deck: Deck):
        """Asks for confirmation and then deletes the deck with all its cards"""
        confirmed = ConfirmDialog.ask(
            self, "Deck löschen",
            f"Soll das Deck \"{deck.name}\" mit {len(deck.cards)} Karte(n) endgültig gelöscht werden?")
        if not confirmed:
            return
        self.deck_deleting_signal.emit(deck)   # first, so that an open editor does not save anything anymore
        self.repository.delete_deck(deck)
        for container in list(self.deck_overview.decks):
            if container.deck is deck:
                self.deck_overview.remove_deck(container)

    @Slot()
    def new_deck(self):
        self.name_window.input.clear()
        self.name_window.show()
        self.name_window.input.setFocus()

    @Slot()
    def create_deck(self):
        name = self.name_window.input.text().strip()
        if not name:
            return
        deck = self.repository.create_deck(name)
        self.add_deck_widget(deck)
        self.name_window.hide()


class NameWindow(QWidget):
    """Window for entering the name of a new deck"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neues Deck")
        self.setFixedSize(400, 300)
        self.layout = QHBoxLayout(self)
        self.label = QLabel("Name: ")
        self.input = QLineEdit()
        self.ok_button = QPushButton("OK")
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input)
        self.layout.addWidget(self.ok_button)


"""Test window for the deck overview"""
if __name__ == "__main__":
    app = QApplication([])
    window = QMainWindow()
    window.setCentralWidget(DeckOverview(DeckRepository()))
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())
