from urllib.parse import parse_qs


class Request:
    def __init__(self, handler):
        # TODO: Extract method from handler.command
        self.method = "GET"
        # TODO: Parse path and query string from handler.path
        self.path = "/"
        self.query_string = ""
        # TODO: Parse query params into dict
        self.query_params = {}
        # TODO: Copy headers from handler.headers
        self.headers = {}
        # TODO: Read request body from handler.rfile
        self.body = b""
        # TODO: Parse JSON body if Content-Type is application/json
        self.json = None

    def _parse_json(self):
        pass
