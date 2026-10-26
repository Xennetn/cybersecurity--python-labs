"""Головна точка входу для Лабораторної роботи №2 (підкоманди demo та analyze)."""

import argparse
import sys
from datetime import timedelta
from pathlib import Path

from labs.lab02.task1 import Admin, AuditLog, User, UserAccount
from labs.lab02.task2 import run_audit, setup_logger


def run_demo() -> None:
    """Демонстраційний сценарій для Завдання 1 (ООП)."""
    print("=" * 70)
    print("ДЕМОНСТРАЦІЯ ЗАВДАННЯ 1: ОБ'ЄКТНО-ОРІЄНТОВАНА МОДЕЛЬ БЕЗПЕКИ")
    print("=" * 70)

    audit = AuditLog()

    # 1. Створення користувача та валідація email через @property
    print("\n1. Створення користувача та перевірка валідатора email:")
    user = User(
        username="m_dudas", email="dudas_sec@polynet.lviv.ua", role="security_analyst"
    )
    user.set_password("SuperSecret2026!P@ss")
    print(f"Створено: {user}")

    print("Тестування некоректного email:")
    try:
        user.email = "bad_email"
    except ValueError as e:
        print(f"[Успішно перехоплено ValueError]: {e}")

    # 2. Наслідування: створення Admin та перевірка прав
    print("\n2. Тестування наслідування (Клас Admin):")
    admin = Admin(
        username="sec_admin",
        email="root_admin@polynet.lviv.ua",
        permissions={"READ_LOGS", "MANAGE_USERS"},
    )
    print(admin)
    print(f"Чи є право MANAGE_USERS: {admin.has_permission('MANAGE_USERS')}")
    print(f"Чи є право DELETE_SYSTEM: {admin.has_permission('DELETE_SYSTEM')}")
    admin.grant_permission("DELETE_SYSTEM")
    print(
        f"Після grant_permission('DELETE_SYSTEM'): {admin.has_permission('DELETE_SYSTEM')}"
    )

    # 3. Композиція: UserAccount та перевірка входу
    print("\n3. Тестування входу, виходу та аудиту (UserAccount):")
    account = UserAccount(user=user, audit_log=audit)

    print("Спроба входу з невірним паролем:")
    ok_fail = account.login("m_dudas", "WrongPassword", ip="192.168.1.100")
    print(
        f"Результат входу: {ok_fail} (is_authenticated: {account.is_authenticated()})"
    )

    print("\nСпроба входу з вірним паролем:")
    ok_success = account.login("m_dudas", "SuperSecret2026!P@ss", ip="192.168.1.100")
    print(
        f"Результат входу: {ok_success} (is_authenticated: {account.is_authenticated()})"
    )

    # 4. ДЕМОНСТРАЦІЯ ТАЙМАУТУ СЕСІЇ (Вимога методички)
    print("\n4. Перевірка завершення сеансу за таймаутом (SESSION_TIMEOUT_SEC = 900):")
    print(f"Активність сесії одразу після входу: {account.is_authenticated()}")
    if account.session is not None:
        # Штучно зміщуємо час останньої активності назад на 901 секунду
        account.session.last_activity -= timedelta(seconds=901)
        print(
            f"Активність сесії після спливу 901 сек: {account.is_authenticated()} (Сеанс протерміновано)"
        )

    # 5. Спеціальні методи __getitem__ та __setitem__
    print("\n5. Перевірка магічних методів __getitem__ та __setitem__:")
    print(f"account['username'] : {account['username']}")
    print(f"account['email']    : {account['email']}")
    account["email"] = "new_security_contact@polynet.lviv.ua"
    print(f"Після оновлення через account['email']: {account['email']}")

    try:
        _ = account["__password_hash"]
    except KeyError as e:
        print(f"[Успішно захищено]: Спроба отримати хеш викликала {type(e).__name__}")

    # 6. Вихід та демонстрація журналу аудиту
    account.logout()
    print("\nКористувач вийшов із системи.")
    audit.show_all()
    print("\n" + "=" * 70)


def main() -> None:
    """Розбір підкоманд CLI."""
    parser = argparse.ArgumentParser(
        description="Лабораторна робота №2: CLI утиліти кібербезпеки"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Підкоманда demo
    subparsers.add_parser("demo", help="Запустити демонстрацію Завдання 1 (ООП)")

    # Підкоманда analyze (Варіант 9)
    analyze_parser = subparsers.add_parser(
        "analyze", help="Запустити аудит HTTP-заголовків (Завдання 2)"
    )
    analyze_parser.add_argument(
        "--headers-file",
        type=Path,
        default=Path("labs/lab02/data/data_v09/headers.json"),
        help="Шлях до файлу заголовків",
    )
    analyze_parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("labs/lab02/data/headers_audit.csv"),
        help="Шлях до файлу CSV звіту",
    )
    analyze_parser.add_argument(
        "--strict", action="store_true", help="Посилений режим аудиту"
    )
    analyze_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Рівень логування",
    )

    args = parser.parse_args()

    if args.subcommand == "demo":
        run_demo()
    elif args.subcommand == "analyze":
        logger = setup_logger(args.log_level)
        try:
            run_audit(args.headers_file, args.output_csv, args.strict, logger)
        except (OSError, ValueError, TypeError) as exc:
            logger.error("%s", exc)
            sys.exit(1)


if __name__ == "__main__":
    main()
