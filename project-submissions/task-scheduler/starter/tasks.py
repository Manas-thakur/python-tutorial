# Task Definitions
# TODO: Task dataclass: id, name, fn, trigger, timeout, retries
# TODO: TaskResult dataclass: success, output, duration, error
# TODO: @every(interval) decorator -- run every N seconds
# TODO: @cron(expr) decorator -- cron expression support
# TODO: @on_event(event) decorator -- event-driven tasks

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
    # TODO: Create IntervalTrigger, build Task, register with default scheduler
    pass


def cron(expression: str, timeout: int = 60, retries: int = 1, retry_delay: int = 10):
    # TODO: Create CronTrigger, build Task, register with default scheduler
    pass


def on_event(event_name: str, timeout: int = 30):
    # TODO: Create EventTrigger, build Task, register with default scheduler
    pass
