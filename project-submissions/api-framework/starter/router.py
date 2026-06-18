import re


class Route:
    def __init__(self, method, pattern, handler):
        self.method = method.upper()
        self.pattern = pattern
        self.handler = handler
        self._regex = None
        self._param_names = []

    # TODO: Compile pattern into regex with named capture groups for {param}
    def _compile(self, pattern):
        pass

    # TODO: Return dict of extracted params if method+path match, else None
    def matches(self, method, path):
        pass


class Router:
    def __init__(self):
        self._routes = []

    # TODO: Add a Route to the internal list
    def add_route(self, method, pattern, handler):
        pass

    # TODO: Iterate routes, return (handler, params) or (None, None)
    def resolve(self, method, path):
        pass
