---
title: "Build a Minimal API Framework"
description: "Build a Flask/FastAPI-inspired web API framework from scratch using only Python's standard library — URL routing, middleware, JSON responses, error handling, and a working todo API."
prerequisites:
  - Python 3.10+
  - Functions
  - Classes
  - Decorators
  - HTTP basics (methods, status codes, headers)
tags:
  - python
  - advanced
  - web
---

# Build a Minimal API Framework

Ever wondered how Flask maps URLs to functions? How does your JSON response make it from a Python dict to the network? In this tutorial, you'll build a working API framework — URL router, request/response objects, middleware pipeline, static file server, and all — using **zero external dependencies**. Only Python's standard library: `http.server`, `json`, `re`, and `urllib`.

By the end, you'll write apps like this:

```python
from app import App
from response import json_response

app = App()

@app.route("/hello/{name}")
def hello(request, name):
    return json_response({"message": f"Hello, {name}!"})

app.run()
```

## Setup

Create the project structure:

```bash
mkdir api-framework
cd api-framework
```

You'll create these files:

```text
api-framework/
├── app.py          # Main API class — decorators, request handling, server
├── router.py       # URL pattern matching with path parameters
├── request.py      # HTTP request parser
├── response.py     # HTTP response builder and helpers
├── middleware.py   # Middleware chain and built-in middleware
└── examples/
    ├── todo.py     # Working CRUD todo API
    └── templates/
        └── greeting.html
```

We'll build each module in order, starting from the bottom of the dependency chain.

---

## Step 1: Router (`router.py`)

The router maps HTTP methods + URL paths to handler functions. It supports path parameters like `/users/{id}` that extract values from the URL.

### Route class

A `Route` stores an HTTP method, a URL pattern, and a handler. The pattern is compiled into a regex on initialization:

```python
import re


class Route:
    def __init__(self, method, pattern, handler):
        self.method = method.upper()
        self.pattern = pattern
        self.handler = handler
        self._regex, self._param_names = self._compile(pattern)

    def _compile(self, pattern):
        param_names = []

        def replace_param(match):
            param_names.append(match.group(1))
            return r"(?P<" + match.group(1) + r">[^/]+)"

        regex_str = re.sub(r"\{(\w+)\}", replace_param, pattern)
        regex_str = "^" + regex_str + "$"
        return re.compile(regex_str), param_names

    def matches(self, method, path):
        if self.method != method.upper():
            return None
        m = self._regex.match(path)
        if not m:
            return None
        return {name: m.group(name) for name in self._param_names}
```

`_compile` converts `/users/{id}` into `^/users/(?P<id>[^/]+)$`. Named capture groups let us extract path parameters by name.

`matches` returns a dict of extracted parameters if both method and path match, or `None` otherwise.

### Router class

The `Router` stores all routes and resolves incoming requests:

```python
class Router:
    def __init__(self):
        self._routes = []

    def add_route(self, method, pattern, handler):
        self._routes.append(Route(method, pattern, handler))

    def resolve(self, method, path):
        for route in self._routes:
            params = route.matches(method, path)
            if params is not None:
                return route.handler, params
        return None, None
```

`resolve` iterates through registered routes and returns the first match. If nothing matches, it returns `(None, None)`.

### Try it

```python
from router import Router

router = Router()

def get_user(request, user_id):
    return f"User {user_id}"

router.add_route("GET", "/users/{user_id}", get_user)

h, p = router.resolve("GET", "/users/42")
# h == get_user, p == {"user_id": "42"}

h, p = router.resolve("POST", "/users/42")
# h == None, p == None (wrong method)
```

---

## Step 2: Request & Response (`request.py` / `response.py`)

Every handler receives a `Request` object and returns a `Response`. These classes encapsulate HTTP parsing and serialization so handlers never touch raw bytes.

### Request

Our `http.server`-based `APIHandler` receives incoming connections. The `Request` object reads from the handler and presents a clean attribute-based interface:

```python
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
```

A POST with `{"title": "Buy milk"}` gives you:

```python
request.method        # "POST"
request.path          # "/todos"
request.headers       # {"Content-Type": "application/json", ...}
request.json          # {"title": "Buy milk"}
request.query_params  # {}
```

### Response

`Response` bundles a status code, headers, and body:

```python
class Response:
    def __init__(self, body="", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}
```

### Helper functions

Helpers reduce boilerplate and enforce consistency:

```python
import json


def json_response(data, status=200, headers=None):
    merged = {"Content-Type": "application/json"}
    if headers:
        merged.update(headers)
    return Response(body=json.dumps(data), status=status, headers=merged)


def html_response(html, status=200, headers=None):
    merged = {"Content-Type": "text/html; charset=utf-8"}
    if headers:
        merged.update(headers)
    return Response(body=html, status=status, headers=merged)


def text_response(text, status=200, headers=None):
    merged = {"Content-Type": "text/plain; charset=utf-8"}
    if headers:
        merged.update(headers)
    return Response(body=text, status=status, headers=merged)


def error_response(message, status=400, headers=None):
    return json_response({"error": message}, status=status, headers=headers)


def redirect(location, status=302, headers=None):
    merged = {"Location": location}
    if headers:
        merged.update(headers)
    return Response(body="", status=status, headers=merged)
```

Without helpers:

```python
body = json.dumps({"hello": "world"})
resp = Response(body=body, status=201, headers={"Content-Type": "application/json"})
```

With `json_response`:

```python
resp = json_response({"hello": "world"}, status=201)
```

---

## Step 3: Application Class (`app.py`)

The `App` class is the public API. It ties the router, middleware chain, and HTTP server together.

### Server integration with `http.server`

We subclass `HTTPServer` to carry a reference to our `App`, and create a handler that dispatches every HTTP method:

```python
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
```

Every HTTP method maps to `_handle`, which creates a `Request`, resolves the route, wraps the handler with middleware, and sends the response. Exceptions are caught and returned as 500 errors.

### The App class

```python
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
```

Key design decisions:

- **`route()`** is a decorator factory. `@app.route("/path", methods=["GET", "POST"])` registers the handler for each method. Default is `["GET"]`.
- **`_wrap_handler()`** injects path parameters (``**params``) into the handler call and auto-converts dict/tuple returns into `json_response`. This is why handlers can just `return {"key": "value"}`.
- **`_serve_static()`** checks the static directory when no route matches. This lets you serve CSS, JS, and images during development.
- **`run()`** starts the `http.server` event loop with graceful keyboard interrupt handling.

### Auto-conversion in action

```python
@app.route("/hello/{name}")
def hello(request, name):
    return {"message": f"Hello, {name}!"}
```

`_wrap_handler` sees the returned dict, wraps it in `json_response()`, and passes it through the middleware chain. The handler never imports `response`.

---

## Step 4: Middleware (`middleware.py`)

Middleware intercepts the request before it reaches the handler and the response after. This pattern handles cross-cutting concerns like logging, CORS, authentication, and rate limiting without touching handler code.

### Middleware base class

```python
class Middleware:
    def process_request(self, request):
        return None

    def process_response(self, request, response):
        return response
```

- `process_request` runs **before** the handler. Return a `Response` to short-circuit (e.g., reject an unauthenticated request). Return `None` to continue.
- `process_response` runs **after** the handler. It receives both the original request and the response, and can modify the response before it's sent.

### MiddlewareChain

The chain composes middleware so each one wraps the next, building an onion-like pipeline:

```python
class MiddlewareChain:
    def __init__(self):
        self._middlewares = []

    def add(self, middleware):
        self._middlewares.append(middleware)

    def wrap(self, handler):
        wrapped = handler
        for mw in reversed(self._middlewares):

            def make_wrapper(mw, inner):
                def wrapper(request):
                    response = mw.process_request(request)
                    if response is not None:
                        return response
                    response = inner(request)
                    return mw.process_response(request, response)

                return wrapper

            wrapped = make_wrapper(mw, wrapped)
        return wrapped
```

Middlewares are applied **inside-out**: the last middleware added wraps closest to the handler, so `process_request` runs last-added-first, and `process_response` runs first-added-last.

### Built-in middleware

```python
import time
import logging

logger = logging.getLogger(__name__)


class LoggerMiddleware(Middleware):
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        duration = time.time() - request._start_time
        logger.info(
            "%s %s -> %d (%.3fs)",
            request.method,
            request.path,
            response.status,
            duration,
        )
        return response


class CORSMiddleware(Middleware):
    def __init__(self, origins="*"):
        self.origins = origins

    def process_request(self, request):
        if request.method == "OPTIONS":
            from response import Response

            resp = Response(status=204)
            resp.headers["Access-Control-Allow-Origin"] = self.origins
            resp.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            )
            resp.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization"
            )
            resp.headers["Access-Control-Max-Age"] = "86400"
            return resp
        return None

    def process_response(self, request, response):
        response.headers["Access-Control-Allow-Origin"] = self.origins
        return response


class AuthMiddleware(Middleware):
    def __init__(self, token_validator=None):
        self.token_validator = token_validator or (lambda t: t == "secret")

    def process_request(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            from response import error_response

            return error_response("Missing or invalid Authorization header", status=401)
        token = auth[7:]
        if not self.token_validator(token):
            from response import error_response

            return error_response("Invalid token", status=401)
        return None
```

### Pipeline in action

For a `GET /api/todos` request with an `Authorization: Bearer secret` header:

1. **LoggerMiddleware** records `request._start_time`
2. **AuthMiddleware** checks the token — valid → continues
3. **Handler runs** → returns `json_response({"todos": [...]})`
4. **CORSMiddleware** adds `Access-Control-Allow-Origin: *`
5. **LoggerMiddleware** logs the duration

If the token is missing, the `AuthMiddleware` short-circuits at step 2 and the handler never runs.

---

## Step 5: JSON & Error Handling

### JSON everywhere

Three conventions make the framework JSON-first:

1. **Auto-conversion** — `App._wrap_handler` converts dicts and tuples to `json_response` automatically. Handlers can `return {"key": "val"}` without any import.
2. **Error shape** — Every error response follows `{"error": "message"}` via `error_response()`. This gives clients a predictable format to parse.
3. **Request body** — `request.json` auto-parses JSON for POST/PUT/PATCH. No manual `json.loads()` needed.

### 404 handling

When `router.resolve()` returns `(None, None)`, `_handle` falls through to `_serve_static`. If no static file matches either, it returns:

```python
{"error": "Not Found"}  ← status 404
```

### 500 handling

The entire `_handle` method is wrapped in `try/except`. Any uncaught exception returns:

```python
{"error": "Internal Server Error: <message>"}  ← status 500
```

### CORS middleware

`CORSMiddleware` handles both preflight `OPTIONS` requests (returning 204 with CORS headers) and adds `Access-Control-Allow-Origin` to every response. This makes the framework usable from browser-based frontends.

---

## Step 6: Static Files & Templates

### Static file serving

Call `app.static("public")` to serve files from a directory. When no route matches a request, `_serve_static` looks for the file on disk:

```python
app.static("./public")
# Now GET /style.css serves ./public/style.css
```

A MIME type map ensures correct `Content-Type` headers for HTML, CSS, JS, images, and more.

### Simple template rendering

The `render_template` function does basic variable substitution:

```python
def render_template(template_path, **context):
    with open(template_path) as f:
        content = f.read()
    for key, value in context.items():
        content = content.replace("{{ " + key + " }}", str(value))
        content = content.replace("{{" + key + "}}", str(value))
    return content
```

Usage:

```python
from app import render_template

html = render_template("examples/templates/greeting.html",
    title="Hello", heading="Welcome", message="Hello, World!")
return html_response(html)
```

Template file (`examples/templates/greeting.html`):

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>{{ message }}</p>
</body>
</html>
```

For production apps, swap this with Jinja2 — the `render_template` function signature stays the same.

---

## Step 7: Example App (`examples/todo.py`)

Build a full CRUD todo API to validate the framework works end-to-end:

```python
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import App
from response import json_response, error_response, html_response
from middleware import LoggerMiddleware, CORSMiddleware

app = App()
app.use(LoggerMiddleware())

todos = []
next_id = 1


@app.route("/", methods=["GET"])
def index(request):
    return html_response(
        "<h1>Todo API</h1>"
        "<p>Endpoints:</p>"
        "<ul>"
        "<li>GET /todos — list all todos</li>"
        "<li>POST /todos — create a todo</li>"
        "<li>GET /todos/{id} — get a todo</li>"
        "<li>PUT /todos/{id} — update a todo</li>"
        "<li>DELETE /todos/{id} — delete a todo</li>"
        "</ul>"
    )


@app.route("/todos", methods=["GET"])
def list_todos(request):
    return json_response({"todos": todos})


@app.route("/todos", methods=["POST"])
def create_todo(request):
    global next_id
    if not request.json or "title" not in request.json:
        return error_response("title is required", status=400)
    todo = {
        "id": next_id,
        "title": request.json["title"],
        "completed": request.json.get("completed", False),
    }
    next_id += 1
    todos.append(todo)
    return json_response(todo, status=201)


@app.route("/todos/html", methods=["GET"])
def todos_html(request):
    items = "".join(
        f"<li>{'&#10003;' if t['completed'] else '&#9675;'} {t['title']}</li>"
        for t in todos
    )
    html = (
        "<!DOCTYPE html><html><head><title>Todos</title>"
        "<style>body{font-family:sans-serif;max-width:600px;margin:40px auto}"
        ".completed{color:#999;text-decoration:line-through}</style></head>"
        f"<body><h1>Todos ({len(todos)})</h1><ul>{items}</ul>"
        '<p><a href="/todos">View as JSON</a></p></body></html>'
    )
    return html_response(html)


@app.route("/todos/{id}", methods=["GET"])
def get_todo(request, id):
    todo_id = int(id)
    for todo in todos:
        if todo["id"] == todo_id:
            return json_response(todo)
    return error_response("Todo not found", status=404)


@app.route("/todos/{id}", methods=["PUT"])
def update_todo(request, id):
    todo_id = int(id)
    if not request.json:
        return error_response("Request body is required", status=400)
    for todo in todos:
        if todo["id"] == todo_id:
            todo["title"] = request.json.get("title", todo["title"])
            todo["completed"] = request.json.get("completed", todo["completed"])
            return json_response(todo)
    return error_response("Todo not found", status=404)


@app.route("/todos/{id}", methods=["DELETE"])
def delete_todo(request, id):
    todo_id = int(id)
    for i, todo in enumerate(todos):
        if todo["id"] == todo_id:
            deleted = todos.pop(i)
            return json_response({"deleted": deleted})
    return error_response("Todo not found", status=404)


if __name__ == "__main__":
    app.run()
```

The example demonstrates:

| Concept | Route | |
|---------|-------|-|
| Read | `GET /todos` | List all todos |
| Create | `POST /todos` | JSON body → `request.json` |
| Read one | `GET /todos/{id}` | Path parameter → `int(id)` |
| Update | `PUT /todos/{id}` | JSON body + path param |
| Delete | `DELETE /todos/{id}` | Remove from list |
| HTML | `GET /todos/html` | Same data, rendered as HTML |

---

## Step 8: Running and Extending

### Run the todo API

```bash
cd api-framework/examples
python todo.py
```

In another terminal:

```bash
curl http://localhost:8000/
# <h1>Todo API</h1>...

curl http://localhost:8000/todos
# {"todos": []}

curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Python"}'
# {"id": 1, "title": "Learn Python", "completed": false}

curl http://localhost:8000/todos/1
# {"id": 1, "title": "Learn Python", "completed": false}

curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
# {"id": 1, "title": "Learn Python", "completed": true}

curl -X DELETE http://localhost:8000/todos/1
# {"deleted": {"id": 1, "title": "Learn Python", "completed": true}}

curl http://localhost:8000/todos/999
# {"error": "Todo not found"}

curl http://localhost:8000/todos/html
# <!DOCTYPE html><html>...
```

### Add middleware

```python
from middleware import LoggerMiddleware, CORSMiddleware, AuthMiddleware

app = App()
app.use(LoggerMiddleware())
app.use(CORSMiddleware(origins="http://myapp.com"))
app.use(AuthMiddleware())
```

Every request is now logged, CORS-enabled, and requires a valid Bearer token — without touching a single handler.

### Extension ideas

**Database integration** — Replace the `todos` list with SQLite:

```python
import sqlite3

@app.route("/todos", methods=["GET"])
def list_todos(request):
    db = sqlite3.connect("todos.db")
    todos = db.execute("SELECT * FROM todos").fetchall()
    return json_response({"todos": [dict(t) for t in todos]})
```

**OpenAPI docs** — Auto-generate a spec from registered routes:

```python
@app.route("/openapi.json")
def spec(request):
    return app.generate_openapi_spec()
```

**Request validation** — Add a `validate` decorator that checks `request.json` against a schema:

```python
@app.route("/todos", methods=["POST"])
@validate({"title": str, "completed": bool})
def create_todo(request):
    ...
```

**Threading** — Swap `HTTPServer` for `ThreadingHTTPServer` to handle concurrent requests.

---

## Conclusion

You've built a production-inspired API framework from scratch. Here's what each piece taught you:

| Concept | Where it applied |
|---------|-----------------|
| Regex | URL routing with `{param}` capture groups |
| `http.server` | HTTP request/response lifecycle |
| Decorators | `@app.route("/path")` registration API |
| Middleware pattern | Request/response pipeline with short-circuit |
| HTTP semantics | Status codes, headers, method dispatch |
| Error handling | 404 routing, 400 validation, 500 errors |
| Layered architecture | Separating router, request, response, middleware |

The full framework is ~300 lines of Python with zero dependencies. It's small enough to read in one sitting, but its architecture mirrors Flask (routing + middleware + request/response objects), FastAPI (auto-JSON conversion), and Express.js (middleware pipeline).

**Next challenge**: Add WebSocket support, write tests with `pytest`, or wrap it with `gunicorn` for production deployment.
