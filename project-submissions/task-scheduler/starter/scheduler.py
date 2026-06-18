# Main Scheduler
# TODO: Load tasks from storage
# TODO: Main loop: check triggers, dispatch ready tasks
# TODO: Run tasks concurrently with ThreadPoolExecutor
# TODO: Handle task timeouts and retries
# TODO: Log all executions
# TODO: Graceful shutdown on SIGINT/SIGTERM

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
        # Set as the default scheduler so @every/@cron decorators register here
        from tasks import _set_default_scheduler
        _set_default_scheduler(self)

    def register(self, task: Task):
        # TODO: add task to self.tasks if not already present
        pass

    def start(self):
        # TODO: start tick loop
        pass

    def stop(self):
        pass

    def _tick(self):
        # TODO: snapshot now, iterate tasks, check triggers with now, submit due tasks to executor
        pass

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        pass
