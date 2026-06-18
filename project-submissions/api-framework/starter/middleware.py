import time


class Middleware:
    # TODO: Process request before handler. Return Response to short-circuit.
    def process_request(self, request):
        return None

    # TODO: Process response after handler. Can modify and return response.
    def process_response(self, request, response):
        return response


class MiddlewareChain:
    def __init__(self):
        self._middlewares = []

    # TODO: Add a middleware to the chain
    def add(self, middleware):
        pass

    # TODO: Wrap handler with all middlewares (last added runs closest to handler)
    def wrap(self, handler):
        pass


class LoggerMiddleware(Middleware):
    # TODO: Record start time on request
    def process_request(self, request):
        pass

    # TODO: Log method, path, status, duration
    def process_response(self, request, response):
        pass


class CORSMiddleware(Middleware):
    def __init__(self, origins="*"):
        self.origins = origins

    # TODO: Handle OPTIONS preflight, return 204 with CORS headers
    def process_request(self, request):
        pass

    # TODO: Add Access-Control-Allow-Origin to every response
    def process_response(self, request, response):
        pass


class AuthMiddleware(Middleware):
    def __init__(self, token_validator=None):
        self.token_validator = token_validator or (lambda t: t == "secret")

    # TODO: Check Authorization header for Bearer token, return 401 if invalid
    def process_request(self, request):
        pass
