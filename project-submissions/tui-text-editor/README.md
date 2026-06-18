---
title: Build a TUI Text Editor
author: Python Interactive Tutorial
uid: tui-text-editor
datePublished: 2026-06-18
description: Create a terminal-based text editor from scratch with syntax highlighting, undo/redo, and file operations — all in pure Python.
published: false
readTime: 90
prerequisites: Python
versions: Python 3.10+
tags:
  - intermediate
  - python
---

## Introduction

Ever wondered how text editors like Vim, Nano, or Emacs work under the hood? In this project, we're going to build our own from scratch — a terminal-based text editor with syntax highlighting, undo/redo, and file operations. No frameworks, no external libraries. Just Python and a terminal.

Here's what you'll learn:

- **Gap buffers** — the data structure powering GNU Emacs and many other editors
- **Terminal raw mode** — how to read keys one at a time and paint pixels (well, characters) on the screen
- **Regex tokenization** — how syntax highlighting works
- **Atomic file writes** — saving without corrupting files
- **Snapshot-based undo/redo** — simple and correct by construction

<img src="./assets/screenshot-1.png" alt="TUI Text Editor screenshot" width="700"/>

Let's build it!

## Setting Up

First, create a new directory for the project and download the starter code:

```bash
mkdir tui-text-editor
cd tui-text-editor
```

Grab the starter template from our repo at [https://github.com/Manas-thakur/python-tutorial](https://github.com/Manas-thakur/python-tutorial) (path: `project-submissions/tui-text-editor/starter/`).

Your project will end up with five files:

```
tui-text-editor/
├── editor.py      # Main loop — ties everything together
├── buffer.py      # Gap buffer + cursor + undo/redo
├── screen.py      # Terminal rendering (raw mode, ANSI codes)
├── syntax.py      # Tokenizer for syntax highlighting
└── files.py       # File I/O with encoding detection
```

**Python version:** You'll need Python 3.10+ for the `str | None` union syntax we use in `files.py`. If you're on an older version, replace `str | None` with `Optional[str]`.

No `pip install` required — we're using only the standard library.

## Step 1: The Editor Loop

Let's start by creating the project's entry point. Create a new file called `editor.py`:

```python
from buffer import EditorBuffer
from screen import Screen
from files import FileHandler
from syntax import tokenize


class Editor:
    def __init__(self):
        self.buffer = EditorBuffer()
        self.screen = Screen()
        self.files = FileHandler()

    def run(self):
        self.screen.enter_raw_mode()
        try:
            while True:
                self.screen.render(self.buffer)
                key = self.screen.read_key()
                if key == "Ctrl-Q":
                    break
                elif key == "Ctrl-S":
                    self.files.save(self.buffer)
                elif key == "Ctrl-Z":
                    self.buffer.undo()
                elif key == "Ctrl-R":
                    self.buffer.redo()
                elif key == "Ctrl-O":
                    content = self.files.open_prompt()
                    self.buffer.load(content)
                else:
                    self.buffer.insert_char(key)
        finally:
            self.screen.exit_raw_mode()


if __name__ == "__main__":
    Editor().run()
```

**Here's what's happening:**

The `Editor` class owns three components — a buffer for text, a screen for display, and a file handler for disk I/O. The `run()` method is the heart of the program:

1. Switch the terminal to raw mode so we can read keys one at a time.
2. Loop forever: render the current buffer, read a key, and dispatch it.
3. `Ctrl-Q` quits. `Ctrl-S` saves. `Ctrl-Z` / `Ctrl-R` undo/redo. `Ctrl-O` opens a file.
4. Any other key gets inserted into the buffer.
5. The `finally` block guarantees the terminal is restored, even if we crash.

At this point `editor.py` won't run yet — the other modules don't exist. That's fine. It's our roadmap. Let's build the modules one by one.

## Step 2: Gap Buffer and Cursor

Create `buffer.py`. This is the data layer — it holds all the text and manages cursor position.

```python
from dataclasses import dataclass


class GapBuffer:
    def __init__(self, initial: str = ""):
        self.buf: list[str] = list(initial) + [" "] * 10
        self.gap_start: int = len(initial)
        self.gap_end: int = len(self.buf) - 1

    def insert_char(self, c: str) -> None:
        self.buf[self.gap_start] = c
        self.gap_start += 1

    def delete_char(self) -> None:
        if self.gap_start > 0:
            self.gap_start -= 1
            self.buf[self.gap_start] = " "

    def move_gap_to(self, pos: int) -> None:
        while self.gap_start < pos:
            self.buf[self.gap_start] = self.buf[self.gap_end + 1]
            self.buf[self.gap_end + 1] = " "
            self.gap_start += 1
            self.gap_end += 1
        while self.gap_start > pos:
            self.gap_end -= 1
            self.gap_start -= 1
            self.buf[self.gap_end + 1] = self.buf[self.gap_start]
            self.buf[self.gap_start] = " "

    def to_string(self) -> str:
        return "".join(self.buf[:self.gap_start] + self.buf[self.gap_end + 1:])


@dataclass
class Cursor:
    row: int = 0
    col: int = 0


class EditorBuffer:
    def __init__(self):
        self.gap = GapBuffer()
        self.cursor = Cursor()

    def insert_char(self, c: str) -> None:
        idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
        self.gap.move_gap_to(idx)
        if c == "\n":
            self.gap.insert_char("\n")
            self.cursor.row += 1
            self.cursor.col = 0
        else:
            self.gap.insert_char(c)
            self.cursor.col += 1

    def delete_char(self) -> None:
        if self.cursor.col == 0 and self.cursor.row > 0:
            idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
            self.gap.move_gap_to(idx)
            self.gap.delete_char()
            self.cursor.row -= 1
            text = self.gap.to_string()
            lines = text.split("\n")
            self.cursor.col = len(lines[self.cursor.row])
        elif self.cursor.col > 0:
            idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
            self.gap.move_gap_to(idx)
            self.gap.delete_char()
            self.cursor.col -= 1

    def _row_col_to_index(self, row: int, col: int) -> int:
        idx = 0
        current_row = 0
        text = self.gap.to_string()
        while current_row < row and idx < len(text):
            if text[idx] == "\n":
                current_row += 1
            idx += 1
        return idx + col

    def move_left(self) -> None:
        if self.cursor.col > 0:
            self.cursor.col -= 1
        elif self.cursor.row > 0:
            self.cursor.row -= 1
            text = self.gap.to_string()
            lines = text.split("\n")
            self.cursor.col = len(lines[self.cursor.row])

    def move_right(self) -> None:
        text = self.gap.to_string()
        lines = text.split("\n")
        if self.cursor.col < len(lines[self.cursor.row]):
            self.cursor.col += 1
        elif self.cursor.row < len(lines) - 1:
            self.cursor.row += 1
            self.cursor.col = 0

    def move_up(self) -> None:
        if self.cursor.row > 0:
            self.cursor.row -= 1
            text = self.gap.to_string()
            lines = text.split("\n")
            self.cursor.col = min(self.cursor.col, len(lines[self.cursor.row]))

    def move_down(self) -> None:
        text = self.gap.to_string()
        lines = text.split("\n")
        if self.cursor.row < len(lines) - 1:
            self.cursor.row += 1
            self.cursor.col = min(self.cursor.col, len(lines[self.cursor.row]))

    def load(self, content: str) -> None:
        self.gap = GapBuffer(content)
        self.cursor = Cursor(0, 0)
```

**Here's what's happening:**

The **gap buffer** is a list of characters with a "hole" at the cursor. Everything before the gap is left text, everything after is right text, and the gap itself is unused space. Inserting a character just writes into the gap — O(1). Deleting just expands the gap backward — O(1). Moving the gap swaps characters through — O(distance). This beats Python's `list.insert(0)` which costs O(n) every time.

The **Cursor** is a simple row/col pair. We keep it separate from the gap buffer because the gap tracks a linear offset, but the user thinks in rows and columns. `_row_col_to_index()` converts between them by scanning through newlines.

The **EditorBuffer** wraps both and provides text-editing operations. `insert_char` handles newlines by inserting `\n` and advancing the row. `delete_char` handles backspace — if we're at column 0, it joins the current line with the previous one.

## Step 3: Undo and Redo

Now let's add undo/redo to `buffer.py`. We'll use a snapshot approach — every time we're about to change the buffer, we save the entire state.

First, update the `__init__` of `EditorBuffer` to add two stacks:

```python
class EditorBuffer:
    def __init__(self):
        self.gap = GapBuffer()
        self.cursor = Cursor()
        self.undo_stack: list[tuple[str, int, int]] = []
        self.redo_stack: list[tuple[str, int, int]] = []
```

Then add these three methods:

```python
    def snapshot(self):
        self.undo_stack.append((
            self.gap.to_string(),
            self.cursor.row,
            self.cursor.col,
        ))
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append((
            self.gap.to_string(),
            self.cursor.row,
            self.cursor.col,
        ))
        text, row, col = self.undo_stack.pop()
        self.gap = GapBuffer(text)
        self.cursor = Cursor(row, col)

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append((
            self.gap.to_string(),
            self.cursor.row,
            self.cursor.col,
        ))
        text, row, col = self.redo_stack.pop()
        self.gap = GapBuffer(text)
        self.cursor = Cursor(row, col)
```

Finally, update `insert_char` and `delete_char` to save a snapshot before making changes. Add `self.snapshot()` as the first line of each method:

```python
    def insert_char(self, c: str) -> None:
        self.snapshot()
        idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
        self.gap.move_gap_to(idx)
        if c == "\n":
            self.gap.insert_char("\n")
            self.cursor.row += 1
            self.cursor.col = 0
        else:
            self.gap.insert_char(c)
            self.cursor.col += 1

    def delete_char(self) -> None:
        self.snapshot()
        if self.cursor.col == 0 and self.cursor.row > 0:
            ...   # rest stays the same
```

**Here's what's happening:**

Each snapshot stores the full text and cursor position as a tuple. When you undo, the current state is pushed onto the redo stack and the top of the undo stack is restored. Redo reverses the process. Any new edit after an undo clears the redo stack (that's the `redo_stack.clear()` in `snapshot()`) — this matches the behavior of every text editor you've ever used.

Why snapshots instead of command deltas? Snapshots are simple and correct by construction. If you undo a paste, then type a character, then redo — what happens? With deltas you'd have to carefully compose or discard operations. With snapshots, the old redo stack is simply cleared. For the file sizes a TUI editor handles, the memory cost of storing a few hundred full-text snapshots is negligible.

## Step 4: Terminal Rendering

Create `screen.py`. This is where the editor talks to the terminal.

```python
import sys
import tty
import shutil
import signal
import termios


class Screen:
    def __init__(self):
        self.width = shutil.get_terminal_size().columns
        self.height = shutil.get_terminal_size().lines
        signal.signal(signal.SIGWINCH, lambda s, f: self._resize())

    def _resize(self):
        self.width = shutil.get_terminal_size().columns
        self.height = shutil.get_terminal_size().lines

    def enter_raw_mode(self):
        tty.setcbreak(sys.stdin.fileno())
        sys.stdout.write("\033[?1049h")
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def exit_raw_mode(self):
        sys.stdout.write("\033[?1049l")
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def read_key(self) -> str:
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            if seq == "[A":
                return "Up"
            elif seq == "[B":
                return "Down"
            elif seq == "[C":
                return "Right"
            elif seq == "[D":
                return "Left"
            return ch + seq
        elif ch == "\x7f":
            return "Backspace"
        elif ch == "\r":
            return "Enter"
        elif ch == "\x11":
            return "Ctrl-Q"
        elif ch == "\x13":
            return "Ctrl-S"
        elif ch == "\x1a":
            return "Ctrl-Z"
        elif ch == "\x12":
            return "Ctrl-R"
        elif ch == "\x0f":
            return "Ctrl-O"
        return ch

    def render(self, buffer) -> None:
        lines = buffer.gap.to_string().split("\n")
        out = ["\033[H"]
        for i, line in enumerate(lines[:self.height - 1]):
            line_num = f"{i + 1:>3} "
            visible = line[:self.width - 5]
            out.append(f"\033[2K{line_num}{visible}")
        out.append(f"\033[{buffer.cursor.row + 1};{buffer.cursor.col + 5}H")
        sys.stdout.write("\n".join(out))
        sys.stdout.flush()
```

**Here's what's happening:**

**Raw mode** (`enter_raw_mode`) switches the terminal so we can read keys instantly without waiting for Enter. It also switches to the alternate screen buffer (so our editor doesn't pollute the terminal history) and hides the cursor.

**Key reading** (`read_key`) reads one byte. If it's `\x1b` (Escape), it tries to read two more bytes to detect arrow key sequences. Control characters are mapped to friendly names like `"Ctrl-Q"`. Regular characters pass through as-is.

**Rendering** (`render`) builds the entire screen from scratch every frame:
1. `\033[H` moves the cursor home.
2. For each visible line, we clear it with `\033[2K`, print the line number, then print the text (truncated to fit).
3. Move the hardware cursor to match the editor cursor position.

**Resize handling** uses `SIGWINCH`. When the terminal is resized, the signal fires, `_resize()` re-queries the dimensions, and the next render adapts. The buffer content is untouched — only the viewport changes.

Here's what the ANSI codes mean:

| Code | Meaning |
|------|---------|
| `\033[H` | Move cursor to home (1, 1) |
| `\033[2K` | Clear entire current line |
| `\033[{row};{col}H` | Move cursor to position |
| `\033[?1049h` | Switch to alternate screen |
| `\033[?25l` / `\033[?25h` | Hide / show cursor |

## Step 5: Syntax Highlighting

Create `syntax.py`. This uses a regex-based tokenizer to colorize Python code.

```python
import re

TOKEN_SPEC = [
    ("KEYWORD", r"\b(def|class|if|elif|else|for|while|return|import|from|try|except|with|as|pass|break|continue|and|or|not|in|is|None|True|False)\b"),
    ("STRING", r'"[^"]*"|\'[^\']*\''),
    ("COMMENT", r"#.*"),
    ("NUMBER", r"\b\d+(\.\d+)?\b"),
    ("FUNCALL", r"\b([a-zA-Z_][a-zA-Z0-9_]*)\("),
    ("BUILTIN", r"\b(print|len|range|int|str|list|dict|open|type|isinstance|enumerate|zip|map|filter|sorted|reversed)\b"),
    ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("WHITESPACE", r"[ \t]+"),
    ("NEWLINE", r"\n"),
    ("MISMATCH", r"."),
]

TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

TOKEN_COLORS = {
    "KEYWORD": "\033[38;5;198m",
    "STRING": "\033[38;5;78m",
    "COMMENT": "\033[38;5;244m",
    "NUMBER": "\033[38;5;220m",
    "FUNCALL": "\033[38;5;51m",
    "BUILTIN": "\033[38;5;141m",
}


def tokenize(code: str) -> list[tuple[str, str]]:
    tokens = []
    for match in TOKEN_RE.finditer(code):
        kind = match.lastgroup
        value = match.group()
        tokens.append((kind, value))
    return tokens


def highlight_line(line: str) -> str:
    tokens = tokenize(line)
    result = ""
    for kind, value in tokens:
        color = TOKEN_COLORS.get(kind)
        if color:
            result += f"{color}{value}\033[0m"
        else:
            result += value
    return result
```

**Here's what's happening:**

The tokenizer scans text left-to-right and classifies each piece. The regex uses named groups — `(?P<KEYWORD>...)` — so each match tells us both what was matched and what kind it is.

The color map assigns ANSI 256-color codes to each token type. `\033[38;5;Nm` sets the foreground color to one of 256 indexed colors, and `\033[0m` resets everything.

Why regex instead of Python's AST? A full AST parser would be more accurate (it knows that `foo` in `foo.bar` is not a function call), but it's slow, requires parsing the whole file, and breaks on syntax errors. For highlighting, regex is fast, incremental, and handles incomplete code gracefully.

## Step 6: File Operations

Create `files.py`. This handles reading and writing files with automatic encoding detection and atomic saves.

```python
import os
import tempfile
import codecs


class FileHandler:
    def __init__(self):
        self.current_path: str | None = None
        self.encoding: str = "utf-8"

    def read(self, path: str) -> str:
        self.current_path = path
        with open(path, "rb") as f:
            raw = f.read()
        self.encoding = self._detect_encoding(raw)
        return raw.decode(self.encoding)

    def _detect_encoding(self, raw: bytes) -> str:
        if raw.startswith(codecs.BOM_UTF32_LE) or raw.startswith(codecs.BOM_UTF32_BE):
            return "utf-32"
        if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
            return "utf-16"
        if raw.startswith(codecs.BOM_UTF8):
            return "utf-8-sig"
        try:
            raw.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            try:
                raw.decode("latin-1")
                return "latin-1"
            except UnicodeDecodeError:
                return "utf-8"

    def save(self, buffer) -> None:
        if not self.current_path:
            return
        text = buffer.gap.to_string()
        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(self.current_path),
            prefix=".editor-tmp-",
        )
        try:
            with os.fdopen(fd, "w", encoding=self.encoding) as f:
                f.write(text)
            os.replace(tmp_path, self.current_path)
        except:
            os.unlink(tmp_path)
            raise

    def open_prompt(self) -> str:
        path = input("File path: ").strip()
        return self.read(path)
```

**Here's what's happening:**

**Reading** detects the file encoding by checking the Byte Order Mark (BOM) in the first few bytes. UTF-16 files saved by Windows Notepad start with `\xff\xfe`. UTF-32 files have a different BOM. If there's no BOM, we try UTF-8, then latin-1, then fall back to UTF-8. The encoding is stored so we re-use it when saving.

**Saving** uses an atomic write pattern: write to a temporary file in the same directory, then `os.replace()` it over the target. `os.replace()` is atomic on POSIX — if the editor crashes mid-write, the original file is untouched. The temp file is hidden (prefixed with `.editor-tmp-`) and lives in the same directory to guarantee `os.replace` doesn't cross filesystem boundaries.

**open_prompt** uses `input()` which works because we briefly leave raw mode. In a more polished editor, you'd draw a prompt line directly on the alternate screen — but this gets the job done for now.

## Step 7: Putting It All Together

Now go back to `editor.py` and update it to handle arrow keys, backspace, and Enter. Replace your file with this:

```python
from buffer import EditorBuffer
from screen import Screen
from files import FileHandler
from syntax import highlight_line


class Editor:
    def __init__(self):
        self.buffer = EditorBuffer()
        self.screen = Screen()
        self.files = FileHandler()

    def run(self):
        self.screen.enter_raw_mode()
        try:
            while True:
                self.screen.render(self.buffer)
                key = self.screen.read_key()
                if key == "Ctrl-Q":
                    break
                elif key == "Ctrl-S":
                    self.files.save(self.buffer)
                elif key == "Ctrl-Z":
                    self.buffer.undo()
                elif key == "Ctrl-R":
                    self.buffer.redo()
                elif key == "Ctrl-O":
                    content = self.files.open_prompt()
                    self.buffer.load(content)
                elif key == "Up":
                    self.buffer.move_up()
                elif key == "Down":
                    self.buffer.move_down()
                elif key == "Left":
                    self.buffer.move_left()
                elif key == "Right":
                    self.buffer.move_right()
                elif key == "Backspace":
                    self.buffer.delete_char()
                elif key == "Enter":
                    self.buffer.insert_char("\n")
                elif len(key) == 1:
                    self.buffer.insert_char(key)
        finally:
            self.screen.exit_raw_mode()


if __name__ == "__main__":
    Editor().run()
```

Now update `screen.py` to use syntax highlighting in the render. Replace the `render` method:

```python
    def render(self, buffer) -> None:
        lines = buffer.gap.to_string().split("\n")
        out = ["\033[H"]
        for i, line in enumerate(lines[:self.height - 1]):
            line_num = f"{i + 1:>3} "
            highlighted = highlight_line(line)
            visible = highlighted[:self.width - 5]
            out.append(f"\033[2K{line_num}{visible}")
        out.append(f"\033[{buffer.cursor.row + 1};{buffer.cursor.col + 5}H")
        sys.stdout.write("\n".join(out))
        sys.stdout.flush()
```

**Here's what's happening:**

The editor now dispatches arrow keys to cursor movement methods, Backspace to `delete_char`, and Enter to `insert_char("\n")`. The `len(key) == 1` guard ensures we don't try to insert multi-character key names like `"Ctrl-Q"` into the buffer.

The renderer now passes each line through `highlight_line()` before printing it. Keywords show up in pink, strings in green, comments in gray, numbers in yellow, function calls in cyan, and builtins in purple. The raw text in the buffer stays uncolored — we only add ANSI codes at display time.

## Step 8: Running and Extending

You're done! Fire it up:

```bash
python editor.py
```

You should see the alternate screen buffer with a blank editing area. Type away.

### Default Keybindings

| Key | Action |
|-----|--------|
| `Ctrl-Q` | Quit |
| `Ctrl-S` | Save |
| `Ctrl-O` | Open file (prompts for path) |
| `Ctrl-Z` | Undo |
| `Ctrl-R` | Redo |
| Arrow keys | Move cursor |
| `Backspace` | Delete character before cursor |
| `Enter` | Insert newline |

### Ideas to Extend

**Split panes.** Give the `Screen` a list of buffers and a layout direction:

```python
class SplitScreen:
    def __init__(self, direction="h"):
        self.panes: list[EditorBuffer] = []
        self.direction = direction
        self.active = 0

    def render(self):
        if self.direction == "h":
            half = self.width // len(self.panes)
            for i, buf in enumerate(self.panes):
                # render buf into slice [i*half : (i+1)*half]
                pass
```

**File explorer sidebar.** Before the main loop, list the current directory. Render a collapsible tree on the left 20 columns. When the user presses `Ctrl-P`, focus switches to the explorer.

**Search (`Ctrl-F`).** Add a find method to `EditorBuffer` that scans for a substring and jumps the cursor to it.

**Line numbers relative to cursor.** Vim-style relative line numbers make navigation faster. Instead of `f"{i + 1:>3}"`, show the absolute distance from the cursor row.

**Beyond the TUI.** Because `GapBuffer` and `EditorBuffer` are pure Python with no terminal imports, you can wrap them in a Flask web app or a Qt widget without changing a single line of buffer code. That separation — data model first, views later — is the real lesson here.

## Conclusion

You built a working text editor from scratch! Here's what you accomplished:

- Implemented a gap buffer with O(1) insert and delete at the cursor
- Built cursor movement across lines with proper column clamping
- Added snapshot-based undo/redo that's simple and correct
- Rendered to the terminal using ANSI escape codes and raw mode
- Tokenized Python code with regex for syntax highlighting
- Handled file I/O with encoding detection and atomic saves
- Wired everything together into a clean, modular event loop

The full source code is available at [https://github.com/Manas-thakur/python-tutorial](https://github.com/Manas-thakur/python-tutorial) (path: `project-submissions/tui-text-editor/solution/`).
