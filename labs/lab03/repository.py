"""Параметризовані SQL-запити до таблиць categories та records.

Модуль не залежить від FastAPI: помилки подаються прикладними винятками
з labs.lab03.errors, а перетворення на HTTP-коди виконує шар API.
"""

import sqlite3
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection
from labs.lab03.errors import ConflictError, NotFoundError

RECORD_SELECT = """
SELECT r.id, r.code, r.title, r.category_id,
       c.name AS category_name, r.value, r.status
FROM records AS r
JOIN categories AS c ON c.id = r.category_id
"""

INSERT_RECORD = (
    "INSERT INTO records (code, title, category_id, value, status) "
    "VALUES (?, ?, ?, ?, ?)"
)
UPDATE_RECORD = (
    "UPDATE records SET code = ?, title = ?, category_id = ?, value = ?, "
    "status = ? WHERE id = ?"
)


def _connect() -> sqlite3.Connection:
    """З'єднання, що повертає рядки як словникоподібні об'єкти."""
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    return connection


def _raise_if_unique(exc: sqlite3.IntegrityError, message: str) -> None:
    """Перетворити порушення UNIQUE на прикладний виняток."""
    if "UNIQUE constraint failed" in str(exc):
        raise ConflictError(message) from exc


def _record_params(data: dict[str, Any]) -> tuple[Any, ...]:
    """Значення змінюваних полів запису у порядку SQL-запиту."""
    return (
        data["code"],
        data["title"],
        data["category_id"],
        data["value"],
        data["status"],
    )


def _require_category(connection: sqlite3.Connection, category_id: int) -> None:
    """Переконатися, що категорія існує."""
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError("Категорію не знайдено")


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> dict[str, Any]:
    """Прочитати запис разом із category_name (JOIN)."""
    row = connection.execute(RECORD_SELECT + " WHERE r.id = ?", (record_id,)).fetchone()
    if row is None:
        raise NotFoundError("Запис не знайдено")
    return dict(row)


# ----------------------------- категорії -----------------------------


def create_category(name: str) -> dict[str, Any]:
    """Створити категорію."""
    try:
        with closing(_connect()) as connection, connection:
            cursor = connection.execute(
                "INSERT INTO categories (name) VALUES (?)", (name,)
            )
            return {"id": cursor.lastrowid, "name": name}
    except sqlite3.IntegrityError as exc:
        _raise_if_unique(exc, "Категорія з такою назвою вже існує")
        raise


def list_categories() -> list[dict[str, Any]]:
    """Список категорій за зростанням id."""
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію."""
    try:
        with closing(_connect()) as connection, connection:
            _require_category(connection, category_id)
            used = connection.execute(
                "SELECT 1 FROM records WHERE category_id = ? LIMIT 1",
                (category_id,),
            ).fetchone()
            if used is not None:
                raise ConflictError("Категорія містить записи, видалення неможливе")
            cursor = connection.execute(
                "DELETE FROM categories WHERE id = ?", (category_id,)
            )
            if cursor.rowcount == 0:
                raise NotFoundError("Категорію не знайдено")
    except sqlite3.IntegrityError as exc:
        if "FOREIGN KEY constraint failed" in str(exc):
            raise ConflictError(
                "Категорія містить записи, видалення неможливе"
            ) from exc
        raise


# ------------------------------- записи -------------------------------


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Додати запис і повернути його разом із category_name."""
    try:
        with closing(_connect()) as connection, connection:
            _require_category(connection, data["category_id"])
            cursor = connection.execute(INSERT_RECORD, _record_params(data))
            return _fetch_record(connection, int(cursor.lastrowid or 0))
    except sqlite3.IntegrityError as exc:
        _raise_if_unique(exc, "Запис із таким code вже існує")
        raise


def get_record(record_id: int) -> dict[str, Any]:
    """Отримати запис за id."""
    with closing(_connect()) as connection:
        return _fetch_record(connection, record_id)


def list_records(
    *,
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Список записів із фільтрами (через AND) та поділом на сторінки.

    SQL-фрагменти нижче — лише константи з коду, значення передаються
    окремим списком параметрів.
    """
    clauses: list[str] = []
    params: list[Any] = []
    if category_id is not None:
        clauses.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        clauses.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        clauses.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        clauses.append("instr(r.title, ?) > 0")
        params.append(q)

    sql = RECORD_SELECT
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(_connect()) as connection:
        rows = connection.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def replace_record(record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Повністю замінити змінювані поля запису; id не змінюється."""
    try:
        with closing(_connect()) as connection, connection:
            exists = connection.execute(
                "SELECT 1 FROM records WHERE id = ?", (record_id,)
            ).fetchone()
            if exists is None:
                raise NotFoundError("Запис не знайдено")
            _require_category(connection, data["category_id"])
            cursor = connection.execute(
                UPDATE_RECORD, (*_record_params(data), record_id)
            )
            if cursor.rowcount == 0:
                raise NotFoundError("Запис не знайдено")
            return _fetch_record(connection, record_id)
    except sqlite3.IntegrityError as exc:
        _raise_if_unique(exc, "Запис із таким code вже існує")
        raise


def delete_record(record_id: int) -> None:
    """Видалити запис."""
    with closing(_connect()) as connection, connection:
        cursor = connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
        if cursor.rowcount == 0:
            raise NotFoundError("Запис не знайдено")


def create_records_bulk(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Атомарно додати пакет записів в одній транзакції.

    Один `with connection` = одна транзакція: commit() виконується один раз
    після всіх вставок, а будь-який виняток скасовує весь пакет.
    """
    try:
        with closing(_connect()) as connection, connection:
            for category_id in sorted({item["category_id"] for item in items}):
                _require_category(connection, category_id)
            new_ids = [
                int(
                    connection.execute(INSERT_RECORD, _record_params(item)).lastrowid
                    or 0
                )
                for item in items
            ]
            return [_fetch_record(connection, record_id) for record_id in new_ids]
    except sqlite3.IntegrityError as exc:
        _raise_if_unique(exc, "Дублікат code у пакеті або в базі, пакет скасовано")
        raise


# --------------------------- початкові дані ---------------------------


def is_database_empty() -> bool:
    """Перевірити, що в базі немає ні категорій, ні записів."""
    with closing(_connect()) as connection:
        categories = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        records = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    return categories == 0 and records == 0


def seed_initial_data(
    categories: list[dict[str, Any]], records: list[dict[str, Any]]
) -> None:
    """Додати категорії (з id із JSON) та записи в одній транзакції."""
    with closing(_connect()) as connection, connection:
        connection.executemany(
            "INSERT INTO categories (id, name) VALUES (?, ?)",
            [(item["id"], item["name"]) for item in categories],
        )
        connection.executemany(INSERT_RECORD, [_record_params(r) for r in records])
