from dataclasses import dataclass, field
from typing import Callable, Optional, List
from datetime import datetime
import uuid


@dataclass
class Task:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    fn: Optional[Callable] = None
    trigger: Optional["Trigger"] = None
    timeout: int = 30
    retries: int = 0
    retry_delay: int = 5
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    depends_on: List[str] = field(default_factory=list)


@dataclass
class TaskResult:
    task_id: str = ""
    success: bool = False
    output: str = ""
    duration: float = 0.0
    error: str = ""


_default_scheduler = None


def _set_default_scheduler(scheduler):
    global _default_scheduler
    _default_scheduler = scheduler


def every(interval: int, timeout: int = 30, retries: int = 0, retry_delay: int = 5):
    from triggers import IntervalTrigger
    def decorator(fn):
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=IntervalTrigger(interval),
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )
        if _default_scheduler is not None:
            _default_scheduler.register(task)
        return task
    return decorator


def cron(expression: str, timeout: int = 60, retries: int = 1, retry_delay: int = 10):
    from triggers import CronTrigger
    def decorator(fn):
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=CronTrigger(expression),
            timeout=timeout,
            retries=retries,
            retry_delay=retry_delay,
        )
        if _default_scheduler is not None:
            _default_scheduler.register(task)
        return task
    return decorator


def on_event(event_name: str, timeout: int = 30):
    from triggers import EventTrigger
    def decorator(fn):
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=EventTrigger(event_name),
            timeout=timeout,
        )
        if _default_scheduler is not None:
            _default_scheduler.register(task)
        return task
    return decorator
