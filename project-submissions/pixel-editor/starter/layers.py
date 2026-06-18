from canvas import PixelGrid


class Layer:
    def __init__(self, name: str, width: int, height: int):
        # TODO: Store name, create a PixelGrid, set visible=True, opacity=1.0
        pass


class LayerStack:
    def __init__(self):
        # TODO: Initialize an empty list of layers
        pass

    def add(self, name: str, width: int, height: int, index: int | None = None) -> Layer:
        # TODO: Create a new Layer, insert it at the given index
        # (or append if index is None). Return the layer.
        pass

    def remove(self, name: str) -> None:
        # TODO: Remove the layer with the given name
        pass

    def active(self) -> Layer | None:
        # TODO: Return the topmost (last) layer, or None
        pass

    def composite(self) -> PixelGrid:
        # TODO: Merge all visible layers into one PixelGrid.
        # Pixels from higher layers overwrite those from lower layers.
        pass
