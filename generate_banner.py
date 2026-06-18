"""Generate a 1200x630 GitHub social preview banner."""

from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"

BG = (10, 12, 22)
ACCENT = (0, 212, 255)
GREEN = (158, 206, 106)
DIM = (86, 95, 137)
FG = (169, 177, 214)

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except (IOError, OSError):
        return ImageFont.load_default()

def draw():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Terminal frame
    pad = 40
    draw.rectangle([pad, pad, W - pad, H - pad], outline=(50, 52, 70), width=2)
    draw.rectangle([pad + 2, pad + 2, W - pad - 2, H - pad - 2], fill=(15, 17, 26))

    # Title bar dots
    for bx, bc in [(pad + 12, (247, 118, 142)), (pad + 30, (255, 158, 100)), (pad + 48, (158, 206, 106))]:
        draw.ellipse([bx, pad + 10, bx + 10, pad + 20], fill=bc)

    # Title
    font_large = get_font(FONT_BOLD, 42)
    font_small = get_font(FONT, 20)
    font_tag = get_font(FONT, 16)
    font_feat = get_font(FONT, 18)

    title = "Python Interactive Tutorial"
    tw = draw.textlength(title, font=font_large)
    draw.text(((W - tw) // 2, 120), title, fill=FG, font=font_large)

    subtitle = "Learn. Practice. Experiment. Build."
    sw = draw.textlength(subtitle, font=font_small)
    draw.text(((W - sw) // 2, 185), subtitle, fill=ACCENT, font=font_small)

    # Feature boxes
    features = [
        ("56 Topics", "7 phases from fundamentals to AI"),
        ("150+ Challenges", "Coding exercises with validation"),
        ("7 Projects", "Step-by-step guided builds"),
        ("Built-in IDE", "Fresh IDE playground with F2"),
    ]
    box_y = 260
    box_w = (W - 2 * pad - 60) // 4
    box_h = 110
    for i, (title, desc) in enumerate(features):
        bx = pad + 30 + i * (box_w + 20)
        draw.rectangle([bx, box_y, bx + box_w, box_y + box_h], fill=(22, 25, 40), outline=(40, 42, 60))
        ttl = get_font(FONT_BOLD, 18) if i == 0 else get_font(FONT_BOLD, 16)
        tw2 = draw.textlength(title, font=ttl)
        draw.text((bx + (box_w - tw2) // 2, box_y + 15), title, fill=GREEN, font=ttl)
        ds = get_font(FONT, 14)
        dw = draw.textlength(desc, font=ds)
        draw.text((bx + (box_w - dw) // 2, box_y + 55), desc, fill=DIM, font=ds)

    # Terminal line
    cmd_x = pad + 30
    cmd_y = 420
    prompt = "$ pytut"
    pw = draw.textlength(prompt, font=font_small)
    draw.text((cmd_x, cmd_y), prompt, fill=GREEN, font=font_small)
    cursor = cmd_x + int(pw) + 4
    draw.rectangle([cursor, cmd_y + 2, cursor + 10, cmd_y + 20], fill=ACCENT)

    # Bottom tagline
    tagline = "pip install git+https://github.com/Manas-thakur/python-tutorial.git"
    tg = get_font(FONT, 18)
    tlx = draw.textlength(tagline, font=tg)
    draw.text(((W - tlx) // 2, 510), tagline, fill=DIM, font=tg)

    # Badges at bottom
    badge_texts = ["No browser needed", "Distraction-free", "Zero config", "Cross-platform"]
    badge_y = 555
    total_bw = 0
    for bt in badge_texts:
        total_bw += draw.textlength(bt, font=font_tag) + 24
    total_bw += (len(badge_texts) - 1) * 16
    bx_start = (W - total_bw) // 2
    cx = bx_start
    for bt in badge_texts:
        bw = draw.textlength(bt, font=font_tag) + 24
        draw.rounded_rectangle([cx, badge_y, cx + bw, badge_y + 28], radius=14, fill=(25, 28, 46))
        tw3 = draw.textlength(bt, font=font_tag)
        draw.text((cx + (bw - tw3) // 2, badge_y + 5), bt, fill=DIM, font=font_tag)
        cx += bw + 16

    out = os.path.join(os.path.dirname(__file__), "banner", "banner.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print(f"Generated {out} ({W}x{H})")

if __name__ == "__main__":
    draw()
