"""Завдання 1: Модель користувача, безпечних сесій та аудиту (ООП)."""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

PBKDF2_ITERATIONS = 100_000
SESSION_TIMEOUT_SEC = 900
EMAIL_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class User:
    """Базовий клас облікового запису користувача."""

    def __init__(
        self, username: str, email: str, role: str = "user", active: bool = True
    ) -> None:
        self.username = username
        self.role = role
        self.active = active
        self._email = ""
        self.email = email

        self.__password_hash: bytes | None = None
        self.__password_salt: bytes | None = None

    @property
    def email(self) -> str:
        """Геттер атрибута email."""
        return self._email

    @email.setter
    def email(self, new_email: str) -> None:
        """Сеттер атрибута email з валідацією регулярним виразом."""
        if not isinstance(new_email, str) or not EMAIL_PATTERN.match(new_email):
            raise ValueError(
                f"Некоректний формат email: '{new_email}'. Локальна частина має "
                "починатися з літери і мати довжину 3-64 символи."
            )
        self._email = new_email

    def set_password(self, password: str) -> None:
        """Генерує випадкову сіль та обчислює стійкий PBKDF2-SHA256 хеш."""
        if not password or not isinstance(password, str):
            raise ValueError("Пароль не може бути порожнім.")
        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        """Звіряє введений пароль з еталонним хешем через безпечне порівняння."""
        if not self.__password_hash or not self.__password_salt:
            return False
        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, computed_hash)

    def deactivate(self) -> None:
        """Деактивує користувача."""
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return (
            f"User(username='{self.username}', role='{self.role}', status='{status}')"
        )


class Admin(User):
    """Клас адміністратора системи, що успадковує User."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str = "admin",
        active: bool = True,
        permissions: set[str] | None = None,
    ) -> None:
        super().__init__(username, email, role=role, active=active)
        self.permissions: set[str] = (
            set(permissions) if permissions is not None else set()
        )

    def grant_permission(self, permission: str) -> None:
        """Надає окремий дозвіл адміністратору."""
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        """Відкликає дозвіл у адміністратора."""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Перевіряє наявність дозволу."""
        return permission in self.permissions

    def __str__(self) -> str:
        base_str = super().__str__()
        sorted_perms = sorted(self.permissions)
        return f"Admin({base_str}, permissions={sorted_perms})"


class Session:
    """Клас активного сеансу автентифікації користувача."""

    def __init__(self, ip: str) -> None:
        self.ip = ip
        now = datetime.now(timezone.utc)
        self.login_time: datetime = now
        self.last_activity: datetime = now

    def touch(self) -> None:
        """Оновлює час останньої активності сеансу."""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        """Перевіряє, чи не перевищено таймаут неактивності сесії."""
        if timeout_sec <= 0:
            raise ValueError("Таймаут повинен бути строго позитивним числом.")
        current_time = datetime.now(timezone.utc)
        return (current_time - self.last_activity) <= timedelta(seconds=timeout_sec)


@dataclass(frozen=True)
class AuditRecord:
    """Незмінний запис події безпеки."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Журнал подій аудиту системи."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        """Додає подію до журналу з міткою часу UTC."""
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self._records.append(record)

    def show_all(self) -> None:
        """Виводить всі записи аудиту."""
        print(f"\n{'Timestamp (UTC)':<26} | {'User':<18} | {'Action'}")
        print("-" * 65)
        for r in self._records:
            ts_str = r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{ts_str:<26} | {r.username:<18} | {r.action}")


class UserAccount:
    """Клас керування обліковим записом на основі композиції."""

    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.user = user
        self.session = session
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        """Виконує автентифікацію з оновленням сеансу та аудиту."""
        if self.user.username != username or not self.user.active:
            self.audit_log.add_log(username, "login_failure")
            return False

        if not self.user.check_password(password):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip=ip)
        self.session.touch()
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        """Перевіряє валідність поточної сесії без її пролонгації."""
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        """Завершує активну сесію та фіксує подію в аудиті."""
        username = self.user.username
        self.session = None
        self.audit_log.add_log(username, "logout")

    def __getitem__(self, key: str) -> object:
        """Індексований доступ до дозволених атрибутів."""
        allowed_keys = {
            "user",
            "session",
            "audit_log",
            "username",
            "email",
            "role",
            "active",
        }
        if key not in allowed_keys:
            raise KeyError(f"Доступ до ключа '{key}' заборонено або ключ не існує.")

        if key in {"user", "session", "audit_log"}:
            return getattr(self, key)
        return getattr(self.user, key)

    def __setitem__(self, key: str, value: object) -> None:
        """Індексоване оновлення дозволених атрибутів з контролем типів."""
        if key == "email":
            if not isinstance(value, str):
                raise TypeError("Атрибут email має бути рядком.")
            self.user.email = value
        elif key == "active":
            if not isinstance(value, bool):
                raise TypeError("Атрибут active має бути булевим значенням.")
            self.user.active = value
        elif key in {"user", "session", "audit_log", "username", "role"}:
            raise KeyError(f"Модифікація поля '{key}' через індексатор заблокована.")
        else:
            raise KeyError(f"Невідомий атрибут '{key}'.")
