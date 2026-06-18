from datetime import datetime, timedelta
from typing import Optional


class IntervalTrigger:
    def __init__(self, interval: int):
        if interval <= 0:
            raise ValueError("Interval must be positive")
        self.interval = interval

    def next_run(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> Optional[datetime]:
        if now is None:
            now = datetime.now()
        if last_run is None:
            return now
        if last_run > now:
            return last_run
        return last_run + timedelta(seconds=self.interval)


class CronTrigger:
    def __init__(self, expression: str):
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        self.minute, self.hour, self.day, self.month, self.weekday = parts

    def _matches(self, dt: datetime) -> bool:
        def match(field: str, value: int, lo: int, hi: int) -> bool:
            if field == "*":
                return True
            if "/" in field:
                _, step = field.split("/")
                return value % int(step) == 0
            if "," in field:
                return value in [int(x) for x in field.split(",")]
            if "-" in field:
                a, b = field.split("-")
                return int(a) <= value <= int(b)
            return int(field) == value

        return (
            match(self.minute, dt.minute, 0, 59)
            and match(self.hour, dt.hour, 0, 23)
            and match(self.day, dt.day, 1, 31)
            and match(self.month, dt.month, 1, 12)
            and match(self.weekday, dt.weekday(), 0, 6)
        )

    def next_run(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> Optional[datetime]:
        if now is None:
            now = datetime.now()
        now = now.replace(second=0, microsecond=0)
        candidate = now
        if last_run is not None:
            last = last_run.replace(second=0, microsecond=0)
            if last > candidate:
                candidate = last
        for _ in range(525600):
            if self._matches(candidate):
                return candidate
            candidate += timedelta(minutes=1)
        return None


class OnceTrigger:
    def __init__(self, run_at: datetime):
        self.run_at = run_at

    def next_run(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> Optional[datetime]:
        if now is None:
            now = datetime.now()
        if last_run is not None:
            return None
        return self.run_at if self.run_at > now else None


class EventTrigger:
    def __init__(self, event_name: str):
        self.event_name = event_name
        self._fired = False

    def fire(self):
        self._fired = True

    def next_run(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> Optional[datetime]:
        if self._fired:
            self._fired = False
            return datetime.now() if now is None else now
        return None
