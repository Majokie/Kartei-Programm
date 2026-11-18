"""Converts the data model into plain dicts (for JSON) and back.

This is the only place that knows the JSON format. Every element gets a
"type" field so the right class can be created when loading.
"""
from dataclasses import asdict

from app.models.deck import Deck
from app.models.elements import ImageElement, StrokeElement, TextElement
from app.models.flashcard import Card, Page
from app.models.learnblock import CardProgress, LearnBlock
from app.models.study import StudyFolder, StudySheet

FORMAT_VERSION = 1

ELEMENT_TYPES = {
    "text": TextElement,
    "stroke": StrokeElement,
    "image": ImageElement,
}
ELEMENT_NAMES = {cls: name for name, cls in ELEMENT_TYPES.items()}


# ---------- Elements ----------
def element_to_dict(element) -> dict:
    return {"type": ELEMENT_NAMES[type(element)], **asdict(element)}


def element_from_dict(data: dict):
    data = dict(data)
    element_type = data.pop("type")
    cls = ELEMENT_TYPES[element_type]
    return cls(**data)


# ---------- Pages and cards ----------
def page_to_list(page: Page) -> list[dict]:
    return [element_to_dict(element) for element in page.elements]


def page_from_list(data: list[dict]) -> Page:
    return Page([element_from_dict(element) for element in data])


def card_to_dict(card: Card) -> dict:
    return {
        "version": FORMAT_VERSION,
        "id": card.id,
        "front": page_to_list(card.front),
        "back": page_to_list(card.back),
    }


def card_from_dict(data: dict) -> Card:
    return Card(
        id=data["id"],
        front=page_from_list(data.get("front", [])),
        back=page_from_list(data.get("back", [])),
    )


# ---------- Deck (header data only, cards live in their own files) ----------
def deck_to_dict(deck: Deck) -> dict:
    return {
        "version": FORMAT_VERSION,
        "id": deck.id,
        "name": deck.name,
        "card_order": [card.id for card in deck.cards],
    }


def deck_from_dict(data: dict) -> tuple[Deck, list[str]]:
    """Returns the deck (without cards yet) and the saved card order."""
    deck = Deck(name=data["name"], id=data["id"])
    return deck, list(data.get("card_order", []))


# ---------- Learn blocks ----------
def learnblock_to_dict(block: LearnBlock) -> dict:
    return {
        "version": FORMAT_VERSION,
        "id": block.id,
        "name": block.name,
        "deck_id": block.deck_id,
        "method": block.method,
        "progress": {card_id: asdict(progress) for card_id, progress in block.progress.items()},
    }


def learnblock_from_dict(data: dict) -> LearnBlock:
    return LearnBlock(
        id=data["id"],
        name=data["name"],
        deck_id=data["deck_id"],
        method=data.get("method", "leitner"),
        progress={card_id: CardProgress(**progress)
                  for card_id, progress in data.get("progress", {}).items()},
    )


# ---------- Study folders and sheets ----------
def sheet_to_dict(sheet: StudySheet) -> dict:
    return {
        "version": FORMAT_VERSION,
        "id": sheet.id,
        "page": page_to_list(sheet.page),
    }


def sheet_from_dict(data: dict) -> StudySheet:
    return StudySheet(id=data["id"], page=page_from_list(data.get("page", [])))


def folder_to_dict(folder: StudyFolder) -> dict:
    return {
        "version": FORMAT_VERSION,
        "id": folder.id,
        "name": folder.name,
        "sheet_order": [sheet.id for sheet in folder.sheets],
    }


def folder_from_dict(data: dict) -> tuple[StudyFolder, list[str]]:
    """Returns the folder (without sheets yet) and the saved sheet order."""
    folder = StudyFolder(name=data["name"], id=data["id"])
    return folder, list(data.get("sheet_order", []))
