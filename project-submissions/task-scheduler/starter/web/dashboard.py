# Web Dashboard (stdlib http.server)
# TODO: Show list of tasks and their status
# TODO: Show execution history
# TODO: Manually trigger a task
# TODO: Auto-refresh every 5 seconds

import http.server
import json
import functools
from urllib.parse import urlparse


def create_web_server(scheduler, host="0.0.0.0", port=8080):
    # TODO: create ThreadingHTTPServer with _DashboardHandler
    pass


class _DashboardHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, scheduler, *args, **kwargs):
        self._scheduler = scheduler
        super().__init__(*args, **kwargs)

    def do_GET(self):
        # TODO: route /, /api/tasks, /api/history, /api/trigger/<id>
        pass

    def log_message(self, format, *args):
        pass
