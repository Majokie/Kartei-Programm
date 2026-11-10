"""Learn block as a pure data model (no Qt).

A learn block belongs to exactly one deck and stores how well each card is
known. The cards themselves stay unchanged, so a deck can also be learned in
several learn blocks, each with its own progress.
"""
from dataclasses import dataclass, field
from datetime import datetime

from app.models.elements import new_id

METHOD_LEITNER = "leitner"
METHOD_SPACED_REPETITION = "spaced_repetition"   # comes after 1.0


@dataclass
class CardProgress:
    """Learning progress of a card within a learn block."""
    level: int = 0                 # how often the card was rated "known"
    due: str | None = None         # when the card is due again (ISO format), None = never learned
    last_rating: str | None = None # last rating (see app/logic/leitner.py)

    def due_datetime(self) -> datetime | None:
        return datetime.fromisoformat(self.due) if self.due else None


@dataclass
class LearnBlock:
    name: str
    deck_id: str
    method: str = METHOD_LEITNER
    progress: dict[str, CardProgress] = field(default_factory=dict)  # card ID -> learning progress
    id: str = field(default_factory=new_id)

    def progress_for(self, card_id: str) -> CardProgress:
        """Returns the learning progress of a card, creating it if needed."""
        if card_id not in self.progress:
            self.progress[card_id] = CardProgress()
        return self.progress[card_id]
