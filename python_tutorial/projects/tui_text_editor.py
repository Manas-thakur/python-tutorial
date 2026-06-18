from python_tutorial.models import ProjectTutorial, Section

TUTORIAL = ProjectTutorial(
    slug="tui-text-editor",
    title="Build a TUI Text Editor",
    description="Create a terminal-based text editor from scratch with syntax highlighting, undo/redo, and file operations.",
    difficulty="intermediate",
    project_dir="tui-text-editor",
    prerequisites=["Functions", "File I/O", "Classes"],
    steps=[
        Section(
            heading="Step 1: Understanding the Architecture",
            content="""\
Let's start by looking at how the editor is wired together. Open the `editor.py` file — it's the entry point and the orchestrator.

```
project/
├── editor.py      # Main loop, ties everything together
├── buffer.py      # Gap buffer + cursor + undo/redo
├── screen.py      # Terminal rendering (raw mode, ANSI codes)
├── syntax.py      # Tokenizer for syntax highlighting
└── files.py       # File I/O with encoding detection
```

**Data flow** in a single keypress:

```
┌──────────┐   key   ┌──────────┐   edit    ┌────────┐
│  screen  │◄─────── │  editor  │─────────► │ buffer │
│ .render()│         │ .run()   │◄───────── │        │
└──────────┘         └──────────┘  content  └────────┘
     ▲                     │                      │
     │                read file                undo/redo
     │                     ▼                      │
     │              ┌──────────┐                  │
     └──────────────┤  files   │◄─────────────────┘
                    └──────────┘
```

The `editor.py` `run()` method looks like this:

```python
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
```

The editor never touches terminal escape codes directly — it delegates to `screen`. It never touches files — it delegates to `files`. All text state lives in `buffer`. This modularity means you can test each piece in isolation, and swap out the terminal layer later if you want to add a GUI. Each component owns one concern, and they communicate through simple method calls on self-contained objects. This is the **single-responsibility principle** in practice: when you fix a rendering bug, you change `screen.py`, not `editor.py`.
""",
        ),
        Section(
            heading="Step 2: The Gap Buffer",
            content="""\
Open `buffer.py` and find the `GapBuffer` class. This is the data structure that holds the text.

Most beginners reach for Python's `list` to store characters, but inserting or deleting at the middle of a list costs **O(n)** — every character after the cursor must shift. A gap buffer solves this by leaving a gap at the cursor position.

```python
class GapBuffer:
    def __init__(self, initial: str = ""):
        self.buf: list[str] = list(initial) + [" "] * 10
        self.gap_start: int = len(initial)
        self.gap_end: int = len(self.buf) - 1
```

**Dry run: Inserting "hello" into an empty gap buffer.**

Start: `gap_start = 0`, `gap_end = 9`, buffer = `[' ',' ',' ',' ',' ',' ',' ',' ',' ',' ']`

1. `insert_char('h')` → write 'h' at `buf[0]`, move `gap_start` to 1. Buffer: `['h',' ',' ',' ',' ',' ',' ',' ',' ',' ']`
2. `insert_char('e')` → write 'e' at `buf[1]`, `gap_start = 2`. Buffer: `['h','e',' ',' ',' ',' ',' ',' ',' ',' ']`
3. `insert_char('l')` → `gap_start = 3`. Buffer: `['h','e','l',' ',' ',' ',' ',' ',' ',' ']`
4. `insert_char('l')` → `gap_start = 4`. Buffer: `['h','e','l','l',' ',' ',' ',' ',' ',' ']`
5. `insert_char('o')` → `gap_start = 5`. Buffer: `['h','e','l','l','o',' ',' ',' ',' ',' ']`

Now let's move the cursor to position 2 and insert 'x':

```python
def move_gap_to(self, pos: int):
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
```

When `move_gap_to(2)` is called, the gap slides right from position 5 to position 2 by swapping characters one at a time from the right side of the gap to the left. After moving, `gap_start = 2`, `gap_end = 7`, and the visible text is `['h','e',' ',' ',' ',' ',' ','l','o',' ']`. Now `insert_char('x')` writes 'x' at position 2 and `gap_start = 3`, yielding visible `"hexlo"`.

**Why a gap buffer?** It gives **O(1)** insert and delete at the cursor, and moves the gap in **O(gap_distance)** — much faster than shifting the entire buffer. It's the structure used by GNU Emacs and many editors because most edits are clustered around the cursor.
""",
        ),
        Section(
            heading="Step 3: Cursor Movement",
            content="""\
Still in `buffer.py`, the `Cursor` class tracks position separately from the gap buffer.

```python
@dataclass
class Cursor:
    row: int = 0
    col: int = 0
```

The `EditorBuffer` holds both:

```python
class EditorBuffer:
    def __init__(self):
        self.gap = GapBuffer()
        self.cursor = Cursor()
```

**Why not store cursor position inside the gap buffer?** Because a cursor has two dimensions (row, column), and the gap buffer tracks a single linear offset. The row/col abstraction is what the user sees, and it's what the screen renderer needs to know where to place the terminal cursor.

**Dry run: Moving through `"ab\\nc"`** (two lines).

The gap buffer stores this linearly as `['a','b','\\n','c',' ','...']` with gap at the end. The `EditorBuffer` has a method to convert row/col to a linear index:

```python
def _row_col_to_index(self, row: int, col: int) -> int:
    idx = 0
    current_row = 0
    text = self.gap.to_string()
    while current_row < row and idx < len(text):
        if text[idx] == '\\n':
            current_row += 1
        idx += 1
    return idx + col
```

Starting state: cursor at `row=0, col=0`, gap at end.

1. Press **→** → `move_right()` increments col to 1. The underlying gap hasn't moved.
2. Press **→** again → col becomes 2. Before insertion, `move_gap_to(2)` slides the gap to linear index 2.
3. Press **↓** → `move_down()` calls `_row_col_to_index(1, 0)` which scans forward past the newline at index 2 and lands at index 3. Then `move_gap_to(3)` slides the gap there.

```python
def move_down(self):
    text = self.gap.to_string()
    idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
    nl = text.find('\\n', idx)
    if nl != -1:
        self.cursor.row += 1
        next_line_start = nl + 1
        next_line_end = text.find('\\n', next_line_start)
        if next_line_end == -1:
            next_line_end = len(text)
        line_len = next_line_end - next_line_start
        self.cursor.col = min(self.cursor.col, line_len)
```

This approach keeps cursor logic testable: you can verify that pressing down on a short line clamps `col` to the available line length, preventing the cursor from floating past the end of the text.
""",
        ),
        Section(
            heading="Step 4: Undo/Redo Stack",
            content="""\
Scroll down in `buffer.py` to see the undo/redo implementation. It uses a **snapshot-based** approach.

```python
class EditorBuffer:
    def __init__(self):
        self.gap = GapBuffer()
        self.cursor = Cursor()
        self.undo_stack: list[tuple[str, int, int]] = []
        self.redo_stack: list[tuple[str, int, int]] = []

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

**Dry run: Type "a", then "b", undo, redo.**

1. Start: buffer = `""` → snapshot saves `("", 0, 0)` to undo_stack.
2. Insert 'a': buffer = `"a"` → snapshot saves `("a", 0, 1)` to undo_stack.
3. Insert 'b': buffer = `"ab"` → snapshot saves `("ab", 0, 2)` to undo_stack.
4. Undo: pop `("ab", 0, 2)`, push it to redo_stack. Pop `("a", 0, 1)` and restore. Buffer = `"a"`.
5. Undo again: pop `("a", 0, 1)`, push to redo_stack. Pop `("", 0, 0)` and restore. Buffer = `""`.
6. Redo: pop back, restore `("a", 0, 1)`. Buffer = `"a"`.

Each snapshot stores the full text (plus cursor). This is **O(n)** memory per snapshot, but for a text editor with typical editing sessions of a few hundred snapshots, it works fine. **Why not the command pattern?** A command pattern stores only deltas (insert "b" at position 1), which is more memory-efficient but far more complex — you need to handle overlapping undos correctly (if you undo "paste 50 chars", then insert one char, then redo, what happens?). Snapshots are simple, correct by construction, and for the file sizes a TUI editor handles, the memory cost is negligible. Emacs famously uses a similar snapshot-like approach (the undo-tree).
""",
        ),
        Section(
            heading="Step 5: Terminal Rendering",
            content="""\
Open `screen.py`. This is where the editor talks to the terminal.

```python
class Screen:
    def __init__(self):
        self.width = shutil.get_terminal_size().columns
        self.height = shutil.get_terminal_size().lines

    def enter_raw_mode(self):
        tty.setcbreak(sys.stdin.fileno())
        sys.stdout.write('\\033[?1049h')   # alternate screen
        sys.stdout.write('\\033[?25l')      # hide cursor
        sys.stdout.flush()

    def exit_raw_mode(self):
        sys.stdout.write('\\033[?1049l')   # main screen
        sys.stdout.write('\\033[?25h')      # show cursor
        sys.stdout.flush()
```

**Dry run: Rendering 3 lines with cursor on line 2.**

The buffer holds `"def foo():\\n    pass\\n"`. The screen's `render()` method:

```python
def render(self, buffer: EditorBuffer):
    lines = buffer.gap.to_string().split('\\n')
    out = []
    out.append('\\033[H')  # cursor to home (1,1)
    for i, line in enumerate(lines[:self.height - 1]):
        line_num = f"{i + 1:>3} "
        visible = line[:self.width - 5]
        out.append(f"\\033[2K{line_num}{visible}")
    # Move hardware cursor to match editor cursor
    out.append(f"\\033[{buffer.cursor.row + 1};{buffer.cursor.col + 5}H")
    sys.stdout.write('\\n'.join(out))
    sys.stdout.flush()
```

The escape codes break down like this:

| Code | Meaning |
|------|---------|
| `\\033[H` | Move cursor to home (1, 1) |
| `\\033[2K` | Clear entire current line |
| `\\033[{};{}H` | Move cursor to row, col |
| `\\033[?1049h` | Switch to alternate screen buffer |
| `\\033[?25l` | Hide cursor |

Step by step for our 3-line buffer on an 80×24 terminal:

1. `\\033[H` resets cursor to top-left.
2. Line 0: `\\033[2K   1 def foo()` — clears line, prints line number and content.
3. Line 1: `\\033[2K   2     pass` — same for second line.
4. Cursor positioning: `\\033[2;7H` — moves hardware cursor to row 2, column 7 (aligning with the 'p' in "pass").

**Terminal resize** is handled by catching `SIGWINCH`:

```python
import signal

signal.signal(signal.SIGWINCH, lambda s, f: self._resize())
```

When the terminal is resized, the signal fires, `_resize()` re-queries the terminal dimensions, and the next `render()` call adapts to the new size. The buffer content is untouched — only the viewport changes.
""",
        ),
        Section(
            heading="Step 6: Syntax Highlighting",
            content="""\
Open `syntax.py`. The highlighter uses a **tokenizer** (lexer) approach: it scans the text left-to-right and emits (token_type, text) pairs.

```python
import re

TOKEN_SPEC = [
    ("KEYWORD", r'\\b(def|class|if|elif|else|for|while|return|import|from|try|except|with|as|pass|break|continue|and|or|not|in|is|None|True|False)\\b'),
    ("STRING", r'"[^"]*"|\'[^\']*\'),
    ("COMMENT", r'#.*'),
    ("NUMBER", r'\\b\\d+(\\.\\d+)?\\b'),
    ("FUNCALL", r'\\b([a-zA-Z_][a-zA-Z0-9_]*)\\('),
    ("BUILTIN", r'\\b(print|len|range|int|str|list|dict|open|type|isinstance|enumerate|zip|map|filter|sorted|reversed)\\b'),
    ("IDENTIFIER", r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ("WHITESPACE", r'[ \\t]+'),
    ("NEWLINE", r'\\n'),
    ("MISMATCH", r'.'),
]

TOKEN_RE = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC))
```

**Dry run: Tokenizing `"def foo():\\n    # comment"`.**

The regex engine produces these tokens:

| Token | Text | Position |
|-------|------|----------|
| KEYWORD | `def` | 0-2 |
| WHITESPACE | ` ` | 3 |
| FUNCALL | `foo(` | 4-7 |
| PUNCTUATION | `)` | 8 |
| NEWLINE | `\\n` | 9 |
| WHITESPACE | `    ` | 10-13 |
| COMMENT | `# comment` | 14-23 |

The screen renderer uses these tokens to apply ANSI color codes:

```python
TOKEN_COLORS = {
    "KEYWORD": "\\033[38;5;198m",   # Bright pink
    "STRING": "\\033[38;5;78m",    # Green
    "COMMENT": "\\033[38;5;244m",  # Gray
    "NUMBER": "\\033[38;5;220m",   # Yellow
    "FUNCALL": "\\033[38;5;51m",   # Cyan
    "BUILTIN": "\\033[38;5;141m",  # Purple
}
```

Before rendering each line, the screen calls `tokenize(line)` and wraps tokens in color codes. When `"def"` comes back as KEYWORD, it becomes `\\033[38;5;198mdef\\033[0m` — pink text followed by a reset.

**Why regex-based instead of AST-based?** A full Python AST parser would be correct (it knows that `foo` in `foo.bar` is not a function call), but it's heavy, requires the `ast` module to parse the entire file even for partial updates, and breaks on syntax errors. Regex tokenization is fast, incremental (you can re-tokenize one line at a time), and handles incomplete or wrong code gracefully. For syntax *highlighting* (where accuracy is cosmetic), regex is the right trade-off. For syntax *analysis* (like a linter), you'd use the AST.
""",
        ),
        Section(
            heading="Step 7: File Operations",
            content="""\
Open `files.py`. The `FileHandler` manages reading and writing files with encoding detection and safe writes.

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
```

**Dry run: Opening a UTF-16 file saved by Windows Notepad.**

The bytes start with a Byte Order Mark (BOM): `\\xff\\xfe`. The `_detect_encoding` method checks:

```python
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
```

It inspects the leading bytes to determine encoding, falling back through common encodings. For a UTF-16 LE file, it returns `"utf-16"`, and the `raw.decode("utf-16")` call produces the correct Python string. The BOM is consumed transparently by the codec.

**Saving uses an atomic write pattern:**

```python
def save(self, buffer: EditorBuffer) -> None:
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
```

**Why write to a temp file first, then rename?** Because the rename (`os.replace`) is **atomic** on POSIX systems. If the editor crashes mid-write, the original file is untouched. If you wrote directly to the target file and the write failed halfway, you'd have a corrupted file. The temp file is also hidden (prefixed with `.editor-tmp-`) and written in the same directory to guarantee the `os.replace` stays on the same filesystem.
""",
        ),
        Section(
            heading="Step 8: Running and Extending",
            content="""\
To start the editor, run the project from its directory:

```bash
cd tui-text-editor
python editor.py
```

This launches the alternate screen buffer with a blank editing area. Here are the default keybindings wired in `editor.py`:

| Key | Action |
|-----|--------|
| `Ctrl-Q` | Quit |
| `Ctrl-S` | Save |
| `Ctrl-O` | Open file (prompt for path) |
| `Ctrl-Z` | Undo |
| `Ctrl-R` | Redo |
| `Ctrl-F` | Find (basic search prompt) |
| Arrow keys | Cursor movement |
| `Backspace` | Delete character before cursor |
| `Enter` | Split line at cursor |

**What to try next — extension ideas:**

**Split panes.** The `Screen` class currently renders one buffer. You could give it a list of buffers and a layout direction:

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

**File explorer sidebar.** Before entering the main loop, list the current directory tree. Use the `os` module to walk directories and render a collapsible tree on the left 20 columns. When the user presses `Ctrl-P`, focus switches to the explorer.

**Minimap.** A compressed overview of the file on the right margin. Render every 10th line as a one-pixel row (using a block character `\\u2588`). Highlight the visible viewport region with inverse video:

```python
def render_minimap(self, lines, viewport_start, viewport_end):
    for i in range(0, len(lines), 10):
        pixel = "\\u2588"  # full block
        if viewport_start <= i <= viewport_end:
            pixel = "\\033[7m" + pixel + "\\033[0m"  # inverted
        # write pixel at rightmost column, row i//10
```

**Beyond the TUI.** Because the editor's core (buffer, cursor, undo) is pure Python with no terminal dependencies, you could trivially wrap it in a Flask web app or a Qt widget. The `GapBuffer` and `EditorBuffer` classes don't import `sys`, `tty`, or anything OS-specific — they make perfect library code. That separation is the real lesson: build the data model first, then attach as many views as you like.
""",
        ),
    ],
)
