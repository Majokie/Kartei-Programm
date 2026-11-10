from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGridLayout, QWidget, QPushButton
from PySide6.QtGui import QMouseEvent, QDrag, QPainter, QPixmap
from PySide6.QtCore import Qt, QPoint, QMimeData


"""Defines the grid in which the individual decks (or learn blocks) are displayed"""
class DeckGrid(QWidget):
    def __init__(self, parent=None, rows: int = 4, columns: int = 5):
        super().__init__(parent)
        self.setAcceptDrops(True) # decks can later be moved around
        self.decks = [] # list of the added decks for later use
        self.columns = columns # number of columns
        self.rows = rows # number of rows (rows * columns = maximum number)
        self.grid = QGridLayout(self) # basic PySide layout that already is a grid
        self.grid.setVerticalSpacing(20) # vertical spacing between the rows

        """set the geometry of the cells by iterating over the rows and columns"""
        for i in range(self.rows):
            self.grid.setRowMinimumHeight(i, 50)
            self.grid.setRowStretch(i, 1)

        for j in range(self.columns):
            self.grid.setColumnMinimumWidth(j, 50)
            self.grid.setColumnStretch(j, 1)

    """Makes sure a deck is always added in the right order: rows are filled before columns,
    i.e. from top left to bottom right. Returns False if the grid is full"""
    def add_deck(self, deck) -> bool:
        for row in range(self.rows):
            for cell in range(self.columns):
                if self.grid.itemAtPosition(row, cell) is None:
                    self.grid.addWidget(deck, row, cell)
                    self.decks.append(deck)
                    return True
        return False

    def is_full(self) -> bool:
        return len(self.decks) >= self.rows * self.columns

    """Removes a deck from the grid. The gap is filled by the next new deck"""
    def remove_deck(self, deck):
        if deck in self.decks:
            self.decks.remove(deck)
        self.grid.removeWidget(deck)
        deck.deleteLater()




if __name__ == "__main__":
    app = QApplication([])


    window = DeckGrid()



    window.setWindowTitle("Deck Grid Widget")
    window.resize(400, 300)

    window.show()

    app.exec()
