import re

TOKEN_SPECS = [
    ("KEYWORD", r"\b(def|class|if|elif|else|for|while|return|import|from|try|except|finally|with|as|pass|break|continue|and|or|not|in|is|None|True|False|lambda|yield|async|await|raise|global|nonlocal|del|assert)\b"),
    ("BUILTIN", r"\b(print|len|range|int|str|list|dict|tuple|set|float|bool|open|type|super|isinstance|enumerate|zip|map|filter|sorted|reversed|min|max|sum|any|all|abs|round|hasattr|getattr|setattr|staticmethod|classmethod|property|object)\b"),
    ("STRING", r'""".*?"""|\'\'\'.*?\'\'\'|"[^"\\]*(\\.[^"\\]*)*"|\'[^\'\\]*(\\.[^\'\\]*)*\''),
    ("COMMENT", r"#.*"),
    ("NUMBER", r"\b\d+(\.\d+)?[jJ]?\b"),
    ("FUNCALL", r"\b[a-zA-Z_][a-zA-Z0-9_]*\("),
    ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("WHITESPACE", r"[ \t]+"),
    ("MISMATCH", r"."),
]

TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECS))

TOKEN_COLORS = {
    "KEYWORD": "\033[38;5;198m",
    "BUILTIN": "\033[38;5;141m",
    "STRING": "\033[38;5;78m",
    "COMMENT": "\033[38;5;244m",
    "NUMBER": "\033[38;5;220m",
    "FUNCALL": "\033[38;5;51m",
}

RESET = "\033[0m"


def tokenize(line: str) -> list[tuple[str, str]]:
    # TODO: implement this
    return []


def apply_highlighting(tokens: list[tuple[str, str]]) -> str:
    # TODO: implement this
    return ""
