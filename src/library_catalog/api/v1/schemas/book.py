from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


def _normalize_isbn(value: str | None) -> str | None:
    if value is None:
        return None

    isbn = value.replace("-", "").replace(" ", "").upper()
    if len(isbn) == 10:
        if not isbn[:9].isdigit() or not (isbn[9].isdigit() or isbn[9] == "X"):
            raise ValueError("ISBN-10 must contain 9 digits and a digit or X checksum")

        digits = [int(character) for character in isbn[:9]]
        checksum = 10 if isbn[9] == "X" else int(isbn[9])
        weighted_sum = sum(
            digit * weight
            for digit, weight in zip(digits, range(10, 1, -1), strict=True)
        ) + checksum
        if weighted_sum % 11 != 0:
            raise ValueError("Invalid ISBN-10 checksum")
    elif len(isbn) == 13:
        if not isbn.isdigit():
            raise ValueError("ISBN-13 must contain only digits")

        weighted_sum = sum(
            int(character) * (1 if index % 2 == 0 else 3)
            for index, character in enumerate(isbn)
        )
        if weighted_sum % 10 != 0:
            raise ValueError("Invalid ISBN-13 checksum")
    else:
        raise ValueError("ISBN must contain 10 or 13 characters")

    return isbn


def _strip_text(value: str | None) -> str | None:
    return value.strip() if isinstance(value, str) else value


class BookBase(BaseModel):

    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=300)
    year: int = Field(..., ge=1000, le=2100)
    genre: str = Field(..., min_length=1, max_length=100)
    pages: int = Field(..., gt=0)

    @field_validator("title", "author", "genre", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        return _strip_text(value)


class BookCreate(BookBase):

    isbn: str | None = Field(None, min_length=10, max_length=20)
    description: str | None = Field(None, max_length=5000)

    @field_validator("isbn", mode="before")
    @classmethod
    def validate_isbn(cls, value: str | None) -> str | None:
        return _normalize_isbn(value)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "isbn": "978-0132350884",
                    "description": "A Handbook of Agile Software Craftsmanship"
                }
            ]
        }
    }

class BookUpdate(BaseModel):

    title: str | None = Field(None, min_length=1, max_length=500)
    author: str | None = Field(None, min_length=1, max_length=300)
    year: int | None = Field(None, ge=1000, le=2100)
    genre: str | None = Field(None, min_length=1, max_length=100)
    pages: int | None = Field(None, gt=0)
    available: bool | None = None
    isbn: str | None = Field(None, min_length=10, max_length=20)
    description: str | None = Field(None, max_length=5000)

    @field_validator("title", "author", "genre", mode="before")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return _strip_text(value)

    @field_validator("isbn", mode="before")
    @classmethod
    def validate_isbn(cls, value: str | None) -> str | None:
        return _normalize_isbn(value)

    @model_validator(mode="after")
    def reject_null_for_required_database_fields(self) -> "BookUpdate":
        non_nullable_fields = {
            "title",
            "author",
            "year",
            "genre",
            "pages",
            "available",
        }
        null_fields = {
            field_name
            for field_name in non_nullable_fields & self.model_fields_set
            if getattr(self, field_name) is None
        }
        if null_fields:
            fields = ", ".join(sorted(null_fields))
            raise ValueError(f"Fields cannot be null: {fields}")
        return self


class ShowBook(BookBase):
    book_id: UUID
    available: bool
    isbn: str | None
    description: str | None
    extra: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,  # Для ORM моделей
        "json_schema_extra": {
            "examples": [
                {
                    "book_id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "available": True,
                    "isbn": "978-0132350884",
                    "description": "A Handbook of Agile Software Craftsmanship",
                    "extra": {
                        "cover_url": "https://covers.openlibrary.org/b/id/123-L.jpg",
                        "subjects": ["Computer Science", "Software Engineering"]
                    },
                    "created_at": "2024-01-01T12:00:00",
                    "updated_at": "2024-01-01T12:00:00"
                }
            ]
        }
    }

class BookFilters(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    author: str | None = Field(None, min_length=1, max_length=300)
    genre: str | None = Field(None, min_length=1, max_length=100)
    year: int | None = Field(None, ge=1000, le=2100)
    available: bool | None = Field(None, description="Фильтр по доступности")

    @field_validator("title", "author", "genre", mode="before")
    @classmethod
    def strip_filter_text(cls, value: str | None) -> str | None:
        return _strip_text(value)
