"""Qt representation of the elements on a page.

Every item holds a reference to its model object (self.model) and writes
each change made by the user straight into it. So there is no second copy
of the data that would have to be kept in sync by hand.
"""
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen, QPixmap, QTextCursor
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsPixmapItem, QGraphicsTextItem

from app.models.elements import ImageElement, StrokeElement, TextElement

MOVABLE_FLAGS = (
    QGraphicsItem.GraphicsItemFlag.ItemIsMovable
    | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
    | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges  # needed so that itemChange reports the position
)


def _notify_step(item: QGraphicsItem) -> None:
    """Tells the scene that a step is complete (for undo)."""
    scene = item.scene()
    if scene is not None and hasattr(scene, "mark_step"):
        scene.mark_step()


def _notify_changed(item: QGraphicsItem) -> None:
    """Tells the scene that something has changed (for 'unsaved changes')."""
    scene = item.scene()
    if scene is not None and hasattr(scene, "mark_changed"):
        scene.mark_changed()


class _PositionSync:
    """Shared logic: write the position into the model when moved."""
    model = None

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.model.x = self.x()
            self.model.y = self.y()
            _notify_changed(self)
        return super().itemChange(change, value)


class TextItem(_PositionSync, QGraphicsTextItem):
    """Text field with two states:
    - normal:   a click selects the field; it can be moved and deleted with Del
    - editing:  via double click (or right after placing it); keys go into the text.
                Finish with Escape or by clicking elsewhere.
    """
    def __init__(self, model: TextElement):
        super().__init__()
        self.model = model
        self.setPlainText(model.text)
        self._apply_font()
        self.setPos(model.x, model.y)
        self.setFlags(MOVABLE_FLAGS)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)  # starts in the normal state
        # connect only after filling in, otherwise loading would count as a change
        self.document().contentsChanged.connect(self._text_changed)

    def _text_changed(self):
        self.model.text = self.toPlainText()
        _notify_changed(self)

    def _apply_font(self):
        font = QFont(self.model.font_family) if self.model.font_family else QFont()
        font.setPointSize(int(self.model.font_size))
        self.setFont(font)

    def set_font(self, family: str, size: int):
        """Change font family and size for the whole text field"""
        if family == self.model.font_family and size == self.model.font_size:
            return
        self.model.font_family = family
        self.model.font_size = size
        self._apply_font()
        _notify_changed(self)

    def is_editing(self) -> bool:
        """True while the user is typing in this text field."""
        return (self.textInteractionFlags() != Qt.TextInteractionFlag.NoTextInteraction
                and self.hasFocus())

    def start_editing(self, select_all: bool = False):
        """Switches to editing mode."""
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        if select_all:
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            self.setTextCursor(cursor)

    def stop_editing(self):
        """Back to the normal state (text selection is cleared)."""
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        _notify_step(self)   # one whole text edit = one step

    def mouseDoubleClickEvent(self, event):
        if not self.is_editing():
            self.start_editing()
        super().mouseDoubleClickEvent(event)   # places the cursor where the user clicked

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.stop_editing()

    def keyPressEvent(self, event):
        # Escape ends typing, the field stays selected -> Del then deletes the whole field
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
            self.setSelected(True)
        else:
            super().keyPressEvent(event)


class StrokeItem(_PositionSync, QGraphicsPathItem):
    def __init__(self, model: StrokeElement):
        super().__init__()
        self.model = model
        self._apply_pen()
        self.setPos(model.x, model.y)
        self.setFlags(MOVABLE_FLAGS)
        self.rebuild_path()

    def _apply_pen(self):
        pen = QPen(QColor(self.model.color))
        pen.setWidthF(self.model.width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

    def set_style(self, color: str, width: float):
        """Change color and width of an existing stroke"""
        if color == self.model.color and width == self.model.width:
            return
        self.model.color = color
        self.model.width = width
        self._apply_pen()
        _notify_changed(self)

    def rebuild_path(self):
        path = QPainterPath()
        if self.model.points:
            first_x, first_y = self.model.points[0]
            path.moveTo(first_x, first_y)
            for px, py in self.model.points[1:]:
                path.lineTo(px, py)
        self.setPath(path)

    def add_point(self, x: float, y: float):
        """Called while drawing. x and y are relative to the item."""
        self.model.points.append([x, y])
        self.rebuild_path()


HANDLE_SIZE = 12     # size of the corner handles in pixels (on the card, independent of the image size)
MIN_IMAGE_SIZE = 20  # an image cannot be made smaller than 20 pixels (shorter side)


class ImageItem(_PositionSync, QGraphicsPixmapItem):
    """Image that can be resized by dragging its four corners.
    Width and height always change in the same ratio."""
    def __init__(self, model: ImageElement, image_dir: Path):
        super().__init__()
        self.model = model
        self.setPixmap(QPixmap(str(image_dir / model.filename)))
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)
        self.setScale(model.scale)
        self.setPos(model.x, model.y)
        self.setFlags(MOVABLE_FLAGS)
        self.setAcceptHoverEvents(True)
        self._drag_corner: int | None = None   # which corner is being dragged
        self._anchor = QPointF()               # opposite corner (stays fixed), in scene coordinates

    # ---------- Corners
    def _handle_size(self) -> float:
        """Handle size in image coordinates (converted because of setScale so the handles keep their size)"""
        return HANDLE_SIZE / max(self.scale(), 0.01)

    def _corners(self) -> list[QPointF]:
        """Corners in image coordinates: top left, top right, bottom right, bottom left"""
        r = QRectF(self.pixmap().rect())
        return [r.topLeft(), r.topRight(), r.bottomRight(), r.bottomLeft()]

    def _corner_at(self, pos: QPointF) -> int | None:
        if not self.isSelected():
            return None
        half = self._handle_size()
        for index, corner in enumerate(self._corners()):
            if abs(pos.x() - corner.x()) <= half and abs(pos.y() - corner.y()) <= half:
                return index
        return None

    def boundingRect(self) -> QRectF:
        half = self._handle_size() / 2
        return QRectF(self.pixmap().rect()).adjusted(-half, -half, half, half)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.boundingRect())   # so the handles are clickable too
        return path

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            size = self._handle_size()
            painter.setPen(QPen(QColor(40, 40, 40), 1 / max(self.scale(), 0.01)))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            for corner in self._corners():
                painter.drawRect(QRectF(corner.x() - size / 2, corner.y() - size / 2, size, size))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.prepareGeometryChange()   # show/hide the handles
        return super().itemChange(change, value)

    # ---------- Mouse
    def hoverMoveEvent(self, event):
        corner = self._corner_at(event.pos())
        if corner in (0, 2):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif corner in (1, 3):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.unsetCursor()
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        corner = self._corner_at(event.pos())
        if corner is not None and event.button() == Qt.MouseButton.LeftButton:
            self._drag_corner = corner
            self._anchor = self.mapToScene(self._corners()[(corner + 2) % 4])
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_corner is None:
            super().mouseMoveEvent(event)
            return
        width, height = self.pixmap().width(), self.pixmap().height()
        if width == 0 or height == 0:
            return
        mouse = event.scenePos()
        # larger of the two factors -> the image follows the mouse but is never distorted
        new_scale = max(abs(mouse.x() - self._anchor.x()) / width,
                        abs(mouse.y() - self._anchor.y()) / height)
        new_scale = max(new_scale, MIN_IMAGE_SIZE / min(width, height))
        w, h = width * new_scale, height * new_scale

        # the opposite corner stays where it is
        ax, ay = self._anchor.x(), self._anchor.y()
        left = {0: ax - w, 1: ax, 2: ax, 3: ax - w}[self._drag_corner]
        top = {0: ay - h, 1: ay - h, 2: ay, 3: ay}[self._drag_corner]

        self.prepareGeometryChange()
        self.setScale(new_scale)
        self.model.scale = new_scale
        self.setPos(left, top)   # writes x/y into the model via itemChange
        event.accept()

    def mouseReleaseEvent(self, event):
        if self._drag_corner is not None:
            self._drag_corner = None
            _notify_changed(self)
            event.accept()
            return
        super().mouseReleaseEvent(event)


def make_item(element, image_dir: Path) -> QGraphicsItem:
    """Creates the matching Qt item for a model element."""
    if isinstance(element, TextElement):
        return TextItem(element)
    if isinstance(element, StrokeElement):
        return StrokeItem(element)
    if isinstance(element, ImageElement):
        return ImageItem(element, image_dir)
    raise TypeError(f"Unbekanntes Element: {element!r}")
