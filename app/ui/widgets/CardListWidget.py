"""List of cards in the card editor."""
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QVBoxLayout, QWidget

from app.models.deck import Deck
from app.ui.widgets.MListWidgetCard import MListWidgetCard
from app.ui.widgets.deck import DeleteButton


class CardListWidget(QWidget):
    card_selected_signal = Signal(object)  # sends the Card object (model) or None for the new card
    delete_card_signal = Signal(object)    # red cross of a card clicked -> sends the Card object

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.list_view = QListWidget()   # QListWidget scrolls by itself, no ScrollArea needed
        self.layout.addWidget(self.list_view)
        self.list_view.itemSelectionChanged.connect(self.find_card)
        self.delete_item: MListWidgetCard | None = None  # entry that currently shows the cross

    def load_deck(self, deck: Deck, show_new_entry: bool = True):
        """Rebuilds the list. The cards are called Karte 1, Karte 2, ...
        At the very bottom (in italics) is the new card that has not been saved yet."""
        self.list_view.blockSignals(True)
        self.delete_item = None          # clear() also deletes the cross
        self.list_view.clear()
        for number, card in enumerate(deck.cards, start=1):
            item = MListWidgetCard(card)
            item.setText(f"Karte {number}")
            self.list_view.addItem(item)
        if show_new_entry:
            item = MListWidgetCard(None)            # None = new card, not saved yet
            item.setText(f"Karte {len(deck.cards) + 1}")
            font = item.font()
            font.setItalic(True)
            item.setFont(font)
            item.setForeground(QColor(120, 120, 120))
            self.list_view.addItem(item)
        self.list_view.blockSignals(False)
        self.update_delete_button()

    def select_card(self, card_id: str):
        """Selects a card without emitting card_selected_signal."""
        self.list_view.blockSignals(True)
        self.list_view.clearSelection()
        for row in range(self.list_view.count()):
            item = self.list_view.item(row)
            if item.card is not None and item.card.id == card_id:
                item.setSelected(True)
                self.list_view.setCurrentItem(item)
                break
        self.list_view.blockSignals(False)
        self.update_delete_button()

    def select_new_entry(self):
        """Selects the new card at the bottom without emitting card_selected_signal."""
        self.list_view.blockSignals(True)
        self.list_view.clearSelection()
        last = self.list_view.item(self.list_view.count() - 1)
        if last is not None and last.card is None:
            last.setSelected(True)
            self.list_view.setCurrentItem(last)
            self.list_view.scrollToItem(last)
        self.list_view.blockSignals(False)
        self.update_delete_button()

    def clear_selection(self):
        self.list_view.blockSignals(True)
        self.list_view.clearSelection()
        self.list_view.blockSignals(False)
        self.update_delete_button()

    def update_delete_button(self):
        """Shows the red cross right-aligned, only on the selected (saved) card."""
        if self.delete_item is not None:
            self.list_view.removeItemWidget(self.delete_item)   # deletes the old cross
            self.delete_item = None

        items = self.list_view.selectedItems()
        if len(items) != 1 or items[0].card is None:   # nothing to delete on the new card
            return
        item = items[0]

        row = QWidget()                                 # transparent row on top of the entry
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.addStretch()                             # pushes the cross all the way to the right
        button = DeleteButton()
        button.setFixedSize(24, 24)
        button.setToolTip("Karte löschen")
        button.clicked.connect(lambda: self.delete_card_signal.emit(item.card))
        layout.addWidget(button)

        self.list_view.setItemWidget(item, row)
        self.delete_item = item

    @Slot()
    def find_card(self):
        items = self.list_view.selectedItems()
        if len(items) == 1:
            self.card_selected_signal.emit(items[0].card)
        self.update_delete_button()
