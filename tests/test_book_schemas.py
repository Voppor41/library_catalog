import pytest
from pydantic import ValidationError

from library_catalog.api.v1.schemas.book import BookCreate, BookUpdate


def make_book_payload(**overrides):
    payload = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "year": 2008,
        "genre": "Programming",
        "pages": 464,
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    ("source", "normalized"),
    [
        ("978-0-13-235088-4", "9780132350884"),
        ("0-8044-2957-X", "080442957X"),
    ],
)
def test_create_normalizes_valid_isbn(source: str, normalized: str) -> None:
    book = BookCreate(**make_book_payload(isbn=source))

    assert book.isbn == normalized


@pytest.mark.parametrize("isbn", ["9780132350885", "0804429571", "12345678X0"])
def test_create_rejects_invalid_isbn(isbn: str) -> None:
    with pytest.raises(ValidationError):
        BookCreate(**make_book_payload(isbn=isbn))


def test_create_strips_text_and_rejects_blank_title() -> None:
    book = BookCreate(**make_book_payload(title="  Clean Code  "))
    assert book.title == "Clean Code"

    with pytest.raises(ValidationError):
        BookCreate(**make_book_payload(title="   "))


@pytest.mark.parametrize(
    "field_name",
    ["title", "author", "year", "genre", "pages", "available"],
)
def test_update_rejects_explicit_null_for_non_nullable_fields(
    field_name: str,
) -> None:
    with pytest.raises(ValidationError):
        BookUpdate(**{field_name: None})


def test_update_distinguishes_missing_fields_from_nullable_fields() -> None:
    update = BookUpdate(description=None, isbn=None)

    assert update.model_dump(exclude_unset=True) == {
        "description": None,
        "isbn": None,
    }
