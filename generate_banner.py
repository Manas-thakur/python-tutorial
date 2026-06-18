"""Generate a 1200x630 GitHub social preview banner — brutalist space theme."""

import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1200, 630
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

SEED = 42
random.seed(SEED)

BG = (4, 4, 14)
STAR_COLORS = [(180, 190, 220), (200, 210, 240), (220, 230, 255), (140, 160, 200)]
ACCENT = (255, 100, 80)
GREEN = (120, 220, 140)
DIM = (80, 90, 140)
FG = (200, 210, 240)
DARK_BG = (10, 12, 28)
BAR_BG = (16, 18, 34)


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except (IOError, OSError):
        return ImageFont.load_default()


def draw_stars(draw, count=180):
    for _ in range(count):
        x = random.randint(0, W)
        y = random.randint(0, H)
        r = random.choice([1, 1, 1, 1.5, 1.5, 2])
        c = random.choice(STAR_COLORS)
        alpha = random.uniform(0.4, 1.0)
        c = tuple(int(ch * alpha) for ch in c)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)


def draw_glow(draw, cx, cy, radius, color):
    for i in range(radius, 0, -1):
        a = int(30 * (1 - i / radius))
        c = (*color, a)
        draw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=c)


def draw():
    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Stars
    draw_stars(draw, 200)

    # Nebula glow
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([-200, 100, 600, 600], fill=(60, 30, 120, 25))
    gdraw.ellipse([700, -100, 1300, 500], fill=(100, 30, 60, 20))
    gdraw.ellipse([300, 400, 900, 700], fill=(30, 60, 120, 20))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img, glow)

    # Bottom bar — brutalist thick line
    draw.rectangle([0, H - 80, W, H], fill=DARK_BG)
    draw.rectangle([0, H - 82, W, H - 78], fill=ACCENT)

    # Top accent line
    draw.rectangle([0, 0, W, 4], fill=ACCENT)

    # Big bold title
    font_huge = get_font(FONT_BOLD, 64)
    font_sub = get_font(FONT, 22)
    font_tag = get_font(FONT, 16)
    font_feat = get_font(FONT, 18)

    # Terminal character blocks (brutalist)
    block_chars = [">>", "$_", "#!", "<>", "[]", "{}", "()"]
    for i, ch in enumerate(block_chars):
        bx = 60 + i * 170
        by = 60
        draw.rectangle([bx, by, bx + 130, by + 50], fill=DARK_BG, outline=(30, 35, 60))
        c = get_font(FONT_BOLD, 28)
        draw.text((bx + 10, by + 10), ch, fill=ACCENT if i % 2 == 0 else GREEN, font=c)

    # Main title
    title = "PYTHON"
    tw = draw.textlength(title, font=font_huge)
    draw.text(((W - tw) // 2, 150), title, fill=FG, font=font_huge)

    title2 = "INTERACTIVE TUTORIAL"
    font_mid = get_font(FONT_BOLD, 36)
    tw2 = draw.textlength(title2, font=font_mid)
    draw.text(((W - tw2) // 2, 220), title2, fill=ACCENT, font=font_mid)

    # Subtitle
    subtitle = "LEARN. PRACTICE. BUILD. — ALL IN YOUR TERMINAL"
    sw = draw.textlength(subtitle, font=font_sub)
    draw.text(((W - sw) // 2, 280), subtitle, fill=DIM, font=font_sub)

    # Stats bar — brutalist horizontal
    stats_y = 340
    bar_h = 56
    stats = [
        ("56 TOPICS", "7 phases"),
        ("150+ CHALLENGES", "validated exercises"),
        ("7 PROJECTS", "step-by-step builds"),
        ("BUILT-IN IDE", "Fresh IDE sandbox"),
    ]
    gap = 16
    sw_t = (W - 2 * gap) // len(stats)
    for i, (label, desc) in enumerate(stats):
        sx = gap + i * sw_t
        draw.rectangle([sx, stats_y, sx + sw_t - 4, stats_y + bar_h], fill=DARK_BG, outline=(30, 35, 60))
        draw.text((sx + 12, stats_y + 8), label, fill=GREEN, font=get_font(FONT_BOLD, 18))
        draw.text((sx + 12, stats_y + 32), desc, fill=DIM, font=get_font(FONT, 14))

    # Command line at bottom
    cmd_y = H - 60
    prompt = "$  pip install git+https://github.com/Manas-thakur/python-tutorial.git"
    draw.text((40, cmd_y), prompt, fill=GREEN, font=get_font(FONT, 18))
    cmd_x = 42 + int(draw.textlength(prompt, font=get_font(FONT, 18)))
    cursor = Image.new("RGBA", (12, 22), ACCENT)
    img = Image.alpha_composite(img, Image.alpha_composite(
        Image.new("RGBA", (W, H), (0, 0, 0, 0)),
        img
    ))

    # Cursor blink
    draw.rectangle([cmd_x, cmd_y + 2, cmd_x + 10, cmd_y + 22], fill=ACCENT)

    # Bottom-right tag
    tag = "pytut"
    tg = get_font(FONT_BOLD, 24)
    tlx = draw.textlength(tag, font=tg)
    draw.rectangle([W - tlx - 40, H - 70, W, H - 18], fill=(0, 0, 0, 0))
    draw.text((W - tlx - 24, H - 62), tag, fill=DIM, font=tg)

    out = os.path.join(os.path.dirname(__file__), "banner", "banner.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img = img.convert("RGB")
    img.save(out)
    print(f"Generated {out} ({W}x{H})")


if __name__ == "__main__":
    draw()
