import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import App
from response import json_response, error_response, html_response
from middleware import LoggerMiddleware

app = App()
app.use(LoggerMiddleware())

todos = []
next_id = 1


# TODO: Register route for GET /
def index(request):
    pass


# TODO: Register route for GET /todos — return list
def list_todos(request):
    pass


# TODO: Register route for POST /todos — create todo from request.json
def create_todo(request):
    pass


# TODO: Register route for GET /todos/{id} — find by id
def get_todo(request, id):
    pass


# TODO: Register route for PUT /todos/{id} — update todo fields
def update_todo(request, id):
    pass


# TODO: Register route for DELETE /todos/{id} — remove from list
def delete_todo(request, id):
    pass


# TODO: Bonus — register route for GET /todos/html — render HTML list
def todos_html(request):
    pass


if __name__ == "__main__":
    app.run()
