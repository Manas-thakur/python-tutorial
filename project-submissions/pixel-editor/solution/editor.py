import os
import select
import sys
import termios
import tty

from canvas import PixelGrid, PALETTE, PALETTE_KEYS, hex_to_rgb
from export import export_ansi, export_ascii_art, export_html, export_svg
from filters import invert, grayscale, brightness, box_blur, edge_detect
from layers import LayerStack
from render import render_frame
from tools import (
    PenTool, EraserTool, LineTool, RectTool,
    FloodFillTool, EyedropperTool, Tool,
)

WIDTH = 64
HEIGHT = 32

TOOLS: list[Tool] = [
    PenTool(),
    EraserTool(),
    LineTool(),
    RectTool(),
    FloodFillTool(),
    EyedropperTool(),
]
TOOL_NAMES = ['Pen', 'Eraser', 'Line', 'Rect', 'Fill', 'Pick']


class Editor:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.layers = LayerStack()
        self.layers.add('Background', self.width, self.height)
        self.layers.add('Foreground', self.width, self.height)
        self.current_tool_idx = 0
        self.current_color_key = '7'
        self.cursor_x = self.width // 2
        self.cursor_y = self.height // 2
        self.line_start: tuple[int, int] | None = None
        self.rect_start: tuple[int, int] | None = None
        self.running = True

    @property
    def current_color(self) -> str:
        return PALETTE[self.current_color_key]

    @property
    def current_tool(self) -> Tool:
        return TOOLS[self.current_tool_idx]

    @property
    def active_layer(self):
        return self.layers.active()

    def composite(self) -> PixelGrid:
        return self.layers.composite()

    def status_lines(self) -> list[str]:
        tool_name = TOOL_NAMES[self.current_tool_idx]
        r, g, b = hex_to_rgb(self.current_color)
        active = self.active_layer
        layer_name = active.name if active else 'None'
        idx = self.layers.layers.index(active) if active in self.layers.layers else -1
        lines = [
            (
                f' Tool: {tool_name}  '
                f'Color: \033[38;2;{r};{g};{b}m\u2588\033[0m #{r:02x}{g:02x}{b:02x}  '
                f'Layer: {layer_name} [{idx + 1}/{len(self.layers.layers)}]  '
                f'Pos: ({self.cursor_x},{self.cursor_y})'
            ),
            self._palette_bar(),
            (
                ' [1-6]Tool  [0-9a-f]Color  Arrows:Move  Space:Draw  '
                '[/]Layer  H:hide  M:merge  C:clear  '
                'I:invert  G:gray  B:bright  U:blur  E:edge  '
                'O:ansi  P:html  S:svg  \x11:quit'
            ),
        ]
        return lines

    def _palette_bar(self) -> str:
        parts = [' Palette:']
        for k in PALETTE_KEYS:
            r, g, b = hex_to_rgb(PALETTE[k])
            block = f'\033[48;2;{r};{g};{b}m \033[0m'
            if k == self.current_color_key:
                parts.append(f'\033[7m{block}{k}\033[27m')
            else:
                parts.append(f'{block}{k}')
        return ' '.join(parts)

    def run(self) -> None:
        self._setup_terminal()
        try:
            sys.stdout.write('\033[?25l')
            sys.stdout.flush()
            self._render()
            while self.running:
                key = self._read_key()
                self._handle_key(key)
                self._render()
        finally:
            self._cleanup_terminal()

    def _setup_terminal(self) -> None:
        self._fd = sys.stdin.fileno()
        self._old = termios.tcgetattr(self._fd)
        tty.setraw(self._fd)

    def _cleanup_terminal(self) -> None:
        try:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old)
        except Exception:
            pass
        sys.stdout.write('\033[2J\033[H\033[?25h')
        sys.stdout.flush()

    def _render(self) -> None:
        grid = self.composite()
        status = self.status_lines()
        screen = render_frame(grid, self.cursor_x, self.cursor_y, status)
        sys.stdout.write(screen)
        sys.stdout.flush()

    def _read_key(self) -> str | None:
        raw = os.read(self._fd, 1)
        if not raw:
            return 'QUIT'
        ch = raw.decode('utf-8', errors='replace')
        if ch == '\x1b':
            if select.select([sys.stdin], [], [], 0.05)[0]:
                seq = os.read(self._fd, 2)
                if seq == b'[A':
                    return 'UP'
                elif seq == b'[B':
                    return 'DOWN'
                elif seq == b'[C':
                    return 'RIGHT'
                elif seq == b'[D':
                    return 'LEFT'
            return None
        if ch == '\x03':
            return 'QUIT'
        return ch

    def _handle_key(self, key: str | None) -> None:
        if key is None:
            return
        active = self.active_layer
        if not active:
            return
        if key == 'QUIT':
            self.running = False
            return
        if key == 'UP':
            self.cursor_y = max(0, self.cursor_y - 1)
        elif key == 'DOWN':
            self.cursor_y = min(self.height - 1, self.cursor_y + 1)
        elif key == 'LEFT':
            self.cursor_x = max(0, self.cursor_x - 1)
        elif key == 'RIGHT':
            self.cursor_x = min(self.width - 1, self.cursor_x + 1)
        elif key == ' ':
            self._apply_tool(active)
        elif key in '123456':
            self.current_tool_idx = int(key) - 1
            self.line_start = None
            self.rect_start = None
        elif key in PALETTE:
            self.current_color_key = key
        elif key == ']':
            if len(self.layers.layers) > 1:
                self.layers.layers.append(self.layers.layers.pop(0))
        elif key == '[':
            if len(self.layers.layers) > 1:
                self.layers.layers.insert(0, self.layers.layers.pop(-1))
        elif key == 'h':
            active.visible = not active.visible
        elif key == 'm':
            self._merge_layer(active)
        elif key == 'n':
            name = f'Layer {len(self.layers.layers) + 1}'
            self.layers.add(name, self.width, self.height)
        elif key == 'i':
            self._apply_filter(invert)
        elif key == 'g':
            self._apply_filter(grayscale)
        elif key == 'b':
            self._apply_filter(lambda g: brightness(g, 1.3))
        elif key == 'd':
            self._apply_filter(lambda g: brightness(g, 0.7))
        elif key == 'u':
            self._apply_filter(lambda g: box_blur(g, 2))
        elif key == 'e':
            self._apply_filter(edge_detect)
        elif key == 'o':
            text = export_ansi(self.composite())
            with open('output.ansi', 'w', encoding='utf-8') as f:
                f.write(text)
        elif key == 'a':
            text = export_ascii_art(self.composite())
            with open('output.txt', 'w', encoding='utf-8') as f:
                f.write(text)
        elif key == 'p':
            html = export_html(self.composite())
            with open('output.html', 'w', encoding='utf-8') as f:
                f.write(html)
        elif key == 's':
            svg = export_svg(self.composite())
            with open('output.svg', 'w', encoding='utf-8') as f:
                f.write(svg)
        elif key == 'c':
            active.grid.clear()

    def _apply_tool(self, active) -> None:
        tool = self.current_tool
        if isinstance(tool, LineTool):
            if self.line_start is None:
                self.line_start = (self.cursor_x, self.cursor_y)
            else:
                x1, y1 = self.line_start
                tool.apply(
                    active.grid, x1, y1,
                    self.cursor_x, self.cursor_y,
                    color=self.current_color,
                )
                self.line_start = None
        elif isinstance(tool, RectTool):
            if self.rect_start is None:
                self.rect_start = (self.cursor_x, self.cursor_y)
            else:
                x1, y1 = self.rect_start
                tool.apply(
                    active.grid, x1, y1,
                    self.cursor_x, self.cursor_y,
                    color=self.current_color,
                )
                self.rect_start = None
        elif isinstance(tool, EyedropperTool):
            picked = tool.apply(active.grid, self.cursor_x, self.cursor_y)
            if picked:
                for k, v in PALETTE.items():
                    if v == picked:
                        self.current_color_key = k
                        break
        elif isinstance(tool, FloodFillTool):
            tool.apply(active.grid, self.cursor_x, self.cursor_y, color=self.current_color)
        else:
            tool.apply(active.grid, self.cursor_x, self.cursor_y, color=self.current_color)

    def _merge_layer(self, active) -> None:
        if len(self.layers.layers) <= 1:
            return
        idx = self.layers.layers.index(active)
        if idx == 0:
            return
        below = self.layers.layers[idx - 1]
        for (x, y), color in active.grid.pixels.items():
            below.grid.set_pixel(x, y, color)
        self.layers.remove(active.name)

    def _apply_filter(self, filter_fn) -> None:
        composite = self.composite()
        filtered = filter_fn(composite)
        if self.active_layer:
            self.active_layer.grid.pixels = filtered.pixels


def main() -> None:
    editor = Editor()
    try:
        editor.run()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        sys.stdout.write('\033[2J\033[H\033[?25h')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
