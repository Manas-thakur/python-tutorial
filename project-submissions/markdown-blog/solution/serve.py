import os
import sys
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from build import build_site

reload_event = threading.Event()


class LiveReloadHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="_site", **kwargs)

    def do_GET(self):
        if self.path == "/_reload":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            while True:
                if reload_event.wait(timeout=1):
                    try:
                        self.wfile.write(b"data: reload\n\n")
                        self.wfile.flush()
                    except BrokenPipeError:
                        break
                    reload_event.clear()
                else:
                    try:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                    except BrokenPipeError:
                        break
            return

        if self.path.endswith(".html") or self.path == "/" or self.path.endswith("/"):
            path = self.translate_path(self.path)
            if os.path.isdir(path):
                path = os.path.join(path, "index.html")
            if os.path.isfile(path):
                try:
                    with open(path, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()

                    sse_script = (
                        b"<script>\n"
                        b"  (function() {\n"
                        b'    var evtSource = new EventSource("/_reload");\n'
                        b"    evtSource.onmessage = function() { location.reload(); };\n"
                        b"  })();\n"
                        b"</script>\n</body>"
                    )
                    content = content.replace(b"</body>", sse_script)
                    self.wfile.write(content)
                    return
                except IOError:
                    pass

        super().do_GET()


def watch_files(content_dir="content", theme_dir="themes/default"):
    last_mtimes = {}

    watched_dirs = [content_dir]
    theme_path = Path(theme_dir)
    if theme_path.exists():
        watched_dirs.append(str(theme_path))

    while True:
        for directory in watched_dirs:
            if not os.path.exists(directory):
                continue
            for root, _, files in os.walk(directory):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        mtime = os.path.getmtime(fpath)
                    except OSError:
                        continue
                    if fpath in last_mtimes and last_mtimes[fpath] != mtime:
                        print(f"  Change detected: {fpath}")
                        build_site(
                            content_dir=content_dir,
                            theme_dir=theme_dir,
                        )
                        reload_event.set()
                        break
                    last_mtimes[fpath] = mtime
        time.sleep(1)


def serve(port=8000, content_dir="content", theme_dir="themes/default"):
    if not os.path.exists("_site"):
        print("Building site for the first time...")
        build_site(content_dir=content_dir, theme_dir=theme_dir)

    watcher = threading.Thread(
        target=watch_files,
        args=(content_dir, theme_dir),
        daemon=True,
    )
    watcher.start()

    server = HTTPServer(("0.0.0.0", port), LiveReloadHandler)
    print(f"Serving at http://localhost:{port}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    serve(port=port)
