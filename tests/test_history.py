"""Tests for undo / redo"""
from app.logic.history import History
from app.models.elements import TextElement
from app.models.flashcard import Card


def test_undo_redo_roundtrip():
    card = Card()
    history = History()
    history.reset(card)
    card.front.elements.append(TextElement(text="A"))
    history.record(card)
    card.front.elements[0].text = "B"
    history.record(card)

    undone = history.undo()
    assert undone.front.elements[0].text == "A"
    undone = history.undo()
    assert undone.front.elements == []
    assert history.undo() is None
    redone = history.redo()
    assert redone.front.elements[0].text == "A"


def test_no_step_without_change():
    card = Card()
    history = History()
    history.reset(card)
    assert history.record(card) is False
    assert not history.can_undo()


def test_limit_of_ten_steps():
    card = Card()
    history = History(limit=10)
    history.reset(card)
    for i in range(15):
        card.front.elements.append(TextElement(text=str(i)))
        history.record(card)
    steps = 0
    while history.undo() is not None:
        steps += 1
    assert steps == 10


def test_new_change_clears_redo():
    card = Card()
    history = History()
    history.reset(card)
    card.front.elements.append(TextElement(text="A"))
    history.record(card)
    state = history.undo()
    state.front.elements.append(TextElement(text="C"))
    history.record(state)
    assert not history.can_redo()


def test_returned_states_are_copies():
    card = Card()
    history = History()
    history.reset(card)
    card.front.elements.append(TextElement(text="A"))
    history.record(card)
    card.front.elements[0].text = "geändert ohne Schritt"
    undone = history.undo()
    redone = history.redo()
    assert redone.front.elements[0].text == "A"
