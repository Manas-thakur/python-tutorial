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
