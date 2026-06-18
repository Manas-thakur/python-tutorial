HEX_DIGITS = '0123456789abcdef'

PALETTE = {
    '0': '#000000', '1': '#FF0000', '2': '#00FF00', '3': '#FFFF00',
    '4': '#0000FF', '5': '#FF00FF', '6': '#00FFFF', '7': '#FFFFFF',
    '8': '#808080', '9': '#FF8800', 'a': '#AA00FF', 'b': '#00FFAA',
    'c': '#FF0066', 'd': '#0088FF', 'e': '#885500', 'f': '#FFFF88',
}

PALETTE_KEYS = list(PALETTE.keys())


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    # TODO: Parse hex color string like '#FF00AA' into (255, 0, 170)
    pass


def rgb_to_hex(r: int, g: int, b: int) -> str:
    # TODO: Convert (255, 0, 170) into '#ff00aa'
    pass


class PixelGrid:
    def __init__(self, width: int = 64, height: int = 32):
        # TODO: Store width, height, and initialize a dict for pixels
        pass

    def set_pixel(self, x: int, y: int, color: str | None) -> None:
        # TODO: Set pixel at (x, y) to color if inside bounds.
        # If color is None, remove the key from the dict.
        pass

    def get_pixel(self, x: int, y: int) -> str | None:
        # TODO: Return the color at (x, y), or None if unset
        pass

    def clear(self) -> None:
        # TODO: Remove all pixels
        pass

    def fill(self, color: str) -> None:
        # TODO: Fill every cell with the given color
        pass

    def copy(self) -> 'PixelGrid':
        # TODO: Return a deep copy of this grid
        pass
