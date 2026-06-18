import time
import logging

logger = logging.getLogger(__name__)


class Middleware:
    def process_request(self, request):
        return None

    def process_response(self, request, response):
        return response


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
