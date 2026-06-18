import json
import os
import fcntl
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class Storage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.tasks_file = self.data_dir / "tasks.json"
        self.history_file = self.data_dir / "history.json"

    def _acquire_lock(self, path: Path):
        lock_path = path.with_suffix(".lock")
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd, lock_path

    def _release_lock(self, fd, lock_path: Path):
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        lock_path.unlink(missing_ok=True)

    def save_tasks(self, tasks: List[Dict[str, Any]]):
        fd, lock = self._acquire_lock(self.tasks_file)
        try:
            with open(self.tasks_file, "w") as f:
                json.dump(tasks, f, indent=2, default=str)
        finally:
            self._release_lock(fd, lock)

    def load_tasks(self) -> List[Dict[str, Any]]:
        if not self.tasks_file.exists():
            return []
        fd, lock = self._acquire_lock(self.tasks_file)
        try:
            with open(self.tasks_file) as f:
                return json.load(f)
        finally:
            self._release_lock(fd, lock)

    def append_history(self, entry: Dict[str, Any]):
        with open(self.history_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        with open(self.history_file) as f:
            lines = f.readlines()
        return [json.loads(line) for line in lines[-limit:]]
