import threading
from datetime import datetime
from typing import List, Optional

from executor import Executor
from storage import Storage
from tasks import Task, TaskResult


class Scheduler:
    def __init__(self, tick_interval: float = 1.0, data_dir: str = "data"):
        self.tick_interval = tick_interval
        self.tasks: List[Task] = []
        self.storage = Storage(data_dir)
        self.executor = Executor(storage=self.storage)
        self._running = False
        from tasks import _set_default_scheduler
        _set_default_scheduler(self)

    def register(self, task: Task):
        if task not in self.tasks:
            self.tasks.append(task)

    def start(self):
        self._running = True
        self._tick()
        print(f"Scheduler started (tick every {self.tick_interval}s)")

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return
        now = datetime.now()
        for task in list(self.tasks):
            if not task.enabled:
                continue
            if task.trigger is None:
                continue
            try:
                next_time = task.trigger.next_run(task.last_run, now)
            except Exception:
                continue
            if next_time is None:
                continue
            if next_time <= now:
                self.executor.submit(task)
                task.last_run = now
                try:
                    task.next_run = task.trigger.next_run(now, now)
                except Exception:
                    task.next_run = None
        threading.Timer(self.tick_interval, self._tick).start()

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
