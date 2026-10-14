"""Завдання 2 (Варіант 9): Аудитор безпеки HTTP-заголовків відповідей."""

import argparse
import csv
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MANDATORY_HEADERS = (
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
)

# Витік версії: "2.4.49", "nginx/1.18.0", "Microsoft-IIS/10.0"
VERSION_LEAK_PATTERN = re.compile(r"\d+(?:\.\d+)+|[a-zA-Z]+/\d+")

PENALTY_MISSING = 20
PENALTY_MISSING_STRICT = 25
PENALTY_LEAK = 15

# (мінімальний бал, оцінка, статус) - від найвищого до найнижчого
GRADES = ((90, "A+", "PASS"), (60, "C", "WARN"), (0, "F", "FAIL"))

logger = logging.getLogger("http_auditor")


@dataclass
class AuditResult:
    """Результат перевірки одного ресурсу."""

    target: str
    score: int
    grade: str
    status: str
    missing_headers: list[str]
    software_leaks: list[str]


def setup_logger(log_level: str) -> logging.Logger:
    """Налаштовує консольне логування аудиту."""
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger


def load_entries(path: Path) -> list[tuple[str, dict[str, str]]]:
    """Читає JSON: список {url, headers} або словник {url: headers}."""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [{"url": url, "headers": hdrs} for url, hdrs in data.items()]
    if not isinstance(data, list):
        raise TypeError("Очікується список {url, headers} або словник {url: headers}.")

    entries: list[tuple[str, dict[str, str]]] = []
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict) or not isinstance(item.get("headers"), dict):
            logger.warning("Запис #%d пропущено: немає об'єкта 'headers'.", idx)
            continue
        target = str(item.get("url") or item.get("target") or f"Resource #{idx}")
        entries.append((target, {str(k): str(v) for k, v in item["headers"].items()}))
    return entries


def evaluate_resource(
    target: str, raw_headers: dict[str, str], strict: bool
) -> AuditResult:
    """Оцінює безпеку заголовків окремого ресурсу."""
    headers = {k.lower(): v for k, v in raw_headers.items()}

    missing = [h for h in MANDATORY_HEADERS if h.lower() not in headers]

    leaks: list[str] = []
    server = headers.get("server", "")
    if VERSION_LEAK_PATTERN.search(server):  # Server - лише якщо видно версію
        leaks.append(f"Server: {server}")
    if "x-powered-by" in headers:  # X-Powered-By розкриває стек сам по собі
        leaks.append(f"X-Powered-By: {headers['x-powered-by']}")

    penalty = PENALTY_MISSING_STRICT if strict else PENALTY_MISSING
    score = max(0, 100 - penalty * len(missing) - PENALTY_LEAK * len(leaks))

    grade, status = next((g, s) for limit, g, s in GRADES if score >= limit)
    return AuditResult(target, score, grade, status, missing, leaks)


def print_table(results: list[AuditResult]) -> None:
    """Виводить підсумкову таблицю з шириною за найдовшим ресурсом."""
    width = max([len("Target Resource")] + [len(r.target) for r in results])
    print(
        f"\n{'Target Resource':<{width}} | {'Security Score':<14} | "
        f"{'Status':<6} | Missing Security Headers"
    )
    print("-" * (width + 60))
    for r in results:
        score = f"{r.score}/100 ({r.grade})"
        missing = ", ".join(r.missing_headers) or "None"
        print(f"{r.target:<{width}} | {score:<14} | {r.status:<6} | {missing}")


def save_csv(results: list[AuditResult], path: Path) -> None:
    """Зберігає результати аудиту у CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Target", "Score", "Grade", "Status", "MissingHeaders", "SoftwareLeaks"]
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


def run_audit(
    headers_path: Path, output_csv: Path | None, strict: bool, logger: logging.Logger
) -> list[AuditResult]:
    """Виконує повний цикл аудиту заголовків."""
    logger.info("Auditing HTTP response headers from %s...", headers_path)
    if not headers_path.is_file():
        raise FileNotFoundError(f"Файл заголовків не знайдено: {headers_path}")

    results = [
        evaluate_resource(target, headers, strict)
        for target, headers in load_entries(headers_path)
    ]
    if not results:
        raise ValueError("У файлі немає жодного коректного запису для аудиту.")

    print_table(results)

    # Вимога методички: логування відсутніх заголовків
    for r in results:
        if r.missing_headers:
            logger.warning(
                "%s: missing headers: %s", r.target, ", ".join(r.missing_headers)
            )

    print("\n=== Server Software Leak Alerts ===")
    leaks = [(r.target, leak) for r in results for leak in r.software_leaks]
    for target, leak in leaks:
        logger.warning("[LEAK] %s leaks info in '%s'", target, leak)
    if not leaks:
        print("Витоків інформації про версії ПЗ не виявлено.")

    if output_csv:
        save_csv(results, output_csv)
        logger.info("Header audit report saved to %s", output_csv)

    return results


def main() -> int:
    """Точка входу при окремому запуску task2.py."""
    parser = argparse.ArgumentParser(
        description="Аудитор безпеки HTTP-заголовків (Варіант 9)"
    )
    parser.add_argument("--headers-file", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--strict", action="store_true", help="Посилений режим")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = parser.parse_args()

    log = setup_logger(args.log_level)
    try:
        run_audit(args.headers_file, args.output_csv, args.strict, log)
    except (OSError, ValueError, TypeError) as exc:  # JSONDecodeError ⊂ ValueError
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
