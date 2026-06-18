import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from router import Router
from request import Request
from response import Response, json_response, error_response
from middleware import MiddlewareChain


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_DELETE(self):
        self._handle("DELETE")

    def do_PATCH(self):
        self._handle("PATCH")

    def do_OPTIONS(self):
        self._handle("OPTIONS")

    def _handle(self, method):
        try:
            request = Request(self)
            handler, params = self.server.app.router.resolve(method, request.path)

            if handler is None:
                response = self.server.app._serve_static(request)
                if response is None:
                    response = error_response("Not Found", status=404)
            else:
                wrapped = self.server.app._wrap_handler(handler, params)
                response = wrapped(request)

            self._send(response)
        except Exception as exc:
            self._send(error_response(f"Internal Server Error: {exc}", status=500))

    def _send(self, response):
        body = response.body
        if isinstance(body, str):
            body = body.encode("utf-8")

        self.send_response(response.status)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


class APIHTTPServer(HTTPServer):
    def __init__(self, server_address, app):
        self.app = app
        super().__init__(server_address, APIHandler)


class App:
    def __init__(self):
        self.router = Router()
        self.middleware = MiddlewareChain()
        self._static_dir = None

    def route(self, path, methods=None):
        if methods is None:
            methods = ["GET"]

        def decorator(handler):
            for method in methods:
                self.router.add_route(method, path, handler)
            return handler

        return decorator

    def use(self, middleware):
        self.middleware.add(middleware)

    def static(self, directory):
        self._static_dir = directory

    def _wrap_handler(self, handler, params):
        def base_handler(request):
            result = handler(request, **params)
            if isinstance(result, Response):
                return result
            if isinstance(result, tuple):
                data, status = result
                return json_response(data, status=status)
            return json_response(result)

        return self.middleware.wrap(base_handler)

    def _serve_static(self, request):
        if self._static_dir is None:
            return None

        rel_path = request.path.lstrip("/")
        file_path = os.path.join(self._static_dir, rel_path)

        if not os.path.isfile(file_path):
            return None

        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".txt": "text/plain; charset=utf-8",
        }
        content_type = mime_types.get(ext, "application/octet-stream")

        with open(file_path, "rb") as f:
            body = f.read()

        return Response(body=body, status=200, headers={"Content-Type": content_type})

    def run(self, host="0.0.0.0", port=8000):
        server = APIHTTPServer((host, port), self)
        print(f" * API Framework serving at http://{host}:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            server.server_close()


def render_template(template_path, **context):
    with open(template_path) as f:
        content = f.read()
    for key, value in context.items():
        content = content.replace("{{ " + key + " }}", str(value))
        content = content.replace("{{" + key + "}}", str(value))
    return content
