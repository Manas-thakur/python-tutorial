from python_tutorial.models import ProjectTutorial, Section

TUTORIAL = ProjectTutorial(
    slug="api-framework",
    title="Build an API Framework",
    description="A minimal web API framework inspired by Flask/FastAPI with URL routing, middleware, JSON responses, error handling, and example apps.",
    difficulty="advanced",
    project_dir="api-framework",
    prerequisites=["Functions", "Classes", "Decorators", "HTTP basics"],
    steps=[
        Section(
            heading="Step 1: Architecture Overview",
            content=r'''
## File layout

Our API framework is split into focused modules, each with a single responsibility:

```text
api-framework/
├── framework.py      # App class — the public API (decorators, run())
├── server.py         # WSGI server adapter (wraps App for wsgiref / gunicorn)
├── routing.py        # URL Router with regex-based path matching
├── request.py        # Request object — parses WSGI environ into nice attributes
├── responses.py      # Response helpers (json_response, html_response, error_response)
├── middleware.py     # Middleware chain (logging, CORS, auth, rate limiting)
└── examples/
    ├── hello.py      # Minimal "Hello, World" API
    └── todo_api.py   # Full CRUD todo list with in-memory storage
```

## Request lifecycle

Every incoming HTTP request flows through the same pipeline:

```
HTTP request
    → server.py (parses raw socket / WSGI environ)
    → App.handle (dispatches to router)
    → Router.resolve (matches method + path)
    → middleware chain (request passes through each middleware)
    → handler function (user code)
    → middleware chain (response passes back through each middleware)
    → server.py (sends raw HTTP response)
```

Each layer is decoupled: the server knows nothing about routing, the router knows nothing about middleware, and handlers know nothing about HTTP parsing. This is the same layered architecture used by WSGI frameworks like Flask and Django.

## Why this architecture

Separating concerns into distinct files means each piece is independently testable. You can swap the server adapter (wsgiref → gunicorn → uvicorn) without touching a single route. You can add a new middleware without modifying any handler. The pipeline from request to response is explicit and easy to trace — you always know exactly which code runs and in what order.

## Dry run — what you'll build

A developer writes a simple hello handler:

```python
from framework import App

app = App()

@app.route("/hello/{name}")
def hello(request, name):
    return json_response({"message": f"Hello, {name}!"})

app.run()
```

Running `python examples/hello.py` starts a server on port 8000. A `curl http://localhost:8000/hello/World` returns `{"message": "Hello, World!"}`. The whole framework that makes this possible is what you'll build step by step.
''',
        ),
        Section(
            heading="Step 2: URL Router (routing.py)",
            content=r'''
## The Route class

A route combines an HTTP method, a URL pattern, and a handler function. The pattern supports `{param}` placeholders that get compiled into named regex groups.

```python
import re


class Route:
    def __init__(self, method: str, pattern: str, handler):
        self.method = method.upper()
        self.pattern = pattern
        self.handler = handler
        self._regex, self._param_names = self._compile(pattern)

    def _compile(self, pattern: str):
        param_names = []
        # Replace {name} with named capture groups
        def replace_param(match):
            param_names.append(match.group(1))
            return r"(?P<" + match.group(1) + r">[^/]+)"
        regex_str = re.sub(r"\\{(\w+)\\}", replace_param, pattern)
        regex_str = "^" + regex_str + "$"
        return re.compile(regex_str), param_names

    def matches(self, method: str, path: str):
        if self.method != method.upper():
            return None
        match = self._regex.match(path)
        if not match:
            return None
        return {name: match.group(name) for name in self._param_names}
```

## The Router class

The router stores all registered routes and resolves incoming requests to the correct handler with extracted parameters.

```python
class Router:
    def __init__(self):
        self._routes = []

    def add_route(self, method: str, pattern: str, handler):
        self._routes.append(Route(method, pattern, handler))

    def resolve(self, method: str, path: str):
        for route in self._routes:
            params = route.matches(method, path)
            if params is not None:
                return route.handler, params
        return None, None
```

## Dry run

Register a route and resolve it:

```python
router = Router()

def get_user(request, user_id):
    return f"User {user_id}"

router.add_route("GET", "/users/{user_id}", get_user)

handler, params = router.resolve("GET", "/users/42")
# handler == get_user
# params  == {"user_id": "42"}

handler, params = router.resolve("GET", "/users/42/posts")
# handler == None, params == None  (no match — pattern is anchored)

handler, params = router.resolve("POST", "/users/42")
# handler == None, params == None  (wrong method)
```

## Why regex

Regex-based routing gives us powerful pattern matching for free:

- **Wildcards** — `{name}` captures any single path segment, but you can also write custom regex like `{id:\\d+}` for numeric-only matches
- **Optional segments** — patterns like `/files/{path:.*}` capture the entire remaining path
- **No external dependencies** — Python's `re` module is in the standard library

Frameworks like Django (`urlpatterns`) and Flask (`@app.route`) use the same approach internally. The only difference is that they cache compiled patterns and use more efficient lookup structures for large route tables.
''',
        ),
        Section(
            heading="Step 3: Request Object (request.py)",
            content=r'''
## Parsing the WSGI environ

In WSGI, every HTTP request arrives as a giant dictionary called `environ`. Our `Request` class wraps it into a clean, attribute-based API.

```python
import json
from urllib.parse import parse_qs


class Request:
    def __init__(self, environ: dict):
        self.method = environ["REQUEST_METHOD"].upper()
        self.path = environ["PATH_INFO"]
        self.query_string = environ.get("QUERY_STRING", "")
        self.headers = self._parse_headers(environ)
        self.body = environ["wsgi.input"].read()
        self.json = self._parse_json()

    def _parse_headers(self, environ: dict) -> dict:
        headers = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").title()
                headers[header_name] = value
        # Content-Type and Content-Length don't have HTTP_ prefix
        if "CONTENT_TYPE" in environ:
            headers["Content-Type"] = environ["CONTENT_TYPE"]
        if "CONTENT_LENGTH" in environ:
            headers["Content-Length"] = environ["CONTENT_LENGTH"]
        return headers

    def _parse_json(self):
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type and self.body:
            try:
                return json.loads(self.body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None
        return None

    @property
    def query_params(self) -> dict:
        return parse_qs(self.query_string)

    @property
    def cookies(self) -> dict:
        raw = self.headers.get("Cookie", "")
        pairs = {}
        for item in raw.split(";"):
            if "=" in item:
                key, _, val = item.partition("=")
                pairs[key.strip()] = val.strip()
        return pairs
```

## Dry run

A client sends a POST request:

```bash
curl -X POST http://localhost:8000/api/todos \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer token123" \\
  -d '{"title": "Buy milk"}'
```

The WSGI server builds an `environ` dict. Our constructor parses it:

```python
request = Request(environ)

request.method        # "POST"
request.path          # "/api/todos"
request.headers       # {"Content-Type": "application/json", "Authorization": "Bearer token123"}
request.json          # {"title": "Buy milk"}
request.query_params  # {}  (no query string in this request)
```

## Why a separate Request class

Without it, handlers would need to parse the raw `environ` dict every time — calling `environ["REQUEST_METHOD"]`, reading `wsgi.input`, and manually splitting headers. That's tedious, error-prone, and impossible to unit-test without constructing a full WSGI environ.

The `Request` class:

- **Encapsulates parsing** — all the messy string manipulation lives in one place
- **Is easy to test** — just pass a dict: `Request({"REQUEST_METHOD": "GET", "PATH_INFO": "/", ...})`
- **Can grow** — add `request.cookies`, `request.files`, `request.auth` without touching handlers
- **Is framework-agnostic** — the same class works with wsgiref, gunicorn, and Waitress
''',
        ),
        Section(
            heading="Step 4: Response Helpers (responses.py)",
            content=r'''
## The Response class

Every response needs a status code, headers, and a body. Our `Response` class holds these and converts them to the WSGI-compatible format.

```python
import json


class Response:
    def __init__(self, body="", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}

    def to_wsgi(self):
        """Returns (status_string, list_of_headers, body_bytes) for WSGI."""
        status_codes = {
            200: "200 OK",
            201: "201 Created",
            204: "204 No Content",
            301: "301 Moved Permanently",
            302: "302 Found",
            400: "400 Bad Request",
            401: "401 Unauthorized",
            403: "403 Forbidden",
            404: "404 Not Found",
            405: "405 Method Not Allowed",
            500: "500 Internal Server Error",
        }
        status_str = status_codes.get(self.status, f"{self.status} Unknown")
        headers_list = [(k, v) for k, v in self.headers.items()]
        body_bytes = self.body.encode("utf-8") if isinstance(self.body, str) else self.body
        return status_str, headers_list, [body_bytes]
```

## Helper functions

Helpers eliminate boilerplate and enforce consistent responses across your API.

```python
def json_response(data, status=200, headers=None):
    """Return a JSON-encoded response."""
    merged_headers = {"Content-Type": "application/json"}
    if headers:
        merged_headers.update(headers)
    return Response(body=json.dumps(data), status=status, headers=merged_headers)


def html_response(html, status=200, headers=None):
    """Return an HTML response."""
    merged_headers = {"Content-Type": "text/html; charset=utf-8"}
    if headers:
        merged_headers.update(headers)
    return Response(body=html, status=status, headers=merged_headers)


def error_response(message, status=400, headers=None):
    """Return a JSON error response."""
    return json_response({"error": message}, status=status, headers=headers)


def redirect(location, status=302, headers=None):
    """Return an HTTP redirect response."""
    merged_headers = {"Location": location}
    if headers:
        merged_headers.update(headers)
    return Response(body="", status=status, headers=merged_headers)
```

## Dry run

```python
# Create a 201 JSON response
resp = json_response({"hello": "world"}, status=201)

resp.status                    # 201
resp.headers                   # {"Content-Type": "application/json"}
resp.body                      # '{"hello": "world"}'

# When the server calls resp.to_wsgi():
# ("201 Created", [("Content-Type", "application/json")], [b'{"hello": "world"}'])
```

## Why helper functions

Without helpers, every handler would repeat the same boilerplate:

```python
# Without helpers:
import json
response_body = json.dumps({"hello": "world"})
response = Response(body=response_body, status=201, headers={"Content-Type": "application/json"})

# With json_response:
response = json_response({"hello": "world"}, status=201)
```

Helpers make handlers more readable and ensure every response follows the same format — no accidentally forgetting `Content-Type`, no inconsistent error shapes, no magic status codes scattered through your codebase.
''',
        ),
        Section(
            heading="Step 5: The App Core (framework.py)",
            content=r'''
## The App class

`App` ties everything together: it exposes the decorator API for registering routes, runs the request pipeline, and starts the server.

```python
from routing import Router
from request import Request
from responses import Response, error_response
from middleware import MiddlewareChain
from server import WSGIServer


class App:
    def __init__(self):
        self.router = Router()
        self.middleware = MiddlewareChain()

    def route(self, pattern: str, methods=None):
        """Decorator that registers a route handler.

        Usage:
            @app.route("/hello/{name}")
            def hello(request, name):
                return json_response({"msg": f"Hello {name}"})
        """
        if methods is None:
            methods = ["GET"]

        def decorator(handler):
            for method in methods:
                self.router.add_route(method, pattern, handler)
            return handler

        return decorator

    def use(self, middleware_instance):
        """Register middleware."""
        self.middleware.add(middleware_instance)

    def handle(self, environ, start_response):
        """WSGI application callable.

        This is the heart of the framework — every request flows through here.
        """
        request = Request(environ)

        handler, params = self.router.resolve(request.method, request.path)

        if handler is None:
            response = error_response("Not Found", status=404)
        else:
            # Wrap the handler so middleware can intercept it
            wrapped = self.middleware.wrap(handler, params)
            try:
                response = wrapped(request)
            except Exception as exc:
                response = error_response(f"Internal error: {exc}", status=500)

        status_str, headers, body_parts = response.to_wsgi()
        start_response(status_str, headers)
        return body_parts

    def run(self, host="0.0.0.0", port=8000):
        """Start the development server."""
        server = WSGIServer(self, host=host, port=port)
        print(f"Serving at http://{host}:{port}")
        server.serve()
```

## Dry run

```python
from framework import App
from responses import json_response

app = App()

@app.route("/hello/{name}")
def say_hello(request, name):
    return json_response({"message": f"Hello, {name}!"})

# Internally, when a GET /hello/World arrives:
#   1. request = Request(environ)
#   2. handler, params = router.resolve("GET", "/hello/World")
#      → handler = say_hello, params = {"name": "World"}
#   3. response = say_hello(request, **params)
#      → returns json_response({"message": "Hello, World!"})
#   4. response.to_wsgi() → ("200 OK", [...], [b'{"message":...}'])
```

## Why a decorator API

The `@app.route` decorator is the defining feature of Flask and inspired by it. This design is:

- **Declarative** — you see the URL pattern and handler together on the same lines
- **Minimal boilerplate** — no manual `router.add_route("GET", "/path", handler)` calls after the function definition
- **Familiar** — anyone who has used Flask, FastAPI, or Bottle already knows this pattern
- **Flexible** — the decorator can accept extra options like methods, middlewares, or response models

```python
@app.route("/posts", methods=["GET", "POST"])
@app.route("/posts/{id}", methods=["GET", "PUT", "DELETE"])
```

Both routes register cleanly with the same decorator syntax, and the framework handles dispatching based on method.
''',
        ),
        Section(
            heading="Step 6: Middleware Chain (middleware.py)",
            content=r'''
## Middleware base class

Middleware wraps the handler to add behavior before or after the request is processed.

```python
class Middleware:
    def process_request(self, request):
        """Called before the handler. Return a Response to short-circuit."""
        return None  # None means "continue to handler"

    def process_response(self, request, response):
        """Called after the handler. Can modify the response."""
        return response
```

## The middleware chain

The chain composes middleware so each one wraps the next, building a pipeline.

```python
class MiddlewareChain:
    def __init__(self):
        self._middlewares = []

    def add(self, middleware):
        self._middlewares.append(middleware)

    def wrap(self, handler, params):
        """Build the middleware stack around the handler."""
        # Start with the original handler
        def base_handler(request):
            return handler(request, **params)

        # Wrap from right to left (last middleware runs closest to handler)
        wrapped = base_handler
        for mw in reversed(self._middlewares):
            current = wrapped

            def make_wrapper(mw, inner):
                def wrapper(request):
                    # process_request can short-circuit by returning a Response
                    response = mw.process_request(request)
                    if response is not None:
                        return response
                    response = inner(request)
                    return mw.process_response(request, response)

                return wrapper

            wrapped = make_wrapper(mw, current)

        return wrapped
```

## Built-in middleware examples

```python
import time
import logging

logger = logging.getLogger(__name__)


class LoggerMiddleware(Middleware):
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        duration = time.time() - request._start_time
        logger.info("%s %s -> %d (%.3fs)", request.method, request.path, response.status, duration)
        return response


class CORSMiddleware(Middleware):
    def __init__(self, origins="*"):
        self.origins = origins

    def process_response(self, request, response):
        response.headers["Access-Control-Allow-Origin"] = self.origins
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response


class AuthMiddleware(Middleware):
    def __init__(self, token_validator=None):
        self.token_validator = token_validator or (lambda t: t == "secret")

    def process_request(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            from responses import error_response
            return error_response("Missing or invalid Authorization header", status=401)
        token = auth[7:]
        if not self.token_validator(token):
            from responses import error_response
            return error_response("Invalid token", status=401)
        return None  # continue to handler


class RateLimitMiddleware(Middleware):
    def __init__(self, max_requests=100, window=60):
        self.max_requests = max_requests
        self.window = window
        self._buckets = {}

    def process_request(self, request):
        client_ip = request.headers.get("X-Forwarded-For", "unknown")
        now = time.time()
        # Simple sliding window
        bucket = self._buckets.setdefault(client_ip, [])
        cutoff = now - self.window
        self._buckets[client_ip] = [t for t in bucket if t > cutoff]
        if len(self._buckets[client_ip]) >= self.max_requests:
            from responses import error_response
            return error_response("Rate limit exceeded", status=429)
        self._buckets[client_ip].append(now)
        return None
```

## Dry run — full pipeline

A request to a protected endpoint:

```
GET /api/todos
Authorization: Bearer secret
```

Pipeline execution:

1. **LoggerMiddleware** — records start time, logs the incoming method and path
2. **AuthMiddleware** — checks `Authorization` header → token is valid → continues
3. **Handler runs** — returns `json_response({"todos": [...]})`
4. **CORSMiddleware** — adds `Access-Control-Allow-Origin: *` to response
5. **LoggerMiddleware** — calculates duration, logs `GET /api/todos -> 200 (0.012s)`

## Why middleware

Middleware is the cleanest way to handle cross-cutting concerns:

- **No repetition** — auth logic appears once instead of in every handler
- **Composable** — mix and match middleware per app or per route group
- **Short-circuitable** — auth failure never reaches the handler; rate limit exceeded returns 429 immediately
- **Request/response aware** — middleware has full access to both, unlike decorators that only wrap the handler

Every major framework has this concept: Flask has `before_request`/`after_request`, FastAPI has `@app.middleware`, Django has `MiddlewareMixin`, Express has `app.use()`.
''',
        ),
        Section(
            heading="Step 7: Example Apps (examples/)",
            content=r'''
## hello.py — minimal API

The simplest possible app to validate the framework works end-to-end.

```python
import sys
sys.path.insert(0, "..")

from framework import App
from responses import json_response

app = App()

@app.route("/")
def index(request):
    return json_response({"message": "Welcome to the API Framework!"})

@app.route("/hello/{name}")
def say_hello(request, name):
    return json_response({"greeting": f"Hello, {name}!"})

if __name__ == "__main__":
    app.run()
```

```bash
curl http://localhost:8000/
# {"message": "Welcome to the API Framework!"}

curl http://localhost:8000/hello/World
# {"greeting": "Hello, World!"}
```

## todo_api.py — CRUD with in-memory storage

A realistic example showcasing all four HTTP methods with path parameters, JSON bodies, and error handling.

```python
import sys
sys.path.insert(0, "..")

from framework import App
from responses import json_response, error_response

app = App()

todos = []
next_id = 1

@app.route("/todos", methods=["GET"])
def list_todos(request):
    return json_response({"todos": todos})

@app.route("/todos", methods=["POST"])
def create_todo(request):
    if not request.json or "title" not in request.json:
        return error_response("title is required", status=400)
    global next_id
    todo = {
        "id": next_id,
        "title": request.json["title"],
        "completed": request.json.get("completed", False),
    }
    next_id += 1
    todos.append(todo)
    return json_response(todo, status=201)

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
    global todos
    for i, todo in enumerate(todos):
        if todo["id"] == todo_id:
            deleted = todos.pop(i)
            return json_response({"deleted": deleted})
    return error_response("Todo not found", status=404)

if __name__ == "__main__":
    app.run()
```

## Dry run

```bash
# Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk"}'
# {"id": 1, "title": "Buy milk", "completed": false}  ← 201 Created

# List todos
curl http://localhost:8000/todos
# {"todos": [{"id": 1, "title": "Buy milk", "completed": false}]}

# Get single todo
curl http://localhost:8000/todos/1
# {"id": 1, "title": "Buy milk", "completed": false}

# Update todo
curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
# {"id": 1, "title": "Buy milk", "completed": true}

# Delete todo
curl -X DELETE http://localhost:8000/todos/1
# {"deleted": {"id": 1, "title": "Buy milk", "completed": true}}

# 404 on missing todo
curl http://localhost:8000/todos/999
# {"error": "Todo not found"}  ← 404
```

## Why start with examples

Example apps serve two crucial purposes:

- **Validation** — if the hello example runs and the todo API handles all CRUD operations correctly, the framework is complete and usable
- **Documentation** — examples are the most concrete form of documentation; new users can copy, extend, and experiment with them

The todo API also demonstrates the pattern you'd use with a real database — replace the `todos` list with SQLite queries and the handlers barely change.
''',
        ),
        Section(
            heading="Step 8: Running and Extensions",
            content=r'''
## Running the framework

```bash
# 1. Navigate to the examples directory
cd api-framework/examples

# 2. Start the todo API
python todo_api.py
# Serving at http://0.0.0.0:8000

# 3. Test with curl (from another terminal)
curl http://localhost:8000/todos
# {"todos": []}

curl -X POST http://localhost:8000/todos \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Learn Python"}'
# {"id": 1, "title": "Learn Python", "completed": false}
```

## Adding middleware

```python
from framework import App
from middleware import LoggerMiddleware, CORSMiddleware, AuthMiddleware

app = App()
app.use(LoggerMiddleware())
app.use(CORSMiddleware(origins="http://myfrontend.com"))
app.use(AuthMiddleware())

@app.route("/secure-data")
def secure_data(request):
    return json_response({"secret": "42"})

app.run()
```

Every request is now logged, has CORS headers, and requires a valid Bearer token — without changing a single line in the handler.

## Extension ideas

### ORM integration

Replace the in-memory `todos` list with SQLAlchemy or Peewee:

```python
from models import Todo, db_session

@app.route("/todos", methods=["POST"])
def create_todo(request):
    todo = Todo(title=request.json["title"])
    db_session.add(todo)
    db_session.commit()
    return json_response(todo.to_dict(), status=201)
```

The framework handles routing, parsing, and response formatting — your handlers just interact with the database.

### WebSocket support

Extend the server to handle WebSocket upgrades. The same middleware pipeline can apply to WebSocket connections:

```python
@app.websocket("/chat")
def chat_handler(ws):
    while True:
        msg = ws.receive()
        ws.send(f"Echo: {msg}")
```

### OpenAPI / Swagger documentation

Auto-generate an OpenAPI spec by inspecting registered routes:

```python
@app.route("/openapi.json")
def openapi_spec(request):
    return json_response(app.generate_openapi_spec())
```

Each route's handler could have a `__doc__` string or a `summary` attribute that feeds into the spec.

### Authentication providers

Extend `AuthMiddleware` with JWT verification, OAuth2, API keys, or session cookies:

```python
app.use(AuthMiddleware(provider=JWTAuthProvider(secret="my-secret")))
app.use(AuthMiddleware(provider=APIKeyAuthProvider(keys={"abc123": "user_1"})))
```

### CLI arguments

Use `argparse` to let the user specify host, port, and middleware at startup:

```bash
python examples/todo_api.py --port 9000 --cors-origins "*" --log-level debug
```

## What you've learned

| Concept | Where it applied |
|---------|-----------------|
| Regex pattern compilation | URL routing with `{param}` capture groups |
| WSGI protocol | Request parsing, response formatting |
| Decorators | `@app.route("/path")` registration API |
| Middleware pattern | Request/response pipeline interception |
| HTTP semantics | Status codes, headers, method dispatch |
| Error handling | 404 routing, 400 validation, 500 server errors |
| Layered architecture | Separating server, router, request, response |

## Next steps

- Write tests for each module with `pytest` (mock WSGI environ for request tests)
- Add route grouping / blueprints for organizing large route tables
- Implement static file serving with `app.serve_static("/static", "./public")`
- Add request validation with Pydantic models (like FastAPI)
- Package the framework with `pyproject.toml` and publish to PyPI

The full source code for this tutorial is available in the `api-framework/` project directory.
''',
        ),
    ],
)
