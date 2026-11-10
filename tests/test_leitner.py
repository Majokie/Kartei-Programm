"""Tests for the Leitner rules and saving learn blocks."""
from datetime import datetime, timedelta

from app.logic import leitner
from app.logic.leitner import KNOWN, PARTIAL, UNKNOWN
from app.models.deck import Deck
from app.models.flashcard import Card
from app.models.learnblock import CardProgress, LearnBlock
from app.storage.repository import LearnBlockRepository

NOW = datetime(2026, 11, 6, 18, 0, 0)


def make(n=3):
    deck = Deck("Thermo", cards=[Card() for _ in range(n)])
    block = LearnBlock("Klausur", deck.id)
    return deck, block


def test_unknown_and_partial_delays():
    p = CardProgress()
    leitner.rate(p, UNKNOWN, NOW)
    assert p.due_datetime() == NOW + timedelta(minutes=2)
    leitner.rate(p, PARTIAL, NOW)
    assert p.due_datetime() == NOW + timedelta(minutes=10)
    assert p.level == 0


def test_known_adds_a_day_up_to_max():
    p = CardProgress()
    days = []
    for _ in range(6):
        leitner.rate(p, KNOWN, NOW)
        days.append((p.due_datetime().date() - NOW.date()).days)
    assert days == [1, 2, 3, 3, 3, 3]
    assert p.due_datetime().time() == datetime.min.time()   # from midnight


def test_no_fallback_on_unknown():
    p = CardProgress()
    leitner.rate(p, KNOWN, NOW)
    leitner.rate(p, KNOWN, NOW)
    leitner.rate(p, UNKNOWN, NOW)
    leitner.rate(p, KNOWN, NOW)
    assert p.level == 3


def test_order_due_then_new():
    deck, block = make(3)
    a, b, c = deck.cards
    leitner.rate(block.progress_for(b.id), UNKNOWN, NOW - timedelta(minutes=5))  # due for 3 minutes
    assert leitner.next_card(block, deck, NOW) is b
    leitner.rate(block.progress_for(b.id), KNOWN, NOW)
    assert leitner.next_card(block, deck, NOW) is a   # then new cards in order


def test_unknown_cards_come_early_but_partial_waits():
    deck, block = make(2)
    a, b = deck.cards
    leitner.rate(block.progress_for(a.id), PARTIAL, NOW)
    leitner.rate(block.progress_for(b.id), UNKNOWN, NOW)
    assert leitner.next_card(block, deck, NOW) is b      # unknown comes up early
    leitner.rate(block.progress_for(b.id), PARTIAL, NOW)
    assert leitner.next_card(block, deck, NOW) is None   # both wait 10 minutes
    assert leitner.next_card(block, deck, NOW + timedelta(minutes=10)) is a


def test_finished_today():
    deck, block = make(2)
    assert not leitner.is_finished_today(block, deck, NOW)       # new cards -> red
    for card in deck.cards:
        leitner.rate(block.progress_for(card.id), PARTIAL, NOW)
    assert not leitner.is_finished_today(block, deck, NOW)       # still due today -> red
    for card in deck.cards:
        leitner.rate(block.progress_for(card.id), KNOWN, NOW)
    assert leitner.is_finished_today(block, deck, NOW)           # not due until tomorrow -> green
    assert leitner.is_finished_today(block, Deck("leer"), NOW)


def test_deleted_cards_are_ignored():
    deck, block = make(1)
    block.progress_for("gibt-es-nicht-mehr")
    leitner.rate(block.progress_for(deck.cards[0].id), KNOWN, NOW)
    assert leitner.is_finished_today(block, deck, NOW)
    assert leitner.next_card(block, deck, NOW) is None


def test_learnblock_storage(tmp_path):
    repo = LearnBlockRepository(tmp_path)
    deck, _ = make(1)
    block = repo.create("Klausur", deck.id, "leitner")
    leitner.rate(block.progress_for(deck.cards[0].id), KNOWN, NOW)
    repo.save(block)
    loaded = LearnBlockRepository(tmp_path).load_all()
    assert loaded == [block]
    repo.delete_for_deck(deck.id)
    assert LearnBlockRepository(tmp_path).load_all() == []
