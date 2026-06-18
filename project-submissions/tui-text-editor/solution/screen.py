import os
import sys
import tty
import signal
import shutil
import select
import re

from syntax import tokenize, apply_highlighting


class Screen:
    def __init__(self):
        self.width = shutil.get_terminal_size().columns
        self.height = shutil.get_terminal_size().lines
        self.scroll_offset = 0
        signal.signal(signal.SIGWINCH, lambda s, f: self._resize())

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
        raw = os.read(sys.stdin.fileno(), 1)
        if not raw:
            return ""
        b = raw[0]

        if b == 0x1B:
            if select.select([sys.stdin], [], [], 0.05)[0]:
                seq = os.read(sys.stdin.fileno(), 1)
                if seq and seq[0] == ord("["):
                    if select.select([sys.stdin], [], [], 0.01)[0]:
                        rest = os.read(sys.stdin.fileno(), 1)
                        if rest:
                            ch = rest[0]
                            if ch == ord("A"):
                                return "Up"
                            if ch == ord("B"):
                                return "Down"
                            if ch == ord("C"):
                                return "Right"
                            if ch == ord("D"):
                                return "Left"
                            if ch == ord("H"):
                                return "Home"
                            if ch == ord("F"):
                                return "End"
                            if ch == ord("~"):
                                if select.select([sys.stdin], [], [], 0.01)[0]:
                                    more = os.read(sys.stdin.fileno(), 1)
                                    if more and more[0] == ord("~"):
                                        return "Del"
            return "Escape"

        if b == 0x7F:
            return "Backspace"
        if b == 0x0D:
            return "Enter"
        if b == 0x09:
            return "Tab"
        if 1 <= b <= 26:
            return f"Ctrl-{chr(64 + b)}"

        return chr(b)

    def render(self, buffer, mode="edit", prompt_input="", filepath=None):
        self.width = shutil.get_terminal_size().columns
        self.height = shutil.get_terminal_size().lines

        text = buffer.gap.to_string()
        lines = text.split("\n")
        screen_lines = self.height - 1

        cursor_row = buffer.cursor.row
        if cursor_row < self.scroll_offset:
            self.scroll_offset = cursor_row
        elif cursor_row >= self.scroll_offset + screen_lines:
            self.scroll_offset = cursor_row - screen_lines + 1

        out = []
        out.append("\033[H")
        max_content = self.width - 5

        for i in range(screen_lines):
            line_idx = self.scroll_offset + i
            out.append("\033[2K")
            if line_idx < len(lines):
                line = lines[line_idx]
                truncated = line[:max_content]
                tokens = tokenize(truncated)
                highlighted = apply_highlighting(tokens)
                line_num = f"{line_idx + 1:>3} "
            else:
                highlighted = ""
                line_num = " ~  "
            out.append(f"{line_num}{highlighted}")
            out.append("\033[0m")
            out.append("\r\n")

        status_parts = []
        if filepath:
            status_parts.append(f" {filepath}")
        else:
            status_parts.append(" [No Name]")
        if mode == "find":
            status_parts.append(f" | Find: {prompt_input}")
        elif mode == "open":
            status_parts.append(f" | Open: {prompt_input}")
        elif mode == "save":
            status_parts.append(f" | Save: {prompt_input}")
        status_parts.append(f" | Ln {cursor_row + 1}, Col {buffer.cursor.col + 1} ")
        status = "".join(status_parts)
        status = status[:self.width - 1]
        out.append(f"\033[2K\033[7m{status}\033[0m")

        cursor_screen_row = cursor_row - self.scroll_offset
        cursor_col = buffer.cursor.col
        screen_col = min(cursor_col + 5, self.width - 1)
        out.append(f"\033[{cursor_screen_row + 1};{screen_col + 1}H")

        sys.stdout.write("".join(out))
        sys.stdout.flush()

    def _resize(self):
        self.width = shutil.get_terminal_size().columns
        self.height = shutil.get_terminal_size().lines
