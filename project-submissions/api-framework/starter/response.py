import json


class Response:
    def __init__(self, body="", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}


# TODO: Return a Response with JSON-encoded body and Content-Type header
def json_response(data, status=200, headers=None):
    pass


# TODO: Return a Response with HTML body and text/html Content-Type
def html_response(html, status=200, headers=None):
    pass


# TODO: Return a plain text response
def text_response(text, status=200, headers=None):
    pass


# TODO: Return a JSON error response with {"error": message}
def error_response(message, status=400, headers=None):
    pass


# TODO: Return a redirect response with Location header
def redirect(location, status=302, headers=None):
    pass
