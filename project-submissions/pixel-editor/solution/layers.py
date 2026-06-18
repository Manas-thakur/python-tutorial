from canvas import PixelGrid


class Layer:
    def __init__(self, name: str, width: int, height: int):
        self.name = name
        self.grid = PixelGrid(width, height)
        self.visible = True
        self.opacity: float = 1.0


class LayerStack:
    def __init__(self):
        self.layers: list[Layer] = []

    def add(self, name: str, width: int, height: int, index: int | None = None) -> Layer:
        layer = Layer(name, width, height)
        if index is None:
            self.layers.append(layer)
        else:
            self.layers.insert(index, layer)
        return layer

    def remove(self, name: str) -> None:
        self.layers = [l for l in self.layers if l.name != name]

    def active(self) -> Layer | None:
        return self.layers[-1] if self.layers else None

    def composite(self) -> PixelGrid:
        if not self.layers:
            return PixelGrid(64, 32)
        ref = self.layers[0].grid
        result = PixelGrid(ref.width, ref.height)
        for layer in self.layers:
            if not layer.visible:
                continue
            for (x, y), color in layer.grid.pixels.items():
                result.set_pixel(x, y, color)
        return result
