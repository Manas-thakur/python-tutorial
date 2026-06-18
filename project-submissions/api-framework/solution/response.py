import json


class Response:
    def __init__(self, body="", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}


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
