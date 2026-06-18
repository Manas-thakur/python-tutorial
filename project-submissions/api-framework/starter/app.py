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

    # TODO: Build Request, resolve route, wrap with middleware, send response
    def _handle(self, method):
        pass

    # TODO: Send Response as HTTP (status line, headers, body)
    def _send(self, response):
        pass

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

    # TODO: Decorator that registers route for given methods
    def route(self, path, methods=None):
        pass

    # TODO: Register middleware
    def use(self, middleware):
        pass

    # TODO: Set static file directory
    def static(self, directory):
        pass

    # TODO: Wrap handler with middleware chain, inject params
    def _wrap_handler(self, handler, params):
        pass

    # TODO: Try to serve a static file, return None if not found
    def _serve_static(self, request):
        pass

    # TODO: Start the HTTP server
    def run(self, host="0.0.0.0", port=8000):
        pass


# TODO: Simple template renderer that replaces {{ key }} with values
def render_template(template_path, **context):
    pass
