import json
import math
from pathlib import Path
from typing import Optional


PROGRESS_FILE = Path.home() / ".python_tutorial_progress.json"


def _xp_for_level(level: int) -> int:
    """XP needed to reach a given level: quadratic scaling."""
    return level * (level + 1) * 25


def _level_from_xp(xp: int) -> tuple[int, int, int]:
    """Return (level, xp_in_current_level, xp_to_next_level)."""
    level = 0
    while True:
        needed = _xp_for_level(level + 1)
        if xp < needed:
            break
        level += 1
    current = xp - _xp_for_level(level)
    next_needed = _xp_for_level(level + 1) - _xp_for_level(level)
    return level, current, next_needed


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
        PROGRESS_FILE.write_text(json.dumps(self.data, indent=2, default=str))

    # ── Topic progress ──

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
            for key, phase_data in self.data.items()
            if isinstance(phase_data, dict) and key.startswith("phase_")
        )

    def is_phase_unlocked(self, phase: int) -> bool:
        """Phase N+1 unlocks when Phase N is 70%+ complete."""
        if phase <= 1:
            return True
        from .content import discover_phases
        phases = discover_phases()
        prev = None
        for p in phases:
            if p.number == phase - 1:
                prev = p
                break
        if not prev or not prev.topics:
            return True
        done, total = self.get_phase_progress(phase - 1, len(prev.topics))
        if total == 0:
            return True
        pct = done / total
        return pct >= 0.7

    # ── XP / Level system ──

    def add_xp(self, amount: int):
        old_level = self.get_level()
        self.data["_xp"] = self.data.get("_xp", 0) + amount
        new_level = self.get_level()
        self._save()
        return new_level > old_level  # True if leveled up

    def get_xp(self) -> int:
        return self.data.get("_xp", 0)

    def get_level(self) -> int:
        return _level_from_xp(self.get_xp())[0]

    def get_level_info(self) -> dict:
        level, current, needed = _level_from_xp(self.get_xp())
        return {
            "level": level,
            "xp_current": current,
            "xp_needed": needed,
            "xp_total": self.get_xp(),
            "progress": current / needed if needed > 0 else 1.0,
        }

    # ── Streak ──

    def add_streak(self):
        today = str(__import__("datetime").date.today())
        streaks = self.data.setdefault("_streaks", [])
        if not streaks or streaks[-1] != today:
            streaks.append(today)
            self._save()

    def get_streak(self) -> int:
        streaks = self.data.get("_streaks", [])
        if not streaks:
            return 0
        today = __import__("datetime").date.today()
        count = 0
        for i in range(len(streaks) - 1, -1, -1):
            expected = (today - __import__("datetime").timedelta(days=len(streaks) - 1 - i)).isoformat()
            if streaks[i] == expected:
                count += 1
            else:
                break
        return count

    # ── Badges ──

    def get_badges(self) -> list[dict]:
        badges = []
        completed = self.get_total_completed()
        level = self.get_level()

        if completed >= 1:
            badges.append({"name": "First Steps", "desc": "Completed first topic"})
        if completed >= 11:
            badges.append({"name": "Fundamentals", "desc": "Completed all Phase 1"})
        if completed >= 19:
            badges.append({"name": "Core Strength", "desc": "Completed Phase 1-2"})
        if completed >= 27:
            badges.append({"name": "OOP Master", "desc": "Completed Phase 1-3"})
        if completed >= 36:
            badges.append({"name": "Pythonista", "desc": "Completed Phase 1-4"})
        if completed >= 43:
            badges.append({"name": "Advanced", "desc": "Completed Phase 1-5"})
        if completed >= 49:
            badges.append({"name": "Engineer", "desc": "Completed Phase 1-6"})
        if completed >= 56:
            badges.append({"name": "AI Ready", "desc": "Completed ALL phases!"})

        if level >= 3:
            badges.append({"name": "Apprentice", "desc": f"Reached level {level}"})
        if level >= 5:
            badges.append({"name": "Code Warrior", "desc": f"Reached level {level}"})
        if level >= 10:
            badges.append({"name": "Python Sage", "desc": f"Reached level {level}"})

        streak = self.get_streak()
        if streak >= 3:
            badges.append({"name": "On Fire", "desc": f"{streak}-day streak"})
        if streak >= 7:
            badges.append({"name": "Unstoppable", "desc": f"{streak}-day streak"})
        if streak >= 30:
            badges.append({"name": "Legendary", "desc": f"{streak}-day streak!"})

        return badges

    # ── Bookmark ──

    def set_bookmark(self, phase: int, topic: int, section_index: int = 0):
        self.data["_bookmark"] = {"phase": phase, "topic": topic, "section": section_index}
        self._save()

    def get_bookmark(self) -> Optional[dict]:
        return self.data.get("_bookmark")

    def clear_bookmark(self):
        self.data.pop("_bookmark", None)
        self._save()

    # ── Challenge tracking ──

    def mark_challenge_done(self, phase: int, topic: int, idx: int = 0):
        key = f"_challenges"
        done = self.data.setdefault(key, {})
        done[f"{phase}.{topic}.{idx}"] = True
        self._save()

    def is_challenge_done(self, phase: int, topic: int, idx: int = 0) -> bool:
        return self.data.get("_challenges", {}).get(f"{phase}.{topic}.{idx}", False)

    # ── Mastery tracking ──

    def record_quiz_attempt(self, phase: int, topic: int, correct: int, total: int):
        """Record a quiz/flashcard session for a topic."""
        key = f"_mastery"
        mastery = self.data.setdefault(key, {})
        topic_key = f"{phase}.{topic}"
        if topic_key not in mastery:
            mastery[topic_key] = {"attempts": [], "last_reviewed": None}
        mastery[topic_key]["attempts"].append({"correct": correct, "total": total})
        mastery[topic_key]["last_reviewed"] = str(__import__("datetime").datetime.now())
        self._save()

    def get_mastery_score(self, phase: int, topic: int) -> float:
        """Return mastery score 0–1 for a topic. Based on success rate and recency."""
        mastery = self.data.get("_mastery", {})
        topic_key = f"{phase}.{topic}"
        if topic_key not in mastery:
            return 0.0  # Not attempted yet

        attempts = mastery[topic_key].get("attempts", [])
        if not attempts:
            return 0.0

        # Success rate (0–1)
        total_correct = sum(a["correct"] for a in attempts)
        total_questions = sum(a["total"] for a in attempts)
        if total_questions == 0:
            return 0.0
        success_rate = total_correct / total_questions

        # Recency factor: decay over time (older reviews count less)
        import datetime
        last_reviewed = mastery[topic_key].get("last_reviewed")
        if last_reviewed:
            try:
                last_date = datetime.datetime.fromisoformat(last_reviewed)
                days_ago = (datetime.datetime.now() - last_date).days
                recency = max(0.3, 1.0 - (days_ago * 0.05))  # Decay ~5% per day, floor at 0.3
            except (ValueError, TypeError):
                recency = 1.0
        else:
            recency = 1.0

        return success_rate * recency

    def get_topic_mastery_level(self, phase: int, topic: int) -> str:
        """Return mastery level: 'weak', 'medium', 'strong', or 'not_attempted'."""
        score = self.get_mastery_score(phase, topic)
        if score == 0.0:  # No mastery attempts recorded
            return "not_attempted"
        elif score >= 0.8:
            return "strong"
        elif score >= 0.5:
            return "medium"
        else:
            return "weak"

    # ── Reset ──

    def reset(self):
        self.data = {}
        self._save()
