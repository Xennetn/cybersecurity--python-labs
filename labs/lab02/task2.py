"""Завдання 2 (Варіант 9): Аудитор безпеки HTTP-заголовків відповідей."""

import argparse
import csv
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MANDATORY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
]

VERSION_LEAK_PATTERN = re.compile(r"(\d+(\.\d+)+|[a-zA-Z]+/\d+)")


@dataclass
class AuditResult:
    """Клас збереження результатів перевірки ресурсу."""

    target: str
    score: int
    grade: str
    status: str
    missing_headers: list[str]
    software_leaks: list[str]


def setup_logger(log_level: str) -> logging.Logger:
    """Налаштовує консольне логування аудиту."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger = logging.getLogger("http_auditor")
    logger.setLevel(numeric_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def normalize_input_data(data: object) -> list[tuple[str, dict[str, str]]]:
    """Нормалізує вхідні дані (список або словник) у єдиний формат (target, headers)."""
    items: list[tuple[str, dict[str, str]]] = []
    if isinstance(data, dict):
        for target, headers in data.items():
            if isinstance(headers, dict):
                items.append(
                    (str(target), {str(k): str(v) for k, v in headers.items()})
                )
    elif isinstance(data, list):
        for idx, entry in enumerate(data, start=1):
            if not isinstance(entry, dict):
                continue
            target = None
            for key in (
                "target",
                "url",
                "resource",
                "site",
                "host",
                "endpoint",
                "domain",
            ):
                if key in entry and isinstance(entry[key], str):
                    target = entry[key]
                    break

            if "headers" in entry and isinstance(entry["headers"], dict):
                headers = {str(k): str(v) for k, v in entry["headers"].items()}
                target = target or f"Resource #{idx}"
                items.append((target, headers))
            else:
                headers = {
                    str(k): str(v)
                    for k, v in entry.items()
                    if k
                    not in (
                        "target",
                        "url",
                        "resource",
                        "site",
                        "host",
                        "endpoint",
                        "domain",
                    )
                }
                target = target or f"Resource #{idx}"
                items.append((target, headers))
    return items


def evaluate_resource(
    target: str, raw_headers: dict[str, str], strict: bool
) -> AuditResult:
    """Оцінює безпеку заголовків окремого ресурсу."""
    headers_lower = {str(k).lower(): str(v) for k, v in raw_headers.items()}

    missing: list[str] = []
    score = 100

    penalty_missing = 25 if strict else 20
    for header in MANDATORY_HEADERS:
        if header.lower() not in headers_lower:
            missing.append(header)
            score -= penalty_missing

    leaks: list[str] = []
    server_val = headers_lower.get("server")
    if server_val and VERSION_LEAK_PATTERN.search(server_val):
        actual_name = next(
            (v for k, v in raw_headers.items() if k.lower() == "server"), server_val
        )
        leaks.append(f"Server: {actual_name}")
        score -= 15

    x_powered = headers_lower.get("x-powered-by")
    if x_powered:
        actual_name = next(
            (v for k, v in raw_headers.items() if k.lower() == "x-powered-by"),
            x_powered,
        )
        leaks.append(f"X-Powered-By: {actual_name}")
        score -= 15

    score = max(0, score)

    if score >= 90:
        grade = "A+"
        status = "PASS"
    elif score >= 60:
        grade = "C"
        status = "WARN"
    else:
        grade = "F"
        status = "FAIL"

    return AuditResult(
        target=target,
        score=score,
        grade=grade,
        status=status,
        missing_headers=missing,
        software_leaks=leaks,
    )


def run_audit(
    headers_path: Path, output_csv: Path | None, strict: bool, logger: logging.Logger
) -> list[AuditResult]:
    """Виконує повний цикл аудиту заголовків."""
    logger.info("Auditing HTTP response headers from %s...", headers_path)

    if not headers_path.exists():
        logger.error("Файл заголовків не знайдено: %s", headers_path)
        raise FileNotFoundError(f"Файл {headers_path} не існує.")

    with headers_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    entries = normalize_input_data(raw_data)

    results: list[AuditResult] = []
    for target, headers in entries:
        res = evaluate_resource(target, headers, strict=strict)
        results.append(res)

    print(
        f"\n{'Target Resource':<30} | {'Security Score':<18} | {'Status':<6} | {'Missing Security Headers'}"
    )
    print("-" * 95)
    for r in results:
        score_str = f"{r.score}/100 ({r.grade})"
        missing_str = ", ".join(r.missing_headers) if r.missing_headers else "None"
        print(f"{r.target:<30} | {score_str:<18} | {r.status:<6} | {missing_str}")

    print("\n=== Server Software Leak Alerts ===")
    leak_found = False
    for r in results:
        for leak in r.software_leaks:
            leak_found = True
            logger.warning("[LEAK] %s leaks info in '%s'", r.target, leak)
    if not leak_found:
        print("Витоків інформації про версії ПЗ не виявлено.")

    if output_csv:
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Target",
                    "Score",
                    "Grade",
                    "Status",
                    "MissingHeaders",
                    "SoftwareLeaks",
                ]
            )
            for r in results:
                writer.writerow(
                    [
                        r.target,
                        r.score,
                        r.grade,
                        r.status,
                        "; ".join(r.missing_headers),
                        "; ".join(r.software_leaks),
                    ]
                )
        logger.info("Header audit report saved to %s", output_csv)

    return results


def main() -> None:
    """Точка входу при окремому запуску task2.py."""
    parser = argparse.ArgumentParser(
        description="Аудитор безпеки HTTP-заголовків (Варіант 9)"
    )
    parser.add_argument(
        "--headers-file", type=Path, required=True, help="Шлях до JSON-файлу заголовків"
    )
    parser.add_argument(
        "--output-csv", type=Path, default=None, help="Шлях для вивантаження CSV-звіту"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Посилений режим перевірки"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Рівень логування",
    )

    args = parser.parse_args()
    logger = setup_logger(args.log_level)
    run_audit(args.headers_file, args.output_csv, args.strict, logger)


if __name__ == "__main__":
    main()
