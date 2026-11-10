import sys
from pathlib import Path

# Makes "import app..." work even when this file is started directly
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from app.models.deck import Deck
from app.models.flashcard import Card
from app.models.learnblock import LearnBlock
from app.storage.repository import DeckRepository, LearnBlockRepository
from app.ui.sites.card_editor import CardEditor
from app.ui.sites.deck_overview import DeckOverview
from app.ui.sites.learn_overview import LearnOverview
from app.ui.sites.learn_session import LearnSession
from app.ui.sites.mainmenu import MainMenu


class MainWindow(QMainWindow):
    """Main window of the application. The individual pages live in a QStackedWidget;
    buttons that work across pages are also connected here."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Karteikartenprogramm")

        self.repository = DeckRepository()              # loading and saving decks
        self.block_repository = LearnBlockRepository()  # loading and saving learn blocks
        self.card_editor: CardEditor | None = None

        self.stacked_widget = QStackedWidget()
        self.main_menu = MainMenu()                          # Index 0
        self.stacked_widget.addWidget(self.main_menu)
        self.deck_overview = DeckOverview(self.repository)  # Index 1
        self.stacked_widget.addWidget(self.deck_overview)
        self.learn_overview = LearnOverview(self.deck_overview.all_decks, self.block_repository)  # Index 2
        self.stacked_widget.addWidget(self.learn_overview)
        self.learn_session = LearnSession(self.repository, self.block_repository)  # Index 3
        self.stacked_widget.addWidget(self.learn_session)
        self.setCentralWidget(self.stacked_widget)

        """Button connections"""
        self.main_menu.decks_button.clicked.connect(self.show_decks)
        self.main_menu.learning_button.clicked.connect(self.show_learning)
        self.main_menu.exit_button.clicked.connect(self.close)
        self.deck_overview.back_button.clicked.connect(self.show_main_menu)
        self.deck_overview.edit_deck_signal.connect(self.show_card_editor)
        self.deck_overview.deck_deleting_signal.connect(self.close_editor_for_deck)
        self.deck_overview.deck_deleting_signal.connect(
            lambda deck: self.block_repository.delete_for_deck(deck.id))  # also delete the learn blocks of the deck
        self.deck_overview.learn_deck_signal.connect(self.show_learning)  # "Lernen" on a deck -> learn blocks
        self.learn_overview.back_button.clicked.connect(self.show_main_menu)
        self.learn_overview.learn_block_signal.connect(self.start_learning)
        self.learn_session.back_signal.connect(self.show_learning)
        self.learn_session.edit_card_signal.connect(self.edit_card_from_learning)

    @Slot()
    def show_decks(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_learning(self, *args):   # *args: can be called by buttons and by the deck signal
        self.learn_overview.refresh()   # update green/red and new cards
        self.stacked_widget.setCurrentIndex(2)

    @Slot(object, object)
    def start_learning(self, block: LearnBlock, deck: Deck):
        """Show the learning page inside the main window (no new window)"""
        self.learn_session.start(block, deck)
        self.stacked_widget.setCurrentIndex(3)

    @Slot()
    def show_main_menu(self):
        self.stacked_widget.setCurrentIndex(0)

    @Slot(object)
    def show_card_editor(self, deck: Deck) -> CardEditor | None:
        """Opens the card editor for a deck (or brings the open one to the front).
        Returns the editor, or None if the old editor could not be closed."""
        if self.card_editor is not None and self.card_editor.isVisible():
            if self.card_editor.deck is deck:
                self.card_editor.raise_()
                self.card_editor.activateWindow()
                return self.card_editor
            if not self.card_editor.close():   # asks about unsaved changes
                return None
        self.card_editor = CardEditor(deck, self.repository)
        self.card_editor.closed_signal.connect(self.editor_closed)
        self.card_editor.setMinimumSize(1000, 500)
        self.card_editor.show()
        return self.card_editor

    @Slot(object, object)
    def edit_card_from_learning(self, deck: Deck, card: Card):
        """edit button while learning: open the editor and show exactly this card"""
        editor = self.show_card_editor(deck)
        if editor is not None:
            editor.open_card(card.id)

    @Slot()
    def editor_closed(self):
        """Editor closed: while learning, redisplay the (possibly changed) card,
        otherwise go back to the deck overview as before"""
        if self.stacked_widget.currentWidget() is self.learn_session:
            self.learn_session.refresh_card()
        else:
            self.show_decks()

    @Slot(object)
    def close_editor_for_deck(self, deck: Deck):
        """Closes the editor without asking when its deck is being deleted"""
        if self.card_editor is not None and self.card_editor.deck is deck:
            self.card_editor.discard_on_close = True   # do not save anything, the deck is being deleted
            self.card_editor.close()
            self.card_editor = None

    def closeEvent(self, event):
        # close an open editor first so that unsaved changes are handled
        if self.card_editor is not None and self.card_editor.isVisible() and not self.card_editor.close():
            event.ignore()
            return
        event.accept()


def run():
    """Starts the application"""
    application = QApplication(sys.argv)
    window = MainWindow()
    window.setMinimumSize(800, 600)
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    run()
