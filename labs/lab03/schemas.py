"""Pydantic-моделі запитів і відповідей."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RecordStatus = Literal["new", "in_progress", "done"]


class CategoryCreate(BaseModel):
    """Тіло запиту на створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=40, description="Назва категорії")


class CategoryRead(CategoryCreate):
    """Категорія у відповіді API."""

    id: int = Field(gt=0, description="Ідентифікатор категорії")


class RecordCreate(BaseModel):
    """Тіло запиту на створення запису (id задає база даних)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(min_length=3, max_length=40, description="Унікальний код")
    title: str = Field(min_length=3, max_length=120, description="Назва вимірювання")
    category_id: int = Field(gt=0, description="Ідентифікатор категорії")
    value: float = Field(
        ge=0,
        allow_inf_nan=False,
        strict=True,
        description="Тривалість опрацювання, хвилини (число, не рядок і не bool)",
    )
    status: RecordStatus = Field(description="Стан перевірки вимірювання")


class RecordReplace(RecordCreate):
    """Тіло PUT: усі змінювані поля обов'язкові."""


class RecordRead(RecordCreate):
    """Запис у відповіді API."""

    id: int = Field(gt=0, description="Ідентифікатор запису")
    category_name: str = Field(description="Назва категорії")


class PingResponse(BaseModel):
    """Відповідь перевірки доступності."""

    status: Literal["ok"]


class StudentInfo(BaseModel):
    """Дані студента з shared/student.py."""

    student_name: str
    group_name: str
    variant_number: int


class ErrorResponse(BaseModel):
    """Повідомлення про помилку для документації OpenAPI."""

    detail: str
