"""The study folder overview. Built like the deck overview (at most 20 folders)."""
import sys

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

from app.models.study import StudyFolder
from app.storage.repository import StudyFolderRepository
from app.ui.widgets.confirm_dialog import ConfirmDialog
from app.ui.widgets.deck_grid import DeckGrid
from app.ui.widgets.folder import FolderContainer


class FolderOverview(QWidget):
    edit_folder_signal = Signal(object)      # folder (model) should be opened in the study sheet editor
    folder_deleting_signal = Signal(object)  # folder is about to be deleted (e.g. close an open editor)

    def __init__(self, repository: StudyFolderRepository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.setMinimumSize(600, 450)

        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)

        """Title"""
        self.label = QLabel("Study Folders", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Comic Sans MS", 20))
        self.verticalLayout.addWidget(self.label)

        self.folder_grid = DeckGrid(self)   # same grid as the deck overview (4 x 5)
        self.verticalLayout.addWidget(self.folder_grid)

        """Buttons at the bottom of the window"""
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.back_button = QPushButton("back", self)
        self.back_button.setFont(QFont("Comic Sans MS", 15))
        self.horizontalLayout.addWidget(self.back_button)
        self.horizontalLayout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.new_folder_button = QPushButton("new folder", self)
        self.new_folder_button.setFont(QFont("Comic Sans MS", 15))
        self.horizontalLayout.addWidget(self.new_folder_button)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 4)
        self.horizontalLayout.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.new_folder_button.clicked.connect(self.new_folder)
        self.load_folders()

    def all_folders(self) -> list[StudyFolder]:
        return [container.folder for container in self.folder_grid.decks]

    def load_folders(self):
        for folder in self.repository.load_all():
            self.add_folder_widget(folder)

    def add_folder_widget(self, folder: StudyFolder):
        container = FolderContainer(folder)
        container.edit_signal.connect(self.edit_folder_signal.emit)
        container.renamed_signal.connect(self.repository.save_folder)   # renaming is saved immediately
        container.delete_signal.connect(self.delete_folder)
        self.folder_grid.add_deck(container)

    @Slot()
    def new_folder(self):
        if self.folder_grid.is_full():
            QMessageBox.information(self, "New folder", "You can create at most 20 study folders.")
            return
        name = FolderNameDialog.ask(self)
        if name:
            self.add_folder_widget(self.repository.create_folder(name))

    @Slot(object)
    def delete_folder(self, folder: StudyFolder):
        """Asks for confirmation and then deletes the folder with all its sheets"""
        confirmed = ConfirmDialog.ask(
            self, "Delete study folder",
            f"Do you really want to delete the folder \"{folder.name}\" with {len(folder.sheets)} sheet(s)?\n"
            "This cannot be undone.",
            confirm_text="Delete", cancel_text="Cancel")
        if not confirmed:
            return
        self.folder_deleting_signal.emit(folder)   # first, so that an open editor does not save anything anymore
        self.repository.delete_folder(folder)
        for container in list(self.folder_grid.decks):
            if container.folder is folder:
                self.folder_grid.remove_deck(container)


DIALOG_STYLE = """
QDialog { background-color: #ffffff; }
QLabel { background-color: transparent; color: #222222; }
QLineEdit { background-color: #ffffff; color: #222222; border: 1px solid #bbbbbb;
            border-radius: 4px; padding: 4px; }
QPushButton { background-color: #eeeeee; color: #222222; border: 1px solid #bbbbbb;
              border-radius: 4px; padding: 6px 18px; }
QPushButton:hover { background-color: #e0e0e0; }
"""


class FolderNameDialog(QDialog):
    """Window for entering the name of a new study folder"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New study folder")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 15)
        layout.setSpacing(15)
        row = QHBoxLayout()
        row.addWidget(QLabel("Name:"))
        self.input = QLineEdit()
        self.input.setPlaceholderText("e.g. Thermodynamics")
        row.addWidget(self.input)
        layout.addLayout(row)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Create")
        self.ok_button.setDefault(True)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.ok_button)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept)

    @staticmethod
    def ask(parent) -> str | None:
        """Shows the dialog and returns the entered name (or None)."""
        dialog = FolderNameDialog(parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.input.text().strip() or None
        return None


"""Test window for the folder overview"""
if __name__ == "__main__":
    app = QApplication([])
    window = QMainWindow()
    window.setCentralWidget(FolderOverview(StudyFolderRepository()))
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())
