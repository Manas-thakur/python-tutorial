"""Generate banner image and screenshots for Codédex submission.

Uses Pillow to render realistic terminal screenshots of the Python Tutorial TUI app.
Creates a 1200x630 banner and individual app screenshots.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import os

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "banner")
FONT_SIZE = 16
FONT_SIZE_LG = 24
FONT_SIZE_XL = 36
BG = (15, 17, 26)       # Tokyo Night bg (#0f111a)
FG = (169, 177, 214)    # text (#a9b1d6)
CYAN = (0, 212, 255)    # cyan
GREEN = (158, 206, 106) # green
YELLOW = (255, 158, 100) # yellow
RED = (247, 118, 142)   # red
DIM = (86, 95, 137)     # dim (#565f89)
BLUE = (122, 162, 247)  # blue
PURPLE = (187, 154, 247) # purple
ORANGE = (255, 158, 100) # orange
WHITE = (220, 220, 230)  # white

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/opentype/urw-base35/NimbusMonoPS-Bold.otf"

def get_font(size=FONT_SIZE):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except (IOError, OSError):
        return ImageFont.load_default()

def get_font_bold(size=FONT_SIZE):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf", size)
    except (IOError, OSError):
        return get_font(size)

def draw_text(draw, x, y, text, font=None, fill=FG, spacing=2):
    if font is None:
        font = get_font()
    draw.text((x, y), text, fill=fill, font=font, spacing=spacing)

def draw_progress_bar(draw, x, y, w, h, filled, total, color=GREEN, bg_color=(30, 32, 48)):
    draw.rectangle([x, y, x + w, y + h], fill=bg_color)
    if total > 0:
        fw = int((filled / total) * w)
        if fw > 0:
            draw.rectangle([x, y, x + fw, y + h], fill=color)

def generate_banner():
    """Generate 1200x630 banner image."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    font = get_font(18)
    font_bold = get_font_bold(18)
    font_title = get_font_bold(32)
    font_sub = get_font(14)

    # Terminal window frame
    margin = 30
    term_w = W - 2 * margin
    term_h = H - 2 * margin
    term_x, term_y = margin, margin

    # Terminal border
    draw.rectangle([term_x, term_y, term_x + term_w, term_y + term_h], outline=(50, 52, 70), width=2)
    draw.rectangle([term_x + 1, term_y + 1, term_x + term_w - 1, term_y + term_h - 1], fill=(20, 22, 34))

    # Title bar
    title_h = 36
    draw.rectangle([term_x + 2, term_y + 2, term_x + term_w - 2, term_y + title_h], fill=(30, 32, 48))

    # Window buttons
    for bx, bc in [(term_x + 10, RED), (term_x + 28, YELLOW), (term_x + 46, GREEN)]:
        draw.ellipse([bx, term_y + 12, bx + 12, term_y + 24], fill=bc)

    # Title text
    title_text = "python-tutorial — Python Interactive Tutorial"
    tw = draw.textlength(title_text, font=font_bold)
    draw.text(((term_w - tw) // 2, term_y + 8), title_text, fill=DIM, font=font_bold)

    # Content area
    cx = term_x + 24
    cy = term_y + title_h + 20

    # Banner line
    banner_line = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    draw_text(draw, cx, cy, banner_line, font=font, fill=CYAN)
    cy += 22

    # Title
    draw_text(draw, cx, cy, "Python Interactive Tutorial", font=font_title, fill=CYAN)
    cy += 40

    # Subtitle
    draw_text(draw, cx, cy, "Learn Python from fundamentals to AI engineering  •  All in your terminal", font=font_sub, fill=DIM)
    cy += 30

    # Tag line
    draw_text(draw, cx, cy, "  Learn  →  Practice  →  Experiment  →  Build", font=font_bold, fill=GREEN)
    cy += 36

    # Roadmap table
    phases_data = [
        (1, "Python Fundamentals", 11, 11, "DONE"),
        (2, "Core Python", 8, 8, "DONE"),
        (3, "Object-Oriented Programming", 8, 6, "75%"),
        (4, "Intermediate Python", 9, 4, "44%"),
        (5, "Advanced Python", 7, 2, "28%"),
        (6, "Python for Engineering", 6, 0, "LOCKED"),
        (7, "Python for AI Engineering", 7, 0, "LOCKED"),
    ]

    # Table header
    col_x = [cx, cx + 40, cx + 420, cx + 520, cx + 620]
    headers = ["#", "Phase", "Topics", "Progress", "Status"]
    col_colors = [DIM, CYAN, DIM, DIM, DIM]
    for i, (hdr, c) in enumerate(zip(headers, col_colors)):
        draw_text(draw, col_x[i], cy, hdr, font=font_bold, fill=c)
    cy += 24

    # Separator
    draw_text(draw, cx, cy, "────", font=font, fill=DIM)
    cy += 8

    for num, title, total, done, status in phases_data:
        # Phase number
        draw_text(draw, col_x[0], cy, str(num), font=font, fill=DIM)
        # Phase title
        if status == "LOCKED":
            phase_color = DIM
            title_display = f"{title} (locked)"
        else:
            phase_color = YELLOW if status == "DONE" else WHITE
            title_display = title
        draw_text(draw, col_x[1], cy, title_display, font=font, fill=phase_color)
        # Topics count
        draw_text(draw, col_x[2], cy, f"{done}/{total}", font=font, fill=WHITE)
        # Progress bar
        bar_x, bar_y = col_x[3], cy + 4
        draw_progress_bar(draw, bar_x, bar_y, 80, 12, done, total, GREEN if done == total else CYAN)
        # Status
        if status == "DONE":
            status_color = GREEN
        elif status == "LOCKED":
            status_color = DIM
        else:
            status_color = YELLOW
        draw_text(draw, col_x[4], cy, status, font=font_bold, fill=status_color)
        cy += 22

    cy += 16

    # Stats line
    stats = "Completed: 31/56 topics  |  Level 12  |  2,450 XP  |  14-day streak"
    draw_text(draw, cx, cy, stats, font=font_sub, fill=DIM)
    cy += 30

    # Bottom action bar
    sep = "─" * 75
    draw_text(draw, cx, cy, sep, font=font, fill=(40, 42, 60))
    cy += 18
    prompt = "Select (phase#, search, flashcards, sandbox, q): "
    draw_text(draw, cx, cy, prompt, font=font_bold, fill=CYAN)
    pw = draw.textlength(prompt, font=font_bold)
    draw_text(draw, cx + pw + 4, cy, "▌", font=font, fill=WHITE)

    # Save
    path = os.path.join(ASSETS_DIR, "banner.png")
    img.save(path, "PNG")
    print(f"Saved banner: {path}")
    return path

def generate_screenshot(name: str, width: int, height: int, draw_content):
    """Generate a screenshot image with the terminal frame."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    margin = 10
    img_w = width + 2 * margin
    img_h = height + 2 * margin
    img = Image.new("RGB", (img_w, img_h), (10, 10, 16))
    draw = ImageDraw.Draw(img)
    font = get_font(14)
    font_bold = get_font_bold(14)

    # Terminal frame
    term_x, term_y = margin, margin
    draw.rectangle([term_x, term_y, term_x + width, term_y + height], outline=(50, 52, 70), width=1)
    draw.rectangle([term_x + 1, term_y + 1, term_x + width - 1, term_y + height - 1], fill=(20, 22, 34))

    # Title bar
    title_h = 28
    draw.rectangle([term_x + 1, term_y + 1, term_x + width - 1, term_y + title_h], fill=(30, 32, 48))
    for bx, bc in [(term_x + 8, RED), (term_x + 22, YELLOW), (term_x + 36, GREEN)]:
        draw.ellipse([bx, term_y + 8, bx + 10, term_y + 18], fill=bc)
    draw_text(draw, term_x + 56, term_y + 6, "python-tutorial", font=font, fill=DIM)

    cx = term_x + 16
    cy = term_y + title_h + 16

    draw_content(draw, cx, cy, font, font_bold)

    path = os.path.join(ASSETS_DIR, f"screenshot-{name}.png")
    img.save(path, "PNG")
    print(f"Saved screenshot: {path}")
    return path

def screen_welcome():
    """Welcome screen / main menu"""
    def draw(draw, cx, cy, font, font_bold):
        draw_text(draw, cx, cy, "Python Interactive Tutorial", font=get_font_bold(20), fill=CYAN)
        cy += 28
        draw_text(draw, cx, cy, "Learn Python from fundamentals to AI", font=font, fill=DIM)
        cy += 20
        draw_text(draw, cx, cy, f"Level 12  {'█'*8 + '░'*4}  1245/2500 XP", font=font_bold, fill=CYAN)
        cy += 26

        # Table
        headers = ["#", "Phase", "Topics", "Progress"]
        for i, h in enumerate(headers):
            cols = [0, 24, 300, 380]
            draw_text(draw, cx + cols[i], cy, h, font=font_bold, fill=CYAN)
        cy += 20
        draw_text(draw, cx, cy, "────" * 20, font=font, fill=(40, 42, 60))
        cy += 6

        phases = [
            ("1", "Python Fundamentals", "11/11", GREEN),
            ("2", "Core Python", "8/8", GREEN),
            ("3", "Object-Oriented Programming", "6/8", YELLOW),
            ("4", "Intermediate Python", "4/9", YELLOW),
            ("5", "Advanced Python", "2/7", YELLOW),
            ("6", "Python for Engineering", "0/6", DIM),
            ("7", "Python for AI Engineering", "0/7", DIM),
        ]
        for num, name, progress, color in phases:
            cols = [0, 24, 300, 380]
            draw_text(draw, cx + cols[0], cy, num, font=font, fill=DIM)
            draw_text(draw, cx + cols[1], cy, name, font=font, fill=color if color != DIM else WHITE)
            draw_text(draw, cx + cols[2], cy, progress, font=font, fill=color)
            bar_x = cx + cols[3]
            done, total = int(progress.split('/')[0]), int(progress.split('/')[1])
            draw_progress_bar(draw, bar_x, cy + 3, 70, 10, done, total, color if color != DIM else (50, 52, 70))
            cy += 20

        cy += 12
        draw_text(draw, cx, cy, "31/56 topics  |  streak 14d  |  search, flashcards, sandbox, progress", font=font, fill=DIM)
        cy += 24
        draw_text(draw, cx, cy, "Select (phase#, search, flashcards, sandbox, q): ", font=font_bold, fill=CYAN)

    return generate_screenshot("welcome", 620, 420, draw)

def screen_projects():
    """F3 Projects browser"""
    def draw(draw, cx, cy, font, font_bold):
        draw_text(draw, cx, cy, "Project Tutorials", font=get_font_bold(18), fill=CYAN)
        cy += 28
        draw_text(draw, cx, cy, "7 step-by-step walkthroughs to build real projects", font=font, fill=DIM)
        cy += 24

        projects = [
            ("1. Expense Tracker", "beginner", "SQLite, CLI, CSV, charts", "4/8", YELLOW),
            ("2. TUI Text Editor", "intermediate", "Gap buffer, raw mode, ANSI", "8/8", GREEN),
            ("3. Markdown Blog Engine", "intermediate", "Parser, templates, SSE", "2/8", YELLOW),
            ("4. Chat Server & Client", "intermediate", "asyncio, TCP, auth", "0/8", DIM),
            ("5. Pixel Art Editor", "intermediate", "Flood fill, Bresenham, filters", "0/8", DIM),
            ("6. Task Scheduler", "advanced", "Cron, decorators, web dashboard", "0/8", DIM),
            ("7. API Framework", "advanced", "Routing, middleware, HTTP", "0/8", DIM),
        ]

        for title, diff, desc, progress, color in projects:
            diff_color = GREEN if diff == "beginner" else YELLOW if diff == "intermediate" else RED
            draw_text(draw, cx, cy, title, font=font_bold, fill=WHITE)
            draw_text(draw, cx + 260, cy, diff, font=font, fill=diff_color)
            tw = draw.textlength(f"  Steps: {progress}  ", font=font)
            draw_text(draw, cx + 370, cy, f"Steps: {progress}", font=font, fill=color)
            cy += 16
            draw_text(draw, cx + 16, cy, desc, font=font, fill=DIM)
            cy += 20

        cy += 8
        draw_text(draw, cx, cy, "[F2] IDE  [F3] Projects  [Ctrl+Q] Quiz  [Ctrl+F] Search", font=font, fill=DIM)

    return generate_screenshot("projects", 580, 420, draw)

def screen_ide():
    """F2 Fresh IDE"""
    def draw(draw, cx, cy, font, font_bold):
        draw_text(draw, cx, cy, "Fresh IDE — sandbox.py", font=get_font_bold(16), fill=CYAN)
        cy += 26

        codedisp = [
            (None, "def fibonacci(n):"),
            (GREEN, '    """Return nth Fibonacci number."""'),
            (None, "    if n <= 1:"),
            (None, "        return n"),
            (None, "    a, b = 0, 1"),
            (None, "    for _ in range(n - 1):"),
            (None, "        a, b = b, a + b"),
            (None, "    return b"),
            (None, ""),
            (DIM, "# Test it"),
            (None, "for i in range(10):"),
            (None, "    print(f'fib({i}) = {fibonacci(i)}')"),
        ]

        line_x = cx + 24
        for lineno, (color, text) in enumerate(codedisp):
            line_color = color or FG
            draw_text(draw, cx, cy, f"{lineno+1:3d} ", font=font, fill=DIM)
            draw_text(draw, line_x, cy, text, font=font, fill=line_color)
            cy += 17

        cy += 10
        draw.rectangle([cx, cy, cx + 500, cy + 120], fill=(10, 12, 20))
        draw_text(draw, cx + 8, cy + 4, "Output:", font=font_bold, fill=CYAN)
        outputs = ["fib(0) = 0", "fib(1) = 1", "fib(2) = 1", "fib(3) = 2", "...", "fib(9) = 34"]
        for idx, out in enumerate(outputs):
            draw_text(draw, cx + 16, cy + 22 + idx * 16, out, font=font, fill=GREEN)

    return generate_screenshot("ide", 580, 460, draw)

if __name__ == "__main__":
    generate_banner()
    screen_welcome()
    screen_projects()
    screen_ide()
    print("\nAll images generated in:", ASSETS_DIR)
