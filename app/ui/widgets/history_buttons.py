"""Buttons for undo (↶) and redo (↷).
The arrows are drawn in code, no image file is needed.
If the button is disabled (nothing to undo), the arrow turns light gray."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget

UNDO, REDO = "undo", "redo"


class HistoryButton(QPushButton):
    def __init__(self, direction: str, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.setMinimumSize(44, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Rückgängig (Strg+Z)" if direction == UNDO else "Wiederherstellen (Strg+Y)")

    def paintEvent(self, event):
        super().paintEvent(event)   # normal button background
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(50, 50, 50) if self.isEnabled() else QColor(180, 180, 180)
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # half circle on top, arrow head at the end points down
        radius = min(self.width(), self.height()) * 0.25
        cx, cy = self.width() / 2, self.height() / 2 + radius * 0.35
        arc = QRectF(cx - radius, cy - radius, 2 * radius, 2 * radius)
        if self.direction == UNDO:
            painter.drawArc(arc, 0 * 16, 180 * 16)      # from the right over the top to the left
            tip_x = cx - radius                          # tip on the left
        else:
            painter.drawArc(arc, 180 * 16, -180 * 16)   # from the left over the top to the right
            tip_x = cx + radius                          # tip on the right

        size = radius * 0.6
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygonF([
            QPointF(tip_x, cy + size),           # tip at the bottom
            QPointF(tip_x - size, cy - size * 0.2),
            QPointF(tip_x + size, cy - size * 0.2),
        ]))
        painter.end()


"""Test window"""
if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QHBoxLayout(window)
    layout.addWidget(HistoryButton(UNDO))
    disabled = HistoryButton(REDO)
    disabled.setEnabled(False)
    layout.addWidget(HistoryButton(REDO))
    layout.addWidget(disabled)
    window.show()
    app.exec()
