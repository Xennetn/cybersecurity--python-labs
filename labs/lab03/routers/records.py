"""Маршрути ресурсу /records."""

from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query

from labs.lab03 import config, repository
from labs.lab03.errors import RepositoryError
from labs.lab03.routers.http_errors import to_http_exception
from labs.lab03.schemas import (
    ErrorResponse,
    RecordCreate,
    RecordRead,
    RecordReplace,
    RecordStatus,
)

router = APIRouter(prefix="/records", tags=["Записи"])

RecordId = Annotated[int, Path(gt=0, description="Додатний ідентифікатор запису")]

NOT_FOUND = {"model": ErrorResponse, "description": "Запис або категорію не знайдено"}
CONFLICT = {"model": ErrorResponse, "description": "Дублікат code"}


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Отримати список записів із фільтрами",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status: Annotated[
        RecordStatus | None, Query(description="Лише записи з цим статусом")
    ] = None,
    min_value: Annotated[
        float | None,
        Query(
            ge=config.VALUE_MIN,
            allow_inf_nan=False,
            description="Мінімальна тривалість у хвилинах (value >= min_value)",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Буквальний підрядок у title (з урахуванням регістру)",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=config.MAX_LIMIT, description="Максимальна кількість записів"),
    ] = config.DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0, description="Кількість пропущених записів")] = 0,
) -> list[dict[str, Any]]:
    """Фільтри поєднуються через AND, результат відсортовано за `id`."""
    return repository.list_records(
        category_id=category_id,
        status=status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=HTTPStatus.CREATED,
    summary="Створити пакет записів (атомарно)",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def create_records_bulk(
    payload: Annotated[
        list[RecordCreate],
        Body(min_length=1, max_length=config.MAX_BATCH_SIZE),
    ],
) -> list[dict[str, Any]]:
    """Зберігає від 1 до 100 записів в одній транзакції: або всі, або жодного."""
    try:
        return repository.create_records_bulk([item.model_dump() for item in payload])
    except RepositoryError as exc:
        raise to_http_exception(exc) from exc


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис за id",
    responses={404: NOT_FOUND},
)
def get_record(record_id: RecordId) -> dict[str, Any]:
    """Повертає запис разом із назвою категорії."""
    try:
        return repository.get_record(record_id)
    except RepositoryError as exc:
        raise to_http_exception(exc) from exc


@router.post(
    "",
    response_model=RecordRead,
    status_code=HTTPStatus.CREATED,
    summary="Створити запис",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def create_record(payload: RecordCreate) -> dict[str, Any]:
    """Створює запис; `id` призначає база даних."""
    try:
        return repository.create_record(payload.model_dump())
    except RepositoryError as exc:
        raise to_http_exception(exc) from exc


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити змінювані поля запису",
    responses={404: NOT_FOUND, 409: CONFLICT},
)
def replace_record(record_id: RecordId, payload: RecordReplace) -> dict[str, Any]:
    """Замінює всі п'ять змінюваних полів; `id` залишається незмінним."""
    try:
        return repository.replace_record(record_id, payload.model_dump())
    except RepositoryError as exc:
        raise to_http_exception(exc) from exc


@router.delete(
    "/{record_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Видалити запис",
    responses={404: NOT_FOUND},
)
def delete_record(record_id: RecordId) -> None:
    """Видаляє запис за `id`."""
    try:
        repository.delete_record(record_id)
    except RepositoryError as exc:
        raise to_http_exception(exc) from exc
