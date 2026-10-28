"""Clickbait thumbnail styles for the long videos, borrowed from the niches where they work best (research Oct 28,
CLAUDE.md '## CLICKBAIT'); none of them is used by the big WW2 channels yet:
- case:     Fern's case board (20M/16M/11M): a 1945 file on manila paper, pinned photos, red strings, a rubber stamp.
- glow:     Fern's 'WORSE THAN HITLER?' (11M): the person cut out with a red rim light on a dark tinted scene,
            the other side of the story huge and dark behind, a short question on a red box.
- mystery:  Barely Sociable (4-13M): near-black, one object in a pool of light, a handwritten question.
- headline: The Infographics Show ('23,000 FEET DOWN', 'NO ESCAPE'): 2-3 words of stakes, huge, over a vivid picture.
Honest rule (YouTube's Test & compare picks by WATCH TIME, so a promise the video does not keep loses): every word
and stamp must be a fact of the story (McVay WAS convicted: 'GUILTY' is true). No fake documents, no censor bars."""
import pathlib, random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

import shorts as S
import pastrak as P
from shorts import W

TW, TH = 1280, 720
FONTS = pathlib.Path("fonts")
BEBAS, MARKER, TYPE = FONTS / "BebasNeue-Regular.ttf", FONTS / "PermanentMarker-Regular.ttf", \
    FONTS / "SpecialElite-Regular.ttf"
RED = (225, 20, 30)
_SESS = {}


def font(f, size):
    return ImageFont.truetype(str(f), int(size))


def prepared(path, p):
    """A story picture: trimmed, colorized (DDColor; warm tone when it gives up or color='tone'), upscaled, vivid."""
    src = pathlib.Path(path)
    if p.get("trim"):
        t = W / f"tt_{src.stem[:40]}_{abs(hash(tuple(p['trim']))) % 10 ** 6}.jpg"
        P.still(src, p["trim"]).save(t, quality=95)
        src = t
    c = p.get("color", True)
    if c == "tone":
        src = S.warm_tone(src)
    elif c and S.toned(src):
        done = S.colorize(src)
        src = S.warm_tone(src) if done == src else done
    src = S.upscale(src, most=int(p.get("most", 900)))
    im = ImageEnhance.Contrast(P.still(src)).enhance(float(p.get("contrast", 1.15)))
    return ImageEnhance.Color(im).enhance(float(p.get("saturation", 1.25)))


def cutout_mask(im):
    """The person/object as an L mask (U2-Net-p, Apache-2.0, ~4.6 MB, rembg's model file, kept in ~/ddcolor)."""
    import onnxruntime as ort
    if "u2" not in _SESS:
        f = S.DDCOLOR_DIR / "u2netp.onnx"
        if not f.exists():
            import requests
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(requests.get("https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx",
                                       timeout=120).content)
        _SESS["u2"] = ort.InferenceSession(str(f), providers=["CPUExecutionProvider"])
    sess = _SESS["u2"]
    x = np.asarray(im.convert("RGB").resize((320, 320), Image.BICUBIC), np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    m = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = (m - m.min()) / max(1e-6, m.max() - m.min())
    m = np.clip((m - 0.15) / 0.6, 0, 1)
    return Image.fromarray((m * 255).astype(np.uint8)).resize(im.size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(1))


def paper(size, base=(212, 188, 140), seed=7):
    """Old manila paper: fibre noise, darker stained edges."""
    rnd = np.random.default_rng(seed)
    w, h = size
    n = rnd.normal(0, 1, (h // 4, w // 4)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n + 3) * 40).clip(0, 255).astype(np.uint8)).resize(size, Image.BICUBIC),
                   np.float32) / 255 - 0.5
    img = np.asarray(Image.new("RGB", size, base), np.float32) + n[..., None] * 38
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.clip(1 - ((xx - w / 2) / (w * 0.62)) ** 2 - ((yy - h / 2) / (h * 0.62)) ** 2, 0, 1) ** 0.5
    img *= (0.62 + 0.38 * edge)[..., None]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def cork(size, seed=11):
    """Fern's corkboard: warm brown with dark and light granules."""
    rnd = np.random.default_rng(seed)
    w, h = size
    img = np.asarray(paper(size, base=(176, 122, 70), seed=seed), np.float32)
    for cell, dark, light in ((4, 0.93, 0.05), (7, 0.965, 0.03)):   # granules big enough to read at 320 px wide
        g = rnd.random((h // cell + 1, w // cell + 1))
        g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.NEAREST)) / 255
        img[g > dark] *= 0.62
        img[g < light] = img[g < light] * 0.7 + 70
    img = np.asarray(Image.fromarray(img.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)),
                     np.float32)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))


def desk(size, seed=5):
    """A dark wooden desk at night under one lamp: grain, a warm pool of light, black corners."""
    rnd = np.random.default_rng(seed)
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    grain = np.sin(yy / 7.0 + np.sin(xx / 90.0) * 3 + rnd.random() * 6) * 0.5 + 0.5
    grain = grain * 0.35 + rnd.normal(0, 0.08, (h, w))
    base = np.stack([62 + 40 * grain, 38 + 26 * grain, 22 + 14 * grain], -1)
    light = np.clip(1 - np.hypot((xx - w * 0.5) / (w * 0.62), (yy - h * 0.45) / (h * 0.75)), 0, 1) ** 1.3
    return Image.fromarray((base * (0.25 + 1.15 * light[..., None])).clip(0, 255).astype(np.uint8))


MARKER_RED = (205, 18, 24)


def marker_ellipse(d, box, color=MARKER_RED, width=8, seed=1):
    """A circle drawn by hand with a marker: wobbly, one and a quarter turns."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    pts = []
    for i in range(0, 451, 6):
        a = np.radians(i - 100)
        k = 1 + 0.04 * np.sin(i / 37) + rnd.uniform(-0.012, 0.012) + (0.06 if i > 360 else 0)
        pts.append((cx + rx * k * np.cos(a), cy + ry * k * np.sin(a)))
    d.line(pts, fill=color, width=width, joint="curve")


def marker_arrow(d, a, b, color=MARKER_RED, width=8, bend=0.18):
    """A hand-drawn curved arrow from a to b (pixels)."""
    (x1, y1), (x2, y2) = a, b
    mx, my = (x1 + x2) / 2 - (y2 - y1) * bend, (y1 + y2) / 2 + (x2 - x1) * bend
    pts = [((1 - t) ** 2 * x1 + 2 * (1 - t) * t * mx + t * t * x2, (1 - t) ** 2 * y1 + 2 * (1 - t) * t * my + t * t * y2)
           for t in np.linspace(0, 1, 40)]
    d.line(pts, fill=color, width=width, joint="curve")
    ang = np.arctan2(y2 - pts[-4][1], x2 - pts[-4][0])
    for s in (-1, 1):
        d.line((x2, y2, x2 - 38 * np.cos(ang + s * 0.5), y2 - 38 * np.sin(ang + s * 0.5)), fill=color, width=width)


def notes(im, v):
    """Handwritten marker notes, circles, arrows and strike-throughs on the board (positions 0-1 of the frame)."""
    d = ImageDraw.Draw(im)
    for c in v.get("circles") or []:
        marker_ellipse(d, (TW * c[0], TH * c[1], TW * c[2], TH * c[3]), seed=int(c[0] * 100))
    for a in v.get("arrows") or []:
        marker_arrow(d, (TW * a[0], TH * a[1]), (TW * a[2], TH * a[3]), bend=a[4] if len(a) > 4 else 0.18)
    for s in v.get("strikes") or []:
        for off in (0, 9):
            d.line((TW * s[0], TH * s[1] + off, TW * s[2], TH * s[3] + off), fill=MARKER_RED, width=10)
    for n in v.get("notes") or []:
        f = font(MARKER, n.get("size", 70))
        layer = Image.new("RGBA", (int(f.getlength(n["text"])) + 40, int(f.size * 1.6)), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((20, 6), n["text"], font=f,
                                   fill=tuple(n.get("color", MARKER_RED)) + (255,),
                                   stroke_width=n.get("stroke", 0), stroke_fill=(250, 245, 235, 255))
        layer = layer.rotate(n.get("angle", 0), expand=True, resample=Image.BICUBIC)
        im.alpha_composite(layer, (round(TW * n["x"] - layer.width / 2), round(TH * n["y"] - layer.height / 2)))


def polaroid(im, w, caption="", angle=0.0, ratio=0.82):
    """A print with a white border (wider at the bottom, a marker caption there), rotated, with a soft shadow."""
    pw, ph = w, round(w * ratio)
    photo = ImageOps.fit(im, (pw - 28, ph - 28), method=Image.LANCZOS)
    card = Image.new("RGB", (pw, ph + 52), (246, 243, 236))
    card.paste(photo, (14, 14))
    if caption:
        d = ImageDraw.Draw(card)
        f = font(MARKER, 30)
        while f.getlength(caption) > pw - 30 and f.size > 14:
            f = font(MARKER, f.size - 2)
        d.text((pw / 2, ph + 22), caption, font=f, fill=(25, 25, 30), anchor="mm")
    card = card.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (card.width + 40, card.height + 40), (0, 0, 0, 0))
    a = card.split()[3].point(lambda v: v * 0.55)
    sh.paste(Image.new("RGBA", card.size, (0, 0, 0, 255)), (26, 30), a)
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh.alpha_composite(card, (14, 14))
    return sh


def stamp(text, size=110, angle=-12, color=RED, seed=3):
    """A rubber stamp: bold letters in a double frame, ink worn away in spots, rotated."""
    f = font(BEBAS, size)
    tw = int(f.getlength(text))
    w, h = tw + size, int(size * 1.45)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w - 6, h - 6), radius=10, outline=255, width=9)
    d.rounded_rectangle((20, 20, w - 20, h - 20), radius=6, outline=255, width=3)
    d.text((w / 2, h / 2 + size * 0.04), text, font=f, fill=255, anchor="mm")
    rnd = np.random.default_rng(seed)
    wear = rnd.random((h // 3, w // 3))
    wear = np.asarray(Image.fromarray((wear * 255).astype(np.uint8)).resize((w, h), Image.NEAREST), np.float32) / 255
    a = (np.asarray(im, np.float32) * np.where(wear > 0.16, 0.92, 0.25)).astype(np.uint8)
    out = Image.new("RGBA", (w, h), color + (0,))
    out.putalpha(Image.fromarray(a))
    return out.rotate(angle, expand=True, resample=Image.BICUBIC)


def pin(d, x, y, r=13):
    d.ellipse((x - r + 3, y - r + 5, x + r + 3, y + r + 5), fill=(0, 0, 0, 110))
    d.ellipse((x - r, y - r, x + r, y + r), fill=(200, 25, 30), outline=(90, 0, 0), width=2)
    d.ellipse((x - r * 0.45, y - r * 0.55, x - r * 0.05, y - r * 0.15), fill=(255, 150, 150))


def headline(d, text, y, size=150, fill="white", key=None, width=TW - 80, stroke=9):
    """Big centred caps with a heavy black edge; `key` = one word on a red box (Infographics / Fern)."""
    f = font(BEBAS, size)
    while f.getlength(text) > width and f.size > 40:
        f = font(BEBAS, f.size - 6)
    x = (TW - f.getlength(text)) / 2
    for i, word in enumerate(text.split(" ")):
        ww = f.getlength(word)
        if key and word.strip("?!.,") == key:
            d.rectangle((x - 12, y + f.size * 0.08, x + ww + 12, y + f.size * 1.02), fill=RED)
            d.text((x, y), word, font=f, fill="white")
        else:
            d.text((x, y), word, font=f, fill=fill, stroke_width=stroke, stroke_fill="black")
        x += ww + f.getlength(" ")


def red_box_text(d, text, x, y, size=84, right=False):
    f = font(BEBAS, size)
    tw = f.getlength(text)
    if right:
        x = TW - x - tw - 24
    d.rectangle((x - 22, y - 6, x + tw + 22, y + size * 1.02), fill=RED)
    d.text((x, y - size * 0.05), text, font=f, fill="white")


# ---- the styles -----------------------------------------------------------------------------------------
def case(v, got):
    """Fern's board on a 1945 file: polaroids pinned, red strings between them, a stamp across the main one."""
    board = {"cork": cork, "desk": desk}.get(v.get("board"), paper)
    im = board((TW, TH)).convert("RGBA")
    d = ImageDraw.Draw(im)
    if v.get("label"):                                 # typed file label, top left
        f = font(TYPE, 40)
        d.rectangle((40, 30, 60 + f.getlength(v["label"]), 88), fill=(236, 226, 196), outline=(120, 100, 60))
        d.text((50, 36), v["label"], font=f, fill=(40, 30, 20))
    spots = []
    for it in v["items"]:
        pic = prepared(got[it["file"]][0], it)
        if it.get("x_crop") is not None or it.get("y_crop") is not None:
            pic = ImageOps.fit(pic, (pic.width, pic.width), centering=(it.get("x_crop", 0.5), it.get("y_crop", 0.4)))
        card = polaroid(pic, it.get("w", 360), it.get("caption", ""), it.get("angle", 0), it.get("ratio", 0.82))
        cx, cy = TW * it["x"], TH * it["y"]
        pos = (round(cx - card.width / 2), round(cy - card.height / 2))
        im.alpha_composite(card, pos)
        spots.append((cx, pos[1] + 34, card, pos))
    d = ImageDraw.Draw(im)
    for a, b in v.get("links") or [(i, i + 1) for i in range(len(spots) - 1)]:
        (x1, y1, *_), (x2, y2, *_) = spots[a], spots[b]
        d.line((x1, y1, x2, y2), fill=(120, 0, 0), width=7)
        d.line((x1, y1 - 1, x2, y2 - 1), fill=(210, 30, 35), width=4)
    for x, y, *_ in spots:
        pin(d, x, y)
    for it, (x, y, card, pos) in zip(v["items"], spots):
        if it.get("stamp"):
            s = stamp(it["stamp"], it.get("stamp_size", 120), it.get("stamp_angle", -14))
            im.alpha_composite(s, (round(pos[0] + card.width / 2 - s.width / 2),
                                   round(pos[1] + card.height * 0.55 - s.height / 2)))
    if v.get("stamp"):
        s = v["stamp"]
        st = stamp(s["text"], s.get("size", 120), s.get("angle", -10))
        im.alpha_composite(st, (round(TW * s["x"] - st.width / 2), round(TH * s["y"] - st.height / 2)))
    notes(im, v)
    if v.get("headline"):                              # big Bebas words on the board (bottom or top)
        h = v["headline"]
        headline(ImageDraw.Draw(im), h["text"].upper(), TH * h.get("y", 0.76), h.get("size", 150), key=h.get("key"))
    return im.convert("RGB")


def glow(v, got):
    """Fern's rim-light portrait: the scene dark and tinted, the person cut out with a red glow, the other side of
    the story huge and dark on the far side, a short question on a red box."""
    bg = prepared(got[v["bg"]["file"]][0], {**v["bg"], "color": v["bg"].get("color", False)})
    bg = ImageOps.fit(bg, (TW, TH), centering=(v["bg"].get("x", 0.5), v["bg"].get("y", 0.5)))
    bg = ImageEnhance.Brightness(ImageOps.grayscale(bg).convert("RGB")).enhance(0.38)
    tint = Image.new("RGB", (TW, TH), tuple(v.get("tint", (20, 40, 70))))
    im = Image.blend(bg, tint, 0.45).convert("RGBA")
    if v.get("shadow"):                                # the other side: big, dark, half out of the frame
        sp = v["shadow"]
        pic = prepared(got[sp["file"]][0], {**sp, "color": False})
        h = round(TH * sp.get("h", 1.15))
        pic = pic.resize((round(pic.width * h / pic.height), h), Image.LANCZOS)
        m = cutout_mask(pic).point(lambda a: a * sp.get("alpha", 0.55))
        dark = ImageEnhance.Brightness(pic).enhance(0.55).convert("RGBA")
        dark.putalpha(m)
        im.alpha_composite(dark, (round(TW * sp.get("x", 0.72) - pic.width / 2), TH - h + round(TH * 0.08)))
    s = v["subject"]
    pic = prepared(got[s["file"]][0], s)
    h = round(TH * s.get("h", 1.0))
    pic = pic.resize((round(pic.width * h / pic.height), h), Image.LANCZOS)
    m = cutout_mask(pic)
    x0, y0 = round(TW * s.get("x", 0.3) - pic.width / 2), TH - h
    halo = m.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(22))
    col = Image.new("RGBA", pic.size, tuple(v.get("glow", RED)) + (0,))
    col.putalpha(halo.point(lambda a: min(255, a * 1.6)))
    im.alpha_composite(col, (x0, y0))
    person = pic.convert("RGBA")
    person.putalpha(m)
    im.alpha_composite(person, (x0, y0))
    im = im.convert("RGB")
    if v.get("tag"):
        red_box_text(ImageDraw.Draw(im), v["tag"], TW * v.get("tag_x", 0.05), TH * v.get("tag_y", 0.08),
                     v.get("tag_size", 92), right=v.get("tag_right", True))
    return im


def mystery(v, got):
    """Barely Sociable: near-black, one picture in a pool of light, a handwritten question."""
    pic = prepared(got[v["file"]][0], {**v, "color": v.get("color", False)})
    pic = ImageOps.fit(pic, (TW, TH), centering=(v.get("x", 0.5), v.get("y", 0.5)))
    pic = ImageEnhance.Brightness(pic).enhance(v.get("bright", 0.8))
    yy, xx = np.mgrid[0:TH, 0:TW]
    cx, cy, r = v.get("light", (0.62, 0.62, 0.42))
    m = np.clip(1 - np.hypot((xx - TW * cx) / (TW * r), (yy - TH * cy) / (TH * r * 1.2)), 0, 1) ** 1.6
    im = Image.composite(pic, Image.new("RGB", (TW, TH), (6, 6, 8)),
                         Image.fromarray((m * 255).astype(np.uint8)))
    d = ImageDraw.Draw(im)
    y = TH * v.get("text_y", 0.1)
    for i, line in enumerate(v["text"]):
        f = font(MARKER, v.get("size", 96))
        d.text((TW * v.get("text_x", 0.05), y), line, font=f, fill=RED if i in v.get("red", []) else "white")
        y += f.size * 1.18
    return im


def headline_style(v, got):
    """The Infographics Show: 2-3 words of stakes, huge, over a vivid picture darkened at the top."""
    pic = prepared(got[v["file"]][0], v)
    im = ImageOps.fit(pic, (TW, TH), centering=(v.get("x", 0.5), v.get("y", 0.5)))
    shade = Image.linear_gradient("L").resize((TW, TH)).point(lambda a: int(210 * (1 - a / 255) ** 2.2))
    im = Image.composite(Image.new("RGB", (TW, TH), "black"), im, shade)
    d = ImageDraw.Draw(im)
    headline(d, v["text"].upper(), TH * v.get("text_y", 0.03), v.get("size", 170), key=v.get("key"))
    return im


# THE CHANNEL'S THUMBNAIL (Andrii, Oct 28: 'all thumbnails in this style'): the 1945 case file on manila paper,
# typed label top left, three pinned polaroids joined by red string: LEFT the machine or place, CENTRE the main
# person (biggest, the stamp across him), RIGHT the other side of the story; one rubber-stamp word that is a FACT
# of the story. Positions, sizes and angles below are the approved Indianapolis cover; story field `case`.
HOUSE = [{"x": 0.2, "y": 0.6, "w": 470, "angle": -7, "ratio": 0.82},
         {"x": 0.52, "y": 0.55, "w": 480, "angle": 3, "ratio": 0.95, "stamp_size": 150},
         {"x": 0.83, "y": 0.6, "w": 390, "angle": -5, "ratio": 1.1}]


def house_case(c, extra=None):
    """story `case` {label, left, center, right ({file, caption, trim, color, x_crop, y_crop...}), stamp} (+ a
    Test & compare variant's overrides: notes, circles, arrows, strikes, stamp) -> a full 'case' spec."""
    c = {**c, **(extra or {})}
    items = []
    for slot, lay in zip(("left", "center", "right"), HOUSE):
        it = {**lay, **c[slot]}
        if slot == "center" and c.get("stamp"):
            it["stamp"] = c["stamp"]
        items.append(it)
    spec = {"style": "case", "label": c.get("label", ""), "items": items, "note": c.get("note", "house case")}
    for k in ("notes", "circles", "arrows", "strikes", "headline", "board"):
        if c.get(k):
            spec[k] = c[k]
    return spec


STYLES = {"case": case, "glow": glow, "mystery": mystery, "headline": headline_style}


def render(v, got, out):
    im = STYLES[v["style"]](v, got)
    if v.get("flags"):
        d = ImageDraw.Draw(im)
        fx = 40
        for c in v["flags"]:
            f = P.flag(c, 120, 80)
            im.paste(f, (fx, TH - 120))
            d.rectangle((fx, TH - 120, fx + 119, TH - 41), outline="black", width=3)
            fx += 140
    im.save(out)
    return out
