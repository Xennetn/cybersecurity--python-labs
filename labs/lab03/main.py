"""FastAPI-застосунок: облік часу опрацювання повідомлень (варіант 9).

Запуск з кореня репозиторію:
    python -m labs.lab03.seed
    uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
"""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from labs.lab03 import config
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from labs.lab03.schemas import PingResponse, StudentInfo
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску (дані не змінюються)."""
    initialize_database()
    yield


app = FastAPI(
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
    lifespan=lifespan,
)
app.include_router(categories.router)
app.include_router(records.router)


@app.exception_handler(sqlite3.Error)
async def sqlite_error_handler(request: Request, exc: sqlite3.Error) -> JSONResponse:
    """Технічні деталі йдуть у лог, клієнт отримує загальне повідомлення."""
    logger.error("Помилка SQLite у %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка роботи з базою даних"},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Відповідь 422 без повернення введених значень (inf/NaN не серіалізуються)."""
    errors = [
        {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/ping", response_model=PingResponse, tags=["Службові"], summary="Перевірка")
def ping() -> dict[str, str]:
    """Перевірка доступності API."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentInfo,
    tags=["Службові"],
    summary="Дані студента",
)
def student() -> dict[str, str | int]:
    """Повертає ПІБ, групу та номер варіанта з `shared/student.py`."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }
