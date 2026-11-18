"""Study folders and study sheets as a pure data model (no Qt).

A study folder works like a deck, but contains study sheets instead of cards.
A study sheet is a single page in DIN A4 portrait format. Every sheet has a
title field at the top left; its text is the name of the sheet in the list.
The title field cannot be moved or deleted.
"""
from dataclasses import dataclass, field

from app.models.elements import TextElement, new_id
from app.models.flashcard import Page

DEFAULT_TITLE = "Study Sheet"
SHEET_WIDTH = 900
SHEET_HEIGHT = 1273          # DIN A4 portrait (ratio 1 : 1.414)
TITLE_X, TITLE_Y = 40.0, 30.0
TITLE_FONT_SIZE = 28


@dataclass
class StudySheet:
    page: Page = field(default_factory=Page)
    id: str = field(default_factory=new_id)

    def title_element(self) -> TextElement | None:
        for element in self.page.elements:
            if isinstance(element, TextElement) and element.is_title:
                return element
        return None

    def title(self) -> str:
        """Name of the sheet: first line of the title field, or DEFAULT_TITLE if it is empty."""
        element = self.title_element()
        if element is None or not element.text.strip():
            return DEFAULT_TITLE
        return element.text.strip().splitlines()[0]

    def is_blank(self) -> bool:
        """True if nothing has been added and the title was not changed."""
        others = [element for element in self.page.elements
                  if not (isinstance(element, TextElement) and element.is_title)]
        return not others and self.title() == DEFAULT_TITLE

    def clear(self) -> None:
        """Removes everything except the title field."""
        self.page.elements = [element for element in self.page.elements
                              if isinstance(element, TextElement) and element.is_title]


def new_sheet() -> StudySheet:
    """A new, empty sheet with the default title field."""
    title = TextElement(text=DEFAULT_TITLE, x=TITLE_X, y=TITLE_Y,
                        font_size=TITLE_FONT_SIZE, is_title=True)
    return StudySheet(page=Page([title]))


@dataclass
class StudyFolder:
    """A folder with a name and an ordered list of sheets (order of creation)."""
    name: str
    sheets: list[StudySheet] = field(default_factory=list)
    id: str = field(default_factory=new_id)

    def find_sheet(self, sheet_id: str) -> StudySheet | None:
        for sheet in self.sheets:
            if sheet.id == sheet_id:
                return sheet
        return None

    def put_sheet(self, sheet: StudySheet) -> None:
        """Replaces the sheet with the same ID or appends it at the end."""
        for index, existing in enumerate(self.sheets):
            if existing.id == sheet.id:
                self.sheets[index] = sheet
                return
        self.sheets.append(sheet)

    def remove_sheet(self, sheet_id: str) -> None:
        self.sheets = [sheet for sheet in self.sheets if sheet.id != sheet_id]
