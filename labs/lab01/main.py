"""Головний модуль запуску Лабораторної роботи №1."""

import os
import sys

# Додавання кореня проекту до шляхів імпорту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from labs.lab01.task1 import run_task1
from labs.lab01.task2 import run_task2
from labs.lab01.task3 import run_task3
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


def main() -> None:
    """Запуск демонстрації всіх завдань лабораторної роботи."""
    print("#" * 80)
    print("НАЦІОНАЛЬНИЙ УНІВЕРСИТЕТ «ЛЬВІВСЬКА ПОЛІТЕХНІКА»")
    print("Звіт з Лабораторної роботи №1")
    print(f"Студент: {STUDENT_NAME} | Група: {GROUP_NAME} | Варіант: {VARIANT_NUMBER}")
    print("#" * 80)

    print("\n\n>>> ЗАПУСК ЗАВДАННЯ 1 <<<")
    run_task1()

    print("\n\n>>> ЗАПУСК ЗАВДАННЯ 2 <<<")
    run_task2()

    print("\n\n>>> ЗАПУСК ЗАВДАННЯ 3 <<<")
    run_task3()

    print("Усі завдання Лабораторної роботи №1 виконано успішно.")

if __name__ == "__main__":
    main()
