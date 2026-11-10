"""The learn block overview. Built like the deck overview, but with at most 10 learn blocks."""
import sys
from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox, QPushButton, QSizePolicy, QSpacerItem,
                               QVBoxLayout, QWidget)

from app.logic import leitner
from app.models.deck import Deck
from app.models.learnblock import METHOD_LEITNER, METHOD_SPACED_REPETITION, LearnBlock
from app.storage.repository import DeckRepository, LearnBlockRepository
from app.ui.widgets.confirm_dialog import ConfirmDialog
from app.ui.widgets.deck_grid import DeckGrid
from app.ui.widgets.learnblock import LearnBlockContainer

GRID_ROWS = 2
GRID_COLUMNS = 5   # 2 x 5 = at most 10 learn blocks


class LearnOverview(QWidget):
    learn_block_signal = Signal(object, object)  # (LearnBlock, Deck) -> open the learning page

    def __init__(self, deck_provider: Callable[[], list[Deck]], block_repository: LearnBlockRepository,
                 parent=None):
        """deck_provider: function that returns the current decks. This way the deck overview,
        editor and learning work with the same deck objects (changes are visible everywhere immediately)."""
        super().__init__(parent)
        self.deck_provider = deck_provider
        self.block_repository = block_repository
        self.decks: dict[str, Deck] = {}   # deck ID -> deck (reloaded whenever the page is shown)
        self.setMinimumSize(600, 450)

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)

        """Title"""
        self.label = QLabel("Lernblöcke", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Comic Sans MS", 20))
        self.verticalLayout.addWidget(self.label)

        self.block_grid = DeckGrid(self, rows=GRID_ROWS, columns=GRID_COLUMNS)
        self.verticalLayout.addWidget(self.block_grid)

        """Buttons at the bottom of the window"""
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.back_button = QPushButton("zurück", self)
        self.back_button.setFont(QFont("Comic Sans MS", 15))
        self.horizontalLayout.addWidget(self.back_button)
        self.horizontalLayout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.new_block_button = QPushButton("neuer Lernblock", self)
        self.new_block_button.setFont(QFont("Comic Sans MS", 15))
        self.horizontalLayout.addWidget(self.new_block_button)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 4)
        self.horizontalLayout.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.new_block_button.clicked.connect(self.new_block)

    def refresh(self):
        """Reloads decks and learn blocks and rebuilds the overview.
        Called every time the page is opened so that green/red is up to date."""
        self.decks = {deck.id: deck for deck in self.deck_provider()}
        for container in list(self.block_grid.decks):
            self.block_grid.remove_deck(container)

        now = datetime.now()
        for block in self.block_repository.load_all():
            deck = self.decks.get(block.deck_id)
            container = LearnBlockContainer(block, deck.name if deck else "(Deck gelöscht)")
            container.set_finished(leitner.is_finished_today(block, deck, now))
            container.learn_signal.connect(self.learn_block)
            container.delete_signal.connect(self.delete_block)
            self.block_grid.add_deck(container)

    @Slot()
    def new_block(self):
        if self.block_grid.is_full():
            QMessageBox.information(self, "Neuer Lernblock",
                                    f"Es können höchstens {GRID_ROWS * GRID_COLUMNS} Lernblöcke angelegt werden.")
            return
        decks = list(self.decks.values())
        if not decks:
            QMessageBox.information(self, "Neuer Lernblock", "Lege zuerst ein Deck an.")
            return
        dialog = NewBlockDialog(decks, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.block_repository.create(dialog.block_name(), dialog.selected_deck().id, dialog.selected_method())
            self.refresh()

    @Slot(object)
    def learn_block(self, block: LearnBlock):
        deck = self.decks.get(block.deck_id)
        if deck is None:
            QMessageBox.information(self, "Lernen", "Das Deck dieses Lernblocks gibt es nicht mehr.")
            return
        self.learn_block_signal.emit(block, deck)

    @Slot(object)
    def delete_block(self, block: LearnBlock):
        if ConfirmDialog.ask(self, "Lernblock löschen",
                             f"Soll der Lernblock \"{block.name}\" gelöscht werden?\n"
                             "Der Lernfortschritt geht verloren, die Karten bleiben erhalten."):
            self.block_repository.delete(block)
            self.refresh()


DIALOG_STYLE = """
QDialog { background-color: #ffffff; }
QLabel { background-color: transparent; color: #222222; }
QLineEdit, QComboBox { background-color: #ffffff; color: #222222; border: 1px solid #bbbbbb;
                       border-radius: 4px; padding: 4px; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #222222; }
QPushButton { background-color: #eeeeee; color: #222222; border: 1px solid #bbbbbb;
              border-radius: 4px; padding: 6px 18px; }
QPushButton:hover { background-color: #e0e0e0; }
"""


class NewBlockDialog(QDialog):
    """Window for creating a learn block: name, deck and learning method"""
    def __init__(self, decks: list[Deck], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neuer Lernblock")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(380)
        self.decks = decks

        form = QFormLayout()
        self.deck_box = QComboBox()
        for deck in decks:
            self.deck_box.addItem(deck.name)
        self.method_box = QComboBox()
        self.method_box.addItem("Leitner-System", METHOD_LEITNER)
        self.method_box.addItem("Spaced Repetition (kommt später)", METHOD_SPACED_REPETITION)
        self.method_box.model().item(1).setEnabled(False)   # not selectable in 1.0 yet
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("z. B. Klausur Thermodynamik")
        form.addRow("Deck:", self.deck_box)
        form.addRow("Lernmethode:", self.method_box)
        form.addRow("Name:", self.name_input)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel_button = QPushButton("Abbrechen")
        self.ok_button = QPushButton("Erstellen")
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.ok_button)
        self.ok_button.setDefault(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 15)
        layout.setSpacing(20)
        layout.addLayout(form)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept)

    def selected_deck(self) -> Deck:
        return self.decks[self.deck_box.currentIndex()]

    def selected_method(self) -> str:
        return self.method_box.currentData()

    def block_name(self) -> str:
        """Without a custom name the block is named after the deck"""
        return self.name_input.text().strip() or self.selected_deck().name


"""Test window for the learn block overview"""
if __name__ == "__main__":
    app = QApplication([])
    window = QMainWindow()
    overview = LearnOverview(DeckRepository().load_all, LearnBlockRepository())
    overview.refresh()
    window.setCentralWidget(overview)
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())
