"""Прикладні винятки шару доступу до даних (без залежності від FastAPI)."""


class RepositoryError(Exception):
    """Базовий виняток шару доступу до даних."""


class NotFoundError(RepositoryError):
    """Запис або категорію не знайдено."""


class ConflictError(RepositoryError):
    """Порушено унікальність або категорія містить записи."""
