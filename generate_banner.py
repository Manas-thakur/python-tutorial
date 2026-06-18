"""Generate a 1200x630 GitHub social preview banner — brutalist space theme."""

import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

W, H = 1200, 630
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

random.seed(42)

BG = (4, 4, 14)
ACCENT = (255, 100, 80)
GREEN = (120, 220, 140)
DIM = (80, 90, 140)
FG = (200, 210, 240)
DARK_BG = (10, 12, 28)


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except (IOError, OSError):
        return ImageFont.load_default()


def draw_stars(draw, count=200):
    for _ in range(count):
        x = random.randint(0, W)
        y = random.randint(0, H)
        r = random.choice([1, 1, 1, 1.5, 1.5, 2])
        bright = random.uniform(0.4, 1.0)
        base = random.choice([
            (180, 190, 220), (200, 210, 240), (220, 230, 255), (140, 160, 200)
        ])
        c = tuple(int(ch * bright) for ch in base)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)


def make_glow(size, ellipses):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for box, color in ellipses:
        draw.ellipse(box, fill=color)
    return img.filter(ImageFilter.GaussianBlur(60))


def draw():
    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Stars
    draw_stars(draw, 220)

    # Nebula glow layers
    glow = make_glow((W, H), [
        ((-200, 100, 600, 600), (60, 30, 120, 30)),
        ((700, -100, 1300, 500), (100, 30, 60, 25)),
        ((300, 400, 900, 700), (30, 60, 120, 20)),
    ])
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Bottom bar
    draw.rectangle([0, H - 80, W, H], fill=DARK_BG)
    draw.rectangle([0, H - 82, W, H - 78], fill=ACCENT)

    # Top accent line
    draw.rectangle([0, 0, W, 4], fill=ACCENT)

    # Terminal character blocks
    chars = [(">>", 0), ("$_", 1), ("#!", 0), ("<>", 1), ("[]", 0), ("{}", 1), ("()", 0)]
    for i, (ch, parity) in enumerate(chars):
        bx = 50 + i * 158
        by = 50
        draw.rectangle([bx, by, bx + 128, by + 46], fill=DARK_BG, outline=(30, 35, 60))
        f = get_font(FONT_BOLD, 26)
        draw.text((bx + 12, by + 8), ch, fill=ACCENT if parity == 0 else GREEN, font=f)

    # Title
    t1 = get_font(FONT_BOLD, 64)
    t2 = get_font(FONT_BOLD, 38)

    title = "PYTHON"
    tw = draw.textlength(title, font=t1)
    draw.text(((W - tw) / 2, 135), title, fill=FG, font=t1)

    subtitle = "INTERACTIVE TUTORIAL"
    sw = draw.textlength(subtitle, font=t2)
    draw.text(((W - sw) / 2, 210), subtitle, fill=ACCENT, font=t2)

    # Tagline
    tag_f = get_font(FONT, 20)
    tag = "LEARN. PRACTICE. EXPERIMENT. BUILD. — ALL IN YOUR TERMINAL"
    tw = draw.textlength(tag, font=tag_f)
    draw.text(((W - tw) / 2, 270), tag, fill=DIM, font=tag_f)

    # Stats boxes
    boxes = [
        ("56 TOPICS", "7 phases"),
        ("150+ CHALLENGES", "validated exercises"),
        ("7 PROJECTS", "step-by-step builds"),
        ("FRESH IDE", "built-in playground"),
    ]
    bx_w = 260
    bx_h = 60
    bx_gap = 24
    total_w = len(boxes) * bx_w + (len(boxes) - 1) * bx_gap
    start_x = (W - total_w) / 2
    by = 320

    for i, (label, desc) in enumerate(boxes):
        bx = start_x + i * (bx_w + bx_gap)
        draw.rectangle([bx, by, bx + bx_w, by + bx_h], fill=DARK_BG, outline=(30, 35, 60))
        lf = get_font(FONT_BOLD, 17)
        df = get_font(FONT, 13)
        draw.text((bx + 14, by + 8), label, fill=GREEN, font=lf)
        draw.text((bx + 14, by + 34), desc, fill=DIM, font=df)

    # Install command
    py = H - 58
    prompt = "$  pip install git+https://github.com/Manas-thakur/python-tutorial.git"
    pf = get_font(FONT, 18)
    draw.text((38, py), prompt, fill=GREEN, font=pf)
    cx = 40 + int(draw.textlength(prompt, font=pf))
    draw.rectangle([cx, py + 2, cx + 10, py + 20], fill=ACCENT)

    # Bottom-right tag
    tf = get_font(FONT_BOLD, 22)
    tag_s = "pytut"
    tlx = draw.textlength(tag_s, font=tf)
    draw.text((W - tlx - 30, H - 62), tag_s, fill=DIM, font=tf)

    img = img.convert("RGB")
    out = os.path.join(os.path.dirname(__file__), "banner", "banner.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print(f"Generated {out} ({W}x{H})")


if __name__ == "__main__":
    draw()
