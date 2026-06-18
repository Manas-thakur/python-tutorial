from dataclasses import dataclass
from typing import Optional


class GapBuffer:
    def __init__(self, initial: str = ""):
        self.buf: list[str] = list(initial) + [" "] * 10
        self.gap_start: int = len(initial)
        self.gap_end: int = len(self.buf) - 1

    def insert_char(self, c: str):
        if self.gap_start > self.gap_end:
            self._grow()
        self.buf[self.gap_start] = c
        self.gap_start += 1

    def delete_char(self):
        if self.gap_start > 0:
            self.gap_start -= 1
            self.buf[self.gap_start] = " "

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

    def to_string(self) -> str:
        return "".join(self.buf[:self.gap_start] + self.buf[self.gap_end + 1:])

    def load(self, text: str):
        self.buf = list(text) + [" "] * 10
        self.gap_start = len(text)
        self.gap_end = len(self.buf) - 1

    def __len__(self) -> int:
        return len(self.buf) - (self.gap_end - self.gap_start + 1)

    def _grow(self):
        extra = [" "] * 10
        self.buf[self.gap_start:self.gap_end + 1] = extra
        self.gap_end = self.gap_start + len(extra) - 1


@dataclass
class Cursor:
    row: int = 0
    col: int = 0


class EditorBuffer:
    def __init__(self):
        self.gap = GapBuffer()
        self.cursor = Cursor()
        self.undo_stack: list[tuple[str, int, int]] = []
        self.redo_stack: list[tuple[str, int, int]] = []

    def insert_char(self, c: str):
        self.snapshot()
        idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
        self.gap.move_gap_to(idx)
        self.gap.insert_char(c)
        if c == "\n":
            self.cursor.row += 1
            self.cursor.col = 0
        else:
            self.cursor.col += 1

    def delete_char(self):
        if self.cursor.col == 0 and self.cursor.row == 0:
            return
        self.snapshot()
        idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
        self.gap.move_gap_to(idx)
        self.gap.delete_char()
        if self.cursor.col > 0:
            self.cursor.col -= 1
        else:
            self.cursor.row -= 1
            text = self.gap.to_string()
            line_start = self._row_col_to_index(self.cursor.row, 0)
            line_end = text.find("\n", line_start)
            if line_end == -1:
                line_end = len(text)
            self.cursor.col = line_end - line_start

    def move_left(self):
        if self.cursor.col > 0:
            self.cursor.col -= 1
        elif self.cursor.row > 0:
            self.cursor.row -= 1
            text = self.gap.to_string()
            line_start = self._row_col_to_index(self.cursor.row, 0)
            line_end = text.find("\n", line_start)
            if line_end == -1:
                line_end = len(text)
            self.cursor.col = line_end - line_start

    def move_right(self):
        text = self.gap.to_string()
        line_start = self._row_col_to_index(self.cursor.row, 0)
        line_end = text.find("\n", line_start)
        if line_end == -1:
            line_end = len(text)
        line_len = line_end - line_start
        if self.cursor.col < line_len:
            self.cursor.col += 1
        elif line_end < len(text):
            self.cursor.row += 1
            self.cursor.col = 0

    def move_up(self):
        if self.cursor.row == 0:
            return
        text = self.gap.to_string()
        idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
        prev_nl = text.rfind("\n", 0, idx)
        if prev_nl == -1:
            return
        prev_prev_nl = text.rfind("\n", 0, prev_nl - 1) if prev_nl > 0 else -1
        line_start = prev_prev_nl + 1 if prev_prev_nl != -1 else 0
        line_len = prev_nl - line_start
        self.cursor.row -= 1
        self.cursor.col = min(self.cursor.col, line_len)

    def move_down(self):
        text = self.gap.to_string()
        idx = self._row_col_to_index(self.cursor.row, self.cursor.col)
        nl = text.find("\n", idx)
        if nl != -1:
            self.cursor.row += 1
            next_line_start = nl + 1
            next_line_end = text.find("\n", next_line_start)
            if next_line_end == -1:
                next_line_end = len(text)
            line_len = next_line_end - next_line_start
            self.cursor.col = min(self.cursor.col, line_len)

    def _row_col_to_index(self, row: int, col: int) -> int:
        idx = 0
        current_row = 0
        text = self.gap.to_string()
        while current_row < row and idx < len(text):
            if text[idx] == "\n":
                current_row += 1
            idx += 1
        line_end = text.find("\n", idx)
        if line_end == -1:
            line_end = len(text)
        col = min(col, line_end - idx)
        return idx + col

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

    def find(self, text: str) -> Optional[tuple[int, int]]:
        full = self.gap.to_string()
        idx = full.find(text)
        if idx == -1:
            return None
        row = full[:idx].count("\n")
        last_nl = full[:idx].rfind("\n")
        col = idx - last_nl - 1 if last_nl != -1 else idx
        return (row, col)
