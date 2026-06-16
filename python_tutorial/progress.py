import json
from pathlib import Path


PROGRESS_FILE = Path.home() / ".python_tutorial_progress.json"


class ProgressTracker:
    def __init__(self):
        self.data: dict = self._load()

    def _load(self) -> dict:
        if PROGRESS_FILE.exists():
            try:
                raw = PROGRESS_FILE.read_text()
                return json.loads(raw) if raw.strip() else {}
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self):
        PROGRESS_FILE.write_text(json.dumps(self.data, indent=2))

    def mark_complete(self, phase: int, topic: int):
        key = f"phase_{phase}"
        if key not in self.data:
            self.data[key] = {}
        self.data[key][str(topic)] = True
        self._save()

    def is_complete(self, phase: int, topic: int) -> bool:
        return self.data.get(f"phase_{phase}", {}).get(str(topic), False)

    def get_phase_progress(self, phase: int, total: int) -> tuple[int, int]:
        completed = sum(
            1 for k in self.data.get(f"phase_{phase}", {}) if self.data[f"phase_{phase}"][k]
        )
        return completed, total

    def get_total_progress(self) -> tuple[int, int]:
        return (
            sum(len(v) for v in self.data.values()),
            sum(
                1
                for phase_data in self.data.values()
                for k, v in phase_data.items()
                if v
            ),
        )

    def reset(self):
        self.data = {}
        self._save()
