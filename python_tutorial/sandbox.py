import subprocess
import sys
import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from .themes import TokyoNightStyle

# Maximum output characters from a sandboxed run.
_MAX_OUTPUT = 100_000

console = Console()

# Commands blocked in the sandbox with explanations for each.
_BLOCKED_REASONS: dict[str, str] = {
    "open": "File access is not allowed (use print() for output)",
    "os.system": "Running shell commands is not allowed",
    "os.popen": "Running shell commands is not allowed",
    "os.remove": "File deletion is not allowed",
    "os.unlink": "File deletion is not allowed",
    "os.rmdir": "Directory removal is not allowed",
    "os.chmod": "Changing file permissions is not allowed",
    "os.chown": "Changing file ownership is not allowed",
    "subprocess.run": "Running subprocesses is not allowed",
    "subprocess.Popen": "Running subprocesses is not allowed",
    "subprocess.call": "Running subprocesses is not allowed",
    "subprocess.check_output": "Running subprocesses is not allowed",
    "subprocess.check_call": "Running subprocesses is not allowed",
    "shutil.rmtree": "Destructive filesystem operations are not allowed",
    "shutil.move": "Filesystem modification is not allowed",
    "shutil.copy": "Writing files is not allowed",
    "shutil.copytree": "Writing files is not allowed",
    "ctypes.CDLL": "Loading native libraries is not allowed",
    "ctypes.WinDLL": "Loading native libraries is not allowed",
    "ctypes.PyDLL": "Loading native libraries is not allowed",
    "socket.connect": "Network connections are not allowed",
    "socket.connect_ex": "Network connections are not allowed",
    "socket.send": "Network access is not allowed",
    "socket.sendall": "Network access is not allowed",
    "socket.sendto": "Network access is not allowed",
    "socket.bind": "Network server sockets are not allowed",
    "socket.listen": "Network server sockets are not allowed",
    "socket.accept": "Network server sockets are not allowed",
    "Path.write_text": "Writing files is not allowed",
    "Path.write_bytes": "Writing files is not allowed",
    "Path.unlink": "File deletion is not allowed",
    "Path.rmdir": "Directory removal is not allowed",
    "Path.chmod": "Changing file permissions is not allowed",
    "exec": "Dynamic code execution is blocked",
    "eval": "Dynamic code evaluation is blocked",
    "breakpoint": "Debugger access is not allowed",
}

# Prologue injected before user code in the sandbox subprocess.
# It lets all imports through but replaces dangerous functions with
# wrappers that raise RuntimeError with the reason from _BLOCKED_REASONS.
_SANDBOX_PROLOGUE = """
import builtins
import os, subprocess, shutil, ctypes, socket
from pathlib import Path

_blocked_reasons = {
"""
for _name, _reason in _BLOCKED_REASONS.items():
    _SANDBOX_PROLOGUE += f"    {_name!r}: {_reason!r},\n"
_SANDBOX_PROLOGUE += """}

def _block(name, _reasons=_blocked_reasons):
    def _blocked(*args, **kwargs):
        raise RuntimeError(f"`{name}()` blocked: " + _reasons[name])
    _blocked.__name__ = name.split('.')[-1]
    return _blocked

builtins.open = _block("open")
builtins.exec = _block("exec")
builtins.eval = _block("eval")
builtins.breakpoint = _block("breakpoint")

for _attr in ["system", "popen", "remove", "unlink", "rmdir", "chmod", "chown"]:
    if hasattr(os, _attr):
        setattr(os, _attr, _block(f"os.{_attr}"))

for _attr in ["run", "Popen", "call", "check_output", "check_call"]:
    if hasattr(subprocess, _attr):
        setattr(subprocess, _attr, _block(f"subprocess.{_attr}"))

for _attr in ["rmtree", "move", "copy", "copytree"]:
    if hasattr(shutil, _attr):
        setattr(shutil, _attr, _block(f"shutil.{_attr}"))

for _attr in ["CDLL", "WinDLL", "PyDLL"]:
    if hasattr(ctypes, _attr):
        setattr(ctypes, _attr, _block(f"ctypes.{_attr}"))

if hasattr(socket, "socket"):
    for _attr in ["connect", "connect_ex", "send", "sendall", "sendto", "bind", "listen", "accept"]:
        if hasattr(socket.socket, _attr):
            setattr(socket.socket, _attr, _block(f"socket.{_attr}"))

for _attr in ["write_text", "write_bytes", "unlink", "rmdir", "chmod"]:
    if hasattr(Path, _attr):
        setattr(Path, _attr, _block(f"Path.{_attr}"))

del _attr, _block, _blocked_reasons
"""

del _name, _reason


def run_code(code: str, timeout: int = 5) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "script.py"
        template = (
            "import sys, math, random, json, re, collections, itertools, string, datetime, fractions, decimal, statistics, pathlib\n"
            "from typing import List, Dict, Tuple, Optional, Union, Any\n"
            + _SANDBOX_PROLOGUE
            + "\n"
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
                stdin=subprocess.DEVNULL,
            )
            stdout = result.stdout[:_MAX_OUTPUT] if len(result.stdout) > _MAX_OUTPUT else result.stdout
            stderr = result.stderr[:_MAX_OUTPUT] if len(result.stderr) > _MAX_OUTPUT else result.stderr
            return {
                "stdout": stdout,
                "stderr": stderr,
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
    console.print(Panel(
        "[bold yellow]Python Sandbox[/]\n\n"
        "Type Python code and press [bold]Ctrl+D[/] (or type [bold]exit[/]) to return to the tutorial.\n"
        "Your code runs in a safe sandbox. Commands like [bold]open()[/], [bold]os.system()[/], [bold]subprocess.run()[/], "
        "and [bold]socket()[/] are blocked for security.\n"
        "You can import any module freely.",
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
        from rich.prompt import Confirm
        expl = explain_error(result["stderr"], result["stderr"])
        if Confirm.ask("[dim]Explain this error?[/]", default=True):
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
    return run_code(code, timeout=5)
