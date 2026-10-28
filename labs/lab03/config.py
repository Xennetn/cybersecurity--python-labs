"""Параметри варіанта 9: облік часу опрацювання повідомлень."""

APP_TITLE = "Облік часу опрацювання повідомлень"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
Сервіс обліку тривалості перевірки повідомлень про події безпеки.

* **Категорія** (`categories`) визначає джерело повідомлення: `siem`,
  `helpdesk`, `monitoring`.
* **Запис** (`records`) описує одне вимірювання опрацювання повідомлення.
* **value** — тривалість перевірки в **хвилинах** (`minutes`), скінченне
  число не менше 0, верхньої межі немає.
* **status** — стан перевірки вимірювання: `new`, `in_progress`, `done`.
* **Поріг** для аналізу: 15.0 хвилин (використовується як `min_value`
  у фільтрі списку записів).

Усі дані навчальні й не описують реальну інфраструктуру.
"""

UNIT = "minutes"
THRESHOLD = 15.0
VALUE_MIN = 0.0
CATEGORY_NAMES = ("siem", "helpdesk", "monitoring")
RECORD_TITLE_PREFIX = "Вимірювання опрацювання"

SEED_CATEGORIES_COUNT = 3
SEED_RECORDS_COUNT = 8
MAX_BATCH_SIZE = 100
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
