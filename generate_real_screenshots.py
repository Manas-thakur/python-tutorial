"""Generate real screenshots by capturing the actual app output.

Uses Rich's recording capability to capture styled terminal output
from the app's rendering functions, then renders them to PNG via Pillow.
"""

import sys
import os
from io import StringIO
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.segment import Segment
from rich.style import Style as RichStyle
from rich.text import Text

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "banner")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
CELL_W = 10
CELL_H = 18

def get_font(size=14):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except (IOError, OSError):
        return ImageFont.load_default()

def get_font_bold(size=14):
    try:
        return ImageFont.truetype(FONT_BOLD_PATH, size)
    except (IOError, OSError):
        return get_font(size)

def rich_color_to_rgb(color_str):
    """Convert a Rich color string like '#aabbcc' or 'rgb(..)' to (R,G,B)."""
    if not color_str:
        return None
    if color_str.startswith("#"):
        h = color_str.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    if color_str.startswith("rgb("):
        parts = color_str.strip("rgb()").split(",")
        return tuple(int(p.strip()) for p in parts)
    return None

# Tokyo Night palette fallback
TN_BG = (15, 17, 26)
TN_FG = (169, 177, 214)
TN_CYAN = (0, 212, 255)
TN_GREEN = (158, 206, 106)
TN_YELLOW = (255, 158, 100)
TN_RED = (247, 118, 142)
TN_DIM = (86, 95, 137)
TN_BLUE = (122, 162, 247)
TN_PURPLE = (187, 154, 247)
TN_ORANGE = (255, 158, 100)

NAMED_COLORS = {
    "cyan": TN_CYAN,
    "green": TN_GREEN,
    "yellow": TN_YELLOW,
    "red": TN_RED,
    "blue": TN_BLUE,
    "magenta": TN_PURPLE,
    "white": (220, 220, 230),
    "bright_blue": TN_BLUE,
    "bright_green": TN_GREEN,
    "bright_yellow": TN_YELLOW,
    "bright_red": TN_RED,
    "dim": TN_DIM,
    "bold": None,
}

def resolve_color(rich_color, default=None):
    if rich_color is None:
        return default
    if isinstance(rich_color, str):
        if rich_color in NAMED_COLORS:
            return NAMED_COLORS[rich_color]
        rgb = rich_color_to_rgb(rich_color)
        if rgb:
            return rgb
        return default
    # It's a Rich Color object
    if hasattr(rich_color, 'triplet'):
        t = rich_color.triplet
        if t:
            return (t.red, t.green, t.blue)
    if hasattr(rich_color, 'name') and rich_color.name:
        return NAMED_COLORS.get(rich_color.name, default)
    if hasattr(rich_color, 'rgb') and rich_color.rgb:
        return rich_color.rgb
    return default

def render_segments_to_image(segments, width_chars, height_chars=None, title=""):
    """Render Rich segments to a Pillow image."""
    font = get_font(14)
    font_bold = get_font_bold(14)
    
    # Calculate image dimensions with padding
    pad = 16
    img_w = width_chars * CELL_W + pad * 2
    img_h = (height_chars or 40) * CELL_H + pad * 2 + 28  # +28 for title bar
    
    img = Image.new("RGB", (img_w, img_h), (10, 10, 16))
    draw = ImageDraw.Draw(img)
    
    # Terminal frame
    draw.rectangle([2, 2, img_w - 3, img_h - 3], outline=(50, 52, 70), width=1)
    draw.rectangle([3, 3, img_w - 4, img_h - 4], fill=(20, 22, 34))
    
    # Title bar
    title_h = 28
    draw.rectangle([3, 3, img_w - 4, 3 + title_h], fill=(30, 32, 48))
    for bx, bc in [(8, TN_RED), (22, TN_YELLOW), (36, TN_GREEN)]:
        draw.ellipse([bx, 10, bx + 10, 20], fill=bc)
    
    if title:
        draw.text((56, 8), title, fill=TN_DIM, font=font)
    
    # Parse segments into rows
    rows = {}
    x, y = 0, 0
    for segment in segments:
        text = segment.text
        style = segment.style or RichStyle()
        try:
            fg = resolve_color(style.color, TN_FG)
        except Exception:
            fg = TN_FG
        bold = style.bold
        
        for ch in text:
            if ch == "\n":
                x = 0
                y += 1
            elif ch == "\r":
                x = 0
            else:
                if y not in rows:
                    rows[y] = {}
                rows[y][x] = (ch, fg, bold)
                x += 1
    
    # Render rows
    content_y = 3 + title_h + 8
    for row_y in sorted(rows.keys()):
        if row_y >= (height_chars or 40):
            break
        row = rows[row_y]
        py = content_y + row_y * CELL_H
        # Draw background for entire row
        draw.rectangle([pad, py, img_w - pad, py + CELL_H], fill=TN_BG)
        
        for col_x in sorted(row.keys()):
            ch, color, bold = row[col_x]
            f = font_bold if bold else font
            px = pad + col_x * CELL_W
            draw.text((px, py), ch, fill=color or TN_FG, font=f)
    
    return img

def capture_console(console_func, width=80, height=30, title=""):
    """Capture output of a function that uses a Rich console."""
    rec = Console(record=True, width=width, color_system="truecolor", force_terminal=True, force_interactive=False)
    
    # Run the function with the recording console
    console_func(rec)
    
    text_segs = list(rec._record_buffer)

    img = render_segments_to_image(text_segs, width, height, title)
    return img

# --- Actual app captures ---

def capture_welcome():
    from python_tutorial.renderer import show_banner, show_phase_list
    from python_tutorial.content import discover_phases
    from python_tutorial.progress import ProgressTracker
    
    progress = ProgressTracker()
    progress.data = {}  # Start fresh, ignore any prior test data
    phases = discover_phases()
    
    def render(console):
        import python_tutorial.renderer as R
        old = R.console
        R.console = console
        show_banner()
        show_phase_list(phases, progress)
        R.console = old
    
    return capture_console(render, width=76, height=20, title="python-tutorial")

def capture_status():
    from python_tutorial.cli import show_detailed_progress
    from python_tutorial.content import discover_phases
    from python_tutorial.progress import ProgressTracker
    
    # Seed progress data so the screenshot shows realistic stats
    progress = ProgressTracker()
    progress.data = {}
    phases = discover_phases()
    # Mark Phase 1 (Fundamentals, 11 topics) mostly done
    for t_num in range(1, 10):
        progress.data.setdefault("phase_1", {})[str(t_num)] = True
    # Mark Phase 2 (Core Python, 8 topics) partially done
    for t_num in range(1, 5):
        progress.data.setdefault("phase_2", {})[str(t_num)] = True
    # XP for level 3
    progress.data["_xp"] = 650
    # 5-day streak
    from datetime import date, timedelta
    today = date.today()
    progress.data["_streaks"] = [(today - timedelta(days=i)).isoformat() for i in range(4, -1, -1)]

    def render(console):
        import python_tutorial.renderer as R
        import python_tutorial.cli as CLI
        old = R.console
        old_progress = CLI.progress
        R.console = console
        CLI.progress = progress
        show_detailed_progress()
        R.console = old
        CLI.progress = old_progress
    
    return capture_console(render, width=76, height=25, title="python-tutorial — status")

def capture_projects():
    from python_tutorial.content import discover_project_tutorials
    from python_tutorial.progress import ProgressTracker
    
    progress = ProgressTracker()
    
    def render(console):
        import python_tutorial.renderer as R
        old = R.console
        R.console = console
        projects = discover_project_tutorials()
        console.print("\n[bold cyan]Project Tutorials[/] ([bold]7[/])\n")
        for i, p in enumerate(projects, 1):
            done, total = progress.get_project_progress(p.slug, len(p.steps))
            diff_color = {"beginner": "green", "intermediate": "yellow", "advanced": "red"}.get(p.difficulty, "white")
            console.print(f"  [bold]{i}. {p.title}[/]  [{diff_color}]{p.difficulty}[/]  [dim]Steps: [cyan]{done}[/]/[cyan]{total}[/]")
            console.print(f"     [dim]{p.description}[/]")
            console.print()
        R.console = old
    
    return capture_console(render, width=76, height=20, title="python-tutorial — projects")

if __name__ == "__main__":
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    print("Capturing welcome screen...")
    img = capture_welcome()
    img.save(os.path.join(ASSETS_DIR, "screenshot-welcome.png"))
    print("  -> banner/screenshot-welcome.png")
    
    print("Capturing status screen...")
    img = capture_status()
    img.save(os.path.join(ASSETS_DIR, "screenshot-status.png"))
    print("  -> banner/screenshot-status.png")
    
    print("Capturing projects screen...")
    img = capture_projects()
    img.save(os.path.join(ASSETS_DIR, "screenshot-projects.png"))
    print("  -> banner/screenshot-projects.png")
    
    print("\nDone! Check banner/ directory.")
