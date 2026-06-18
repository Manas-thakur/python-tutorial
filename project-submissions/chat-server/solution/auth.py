import hashlib
import json
import os
from pathlib import Path

USERS_FILE = Path("users.json")


def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text())
    return {}


def _save_users(users: dict) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2))


def register(username: str, password: str) -> str | None:
    users = _load_users()
    if username in users:
        return "Username already taken"
    salt = os.urandom(16).hex()
    users[username] = {
        "salt": salt,
        "hash": _hash(password, salt),
    }
    _save_users(users)
    return None


def login(username: str, password: str) -> str | None:
    users = _load_users()
    if username not in users:
        return "User not found"
    record = users[username]
    if _hash(password, record["salt"]) != record["hash"]:
        return "Invalid password"
    return None
