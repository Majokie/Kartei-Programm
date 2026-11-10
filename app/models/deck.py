"""Deck as a pure data model (no Qt)."""
from dataclasses import dataclass, field

from app.models.elements import new_id
from app.models.flashcard import Card


@dataclass
class Deck:
    """A deck with a name and an ordered list of cards.
    The folder on disk is named after the ID, so the name can change."""
    name: str
    cards: list[Card] = field(default_factory=list)
    id: str = field(default_factory=new_id)

    def find_card(self, card_id: str) -> Card | None:
        for card in self.cards:
            if card.id == card_id:
                return card
        return None

    def put_card(self, card: Card) -> None:
        """Replaces the card with the same ID or appends it at the end."""
        for index, existing in enumerate(self.cards):
            if existing.id == card.id:
                self.cards[index] = card
                return
        self.cards.append(card)

    def remove_card(self, card_id: str) -> None:
        self.cards = [card for card in self.cards if card.id != card_id]
