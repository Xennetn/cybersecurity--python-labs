"""Завдання 1: Комплексний аналізатор надійності паролів (Варіант 9)."""

import os
import random
import string
import sys

# Підключення спільного модуля
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Вхідні дані Варіанту 9
PASSWORDS = [
    "Digital@F0r3nsics",
    "plain",
    "Encrypt10n@Key",
    "member",
    "Security@Audit2023",
    "regular",
    "Hack3r@D3fense",
    "ordinary",
    "Threat@Intel",
    "usual",
]

CRITERIA = {
    "min_length": 8,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

FORBIDDEN_PASSWORDS = {
    "plain",
    "member",
    "regular",
    "ordinary",
    "usual",
    "user",
}


def evaluate_password(
    pwd: str,
    all_passwords: list[str],
    criteria: dict,
    forbidden: set[str],
) -> str:
    """Оцінює надійність пароля за правилами безпеки."""
    # 1. Заборонений: у списку заборонених або занадто короткий
    if pwd in forbidden or len(pwd) < criteria["min_length"]:
        return "Заборонений"

    has_digit = any(char.isdigit() for char in pwd)
    has_upper = any(char.isupper() for char in pwd)
    has_lower = any(char.islower() for char in pwd)
    has_special = any(char in string.punctuation for char in pwd)

    # Перевірка виконання обов'язкових умов надійності
    meets_all_mandatory = (
        len(pwd) >= criteria["min_length"]
        and (not criteria["require_digits"] or has_digit)
        and (not criteria["require_upper"] or has_upper)
        and (not criteria["require_special"] or has_special)
    )

    # 2. Дуже сильний: всі критерії, довжина >= min + 4 і повна унікальність
    if (
        meets_all_mandatory
        and len(pwd) >= criteria["min_length"] + 4
        and all_passwords.count(pwd) == 1
    ):
        return "Дуже сильний"

    # 3. Сильний: всі критерії, але довжина < min + 4 або дублюється
    if meets_all_mandatory:
        return "Сильний"

    # 4. Середній: достатня довжина і мінімум 2 типи символів
    type_matches = sum([has_digit, has_upper, has_lower, has_special])
    if len(pwd) >= criteria["min_length"] and type_matches >= 2:
        return "Середній"

    # 5. Слабкий: відповідає хоча б одній групі символів
    if any([has_digit, has_upper, has_lower, has_special]):
        return "Слабкий"

    return "Заборонений"


def run_task1() -> None:
    """Запуск виконання аналізатора паролів."""
    print("=" * 80)
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print("Завдання 1: Комплексний аналізатор надійності паролів")
    print("=" * 80)

    # Копіюємо список та штучно додаємо 3 випадкові дублікати
    working_list = list(PASSWORDS)
    random_indices = [random.randint(0, len(PASSWORDS) - 1) for _ in range(3)]
    for idx in random_indices:
        working_list.append(PASSWORDS[idx])

    print(f"Загальна кількість паролів (з дублікатами): {len(working_list)}\n")

    # Форматування таблиці
    header = f"{'№':<4} | {'Пароль':<24} | {'Довжина':<8} | {'Надійність':<16}"
    print(header)
    print("-" * len(header))

    for idx, pwd in enumerate(working_list, start=1):
        status = evaluate_password(pwd, working_list, CRITERIA, FORBIDDEN_PASSWORDS)
        print(f"{idx:<4} | {pwd:<24} | {len(pwd):<8} | {status:<16}")


if __name__ == "__main__":
    run_task1()
