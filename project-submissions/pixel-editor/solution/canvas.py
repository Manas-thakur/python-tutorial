HEX_DIGITS = '0123456789abcdef'

PALETTE = {
    '0': '#000000', '1': '#FF0000', '2': '#00FF00', '3': '#FFFF00',
    '4': '#0000FF', '5': '#FF00FF', '6': '#00FFFF', '7': '#FFFFFF',
    '8': '#808080', '9': '#FF8800', 'a': '#AA00FF', 'b': '#00FFAA',
    'c': '#FF0066', 'd': '#0088FF', 'e': '#885500', 'f': '#FFFF88',
}

PALETTE_KEYS = list(PALETTE.keys())


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip('#')
    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f'#{r:02x}{g:02x}{b:02x}'


class PixelGrid:
    def __init__(self, width: int = 64, height: int = 32):
        self.width = width
        self.height = height
        self.pixels: dict[tuple[int, int], str] = {}

    def set_pixel(self, x: int, y: int, color: str | None) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            if color is None:
                self.pixels.pop((x, y), None)
            else:
                self.pixels[(x, y)] = color

    def get_pixel(self, x: int, y: int) -> str | None:
        return self.pixels.get((x, y))

    def clear(self) -> None:
        self.pixels.clear()

    def fill(self, color: str) -> None:
        for y in range(self.height):
            for x in range(self.width):
                self.pixels[(x, y)] = color

    def copy(self) -> 'PixelGrid':
        new = PixelGrid(self.width, self.height)
        new.pixels = dict(self.pixels)
        return new
