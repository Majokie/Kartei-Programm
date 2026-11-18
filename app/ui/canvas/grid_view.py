"""View for a card page or study sheet.

- mouse wheel: zoom (with limits)
- hold the right mouse button: move (pan) the view in any direction
"""
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView


class GridView(QGraphicsView):
    def __init__(self, pan_margin: float = 0):
        """pan_margin: extra space around the page, so it can also be dragged
        a bit beyond its edges (used for study sheets)."""
        super().__init__()
        self.pan_margin = pan_margin
        self._pan_last: QPointF | None = None   # last mouse position while panning
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.scale_factor = 1.15
        self.min_scale = 0.5
        self.max_scale = 2
        self.current_scale = 1

    def wheelEvent(self, event):
        """Mouse-wheel zoom with limits"""
        if event.angleDelta().y() > 0 and self.current_scale < self.max_scale:
            self.scale(self.scale_factor, self.scale_factor)
            self.current_scale *= self.scale_factor
        elif event.angleDelta().y() < 0 and self.current_scale > self.min_scale:
            self.scale(1 / self.scale_factor, 1 / self.scale_factor)
            self.current_scale /= self.scale_factor
        else:
            super().wheelEvent(event)

    def setScene(self, scene):
        super().setScene(scene)
        if scene is not None and self.pan_margin:
            m = self.pan_margin
            self.setSceneRect(scene.sceneRect().adjusted(-m, -m, m, m))

    # ---------- Panning with the right mouse button ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._pan_last = event.position()
            self.viewport().setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_last is not None:
            delta = event.position() - self._pan_last
            self._pan_last = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - round(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - round(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self._pan_last is not None:
            self._pan_last = None
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)
