"""16:9 MAP SHOTS for the long videos (The Entire War format, Andrii, Nov 10): plain light land, pale sea, the
coastlines of Natural Earth (map/land-10m.json, the Shorts bot's decoder), red dots with the place names and red
routes drawn while the camera pushes in slowly.
Story shot: {"s": 3, "map": {"places": [{"label": "TRIPOLI", "lat": 32.9, "lon": 13.2} | {"title": "Wikipedia
title", "label": "..."}], "routes": [[0, 1], [1, 2]], "pad": 0.35}}  (routes = place indexes, drawn in order)."""
import math, pathlib, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))  # shorts/jurgen/pastrak from ww2-bot
import shorts as S
from shorts import W

SIZE = (1920, 1080)
OVER = 1.12                       # the base map is drawn 12% bigger: the push-in happens inside it
SEA, LAND, COAST, GRID = (196, 210, 214), (232, 222, 196), (120, 108, 86), (182, 196, 200)
RED, INK = (196, 28, 28), (38, 30, 22)
FONT = pathlib.Path("fonts/BebasNeue-Regular.ttf")


def merc(lat):
    lat = max(-84.0, min(84.0, lat))
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def places_of(spec):
    """Places with coordinates: given in the story, or from the Wikipedia article ('title')."""
    ps = [dict(p) for p in spec["places"]]
    need = [p["title"] for p in ps if "lat" not in p and p.get("title")]
    got = S.wiki_coords(need) if need else {}
    out = []
    for p in ps:
        if "lat" not in p and p.get("title") in got:
            p["lat"], p["lon"] = got[p["title"]]
        if "lat" in p:
            p["label"] = str(p.get("label") or p.get("title", "")).upper()
            out.append(p)
    if len(out) < len(ps):
        print("map: places without coordinates dropped:", [p.get("label") or p.get("title") for p in ps if "lat" not in p])
    return out


def view(ps, pad=0.35):
    """(lon left, mercator top, lon right, mercator bottom) around the places, 16:9, with room around them."""
    lons, ys = [p["lon"] for p in ps], [merc(p["lat"]) for p in ps]
    l, r, b, t = min(lons), max(lons), min(ys), max(ys)
    w, h = max(r - l, 4.0), max(t - b, 4.0 * 9 / 16)
    w, h = w * (1 + 2 * pad), h * (1 + 2 * pad)
    if w / h < 16 / 9:
        w = h * 16 / 9
    else:
        h = w * 9 / 16
    cx, cy = (l + r) / 2, (t + b) / 2
    return cx - w / 2, cy + h / 2, cx + w / 2, cy - h / 2


def base(ps, pad):
    """The map picture (OVER x the frame) and a lon/lat -> pixel function for it."""
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
    l0, t0, l1, b1 = view(ps, pad)
    cx, cy, w, h = (l0 + l1) / 2, (t0 + b1) / 2, (l1 - l0) * OVER, (t0 - b1) * OVER
    l0, t0, l1, b1 = cx - w / 2, cy + h / 2, cx + w / 2, cy - h / 2
    BW, BH = round(SIZE[0] * OVER), round(SIZE[1] * OVER)
    k = 2                                              # supersampled, then reduced: smooth coastlines
    px = lambda lon, lat: ((lon - l0) / (l1 - l0) * BW * k, (t0 - merc(lat)) / (t0 - b1) * BH * k)
    im = Image.new("RGB", (BW * k, BH * k), SEA)
    d = ImageDraw.Draw(im)
    step = 10 if l1 - l0 > 40 else 5
    for lon in range(int(l0 // step * step), int(l1) + step, step):
        d.line([px(lon, 84), px(lon, -84)], fill=GRID, width=2 * k)
    for lat in range(-80, 81, step):
        d.line([px(l0, lat), px(l1, lat)], fill=GRID, width=2 * k)
    for (bx0, by0, bx1, by1), rings in S.land_polys():
        for sh in (-360, 0, 360):
            if bx1 + sh < l0 or bx0 + sh > l1 or merc(by1) < b1 or merc(by0) > t0:
                continue
            d.polygon([px(x + sh, y) for x, y in rings[0]], fill=LAND)
            for hole in rings[1:]:
                d.polygon([px(x + sh, y) for x, y in hole], fill=SEA)
            d.line([px(x + sh, y) for x, y in rings[0]], fill=COAST, width=3 * k)
    im = im.resize((BW, BH), Image.LANCZOS)
    a = np.asarray(im, np.float32)                     # old paper: grain + darker edges
    rng = np.random.default_rng(5)
    a += rng.normal(0, 4, a.shape[:2])[..., None]
    yy, xx = np.mgrid[0:BH, 0:BW]
    r = np.hypot((xx - BW / 2) / (BW / 2), (yy - BH / 2) / (BH / 2))
    a *= np.clip(1 - 0.28 * np.clip(r - 0.6, 0, None), 0, 1)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.SMOOTH)
    return im, lambda lon, lat: ((lon - l0) / (l1 - l0) * BW, (t0 - merc(lat)) / (t0 - b1) * BH)


def frame(bm, xy, ps, routes, t, dur):
    """One frame at t s: the push-in crop of the base map, then the routes (drawn one after another) and places."""
    from PIL import Image, ImageDraw, ImageFont
    BW, BH = bm.size
    e = 0.5 - 0.5 * math.cos(math.pi * min(1.0, t / max(dur, 0.1)))
    z = 1 + (1 / OVER - 1) * e                         # the share of the base that is visible: all -> the view
    cw, ch = BW * z, BH * z
    x0, y0 = (BW - cw) / 2, (BH - ch) / 2
    img = bm.transform(SIZE, Image.Transform.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.Resampling.BILINEAR)
    k = 2
    ov = Image.new("RGBA", (SIZE[0] * k, SIZE[1] * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    to = lambda p: ((xy(p["lon"], p["lat"])[0] - x0) / cw * SIZE[0] * k, (xy(p["lon"], p["lat"])[1] - y0) / ch * SIZE[1] * k)
    per = 1.6                                          # seconds to draw one route
    for n, (i, j) in enumerate(routes):
        p = (t - 0.5 - n * (per + 0.3)) / per
        if p <= 0:
            continue
        (ax, ay), (bx, by) = to(ps[i]), to(ps[j])
        ln = max(1.0, math.hypot(bx - ax, by - ay))
        ux, uy = (bx - ax) / ln, (by - ay) / ln
        ax, ay = ax + ux * 18 * k, ay + uy * 18 * k        # from the edge of one dot to just before the next
        bx, by = bx - ux * 46 * k, by - uy * 46 * k
        p = min(1.0, p)
        ex, ey = ax + (bx - ax) * p, ay + (by - ay) * p
        d.line([(ax, ay), (ex, ey)], fill=RED + (255,), width=9 * k, joint="curve")
        if p > 0.05:
            d.polygon([(ex + ux * 26 * k, ey + uy * 26 * k), (ex - uy * 17 * k, ey + ux * 17 * k),
                       (ex + uy * 17 * k, ey - ux * 17 * k)], fill=RED + (255,))
    f = ImageFont.truetype(str(FONT), 54 * k)
    for n, p in enumerate(ps):
        a = max(0.0, min(1.0, (t - 0.15 * n) / 0.35))
        if not a:
            continue
        x, y = to(p)
        r = 11 * k
        d.ellipse((x - r, y - r, x + r, y + r), fill=RED + (int(255 * a),), outline=(255, 255, 255, int(255 * a)),
                  width=3 * k)
        right = x < SIZE[0] * k * 0.7
        d.text((x + (22 if right else -22) * k, y - 4 * k), p["label"], font=f, anchor="lm" if right else "rm",
               fill=INK + (int(255 * a),), stroke_width=4 * k, stroke_fill=(245, 238, 220, int(220 * a)))
    ov = ov.reduce(k)
    img.paste(ov, (0, 0), ov)
    return img


def render(m, dur, k, enc):
    """The map shot -> work/s{k:04d}.mp4 (same encoder settings as the other shots)."""
    spec = m["spec"]
    ps = places_of(spec)
    if not ps:
        raise SystemExit(f"map shot {k}: no place with coordinates")
    routes = [(i, j) for i, j in (spec.get("routes") or []) if i < len(ps) and j < len(ps)]
    bm, xy = base(ps, float(spec.get("pad", 0.35)))
    out = W / f"s{k:04d}.mp4"
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                           f"{SIZE[0]}x{SIZE[1]}", "-r", "30", "-i", "-", "-vf", "format=yuv420p", *enc, out.name],
                          stdin=subprocess.PIPE, cwd=W)
    n = max(1, round(dur * 30))
    for i in range(n):
        pr.stdin.write(frame(bm, xy, ps, routes, i / 30, dur).tobytes())
    pr.stdin.close()
    if pr.wait():
        raise RuntimeError(f"map shot {k} failed")
    return out


def still(m):
    """The map's last frame (for a chapter card)."""
    ps = places_of(m["spec"])
    bm, xy = base(ps, float(m["spec"].get("pad", 0.35)))
    routes = [(i, j) for i, j in (m["spec"].get("routes") or []) if i < len(ps) and j < len(ps)]
    return frame(bm, xy, ps, routes, 30.0, 30.0)
