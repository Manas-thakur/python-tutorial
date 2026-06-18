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
        # TODO: Initialize layers, cursor position, tool index, color
        pass

    @property
    def current_color(self) -> str:
        # TODO: Return hex color string for current_color_key
        pass

    @property
    def current_tool(self) -> Tool:
        pass

    @property
    def active_layer(self):
        pass

    def composite(self) -> PixelGrid:
        pass

    def status_lines(self) -> list[str]:
        # TODO: Return [tool/color/layer info, palette bar, keybindings]
        pass

    def _palette_bar(self) -> str:
        # TODO: Build a string showing palette colors with current one highlighted
        pass

    def run(self) -> None:
        # TODO: Set up raw terminal, render loop, clean up on exit
        pass

    def _setup_terminal(self) -> None:
        pass

    def _cleanup_terminal(self) -> None:
        pass

    def _render(self) -> None:
        pass

    def _read_key(self) -> str | None:
        # TODO: Read a single keypress. Handle arrow key escape sequences.
        pass

    def _handle_key(self, key: str | None) -> None:
        # TODO: Dispatch key to movement, tool, color, layer, filter, or export
        pass

    def _apply_tool(self, active) -> None:
        # TODO: Apply the current tool at cursor position
        # Handle multi-click tools (Line, Rect) with start/end points
        pass

    def _merge_layer(self, active) -> None:
        pass

    def _apply_filter(self, filter_fn) -> None:
        pass


def main() -> None:
    # TODO: Create and run editor
    pass


if __name__ == '__main__':
    main()
