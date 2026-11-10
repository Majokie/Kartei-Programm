"""Card and card page as a pure data model (no Qt)."""
from dataclasses import dataclass, field

from app.models.elements import Element, new_id


@dataclass
class Page:
    """One side of a card (front or back)."""
    elements: list[Element] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.elements) == 0


@dataclass
class Card:
    """A flashcard with a front and a back.
    Learning progress is stored separately in learn blocks (see learnblock.py)."""
    front: Page = field(default_factory=Page)
    back: Page = field(default_factory=Page)
    id: str = field(default_factory=new_id)
