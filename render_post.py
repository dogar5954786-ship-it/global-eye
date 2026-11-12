#!/usr/bin/env python3
"""Render a Global Eye news post picture (1080x1350, Facebook 4:5).

Usage:
  python3 render_post.py --category tech --headline "..." --sub "..." \
      --emoji "🤖" --logo logo.png --out post.jpg [--breaking]
"""
import argparse, datetime, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1350
NAVY = (8, 18, 38)
NAVY2 = (14, 34, 68)
WHITE = (255, 255, 255)
SOFT = (190, 205, 228)

CATS = {
    "tech":     ("TECH",     (0, 174, 255),  "💻"),
    "sports":   ("SPORTS",   (0, 200, 120),  "🏆"),
    "politics": ("POLITICS", (255, 170, 0),  "🏛️"),
    "climate":  ("CLIMATE",  (0, 210, 200),  "🌍"),
    "world":    ("WORLD",    (90, 140, 255), "🌐"),
}

def font(names, size):
    dirs = ["/usr/share/fonts/opentype/inter/", "/usr/share/fonts/truetype/google-fonts/",
            "/usr/share/fonts/truetype/dejavu/"]
    for n in names:
        for d in dirs:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)

def emoji_img(ch, px):
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    except OSError:
        return None
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    bbox = im.getbbox()
    if not bbox:
        return None
    im = im.crop(bbox)
    s = px / max(im.size)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)

def wrap(draw, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=CATS.keys())
    ap.add_argument("--headline", required=True)
    ap.add_argument("--sub", default="")
    ap.add_argument("--emoji", default="")
    ap.add_argument("--logo", default="logo.png")
    ap.add_argument("--date", default=datetime.date.today().strftime("%d %B %Y"))
    ap.add_argument("--breaking", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    label, accent, default_emoji = CATS[a.category]
    em = a.emoji or default_emoji

    # Background: vertical navy gradient + accent glow + globe grid lines
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        c = tuple(int(NAVY2[i] * (1 - t) + NAVY[i] * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 700, 120, W + 300, 1120], fill=accent + (70,))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.alpha_composite(img.convert("RGBA"), glow)

    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gr = ImageDraw.Draw(grid)
    cx, cy, R = W - 170, 520, 430
    for k in range(-4, 5):  # latitude ellipses
        ry = abs(k) / 4 * R
        hh = math.sqrt(max(R * R - ry * ry, 0))
        yy = cy + (k / 4) * R
        gr.line([(cx - hh, yy), (cx + hh, yy)], fill=(255, 255, 255, 22), width=2)
    for k in range(1, 5):  # longitude ellipses
        rx = R * k / 4
        gr.ellipse([cx - rx, cy - R, cx + rx, cy + R], outline=(255, 255, 255, 22), width=2)
    gr.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(255, 255, 255, 34), width=3)
    img = Image.alpha_composite(img, grid)

    # Big story emoji in the background (faded)
    e = emoji_img(em, 360)
    if e:
        e = e.copy()
        e.putalpha(e.getchannel("A").point(lambda v: int(v * 0.55)))
        img.alpha_composite(e, (W - e.width - 90, 200))

    d = ImageDraw.Draw(img)

    # Top bar: logo + page name
    if os.path.exists(a.logo):
        lg = Image.open(a.logo).convert("RGBA")
        lg.thumbnail((110, 110), Image.LANCZOS)
        img.alpha_composite(lg, (60, 60 + (110 - lg.height) // 2))
        name_x = 60 + lg.width + 24
    else:
        name_x = 60
    d.text((name_x, 82), "GLOBAL EYE", font=font(["Inter-Black.otf", "Poppins-Bold.ttf"], 46), fill=WHITE)
    d.text((name_x, 136), "World updates, every day", font=font(["Inter-Medium.otf", "Inter-Regular.otf"], 24), fill=SOFT)

    # Category pill (+ BREAKING pill)
    fpill = font(["Inter-ExtraBold.otf", "Poppins-Bold.ttf"], 30)
    x, y = 60, 600
    if a.breaking:
        tw = d.textlength("BREAKING", font=fpill)
        d.rounded_rectangle([x, y, x + tw + 44, y + 58], 29, fill=(230, 40, 50))
        d.text((x + 22, y + 29), "BREAKING", font=fpill, fill=WHITE, anchor="lm")
        x += tw + 44 + 16
    tw = d.textlength(label, font=fpill)
    d.rounded_rectangle([x, y, x + tw + 44, y + 58], 29, fill=accent)
    d.text((x + 22, y + 29), label, font=fpill, fill=NAVY, anchor="lm")

    # Headline: shrink font until it fits in 5 lines
    maxw = W - 120
    for size in range(84, 46, -4):
        fh = font(["Inter-ExtraBold.otf", "Poppins-Bold.ttf"], size)
        lines = wrap(d, a.headline, fh, maxw)
        if len(lines) <= 5:
            break
    lh = int(size * 1.15)
    y = 690
    for ln in lines:
        d.text((60, y), ln, font=fh, fill=WHITE)
        y += lh

    # Accent rule + sub line
    y += 24
    d.rectangle([60, y, 180, y + 8], fill=accent)
    y += 36
    if a.sub:
        fs = font(["Inter-Medium.otf", "Inter-Regular.otf"], 34)
        for ln in wrap(d, a.sub, fs, maxw)[:3]:
            d.text((60, y), ln, font=fs, fill=SOFT)
            y += 46

    # Footer
    d.rectangle([0, H - 96, W, H], fill=(5, 12, 26))
    d.rectangle([0, H - 96, W, H - 92], fill=accent)
    ff = font(["Inter-SemiBold.otf", "Inter-Medium.otf"], 28)
    d.text((60, H - 48), a.date, font=ff, fill=SOFT, anchor="lm")
    d.text((W - 60, H - 48), "Full story in the caption 👇".replace(" 👇", ""), font=ff, fill=WHITE, anchor="rm")

    img.convert("RGB").save(a.out, "JPEG", quality=90)
    print(a.out, os.path.getsize(a.out))

if __name__ == "__main__":
    main()
