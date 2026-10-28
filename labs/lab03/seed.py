"""Початкове заповнення бази з data/seed.json.

Запуск з кореня репозиторію: python -m labs.lab03.seed
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from labs.lab03 import config, repository
from labs.lab03.database import initialize_database
from labs.lab03.schemas import CategoryCreate, RecordCreate

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"

logger = logging.getLogger(__name__)


class SeedCategory(CategoryCreate):
    """Категорія з id, заданим у JSON."""

    id: int = Field(gt=0)


class SeedData(BaseModel):
    """Структура seed.json."""

    model_config = ConfigDict(extra="forbid")

    categories: list[SeedCategory]
    records: list[RecordCreate]


def load_seed(path: Path) -> SeedData:
    """Прочитати та перевірити початкові дані; ValueError — якщо вони некоректні."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        data = SeedData.model_validate(raw)
    except OSError as exc:
        raise ValueError(f"не вдалося прочитати файл {path.name}") from exc
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in exc.errors()
        )
        raise ValueError(details) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"некоректний JSON: {exc.msg} (рядок {exc.lineno})") from exc

    if len(data.categories) != config.SEED_CATEGORIES_COUNT:
        raise ValueError(f"очікується категорій: {config.SEED_CATEGORIES_COUNT}")
    if len(data.records) != config.SEED_RECORDS_COUNT:
        raise ValueError(f"очікується записів: {config.SEED_RECORDS_COUNT}")
    return data


def seed_database(path: Path = SEED_PATH) -> int:
    """Заповнити порожню базу. Повертає код завершення (0 — успіх)."""
    initialize_database()

    if not repository.is_database_empty():
        print("База вже містить дані: заповнення пропущено, дані не змінено.")
        return 0

    try:
        data = load_seed(path)
    except ValueError as exc:
        print(f"Початкові дані некоректні, нічого не додано: {exc}")
        return 1

    try:
        repository.seed_initial_data(
            [item.model_dump() for item in data.categories],
            [item.model_dump() for item in data.records],
        )
    except sqlite3.Error as exc:
        logger.error("Помилка початкового заповнення: %s", exc)
        print("Заповнення скасовано: порушено обмеження бази, зміни відкочено.")
        return 1

    print(f"Додано категорій: {len(data.categories)}, записів: {len(data.records)}.")
    return 0


if __name__ == "__main__":
    sys.exit(seed_database())
