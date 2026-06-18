---
title: Build a Pixel Art Editor
description: Create a terminal-based pixel art editor with drawing tools, layers, filters, and multiple export formats — all using only the Python standard library.
prerequisites:
  - Functions
  - Classes
  - 2D arrays
tags:
  - python
  - intermediate
  - creative
  - terminal
  - graphics
---

# Build a Pixel Art Editor

## Introduction

In this project you'll build a **terminal-based pixel art editor** — think Microsoft Paint running in your terminal, but with layers, filters, and multiple export formats. You'll draw pixels using ANSI-colored block characters, paint with a palette of 16 colors, draw lines and rectangles, flood-fill regions, stack layers, apply image filters, and export your artwork as ANSI art, ASCII art, HTML, or SVG.

Here's what you'll learn:

- **Sparse 2D data structures** — storing pixels in a dict instead of a full grid
- **ANSI escape codes** — rendering colored text in the terminal without curses
- **Bresenham's line algorithm** — integer-only line drawing
- **BFS flood fill** — the paint bucket algorithm
- **Layer compositing** — stacking transparent canvases
- **Image processing** — convolution, color transforms, edge detection
- **Raw terminal I/O** — reading keypresses one at a time

The entire project uses **zero external dependencies**. No PIL, no numpy, no curses. Every pixel is a hex string in a Python dict, and every frame is printed with ANSI escape codes.

## Setup

Create a new directory for your project:

```bash
mkdir pixel-editor
cd pixel-editor
```

You'll create seven files:

```
pixel-editor/
├── canvas.py    # 2D pixel grid data structure
├── render.py    # ANSI terminal rendering
├── tools.py     # Drawing tools (pen, eraser, line, rect, fill, eyedropper)
├── layers.py    # Layer stack and compositing
├── filters.py   # Image filters (invert, grayscale, brightness, blur, edge)
├── export.py    # Export as ANSI, ASCII, HTML, SVG
└── editor.py    # Main interactive loop
```

Each file builds on the ones before it. Start with `canvas.py` — the data core — and work your way up to `editor.py` which ties everything together.

---

## Step 1: Canvas Model (`canvas.py`)

The canvas is a **sparse 2D grid of pixels**. Instead of allocating a `list[list[str]]` for every cell (which would waste memory on blank canvases), we store only the pixels that have been painted, using a dictionary keyed by `(x, y)` tuples.

```python
class PixelGrid:
    def __init__(self, width=64, height=32):
        self.width = width
        self.height = height
        self.pixels: dict[tuple[int, int], str] = {}

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            if color is None:
                self.pixels.pop((x, y), None)  # erase
            else:
                self.pixels[(x, y)] = color     # paint

    def get_pixel(self, x, y):
        return self.pixels.get((x, y))          # None = transparent/empty
```

**Why sparse?** A 100×100 grid stores 10,000 entries. If you only draw 50 pixels, a full list wastes 9,950 empty slots. A dict stores only the 50 painted pixels. Missing keys naturally represent transparent/empty cells — `get_pixel` returns `None` for anything that hasn't been painted.

Colors are stored as hex strings (`#FF0000` for red). We also define a 16-color palette:

```python
PALETTE = {
    '0': '#000000', '1': '#FF0000', '2': '#00FF00', '3': '#FFFF00',
    '4': '#0000FF', '5': '#FF00FF', '6': '#00FFFF', '7': '#FFFFFF',
    '8': '#808080', '9': '#FF8800', 'a': '#AA00FF', 'b': '#00FFAA',
    'c': '#FF0066', 'd': '#0088FF', 'e': '#885500', 'f': '#FFFF88',
}
```

Two utility functions convert between hex strings and RGB tuples:

```python
def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip('#')
    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f'#{r:02x}{g:02x}{b:02x}'
```

### Your turn

Implement `PixelGrid` with `set_pixel`, `get_pixel`, `clear`, `fill`, and `copy`. Then add `hex_to_rgb` and `rgb_to_hex`. Test by creating a grid, painting a few pixels, and verifying they can be read back.

---

## Step 2: Terminal Rendering (`render.py`)

Now we need to display the grid. We'll use **ANSI escape codes** — special sequences that start with `\033[` and tell the terminal to change colors, move the cursor, or clear the screen.

Key ANSI sequences:

| Code | Effect |
|------|--------|
| `\033[2J` | Clear entire screen |
| `\033[H` | Move cursor home (top-left) |
| `\033[38;2;R;G;Bm` | Set foreground color (24-bit RGB) |
| `\033[48;2;R;G;Bm` | Set background color (24-bit RGB) |
| `\033[0m` | Reset all attributes |
| `\033[K` | Clear to end of line |

For each pixel, we render a **full block character** (`█`, Unicode U+2588) in the pixel's foreground color:

```python
FULL_BLOCK = '\u2588'

def render_frame(grid, cursor_x, cursor_y, status_lines):
    lines = ['\033[2J\033[H']  # clear + home
    for y in range(grid.height):
        row = ''
        for x in range(grid.width):
            color = grid.get_pixel(x, y)
            is_cursor = (x == cursor_x and y == cursor_y)
            if color:
                r, g, b = hex_to_rgb(color)
                if is_cursor:
                    # Inverted colors for cursor position
                    row += f'\033[38;2;{255-r};{255-g};{255-b}m'
                    row += f'\033[48;2;{r};{g};{b}m{CURSOR_BLOCK}\033[0m'
                else:
                    row += f'\033[38;2;{r};{g};{b}m{FULL_BLOCK}\033[0m'
            else:
                if is_cursor:
                    row += '\033[48;2;80;80;80m \033[0m'  # gray cursor on empty
                else:
                    row += ' '  # empty cell = space
        lines.append(row)
    for line in status_lines:
        lines.append(f'\033[K{line}')  # clear line before status text
    return '\n'.join(lines)
```

The cursor cell uses a medium-shade block (`▒`, U+2592) with inverted colors so it's always visible. Status lines are appended at the bottom, cleared with `\033[K` to handle partial redraws.

### Your turn

Implement `render_frame`. Each call rebuilds the entire screen string. The editor calls this in a loop, writing the string to `sys.stdout`. Try it by creating a `PixelGrid`, painting a few pixels, and printing the render output.

---

## Step 3: Drawing Tools (`tools.py`)

Drawing tools are classes that share a common interface. Each tool has a `name` and an `apply` method that mutates the grid.

```python
class Tool(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def apply(self, grid, x, y, **kwargs):
        ...
```

### PenTool

The simplest tool — it sets a single pixel:

```python
class PenTool(Tool):
    def apply(self, grid, x, y, **kwargs):
        color = kwargs.get('color')
        if color:
            grid.set_pixel(x, y, color)
```

### EraserTool

Sets the pixel to `None` (removes it from the dict):

```python
class EraserTool(Tool):
    def apply(self, grid, x, y, **kwargs):
        grid.set_pixel(x, y, None)
```

### LineTool (Bresenham's Algorithm)

Drawing a straight line between two points requires figuring out which pixels to fill. **Bresenham's algorithm** uses only integer addition and subtraction — no floating-point division — making it extremely fast:

```python
class LineTool(Tool):
    def apply(self, grid, x1, y1, x2, y2, **kwargs):
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
```

The algorithm tracks an error term that accumulates the difference between the ideal line and the chosen pixel. When the error crosses a threshold, it steps in the y-direction.

### RectTool

Draws a rectangle outline (or filled rectangle if `fill=True`):

```python
class RectTool(Tool):
    def apply(self, grid, x1, y1, x2, y2, **kwargs):
        color = kwargs.get('color')
        if not color:
            return
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        # Draw four edges
        for x in range(x_min, x_max + 1):
            grid.set_pixel(x, y_min, color)
            grid.set_pixel(x, y_max, color)
        for y in range(y_min, y_max + 1):
            grid.set_pixel(x_min, y, color)
            grid.set_pixel(x_max, y, color)
        if kwargs.get('fill', False):
            for y in range(y_min + 1, y_max):
                for x in range(x_min + 1, x_max):
                    grid.set_pixel(x, y, color)
```

### EyedropperTool

Instead of drawing, this tool **reads** the color at a position. The editor uses the result to set the active drawing color:

```python
class EyedropperTool(Tool):
    def apply(self, grid, x, y, **kwargs):
        return grid.get_pixel(x, y)
```

### Your turn

Implement all six tools: `PenTool`, `EraserTool`, `LineTool` (with Bresenham), `RectTool` (outline and fill), `FloodFillTool` (we'll do this in Step 4), and `EyedropperTool`.

---

## Step 4: Flood Fill

The flood fill tool replaces every pixel in a contiguous region of one color with another color. It's the "paint bucket" tool in every graphics editor.

The algorithm uses **BFS (breadth-first search)** with a queue. Starting from the clicked pixel, it checks each neighbor — if the neighbor matches the target color, it gets filled and its neighbors are added to the queue.

```python
from collections import deque

class FloodFillTool(Tool):
    def apply(self, grid, x, y, **kwargs):
        fill_color = kwargs.get('color')
        if not fill_color:
            return
        target = grid.get_pixel(x, y)
        if target == fill_color:          # already this color — nothing to do
            return
        queue = deque()
        queue.append((x, y))
        while queue:
            cx, cy = queue.popleft()
            if grid.get_pixel(cx, cy) != target:
                continue                  # already filled or different color
            grid.set_pixel(cx, cy, fill_color)
            for nx, ny in (
                (cx + 1, cy), (cx - 1, cy),
                (cx, cy + 1), (cx, cy - 1),
            ):
                if 0 <= nx < grid.width and 0 <= ny < grid.height:
                    queue.append((nx, ny))
```

**Why BFS instead of recursion?** A recursive DFS would work for small images but could overflow Python's call stack (default limit = 1000) on a large fill. BFS uses a `collections.deque` which grows only as wide as the fill frontier — typically far less memory than stack frames.

**Dry run:** Imagine a 10×10 grid with a red square in the center. You click inside the red square with blue selected:

1. `target = red`, `fill_color = blue`. They differ, so continue.
2. Queue starts with `[(5, 5)]`.
3. Pop `(5, 5)`: pixel is red → set to blue. Push `(6,5), (4,5), (5,6), (5,4)`.
4. Pop `(6, 5)`: pixel is red → set to blue. Push its neighbors.
5. The BFS spreads outward in rings, filling all reachable red pixels.
6. When the queue hits the edge of the red square, neighbors outside are not red, so the `get_pixel` check skips them — the fill stops at the boundary.

### Your turn

Implement `FloodFillTool.apply` using BFS. Make sure to check bounds and skip pixels that don't match the target color. Handle the edge case where the pixel under the cursor is already the fill color.

---

## Step 5: Layers (`layers.py`)

Layers let you compose multiple independent canvases, like stacking transparencies on an overhead projector. Each layer has its own name, pixel grid, visibility toggle, and opacity.

```python
class Layer:
    def __init__(self, name, width, height):
        self.name = name
        self.grid = PixelGrid(width, height)
        self.visible = True
        self.opacity = 1.0
```

The `LayerStack` manages an ordered list of layers. The **last layer in the list is the active (topmost) layer** — new drawing goes here.

```python
class LayerStack:
    def __init__(self):
        self.layers = []

    def add(self, name, width, height, index=None):
        layer = Layer(name, width, height)
        if index is None:
            self.layers.append(layer)
        else:
            self.layers.insert(index, layer)
        return layer

    def remove(self, name):
        self.layers = [l for l in self.layers if l.name != name]

    def active(self):
        return self.layers[-1] if self.layers else None
```

The key method is **`composite()`** — it merges all visible layers into a single result. It walks layers from bottom to top, and pixels from higher layers overwrite those below:

```python
    def composite(self):
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
```

This simple compositing gives the "normal" blend mode. With opacity support, you'd blend each pixel based on `layer.opacity` — but for this project, simple overwrite compositing is sufficient.

**Why layers?** Non-destructive editing. Draw a background on layer 1, a foreground character on layer 2. If you mess up the foreground, just clear layer 2 without touching the background. Hide layers to preview the composition.

### Your turn

Implement the `Layer` and `LayerStack` classes. Make sure `composite()` only includes visible layers. The editor will maintain two default layers: "Background" and "Foreground".

---

## Step 6: Filters (`filters.py`)

Filters transform the composited canvas pixel by pixel. Each filter takes a `PixelGrid` and returns a new `PixelGrid`. The editor composites all visible layers, applies the filter, and replaces the active layer's pixels with the result.

### Invert

Flips every color channel: `new = 255 - old`:

```python
def invert(grid):
    result = grid.copy()
    for (x, y), color in list(result.pixels.items()):
        r, g, b = hex_to_rgb(color)
        result.set_pixel(x, y, rgb_to_hex(255 - r, 255 - g, 255 - b))
    return result
```

### Grayscale

Converts each pixel to a shade of gray using **luminosity weights** — human eyes are most sensitive to green, least to blue:

```python
def grayscale(grid):
    result = grid.copy()
    for (x, y), color in list(result.pixels.items()):
        r, g, b = hex_to_rgb(color)
        gray = int(0.299 * r + 0.587 * g + 0.114 * b)
        result.set_pixel(x, y, rgb_to_hex(gray, gray, gray))
    return result
```

### Brightness

Multiplies each channel by a factor, clamping to [0, 255]:

```python
def brightness(grid, factor=1.2):
    result = grid.copy()
    for (x, y), color in list(result.pixels.items()):
        r, g, b = hex_to_rgb(color)
        r = min(255, max(0, int(r * factor)))
        g = min(255, max(0, int(g * factor)))
        b = min(255, max(0, int(b * factor)))
        result.set_pixel(x, y, rgb_to_hex(r, g, b))
    return result
```

### Box Blur

Replaces each pixel with the average of its (radius×2+1)² neighborhood. This is the simplest blur — it creates a smooth, softened effect:

```python
def box_blur(grid, radius=2):
    result = PixelGrid(grid.width, grid.height)
    for (x, y), color in list(grid.pixels.items()):
        r_sum = g_sum = b_sum = count = 0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nc = grid.get_pixel(x + dx, y + dy)
                if nc:
                    r, g, b = hex_to_rgb(nc)
                    r_sum += r; g_sum += g; b_sum += b
                    count += 1
        if count > 0:
            result.set_pixel(x, y, rgb_to_hex(
                r_sum // count, g_sum // count, b_sum // count))
    return result
```

### Edge Detection (Sobel)

Finds edges by convolving the image with two 3×3 kernels — one detecting horizontal changes (Gx), one detecting vertical changes (Gy):

```
Sobel X:     Sobel Y:
-1  0 +1    -1 -2 -1
-2  0 +2     0  0  0
-1  0 +1    +1 +2 +1
```

The magnitude at each pixel is `sqrt(Gx² + Gy²)`. If the magnitude exceeds a threshold, the pixel is rendered as an edge:

```python
def edge_detect(grid, threshold=30):
    sobel_x = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    sobel_y = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    result = PixelGrid(grid.width, grid.height)
    for (x, y), _ in list(grid.pixels.items()):
        gx_r = gx_g = gx_b = 0
        gy_r = gy_g = gy_b = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nc = grid.get_pixel(x + dx, y + dy)
                if nc:
                    r, g, b = hex_to_rgb(nc)
                    sx = sobel_x[dx + 1][dy + 1]
                    sy = sobel_y[dx + 1][dy + 1]
                    gx_r += r * sx; gx_g += g * sx; gx_b += b * sx
                    gy_r += r * sy; gy_g += g * sy; gy_b += b * sy
        mag_r = min(int((gx_r**2 + gy_r**2)**0.5), 255)
        mag_g = min(int((gx_g**2 + gy_g**2)**0.5), 255)
        mag_b = min(int((gx_b**2 + gy_b**2)**0.5), 255)
        avg_mag = (mag_r + mag_g + mag_b) // 3
        if avg_mag > threshold:
            result.set_pixel(x, y, rgb_to_hex(mag_r, mag_g, mag_b))
    return result
```

### Your turn

Implement all five filters. Each function should return a **new** `PixelGrid` without modifying the original. Test with a simple pattern: draw a red square, apply `grayscale`, verify it became gray.

---

## Step 7: Export (`export.py`)

Once you've created pixel art, you'll want to save it. The export module provides four output formats.

### ANSI Art

Preserves full color using ANSI background codes. Reopenable in the editor:

```python
def export_ansi(grid):
    lines = []
    for y in range(grid.height):
        row = []
        for x in range(grid.width):
            color = grid.get_pixel(x, y)
            if color:
                r, g, b = hex_to_rgb(color)
                row.append(f'\033[48;2;{r};{g};{b}m \033[0m')
            else:
                row.append(' ')
        lines.append(''.join(row))
    return '\n'.join(lines)
```

### ASCII Art

Maps each pixel's luminance to a character in a ramp — denser characters (`@`, `%`, `#`) for darker pixels, lighter characters (`.`, ` `) for brighter ones:

```python
ASCII_CHARS = '@%#*+=-:. '

def luminance(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return int(0.2126 * r + 0.7152 * g + 0.0722 * b)

def export_ascii_art(grid):
    lines = []
    for y in range(grid.height):
        row = []
        for x in range(grid.width):
            color = grid.get_pixel(x, y)
            if color is None:
                row.append(' ')
            else:
                lum = luminance(color)
                idx = int(lum / 255 * (len(ASCII_CHARS) - 1))
                row.append(ASCII_CHARS[idx])
        lines.append(''.join(row))
    return '\n'.join(lines)
```

### HTML

Renders each pixel as a table cell with a background color. Open the result in a browser:

```python
def export_html(grid, cell_size=10):
    cells = []
    for y in range(grid.height):
        for x in range(grid.width):
            color = grid.get_pixel(x, y)
            bg = color if color else '#111'
            cells.append(
                f'<td style="background:{bg};'
                f'width:{cell_size}px;height:{cell_size}px;"></td>')
        cells.append('</tr><tr>')
    return '<table style="border-collapse:collapse;"><tr>' \
           + ''.join(cells) + '</tr></table>'
```

### SVG

Resolution-independent vector format — each pixel becomes a `<rect>` element:

```python
def export_svg(grid, cell_size=8):
    rects = []
    for (x, y), color in grid.pixels.items():
        rects.append(
            f'<rect x="{x * cell_size}" y="{y * cell_size}" '
            f'width="{cell_size}" height="{cell_size}" fill="{color}" />')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{grid.width * cell_size}" '
        f'height="{grid.height * cell_size}">\n'
        + '\n'.join(rects) + '\n</svg>'
    )
```

### Your turn

Implement all four export functions. Test by drawing something, exporting, and inspecting the output file.

---

## Step 8: Running and Extending (`editor.py`)

The editor ties everything together with an interactive terminal loop. It uses **raw terminal mode** (via the `termios` and `tty` modules) to read individual keypresses without waiting for Enter.

### Raw Terminal I/O

Set raw mode on startup, restore the terminal on exit:

```python
def _setup_terminal(self):
    self._fd = sys.stdin.fileno()
    self._old = termios.tcgetattr(self._fd)
    tty.setraw(self._fd)

def _cleanup_terminal(self):
    termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old)
    sys.stdout.write('\033[2J\033[H\033[?25h')  # clear + show cursor
```

### Reading Keys

Arrow keys send escape sequences (`\x1b[A` through `\x1b[D`). We read the first byte, check for `\x1b`, and read two more bytes to identify the arrow:

```python
def _read_key(self):
    raw = os.read(self._fd, 1)
    if not raw:
        return 'QUIT'
    ch = raw.decode()
    if ch == '\x1b':
        import select
        if select.select([sys.stdin], [], [], 0.05)[0]:
            seq = os.read(self._fd, 2)
            if seq == b'[A': return 'UP'
            if seq == b'[B': return 'DOWN'
            if seq == b'[C': return 'RIGHT'
            if seq == b'[D': return 'LEFT'
        return None
    return ch
```

### Key Bindings

| Key | Action |
|-----|--------|
| Arrow keys | Move cursor |
| Space | Draw with current tool |
| `1`–`6` | Switch tool (Pen, Eraser, Line, Rect, Fill, Pick) |
| `0`–`9`, `a`–`f` | Select color from palette |
| `[` / `]` | Cycle active layer |
| `h` | Toggle layer visibility |
| `m` | Merge active layer down |
| `n` | New layer |
| `i` | Invert colors |
| `g` | Grayscale |
| `b` / `d` | Brighten / Darken |
| `u` | Box blur |
| `e` | Edge detect |
| `o` / `a` | Export ANSI / ASCII art |
| `p` / `s` | Export HTML / SVG |
| `c` | Clear active layer |
| Ctrl-Q | Quit |

### Main Loop

The editor runs a render-read-dispatch loop:

```python
def run(self):
    self._setup_terminal()
    try:
        sys.stdout.write('\033[?25l')  # hide cursor
        sys.stdout.flush()
        self._render()
        while self.running:
            key = self._read_key()
            self._handle_key(key)
            self._render()
    finally:
        self._cleanup_terminal()
```

The `_handle_key` method dispatches each key to the appropriate action — moving the cursor, switching tools, selecting colors, applying tools, manipulating layers, running filters, or exporting.

### Your turn

Wire up the full editor:
1. Initialize two layers (Background and Foreground)
2. Set default tool to Pen, color to white
3. Implement the render loop
4. Handle all key bindings
5. For Line and Rectangle tools, use a two-click pattern: first click sets the start point, second click completes the shape
6. For Eyedropper, set the current color to the picked color
7. Clean up the terminal gracefully on exit

### Running

```bash
python editor.py
```

You should see a 64×32 grid, a status bar at the bottom showing your tool, color, layer, and cursor position. Move around with arrow keys and start drawing with Space.

---

## Conclusion

You've built a complete terminal-based pixel art editor with:

- **A sparse pixel grid** that stores only painted cells
- **ANSI terminal rendering** with 24-bit color block characters
- **Six drawing tools** including Bresenham lines and BFS flood fill
- **Layer compositing** with visibility toggles and merging
- **Five image filters** — invert, grayscale, brightness, box blur, edge detection
- **Four export formats** — ANSI art, ASCII art, HTML, SVG
- **Raw terminal I/O** with custom key bindings

### What to try next

**Animation frames.** Treat each frame as a full `LayerStack`. Add a timeline that plays frames at a configurable FPS. Export as a spritesheet (render all frames side-by-side).

**Palette management.** Constrain the editor to specific palettes like PICO-8 or NES. Map pixel values to palette indices for file size efficiency.

**PNG import/export.** Use the `Pillow` library (when available) to load real images onto the canvas or save your pixel art as PNG.

**Collaborative editing.** Add networking with `socket` — each `set_pixel` call broadcasts to connected clients. Since pixel writes are idempotent, last-write-wins is a natural conflict resolution strategy.

**Undo/redo.** Before each tool application, snapshot the active layer's pixels. Push onto an undo stack. Ctrl-Z pops from undo and pushes to redo.

The architecture you've built — decoupled canvas, tools, layers, filters, and export — makes all of these extensions straightforward without changing the core modules. Happy painting!
