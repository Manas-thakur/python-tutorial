from canvas import PixelGrid, hex_to_rgb, rgb_to_hex

ASCII_CHARS = '@%#*+=-:. '


def luminance(hex_color: str) -> int:
    r, g, b = hex_to_rgb(hex_color)
    return int(0.2126 * r + 0.7152 * g + 0.0722 * b)


def export_ansi(grid: PixelGrid) -> str:
    lines = []
    for y in range(grid.height):
        row = []
        for x in range(grid.width):
            color = grid.get_pixel(x, y)
            if color:
                r, g, b = hex_to_rgb(color)
                row.append(f'\033[48;2;{r};{g};{b}m \033[0m')
            else:
                row.append(' ')
        lines.append(''.join(row))
    return '\n'.join(lines)


def export_ascii_art(grid: PixelGrid) -> str:
    lines = []
    for y in range(grid.height):
        row = []
        for x in range(grid.width):
            color = grid.get_pixel(x, y)
            if color is None:
                row.append(' ')
            else:
                lum = luminance(color)
                idx = int(lum / 255 * (len(ASCII_CHARS) - 1))
                row.append(ASCII_CHARS[idx])
        lines.append(''.join(row))
    return '\n'.join(lines)


def export_html(grid: PixelGrid, cell_size: int = 10) -> str:
    cells = []
    for y in range(grid.height):
        for x in range(grid.width):
            color = grid.get_pixel(x, y)
            bg = color if color else '#111'
            cells.append(
                f'<td style="background:{bg};'
                f'width:{cell_size}px;height:{cell_size}px;"></td>',
            )
        cells.append('</tr><tr>')
    html = (
        '<table style="border-collapse:collapse;"><tr>'
        + ''.join(cells)
        + '</tr></table>'
    )
    return html


def export_svg(grid: PixelGrid, cell_size: int = 8) -> str:
    rects = []
    for (x, y), color in grid.pixels.items():
        rects.append(
            f'<rect x="{x * cell_size}" y="{y * cell_size}" '
            f'width="{cell_size}" height="{cell_size}" fill="{color}" />',
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{grid.width * cell_size}" '
        f'height="{grid.height * cell_size}">\n'
        + '\n'.join(rects)
        + '\n</svg>'
    )
    return svg
