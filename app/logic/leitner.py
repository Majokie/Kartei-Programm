"""Leitner system: the rules for when a card comes up again.

Only rules live here - no data and no Qt. The data is stored in the
LearnBlock (app/models/learnblock.py).

Rules:
- unknown:          the card comes back in 2 minutes
- partially known:  the card comes back after 10 minutes at the earliest
- known:            the card comes back in 1, 2, 3 ... days (each "known" adds a day),
                    at most every MAX_INTERVAL_DAYS days (about twice a week)
- The level does not drop on "unknown" or "partially known".
- If no card is due right now, "unknown" cards are shown early anyway.
  "partially known" cards really wait the full 10 minutes.
"""
from datetime import datetime, time, timedelta

from app.models.deck import Deck
from app.models.flashcard import Card
from app.models.learnblock import CardProgress, LearnBlock

UNKNOWN = "unknown"   # not known
PARTIAL = "partial"   # partially known
KNOWN = "known"       # known for sure

UNKNOWN_DELAY = timedelta(minutes=2)
PARTIAL_DELAY = timedelta(minutes=10)
MAX_INTERVAL_DAYS = 3   # 3 days apart ~ twice a week


def start_of_day(day: datetime, plus_days: int = 0) -> datetime:
    """Midnight of the day (plus a number of days)."""
    return datetime.combine(day.date() + timedelta(days=plus_days), time.min)


def rate(progress: CardProgress, rating: str, now: datetime) -> None:
    """Record the rating of a card and calculate its next due date."""
    if rating == UNKNOWN:
        due = now + UNKNOWN_DELAY
    elif rating == PARTIAL:
        due = now + PARTIAL_DELAY
    elif rating == KNOWN:
        progress.level += 1
        days = min(progress.level, MAX_INTERVAL_DAYS)
        due = start_of_day(now, days)   # "tomorrow" = from midnight tomorrow
    else:
        raise ValueError(f"Unbekannte Bewertung: {rating}")
    progress.due = due.isoformat(timespec="seconds")
    progress.last_rating = rating


def next_card(block: LearnBlock, deck: Deck, now: datetime) -> Card | None:
    """Which card is learned next. None = no card is due right now.

    Order: due cards first (the one overdue the longest first), then new cards
    in deck order. If there are none of those, "unknown" cards come up early.
    """
    due_cards, new_cards, early_cards = [], [], []
    for index, card in enumerate(deck.cards):
        progress = block.progress.get(card.id)
        due = progress.due_datetime() if progress else None
        if due is None:
            new_cards.append(card)
        elif due <= now:
            due_cards.append((due, index, card))
        elif progress.last_rating == UNKNOWN:
            early_cards.append((due, index, card))

    if due_cards:
        return min(due_cards, key=lambda entry: (entry[0], entry[1]))[2]
    if new_cards:
        return new_cards[0]
    if early_cards:
        return min(early_cards, key=lambda entry: (entry[0], entry[1]))[2]
    return None


def next_due_time(block: LearnBlock, deck: Deck) -> datetime | None:
    """When the next card is due again (e.g. for 'next card at 18:05').
    None = there are still new cards or the deck is empty."""
    times = []
    for card in deck.cards:
        progress = block.progress.get(card.id)
        if progress is None or progress.due is None:
            return None
        times.append(progress.due_datetime())
    return min(times) if times else None


def is_finished_today(block: LearnBlock, deck: Deck | None, now: datetime) -> bool:
    """True (green) if no card is due anymore today, otherwise False (red)."""
    if deck is None:
        return True
    tomorrow = start_of_day(now, 1)
    for card in deck.cards:
        progress = block.progress.get(card.id)
        due = progress.due_datetime() if progress else None
        if due is None or due < tomorrow:
            return False
    return True


def summary(block: LearnBlock, deck: Deck, now: datetime) -> dict[str, int]:
    """Numbers for display: new, due now, later today (waiting), done."""
    result = {"new": 0, "due": 0, "waiting": 0, "done": 0}
    tomorrow = start_of_day(now, 1)
    for card in deck.cards:
        progress = block.progress.get(card.id)
        due = progress.due_datetime() if progress else None
        if due is None:
            result["new"] += 1
        elif due <= now:
            result["due"] += 1
        elif due < tomorrow:
            result["waiting"] += 1
        else:
            result["done"] += 1
    return result
