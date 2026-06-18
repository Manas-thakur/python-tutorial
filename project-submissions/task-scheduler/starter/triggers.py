# Trigger Types
# TODO: IntervalTrigger -- run every N seconds
# TODO: CronTrigger -- parse cron expression, compute next run
# TODO: EventTrigger -- fire when an event is signaled
# TODO: OnceTrigger -- run at a specific datetime

from datetime import datetime, timedelta
from typing import Optional


class IntervalTrigger:
    def __init__(self, interval: int):
        self.interval = interval

    def next_run(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> Optional[datetime]:
        pass


class CronTrigger:
    def __init__(self, expression: str):
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        self.minute, self.hour, self.day, self.month, self.weekday = parts

    def _matches(self, dt: datetime) -> bool:
        pass

    def next_run(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> Optional[datetime]:
        pass


class OnceTrigger:
    def __init__(self, run_at: datetime):
        self.run_at = run_at

    def next_run(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> Optional[datetime]:
        pass


class EventTrigger:
    def __init__(self, event_name: str):
        self.event_name = event_name
        self._fired = False

    def fire(self):
        pass

    def next_run(self, last_run: Optional[datetime], now: Optional[datetime] = None) -> Optional[datetime]:
        pass
