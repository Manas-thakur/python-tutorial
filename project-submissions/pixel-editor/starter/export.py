from canvas import PixelGrid, hex_to_rgb

ASCII_CHARS = '@%#*+=-:. '


def luminance(hex_color: str) -> int:
    # TODO: Compute perceived luminance: 0.2126*R + 0.7152*G + 0.0722*B
    pass


def export_ansi(grid: PixelGrid) -> str:
    # TODO: Render grid as ANSI-colored text (each pixel = colored space)
    pass


def export_ascii_art(grid: PixelGrid) -> str:
    # TODO: Render grid as ASCII art, mapping luminance to ASCII_CHARS
    pass


def export_html(grid: PixelGrid, cell_size: int = 10) -> str:
    # TODO: Render grid as an HTML table with colored cells
    pass


def export_svg(grid: PixelGrid, cell_size: int = 8) -> str:
    # TODO: Render grid as an SVG with colored rect elements
    pass
