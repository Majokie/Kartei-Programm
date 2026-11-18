"""List of study sheets in the study sheet editor.

Works exactly like the card list (it is derived from it), but the entries show
the title of each sheet instead of "Karte 1, Karte 2, ...". The signals keep
their names from the card list: card_selected_signal sends a StudySheet (or None
for the new sheet at the bottom), delete_card_signal sends the StudySheet to delete.
"""
from PySide6.QtGui import QColor

from app.models.study import StudyFolder, StudySheet
from app.ui.widgets.CardListWidget import CardListWidget
from app.ui.widgets.MListWidgetCard import MListWidgetCard
from app.ui.widgets.deck import DeleteButton


class SheetListWidget(CardListWidget):
    def load_folder(self, folder: StudyFolder, new_sheet: StudySheet | None):
        """Rebuilds the list in the order of creation. At the very bottom (in italics)
        is the new sheet that has not been saved yet."""
        self.list_view.blockSignals(True)
        self.delete_item = None          # clear() also deletes the cross
        self.list_view.clear()
        for sheet in folder.sheets:
            item = MListWidgetCard(sheet)
            item.setText(sheet.title())
            self.list_view.addItem(item)
        if new_sheet is not None:
            item = MListWidgetCard(None)            # None = new sheet, not saved yet
            item.setText(new_sheet.title())
            font = item.font()
            font.setItalic(True)
            item.setFont(font)
            item.setForeground(QColor(120, 120, 120))
            self.list_view.addItem(item)
        self.list_view.blockSignals(False)
        self.update_delete_button()

    def set_entry_title(self, sheet_id: str | None, title: str):
        """Updates the shown name of a sheet (None = the new sheet at the bottom)."""
        for row in range(self.list_view.count()):
            item = self.list_view.item(row)
            if (item.card is None and sheet_id is None) or (item.card is not None and item.card.id == sheet_id):
                item.setText(title)
                return

    def update_delete_button(self):
        super().update_delete_button()
        if self.delete_item is not None:   # English tooltip for the cross
            row = self.list_view.itemWidget(self.delete_item)
            button = row.findChild(DeleteButton) if row is not None else None
            if button is not None:
                button.setToolTip("Delete sheet")
