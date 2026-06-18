from canvas import PixelGrid, hex_to_rgb, rgb_to_hex


def invert(grid: PixelGrid) -> PixelGrid:
    # TODO: Return a copy of the grid with every color channel inverted (255 - c)
    pass


def grayscale(grid: PixelGrid) -> PixelGrid:
    # TODO: Return a copy converted to grayscale using luminosity weights:
    # gray = 0.299*R + 0.587*G + 0.114*B
    pass


def brightness(grid: PixelGrid, factor: float = 1.2) -> PixelGrid:
    # TODO: Return a copy with each R/G/B channel multiplied by factor,
    # clamped to [0, 255]
    pass


def box_blur(grid: PixelGrid, radius: int = 2) -> PixelGrid:
    # TODO: Return a new grid where each pixel is the average of its
    # (radius*2+1) x (radius*2+1) neighborhood. Only process pixels
    # that exist in the original grid.
    pass


def edge_detect(grid: PixelGrid, threshold: int = 30) -> PixelGrid:
    # TODO: Apply Sobel edge detection. For each existing pixel,
    # convolve with sobel_x and sobel_y kernels. If the magnitude
    # exceeds threshold, set the pixel to the edge color.
    pass
