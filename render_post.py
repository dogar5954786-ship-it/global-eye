#!/usr/bin/env python3
"""Render a Global Eye news post picture (1080x1350, Facebook 4:5).

Put [square brackets] around 1-3 key words in the headline to highlight them.

Usage:
  python3 render_post.py --style split --category tech \
      --headline "OpenAI [launches] new model" --sub "..." --emoji "🤖" \
      --out post.jpg [--breaking] [--no-tags]
Styles: split | neon | stack
"""
import argparse, math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
WHITE = (255, 255, 255)
INK = (10, 20, 40)

# category: label, main colour, second colour (for gradients), default emoji
CATS = {
    "tech":     ("TECH",     (0, 160, 255), (120, 60, 255), "💻"),
    "sports":   ("SPORTS",   (0, 200, 110), (0, 120, 200),  "🏆"),
    "politics": ("POLITICS", (255, 150, 0), (230, 40, 70),  "🏛️"),
    "climate":  ("CLIMATE",  (0, 200, 190), (0, 110, 220),  "🌍"),
    "world":    ("WORLD",    (80, 130, 255), (150, 60, 220), "🌐"),
}
RED = (235, 35, 50)


def font(size, weight="black"):
    names = {
        "black": ["Inter-Black.otf", "Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
        "xbold": ["Inter-ExtraBold.otf", "Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
        "bold": ["Inter-Bold.otf", "Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
        "semi": ["Inter-SemiBold.otf", "Inter-Medium.otf", "DejaVuSans.ttf"],
        "med": ["Inter-Medium.otf", "Inter-Regular.otf", "DejaVuSans.ttf"],
    }[weight]
    dirs = ["/usr/share/fonts/opentype/inter/", "/usr/share/fonts/truetype/google-fonts/",
            "/usr/share/fonts/truetype/dejavu/"]
    for n in names:
        for d in dirs:
            if os.path.exists(d + n):
                return ImageFont.truetype(d + n, size)
    return ImageFont.load_default(size)


def emoji_img(ch, px):
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
    except OSError:
        return None
    im = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((90, 90), ch, font=f, embedded_color=True, anchor="mm")
    bb = im.getbbox()
    if not bb:
        return None
    im = im.crop(bb)
    s = px / max(im.size)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def fade(im, k):
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
    return im


def gradient(w, h, c1, c2, diagonal=True):
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        for x in range(0, w, 1):
            t = ((x / w) * 0.45 + (y / h) * 0.55) if diagonal else y / h
            px[x, y] = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))
    return g


def parse_words(headline):
    """'A [big] win' -> [('A',False),('big',True),('win',False)]"""
    out, hot = [], False
    for w in headline.split():
        start = w.startswith("[")
        end = w.endswith("]")
        if start:
            hot = True
        out.append((w.strip("[]"), hot))
        if end:
            hot = False
    return out


def wrap_words(draw, words, f, maxw):
    lines, cur = [], []
    for w in words:
        test = " ".join(x[0] for x in cur + [w])
        if draw.textlength(test, font=f) <= maxw or not cur:
            cur.append(w)
        else:
            lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)
    return lines


def fit_headline(draw, words, maxw, max_lines, start, stop, weight="black"):
    for size in range(start, stop, -4):
        f = font(size, weight)
        lines = wrap_words(draw, words, f, maxw)
        if len(lines) <= max_lines:
            return f, size, lines
    return f, size, lines


def draw_words(draw, lines, f, size, x, y, base, hot, lh=1.08, align="left", cx=None):
    sp = draw.textlength(" ", font=f)
    for ln in lines:
        lw = sum(draw.textlength(w, font=f) for w, _ in ln) + sp * (len(ln) - 1)
        xx = (cx - lw / 2) if align == "center" else x
        for w, h in ln:
            draw.text((xx, y), w, font=f, fill=hot if h else base)
            xx += draw.textlength(w, font=f) + sp
        y += int(size * lh)
    return y


def wrap_plain(draw, text, f, maxw):
    return [" ".join(w for w, _ in ln) for ln in wrap_words(draw, [(w, False) for w in text.split()], f, maxw)]


def logo_block(img, x, y, logo_path, dark_text=False, h=96):
    d = ImageDraw.Draw(img)
    if os.path.exists(logo_path):
        lg = Image.open(logo_path).convert("RGBA")
        lg.thumbnail((int(h * 1.6), h), Image.LANCZOS)
        img.alpha_composite(lg, (x, y + (h - lg.height) // 2))
        x += lg.width + 20
    col = INK if dark_text else WHITE
    d.text((x, y + h // 2 - 4), "GLOBAL EYE", font=font(42, "black"), fill=col, anchor="lb")
    d.text((x + 2, y + h // 2 + 4), "World updates, every day", font=font(22, "med"),
           fill=(80, 95, 120) if dark_text else (200, 215, 235), anchor="lt")


def pill(d, x, y, text, bg, fg, f):
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + tw + 40, y + 54], 27, fill=bg)
    d.text((x + 20, y + 27), text, font=f, fill=fg, anchor="lm")
    return x + tw + 40 + 14


def tags(d, x, y, a, label, accent, fg=INK):
    if a.no_tags:
        return
    f = font(28, "xbold")
    if a.breaking:
        x = pill(d, x, y, "● BREAKING", RED, WHITE, f)
    pill(d, x, y, label, accent, fg, f)


# ---------------------------------------------------------------- STYLE: SPLIT
def style_split(a, label, c1, c2, em, logo):
    """Colour gradient top with a giant icon, white card bottom with headline."""
    img = gradient(W, H, c2, c1).convert("RGBA")
    d = ImageDraw.Draw(img)
    # light rays from the icon
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    cx, cy = W // 2 + 170, 380
    for i in range(18):
        ang = i * math.pi / 9
        rd.polygon([(cx, cy), (cx + 1400 * math.cos(ang), cy + 1400 * math.sin(ang)),
                    (cx + 1400 * math.cos(ang + 0.12), cy + 1400 * math.sin(ang + 0.12))],
                   fill=(255, 255, 255, 18))
    img = Image.alpha_composite(img, rays)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - 260, cy - 260, cx + 260, cy + 260], fill=(255, 255, 255, 90))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(90)))
    e = emoji_img(em, 380)
    if e:
        sh = Image.new("RGBA", (e.width + 80, e.height + 80), (0, 0, 0, 0))
        sh.paste((0, 0, 0, 255), (40, 40), e.getchannel("A").point(lambda v: int(v * 0.35)))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (cx - e.width // 2 - 26, cy - e.height // 2 - 18))
        img.alpha_composite(e, (cx - e.width // 2, cy - e.height // 2))
    # white card with slanted top edge
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    top = 700
    cd.polygon([(0, top + 70), (W, top - 30), (W, H), (0, H)], fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img, card)
    d = ImageDraw.Draw(img)
    d.polygon([(0, top + 70), (W, top - 30), (W, top - 16), (0, top + 84)], fill=c1)
    logo_block(img, 50, 50, logo)
    tags(d, 60, top + 40 if a.no_tags else top + 70, a, label, c1, WHITE)
    words = parse_words(a.headline)
    f, size, lines = fit_headline(d, words, W - 120, 4, 96, 50)
    space_top = top + (110 if a.no_tags else 160)
    block = len(lines) * int(size * 1.08) + (100 if a.sub else 0)
    y = space_top + max(0, (H - 100 - space_top - block) // 2)
    y = draw_words(d, lines, f, size, 60, y, INK, c2 if sum(c2) < 450 else c1)
    if a.sub:
        y += 10
        for ln in wrap_plain(d, a.sub, font(32, "med"), W - 120)[:2]:
            d.text((60, y), ln, font=font(32, "med"), fill=(85, 95, 115))
            y += 44
    d.rectangle([0, H - 78, W, H], fill=INK)
    d.text((W // 2, H - 39), "FULL STORY IN THE CAPTION  ↓", font=font(26, "xbold"), fill=WHITE, anchor="mm")
    return img


# ---------------------------------------------------------------- STYLE: NEON
def style_neon(a, label, c1, c2, em, logo):
    """Near-black, glowing frame, huge headline with neon key words, ticker band."""
    img = Image.new("RGBA", (W, H), (6, 8, 18, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-300, -200, 700, 700], fill=c2 + (120,))
    gd.ellipse([500, 500, 1400, 1400], fill=c1 + (110,))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(200)))
    # dotted world-grid texture
    dots = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    for yy in range(20, H, 34):
        for xx in range(20, W, 34):
            dd.ellipse([xx, yy, xx + 3, yy + 3], fill=(255, 255, 255, 28))
    img = Image.alpha_composite(img, dots)
    e = emoji_img(em, 520)
    if e:
        img.alpha_composite(fade(e.rotate(-12, expand=True, resample=Image.BICUBIC), 0.20), (W - 500, 110))
    # glowing frame
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rounded_rectangle([28, 28, W - 28, H - 28], 36, outline=c1 + (255,), width=6)
    img = Image.alpha_composite(img, fr.filter(ImageFilter.GaussianBlur(10)))
    img = Image.alpha_composite(img, fr)
    d = ImageDraw.Draw(img)
    logo_block(img, 66, 66, logo)
    words = parse_words(a.headline)
    f, size, lines = fit_headline(d, words, W - 140, 5, 104, 56)
    block_h = len(lines) * int(size * 1.02)
    y = max(330, 900 - block_h)
    tags(d, 70, y - 90, a, label, c1)
    # neon glow behind highlighted words
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_words(ImageDraw.Draw(gl), lines, f, size, 70, y, (0, 0, 0, 0), c1 + (255,), lh=1.02)
    img = Image.alpha_composite(img, gl.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(img)
    y = draw_words(d, lines, f, size, 70, y, WHITE, c1, lh=1.02)
    if a.sub:
        y += 26
        for ln in wrap_plain(d, a.sub, font(34, "semi"), W - 140)[:2]:
            d.text((70, y), ln, font=font(34, "semi"), fill=(200, 210, 230))
            y += 46
    # ticker band
    band_y = H - 190
    d.rectangle([28, band_y, W - 28, band_y + 70], fill=c1)
    d.rectangle([28, band_y, 250, band_y + 70], fill=WHITE)
    d.text((139, band_y + 35), "GLOBAL EYE", font=font(28, "black"), fill=INK, anchor="mm")
    d.text((280, band_y + 35), "FULL STORY IN THE CAPTION  ↓", font=font(28, "xbold"), fill=INK, anchor="lm")
    return img


# ---------------------------------------------------------------- STYLE: STACK
def style_stack(a, label, c1, c2, em, logo):
    """Bold gradient, scattered icons, headline on stacked highlight bars."""
    img = gradient(W, H, c1, c2).convert("RGBA")
    # scattered faded icons as pattern
    e_small = emoji_img(em, 120)
    if e_small:
        rnd = random.Random(a.headline)
        for _ in range(14):
            r = e_small.rotate(rnd.randint(-30, 30), expand=True)
            ic = Image.new("RGBA", r.size, (255, 255, 255, 0))
            ic.putalpha(r.getchannel("A").point(lambda v: int(v * 0.10)))
            img.alpha_composite(ic, (rnd.randint(-40, W - 80), rnd.randint(150, H - 250)))
    e = emoji_img(em, 330)
    if e:
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        cx, cy = W - 250, 360
        rd.ellipse([cx - 230, cy - 230, cx + 230, cy + 230], fill=(255, 255, 255, 235))
        img = Image.alpha_composite(img, ring)
        ImageDraw.Draw(img).ellipse([cx - 248, cy - 248, cx + 248, cy + 248], outline=WHITE, width=6)
        img.alpha_composite(e, (cx - e.width // 2, cy - e.height // 2))
    d = ImageDraw.Draw(img)
    logo_block(img, 50, 50, logo)
    words = parse_words(a.headline)
    f, size, lines = fit_headline(d, words, W - 170, 5, 80, 48)
    lh = int(size * 1.32)
    y = max(660, 1090 - len(lines) * lh)
    tags(d, 60, y - 84, a, label, WHITE)
    sp = d.textlength(" ", font=f)
    for ln in lines:
        text_w = sum(d.textlength(w, font=f) for w, _ in ln) + sp * (len(ln) - 1)
        d.rectangle([48, y - 6, 48 + text_w + 36, y + int(size * 1.18)], fill=INK)
        xx = 66
        for w, h in ln:
            d.text((xx, y + int(size * 0.06)), w, font=f, fill=c1 if h else WHITE)
            xx += d.textlength(w, font=f) + sp
        y += lh
    if a.sub:
        y += 14
        for ln in wrap_plain(d, a.sub, font(32, "semi"), W - 120)[:2]:
            d.text((60, y), ln, font=font(32, "semi"), fill=WHITE)
            y += 44
    d.rectangle([0, H - 80, W, H], fill=WHITE)
    d.text((W // 2, H - 40), "FULL STORY IN THE CAPTION  ↓", font=font(26, "black"), fill=INK, anchor="mm")
    return img


STYLES = {"split": style_split, "neon": style_neon, "stack": style_stack}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="split", choices=STYLES.keys())
    ap.add_argument("--category", required=True, choices=CATS.keys())
    ap.add_argument("--headline", required=True)
    ap.add_argument("--sub", default="")
    ap.add_argument("--emoji", default="")
    ap.add_argument("--logo", default=os.path.join(HERE, "logo.png"))
    ap.add_argument("--breaking", action="store_true")
    ap.add_argument("--no-tags", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    label, c1, c2, de = CATS[a.category]
    img = STYLES[a.style](a, label, c1, c2, a.emoji or de, a.logo)
    img.convert("RGB").save(a.out, "JPEG", quality=90)
    print(a.out, os.path.getsize(a.out))


if __name__ == "__main__":
    main()
