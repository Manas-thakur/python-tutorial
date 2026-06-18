from python_tutorial.models import ProjectTutorial, Section

TUTORIAL = ProjectTutorial(
    slug="pixel-editor",
    title="Build a Pixel Art Editor",
    description="A terminal-based ASCII art and pixel editor with drawing tools, layers, filters, and multiple export formats.",
    difficulty="intermediate",
    project_dir="pixel-editor",
    prerequisites=["Functions", "Classes", "2D arrays"],
    steps=[
        Section(
            heading="Step 1: Architecture Overview",
            content="""\
Let's start by looking at how the pixel editor is wired together. Open the project directory — six modules form the core of the editor.

```
project/
├── canvas.py    # 2D pixel grid data structure
├── tools.py     # Drawing tools (pen, line, rect, flood fill, eyedropper)
├── layers.py    # Layer composition and blending
├── filters.py   # Image effects (blur, edge detect, color transforms)
├── formats.py   # Import/export (ASCII art, HTML, SVG)
└── editor.py    # Main event loop, ties everything together
```

**Data flow** in a single stroke:

```
┌──────────┐   event   ┌──────────┐   draw    ┌────────┐   render   ┌──────────┐
│  editor  │──────────► │  tools   │──────────► │ canvas │──────────► │ terminal │
│ .run()   │            │ .apply() │            │        │            │ .draw()  │
└──────────┘            └──────────┘            └────────┘            └──────────┘
     │                                               │
     │                                           composite
     │                                               ▼
     │                                         ┌──────────┐
     └─────────────────────────────────────────► │  layers  │
                                                 └──────────┘
```

The `editor.py` `run()` method looks like this:

```python
def run(self):
    self.canvas = Canvas(64, 32)
    self.layers = LayerStack()
    self.layers.add(Layer("background", Canvas(64, 32)))
    self.layers.add(Layer("foreground", Canvas(64, 32)))
    self.tool = PenTool()
    while True:
        self.render()
        event = self.read_event()
        if event.type == "QUIT":
            break
        elif event.type == "KEY":
            self._handle_key(event)
        elif event.type == "MOUSE":
            self.tool.apply(self.layers.active().canvas, event.x, event.y)
```

Each module owns one concern: `canvas` stores raw pixels, `tools` mutates canvas data, `layers` composites multiple canvases into one result, `filters` transform the composited image, and `formats` serialize it. The editor loop never touches pixel data directly — it delegates to the tool. This separation makes each piece independently testable and swappable.
""",
        ),
        Section(
            heading="Step 2: The Canvas (canvas.py)",
            content="""\
Open `canvas.py`. The `Canvas` class is a sparse 2D pixel grid backed by a dictionary.

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Canvas:
    width: int
    height: int
    pixels: dict[tuple[int, int], str] = field(default_factory=dict)

    def set_pixel(self, x: int, y: int, color: str) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[(x, y)] = color

    def get_pixel(self, x: int, y: int) -> Optional[str]:
        return self.pixels.get((x, y))

    def clear(self) -> None:
        self.pixels.clear()
```

**Why a dict instead of a 2D list?** A 2D list `grid[y][x] = color` allocates every cell upfront — a 100×100 canvas stores 10,000 entries even if only 10 pixels are drawn. A dict stores only the keys that have been set, making it **sparse**. Missing keys automatically represent the background (transparent), so `get_pixel` returns `None` for untouched cells. This matters for layers — a 1024×768 canvas with a small doodle in the corner uses kilobytes instead of megabytes.

**Dry run: `set_pixel(5, 10, "red")`.**

Before: `pixels = {}`

```
canvas.pixels[(5, 10)] = "red"
```

Now: `pixels = {(5, 10): "red"}`. The dict has exactly one entry. Calling `get_pixel(5, 10)` returns `"red"`; `get_pixel(0, 0)` returns `None`.

**Dry run: `render()` walks the grid bounds.**

```python
def render(self) -> list[list[Optional[str]]]:
    grid = [[None] * self.width for _ in range(self.height)]
    for (x, y), color in self.pixels.items():
        grid[y][x] = color
    return grid
```

This rebuilds a dense grid from the sparse dict each render cycle. For a 64×32 canvas with 100 painted pixels, it iterates 100 dict entries and fills a 2048-cell grid. The untouched cells stay `None`, which the renderer treats as the terminal's background color.
""",
        ),
        Section(
            heading="Step 3: Drawing Tools (tools.py)",
            content="""\
Open `tools.py`. Each tool is a class with an `apply` method that mutates the canvas.

```python
from abc import ABC, abstractmethod
from canvas import Canvas

class Tool(ABC):
    @abstractmethod
    def apply(self, canvas: Canvas, x: int, y: int, **kwargs) -> None:
        ...

class PenTool(Tool):
    def apply(self, canvas: Canvas, x: int, y: int, **kwargs) -> None:
        color = kwargs.get("color", "white")
        canvas.set_pixel(x, y, color)

class RectTool(Tool):
    def apply(self, canvas: Canvas, x1: int, y1: int, x2: int, y2: int, **kwargs) -> None:
        color = kwargs.get("color", "white")
        fill = kwargs.get("fill", False)
        for x in range(min(x1, x2), max(x1, x2) + 1):
            canvas.set_pixel(x, y1, color)
            canvas.set_pixel(x, y2, color)
        for y in range(min(y1, y2), max(y1, y2) + 1):
            canvas.set_pixel(x1, y, color)
            canvas.set_pixel(x2, y, color)
        if fill:
            for y in range(min(y1, y2) + 1, max(y1, y2)):
                for x in range(min(x1, x2) + 1, max(x1, x2)):
                    canvas.set_pixel(x, y, color)
```

**LineTool and Bresenham's algorithm.**

```python
class LineTool(Tool):
    def apply(self, canvas: Canvas, x1: int, y1: int, x2: int, y2: int, **kwargs) -> None:
        color = kwargs.get("color", "white")
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        x, y = x1, y1
        while True:
            canvas.set_pixel(x, y, color)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy
```

**Dry run: LineTool draws from (1,1) to (5,3).**

Initial state: `dx = 4`, `dy = -2`, `sx = 1`, `sy = 1`, `err = 4 + (-2) = 2`.

| Step | x | y | err | e2 | Pixel set |
|------|---|---|-----|----|-----------|
| 0 | 1 | 1 | 2 | 4 | (1,1) |
| 1 | 2 | 1 | -2 | — | (2,1) |
| 2 | 2 | 2 | 2 | 4 | (2,2) |
| 3 | 3 | 2 | -2 | — | (3,2) |
| 4 | 3 | 3 | 2 | — | (3,3) |
| 5 | 4 | 3 | 2 | — | (4,3) |
| 6 | 5 | 3 | — | — | (5,3) |

The path at each step moves either x or y (or both) depending on the error term, producing a clean diagonal line: `(1,1) → (2,2) → (3,3) → (4,3) → (5,3)`.

**Why Bresenham?** It uses only integer addition, subtraction, and bit shifts — no floating-point division or `sqrt`. This makes it extremely fast on embedded terminals and guarantees pixel-perfect straight lines without aliasing artifacts.

**FloodFillTool (BFS) and EyedropperTool** follow the same pattern:

```python
class EyedropperTool(Tool):
    def apply(self, canvas: Canvas, x: int, y: int, **kwargs) -> str | None:
        return canvas.get_pixel(x, y)
```

The eyedropper returns the color under the cursor instead of drawing — the editor can then set this as the active drawing color.
""",
        ),
        Section(
            heading="Step 4: Flood Fill Algorithm (FloodFillTool)",
            content="""\
The flood fill tool replaces a contiguous region of one color with another. It's the "paint bucket" in every graphics editor.

```python
from collections import deque

class FloodFillTool(Tool):
    def apply(self, canvas: Canvas, x: int, y: int, **kwargs) -> None:
        fill_color = kwargs["color"]
        target_color = canvas.get_pixel(x, y)
        if target_color == fill_color:
            return
        queue = deque()
        queue.append((x, y))
        while queue:
            cx, cy = queue.popleft()
            if canvas.get_pixel(cx, cy) != target_color:
                continue
            canvas.set_pixel(cx, cy, fill_color)
            for nx, ny in [(cx + 1, cy), (cx - 1, cy),
                           (cx, cy + 1), (cx, cy - 1)]:
                if 0 <= nx < canvas.width and 0 <= ny < canvas.height:
                    queue.append((nx, ny))
```

**Dry run: Flood fill at (5,5) with "blue" on a red shape.**

Imagine a 10×10 canvas with a red rectangle covering (2,2) through (8,8) and the rest empty (`None`). The user clicks at (5,5) — inside the red shape.

1. `target_color = "red"`, `fill_color = "blue"`. The colors differ, so we continue.
2. Queue starts with `[(5, 5)]`.
3. Pop (5,5): pixel is `"red"` → set to `"blue"`. Push neighbors (6,5), (4,5), (5,6), (5,4). Queue: `[(6,5), (4,5), (5,6), (5,4)]`.
4. Pop (6,5): pixel is `"red"` → set to `"blue"`. Push neighbors.
5. The BFS continues, spreading outward in all four directions.
6. When the queue reaches the edge of the rectangle at (8, y) or (x, 2), those neighbor pixels are `None` (background) or a different color, so the `get_pixel` check skips them — the fill stops at the red boundary.

After completion, every red pixel reachable from (5,5) without crossing a non-red border is now blue. The fill stops precisely at the rectangle edges.

**Why BFS instead of DFS?** A recursive DFS (flood-fill via function calls) would work for small images:
```python
def dfs_fill(canvas, x, y, target, fill):
    if canvas.get_pixel(x, y) != target:
        return
    canvas.set_pixel(x, y, fill)
    for nx, ny in neighbors:
        dfs_fill(canvas, nx, ny, target, fill)
```

But a 100×100 fill could recurse 10,000 levels deep — Python's default recursion limit is 1000, and each call consumes a stack frame. A **BFS using `collections.deque`** uses O(width) memory for the queue (the maximum frontier width) instead of O(pixels) stack frames, and it avoids recursion entirely. The `popleft()` guarantees we process in expanding rings, which is also the behavior users expect — the fill appears to grow outward evenly.
""",
        ),
        Section(
            heading="Step 5: Layer System (layers.py)",
            content="""\
Open `layers.py`. Layers let you compose multiple canvases independently, like stacking transparencies on an overhead projector.

```python
from dataclasses import dataclass, field
from canvas import Canvas

@dataclass
class Layer:
    name: str
    canvas: Canvas
    visible: bool = True
    opacity: float = 1.0  # 0.0 (transparent) to 1.0 (opaque)


class LayerStack:
    def __init__(self):
        self.layers: list[Layer] = []

    def add(self, layer: Layer, index: int | None = None) -> None:
        if index is None:
            self.layers.append(layer)
        else:
            self.layers.insert(index, layer)

    def remove(self, name: str) -> None:
        self.layers = [l for l in self.layers if l.name != name]

    def merge_down(self, name: str) -> None:
        idx = next(i for i, l in enumerate(self.layers) if l.name == name)
        if idx == 0:
            return
        above = self.layers[idx]
        below = self.layers[idx - 1]
        for (x, y), color in above.canvas.pixels.items():
            below.canvas.set_pixel(x, y, color)
        self.remove(above.name)

    def reorder(self, name: str, new_index: int) -> None:
        layer = next(l for l in self.layers if l.name == name)
        self.layers.remove(layer)
        self.layers.insert(new_index, layer)

    def active(self) -> Layer:
        return self.layers[-1]
```

**Composite — the core of the layer system.**

```python
def composite(self) -> Canvas:
    result = Canvas(self.layers[0].canvas.width,
                    self.layers[0].canvas.height)
    for layer in self.layers:
        if not layer.visible:
            continue
        for (x, y), color in layer.canvas.pixels.items():
            if layer.opacity >= 1.0:
                result.set_pixel(x, y, color)
            elif layer.opacity > 0.0:
                existing = result.get_pixel(x, y)
                if existing is None or existing == "black":
                    result.set_pixel(x, y, color)
                # In a full implementation, blend based on opacity
    return result
```

**Dry run: Composite three layers.**

Layer setup:
- Layer "sky" (bottom, visible, opacity 1.0): blue pixel at (5, 5)
- Layer "sun" (middle, visible, opacity 0.5): yellow pixel at (5, 5)
- Layer "cloud" (top, visible, opacity 1.0): white pixel at (7, 7)

Composite walks top-to-bottom (cloud → sun → sky):

1. Start: empty result canvas.
2. Layer "cloud": set (7,7) = white. Result has white at (7,7).
3. Layer "sun": set (5,5) = yellow. Result has yellow at (5,5).
4. Layer "sky": set (5,5) is already yellow, so it stays yellow. Blue from sky was overwritten by sun above.

If "cloud" were hidden (`visible = False`), the composite would skip it entirely — the white pixel at (7,7) would not appear, showing whatever is underneath at that coordinate.

**Why layers?** Non-destructive editing — you can draw on a foreground layer without affecting the background. Mistakes live in a single layer; delete or hide it instead of undoing 50 strokes. Artists separate line art, flat colors, shading, and highlights into different layers, then toggle visibility to preview combinations.
""",
        ),
        Section(
            heading="Step 6: Image Filters (filters.py)",
            content="""\
Open `filters.py`. Filters transform the composited canvas pixel by pixel. Each filter is a function that takes a canvas and returns a new canvas.

```python
from canvas import Canvas

def invert(canvas: Canvas) -> Canvas:
    result = Canvas(canvas.width, canvas.height)
    for (x, y), color in canvas.pixels.items():
        result.set_pixel(x, y, _invert_color(color))
    return result

def grayscale(canvas: Canvas) -> Canvas:
    result = Canvas(canvas.width, canvas.height)
    for (x, y), color in canvas.pixels.items():
        result.set_pixel(x, y, _to_grayscale(color))
    return result

def brightness(canvas: Canvas, factor: float) -> Canvas:
    result = Canvas(canvas.width, canvas.height)
    for (x, y), color in canvas.pixels.items():
        result.set_pixel(x, y, _adjust_brightness(color, factor))
    return result

def contrast(canvas: Canvas, factor: float) -> Canvas:
    result = Canvas(canvas.width, canvas.height)
    for (x, y), color in canvas.pixels.items():
        result.set_pixel(x, y, _adjust_contrast(color, factor))
    return result
```

**Box blur.**

```python
def box_blur(canvas: Canvas, radius: int = 3) -> Canvas:
    result = Canvas(canvas.width, canvas.height)
    for (x, y) in canvas.pixels:
        r_sum, g_sum, b_sum, count = 0, 0, 0, 0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                color = canvas.get_pixel(nx, ny)
                if color:
                    r, g, b = _parse_color(color)
                    r_sum += r
                    g_sum += g
                    b_sum += b
                    count += 1
        if count > 0:
            avg = _rgb(r_sum // count, g_sum // count, b_sum // count)
            result.set_pixel(x, y, avg)
    return result
```

**Dry run: Box blur with radius 3 on a 3×3 red square at (5,5).**

The pixel at (5,5) is red (`#FF0000`). Radius 3 means a 7×7 neighborhood (from x-3 to x+3, y-3 to y+3). The neighborhood includes:
- Red pixels from the square at (4,4), (4,5), (5,4), (5,5), (5,6), (6,5), (6,6)
- Empty pixels (None) elsewhere in the 7×7 block

The 7×7 area has 49 cells. Say 7 are red and 42 are empty. The empty cells contribute nothing to the sum, so `r_sum = 7 * 255 = 1785`, `count = 7`. The averaged pixel has `r = 1785 // 7 = 255`, remaining channels 0, so it stays pure red — the center of a solid block doesn't change.

But take edge pixel (4,4) — its neighborhood has fewer red neighbors (about 4), so `r_sum = 4 * 255 = 1020`, `count = 4`, giving `r = 255`. The corner at (3,3) might have only 1 red neighbor, giving `r = 255 // 1 = 255` — still red. The blur effect is subtle on solid shapes; it's most visible on gradients and edges where the average pulls colors toward their surroundings.

**Edge detect (Sobel).**

```python
def edge_detect(canvas: Canvas) -> Canvas:
    sobel_x = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    sobel_y = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    result = Canvas(canvas.width, canvas.height)
    for (x, y), color in canvas.pixels.items():
        gx = _convolve(canvas, x, y, sobel_x)
        gy = _convolve(canvas, x, y, sobel_y)
        magnitude = min(int((gx ** 2 + gy ** 2) ** 0.5), 255)
        if magnitude > 30:
            result.set_pixel(x, y, _rgb(magnitude, magnitude, magnitude))
    return result
```

**Why box blur instead of Gaussian?** Box blur is the simplest blur — it just averages a square neighborhood. It's O(n × r²) per pixel (naive) but can be optimized to O(n) per pixel using integral images or two-pass row/column separation. Despite being "worse" than Gaussian (it creates some aliasing), it's educational, trivially implementable, and good enough for pixel art where the grid is already coarse.
""",
        ),
        Section(
            heading="Step 7: Export Formats (formats.py)",
            content="""\
Open `formats.py`. The exporter serializes the canvas into different output formats.

```python
from canvas import Canvas

ASCII_CHARS = "@%#*+=-:. "

def export_ascii(canvas: Canvas) -> str:
    lines = []
    for y in range(canvas.height):
        row = []
        for x in range(canvas.width):
            color = canvas.get_pixel(x, y)
            if color is None:
                row.append(" ")
            else:
                brightness = _luminance(color)
                idx = int(brightness / 255 * (len(ASCII_CHARS) - 1))
                row.append(ASCII_CHARS[idx])
        lines.append("".join(row))
    return "\n".join(lines)

def export_html(canvas: Canvas) -> str:
    cells = []
    for y in range(canvas.height):
        for x in range(canvas.width):
            color = canvas.get_pixel(x, y)
            bg = color if color else "#000"
            cells.append(
                f'<td style="background:{bg};width:10px;height:10px;"></td>'
            )
        cells.append("</tr><tr>")
    return (
        "<table><tr>"
        + "".join(cells)
        + "</tr></table>"
    )

def export_svg(canvas: Canvas, cell_size: int = 10) -> str:
    rects = []
    for (x, y), color in canvas.pixels.items():
        rects.append(
            f'<rect x="{x * cell_size}" y="{y * cell_size}" '
            f'width="{cell_size}" height="{cell_size}" fill="{color}" />'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{canvas.width * cell_size}" '
        f'height="{canvas.height * cell_size}">\n'
        + "\n".join(rects)
        + "\n</svg>"
    )
    return svg
```

**Dry run: `export_ascii()` on a canvas with a white pixel at (0,0).**

The canvas is 5×5 with one white pixel (`#FFFFFF`) at (0,0). `_luminance("#FFFFFF")` computes:
```
0.2126 * 255 + 0.7152 * 255 + 0.0722 * 255 = 255
```
Index = `int(255 / 255 * 9) = 8`. `ASCII_CHARS[8] = "."`. Every other cell is empty → space.

Output:
```
.    
     
     
     
     
```

If the pixel were dim red (`#440000`), luminance might be `~29`, index = `int(29 / 255 * 9) = 1`, mapping to `ASCII_CHARS[1] = "%"` — a denser character for a darker pixel.

**Why multiple formats?** ASCII art renders in any terminal without special fonts — it's the lowest common denominator. HTML tables work in browsers and emails. SVG is resolution-independent, scales cleanly, and can be embedded in web pages or edited in vector tools. Each format serves a different consumption context, and because the canvas data structure is decoupled from rendering, adding a new format (e.g., PNG via Pillow) is just another function.
""",
        ),
        Section(
            heading="Step 8: Running and Extensions",
            content="""\
To start the pixel art editor, run the project from its directory:

```bash
cd pixel-editor
python editor.py
```

This launches an interactive terminal session. Here are the default controls wired in `editor.py`:

| Key / Action | Behavior |
|---|---|
| Mouse click | Draw with current tool |
| `1`–`5` | Switch tool (pen, line, rect, flood fill, eyedropper) |
| `[` / `]` | Cycle active layer |
| `H` | Toggle layer visibility |
| `M` | Merge layer down |
| `I` | Invert colors filter |
| `G` | Grayscale filter |
| `B` | Box blur filter |
| `E` | Edge detect filter |
| `A` | Export ASCII art (prints to terminal) |
| `S` | Export SVG (saves to file) |
| `C` | Clear active layer |
| `Ctrl-Q` | Quit |

**What to try next — extension ideas:**

**Animation frames.** Treat each frame as a full `LayerStack`. Add a timeline that plays frames at a configurable FPS:

```python
class Animation:
    def __init__(self):
        self.frames: list[LayerStack] = []
        self.current_frame = 0
        self.fps = 8

    def next_frame(self) -> LayerStack:
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        return self.frames[self.current_frame]
```

Export as an animated GIF (using the `images` library) or as a spritesheet (render all frames side-by-side on a single canvas).

**Palette management.** Instead of arbitrary hex colors, constrain the editor to a fixed palette (e.g., the PICO-8 16-color palette or the ANSI terminal 256 colors). Store the palette as a list of color strings and map pixel values to palette indices:

```python
PICO8 = ["#000000", "#1D2B53", "#7E2553", "#008751",
         "#AB5236", "#5F574F", "#C2C3C7", "#FFF1E8",
         "#FF004D", "#FFA300", "#FFEC27", "#00E436",
         "#29ADFF", "#83769C", "#FF77A8", "#FFCCAA"]

class PaletteCanvas(Canvas):
    def __init__(self, width, height, palette):
        super().__init__(width, height)
        self.palette = palette

    def set_pixel(self, x, y, color_index: int) -> None:
        if 0 <= color_index < len(self.palette):
            super().set_pixel(x, y, self.palette[color_index])
```

**Collaborative editing.** Add a networking layer using `socket` or `websockets` that broadcasts pixel changes to connected clients. Each `set_pixel` call becomes a message:

```python
def apply_remote(self, x, y, color):
    self.canvas.set_pixel(x, y, color)
    self.broadcast({"type": "pixel", "x": x, "y": y, "color": color})
```

Use a CRDT (Conflict-free Replicated Data Type) to handle concurrent edits — since pixel writes are idempotent (setting the same pixel twice just overwrites), the last write wins naturally.

**PNG import with Pillow.** Use the `Pillow` library to load real images onto the canvas:

```python
from PIL import Image

def import_png(path: str, canvas: Canvas) -> None:
    img = Image.open(path).convert("RGB")
    img = img.resize((canvas.width, canvas.height))
    for y in range(canvas.height):
        for x in range(canvas.width):
            r, g, b = img.getpixel((x, y))
            canvas.set_pixel(x, y, _rgb(r, g, b))
```

This turns the pixel editor into a real image converter — draw by hand or import photos and apply filters, then export as ASCII art or SVG. The architecture you've built handles all of these without changing the core modules.
""",
        ),
    ],
)
