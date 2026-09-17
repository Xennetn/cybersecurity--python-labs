"""Завдання 2: Багаторівнева система контролю доступу (Варіант 9)."""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

USERS = {
    "cloud_architect": {
        "role": "cloud_security",
        "clearance": 4,
        "department": "Cloud",
        "active": True,
    },
    "devops_engineer": {
        "role": "devops",
        "clearance": 3,
        "department": "DevOps",
        "active": True,
    },
    "qa_tester": {
        "role": "quality_assurance",
        "clearance": 2,
        "department": "QA",
        "active": True,
    },
    "partner_access": {
        "role": "partner",
        "clearance": 2,
        "department": "Partnership",
        "active": True,
    },
    "migrated_user": {
        "role": "migrated",
        "clearance": 1,
        "department": "Migration",
        "active": False,
    },
}

RESOURCES = [
    ("cloud_configs", 4),
    ("deployment_pipelines", 3),
    ("test_environments", 2),
    ("partner_apis", 2),
    ("infrastructure_code", 4),
    ("shared_resources", 1),
    ("container_registry", 3),
    ("secrets_vault", 4),
    ("build_artifacts", 2),
    ("public_endpoints", 1),
]

SECURITY_LEVELS = (
    "Development",
    "Staging",
    "Production",
    "Critical Infrastructure",
)

BLOCKED_USERS = {
    "migrated_user",
    "container_breach",
    "pipeline_compromise",
}


def check_access(
    user: str,
    resource_name: str,
    resource_level: int,
    users: dict,
    blocked: set[str],
) -> str:
    """Перевіряє права доступу користувача до заданого ресурсу."""

    if user not in users:
        return "DENY (User not found)"

    if user in blocked:
        return "DENY (User is blocked)"

    user_info = users[user]

    if not user_info.get("active", False):
        return "DENY (Account inactive)"

    if user_info.get("clearance", 0) >= resource_level:
        return "ALLOW"

    return "DENY (Insufficient clearance)"


def run_task2() -> None:
    """Головна функція виконання Завдання 2."""
    print("=" * 80)
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print("Завдання 2: Багаторівнева система контролю доступу")
    print("=" * 80)

    print("\n--- Список ресурсів системи та їхні рівні безпеки ---")
    header_res = f"{'Ресурс':<24} | {'Числовий рівень':<16} | {'Рівень безпеки'}"
    print(header_res)
    print("-" * len(header_res))

    for res_name, res_lvl in RESOURCES:
        text_level = SECURITY_LEVELS[res_lvl - 1]
        print(f"{res_name:<24} | {res_lvl:<16} | {text_level}")

    print("\n--- Результати аудиту доступу користувачів ---")
    test_user_list = list(USERS.keys()) + ["unknown_intruder"]

    for user in test_user_list:
        print(f"\n>> Перевірка для суб'єкта: {user}")
        for res_name, res_lvl in RESOURCES:
            result = check_access(user, res_name, res_lvl, USERS, BLOCKED_USERS)
            print(f"user=[{user}] resource=[{res_name}] -> {result}")


if __name__ == "__main__":
    run_task2()
