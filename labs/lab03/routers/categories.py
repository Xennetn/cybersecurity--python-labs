"""Маршрути ресурсу /categories."""

from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Path

from labs.lab03 import repository
from labs.lab03.errors import RepositoryError
from labs.lab03.routers.http_errors import to_http_exception
from labs.lab03.schemas import CategoryCreate, CategoryRead, ErrorResponse

router = APIRouter(prefix="/categories", tags=["Категорії"])

CategoryId = Annotated[int, Path(gt=0, description="Додатний ідентифікатор категорії")]


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Отримати список категорій",
)
def list_categories() -> list[dict[str, Any]]:
    """Повертає всі категорії за зростанням `id`."""
    return repository.list_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=HTTPStatus.CREATED,
    summary="Створити категорію",
    responses={409: {"model": ErrorResponse, "description": "Назва вже існує"}},
)
def create_category(payload: CategoryCreate) -> dict[str, Any]:
    """Створює категорію; `id` призначає база даних."""
    try:
        return repository.create_category(payload.name)
    except RepositoryError as exc:
        raise to_http_exception(exc) from exc


@router.delete(
    "/{category_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Видалити порожню категорію",
    responses={
        404: {"model": ErrorResponse, "description": "Категорію не знайдено"},
        409: {"model": ErrorResponse, "description": "Категорія містить записи"},
    },
)
def delete_category(category_id: CategoryId) -> None:
    """Видаляє категорію, якщо до неї не прив'язано жодного запису."""
    try:
        repository.delete_category(category_id)
    except RepositoryError as exc:
        raise to_http_exception(exc) from exc
