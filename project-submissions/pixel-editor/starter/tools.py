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
        # TODO: Set pixel at (x, y) to kwargs['color']
        pass


class EraserTool(Tool):
    def __init__(self):
        super().__init__('Eraser')

    def apply(self, grid: PixelGrid, x: int, y: int, **kwargs):
        # TODO: Remove pixel at (x, y) (set to None)
        pass


class LineTool(Tool):
    def __init__(self):
        super().__init__('Line')

    def apply(self, grid: PixelGrid, x1: int, y1: int, x2: int, y2: int, **kwargs):
        # TODO: Draw a line from (x1,y1) to (x2,y2) using Bresenham's algorithm
        pass


class RectTool(Tool):
    def __init__(self):
        super().__init__('Rectangle')

    def apply(self, grid: PixelGrid, x1: int, y1: int, x2: int, y2: int, **kwargs):
        # TODO: Draw a rectangle outline from (x1,y1) to (x2,y2).
        # If kwargs['fill'] is True, fill the interior too.
        pass


class FloodFillTool(Tool):
    def __init__(self):
        super().__init__('Flood Fill')

    def apply(self, grid: PixelGrid, x: int, y: int, **kwargs):
        # TODO: BFS flood fill: replace all adjacent pixels matching
        # the target color with kwargs['color']
        pass


class EyedropperTool(Tool):
    def __init__(self):
        super().__init__('Eyedropper')

    def apply(self, grid: PixelGrid, x: int, y: int, **kwargs):
        # TODO: Return the color at (x, y)
        pass
