import http.server
import json
import functools
from datetime import datetime
from urllib.parse import urlparse


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Task Scheduler Dashboard</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #fafafa; color: #333; }
  h1 { border-bottom: 2px solid #ddd; padding-bottom: 8px; }
  h2 { margin-top: 28px; }
  table { border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
  th, td { border: 1px solid #e0e0e0; padding: 10px 12px; text-align: left; font-size: 14px; }
  th { background: #f5f5f5; font-weight: 600; }
  tr:hover td { background: #f0f7ff; }
  .ok { color: #2e7d32; font-weight: 600; }
  .fail { color: #c62828; font-weight: 600; }
  .enabled { color: #2e7d32; }
  .disabled { color: #999; }
  button { cursor: pointer; background: #1976d2; color: #fff; border: none; padding: 6px 14px; border-radius: 4px; font-size: 13px; }
  button:hover { background: #1565c0; }
  #refresh { background: #555; margin-bottom: 16px; padding: 8px 20px; font-size: 14px; }
  #status { display: inline-block; margin-left: 12px; color: #666; font-size: 13px; }
  td button { font-size: 12px; padding: 4px 10px; }
</style>
</head>
<body>
<h1>Task Scheduler Dashboard</h1>
<div style="margin-bottom:8px">
  <button id="refresh" onclick="loadData()">Refresh</button>
  <span id="status"></span>
</div>

<h2>Tasks</h2>
<table id="tasks-table">
  <thead><tr><th>ID</th><th>Name</th><th>Trigger</th><th>Enabled</th><th>Last Run</th><th>Next Run</th><th>Action</th></tr></thead>
  <tbody></tbody>
</table>

<h2>History (last 50 runs)</h2>
<table id="history-table">
  <thead><tr><th>Task</th><th>Time</th><th>Duration</th><th>Status</th><th>Output / Error</th></tr></thead>
  <tbody></tbody>
</table>

<script>
async function loadData() {
  const statusEl = document.getElementById("status");
  statusEl.textContent = "Loading...";
  try {
    const [tasks, history] = await Promise.all([
      fetch("/api/tasks").then(r => r.json()),
      fetch("/api/history").then(r => r.json()),
    ]);
    const tb = document.querySelector("#tasks-table tbody");
    tb.innerHTML = tasks.map(t => `<tr>
      <td><code>${t.id}</code></td>
      <td><strong>${t.name}</strong></td>
      <td>${t.trigger_type || "-"}</td>
      <td class="${t.enabled ? "enabled" : "disabled"}">${t.enabled ? "&#10003;" : "&#10007;"}</td>
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
      <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${(h.output || h.error || "").replace(/"/g,"&quot;")}">${((h.output || h.error || "-")).substring(0, 80)}</td>
    </tr>`).join("");
    statusEl.textContent = "Updated " + new Date().toLocaleTimeString();
  } catch (e) {
    statusEl.textContent = "Error loading data";
  }
}

async function triggerTask(id) {
  try {
    await fetch("/api/trigger/" + id);
    loadData();
  } catch (e) {
    alert("Failed to trigger task");
  }
}

loadData();
setInterval(loadData, 5000);
</script>
</body>
</html>"""


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

        if path in ("", "/index.html"):
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
            from triggers import EventTrigger
            for task in self._scheduler.tasks:
                if task.id == task_id:
                    if isinstance(task.trigger, EventTrigger):
                        task.trigger.fire()
                        return self._json({"status": "triggered", "task": task.name})
                    task.last_run = None
                    return self._json({"status": "queued", "task": task.name})
            return self._json({"error": "not found"}, 404)

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def create_web_server(scheduler, host="0.0.0.0", port=8080):
    handler = functools.partial(_DashboardHandler, scheduler)
    server = http.server.ThreadingHTTPServer((host, port), handler)
    return server
