# Persistent Storage
# TODO: Store/load tasks from JSON file
# TODO: Store execution history (append-only JSON lines)
# TODO: Handle concurrent access with file locking (fcntl)
# TODO: Get next scheduled run times

import json
import os
import fcntl
from typing import Dict, Any, List
from pathlib import Path


class Storage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.tasks_file = self.data_dir / "tasks.json"
        self.history_file = self.data_dir / "history.json"

    def _acquire_lock(self, path: Path):
        pass

    def _release_lock(self, fd, lock_path: Path):
        pass

    def save_tasks(self, tasks: List[Dict[str, Any]]):
        pass

    def load_tasks(self) -> List[Dict[str, Any]]:
        pass

    def append_history(self, entry: Dict[str, Any]):
        pass

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        pass
