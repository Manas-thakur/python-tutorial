from canvas import hex_to_rgb

ANSI_RESET = '\033[0m'
ANSI_CLEAR = '\033[2J'
ANSI_HOME = '\033[H'
FULL_BLOCK = '\u2588'
CURSOR_BLOCK = '\u2592'


def render_frame(
    grid: 'PixelGrid',
    cursor_x: int,
    cursor_y: int,
    status_lines: list[str],
) -> str:
    # TODO: Build a string that draws the full terminal frame:
    # 1. Clear screen and move cursor home
    # 2. For each row, for each column:
    #    - If the cell has a color, render a FULL_BLOCK in that color using ANSI
    #    - If the cursor is on this cell, use CURSOR_BLOCK with inverted colors
    #    - Empty cells are spaces
    # 3. Append each status line (with \033[K to clear to end of line)
    pass
