"""The editor for the study sheets of a study folder.

Works like the card editor, but with one page in DIN A4 format:
- The list on the left shows the titles of the sheets (order of creation).
  The title is the text field at the top left; it cannot be moved or deleted.
- Existing sheets are saved automatically when switching to another sheet or
  closing the editor (the save button works as well).
- The new sheet at the bottom of the list has to be saved once with save.
  Leaving it with changes before that asks for confirmation.
- Undo / redo (Ctrl+Z / Ctrl+Y) goes back up to 10 steps for the sheet shown.
- Mouse wheel zooms, holding the right mouse button moves the sheet around.
"""
import copy
import sys

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSizePolicy,
                               QSpacerItem, QStackedWidget, QToolBar, QVBoxLayout, QWidget)

from app.logic.history import History
from app.models.study import DEFAULT_TITLE, SHEET_HEIGHT, SHEET_WIDTH, StudyFolder, StudySheet, new_sheet
from app.storage.repository import StudyFolderRepository
from app.ui.canvas.grid_view import GridView
from app.ui.canvas.items import TextItem
from app.ui.canvas.page_scene import TOOL_DRAW, TOOL_NONE, TOOL_TEXT, PageScene
from app.ui.widgets.history_buttons import REDO, UNDO, HistoryButton
from app.ui.widgets.sheet_list import SheetListWidget
from app.ui.widgets.tool_settings import DrawSettings, TextSettings
from app.ui.widgets.toolbuttons import DrawButton, TextButton

# pages of the settings bar below the toolbar
SETTINGS_EMPTY, SETTINGS_TEXT, SETTINGS_DRAW = 0, 1, 2
PAN_MARGIN = 150   # the sheet can be dragged this far beyond its edges


class SheetEditor(QWidget):
    closed_signal = Signal()  # the editor was closed

    def __init__(self, folder: StudyFolder, repository: StudyFolderRepository):
        super().__init__()
        self.folder = folder
        self.repository = repository

        self.sheet: StudySheet = new_sheet()   # working copy of the sheet currently shown
        self.is_new = True                     # True = sheet is not in the folder yet
        self.dirty = False                     # True = unsaved changes
        self.history = History()               # undo / redo (in memory only)
        self.discard_on_close = False          # True = do not save anything on close (folder is being deleted)
        self.scene: PageScene | None = None

        self.setWindowTitle(f"Study sheet editor – {folder.name}")
        self._build_layout()

        """Button connections"""
        self.text_button.toggled.connect(self.text_toggled)
        self.draw_button.toggled.connect(self.draw_toggled)
        self.save_button.clicked.connect(self.save_sheet)
        self.clear_button.clicked.connect(self.clear_sheet)
        self.close_button.clicked.connect(self.close)
        self.sheet_list.card_selected_signal.connect(self.select_sheet)
        self.sheet_list.delete_card_signal.connect(self.delete_sheet)
        self.text_settings.changed_signal.connect(self.text_settings_changed)
        self.draw_settings.changed_signal.connect(self.draw_settings_changed)
        self.draw_settings.committed_signal.connect(self.record_step)
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)

        """Keyboard shortcuts"""
        QShortcut(QKeySequence.StandardKey.Undo, self, self.undo)   # Ctrl+Z
        QShortcut(QKeySequence.StandardKey.Redo, self, self.redo)   # Ctrl+Y (on Windows also Ctrl+Shift+Z)

        self.load_sheet(new_sheet(), is_new=True)
        self.refresh_list()

    # ------------------------------------------------------------------ Layout
    def _build_layout(self):
        """Layout: sheet list on the left, the sheet with tools below it in the middle,
        folder name, undo/redo and buttons on the right"""
        self.main = QHBoxLayout(self)
        self.main.setSpacing(10)
        self.main.setContentsMargins(5, 5, 5, 5)

        # ----- left
        self.left_layout = QVBoxLayout()
        self.list_label = QLabel("Sheets", self)
        label_font = QFont()
        label_font.setPointSize(20)
        self.list_label.setFont(label_font)
        self.left_layout.addWidget(self.list_label)
        self.sheet_list = SheetListWidget()
        self.left_layout.addWidget(self.sheet_list)
        self.main.addLayout(self.left_layout)

        # ----- middle: sheet, tool buttons and settings below it
        self.central_layout = QVBoxLayout()
        self.view = GridView(pan_margin=PAN_MARGIN)
        self.central_layout.addWidget(self.view)

        self.toolbar = QToolBar()
        tool_policy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.text_button = TextButton()
        self.text_button.setToolTip("Place a text field (then click on the sheet)")
        self.toolbar.addWidget(self.text_button)
        self.draw_button = DrawButton()
        self.draw_button.setToolTip("Draw")
        self.toolbar.addWidget(self.draw_button)
        self.central_layout.addWidget(self.toolbar)

        self.toolbar_stacked = QStackedWidget(self)
        self.text_settings = TextSettings()
        self.draw_settings = DrawSettings()
        self.toolbar_stacked.addWidget(QWidget())           # SETTINGS_EMPTY
        self.toolbar_stacked.addWidget(self.text_settings)  # SETTINGS_TEXT
        self.toolbar_stacked.addWidget(self.draw_settings)  # SETTINGS_DRAW
        self.central_layout.addWidget(self.toolbar_stacked)

        self.central_layout.setStretch(0, 20)
        self.central_layout.setStretch(1, 1)
        self.central_layout.setStretch(2, 1)
        self.main.addLayout(self.central_layout)

        # ----- right
        self.right_layout = QVBoxLayout()
        self.folder_name = QLabel(self.folder.name, self)
        name_font = QFont()
        name_font.setPointSize(30)
        self.folder_name.setFont(name_font)
        self.folder_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.folder_name.setWordWrap(True)
        self.right_layout.addWidget(self.folder_name)

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
        self.save_button = QPushButton("save", self)
        self.clear_button = QPushButton("clear sheet", self)
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
        self.main.setStretch(1, 3)
        self.main.setStretch(2, 1)

    # ------------------------------------------------------------------ Showing a sheet
    def load_sheet(self, sheet: StudySheet, is_new: bool):
        """Shows the sheet. 'sheet' is already a working copy."""
        self.sheet = sheet
        self.is_new = is_new
        self.dirty = False
        self.history.reset(sheet)   # the history only applies to this sheet
        self._build_scene()
        self.update_history_buttons()
        QTimer.singleShot(0, self.scroll_to_top)   # after the layout is done, show the top of the sheet

    def scroll_to_top(self):
        """Show the top of the sheet (with the title) instead of its middle"""
        self.view.centerOn(SHEET_WIDTH / 2, 0)
        bar = self.view.verticalScrollBar()
        bar.setValue(bar.value() + self.view.viewport().height() // 2 - 20)

    def _build_scene(self):
        self.scene = PageScene(self.sheet.page, self.repository.images_dir(self.folder),
                               lambda: self.repository.new_image_path(self.folder),
                               width=SHEET_WIDTH, height=SHEET_HEIGHT)
        self.scene.changed_signal.connect(self.mark_dirty)
        self.scene.step_signal.connect(self.record_step)
        self.scene.text_placed_signal.connect(self.text_placed)
        self.scene.set_text_style(self.text_settings.family(), self.text_settings.size())
        self.scene.set_pen(self.draw_settings.color(), self.draw_settings.width())
        self.scene.selectionChanged.connect(self.selection_changed)
        self.scene.focusItemChanged.connect(lambda *args: self.update_settings_page())
        self.view.setScene(self.scene)
        self.update_tool()

    @Slot()
    def mark_dirty(self):
        self.dirty = True

    # ------------------------------------------------------------------ Undo / redo
    @Slot()
    def record_step(self):
        """Remember the state of the sheet after a completed step and update its name in the list"""
        if self.history.record(self.sheet):
            self.dirty = True
        self.update_history_buttons()
        self._update_list_title()

    def _update_list_title(self):
        self.sheet_list.set_entry_title(None if self.is_new else self.sheet.id, self.sheet.title())

    def update_history_buttons(self):
        self.undo_button.setEnabled(self.history.can_undo())
        self.redo_button.setEnabled(self.history.can_redo())

    def _editing_text_item(self) -> TextItem | None:
        if self.scene is None:
            return None
        focus = self.scene.focusItem()
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

    def _restore(self, state: StudySheet):
        """Show a state from the history (the sheet keeps its ID)"""
        self.sheet = state
        self.dirty = True
        self._build_scene()
        self.update_history_buttons()
        self.update_settings_page()
        self._update_list_title()

    def confirm_discard(self) -> bool:
        """Asks for confirmation if there are unsaved changes. True = continue."""
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self, "Unsaved changes",
            "The current sheet has unsaved changes.\nDo you want to discard them?",
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
        if self.scene is not None:
            self.scene.set_tool(tool)

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
    def _selected_texts(self):
        return self.scene.selected_text_items() if self.scene is not None else []

    def _selected_strokes(self):
        return self.scene.selected_stroke_items() if self.scene is not None else []

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

    @Slot()
    def selection_changed(self):
        texts, strokes = self._selected_texts(), self._selected_strokes()
        if len(texts) == 1:
            model = texts[0].model
            self.text_settings.set_values(model.font_family, model.font_size)
            self.scene.set_text_style(self.text_settings.family(), self.text_settings.size())
        elif len(strokes) == 1 and not texts:
            model = strokes[0].model
            self.draw_settings.set_values(model.color, model.width)
            self.scene.set_pen(self.draw_settings.color(), self.draw_settings.width())
        self.update_settings_page()

    @Slot(str, int)
    def text_settings_changed(self, family: str, size: int):
        """applies to new text fields and to the selected or edited text field"""
        self.scene.set_text_style(family, size)
        for item in self._selected_texts():
            item.set_font(family, size)
        self.record_step()

    @Slot(str, float)
    def draw_settings_changed(self, color: str, width: float):
        """applies to new strokes and to selected strokes"""
        self.scene.set_pen(color, width)
        for item in self._selected_strokes():
            item.set_style(color, width)

    # ------------------------------------------------------------------ Actions
    def refresh_list(self):
        """Rebuild the list and select the current sheet"""
        self.sheet_list.load_folder(self.folder, self.sheet if self.is_new else new_sheet())
        self._restore_list_selection()

    @Slot(object)
    def select_sheet(self, sheet: StudySheet | None):
        """Sheet clicked in the list (None = the new sheet at the bottom)"""
        if sheet is None:
            self.new_sheet()
            return
        if not self.is_new and sheet.id == self.sheet.id:
            return
        if not self.leave_current_sheet():
            self._restore_list_selection()
            return
        # always take the current version from the folder (the list may hold an old object)
        current = self.folder.find_sheet(sheet.id) or sheet
        self.load_sheet(copy.deepcopy(current), is_new=False)
        # the new sheet at the bottom starts fresh again -> show its default title
        # (the list is not rebuilt here, because this runs inside the list's own selection signal)
        self.sheet_list.set_entry_title(None, DEFAULT_TITLE)

    def new_sheet(self):
        """Switch to the new, empty sheet at the bottom"""
        if self.is_new:
            self.sheet_list.select_new_entry()
            return
        if not self.leave_current_sheet():
            self._restore_list_selection()
            return
        self.load_sheet(new_sheet(), is_new=True)
        self.sheet_list.set_entry_title(None, DEFAULT_TITLE)
        self.sheet_list.select_new_entry()

    @Slot()
    def clear_sheet(self):
        """Removes everything except the title field"""
        if len(self.sheet.page.elements) <= 1:
            return
        self.sheet.clear()
        self._build_scene()
        self.record_step()   # can be undone

    @Slot()
    def save_sheet(self):
        self._finish_text_editing()
        if self.is_new and self.sheet.is_blank():
            QMessageBox.information(self, "Empty sheet", "The sheet is empty and was not saved.")
            return
        was_new = self.is_new
        # put a copy into the folder so later changes only count after saving again
        self.repository.save_sheet(self.folder, copy.deepcopy(self.sheet))
        self.dirty = False
        self.is_new = False
        # bottom sheet (the new one) saved -> a new, empty sheet appears below it right away
        if was_new:
            self.load_sheet(new_sheet(), is_new=True)
        self.refresh_list()

    @Slot(object)
    def delete_sheet(self, sheet: StudySheet):
        """Red cross in the list: delete the sheet permanently right away (no confirmation)"""
        stored = self.folder.find_sheet(sheet.id)
        if stored is None:
            return
        self.repository.delete_sheet(self.folder, stored)
        if not self.is_new and self.sheet.id == sheet.id:
            self.load_sheet(new_sheet(), is_new=True)   # afterwards the new sheet at the bottom is selected
        self.refresh_list()

    def autosave(self):
        """Save an existing sheet with changes (not the new sheet at the bottom)"""
        if self.is_new or not self.dirty:
            return
        self.repository.save_sheet(self.folder, copy.deepcopy(self.sheet))
        self.dirty = False

    def leave_current_sheet(self) -> bool:
        """Before switching/closing: save an existing sheet, ask for confirmation on the new sheet.
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
            self.sheet_list.select_new_entry()
        else:
            self.sheet_list.select_card(self.sheet.id)

    def closeEvent(self, event):
        if self.leave_current_sheet():   # saves existing sheets automatically
            self.dirty = False
            self.closed_signal.emit()
            event.accept()
        else:
            event.ignore()


"""Test window for the study sheet editor (saves into the normal data folder)"""
if __name__ == "__main__":
    app = QApplication(sys.argv)
    repo = StudyFolderRepository()
    folders = repo.load_all()
    test_folder = folders[0] if folders else repo.create_folder("Test folder")
    editor = SheetEditor(test_folder, repo)
    editor.setMinimumSize(1100, 700)
    editor.show()
    sys.exit(app.exec())
