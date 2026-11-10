"""Settings bars below the toolbar in the card editor.

TextSettings:  font family (QFontComboBox) and font size (QSpinBox, the number can also be typed)
DrawSettings:  pen width (slider with the number next to it) and color (picker with color circle and name)

The bars know nothing about cards or scenes. They only report via a signal
that a setting has changed. What happens then is up to the editor.
"""
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QFontComboBox, QHBoxLayout, QLabel, QSlider, QSpinBox,
                               QVBoxLayout, QWidget)

# pen colors: (name, color value). Simply add more colors here.
PEN_COLORS = [
    ("Schwarz", "black"),
    ("Grün", "#2e9d3a"),
    ("Rot", "#d62828"),
]

MIN_FONT_SIZE, MAX_FONT_SIZE, DEFAULT_FONT_SIZE = 6, 200, 20
MIN_PEN_WIDTH, MAX_PEN_WIDTH, DEFAULT_PEN_WIDTH = 1, 30, 5


class TextSettings(QWidget):
    changed_signal = Signal(str, int)   # (font family, font size)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)

        self.font_box = QFontComboBox()
        self.font_box.setToolTip("Schriftart")
        self.size_box = QSpinBox()
        self.size_box.setRange(MIN_FONT_SIZE, MAX_FONT_SIZE)
        self.size_box.setValue(DEFAULT_FONT_SIZE)
        self.size_box.setToolTip("Schriftgröße (auch direkt eintippen)")
        self.size_box.setKeyboardTracking(False)   # when typing, apply only after Enter / leaving the field

        layout.addWidget(self.font_box)
        layout.addWidget(self.size_box)
        layout.addStretch()

        self.font_box.currentFontChanged.connect(self._emit)
        self.size_box.valueChanged.connect(self._emit)

    def family(self) -> str:
        return self.font_box.currentFont().family()

    def size(self) -> int:
        return self.size_box.value()

    def set_values(self, family: str, size: int):
        """Show values without emitting changed_signal (e.g. when a text field is selected)"""
        self.font_box.blockSignals(True)
        self.size_box.blockSignals(True)
        self.font_box.setCurrentFont(QFont(family) if family else QFont())
        self.size_box.setValue(size)
        self.font_box.blockSignals(False)
        self.size_box.blockSignals(False)

    def _emit(self, *args):
        self.changed_signal.emit(self.family(), self.size())


def color_icon(color: str, size: int = 16) -> QIcon:
    """Small filled color circle for the color picker"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(80, 80, 80))
    painter.setBrush(QColor(color))
    painter.drawEllipse(1, 1, size - 2, size - 2)
    painter.end()
    return QIcon(pixmap)


class DrawSettings(QWidget):
    changed_signal = Signal(str, float)   # (color, width) - also while the slider is being dragged
    committed_signal = Signal()           # change complete (slider released / color chosen)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)

        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(MIN_PEN_WIDTH, MAX_PEN_WIDTH)
        self.width_slider.setValue(DEFAULT_PEN_WIDTH)
        self.width_slider.setMinimumWidth(150)
        self.width_slider.setToolTip("Stiftdicke")
        self.width_label = QLabel(str(DEFAULT_PEN_WIDTH))
        self.width_label.setMinimumWidth(25)

        self.color_box = QComboBox()
        self.color_box.setIconSize(QSize(16, 16))
        self.color_box.setToolTip("Farbe")
        for name, value in PEN_COLORS:
            self.color_box.addItem(color_icon(value), name, value)

        layout.addWidget(self.width_slider)
        layout.addWidget(self.width_label)
        layout.addSpacing(20)
        layout.addWidget(self.color_box)
        layout.addStretch()

        self.width_slider.valueChanged.connect(self._width_changed)
        self.width_slider.sliderReleased.connect(self.committed_signal.emit)
        self.color_box.currentIndexChanged.connect(self._color_changed)

    def color(self) -> str:
        return self.color_box.currentData()

    def width(self) -> float:
        return float(self.width_slider.value())

    def set_values(self, color: str, width: float):
        """Show values without emitting changed_signal (e.g. when a stroke is selected)"""
        self.width_slider.blockSignals(True)
        self.color_box.blockSignals(True)
        self.width_slider.setValue(int(round(width)))
        self.width_label.setText(str(int(round(width))))
        index = self.color_box.findData(color)
        if index >= 0:
            self.color_box.setCurrentIndex(index)
        self.width_slider.blockSignals(False)
        self.color_box.blockSignals(False)

    def _width_changed(self, value: int):
        self.width_label.setText(str(value))
        self._emit()
        if not self.width_slider.isSliderDown():   # e.g. via arrow key or a click next to the handle
            self.committed_signal.emit()

    def _color_changed(self, *args):
        self._emit()
        self.committed_signal.emit()

    def _emit(self, *args):
        self.changed_signal.emit(self.color(), self.width())


"""Test window with both bars"""
if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout(window)
    text_settings, draw_settings = TextSettings(), DrawSettings()
    text_settings.changed_signal.connect(lambda f, s: print("Text:", f, s))
    draw_settings.changed_signal.connect(lambda c, w: print("Stift:", c, w))
    layout.addWidget(text_settings)
    layout.addWidget(draw_settings)
    window.show()
    app.exec()
