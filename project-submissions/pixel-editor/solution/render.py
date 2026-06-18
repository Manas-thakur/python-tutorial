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
    lines = [ANSI_CLEAR + ANSI_HOME]
    for y in range(grid.height):
        row = ''
        for x in range(grid.width):
            color = grid.get_pixel(x, y)
            is_cursor = (x == cursor_x and y == cursor_y)
            if color:
                r, g, b = hex_to_rgb(color)
                if is_cursor:
                    row += (
                        f'\033[38;2;{255-r};{255-g};{255-b}m'
                        f'\033[48;2;{r};{g};{b}m{CURSOR_BLOCK}'
                        f'{ANSI_RESET}'
                    )
                else:
                    row += f'\033[38;2;{r};{g};{b}m{FULL_BLOCK}{ANSI_RESET}'
            else:
                if is_cursor:
                    row += '\033[48;2;80;80;80m \033[0m'
                else:
                    row += ' '
        lines.append(row)
    for line in status_lines:
        lines.append(f'\033[K{line}')
    return '\n'.join(lines)
