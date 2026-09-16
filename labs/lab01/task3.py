"""Завдання 3: Безпечне хешування, CSV-база та JSON-логування (Варіант 9)."""

import csv
import functools
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

# Підключення персональних даних студента
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Константи варіанту 9
MIN_PASSWORD_LENGTH = 13
PERSONAL_SALT = f"{VARIANT_NUMBER:05d}"  # Рядок "00009"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_CSV_FILE = os.path.join(DATA_DIR, "users.csv")
LOG_JSON_FILE = os.path.join(DATA_DIR, "log.json")


class ValidationError(Exception):
    """Власний виняток для помилок валідації довжини пароля."""



def generate_hash(password: str, salt: str = "00000") -> str:
    """Генерує хеш sha224 від конкатенації пароля та солі."""
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль занадто короткий (мінімум {MIN_PASSWORD_LENGTH} символів)."
        )

    salted_data = (password + salt).encode("utf-8")
    return hashlib.sha224(salted_data).hexdigest()


def log_event(func):
    """Декоратор для логування спроб автентифікації у JSON-файл."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        username = args[0] if len(args) > 0 else kwargs.get("username", "")
        safe_args = [args[0], "********"] if len(args) > 1 else list(args)

        try:
            result = func(*args, **kwargs)
            status_str = "success" if result else "failure"
        except Exception as exc:
            status_str = f"error: {type(exc).__name__}"
            raise
        finally:
            log_entry = {
                "event": "login",
                "user": username,
                "result": status_str if "status_str" in locals() else "failed",
                "timestamp": datetime.now(tz=timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "args": safe_args,
                "kwargs": {
                    k: ("********" if k == "password" else v)
                    for k, v in kwargs.items()
                },
            }

            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                logs = []
                if os.path.exists(LOG_JSON_FILE):
                    try:
                        with open(LOG_JSON_FILE, "r", encoding="utf-8") as f:
                            logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []

                logs.append(log_entry)
                with open(LOG_JSON_FILE, "w", encoding="utf-8") as f:
                    json.dump(logs, f, indent=4, ensure_ascii=False)
            except (OSError, PermissionError) as err:
                print(f"[Помилка запису логу]: {err}")

        return result

    return wrapper


def create_user(username: str, password: str) -> tuple[str, str]:
    """Створює кортеж користувача з обчисленим хешем."""
    hash_val = generate_hash(password, PERSONAL_SALT)
    return (username, hash_val)


def create_users(users_list: tuple) -> None:
    """Зберігає список користувачів у файл users.csv."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        for user, pwd in users_list:
            u_name, u_hash = create_user(user, pwd)
            writer.writerow([u_name, u_hash])


def read_users_db() -> list[tuple[str, str]]:
    """Зчитує користувачів із CSV-файлу."""
    if not os.path.exists(USERS_CSV_FILE):
        raise FileNotFoundError(f"Файл {USERS_CSV_FILE} не знайдено.")

    users_db = []
    with open(USERS_CSV_FILE, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:
                users_db.append((row[0], row[1]))
    return users_db


@log_event
def login(username: str, password: str) -> bool:
    """Автентифікує користувача шляхом звірки sha224-хешу з базою."""
    if not username or not password:
        raise ValueError("Логін і пароль є обов'язковими для заповнення.")

    users_db = read_users_db()
    input_hash = generate_hash(password, PERSONAL_SALT)

    for db_user, db_hash in users_db:
        if db_user == username:
            return db_hash == input_hash
    return False


def run_task3() -> None:
    """Головна функція виконання Завдання 3."""
    print("=" * 80)
    print(
        f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}"
    )
    print("Завдання 3: Безпечне хешування, CSV-база та JSON-логування")
    print(
        f"Алгоритм: SHA-224 | Сіль: {PERSONAL_SALT} | "
        f"Мін. довжина: {MIN_PASSWORD_LENGTH}"
    )
    print("=" * 80)

    # 10 тестових користувачів (довжина паролів >= 13)
    users_to_register = (
        ("cloud_admin", "SuperSecurePassword2026!"),
        ("devops_lead", "ContinuousDeploy99#"),
        ("sec_officer", "ZeroTrustPolicy2026$"),
        ("qa_specialist", "AutomatedTestingPass!"),
        ("partner_dev", "ApiIntegrationSecret123"),
        ("audit_manager", "ComplianceCheck2026!"),
        ("soc_analyst", "IncidentResponseTeam#1"),
        ("db_operator", "DatabaseProtectionKey!"),
        ("network_eng", "CoreRouterSecure2026"),
        ("guest_auditor", "TemporaryPasscode2026!"),
    )

    try:
        # Реєстрація користувачів у CSV
        print("\n1. Реєстрація користувачів та збереження в CSV...")
        create_users(users_to_register)
        print("Користувачів успішно записано у файл users.csv.")

        # Читання та виведення бази даних у вигляді таблиці
        print("\n2. Зчитування зареєстрованих користувачів із бази:")
        db_records = read_users_db()
        header = f"{'Логін':<18} | {'Хеш пароля (SHA-224 + сіль)':<56}"
        print(header)
        print("-" * len(header))
        for u, h in db_records:
            print(f"{u:<18} | {h:<56}")

        # Демонстрація автентифікації та логування
        print("\n3. Тестування входу в систему:")

        ok_res = login("cloud_admin", "SuperSecurePassword2026!")
        print(
            f"Вхід cloud_admin (правильний пароль): "
            f"{'Успішно' if ok_res else 'Невдача'}"
        )

        fail_res = login("cloud_admin", "WrongPasswordExample123!")
        print(
            f"Вхід cloud_admin (невірний пароль): "
            f"{'Успішно' if fail_res else 'Невдача'}"
        )

        unknown_res = login("unknown_user", "SomeSecretPassword2026!")
        print(f"Вхід unknown_user: {'Успішно' if unknown_res else 'Невдача'}")

        # Перевірка валідації короткого пароля
        print("\n4. Перевірка обробки помилок валідації:")
        try:
            login("cloud_admin", "short")
        except ValidationError as val_err:
            print(f"Перехоплено очікуваний ValidationError: {val_err}")

    except (OSError, FileNotFoundError, PermissionError, ValidationError, ValueError) as e:
        print(f"[Критична помилка виконання]: {type(e).__name__} -> {e}")


if __name__ == "__main__":
    run_task3()