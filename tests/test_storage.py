"""Tests for the data model and storage. Run with:  python -m pytest tests"""
from app.models.elements import ImageElement, StrokeElement, TextElement
from app.models.flashcard import Card, Page
from app.storage import serializer
from app.storage.repository import DeckRepository


def make_card() -> Card:
    return Card(
        front=Page([TextElement(text="Was ist Entropie?", x=10, y=20, font_size=24)]),
        back=Page([
            StrokeElement(points=[[0, 0], [5, 5], [10, 3]], width=3, x=100, y=50),
            ImageElement(filename="bild.png", x=1.5, y=2.5),
        ]),
    )


def test_card_roundtrip():
    card = make_card()
    assert serializer.card_from_dict(serializer.card_to_dict(card)) == card


def test_save_and_load_deck(tmp_path):
    repo = DeckRepository(tmp_path)
    deck = repo.create_deck("Thermodynamik")
    first, second = make_card(), Card()
    repo.save_card(deck, first)
    repo.save_card(deck, second)

    loaded = DeckRepository(tmp_path).load_all()
    assert len(loaded) == 1
    assert loaded[0].name == "Thermodynamik"
    assert [c.id for c in loaded[0].cards] == [first.id, second.id]
    assert loaded[0].cards[0] == first


def test_saving_twice_does_not_duplicate(tmp_path):
    repo = DeckRepository(tmp_path)
    deck = repo.create_deck("A")
    card = make_card()
    repo.save_card(deck, card)
    card.front.elements[0].text = "geändert"
    repo.save_card(deck, card)

    loaded = DeckRepository(tmp_path).load_all()[0]
    assert len(loaded.cards) == 1
    assert len(loaded.cards[0].front.elements) == 1
    assert loaded.cards[0].front.elements[0].text == "geändert"


def test_rename_keeps_cards(tmp_path):
    repo = DeckRepository(tmp_path)
    deck = repo.create_deck("Alt")
    repo.save_card(deck, make_card())
    deck.name = "Neu"
    repo.save_deck(deck)
    repo.save_card(deck, Card())   # this used to crash after renaming

    loaded = DeckRepository(tmp_path).load_all()[0]
    assert loaded.name == "Neu"
    assert len(loaded.cards) == 2


def test_delete_card(tmp_path):
    repo = DeckRepository(tmp_path)
    deck = repo.create_deck("A")
    card = make_card()
    repo.save_card(deck, card)
    repo.delete_card(deck, card)
    assert DeckRepository(tmp_path).load_all()[0].cards == []


def test_delete_deck(tmp_path):
    repo = DeckRepository(tmp_path)
    keep = repo.create_deck("Behalten")
    gone = repo.create_deck("Weg")
    repo.save_card(gone, make_card())
    repo.delete_deck(gone)
    assert [d.name for d in DeckRepository(tmp_path).load_all()] == ["Behalten"]


def test_new_fields_and_old_files():
    card = Card(front=Page([TextElement(font_family="Arial", font_size=30),
                            ImageElement(filename="a.png", scale=0.5)]))
    assert serializer.card_from_dict(serializer.card_to_dict(card)) == card
    # older cards without font_family/scale can still be loaded
    old = {"id": "x", "front": [{"type": "text", "text": "Hi", "x": 0, "y": 0, "font_size": 20, "id": "t"},
                                {"type": "image", "filename": "b.png", "x": 0, "y": 0, "id": "i"}], "back": []}
    loaded = serializer.card_from_dict(old)
    assert loaded.front.elements[0].font_family == ""
    assert loaded.front.elements[1].scale == 1.0
