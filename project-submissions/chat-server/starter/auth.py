# Authentication
#
# TODO: Store users in JSON file with salted SHA-256 hashed passwords
# TODO: register(username, password) -> None on success, error string on failure
# TODO: login(username, password) -> None on success, error string on failure
# TODO: Generate random salt with os.urandom for each user
# TODO: Never store plaintext passwords

import hashlib
import json
import os
from pathlib import Path

USERS_FILE = Path("users.json")


def register(username: str, password: str) -> str | None:
    pass


def login(username: str, password: str) -> str | None:
    pass
