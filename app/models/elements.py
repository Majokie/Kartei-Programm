"""The elements that can be placed on a card page.

Pure data model: no Qt and no file access here.
Displaying happens in app/ui/canvas, saving in app/storage.
"""
from dataclasses import dataclass, field
import uuid


def new_id() -> str:
    """Creates a unique ID for decks, cards and elements."""
    return uuid.uuid4().hex


@dataclass
class TextElement:
    """A text field on a page."""
    text: str = "Textfeld"
    x: float = 0.0
    y: float = 0.0
    font_size: int = 20
    font_family: str = ""          # empty = default font
    id: str = field(default_factory=new_id)


@dataclass
class StrokeElement:
    """A drawn stroke. The points are stored relative to (x, y),
    so moving it only requires changing x and y."""
    points: list[list[float]] = field(default_factory=list)  # [[x, y], [x, y], ...]
    color: str = "black"
    width: float = 5.0
    x: float = 0.0
    y: float = 0.0
    id: str = field(default_factory=new_id)


@dataclass
class ImageElement:
    """An image. Only the file name inside the image folder of the deck is stored."""
    filename: str = ""
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0             # scale factor (1.0 = original size), aspect ratio is kept
    id: str = field(default_factory=new_id)


Element = TextElement | StrokeElement | ImageElement
