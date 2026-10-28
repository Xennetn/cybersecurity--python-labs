"""Перетворення прикладних винятків на HTTP-помилки."""

from fastapi import HTTPException

from labs.lab03.errors import ConflictError, NotFoundError, RepositoryError


def to_http_exception(exc: RepositoryError) -> HTTPException:
    """NotFoundError -> 404, ConflictError -> 409, решта -> 500."""
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Внутрішня помилка сервера")
