# Task Executor
# TODO: Run task function in a subprocess via inspect.getsource
# TODO: Enforce timeout (kill if exceeded)
# TODO: Capture stdout/stderr
# TODO: Implement retry logic with backoff
# TODO: Log results to storage history

import subprocess
import sys
import time
import textwrap
import inspect
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from tasks import Task, TaskResult


class Executor:
    def __init__(self, max_workers: int = 4, storage=None):
        self.pool = ThreadPoolExecutor(max_workers=max_workers)
        self.storage = storage

    def submit(self, task: Task):
        pass

    def _run(self, task: Task):
        # TODO: loop with retries, call _execute_with_timeout, log to storage
        pass

    def _execute_with_timeout(self, task: Task) -> str:
        # TODO: spawn subprocess, communicate with timeout, handle TimeoutExpired
        pass

    def _source_for(self, task: Task) -> str:
        # TODO: extract source code of task.fn and return runnable script
        pass
