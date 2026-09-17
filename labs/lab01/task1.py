"""Завдання 1: Комплексний аналізатор надійності паролів (Варіант 9)."""

import os
import random
import string
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

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
    if pwd in forbidden or len(pwd) < criteria["min_length"]:
        return "Заборонений"

    has_digit = any(char.isdigit() for char in pwd)
    has_upper = any(char.isupper() for char in pwd)
    has_lower = any(char.islower() for char in pwd)
    has_special = any(char in string.punctuation for char in pwd)

    meets_all_mandatory = (
        len(pwd) >= criteria["min_length"]
        and (not criteria["require_digits"] or has_digit)
        and (not criteria["require_upper"] or has_upper)
        and (not criteria["require_special"] or has_special)
    )

    if (
        meets_all_mandatory
        and len(pwd) >= criteria["min_length"] + 4
        and all_passwords.count(pwd) == 1
    ):
        return "Дуже сильний"

    if meets_all_mandatory:
        return "Сильний"

    type_matches = sum([has_digit, has_upper, has_lower, has_special])
    if len(pwd) >= criteria["min_length"] and type_matches >= 2:
        return "Середній"

    if any([has_digit, has_upper, has_lower, has_special]):
        return "Слабкий"

    return "Заборонений"


def run_task1() -> None:
    """Запуск виконання аналізатора паролів."""
    print("=" * 80)
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print("Завдання 1: Комплексний аналізатор надійності паролів")
    print("=" * 80)

    working_list = list(PASSWORDS)
    random_indices = [random.randint(0, len(PASSWORDS) - 1) for _ in range(3)]
    for idx in random_indices:
        working_list.append(PASSWORDS[idx])

    print(f"Загальна кількість паролів (з дублікатами): {len(working_list)}\n")

    header = f"{'№':<4} | {'Пароль':<24} | {'Довжина':<8} | {'Надійність':<16}"
    print(header)
    print("-" * len(header))

    for idx, pwd in enumerate(working_list, start=1):
        status = evaluate_password(pwd, working_list, CRITERIA, FORBIDDEN_PASSWORDS)
        print(f"{idx:<4} | {pwd:<24} | {len(pwd):<8} | {status:<16}")


if __name__ == "__main__":
    run_task1()
