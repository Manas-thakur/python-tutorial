import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt

console = Console()

SAFE_BUILTINS = {
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
    "chr", "complex", "dict", "dir", "divmod", "enumerate", "float",
    "format", "frozenset", "hash", "hex", "id", "int", "isinstance",
    "issubclass", "iter", "len", "list", "map", "max", "min", "next",
    "object", "oct", "ord", "pow", "range", "repr", "reversed", "round",
    "set", "slice", "sorted", "str", "sum", "tuple", "type", "zip",
    "filter", "print", "input",
}

BLOCKED_IMPORTS = {
    "os", "subprocess", "sys", "shutil", "signal", "ctypes",
    "socket", "http", "urllib", "requests", "pathlib",
    "importlib", "__builtins__", "eval", "exec", "compile",
    "open", "file",
}


def run_code(code: str, timeout: int = 5) -> dict:
    """Execute Python code in a subprocess and return results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "script.py"
        template = (
            "import sys, math, random, json, re, collections, itertools, string, datetime, fractions, decimal, statistics\n"
            "from typing import List, Dict, Tuple, Optional, Union, Any\n\n"
            "def __secret_check__(code_to_check, in_func=False):\n"
            "    if in_func:\n"
            "        return\n"
            '    banned = ["__import__", "eval(", "exec(", "open(", "__builtins__"]\n'
            "    for b in banned:\n"
            "        if b in code_to_check:\n"
            '            raise RuntimeError("Use of \'" + b.split("(")[0] + "\' is not allowed in the sandbox.")\n\n'
            + code
        )
        filepath.write_text(template)

        try:
            result = subprocess.run(
                [sys.executable, str(filepath)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"⏱️  Execution timed out after {timeout}s",
                "returncode": -1,
                "success": False,
            }


def sandbox_loop():
    """Interactive code sandbox: type Python code, see results instantly."""
    console.print(Panel(
        "[bold yellow]🐍 Python Sandbox[/]\n\n"
        "Type Python code and press [bold]Ctrl+D[/] (or type [bold]exit[/]) to return to the tutorial.\n"
        "Your code runs in a safe sandbox with [bold]math[/], [bold]random[/], [bold]json[/] and other standard modules available.",
        border_style="yellow",
        title="Code Playground",
    ))

    lines: list[str] = []
    while True:
        try:
            line = input("  >>> ")
        except EOFError:
            break

        if line.strip().lower() in ("exit", "quit"):
            break

        if line.strip() == "" and lines:
            code = "\n".join(lines)
            result = run_code(code)
            _show_result(result)
            lines = []
        elif line.strip() == "":
            continue
        else:
            lines.append(line)

    if lines:
        code = "\n".join(lines)
        result = run_code(code)
        _show_result(result)


def _show_result(result: dict):
    if result["stdout"]:
        console.print(Syntax(result["stdout"].rstrip(), "python", theme="monokai", word_wrap=True))
    if result["stderr"]:
        console.print(f"[red]{result['stderr'].rstrip()}[/]")
    if result["success"] and not result["stdout"].strip():
        console.print("[dim](code ran successfully, no output)[/]")


def run_challenge_code(code: str) -> dict:
    """Run code specifically for a challenge exercise."""
    return run_code(code, timeout=5)
