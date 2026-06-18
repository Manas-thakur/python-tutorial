import subprocess
import sys
import time
import textwrap
import inspect
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

from tasks import Task, TaskResult


class Executor:
    def __init__(self, max_workers: int = 4, storage=None):
        self.pool = ThreadPoolExecutor(max_workers=max_workers)
        self.storage = storage

    def submit(self, task: Task):
        self.pool.submit(self._run, task)

    def _run(self, task: Task):
        for attempt in range(task.retries + 1):
            started = datetime.now()
            try:
                result = self._execute_with_timeout(task)
                duration = (datetime.now() - started).total_seconds()
                entry = {
                    "task_id": task.id,
                    "task_name": task.name,
                    "started_at": str(started),
                    "duration": round(duration, 3),
                    "success": True,
                    "output": result,
                }
                if self.storage:
                    self.storage.append_history(entry)
                return
            except TimeoutError:
                duration = (datetime.now() - started).total_seconds()
                print(f"[{task.name}] Timeout after {task.timeout}s "
                      f"(attempt {attempt + 1}/{task.retries + 1})")
                if attempt < task.retries:
                    time.sleep(task.retry_delay)
                else:
                    entry = {
                        "task_id": task.id,
                        "task_name": task.name,
                        "started_at": str(started),
                        "duration": round(duration, 3),
                        "success": False,
                        "error": f"Timeout after {task.timeout}s, retries exhausted",
                    }
                    if self.storage:
                        self.storage.append_history(entry)
            except Exception as e:
                duration = (datetime.now() - started).total_seconds()
                print(f"[{task.name}] Failed: {e}")
                if attempt < task.retries:
                    time.sleep(task.retry_delay)
                else:
                    entry = {
                        "task_id": task.id,
                        "task_name": task.name,
                        "started_at": str(started),
                        "duration": round(duration, 3),
                        "success": False,
                        "error": str(e),
                    }
                    if self.storage:
                        self.storage.append_history(entry)

    def _execute_with_timeout(self, task: Task) -> str:
        source = self._source_for(task)
        proc = subprocess.Popen(
            [sys.executable, "-c", source],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = proc.communicate(timeout=task.timeout)
            if proc.returncode != 0:
                raise RuntimeError(stderr.decode().strip())
            return stdout.decode().strip()
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise TimeoutError

    def _source_for(self, task: Task) -> str:
        src = inspect.getsource(task.fn)
        src = textwrap.dedent(src)
        return f"{src}\n{task.fn.__name__}()"
