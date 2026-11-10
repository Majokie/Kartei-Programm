"""Loading and saving decks and cards. The only place that touches files.

Layout on disk (inside DATA_DIR, see paths.py):
    decks/<deck-id>/deck.json          name and order of the cards
    decks/<deck-id>/cards/<card-id>.json
    decks/<deck-id>/images/<image>.png
    learnblocks/<block-id>.json
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.models.deck import Deck
from app.models.elements import new_id
from app.models.flashcard import Card
from app.models.learnblock import LearnBlock
from app.storage import serializer
from app.storage.paths import DECKS_DIR, LEARNBLOCKS_DIR


class DeckRepository:
    def __init__(self, base_dir: Path = DECKS_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ---------- Folders ----------
    def deck_dir(self, deck: Deck) -> Path:
        return self.base_dir / deck.id

    def cards_dir(self, deck: Deck) -> Path:
        return self.deck_dir(deck) / "cards"

    def images_dir(self, deck: Deck) -> Path:
        return self.deck_dir(deck) / "images"

    # ---------- Decks ----------
    def create_deck(self, name: str) -> Deck:
        deck = Deck(name=name)
        self.save_deck(deck)
        return deck

    def save_deck(self, deck: Deck) -> None:
        """Saves only the header data (name, order). Also used for renaming."""
        self.cards_dir(deck).mkdir(parents=True, exist_ok=True)
        self.images_dir(deck).mkdir(parents=True, exist_ok=True)
        self._write_json(self.deck_dir(deck) / "deck.json", serializer.deck_to_dict(deck))

    def delete_deck(self, deck: Deck) -> None:
        """Permanently deletes the deck with all cards and images from disk."""
        folder = self.deck_dir(deck)
        if folder.exists():
            shutil.rmtree(folder)

    def load_all(self) -> list[Deck]:
        decks = []
        for folder in sorted(self.base_dir.iterdir()):
            deck_file = folder / "deck.json"
            if folder.is_dir() and deck_file.exists():
                decks.append(self._load_deck(deck_file))
        return decks

    def _load_deck(self, deck_file: Path) -> Deck:
        deck, card_order = serializer.deck_from_dict(self._read_json(deck_file))
        cards = {}
        for card_file in self.cards_dir(deck).glob("*.json"):
            card = serializer.card_from_dict(self._read_json(card_file))
            cards[card.id] = card
        # saved order first, then any remaining cards
        for card_id in card_order:
            if card_id in cards:
                deck.cards.append(cards.pop(card_id))
        deck.cards.extend(cards.values())
        return deck

    # ---------- Cards ----------
    def save_card(self, deck: Deck, card: Card) -> None:
        """Puts the card into the deck (new or replaced) and writes it to disk."""
        deck.put_card(card)
        self.cards_dir(deck).mkdir(parents=True, exist_ok=True)
        self._write_json(self.cards_dir(deck) / f"{card.id}.json", serializer.card_to_dict(card))
        self.save_deck(deck)

    def delete_card(self, deck: Deck, card: Card) -> None:
        deck.remove_card(card.id)
        card_file = self.cards_dir(deck) / f"{card.id}.json"
        if card_file.exists():
            card_file.unlink()
        self.save_deck(deck)

    # ---------- Images ----------
    def new_image_path(self, deck: Deck) -> tuple[str, Path]:
        """Returns a free file name and the full path for a new image.
        The actual saving is done by the UI (which knows Qt)."""
        self.images_dir(deck).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{new_id()[:8]}.png"
        return filename, self.images_dir(deck) / filename

    # ---------- Helpers ----------
    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        """Writes to a temporary file first and then replaces the old one.
        If the program crashes while writing, the old file stays intact."""
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)

    @staticmethod
    def _read_json(path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)


class LearnBlockRepository:
    """Loading and saving learn blocks: learnblocks/<block-id>.json"""
    def __init__(self, base_dir: Path = LEARNBLOCKS_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _file(self, block: LearnBlock) -> Path:
        return self.base_dir / f"{block.id}.json"

    def create(self, name: str, deck_id: str, method: str) -> LearnBlock:
        block = LearnBlock(name=name, deck_id=deck_id, method=method)
        self.save(block)
        return block

    def save(self, block: LearnBlock) -> None:
        DeckRepository._write_json(self._file(block), serializer.learnblock_to_dict(block))

    def delete(self, block: LearnBlock) -> None:
        if self._file(block).exists():
            self._file(block).unlink()

    def delete_for_deck(self, deck_id: str) -> None:
        """Deletes all learn blocks of a deck (when the deck is deleted)."""
        for block in self.load_all():
            if block.deck_id == deck_id:
                self.delete(block)

    def load_all(self) -> list[LearnBlock]:
        blocks = []
        for block_file in sorted(self.base_dir.glob("*.json")):
            blocks.append(serializer.learnblock_from_dict(DeckRepository._read_json(block_file)))
        return blocks
