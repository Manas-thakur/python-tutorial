---
title: "Build a Task Scheduler"
description: "A cron-like task scheduler with persistent storage, interval/cron/event triggers, subprocess execution, and a web dashboard."
prerequisites:
  - Python
  - Threading
  - SQLite (concepts)
tags:
  - python
  - advanced
  - systems
difficulty: advanced
---

# Build a Task Scheduler

## Introduction

You'll build a production-grade task scheduler from scratch — something that could replace `cron` for personal projects. The scheduler supports multiple trigger types (interval, cron, event), runs tasks in isolated subprocesses with timeout enforcement, persists state to JSON with file locking, and exposes a web dashboard for remote management.

**Architecture:**

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│  Scheduler  │────▶│   Triggers   │────▶│   Executor    │
│   Loop      │     │              │     │ (subprocess)  │
│  (tick())   │     │ IntervalTrigger│   │  with timeout │
│             │     │ CronTrigger   │     │  and retry    │
│             │     │ OnceTrigger   │     │               │
│             │     │ EventTrigger  │     │               │
└──────┬──────┘     └──────────────┘     └───────┬───────┘
       │                                         │
       ▼                                         ▼
┌──────────────┐                       ┌─────────────────┐
│   Storage    │                       │   Web Dashboard │
│  tasks.json  │                       │   (http.server) │
│  history.log │                       │  /api/tasks     │
│  file lock   │                       │  /api/history   │
└──────────────┘                       │  /api/trigger   │
                                       └─────────────────┘
```

**Data flow:**

1. **Scheduler tick** fires every second via `threading.Timer`
2. Each tick iterates all registered tasks
3. For each task, the scheduler calls `trigger.next_run(last_run)` to check if due
4. Due tasks are handed to the **Executor** which runs them in a subprocess
5. The **Executor** captures stdout/stderr, enforces a timeout, and retries on failure
6. Results are written to **Storage** (JSON with file locking)
7. The **Web Dashboard** queries the scheduler and storage to display status

**Project structure:**

```
task-scheduler/
├── scheduler.py    # Main loop — the brain
├── tasks.py        # Task definition + decorators
├── triggers.py     # Trigger types
├── executor.py     # Subprocess runner
├── storage.py      # JSON persistence
└── web/
    ├── __init__.py
    └── dashboard.py  # HTTP dashboard (stdlib only)
```

---

## Setup

```bash
mkdir task-scheduler && cd task-scheduler
# Create the files above (or use the starter template)
python scheduler.py
```

No external dependencies needed — everything uses Python standard library.

---

## Step 1: Task Model (`tasks.py`)

A **Task** bundles a function with its scheduling metadata.

```python
from dataclasses import dataclass, field
from typing import Callable, Optional
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


@dataclass
class TaskResult:
    task_id: str = ""
    success: bool = False
    output: str = ""
    duration: float = 0.0
    error: str = ""
```

We also define three decorators that auto-register tasks with a global scheduler:

```python
_default_scheduler = None


def _set_default_scheduler(scheduler):
    global _default_scheduler
    _default_scheduler = scheduler


def every(interval: int, timeout: int = 30, retries: int = 0):
    def decorator(fn):
        from triggers import IntervalTrigger
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=IntervalTrigger(interval),
            timeout=timeout,
            retries=retries,
        )
        if _default_scheduler:
            _default_scheduler.register(task)
        return task
    return decorator


def cron(expression: str, timeout: int = 60, retries: int = 1):
    def decorator(fn):
        from triggers import CronTrigger
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=CronTrigger(expression),
            timeout=timeout,
            retries=retries,
        )
        if _default_scheduler:
            _default_scheduler.register(task)
        return task
    return decorator


def on_event(event_name: str, timeout: int = 30):
    def decorator(fn):
        from triggers import EventTrigger
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=EventTrigger(event_name),
            timeout=timeout,
        )
        if _default_scheduler:
            _default_scheduler.register(task)
        return task
    return decorator
```

### What makes this tick?

- `uuid.uuid4().hex[:8]` generates short unique IDs (e.g., `a1b2c3d4`)
- The decorators create a `Task` and call `scheduler.register(task)` — colocating the schedule with the function
- Functions remain regular callables; the scheduler stores the `fn` reference for subprocess execution

---

## Step 2: Trigger Types (`triggers.py`)

Triggers determine *when* a task should run. Each implements `next_run(last_run)`.

```python
from datetime import datetime, timedelta


class IntervalTrigger:
    """Run every N seconds."""

    def __init__(self, interval: int):
        self.interval = interval

    def next_run(self, last_run: Optional[datetime]) -> Optional[datetime]:
        now = datetime.now()
        if last_run is None:
            return now
        return last_run + timedelta(seconds=self.interval)
```

```python
class CronTrigger:
    """Parse and match standard cron expressions (min hour dom month dow)."""

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
                return value % int(field.split("/")[1]) == 0
            if "," in field:
                return value in [int(x) for x in field.split(",")]
            if "-" in field:
                a, b = int(field.split("-")[0]), int(field.split("-")[1])
                return a <= value <= b
            return int(field) == value

        return (
            match(self.minute, dt.minute, 0, 59)
            and match(self.hour, dt.hour, 0, 23)
            and match(self.day, dt.day, 1, 31)
            and match(self.month, dt.month, 1, 12)
            and match(self.weekday, dt.weekday(), 0, 6)
        )

    def next_run(self, last_run: Optional[datetime]) -> Optional[datetime]:
        now = datetime.now().replace(second=0, microsecond=0)
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
```

```python
class OnceTrigger:
    """Run once at a specific datetime."""

    def __init__(self, run_at: datetime):
        self.run_at = run_at

    def next_run(self, last_run: Optional[datetime]) -> Optional[datetime]:
        if last_run is not None:
            return None
        return self.run_at if self.run_at > datetime.now() else None


class EventTrigger:
    """Fired manually by name."""

    def __init__(self, event_name: str):
        self.event_name = event_name
        self._fired = False

    def fire(self):
        self._fired = True

    def next_run(self, last_run: Optional[datetime]) -> Optional[datetime]:
        if self._fired:
            self._fired = False
            return datetime.now()
        return None
```

### How `next_run` works in practice

For an `IntervalTrigger(60)`, after a task runs at `T=10:00:00`, `next_run` returns `10:01:00`, then `10:02:00`, etc.

For `CronTrigger("*/5 * * * *")`, the scheduler finds the next minute boundary where `minute % 5 == 0`. If `last_run` was `10:03:00`, it scans forward to `10:05:00`.

For `OnceTrigger`, if the scheduled time has passed and the task hasn't run yet, it fires immediately. After that, `next_run` returns `None` (one-shot).

For `EventTrigger`, it returns `None` until `fire()` is called externally, then returns the current time (fires immediately on next tick).

---

## Step 3: Task Storage (`storage.py`)

Storage persists tasks and execution history to JSON with file locking for safety.

```python
import json
import os
import fcntl
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class Storage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.tasks_file = self.data_dir / "tasks.json"
        self.history_file = self.data_dir / "history.json"

    def _acquire_lock(self, path: Path):
        lock_path = path.with_suffix(".lock")
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd, lock_path

    def _release_lock(self, fd, lock_path: Path):
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        lock_path.unlink(missing_ok=True)

    def save_tasks(self, tasks: List[Dict[str, Any]]):
        fd, lock = self._acquire_lock(self.tasks_file)
        try:
            with open(self.tasks_file, "w") as f:
                json.dump(tasks, f, indent=2, default=str)
        finally:
            self._release_lock(fd, lock)

    def load_tasks(self) -> List[Dict[str, Any]]:
        if not self.tasks_file.exists():
            return []
        fd, lock = self._acquire_lock(self.tasks_file)
        try:
            with open(self.tasks_file) as f:
                return json.load(f)
        finally:
            self._release_lock(fd, lock)

    def append_history(self, entry: Dict[str, Any]):
        with open(self.history_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.history_file.exists():
            return []
        with open(self.history_file) as f:
            lines = f.readlines()
        return [json.loads(line) for line in lines[-limit:]]
```

### Locking sequence

1. `_acquire_lock("data/tasks.json")` → opens `data/tasks.json.lock`, `fcntl.flock(fd, LOCK_EX)` blocks until exclusive lock acquired
2. Write JSON to `tasks.json`
3. `_release_lock` → `LOCK_UN`, close fd, delete `.lock` file

This prevents corruption when the web dashboard and scheduler process both try to write simultaneously.

### Why JSON lines for history?

`append_history` writes one JSON object per line. This is append-only — no locking needed, no rewriting the whole file. `get_history` reads the last N lines.

---

## Step 4: Task Executor (`executor.py`)

The executor runs tasks in **subprocesses** with timeout enforcement and retry with backoff.

```python
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
            except TimeoutError as e:
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
```

### What happens when a task times out?

```python
@every(interval=10, timeout=5, retries=1, retry_delay=2)
def slow_task():
    import time
    time.sleep(10)
```

1. `_execute_with_timeout` spawns a subprocess running `slow_task()`
2. `proc.communicate(timeout=5)` — blocks for 5 seconds
3. After 5s, `TimeoutExpired` is raised
4. `proc.kill()` sends SIGKILL — child dies immediately
5. `proc.wait()` reaps the zombie
6. `TimeoutError` propagates to `_run()`, which sleeps 2s and retries
7. Retry also times out → `"All retries exhausted"` logged to history

### Why subprocesses?

- **Isolation**: A task that segfaults or calls `sys.exit()` only kills itself
- **Timeout**: `subprocess.Popen.communicate(timeout=...)` is the only reliable way to kill runaway Python code
- **Parallelism**: Subprocesses bypass the GIL for CPU-bound work
- `ThreadPoolExecutor` in the scheduler just dispatches subprocess launches — it never holds the GIL during I/O wait

---

## Step 5: Main Scheduler (`scheduler.py`)

The scheduler is a polling loop that checks each task's trigger every second.

```python
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

    def register(self, task: Task):
        if task not in self.tasks:
            self.tasks.append(task)

    def start(self):
        from tasks import _set_default_scheduler
        _set_default_scheduler(self)
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
                next_time = task.trigger.next_run(task.last_run)
            except Exception:
                continue
            if next_time is None:
                continue
            if next_time <= now:
                self.executor.submit(task)
                task.last_run = now
                # Recompute next_run for display
                try:
                    task.next_run = task.trigger.next_run(now)
                except Exception:
                    task.next_run = None
        threading.Timer(self.tick_interval, self._tick).start()
```

### Tick walkthrough

```
T=0.0: tick()
  → check_disk: last_run=None, next_run=now → due → submit → last_run=now
  → nightly_backup: last_run=None, next_run=03:00 → not due → skip
T=1.0: tick()
  → check_disk: last_run=T+0.0, next_run=T+60.0 → not due → skip
  → ... every 1s, all tasks skipped ...
T=60.0: tick()
  → check_disk: last_run=T+0.0, next_run=T+60.0 → due → submit → last_run=T+60.0
```

### Why polling (every 1s)?

- **Simplicity**: No priority queue, no wake-up logic
- **Reliability**: If a tick takes longer than expected, the next tick still fires
- **Dynamic**: Add tasks or change triggers without recalculating sleep times
- **Accuracy**: 1-second resolution is fine for cron-like jobs

---

## Step 6: Web Dashboard (`web/dashboard.py`)

A lightweight HTTP dashboard using only the standard library.

```python
import http.server
import json
import functools
from datetime import datetime
from urllib.parse import urlparse


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Task Scheduler Dashboard</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
  th { background: #f5f5f5; }
  .ok { color: green; } .fail { color: red; }
  button { cursor: pointer; }
  #refresh { margin-bottom: 12px; }
</style>
</head>
<body>
<h1>Task Scheduler</h1>
<button id="refresh" onclick="loadData()">Refresh</button>

<h2>Tasks</h2>
<table id="tasks-table">
  <thead><tr><th>ID</th><th>Name</th><th>Trigger</th><th>Enabled</th><th>Last Run</th><th>Next Run</th><th>Action</th></tr></thead>
  <tbody></tbody>
</table>

<h2>History (last 50 runs)</h2>
<table id="history-table">
  <thead><tr><th>Task</th><th>Time</th><th>Duration</th><th>Status</th><th>Output</th></tr></thead>
  <tbody></tbody>
</table>

<script>
async function loadData() {
  const [tasks, history] = await Promise.all([
    fetch("/api/tasks").then(r => r.json()),
    fetch("/api/history").then(r => r.json()),
  ]);
  const tb = document.querySelector("#tasks-table tbody");
  tb.innerHTML = tasks.map(t => `<tr>
    <td>${t.id}</td>
    <td>${t.name}</td>
    <td>${t.trigger_type || "-"}</td>
    <td>${t.enabled ? "✓" : "✗"}</td>
    <td>${t.last_run || "-"}</td>
    <td>${t.next_run || "-"}</td>
    <td><button onclick="triggerTask('${t.id}')">Trigger Now</button></td>
  </tr>`).join("");

  const hb = document.querySelector("#history-table tbody");
  hb.innerHTML = history.map(h => `<tr>
    <td>${h.task_name || h.task_id}</td>
    <td>${h.started_at || "-"}</td>
    <td>${h.duration || "-"}s</td>
    <td class="${h.success ? "ok" : "fail"}">${h.success ? "OK" : "FAIL"}</td>
    <td>${(h.output || h.error || "-").substring(0, 80)}</td>
  </tr>`).join("");
}

async function triggerTask(id) {
  await fetch("/api/trigger/" + id);
  loadData();
}

loadData();
setInterval(loadData, 5000);
</script>
</body>
</html>
"""


class _DashboardHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, scheduler, *args, **kwargs):
        self._scheduler = scheduler
        super().__init__(*args, **kwargs)

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _html(self, content):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "" or path == "/index.html":
            return self._html(DASHBOARD_HTML)

        if path == "/api/tasks":
            tasks = []
            for t in self._scheduler.tasks:
                trigger_type = type(t.trigger).__name__ if t.trigger else None
                tasks.append({
                    "id": t.id,
                    "name": t.name,
                    "enabled": t.enabled,
                    "timeout": t.timeout,
                    "retries": t.retries,
                    "trigger_type": trigger_type,
                    "last_run": str(t.last_run) if t.last_run else None,
                    "next_run": str(t.next_run) if t.next_run else None,
                })
            return self._json(tasks)

        if path == "/api/history":
            history = self._scheduler.storage.get_history(limit=50)
            return self._json(history)

        if path.startswith("/api/trigger/"):
            task_id = path.split("/api/trigger/")[1]
            for task in self._scheduler.tasks:
                if task.id == task_id:
                    from triggers import EventTrigger
                    if isinstance(task.trigger, EventTrigger):
                        task.trigger.fire()
                        return self._json({"status": "triggered", "task": task.name})
                    task.last_run = None
                    return self._json({"status": "queued", "task": task.name})
            return self._json({"error": "not found"}, 404)

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # quiet


def create_web_server(scheduler, host="0.0.0.0", port=8080):
    handler = functools.partial(_DashboardHandler, scheduler)
    server = http.server.ThreadingHTTPServer((host, port), handler)
    return server
```

---

## Step 7: Running It

Create a `main.py` that wires everything together:

```python
import threading
from scheduler import Scheduler
from tasks import every, cron, on_event
from web.dashboard import create_web_server


scheduler = Scheduler(tick_interval=1.0)


@cron("*/5 * * * *")
def health_check():
    import urllib.request
    data = urllib.request.urlopen("https://httpbin.org/get", timeout=10).read()
    print(f"Health check: {len(data)} bytes received")


@every(interval=3600)
def clean_temp():
    import shutil, os, tempfile
    tmp = tempfile.gettempdir()
    print(f"Cleanup would remove files in {tmp}")


@on_event("deploy_complete")
def post_deploy():
    print("Post-deploy hook running...")


if __name__ == "__main__":
    scheduler.start()

    web = create_web_server(scheduler, port=8080)
    t = threading.Thread(target=web.serve_forever, daemon=True)
    t.start()

    print("Scheduler running. Dashboard at http://localhost:8080")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        web.shutdown()
        print("\nShutdown complete.")
```

```bash
$ python main.py
Scheduler running. Dashboard at http://localhost:8080
```

Open `http://localhost:8080` to see all tasks, their status, and execution history. Click "Trigger Now" on any task to force an immediate run.

---

## Step 8: Extensions

### 1. Email/SMS Notifications

Wrap the executor to send alerts on failure:

```python
class NotifyingExecutor(Executor):
    def __init__(self, notifier, **kwargs):
        super().__init__(**kwargs)
        self.notifier = notifier

    def _run(self, task):
        try:
            super()._run(task)
        except Exception:
            self.notifier.send(f"Task {task.name} failed after {task.retries} retries")
```

### 2. Task Chaining (Dependencies)

Add `depends_on` to the Task dataclass. The scheduler skips a task if its dependency hasn't completed successfully:

```python
@dataclass
class Task:
    ...
    depends_on: List[str] = field(default_factory=list)
    last_success: Optional[datetime] = None

# In scheduler._tick():
for task in self.tasks:
    if task.depends_on:
        dep = next(t for t in self.tasks if t.id in task.depends_on)
        if dep.last_success is None:
            continue
```

### 3. REST API for Remote Management

Add pause/resume/delete endpoints to the web dashboard:

```python
@app.route("/api/tasks/<task_id>/pause", methods=["POST"])
def pause_task(task_id):
    task = find_task(task_id)
    task.enabled = False
    return jsonify({"status": "paused"})
```

### 4. Dynamic Task Loading

Auto-discover tasks from a `tasks/` directory:

```python
import importlib, pkgutil
for importer, name, ispkg in pkgutil.iter_modules(["tasks"]):
    importlib.import_module(f"tasks.{name}")
    # decorators auto-register tasks with the global scheduler
```

### 5. Metrics and Alerting

Emit Prometheus-style metrics:

```python
from prometheus_client import Counter
TASK_RUNS = Counter("task_runs", "Total runs", ["task", "status"])
# In executor, after each run:
TASK_RUNS.labels(task=task.name, status="ok" if success else "fail").inc()
```

---

## Conclusion

You've built a production-grade task scheduler with:

- **Decorator-based configuration** — `@every(60)`, `@cron("0 3 * * *")`, `@on_event("deploy")`
- **Four trigger types** — interval, cron, once, and event-driven
- **Subprocess isolation** — with timeout enforcement and retry with backoff
- **Persistent storage** — JSON with file locking for safe concurrent access
- **Web dashboard** — built entirely with Python standard library
- **Modular architecture** — every component is independently replaceable

The total code is under 400 lines. The architecture scales from a personal cron replacement to a distributed job scheduler by swapping storage (Redis), adding a message queue (RabbitMQ), or deploying behind a reverse proxy (Nginx).

**Next steps:** Pick one extension from Step 8 and implement it. Start with task chaining — it's the most impactful for real-world workflows.
