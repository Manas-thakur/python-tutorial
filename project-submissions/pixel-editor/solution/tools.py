from abc import ABC, abstractmethod
from collections import deque

from canvas import PixelGrid


class Tool(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def apply(self, grid: PixelGrid, x: int, y: int, **kwargs):
        pass


class PenTool(Tool):
    def __init__(self):
        super().__init__('Pen')

    def apply(self, grid: PixelGrid, x: int, y: int, **kwargs):
        color = kwargs.get('color')
        if color:
            grid.set_pixel(x, y, color)


class EraserTool(Tool):
    def __init__(self):
        super().__init__('Eraser')

    def apply(self, grid: PixelGrid, x: int, y: int, **kwargs):
        grid.set_pixel(x, y, None)


class LineTool(Tool):
    def __init__(self):
        super().__init__('Line')

    def apply(self, grid: PixelGrid, x1: int, y1: int, x2: int, y2: int, **kwargs):
        color = kwargs.get('color')
        if not color:
            return
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        x, y = x1, y1
        while True:
            grid.set_pixel(x, y, color)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy


class RectTool(Tool):
    def __init__(self):
        super().__init__('Rectangle')

    def apply(self, grid: PixelGrid, x1: int, y1: int, x2: int, y2: int, **kwargs):
        color = kwargs.get('color')
        fill = kwargs.get('fill', False)
        if not color:
            return
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        for x in range(x_min, x_max + 1):
            grid.set_pixel(x, y_min, color)
            grid.set_pixel(x, y_max, color)
        for y in range(y_min, y_max + 1):
            grid.set_pixel(x_min, y, color)
            grid.set_pixel(x_max, y, color)
        if fill:
            for y in range(y_min + 1, y_max):
                for x in range(x_min + 1, x_max):
                    grid.set_pixel(x, y, color)


class FloodFillTool(Tool):
    def __init__(self):
        super().__init__('Flood Fill')

    def apply(self, grid: PixelGrid, x: int, y: int, **kwargs):
        fill_color = kwargs.get('color')
        if not fill_color:
            return
        target = grid.get_pixel(x, y)
        if target == fill_color:
            return
        queue = deque()
        queue.append((x, y))
        while queue:
            cx, cy = queue.popleft()
            if grid.get_pixel(cx, cy) != target:
                continue
            grid.set_pixel(cx, cy, fill_color)
            for nx, ny in (
                (cx + 1, cy), (cx - 1, cy),
                (cx, cy + 1), (cx, cy - 1),
            ):
                if 0 <= nx < grid.width and 0 <= ny < grid.height:
                    queue.append((nx, ny))


class EyedropperTool(Tool):
    def __init__(self):
        super().__init__('Eyedropper')

    def apply(self, grid: PixelGrid, x: int, y: int, **kwargs):
        return grid.get_pixel(x, y)
