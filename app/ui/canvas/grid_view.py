"""View for a card page with limited mouse-wheel zoom."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView


class GridView(QGraphicsView):
    def __init__(self):
        super().__init__()
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
