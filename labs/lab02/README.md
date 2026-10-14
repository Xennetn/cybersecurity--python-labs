# Лабораторна робота №2: Розробка консольних утиліт для задач кібербезпеки

**Виконав:** студент групи КБ-208 Дудас Михайло Ігорович
**Варіант:** 9 — Аудитор безпеки HTTP-заголовків відповідей

Значення `VARIANT_NUMBER = 9` задано в `shared/student.py`.

## 1. Встановлення залежностей

Робота виконується у спільному віртуальному середовищі з ЛР №1. Усі команди запускаються з кореня репозиторію.

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

У `requirements.txt` вказано `ruff` (лінтер і форматер). Інших зовнішніх залежностей немає: використовується лише стандартна бібліотека Python 3.10+.

## 2. Структура файлів

```text
labs/lab02/
├── __init__.py
├── main.py        # підкоманди demo та analyze
├── task1.py       # Завдання 1: User, Admin, Session, AuditLog, UserAccount
├── task2.py       # Завдання 2: аудитор HTTP-заголовків (варіант 9)
├── README.md
└── data/
    └── data_v09/
        └── headers.json   # вхідні дані варіанта 9 з lab2_data.zip
```

## 3. Запуск

### Завдання 1 — демонстрація ООП

```bash
python -m labs.lab02.main demo
```

Показує: створення користувача й валідацію email, права адміністратора, успішний і невдалий вхід, завершення сеансу за таймаутом (`SESSION_TIMEOUT_SEC = 900`), вихід із системи та записи `AuditLog`. При імпорті `task1.py` нічого не виконується.

### Завдання 2 — аудит HTTP-заголовків

```bash
python -m labs.lab02.main analyze \
    --headers-file labs/lab02/data/data_v09/headers.json \
    --output-csv labs/lab02/data/headers_audit.csv
```

Посилений режим і детальне логування:

```bash
python -m labs.lab02.main analyze --strict --log-level DEBUG
```

Окремий запуск утиліти без `main.py`:

```bash
python -m labs.lab02.task2 --headers-file labs/lab02/data/data_v09/headers.json
```

## 4. Параметри CLI (`analyze`)

| Параметр | Опис | Типове значення |
|---|---|---|
| `--headers-file` | Шлях до JSON-файлу із заголовками відповідей | `labs/lab02/data/data_v09/headers.json` |
| `--output-csv` | Шлях для CSV-звіту (каталог створюється автоматично) | `labs/lab02/data/headers_audit.csv` |
| `--strict` | Посилений режим: штраф за відсутній заголовок 25 замість 20 | вимкнено |
| `--log-level` | Рівень логування: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

## 5. Формат вхідних даних

JSON-список об'єктів з ключами `url` і `headers` (також підтримується словник `{url: headers}`):

```json
[
  {
    "url": "https://legacy.example.invalid/",
    "headers": {
      "X-Frame-Options": "SAMEORIGIN",
      "Server": "Apache/2.4.49",
      "X-Powered-By": "PHP/7.4.3"
    }
  }
]
```

Імена заголовків порівнюються без урахування регістру.

## 6. Алгоритм оцінювання

1. Обов'язкові заголовки: `Strict-Transport-Security`, `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`. За кожен відсутній — штраф 20 балів (25 у `--strict`).
2. Витік версії в `Server`: регулярний вираз `\d+(?:\.\d+)+|[a-zA-Z]+/\d+` (наприклад `Apache/2.4.49`, `nginx/1.18.0`). Штраф 15.
3. Заголовок `X-Powered-By`, якщо присутній, завжди вважається витоком технологічного стеку. Штраф 15.
4. Підсумковий бал = `max(0, 100 − штрафи)`.

| Бал | Оцінка | Статус |
|---|---|---|
| 90–100 | A+ | PASS |
| 60–89 | C | WARN |
| 0–59 | F | FAIL |

Відсутні заголовки та витоки записуються в лог рівня `WARNING`.

## 7. Приклад результату

| Ресурс | Бал | Статус | Відсутні заголовки |
|---|---|---|---|
| secure.example.invalid | 100/100 (A+) | PASS | — |
| legacy.example.invalid | 10/100 (F) | FAIL | HSTS, CSP, X-Content-Type-Options |
| api.example.invalid | 65/100 (C) | WARN | X-Frame-Options |
| portal.example.invalid | 85/100 (C) | WARN | — |
| minimal.example.invalid | 5/100 (F) | FAIL | усі чотири |

## 8. Поведінка при помилках

| Ситуація | Реакція |
|---|---|
| Файл заголовків не існує | `[ERROR] Файл заголовків не знайдено: ...`, код виходу 1 |
| Некоректний JSON | `[ERROR]` з описом помилки парсингу, код виходу 1 |
| Невірна структура JSON (не список і не словник) | `[ERROR]`, код виходу 1 |
| Запис без об'єкта `headers` | пропускається з `[WARNING]`, аудит продовжується |
| У файлі немає жодного коректного запису | `[ERROR]`, код виходу 1 |
| Невірне значення `--log-level` | відхиляється `argparse` |

## 9. Перевірка коду

```bash
ruff check .
ruff format --check .
```
