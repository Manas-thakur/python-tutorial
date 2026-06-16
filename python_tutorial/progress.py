import json
from pathlib import Path
from typing import Optional


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

    def get_total_completed(self) -> int:
        return sum(
            sum(1 for v in phase_data.values() if v)
            for phase_data in self.data.values()
        )

    def set_bookmark(self, phase: int, topic: int, section_index: int = 0):
        self.data["_bookmark"] = {"phase": phase, "topic": topic, "section": section_index}
        self._save()

    def get_bookmark(self) -> Optional[dict]:
        return self.data.get("_bookmark")

    def clear_bookmark(self):
        self.data.pop("_bookmark", None)
        self._save()

    def add_streak(self):
        import datetime
        today = str(datetime.date.today())
        streaks = self.data.setdefault("_streaks", [])
        if not streaks or streaks[-1] != today:
            streaks.append(today)
            self._save()

    def get_streak(self) -> int:
        import datetime
        streaks = self.data.get("_streaks", [])
        if not streaks:
            return 0
        count = 0
        today = datetime.date.today()
        for i in range(len(streaks) - 1, -1, -1):
            expected = (today - datetime.timedelta(days=len(streaks) - 1 - i)).isoformat()
            if streaks[i] == expected:
                count += 1
            else:
                break
        return count

    def get_badges(self) -> list[dict]:
        badges = []
        completed = self.get_total_completed()

        if completed >= 1:
            badges.append({"name": "First Steps", "icon": "👶", "desc": "Completed first topic"})
        if completed >= 11:
            badges.append({"name": "Fundamentals", "icon": "📘", "desc": "Completed all Phase 1"})
        if completed >= 19:
            badges.append({"name": "Core Strength", "icon": "💪", "desc": "Completed Phase 1-2"})
        if completed >= 27:
            badges.append({"name": "OOP Master", "icon": "🧩", "desc": "Completed Phase 1-3"})
        if completed >= 36:
            badges.append({"name": "Pythonista", "icon": "🐍", "desc": "Completed Phase 1-4"})
        if completed >= 43:
            badges.append({"name": "Advanced", "icon": "⚡", "desc": "Completed Phase 1-5"})
        if completed >= 49:
            badges.append({"name": "Engineer", "icon": "🔧", "desc": "Completed Phase 1-6"})
        if completed >= 56:
            badges.append({"name": "AI Ready", "icon": "🤖", "desc": "Completed ALL phases!"})

        streak = self.get_streak()
        if streak >= 3:
            badges.append({"name": "On Fire", "icon": "🔥", "desc": f"{streak}-day streak"})
        if streak >= 7:
            badges.append({"name": "Unstoppable", "icon": "💎", "desc": f"{streak}-day streak"})

        return badges

    def reset(self):
        self.data = {}
        self._save()
