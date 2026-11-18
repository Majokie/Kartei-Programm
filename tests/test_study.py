"""Tests for study folders and study sheets."""
from app.models.elements import StrokeElement, TextElement
from app.models.study import DEFAULT_TITLE, new_sheet
from app.storage import serializer
from app.storage.repository import StudyFolderRepository


def test_new_sheet_has_title():
    sheet = new_sheet()
    assert sheet.title() == DEFAULT_TITLE
    assert sheet.title_element().is_title
    assert sheet.is_blank()


def test_title_uses_first_line_and_falls_back():
    sheet = new_sheet()
    sheet.title_element().text = "Thermodynamics\nsecond line"
    assert sheet.title() == "Thermodynamics"
    assert not sheet.is_blank()
    sheet.title_element().text = "   "
    assert sheet.title() == DEFAULT_TITLE


def test_clear_keeps_title():
    sheet = new_sheet()
    sheet.title_element().text = "Formulas"
    sheet.page.elements.append(TextElement(text="F = m * a"))
    sheet.page.elements.append(StrokeElement(points=[[0, 0], [1, 1]]))
    sheet.clear()
    assert len(sheet.page.elements) == 1
    assert sheet.title() == "Formulas"


def test_sheet_roundtrip():
    sheet = new_sheet()
    sheet.page.elements.append(TextElement(text="content", x=50, y=200))
    assert serializer.sheet_from_dict(serializer.sheet_to_dict(sheet)) == sheet


def test_folder_save_load_order_and_delete(tmp_path):
    repo = StudyFolderRepository(tmp_path)
    folder = repo.create_folder("Physics")
    first, second, third = new_sheet(), new_sheet(), new_sheet()
    for sheet in (first, second, third):
        repo.save_sheet(folder, sheet)
    second.title_element().text = "changed"
    repo.save_sheet(folder, second)   # saving again must not change the order

    loaded = StudyFolderRepository(tmp_path).load_all()[0]
    assert loaded.name == "Physics"
    assert [s.id for s in loaded.sheets] == [first.id, second.id, third.id]
    assert loaded.sheets[1].title() == "changed"

    repo.delete_sheet(folder, first)
    assert [s.id for s in StudyFolderRepository(tmp_path).load_all()[0].sheets] == [second.id, third.id]

    repo.delete_folder(folder)
    assert StudyFolderRepository(tmp_path).load_all() == []


def test_old_text_elements_load_without_is_title():
    old = {"id": "x", "front": [{"type": "text", "text": "Hi", "x": 0, "y": 0, "font_size": 20, "id": "t"}], "back": []}
    card = serializer.card_from_dict(old)
    assert card.front.elements[0].is_title is False
