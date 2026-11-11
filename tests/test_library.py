"""Библиотека: у каждого диагноза есть книги, и страницы с книгами открываются без ошибок."""
from pathlib import Path

import pandas as pd
import pytest

import core
import library

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("author", "title_ru", "title_original", "why_ru", "why_kk")


def test_library_covers_every_cause():
    assert set(library.BOOKS) == set(core.CAUSES)
    for cause in core.CAUSES:
        assert len(library.books_for(cause)) >= 1, cause


def test_books_have_all_fields():
    for cause, books in library.BOOKS.items():
        for b in books:
            for f in FIELDS:
                assert isinstance(b[f], str) and b[f].strip(), (cause, f)


def test_nodata_has_no_books():
    assert library.books_for("nodata") == []


def test_roles_use_known_causes():
    assert set(library.ROLES) == {"Методист", "Завуч", "Учитель"}
    for causes in library.ROLES.values():
        assert causes and set(causes) <= set(library.BOOKS)


def test_english_edition_is_marked():
    wiliam = [b for b in library.BOOKS["schools"] if b["author"] == "Дилан Уильям"][0]
    assert wiliam["english"]
    assert "на английском" in library.title_line(wiliam)


@pytest.fixture(scope="module")
def demo():
    data = ROOT / "data"
    return pd.read_csv(data / "results.csv"), pd.read_csv(data / "items.csv"), pd.read_csv(data / "plan.csv")


def test_demo_diagnoses_have_books(demo):
    a = core.analyze(*demo, target=0.60)
    causes = {d["cause"] for d in a["diagnoses"]}
    assert causes == set(core.CAUSES)   # в демо-данные заложены все четыре причины
    for cause in causes:
        assert library.books_for(cause)


def _app(page, data=None):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.session_state["page"] = page
    if data is not None:
        at.session_state["data"] = data
        at.session_state["synthetic"] = True
    return at.run()


def test_library_page_opens_without_data():
    at = _app("Библиотека")
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    for books in library.BOOKS.values():
        for b in books:
            assert b["title_ru"] in text


def test_topic_page_shows_books(demo):
    at = _app("Тема", demo)
    assert not at.exception
    assert any(e.label == "Что почитать" for e in at.expander)
