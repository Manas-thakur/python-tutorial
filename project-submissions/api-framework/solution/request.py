import json
from urllib.parse import urlparse, parse_qs


class Request:
    def __init__(self, handler):
        self.method = handler.command
        parsed = urlparse(handler.path)
        self.path = parsed.path
        self.query_string = parsed.query

        raw = parse_qs(parsed.query)
        self.query_params = {
            k: v[0] if len(v) == 1 else v
            for k, v in raw.items()
        }

        self.headers = dict(handler.headers)
        content_length = int(handler.headers.get("Content-Length", 0))
        self.body = handler.rfile.read(content_length) if content_length > 0 else b""
        self.json = self._parse_json()

    def _parse_json(self):
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type and self.body:
            try:
                return json.loads(self.body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None
        return None
