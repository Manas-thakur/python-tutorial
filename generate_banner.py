"""Generate a 1200x630 GitHub social preview banner."""

from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except (IOError, OSError):
        return ImageFont.load_default()


def draw():
    BG = (18, 22, 40)
    CARD = (30, 35, 55)
    RED = (220, 50, 40)
    GREEN = (50, 220, 100)
    WHITE = (255, 255, 255)
    MUTED = (155, 165, 200)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Top bar
    draw.rectangle([0, 0, W, 6], fill=RED)

    # Title — huge
    tf = get_font(FONT_BOLD, 78)
    title = "PYTHON TUTORIAL"
    tw = draw.textlength(title, font=tf)
    draw.text(((W - tw) / 2, 90), title, fill=WHITE, font=tf)

    # Subtitle
    sf = get_font(FONT, 24)
    sub = "56 topics  |  150+ challenges  |  7 projects  |  built-in IDE"
    sw = draw.textlength(sub, font=sf)
    draw.text(((W - sw) / 2, 200), sub, fill=MUTED, font=sf)

    # Feature boxes
    boxes = [
        ("LEARN", "56 guided topics\nacross 7 phases"),
        ("PRACTICE", "Coding challenges,\nquizzes & flashcards"),
        ("BUILD", "7 real projects\nwith step-by-step guides"),
    ]

    bw, bh = 310, 140
    gap = 35
    total = 3 * bw + 2 * gap
    sx = (W - total) / 2
    sy = 270

    for i, (title, desc) in enumerate(boxes):
        x = sx + i * (bw + gap)
        draw.rectangle([x, sy, x + bw, sy + bh], fill=CARD, outline=(50, 56, 80))

        # Number
        nf = get_font(FONT_BOLD, 26)
        lw = draw.textlength(title, font=nf)
        draw.text((x + (bw - lw) / 2, sy + 18), title, fill=RED, font=nf)

        # Description
        df = get_font(FONT, 17)
        for j, line in enumerate(desc.split("\n")):
            dw = draw.textlength(line, font=df)
            draw.text((x + (bw - dw) / 2, sy + 58 + j * 26), line, fill=MUTED, font=df)

    # Bottom bar
    draw.rectangle([0, H - 72, W, H], fill=(0, 0, 0))
    draw.rectangle([0, H - 72, W, H - 70], fill=RED)

    pf = get_font(FONT, 18)
    prompt = "$ pip install git+https://github.com/Manas-thakur/python-tutorial.git"
    draw.text((30, H - 56), prompt, fill=GREEN, font=pf)

    cx = 32 + int(draw.textlength(prompt, font=pf))
    draw.rectangle([cx, H - 52, cx + 10, H - 36], fill=WHITE)

    pf2 = get_font(FONT_BOLD, 22)
    tag = ">>> pytut"
    pw = draw.textlength(tag, font=pf2)
    draw.text((W - pw - 28, H - 64), tag, fill=(80, 85, 110), font=pf2)

    out = os.path.join(os.path.dirname(__file__), "banner", "banner.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, quality=95)
    print(f"Generated {out} ({W}x{H})")


if __name__ == "__main__":
    draw()
