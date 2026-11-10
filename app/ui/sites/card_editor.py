"""The editor for the cards of a deck.

Editing happens on a copy of the card.
- Existing cards are saved automatically when switching to another card or
  closing the editor (the save button works as well).
- The new, empty card at the bottom has to be saved once with save. Leaving it
  with changes before that asks for confirmation.
- Undo / redo (Ctrl+Z / Ctrl+Y) goes back up to 10 steps, always for the card
  currently shown (see app/logic/history.py).
"""
import copy
import sys

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
                               QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QStackedWidget,
                               QToolBar, QVBoxLayout, QWidget)

from app.logic.history import History
from app.models.deck import Deck
from app.models.flashcard import Card
from app.storage.repository import DeckRepository
from app.ui.canvas.grid_view import GridView
from app.ui.canvas.page_scene import TOOL_DRAW, TOOL_NONE, TOOL_TEXT, PageScene
from app.ui.canvas.items import TextItem
from app.ui.widgets.CardListWidget import CardListWidget
from app.ui.widgets.history_buttons import REDO, UNDO, HistoryButton
from app.ui.widgets.tool_settings import DrawSettings, TextSettings
from app.ui.widgets.toolbuttons import DrawButton, TextButton

# pages of the settings bar below the toolbar
SETTINGS_EMPTY, SETTINGS_TEXT, SETTINGS_DRAW = 0, 1, 2


class CardEditor(QWidget):
    closed_signal = Signal()  # the editor was closed

    def __init__(self, deck: Deck, repository: DeckRepository):
        super().__init__()
        self.deck = deck
        self.repository = repository

        self.card: Card = Card()   # working copy of the card currently shown
        self.is_new = True         # True = card is not in the deck yet
        self.dirty = False         # True = unsaved changes
        self.history = History()   # undo / redo (in memory only)
        self.discard_on_close = False  # True = do not save anything on close (deck is being deleted)
        self.front_scene: PageScene | None = None
        self.back_scene: PageScene | None = None

        self.setWindowTitle(f"Karteneditor – {deck.name}")
        self._build_layout()

        """Button connections"""
        self.text_button.toggled.connect(self.text_toggled)
        self.draw_button.toggled.connect(self.draw_toggled)
        self.save_button.clicked.connect(self.save_card)
        self.clear_button.clicked.connect(self.clear_card)
        self.close_button.clicked.connect(self.close)
        self.card_list.card_selected_signal.connect(self.select_card)
        self.card_list.delete_card_signal.connect(self.delete_card)
        self.text_settings.changed_signal.connect(self.text_settings_changed)
        self.draw_settings.changed_signal.connect(self.draw_settings_changed)
        self.draw_settings.committed_signal.connect(self.record_step)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)

        """Keyboard shortcuts"""
        QShortcut(QKeySequence.StandardKey.Undo, self, self.undo)        # Ctrl+Z
        QShortcut(QKeySequence.StandardKey.Redo, self, self.redo)        # Ctrl+Y (on Windows also Ctrl+Shift+Z)

        self.load_card(Card(), is_new=True)
        self.refresh_list()

    # ------------------------------------------------------------------ Layout
    def _build_layout(self):
        """Layout: card list on the left, front/back in the middle, deck name and buttons on the right"""
        self.main = QHBoxLayout(self)
        self.main.setSpacing(0)
        self.main.setContentsMargins(0, 5, 0, 5)

        label_font = QFont()
        label_font.setPointSize(24)

        # ----- left
        self.left_layout = QVBoxLayout()
        self.top_label = QLabel("front page: ", self)
        self.top_label.setFont(label_font)
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.left_layout.addWidget(self.top_label)

        self.card_list = CardListWidget()
        self.left_layout.addWidget(self.card_list)

        self.left_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.left_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.bottom_label = QLabel("back page: ", self)
        self.bottom_label.setFont(label_font)
        self.bottom_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.left_layout.addWidget(self.bottom_label)

        for index, stretch in enumerate((1, 9, 1, 1, 10)):
            self.left_layout.setStretch(index, stretch)
        self.main.addLayout(self.left_layout)

        # ----- middle
        self.central_layout = QVBoxLayout()
        self.top_view = GridView()
        self.central_layout.addWidget(self.top_view)

        self.toolbar = QToolBar()
        tool_policy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.text_button = TextButton()
        self.text_button.setToolTip("Textfeld setzen (danach in die Karte klicken)")
        self.text_button.setSizePolicy(tool_policy)
        self.toolbar.addWidget(self.text_button)
        self.draw_button = DrawButton()
        self.draw_button.setToolTip("Zeichnen")
        self.draw_button.setSizePolicy(tool_policy)
        self.toolbar.addWidget(self.draw_button)
        self.central_layout.addWidget(self.toolbar)

        # settings bar: shows the text or drawing settings depending on tool/selection
        self.toolbar_stacked = QStackedWidget(self)
        self.text_settings = TextSettings()
        self.draw_settings = DrawSettings()
        self.toolbar_stacked.addWidget(QWidget())           # SETTINGS_EMPTY
        self.toolbar_stacked.addWidget(self.text_settings)  # SETTINGS_TEXT
        self.toolbar_stacked.addWidget(self.draw_settings)  # SETTINGS_DRAW
        self.central_layout.addWidget(self.toolbar_stacked)

        self.bottom_view = GridView()
        self.central_layout.addWidget(self.bottom_view)

        for index, stretch in enumerate((10, 1, 1, 10)):
            self.central_layout.setStretch(index, stretch)
        self.main.addLayout(self.central_layout)

        # ----- right
        self.right_layout = QVBoxLayout()
        self.deck_name = QLabel(self.deck.name, self)
        name_font = QFont()
        name_font.setPointSize(30)
        self.deck_name.setFont(name_font)
        self.deck_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addWidget(self.deck_name)

        # undo / redo below the title
        self.history_layout = QHBoxLayout()
        self.history_layout.addStretch()
        self.undo_button = HistoryButton(UNDO, self)
        self.redo_button = HistoryButton(REDO, self)
        self.history_layout.addWidget(self.undo_button)
        self.history_layout.addWidget(self.redo_button)
        self.history_layout.addStretch()
        self.right_layout.addLayout(self.history_layout)
        self.right_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(15)
        self.button_layout.setContentsMargins(-1, 30, -1, 30)
        button_font = QFont()
        button_font.setPointSize(15)
        button_font.setKerning(False)
        self.save_button = QPushButton("save", self)
        self.clear_button = QPushButton("clear card", self)
        self.close_button = QPushButton("Close", self)
        for button in (self.save_button, self.clear_button, self.close_button):
            button.setSizePolicy(tool_policy)
            button.setFont(button_font)
            self.button_layout.addWidget(button)
        self.right_layout.addLayout(self.button_layout)

        for index, stretch in enumerate((1, 1, 16, 2)):   # title, arrows, space, buttons
            self.right_layout.setStretch(index, stretch)
        self.main.addLayout(self.right_layout)

        self.main.setStretch(0, 1)
        self.main.setStretch(1, 2)
        self.main.setStretch(2, 1)

    # ------------------------------------------------------------------ Showing a card
    def load_card(self, card: Card, is_new: bool):
        """Shows the card. 'card' is already a working copy."""
        self.card = card
        self.is_new = is_new
        self.dirty = False
        self.history.reset(card)   # the history only applies to this card
        self._build_scenes()
        self.update_history_buttons()

    def _build_scenes(self):
        images_dir = self.repository.images_dir(self.deck)
        new_image_path = lambda: self.repository.new_image_path(self.deck)

        self.front_scene = PageScene(self.card.front, images_dir, new_image_path)
        self.back_scene = PageScene(self.card.back, images_dir, new_image_path)
        for scene in (self.front_scene, self.back_scene):
            scene.changed_signal.connect(self.mark_dirty)
            scene.step_signal.connect(self.record_step)
            scene.text_placed_signal.connect(self.text_placed)
            scene.set_text_style(self.text_settings.family(), self.text_settings.size())
            scene.set_pen(self.draw_settings.color(), self.draw_settings.width())
            # selection or typing changes -> show the matching settings
            scene.selectionChanged.connect(lambda s=scene: self.selection_changed(s))
            scene.focusItemChanged.connect(lambda *args: self.update_settings_page())
        self.top_view.setScene(self.front_scene)
        self.bottom_view.setScene(self.back_scene)
        self.update_tool()

    @Slot()
    def mark_dirty(self):
        self.dirty = True

    # ------------------------------------------------------------------ Undo / redo
    @Slot()
    def record_step(self):
        """Remember the state of the card after a completed step"""
        if self.history.record(self.card):
            self.dirty = True
        self.update_history_buttons()

    def update_history_buttons(self):
        self.undo_button.setEnabled(self.history.can_undo())
        self.redo_button.setEnabled(self.history.can_redo())

    def _editing_text_item(self) -> TextItem | None:
        for scene in self._scenes():
            focus = scene.focusItem()
            if isinstance(focus, TextItem) and focus.is_editing():
                return focus
        return None

    @Slot()
    def undo(self):
        # while typing, Ctrl+Z first undoes single typing steps inside the text field
        item = self._editing_text_item()
        if item is not None and item.document().isUndoAvailable():
            item.document().undo()
            return
        state = self.history.undo()
        if state is not None:
            self._restore(state)

    @Slot()
    def redo(self):
        item = self._editing_text_item()
        if item is not None and item.document().isRedoAvailable():
            item.document().redo()
            return
        state = self.history.redo()
        if state is not None:
            self._restore(state)

    def _restore(self, state: Card):
        """Show a state from the history (the card keeps its ID)"""
        self.card = state
        self.dirty = True
        self._build_scenes()
        self.update_history_buttons()
        self.update_settings_page()

    def confirm_discard(self) -> bool:
        """Asks for confirmation if there are unsaved changes. True = continue."""
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self, "Ungespeicherte Änderungen",
            "Die aktuelle Karte hat ungespeicherte Änderungen.\nSollen sie verworfen werden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        return answer == QMessageBox.StandardButton.Yes

    # ------------------------------------------------------------------ Tools
    def update_tool(self):
        if self.text_button.isChecked():
            tool = TOOL_TEXT
        elif self.draw_button.isChecked():
            tool = TOOL_DRAW
        else:
            tool = TOOL_NONE
        for scene in (self.front_scene, self.back_scene):
            if scene is not None:
                scene.set_tool(tool)

    @Slot(bool)
    def text_toggled(self, checked: bool):
        if checked:
            self.draw_button.setChecked(False)   # only one tool active at a time
        self.update_tool()
        self.update_settings_page()

    @Slot(bool)
    def draw_toggled(self, checked: bool):
        if checked:
            self.text_button.setChecked(False)
        self.update_tool()
        self.update_settings_page()

    @Slot()
    def text_placed(self):
        self.text_button.setChecked(False)       # one text field per click on the button

    # ------------------------------------------------------------------ Settings bar
    def _scenes(self):
        return [scene for scene in (self.front_scene, self.back_scene) if scene is not None]

    def _selected_texts(self):
        return [item for scene in self._scenes() for item in scene.selected_text_items()]

    def _selected_strokes(self):
        return [item for scene in self._scenes() for item in scene.selected_stroke_items()]

    def update_settings_page(self):
        """Text settings: text button checked or a text field selected/being edited.
        Drawing settings: draw button checked or a stroke selected."""
        if self.draw_button.isChecked():
            page = SETTINGS_DRAW
        elif self.text_button.isChecked() or self._selected_texts():
            page = SETTINGS_TEXT
        elif self._selected_strokes():
            page = SETTINGS_DRAW
        else:
            page = SETTINGS_EMPTY
        self.toolbar_stacked.setCurrentIndex(page)

    def selection_changed(self, scene: PageScene):
        # only select on one side at a time so changes never affect both sides
        if scene.selectedItems():
            for other in self._scenes():
                if other is not scene:
                    other.clearSelection()
        # show the values of the selected element in the bar
        texts, strokes = self._selected_texts(), self._selected_strokes()
        if len(texts) == 1:
            model = texts[0].model
            self.text_settings.set_values(model.font_family, model.font_size)
            self._push_text_style()
        elif len(strokes) == 1 and not texts:
            model = strokes[0].model
            self.draw_settings.set_values(model.color, model.width)
            self._push_pen()
        self.update_settings_page()

    def _push_text_style(self):
        for scene in self._scenes():
            scene.set_text_style(self.text_settings.family(), self.text_settings.size())

    def _push_pen(self):
        for scene in self._scenes():
            scene.set_pen(self.draw_settings.color(), self.draw_settings.width())

    @Slot(str, int)
    def text_settings_changed(self, family: str, size: int):
        """applies to new text fields and to the selected or edited text field"""
        self._push_text_style()
        for item in self._selected_texts():
            item.set_font(family, size)
        self.record_step()

    @Slot(str, float)
    def draw_settings_changed(self, color: str, width: float):
        """applies to new strokes and to selected strokes"""
        self._push_pen()
        for item in self._selected_strokes():
            item.set_style(color, width)

    # ------------------------------------------------------------------ Actions
    def refresh_list(self):
        """Rebuild the list and select the current card"""
        self.card_list.load_deck(self.deck)
        self._restore_list_selection()

    @Slot(object)
    def select_card(self, card: Card | None):
        """Card clicked in the list (None = the new card at the bottom)"""
        if card is None:
            self.new_card()
            return
        if not self.is_new and card.id == self.card.id:
            return
        if not self.leave_current_card():
            self._restore_list_selection()
            return
        # Always take the current version from the deck: after autosaving, the list
        # may still hold the old card object.
        current = self.deck.find_card(card.id) or card
        self.load_card(copy.deepcopy(current), is_new=False)

    def open_card(self, card_id: str):
        """Show a specific card (e.g. from the edit button while learning).
        The current card is saved (or confirmed) first, just like when clicking in the list."""
        card = self.deck.find_card(card_id)
        if card is None:
            return
        if not self.is_new and self.card.id == card_id:
            return   # already open
        if not self.leave_current_card():
            return
        self.load_card(copy.deepcopy(card), is_new=False)
        self.card_list.select_card(card_id)

    def new_card(self):
        """Switch to the new, empty card at the bottom"""
        if self.is_new:
            self.card_list.select_new_entry()
            return
        if not self.leave_current_card():
            self._restore_list_selection()
            return
        self.load_card(Card(), is_new=True)
        self.card_list.select_new_entry()

    def mouseDoubleClickEvent(self, event, /):
        """Double click next to the cards -> new, empty card"""
        self.new_card()
        super().mouseDoubleClickEvent(event)

    @Slot()
    def clear_card(self):
        if self.card.front.is_empty() and self.card.back.is_empty():
            return
        self.card.front.elements.clear()
        self.card.back.elements.clear()
        self._build_scenes()
        self.record_step()   # can be undone

    @Slot()
    def save_card(self):
        if self.card.front.is_empty() and self.card.back.is_empty():
            QMessageBox.information(self, "Leere Karte", "Die Karte ist leer und wurde nicht gespeichert.")
            return
        was_new = self.is_new
        # put a copy into the deck so later changes only count after saving again
        self.repository.save_card(self.deck, copy.deepcopy(self.card))
        self.dirty = False
        self.is_new = False

        # Bottom card (the new one) saved -> a new, empty card appears below it right away.
        # That one is only saved when save is pressed on it.
        # Card further up saved -> it stays selected, no new card is added.
        if was_new:
            self.load_card(Card(), is_new=True)
        self.refresh_list()

    @Slot(object)
    def delete_card(self, card: Card):
        """Red cross in the list: delete the card permanently right away (no confirmation)"""
        stored = self.deck.find_card(card.id)
        if stored is None:
            return
        self.repository.delete_card(self.deck, stored)
        if not self.is_new and self.card.id == card.id:
            self.load_card(Card(), is_new=True)   # afterwards the new, empty card at the bottom is selected
        self.refresh_list()

    def autosave(self):
        """Save an existing card with changes (not the new card at the bottom)"""
        if self.is_new or not self.dirty:
            return
        self.repository.save_card(self.deck, copy.deepcopy(self.card))
        self.dirty = False

    def leave_current_card(self) -> bool:
        """Before switching/closing: save an existing card, ask for confirmation on the new card.
        True = continue."""
        if self.discard_on_close:
            return True
        self._finish_text_editing()
        if self.is_new:
            return self.confirm_discard()
        self.autosave()
        return True

    def _finish_text_editing(self):
        """Finish a text field that is being edited so the text is definitely applied"""
        item = self._editing_text_item()
        if item is not None:
            item.clearFocus()

    def _restore_list_selection(self):
        if self.is_new:
            self.card_list.select_new_entry()
        else:
            self.card_list.select_card(self.card.id)

    def closeEvent(self, event):
        if self.leave_current_card():   # saves existing cards automatically
            self.dirty = False
            self.closed_signal.emit()
            event.accept()
        else:
            event.ignore()


"""Test window for the card editor (saves into the normal data folder)"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    repo = DeckRepository()
    decks = repo.load_all()
    test_deck = decks[0] if decks else repo.create_deck("Testdeck")
    editor = CardEditor(test_deck, repo)
    editor.setMinimumSize(1000, 500)
    editor.show()
    sys.exit(app.exec())
