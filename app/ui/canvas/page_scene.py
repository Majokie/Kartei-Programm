"""The drawing surface for a card page.

The scene displays a Page object from the data model. Everything the user
adds or deletes is changed in the model first and then displayed.
"""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QGraphicsScene

from app.models.elements import ImageElement, StrokeElement, TextElement
from app.models.flashcard import Page
from app.ui.canvas.items import ImageItem, StrokeItem, TextItem, make_item

# Tools
TOOL_NONE = None
TOOL_TEXT = "text"
TOOL_DRAW = "draw"


class PageScene(QGraphicsScene):
    changed_signal = Signal()      # something on the page has changed
    text_placed_signal = Signal()  # a text field was placed (the editor then unchecks the button)
    step_signal = Signal()         # a step is complete (the editor records the state for undo)

    def __init__(self, page: Page, image_dir: Path, new_image_path=None,
                 width: int = 900, height: int = 600, read_only: bool = False, parent=None):
        """
        page:            the page from the data model
        image_dir:       folder that contains the images of the deck
        new_image_path:  function that returns (file name, path) for a new image.
                         If it is None, no images can be pasted.
        read_only:       True = display only (e.g. while learning), nothing can be changed
        """
        super().__init__(parent)
        self.page = page
        self.image_dir = image_dir
        self.new_image_path = new_image_path
        self.tool = TOOL_NONE
        self.read_only = read_only
        self.grid_size = 30
        # settings for new elements (set by the editor via set_text_style / set_pen)
        self.text_family = ""
        self.text_size = 20
        self.pen_color = "black"
        self.pen_width = 5.0
        self.current_stroke: StrokeItem | None = None

        self.setSceneRect(0, 0, width, height)
        for element in page.elements:   # model -> display
            self.addItem(make_item(element, image_dir))

    # ---------- Tools ----------
    def set_tool(self, tool):
        self.tool = tool

    def mark_changed(self):
        self.changed_signal.emit()

    def mark_step(self):
        """Step complete. The history ignores 'steps' without a real change."""
        if not self.read_only:
            self.step_signal.emit()

    def set_text_style(self, family: str, size: int):
        """Font for new text fields"""
        self.text_family, self.text_size = family, size

    def set_pen(self, color: str, width: float):
        """Color and width for new strokes"""
        self.pen_color, self.pen_width = color, width

    def selected_text_items(self) -> list[TextItem]:
        """selected text fields and the text field currently being edited"""
        items = [item for item in self.selectedItems() if isinstance(item, TextItem)]
        focus = self.focusItem()
        if isinstance(focus, TextItem) and focus not in items:
            items.append(focus)
        return items

    def selected_stroke_items(self) -> list[StrokeItem]:
        return [item for item in self.selectedItems() if isinstance(item, StrokeItem)]

    # ---------- Background ----------
    def drawBackground(self, painter: QPainter, rect):
        """Draws the card with a grid pattern"""
        painter.fillRect(self.sceneRect(), QColor(255, 204, 203))
        painter.setPen(QPen(QColor(30, 100, 100), 0.2))
        r = self.sceneRect()
        left, top, right, bottom = int(r.left()), int(r.top()), int(r.right()), int(r.bottom())
        for x in range(left, right, self.grid_size):
            painter.drawLine(x, top, x, bottom)
        for y in range(top, bottom, self.grid_size):
            painter.drawLine(left, y, right, y)

    # ---------- Adding ----------
    def add_text(self, x: float, y: float) -> TextItem:
        element = TextElement(x=x, y=y, font_size=self.text_size, font_family=self.text_family)
        self.page.elements.append(element)   # model first
        item = TextItem(element)             # then display
        self.addItem(item)
        self.clearSelection()
        item.setSelected(True)               # selected -> text settings stay visible
        item.start_editing(select_all=True)  # "Textfeld" is selected -> just start typing
        self.mark_changed()
        self.mark_step()                     # inserting is one step
        return item

    def paste_image(self):
        if self.new_image_path is None:
            return
        image = QApplication.clipboard().image()
        if image.isNull():
            return
        filename, path = self.new_image_path()
        if not image.save(str(path), "PNG"):
            return
        element = ImageElement(filename=filename,
                               x=self.width() / 2 - image.width() / 2,
                               y=self.height() / 2 - image.height() / 2)
        self.page.elements.append(element)
        self.addItem(ImageItem(element, self.image_dir))
        self.mark_changed()
        self.mark_step()

    def delete_selected(self):
        for item in self.selectedItems():
            model = getattr(item, "model", None)
            if model in self.page.elements:
                self.page.elements.remove(model)   # from the model
            self.removeItem(item)                  # and from the scene
        self.mark_changed()
        self.mark_step()

    # ---------- Mouse ----------
    def mousePressEvent(self, event):
        if self.read_only:   # while learning: nothing can be selected, moved or edited
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self.tool == TOOL_TEXT:
            pos = event.scenePos()
            self.add_text(pos.x(), pos.y())
            self.text_placed_signal.emit()
        elif event.button() == Qt.MouseButton.LeftButton and self.tool == TOOL_DRAW:
            pos = event.scenePos()
            element = StrokeElement(points=[[0.0, 0.0]], x=pos.x(), y=pos.y(),
                                    color=self.pen_color, width=self.pen_width)
            self.page.elements.append(element)
            self.current_stroke = StrokeItem(element)
            self.addItem(self.current_stroke)
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.read_only:
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self.read_only:
            event.accept()
            return
        if self.current_stroke is not None:
            pos = event.scenePos()
            self.current_stroke.add_point(pos.x() - self.current_stroke.x(),
                                          pos.y() - self.current_stroke.y())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.current_stroke is not None:
            stroke = self.current_stroke
            self.current_stroke = None
            if len(stroke.model.points) < 2:   # only clicked, not dragged -> keep nothing
                self.page.elements.remove(stroke.model)
                self.removeItem(stroke)
            else:
                self.mark_changed()
        else:
            super().mouseReleaseEvent(event)
        # releasing finishes drawing, moving and image scaling -> step
        self.mark_step()

    # ---------- Keyboard ----------
    def keyPressEvent(self, event):
        if self.read_only:
            event.accept()
            return
        # While typing in a text field, the text field gets the keys
        # (otherwise Del would delete the whole field and Ctrl+V would paste an image).
        focus = self.focusItem()
        if isinstance(focus, TextItem) and focus.is_editing():
            super().keyPressEvent(event)
            return

        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_V:
            self.paste_image()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(event)
