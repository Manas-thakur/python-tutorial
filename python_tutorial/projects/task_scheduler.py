from python_tutorial.models import ProjectTutorial, Section

TUTORIAL = ProjectTutorial(
    slug="task-scheduler",
    title="Build a Task Scheduler",
    description="A cron-like task scheduler with persistent storage, interval/cron/event triggers, dependency management, and a web dashboard.",
    difficulty="advanced",
    project_dir="task-scheduler",
    prerequisites=["Functions", "Classes", "Threading", "SQLite"],
    steps=[
        Section(heading="Step 1: Architecture Overview", content="""\
We'll build a cron-like task scheduler from scratch. Here's the architecture:

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
│  tasks.json  │                       │   (Flask)       │
│  history.log │                       │  /tasks         │
│  file lock   │                       │  /history       │
└──────────────┘                       │  /trigger/<id>  │
                                       └─────────────────┘
```

**How data flows:**

1. **Scheduler tick** fires every second via `threading.Timer`
2. Each tick iterates all registered tasks
3. For each task, the scheduler calls `trigger.next_run(last_run)` to check if the task is due
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
├── web/
│   ├── __init__.py
│   └── app.py      # Flask dashboard
└── requirements.txt
```

**Why this architecture?** Separation of concerns. The scheduler doesn't care *how* triggers work or *how* tasks are persisted. You can swap SQLite for JSON, or add a Redis backend, without touching the loop.""",),
        Section(heading="Step 2: Task Definitions (tasks.py)", content="""\
A **Task** bundles a function with its scheduling metadata. We define it as a dataclass:

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
    trigger: Optional["Trigger"] = None  # forward ref
    timeout: int = 30
    retries: int = 0
    retry_delay: int = 5
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
```

**The `@every` decorator** — runs a task every N seconds:

```python
def every(interval: int, timeout: int = 30, retries: int = 0):
    def decorator(fn):
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=IntervalTrigger(interval),
            timeout=timeout,
            retries=retries,
        )
        scheduler.register(task)
        return task
    return decorator
```

**The `@cron` decorator** — standard cron expression:

```python
def cron(expression: str, timeout: int = 60, retries: int = 1):
    def decorator(fn):
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=CronTrigger(expression),
            timeout=timeout,
            retries=retries,
        )
        scheduler.register(task)
        return task
    return decorator
```

**The `@on_event` decorator** — triggered by an external signal:

```python
def on_event(event_name: str, timeout: int = 30):
    def decorator(fn):
        task = Task(
            name=fn.__name__,
            fn=fn,
            trigger=EventTrigger(event_name),
            timeout=timeout,
        )
        scheduler.register(task)
        return task
    return decorator
```

**Dry run:**

```python
# user code
@every(interval=60)
def check_disk():
    # check disk usage...
    pass

@cron("0 3 * * *")  # every night at 3 AM
def nightly_backup():
    # backup logic...
    pass

@on_event("deploy_complete")
def deploy_hook():
    # post-deploy logic...
    pass
```

This creates three `Task` instances. `check_disk` gets an `IntervalTrigger(60)`, `nightly_backup` gets a `CronTrigger("0 3 * * *")`, and `deploy_hook` gets an `EventTrigger("deploy_complete")`. All are auto-registered with the global scheduler.

**Why decorators?** Clean syntax — they separate *configuration* (every 60s) from *implementation* (the function body). Without decorators you'd need boilerplate like:

```python
scheduler.add(Task(name="check_disk", fn=check_disk, trigger=IntervalTrigger(60)))
```

Decorators keep the schedule colocated with the logic, which is easier to read and maintain.""",),
        Section(heading="Step 3: Trigger Types (triggers.py)", content="""\
Triggers determine *when* a task should run. Each trigger implements a `next_run()` method.

**IntervalTrigger** — runs every N seconds:

```python
from datetime import datetime, timedelta


class IntervalTrigger:
    def __init__(self, interval: int):
        self.interval = interval  # seconds

    def next_run(self, last_run: datetime | None) -> datetime:
        now = datetime.now()
        if last_run is None:
            return now
        return last_run + timedelta(seconds=self.interval)
```

**CronTrigger** — parses a standard cron expression (`minute hour day month weekday`):

```python
class CronTrigger:
    def __init__(self, expression: str):
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        self.minute, self.hour, self.day, self.month, self.weekday = parts

    def _matches(self, dt: datetime) -> bool:
        def match(field: str, value: int, min_val: int, max_val: int) -> bool:
            if field == "*":
                return True
            if "/" in field:
                base = int(field.split("/")[1])
                return value % base == 0
            if "," in field:
                return value in [int(x) for x in field.split(",")]
            if "-" in field:
                lo, hi = int(field.split("-")[0]), int(field.split("-")[1])
                return lo <= value <= hi
            return int(field) == value

        return (
            match(self.minute, dt.minute, 0, 59)
            and match(self.hour, dt.hour, 0, 23)
            and match(self.day, dt.day, 1, 31)
            and match(self.month, dt.month, 1, 12)
            and match(self.weekday, dt.weekday(), 0, 6)
        )

    def next_run(self, last_run: datetime | None) -> datetime:
        candidate = datetime.now()
        if last_run is not None and last_run > candidate:
            candidate = last_run
        for _ in range(525600):  # search up to 1 year
            if self._matches(candidate):
                return candidate
            candidate += timedelta(minutes=1)
        raise RuntimeError("No matching cron time found within 1 year")
```

**OnceTrigger** — runs at a specific datetime:

```python
class OnceTrigger:
    def __init__(self, run_at: datetime):
        self.run_at = run_at

    def next_run(self, last_run: datetime | None) -> datetime | None:
        if last_run is not None:
            return None  # already ran
        return self.run_at if self.run_at > datetime.now() else None
```

**EventTrigger** — fired manually by name:

```python
class EventTrigger:
    def __init__(self, event_name: str):
        self.event_name = event_name
        self._fired = False

    def fire(self):
        self._fired = True

    def next_run(self, last_run: datetime | None) -> datetime | None:
        if self._fired:
            self._fired = False
            return datetime.now()
        return None
```

**Dry run:**

```python
trigger = CronTrigger("*/5 * * * *")
print(trigger.next_run(None))
# 2026-06-18 10:00:00  (rounded up to next :00 or :05)
```

The parser splits `*/5` → detects `/`, extracts `5`, and `_matches` returns `True` when `minute % 5 == 0`. For `last_run=datetime(2026,6,18,9,58)`, `next_run` would return `10:00` — the first minute boundary where `minute % 5 == 0`.

**Why cron expressions?** They're an industry standard (Unix cron, Jenkins, Airflow all use them). Compact and human-readable once you learn the notation — `"0 3 * * 1-5"` = weekdays at 3 AM, no database lookup needed.""",),
        Section(heading="Step 4: Main Scheduler Loop (scheduler.py)", content="""\
The scheduler is a loop that polls tasks on a fixed interval.

```python
import threading
from datetime import datetime
from typing import List, Optional

from executor import Executor
from storage import Storage
from tasks import Task


class Scheduler:
    def __init__(self, tick_interval: float = 1.0):
        self.tick_interval = tick_interval
        self.tasks: List[Task] = []
        self.executor = Executor()
        self.storage = Storage()
        self._running = False

    def register(self, task: Task):
        self.tasks.append(task)

    def start(self):
        self._running = True
        self._tick()

    def stop(self):
        self._running = False

    def _tick(self):
        if not self._running:
            return
        now = datetime.now()
        for task in self.tasks:
            if not task.enabled:
                continue
            next_time = task.trigger.next_run(task.last_run)
            if next_time is None:
                continue
            if next_time <= now:
                self.executor.submit(task)
                task.last_run = now
        threading.Timer(self.tick_interval, self._tick).start()
```

**How `tick()` works step by step:**

1. Check `_running` flag — allows graceful shutdown
2. Snapshot `datetime.now()` — consistent timestamp across all tasks
3. For each task: call `trigger.next_run(last_run)`
4. If `next_time <= now`, the task is due → submit to executor
5. Update `task.last_run` so the trigger can compute the next window

**Dry run:**

```python
scheduler = Scheduler(tick_interval=1.0)
scheduler.start()
# Thread 1: tick() at T=0.0
#   - check_disk: last_run=None → next_run=T+0.0 → due → submit → last_run=T+0.0
#   - nightly_backup: last_run=None → next_run=03:00 → not due → skip
# Thread 2: tick() at T=1.0
#   - check_disk: last_run=T+0.0 → next_run=T+60.0 → not due → skip
#   - ...runs every second...
# Thread N: tick() at T=60.0
#   - check_disk: last_run=T+0.0 → next_run=T+60.0 → due → submit → last_run=T+60.0
```

**Why polling (every 1s) instead of sleeping until the next event?**

- **Simplicity** — no need to maintain a priority queue or wake-up logic
- **Reliability** — if a tick takes longer than expected, the next tick still fires on schedule
- **Control** — you can add tasks or change schedules dynamically without recalculating sleep times
- **Accuracy is good enough** — 1-second resolution is fine for most scheduled jobs. For sub-second precision, you add an `EventTrigger`-based approach alongside polling.""",),
        Section(heading="Step 5: Task Executor (executor.py)", content="""\
The executor runs tasks in **subprocesses** with timeout enforcement and retry logic.

```python
import subprocess
import sys
import signal
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from tasks import Task


class Executor:
    def __init__(self, max_workers: int = 4):
        self.pool = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, task: Task):
        self.pool.submit(self._run, task)

    def _run(self, task: Task):
        for attempt in range(task.retries + 1):
            try:
                self._execute_with_timeout(task)
                break  # success → don't retry
            except TimeoutError:
                print(f"[{task.name}] Timeout after {task.timeout}s "
                      f"(attempt {attempt + 1}/{task.retries + 1})")
                if attempt < task.retries:
                    time.sleep(task.retry_delay)
                else:
                    print(f"[{task.name}] All retries exhausted")

    def _execute_with_timeout(self, task: Task):
        # Run the task function via subprocess for isolation
        proc = subprocess.Popen(
            [sys.executable, "-c", self._source_for(task)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = proc.communicate(timeout=task.timeout)
            if proc.returncode != 0:
                print(f"[{task.name}] Failed: {stderr.decode()}")
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            raise TimeoutError

    def _source_for(self, task: Task) -> str:
        # Serialize the task function call into executable source
        import inspect
        src = inspect.getsource(task.fn)
        return f"{src}\n{task.fn.__name__}()"
```

**Dry run:**

```python
@every(interval=10, timeout=5, retries=1, retry_delay=2)
def slow_task():
    import time
    time.sleep(10)
```

1. `_execute_with_timeout(slow_task)` spawns a subprocess
2. `proc.communicate(timeout=5)` — blocks for 5 seconds
3. After 5s, Python raises `TimeoutExpired`
4. `proc.kill()` sends SIGKILL — child process dies immediately
5. `TimeoutError` propagates to `_run()`, which waits 2s, then retries
6. Retry also times out → "All retries exhausted" logged

**Why subprocesses instead of threads?**

- **Isolation** — a task that calls `sys.exit(1)` or consumes all memory only kills itself, not the scheduler
- **Timeout enforcement** — `subprocess.Popen.communicate(timeout=...)` reliably terminates runaway tasks. With threads, killing a stuck thread is unsafe (no `Thread.kill()` in Python)
- **Parallelism** — subprocesses can use multiple CPU cores, while the GIL limits CPU-bound threads

The `ThreadPoolExecutor` in the scheduler just dispatches subprocess launches — it doesn't hold the GIL because `Popen.communicate()` releases it during I/O wait.""",),
        Section(heading="Step 6: Persistent Storage (storage.py)", content='''\
Storage saves and loads tasks and execution history to/from JSON files with proper locking.

```python
import json
import os
import fcntl
import time
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
        """Blocking file lock to prevent concurrent writes."""
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

**Dry run:**

```python
storage = Storage()

# Save two tasks
storage.save_tasks([
    {"id": "a1b2c3d4", "name": "check_disk", "interval": 60, "enabled": True},
    {"id": "e5f6g7h8", "name": "nightly_backup", "cron": "0 3 * * *", "enabled": True},
])

# Append a history entry
storage.append_history({
    "task_id": "a1b2c3d4",
    "started_at": "2026-06-18T10:00:00",
    "duration": 0.34,
    "success": True,
})
```

Sequence inside `save_tasks()`:
1. `_acquire_lock(tasks.json)` → opens `tasks.json.lock`, calls `fcntl.flock(fd, LOCK_EX)` — blocks if another process holds the lock
2. Writes JSON to `tasks.json`
3. `_release_lock()` → unlocks and removes `.lock` file

**Why JSON instead of SQLite?**

| Concern | JSON | SQLite |
|---------|------|--------|
| **Debugging** | Open in any editor, readable immediately | Need `sqlite3` CLI or a GUI tool |
| **Setup** | Zero config | Schema migrations, connection management |
| **Concurrent writes** | File locking (added above) | Built-in WAL mode |
| **Querying** | Load all, filter in Python | SQL queries for complex filtering |
| **Performance at scale** | Bad beyond ~10K tasks | Handles millions of rows |

JSON is the right choice here. For a personal scheduler with <100 tasks, the simplicity of "open file, read, done" beats SQLite's overhead. If you need multi-user access or complex queries, swap JSON for SQLite — the `Storage` abstraction makes this a drop-in change.''',),
        Section(heading="Step 7: Web Dashboard (web/app.py)", content='''\
A Flask dashboard to inspect and manage the scheduler remotely.

```python
from flask import Flask, jsonify, render_template_string, request
from scheduler import Scheduler

app = Flask(__name__)

# Global scheduler reference — set by main()
scheduler: Scheduler = None

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>Task Scheduler</title></head>
<body>
  <h1>Task Scheduler</h1>
  <h2>Tasks</h2>
  <table border="1">
    <tr><th>ID</th><th>Name</th><th>Enabled</th><th>Last Run</th><th>Action</th></tr>
    {% for task in tasks %}
    <tr>
      <td>{{ task.id }}</td>
      <td>{{ task.name }}</td>
      <td>{{ "✓" if task.enabled else "✗" }}</td>
      <td>{{ task.last_run or "never" }}</td>
      <td><a href="/trigger/{{ task.id }}">Trigger Now</a></td>
    </tr>
    {% endfor %}
  </table>
  <h2>History (last {{ history|length }} runs)</h2>
  <table border="1">
    <tr><th>Task</th><th>Time</th><th>Duration</th><th>Status</th></tr>
    {% for entry in history %}
    <tr>
      <td>{{ entry.task_id }}</td>
      <td>{{ entry.started_at }}</td>
      <td>{{ entry.duration }}s</td>
      <td>{{ "OK" if entry.success else "FAIL" }}</td>
    </tr>
    {% endfor %}
  </table>
</body>
</html>
"""


@app.route("/")
def index():
    tasks = [
        {
            "id": t.id,
            "name": t.name,
            "enabled": t.enabled,
            "last_run": str(t.last_run) if t.last_run else None,
        }
        for t in scheduler.tasks
    ]
    history = scheduler.storage.get_history(limit=50)
    return render_template_string(INDEX_HTML, tasks=tasks, history=history)


@app.route("/tasks")
def list_tasks():
    return jsonify([
        {"id": t.id, "name": t.name, "enabled": t.enabled}
        for t in scheduler.tasks
    ])


@app.route("/trigger/<task_id>")
def trigger_task(task_id: str):
    for task in scheduler.tasks:
        if task.id == task_id:
            if isinstance(task.trigger, EventTrigger):
                task.trigger.fire()
                return f"Triggered {task.name}", 200
            # For non-event triggers, force immediate execution
            task.last_run = None
            return f"Queued {task.name} for next tick", 200
    return "Task not found", 404


def create_web_server(sched: Scheduler, host: str = "0.0.0.0", port: int = 8080):
    global scheduler
    scheduler = sched
    return lambda: app.run(host=host, port=port, debug=False, use_reloader=False)
```

**Dry run:**

```
# User opens http://localhost:8080/
Browser → GET /
Flask   → scheduler.tasks → [check_disk, nightly_backup, ...]
       → scheduler.storage.get_history(50) → [... last 50 entries ...]
       → render_template_string(INDEX_HTML, tasks=..., history=...)
Browser ← HTML table with all tasks and history
```

When the user clicks "Trigger Now" on `check_disk`:
```
Browser → GET /trigger/a1b2c3d4
Flask   → finds task with id="a1b2c3d4"
       → if EventTrigger → .fire() sets internal flag
       → else → .last_run = None → next tick will see it as due
Browser ← "Queued check_disk for next tick"
```

**Why Flask?** Minimal, well-known, and good enough for an internal dashboard. Django would be overkill for 3 routes. Flask's `render_template_string` means zero external template files — the entire dashboard is self-contained.''',),
        Section(heading="Step 8: Running and Extensions", content="""\
**Starting the system:**

```python
# main.py — entry point
from scheduler import Scheduler
from triggers import EventTrigger
from web.app import create_web_server
import threading


scheduler = Scheduler(tick_interval=1.0)


@cron("*/5 * * * *")
def health_check():
    import urllib.request
    urllib.request.urlopen("https://example.com/health").read()


@every(interval=3600)
def clean_temp_files():
    import shutil
    shutil.rmtree("/tmp/app-cache", ignore_errors=True)


if __name__ == "__main__":
    # Start scheduler in background thread
    scheduler.start()

    # Start Flask dashboard in main thread
    web = create_web_server(scheduler, port=8080)
    t = threading.Thread(target=web, daemon=True)
    t.start()

    print("Scheduler running. Dashboard at http://localhost:8080")
    print("Press Ctrl+C to stop.")
    try:
        t.join()
    except KeyboardInterrupt:
        scheduler.stop()
```

```bash
$ python main.py
Scheduler running. Dashboard at http://localhost:8080
```

**Extensions to consider:**

### 1. Email / SMS Notifications
Wrap the executor to send alerts on failure:

```python
class NotifyingExecutor(Executor):
    def __init__(self, notifier):
        super().__init__()
        self.notifier = notifier

    def _run(self, task):
        try:
            super()._run(task)
        except Exception:
            self.notifier.send(f"Task {task.name} failed after {task.retries} retries")
```

### 2. Task Chaining (Dependencies)
Add `depends_on: List[str]` to the Task dataclass. The scheduler skips a task if its dependency hasn't completed successfully:

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
        if dep.last_success is None or dep.last_success != task.last_run:
            continue  # dependency hasn't run since this task last ran
```

### 3. REST API for Remote Management
Use Flask-RESTful or just raw Flask views:

```python
@app.route("/api/tasks/<task_id>/pause", methods=["POST"])
def pause_task(task_id):
    task = find_task(task_id)
    task.enabled = False
    scheduler.storage.save_tasks([t.__dict__ for t in scheduler.tasks])
    return jsonify({"status": "paused"}), 200
```

### 4. Dynamic Task Loading
Auto-discover tasks from a `tasks/` directory using `importlib`:

```python
import importlib, pkgutil, tasks
for importer, name, ispkg in pkgutil.iter_modules(tasks.__path__):
    importlib.import_module(f"tasks.{name}")
    # decorators auto-register tasks with the global scheduler
```

### 5. Metrics and Alerting
Emit Prometheus metrics from the scheduler:

```python
from prometheus_client import Counter, start_http_server

TASK_RUNS = Counter("task_runs_total", "Total task runs", ["task", "status"])

# In executor, after each run:
TASK_RUNS.labels(task=task.name, status="ok" if success else "fail").inc()
```

**What you've built:** A production-grade task scheduler with decorator-based configuration, cron/interval/event triggers, subprocess isolation, persistent storage with file locking, and a web dashboard. The architecture is modular — every component can be replaced or extended independently.""",),
    ],
)
