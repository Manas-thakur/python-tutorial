import subprocess
import sys
import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt

from .themes import TokyoNightStyle

console = Console()

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
        blocked_set = sorted(BLOCKED_IMPORTS)
        template = (
            "import sys, math, random, json, re, collections, itertools, string, datetime, fractions, decimal, statistics\n"
            "from typing import List, Dict, Tuple, Optional, Union, Any\n"
            f"_BLOCKED = {blocked_set!r}\n"
            "_original_import = __builtins__.__import__\n"
            "def _safe_import(name, *args, **kwargs):\n"
            "    if name in _BLOCKED:\n"
            '        raise ImportError(f"Import of {name!r} is not allowed in sandbox")\n'
            "    return _original_import(name, *args, **kwargs)\n"
            "__builtins__.__import__ = _safe_import\n\n"
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
                "stderr": f"Execution timed out after {timeout}s",
                "returncode": -1,
                "success": False,
            }


def sandbox_loop():
    """Interactive code sandbox: type Python code, see results instantly."""
    console.print(Panel(
        "[bold yellow]Python Sandbox[/]\n\n"
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
        console.print(Syntax(result["stdout"].rstrip(), "python", theme=TokyoNightStyle, word_wrap=True))
    if result["stderr"]:
        console.print(f"[red]{result['stderr'].rstrip()}[/]")
        from .explainer import explain_error
        expl = explain_error(result["stderr"], result["stderr"])
        from rich.prompt import Confirm
        if Confirm.ask("[dim]Explain this error?[/]", default=True):
            from rich.panel import Panel
            from rich.markdown import Markdown
            lines = [
                f"[bold yellow]{expl['title']}[/]",
                f"\n{expl['explanation']}",
                f"\n[bold]Common causes:[/]",
            ]
            for c in expl["common_causes"]:
                lines.append(f"  - {c}")
            lines.append(f"\n[bold]How to fix:[/]")
            for f in expl["fixes"]:
                lines.append(f"  - {f}")
            console.print(Panel("\n".join(lines), border_style="yellow", title="[bold]Error Guide[/]"))
    if result["success"] and not result["stdout"].strip():
        console.print("[dim](code ran successfully, no output)[/]")


def run_challenge_code(code: str) -> dict:
    """Run code specifically for a challenge exercise."""
    return run_code(code, timeout=5)
