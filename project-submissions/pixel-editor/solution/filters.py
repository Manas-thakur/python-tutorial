from canvas import PixelGrid, hex_to_rgb, rgb_to_hex


def invert(grid: PixelGrid) -> PixelGrid:
    result = grid.copy()
    for (x, y), color in list(result.pixels.items()):
        r, g, b = hex_to_rgb(color)
        result.set_pixel(x, y, rgb_to_hex(255 - r, 255 - g, 255 - b))
    return result


def grayscale(grid: PixelGrid) -> PixelGrid:
    result = grid.copy()
    for (x, y), color in list(result.pixels.items()):
        r, g, b = hex_to_rgb(color)
        gray = int(0.299 * r + 0.587 * g + 0.114 * b)
        result.set_pixel(x, y, rgb_to_hex(gray, gray, gray))
    return result


def brightness(grid: PixelGrid, factor: float = 1.2) -> PixelGrid:
    result = grid.copy()
    for (x, y), color in list(result.pixels.items()):
        r, g, b = hex_to_rgb(color)
        r = min(255, max(0, int(r * factor)))
        g = min(255, max(0, int(g * factor)))
        b = min(255, max(0, int(b * factor)))
        result.set_pixel(x, y, rgb_to_hex(r, g, b))
    return result


def box_blur(grid: PixelGrid, radius: int = 2) -> PixelGrid:
    result = PixelGrid(grid.width, grid.height)
    for (x, y), color in list(grid.pixels.items()):
        r_sum, g_sum, b_sum, count = 0, 0, 0, 0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                nc = grid.get_pixel(nx, ny)
                if nc:
                    r, g, b = hex_to_rgb(nc)
                    r_sum += r
                    g_sum += g
                    b_sum += b
                    count += 1
        if count > 0:
            result.set_pixel(
                x, y,
                rgb_to_hex(r_sum // count, g_sum // count, b_sum // count),
            )
    return result


def edge_detect(grid: PixelGrid, threshold: int = 30) -> PixelGrid:
    sobel_x = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    sobel_y = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    result = PixelGrid(grid.width, grid.height)
    for (x, y), _ in list(grid.pixels.items()):
        gx_r, gx_g, gx_b = 0, 0, 0
        gy_r, gy_g, gy_b = 0, 0, 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                nc = grid.get_pixel(nx, ny)
                if nc:
                    r, g, b = hex_to_rgb(nc)
                    sx = sobel_x[dx + 1][dy + 1]
                    sy = sobel_y[dx + 1][dy + 1]
                    gx_r += r * sx
                    gx_g += g * sx
                    gx_b += b * sx
                    gy_r += r * sy
                    gy_g += g * sy
                    gy_b += b * sy
        mag_r = min(int((gx_r ** 2 + gy_r ** 2) ** 0.5), 255)
        mag_g = min(int((gx_g ** 2 + gy_g ** 2) ** 0.5), 255)
        mag_b = min(int((gx_b ** 2 + gy_b ** 2) ** 0.5), 255)
        avg_mag = (mag_r + mag_g + mag_b) // 3
        if avg_mag > threshold:
            result.set_pixel(x, y, rgb_to_hex(mag_r, mag_g, mag_b))
    return result
