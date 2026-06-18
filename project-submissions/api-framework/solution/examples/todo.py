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
