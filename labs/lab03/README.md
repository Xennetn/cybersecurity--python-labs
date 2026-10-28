# Лабораторна робота №3: FastAPI + SQLite (варіант 9)

**Виконав:** студент групи КБ-208 Дудас Михайло Ігорович
**Варіант:** 9, облік часу опрацювання повідомлень

## Предметна область

Сервіс обліку тривалості перевірки повідомлень про події безпеки.

| Поле | Значення |
|---|---|
| Категорії (`categories`) | `siem`, `helpdesk`, `monitoring` (джерело повідомлення) |
| Запис (`records`) | одне вимірювання опрацювання повідомлення |
| `value` | тривалість у **хвилинах** (`minutes`), скінченне число `>= 0`, верхньої межі немає |
| `status` | `new`, `in_progress`, `done` (стан перевірки вимірювання) |
| Поріг | `15.0` хвилин (орієнтир для фільтра `min_value`) |
| Назва запису | `Вимірювання опрацювання NN`, код `V09-NN` |

Усі дані навчальні.

## Структура

```text
labs/lab03/
├── main.py          # FastAPI-застосунок, /ping, /student, обробники помилок
├── database.py      # з'єднання SQLite, виконання schema.sql
├── schema.sql       # готова схема (варіанти 7-9)
├── repository.py    # параметризовані SQL-запити, транзакції
├── schemas.py       # Pydantic-моделі
├── errors.py        # прикладні винятки (без залежності від FastAPI)
├── config.py        # параметри варіанта 9
├── seed.py          # початкове заповнення з data/seed.json
├── routers/         # categories.py, records.py, http_errors.py
├── data/seed.json   # початкові дані (у Git)
└── data/lab3.sqlite3  # створюється програмою (НЕ в Git)
```

## Встановлення

З кореня репозиторію, в активованому `.venv` (Python 3.10+):

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python -m labs.lab03.seed
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI-схема: http://127.0.0.1:8000/openapi.json

`seed` створює базу за `schema.sql` і додає 3 категорії та 8 записів в одній
транзакції. Повторний запуск не змінює дані. Щоб почати з нуля, видали файл
`labs/lab03/data/lab3.sqlite3` і повтори `seed`.

## Маршрути

| Метод і шлях | Призначення | Успіх |
|---|---|---|
| `GET /ping` | перевірка доступності | 200 |
| `GET /student` | дані з `shared/student.py` | 200 |
| `GET /categories` | список категорій | 200 |
| `POST /categories` | створити категорію | 201 |
| `DELETE /categories/{category_id}` | видалити порожню категорію | 204 |
| `GET /records` | список із фільтрами `category_id`, `status`, `min_value`, `q`, `limit`, `offset` | 200 |
| `GET /records/{record_id}` | один запис | 200 |
| `POST /records` | створити запис | 201 |
| `PUT /records/{record_id}` | замінити всі змінювані поля | 200 |
| `DELETE /records/{record_id}` | видалити запис | 204 |
| `POST /records/bulk` | атомарне пакетне створення (1-100) | 201 |

Помилки: `404` (запис або категорія не існує), `409` (дублікат `code` чи назви,
непорожня категорія), `422` (некоректні дані), `500` (помилка бази, без
технічних деталей у відповіді).

## Приклади запитів

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&min_value=15&limit=5"

curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V09-TEST","title":"Навчальне вимірювання","category_id":1,"value":7.5,"status":"new"}'

# відкат пакета: V09-01 уже є в базі, V09-ROLLBACK не має зберегтися
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V09-ROLLBACK","title":"Перший елемент","category_id":1,"value":4.0,"status":"new"},{"code":"V09-01","title":"Дублікат коду","category_id":2,"value":5.0,"status":"new"}]'
```

Усі сценарії перевірки (2-13) одним запуском, коли API працює:

```bash
bash labs/lab03/demo_requests.sh
```

## Перевірка стилю

```bash
ruff check labs/lab03
ruff format --check labs/lab03
ruff check .
ruff format --check .
```
