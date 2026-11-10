"""PASTRAK format (Andrii, Oct 26): 60-100 s armour Shorts in the style of @pasttrack (PastTrack: median 55k views,
"How 17 German Panther Tanks Broke a Soviet Siege" 1.66M). Research: CLAUDE.md '## PASTRAK'.
Run: python pastrak.py (same secrets and env as jurgen.py); P_STORY=stories/pastrak/x.json renders that story.

What is different from the jurgen format:
- A hand-made story file (stories/pastrak/*.json), 14-22 sentences / 160-300 words: year + trap -> "the answer" ->
  one visible oddity -> "But" before a third -> the fight or fate with a number -> a quiet verdict -> the debate
  question, spoken ("...which was the better tank? Let me know in the comments."). Every fact from the article(s).
- MOVING archive film first: every shot is a hand-picked clip (a film of the story file: Internet Archive / Commons,
  from-to seconds) or a photo, 2-3.5 s each, showing exactly what the sentence says.
- The picture in a band in the upper part of the frame (film 1080x760, photos 1080x960) on a dark blurred copy of
  itself; the two-line karaoke captions under it (S.captions_two, the spoken first sentence from frame 0).
- Sound: the voice + sound effects on the pictures (tank tracks and engines, guns, explosions: sfx/, Mixkit free
  licence) over a low battle rumble; no music (Andrii: "just the voice and sound effects like tank tracks").
- The cover in the last seconds: the vehicle big, full frame, with the country flags and a yellow name plate; the
  Short ends on it and loops, and the same frame is the thumbnail.
"""
import json, math, pathlib, re, subprocess

import requests

import shorts as S
import jurgen as J
from shorts import W, env, plain, stage, ff, probe_duration, pmap

SIZE = (1080, 1920)
BAND = {"film": (300, 760), "photo": (220, 960)}      # y and height of the picture band (PastTrack: film ~1.4:1)
CAP_Y = (1250, 1320)                                   # the two caption lines, under the band
SHOT_MAX = float(env("P_SHOT_MAX", "3.6"))             # PastTrack cuts every 2-3 s (50 cuts in 100 s)
FIRST_MAX = 2.4                                        # the first shot
COVER_S = float(env("P_COVER", "2.4"))                 # the cover at the end (the Short loops from it)
RATE = env("P_RATE", "+10%")                           # PastTrack's narrator ~160-170 words a minute
PAUSE = 0.45                                           # pauses kept up to this (s): a brisk read
MAX_LEN = float(env("P_MAX", "110"))
WORDS_LO, WORDS_HI = 150, 300
SENTS_LO, SENTS_HI = 12, 24
NUM_WORDS, NUM_MAX = 33, 3                             # at most 3 numbers heard in ~12 s (33 words)
STORIES = pathlib.Path("stories/pastrak")
SFX = pathlib.Path("sfx")
BED, BED_LUFS, FX_LUFS = env("P_BED", "low_rumble"), -36.0, -27.0
SFX_DB = 20 * math.log10(float(env("P_SFX_VOL", "0.81")))   # v1.99 (Andrii, Oct 26): effects 15% quieter in the final
# video (0.81 here: the final loudnorm lifts quiet passages a little, measured -1.4 dB = x0.85 on the effects band)
GRADE = "eq=contrast=1.07:brightness=-0.01:saturation=1.05"
PUNCH = "eq=contrast=1.45:brightness=-0.10:gamma=0.80"  # a shot's "punch": hazy, washed-out film (smoke) darker
ENC = ["-r", "30", "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "17", "-pix_fmt", "yuv420p"]
FILMS = W / "films"
DATE_RE = re.compile(r"\b(1[89]\d\d)\b|\b(January|February|March|April|May|June|July|August|September|October|"
                     r"November|December)\b")
TURN_RE = re.compile(r"^(But|However|Yet|Then|Until|Instead|Still)\b", re.I)
UPLOADED = []


# ---- the story ----------------------------------------------------------------------------------------------
def sentences(d):
    return [plain(s) for s in (d.get("sentences") or []) if isinstance(s, str) and plain(s)]


def check(d, text, facts_hard=True):
    """(hard, soft) problems of a story file, like jurgen.check: hard ones block the video. The facts (numbers,
    names) are hard when checked against the FULL articles (tools/stories/pcheck.py, when the story is written);
    in the run they are only reported: the bot's article text stops at 20,000 characters."""
    ss, hard, soft = sentences(d), [], []
    facts = hard if facts_hard else soft
    words = len(" ".join(ss).split())
    if not SENTS_LO <= len(ss) <= SENTS_HI:
        hard.append(f"{len(ss)} sentences (want {SENTS_LO}-{SENTS_HI})")
    if not WORDS_LO <= words <= WORDS_HI:
        hard.append(f"{words} words (want {WORDS_LO}-{WORDS_HI})")
    body = " ".join(ss)
    if S.numbers_ok(body, text):
        facts.append(f"numbers not in the source: {S.numbers_ok(body, text)}")
    if S.names_ok(body, text):
        facts.append(f"names not in the source: {S.names_ok(body, text)}")
    if S.OVERCLAIM.search(body):
        facts.append(f"overclaim: {S.OVERCLAIM.search(body).group(0)}")
    have = {int(s["sentence"]) for s in d.get("shots") or [] if str(s.get("sentence", "")).isdigit()}
    missing = [i for i in range(1, len(ss)) if i not in have]          # the last one is the cover
    if missing:
        hard.append(f"sentences without a shot: {missing}")
    films = d.get("films") or {}
    bad = [s.get("film") for s in d.get("shots") or [] if s.get("film") and s["film"] not in films]
    if bad:
        hard.append(f"shots of unknown films: {bad}")
    if not (d.get("cover") or {}).get("file"):
        hard.append("no cover picture")
    if ss and not DATE_RE.search(ss[0]):
        soft.append("sentence 1 has no year or month (PastTrack: 'March 1944. ...')")
    if not any(TURN_RE.match(s) for s in ss[1:max(2, round(len(ss) * 0.45))]):
        soft.append("no 'But/However' turn before the middle")
    if ss and not ("?" in ss[-1] or "comment" in ss[-1].lower()):
        soft.append("the last sentence is not the debate question")
    long = [i + 1 for i, s in enumerate(ss) if len(s.split()) > 26]
    if long:
        soft.append(f"sentences over 26 words: {long}")
    # Andrii (Oct 27, Panther at Kursk): too many figures within 10-15 seconds are hard to listen to (two in one
    # sentence are fine). The standard: at most NUM_MAX numbers in any ~12 s of speech; say the rest in plain words
    # ("half", "most of them", "a small part") or spread them through the story.
    names = {f"{a} {b}" for x in ss for a, b in re.findall(r"(?<=\S\s)([A-Z][a-z]+)\s+(\d+)\b", plain(x))}
    spots, w0 = [], 0
    for i, x in enumerate(ss):
        spots += [(w0 + k, i + 1) for _, k in heard_numbers(x, names)]
        w0 += len(plain(x).split())
    for a, i in spots:
        near = [j for p, j in spots if a <= p < a + NUM_WORDS]
        if len(near) > NUM_MAX:
            soft.append(f"{len(near)} numbers within ~12 s (sentences {i}-{near[-1]}): say some in words or spread them")
            break
    return hard, soft


MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"


def heard_numbers(sentence, names=()):
    """The figures a listener has to take in, as (number, words before it): digit groups, without years (1943), days
    of a date (5 July) and the digits of names (T-34, M26, U-234, 'Eagle 7': a capitalized word + number seen
    inside a sentence, passed in `names`, also counts as a name at the start of one)."""
    t = plain(sentence)
    out = []
    for m in re.finditer(r"(?<![\w-])\d[\d,.]*\d|(?<![\w-])\d", t):
        n = m.group(0).replace(",", "")
        if re.fullmatch(r"1[89]\d\d", n):
            continue
        before = re.search(r"(\S\s+)?([A-Z][a-z]+)\s+$", t[:m.start()])
        if before and (before.group(1) or f"{before.group(2)} {n}" in names):   # 'Eagle 7', 'Tiger 131'
            continue
        if n.isdigit() and int(n) <= 31 and (re.match(rf"\s+{MONTH}\b", t[m.end():]) or
                                            re.search(rf"\b{MONTH}\s+$", t[:m.start()])):
            continue
        out.append((n, len(t[:m.start()].split())))
    return out


def finish(d):
    """The shape shorts.py's helpers expect: headline = sentence 1, lines = the rest; the title is the story's own
    (PastTrack's titles are not the first sentence)."""
    ss = sentences(d)
    raw = [s for s in d["sentences"] if isinstance(s, str) and plain(s)]
    return {**d, "headline": raw[0], "lines": raw[1:], "hook_text": raw[0], "title": J.short_title(plain(d["title"])),
            "labels": {}, "scenes": {}, "people": {}, "map": None, "_n": len(ss)}


def ready_story():
    """The next hand-made story (lowest priority) not on the channel yet."""
    if not STORIES.exists():
        return None
    titles = [t.lower() for t in S.CHANNEL_TITLES + [v.get("title", "") for v in S.load_stats()["videos"]]]
    for p in sorted(STORIES.glob("*.json"), key=lambda p: (json.loads(p.read_text(encoding="utf-8")).get("priority",
                                                                                                         99), p.name)):
        d = json.loads(p.read_text(encoding="utf-8"))
        name = plain(d.get("title", "")).lower()
        if d.get("topic") and d.get("sentences") and d.get("shots") and not S.is_used(d.get("key") or d["topic"]) \
                and not any(name and t.startswith(name) for t in titles):
            return str(p)
    return None


# ---- media ----------------------------------------------------------------------------------------------
def commons_photo(name, k):
    """A Commons file (chosen by hand: only the licence and author are read) -> (path, credit)."""
    name = str(name).replace(" ", "_")
    cached = pathlib.Path(env("P_PHOTOS", "")) / name if env("P_PHOTOS") else None
    if cached and cached.exists():                     # a local copy (tests)
        return cached.resolve(), f"{name.replace('_', ' ')} (Wikimedia Commons)"
    try:
        page = requests.get(S.COMMONS, headers=S.UA, timeout=60, params={
            "action": "query", "format": "json", "formatversion": 2, "titles": "File:" + name, "prop": "imageinfo",
            "iiprop": "url|size|extmetadata", "iiurlwidth": 1280}).json()["query"]["pages"][0]
        item = J.free_item(name, (page.get("imageinfo") or [{}])[0])
    except Exception as ex:
        print("picture not found:", name[:70], type(ex).__name__)
        item = None
    if not item:                                       # the API refuses (429 in the sandbox): the thumbnail service
        url = "https://commons.wikimedia.org/w/thumb.php?w=1280&f=" + requests.utils.quote(name)
        item = (url, f"{name.replace('_', ' ')} (Wikimedia Commons)")
    path = S.download(item[0], f"p{k:03d}{pathlib.Path(name).suffix.lower() or '.jpg'}")
    return (path, item[1]) if path else None


def film_file(key, f):
    """A film of the story, downloaded once (Internet Archive / Commons files are 20-300 MB)."""
    FILMS.mkdir(parents=True, exist_ok=True)
    path = FILMS / (re.sub(r"[^A-Za-z0-9]+", "_", key) + pathlib.Path(f["url"].split("?")[0]).suffix.lower())
    local = pathlib.Path(env("P_FILMS", "")) / path.name if env("P_FILMS") else None
    if local and local.exists():                       # a local copy (tests)
        return local.resolve()
    if path.exists() and path.stat().st_size > 1_000_000:
        return path.resolve()
    for attempt in range(3):
        try:
            with requests.get(f["url"], headers=S.UA, stream=True, timeout=(20, 120)) as r, \
                    open(path.with_suffix(".part"), "wb") as out:
                r.raise_for_status()
                for chunk in r.iter_content(1 << 20):
                    out.write(chunk)
            path.with_suffix(".part").replace(path)
            return path.resolve()
        except requests.RequestException as e:
            print("film download failed:", key, str(e)[:120])
    raise SystemExit(f"film {key} could not be downloaded")


def fetch_media(d):
    """Every shot's picture: films downloaded once, photos from Commons -> list of media dicts in story order."""
    films = {k: {**f, "path": film_file(k, f)} for k, f in (d.get("films") or {}).items()
             if any(s.get("film") == k for s in d.get("shots") or [])}
    photos = list(dict.fromkeys(str(s["file"]) for s in d.get("shots") or [] if s.get("file")))
    got = dict(zip(photos, pmap(lambda a: commons_photo(a[1], a[0]), list(enumerate(photos)), workers=3)))
    media, credits = [], []
    for s in d.get("shots") or []:
        i = int(s["sentence"]) - 1
        if s.get("film"):
            f = films[s["film"]]
            media.append({"i": i, "kind": "film", "path": f["path"], "ss": float(s["from"]), "to": float(s["to"]),
                          "crop": f.get("crop"), "x": float(s.get("x", 0.5)), "sfx": s.get("sfx"),
                          "punch": bool(s.get("punch"))})
            credits.append(f["credit"])
        elif got.get(str(s.get("file"))):
            p, c = got[str(s["file"])]
            media.append({"i": i, "kind": "photo", "path": p, "x": float(s.get("x", 0.5)), "y": float(s.get("y", 0.5)),
                          "trim": s.get("trim"), "sfx": s.get("sfx")})
            credits.append(c)
        else:
            print("shot dropped (picture missing):", s.get("file"))
    cv = d["cover"]
    c = commons_photo(cv["file"], 999)
    if not c:
        raise SystemExit("the cover picture could not be downloaded")
    credits.append(c[1])
    return media, {**cv, "path": c[0]}, list(dict.fromkeys(credits))


# ---- the voice ------------------------------------------------------------------------------------------
def narrate(spoken):
    """The narration at PastTrack's brisk pace (short pauses), under MAX_LEN."""
    path, base = W / "voice.mp3", S.TTS_RATE
    S.TTS_RATE = RATE
    try:
        words = J.calm_pauses(path, S.speak(spoken, path), keep=PAUSE)
    finally:
        S.TTS_RATE = base
    J.MAX_LEN = MAX_LEN
    return J.fit_length(path, words)


# ---- shots ----------------------------------------------------------------------------------------------
def plan(tl, total, media, cover):
    """Sentence by sentence: its pictures share the sentence's time (a sentence without one holds the last shot);
    the first shot is short; a photo held longer than ~4.5 s becomes two shots (the second a closer crop, like a
    second camera); the cover takes the last COVER_S + 1 s (from the last sentence's start if it has no picture)."""
    n = 1 + len(tl)
    starts = [0.0] + [l["start"] for l in tl]
    by = {}
    for m in media:
        by.setdefault(m["i"], []).append(m)
    cover_at = max(starts[-1], total - COVER_S - 1.0) if by.get(n - 1) else starts[-1]
    ends = starts[1:] + [cover_at]
    shots = []
    for i in range(n):
        a, b = starts[i], min(ends[i], cover_at)
        items = by.get(i) or []
        if b - a < 0.05:
            continue
        if not items:
            if shots:
                shots[-1]["dur"] += b - a
            continue
        if i == 0 and len(items) == 1 and b - a > FIRST_MAX + 1.0 and items[0]["kind"] == "film":
            items = items * 2                         # a long first sentence on one film: cut after FIRST_MAX
        cuts = [a + (b - a) * j / len(items) for j in range(len(items))] + [b]
        if i == 0 and len(items) > 1:
            cuts[1] = min(cuts[1], a + FIRST_MAX)
            rest = len(items) - 1
            cuts = cuts[:2] + [cuts[1] + (b - cuts[1]) * j / rest for j in range(1, rest)] + [b]
        for j, m in enumerate(items):
            sh = {**m, "start": cuts[j], "dur": cuts[j + 1] - cuts[j]}
            if j and items[j - 1] is m:               # the same film twice: continue where the first part ended
                sh["ss"] = m["ss"] + (cuts[j] - cuts[j - 1])
            if sh["kind"] == "photo" and sh["dur"] > SHOT_MAX * 1.25:
                half = sh["dur"] / 2
                shots += [{**sh, "dur": half}, {**sh, "start": sh["start"] + half, "dur": half, "zoom": 1.28}]
            else:
                shots.append(sh)
    shots.append({"i": n - 1, "kind": "cover", "path": cover["path"], "start": cover_at, "dur": total - cover_at,
                  "sfx": None})
    return shots


def band_film(m, d, k):
    """A film clip in the band on its own blurred copy; slowed (max 1.6x) or held if the shot outlasts it."""
    out = W / f"p{k:03d}.mp4"
    y, h = BAND["film"]
    avail = max(0.3, m["to"] - m["ss"])
    slow = min(1.6, d / avail) if d > avail else 1.0
    pre = (f"crop={m['crop']}," if m.get("crop") else "") + (f"setpts={slow:.3f}*PTS," if slow > 1.0 else "")
    hold = f",tpad=stop_mode=clone:stop_duration={d:.2f}" if d > avail * slow else ""
    whip = "," + S.WHIP_VF.rstrip(",") if k > 0 else ""
    fc = (f"[0:v]{pre}fps=30{hold},setsar=1,split[a][b];"
          f"[a]scale=216:384:force_original_aspect_ratio=increase,crop=216:384,boxblur=10:2,scale=1080:1920,"
          f"eq=brightness=-0.20:saturation=0.7[bg];"
          f"[b]scale=1080:{h}:force_original_aspect_ratio=increase,crop=1080:{h}:(iw-ow)*{m['x']:.2f}:(ih-oh)/2,"
          f"{PUNCH + ',' if m.get('punch') else ''}{GRADE}[fg];[bg][fg]overlay=0:{y},format=yuv420p{whip}[v]")
    ff("-ss", f"{m['ss']:.2f}", "-t", f"{avail + 0.2:.2f}", "-i", str(m["path"]), "-filter_complex", fc, "-map", "[v]",
       "-t", f"{d:.3f}", *ENC, out.name)
    return out


def still(path, trim=None):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if trim:                                           # [left, top, right, bottom] fractions cut away (archive
        w, h = im.size                                 # caption strips, borders)
        l, t, r, b = (float(x) for x in trim)
        im = im.crop((round(w * l), round(h * t), round(w * (1 - r)), round(h * (1 - b))))
    return im


def band_photo(m, d, k):
    """A photo in the band on its blurred copy: a slow push-in (pull-out on every other shot)."""
    from PIL import ImageFilter, ImageOps, ImageEnhance
    out = W / f"p{k:03d}.mp4"
    y, h = BAND["photo"]
    im = still(m["path"], m.get("trim"))
    bg = ImageOps.fit(im, (216, 384)).filter(ImageFilter.GaussianBlur(9)).resize(SIZE)
    bg = ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(0.7)).enhance(0.55)
    z0 = float(m.get("zoom", 1.0))                     # >1: a closer crop (the second shot of a long hold)
    fg = ImageOps.fit(im, (round(1080 / z0), round(h / z0)), centering=(m.get("x", 0.5), m.get("y", 0.5)))
    fg = fg.resize((1080, h))
    if min(im.size) < 700:                             # small archive photos: a little sharper when enlarged
        fg = fg.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    bp, fp = W / f"pb{k:03d}.jpg", W / f"pf{k:03d}.jpg"
    bg.save(bp, quality=90)
    fg.save(fp, quality=94)
    ease = f"(1-cos(PI*min(t/{d:.3f},1)))/2"
    z = f"(1.0+0.09*{ease})" if k % 2 == 0 else f"(1.09-0.09*{ease})"
    whip = "," + S.WHIP_VF.rstrip(",") if k > 0 else ""
    fc = (f"[1:v]scale=w='trunc(1080*{z}/2)*2':h=-2:eval=frame,crop=1080:{h},{GRADE}[fg];"
          f"[0:v][fg]overlay=0:{y},setsar=1,format=yuv420p{whip}[v]")
    ff("-loop", "1", "-framerate", "30", "-i", bp.name, "-loop", "1", "-framerate", "30", "-i", fp.name,
       "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}", *ENC, out.name)
    return out


# ---- the cover ------------------------------------------------------------------------------------------
YELLOW_PLATE, GREEN_PLATE = (255, 210, 31), (22, 163, 74)


def flag(code, w=120, h=80):
    """A small country flag drawn in code (no picture files): us, de (Balkenkreuz, like PastTrack), gb, su, it,
    fr, jp, pl, fi, ca, au."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), "white")
    dr = ImageDraw.Draw(im)
    c = code.lower()
    if c == "us":
        for s in range(13):
            dr.rectangle((0, s * h / 13, w, (s + 1) * h / 13), fill=(178, 34, 52) if s % 2 == 0 else "white")
        cw, ch = w * 0.42, h * 7 / 13
        dr.rectangle((0, 0, cw, ch), fill=(60, 59, 110))
        for r in range(5):
            for q in range(6 if r % 2 == 0 else 5):
                x = cw * (q + (0.5 if r % 2 == 0 else 1.0)) / 6.2
                yy = ch * (r + 0.6) / 5.4
                dr.ellipse((x - 2.2, yy - 2.2, x + 2.2, yy + 2.2), fill="white")
    elif c == "de":
        dr.rectangle((0, 0, w, h), fill=(200, 16, 46))
        cx, cy, a, t = w / 2, h / 2, h * 0.36, h * 0.12
        for (dx, dy) in ((1, 0), (0, 1)):              # white-edged black cross (Balkenkreuz)
            dr.rectangle((cx - a * dx - t * dy - 5, cy - a * dy - t * dx - 5, cx + a * dx + t * dy + 5,
                          cy + a * dy + t * dx + 5), fill="white")
        for (dx, dy) in ((1, 0), (0, 1)):
            dr.rectangle((cx - a * dx - t * dy, cy - a * dy - t * dx, cx + a * dx + t * dy, cy + a * dy + t * dx),
                         fill="black")
    elif c == "gb":
        dr.rectangle((0, 0, w, h), fill=(1, 33, 105))
        dr.line((0, 0, w, h), fill="white", width=14)
        dr.line((0, h, w, 0), fill="white", width=14)
        dr.line((0, 0, w, h), fill=(200, 16, 46), width=5)
        dr.line((0, h, w, 0), fill=(200, 16, 46), width=5)
        dr.rectangle((w / 2 - 12, 0, w / 2 + 12, h), fill="white")
        dr.rectangle((0, h / 2 - 12, w, h / 2 + 12), fill="white")
        dr.rectangle((w / 2 - 7, 0, w / 2 + 7, h), fill=(200, 16, 46))
        dr.rectangle((0, h / 2 - 7, w, h / 2 + 7), fill=(200, 16, 46))
    elif c == "su":
        dr.rectangle((0, 0, w, h), fill=(204, 0, 0))
        cx, cy, r = w * 0.2, h * 0.24, h * 0.1
        pts = [(cx + r * math.sin(math.pi * 2 * j / 10) * (1 if j % 2 == 0 else 0.45),
                cy - r * math.cos(math.pi * 2 * j / 10) * (1 if j % 2 == 0 else 0.45)) for j in range(10)]
        dr.polygon(pts, fill=(255, 215, 0))
    elif c in ("it", "fr"):
        cols = [(0, 146, 70), "white", (206, 43, 55)] if c == "it" else [(0, 35, 149), "white", (237, 41, 57)]
        for j, col in enumerate(cols):
            dr.rectangle((w * j / 3, 0, w * (j + 1) / 3, h), fill=col)
    elif c == "jp":
        dr.ellipse((w / 2 - h * 0.3, h / 2 - h * 0.3, w / 2 + h * 0.3, h / 2 + h * 0.3), fill=(188, 0, 45))
    elif c == "pl":
        dr.rectangle((0, h / 2, w, h), fill=(220, 20, 60))
    elif c == "fi":
        dr.rectangle((w * 0.28, 0, w * 0.42, h), fill=(0, 47, 108))
        dr.rectangle((0, h * 0.4, w, h * 0.6), fill=(0, 47, 108))
    elif c in ("ca", "au"):
        dr.rectangle((0, 0, w, h), fill=(200, 16, 46) if c == "ca" else (1, 33, 105))
    return im


def plate(label, flags, green=False):
    """PastTrack's name plate: flags + the name in bold black on a rounded yellow (or green) box."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(S.FONTS_DIR + "/DejaVuSans-Bold.ttf", 66)
    tw = int(font.getlength(label))
    fl = [flag(c) for c in flags[:2]]
    w = tw + 56 + sum(f.width + 18 for f in fl)
    im = Image.new("RGBA", (w + 8, 112), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = 0
    for f in fl:
        im.paste(f, (x, 16))
        dr.rectangle((x, 16, x + f.width - 1, 16 + f.height - 1), outline=(0, 0, 0), width=2)
        x += f.width + 18
    dr.rounded_rectangle((x, 6, x + tw + 56, 106), radius=22, fill=GREEN_PLATE if green else YELLOW_PLATE)
    dr.text((x + 28, 56), label, font=font, fill="white" if green else (12, 12, 12), anchor="lm")
    return im


def cover_frame(cover):
    """The cover: the picture upscaled, filling 9:16 (crop centred at cover x/y), the plate near the top.
    Saved as thumb_clean.png (the thumbnail) and used as the last shot."""
    from PIL import ImageOps
    src = cover["path"]
    try:
        src = S.upscale(src)                            # Real-ESRGAN x4 (v1.93: covers only upscaled)
    except Exception as e:
        print("cover upscale skipped:", type(e).__name__, str(e)[:100])
    im = still(src, cover.get("trim"))
    im = ImageOps.fit(im, SIZE, centering=(float(cover.get("x", 0.5)), float(cover.get("y", 0.4))))
    pl = plate(str(cover.get("label", "")).strip()[:28], cover.get("flags") or [], cover.get("green"))
    if pl.width > 1000:
        pl = pl.resize((1000, round(pl.height * 1000 / pl.width)))
    im.paste(pl, ((SIZE[0] - pl.width) // 2, 250), pl)
    p = W / "thumb_clean.png"
    im.save(p)
    return p


def cover_shot(p, d, k):
    out = W / f"p{k:03d}.mp4"
    ease = f"(1-cos(PI*min(t/{d:.3f},1)))/2"
    whip = "," + S.WHIP_VF.rstrip(",")
    ff("-loop", "1", "-framerate", "30", "-i", str(pathlib.Path(p).resolve()), "-vf",
       f"scale=w='trunc(1080*(1.0+0.05*{ease})/2)*2':h=-2:eval=frame,crop=1080:1920,setsar=1,format=yuv420p{whip}",
       "-t", f"{d:.3f}", *ENC, out.name)
    return out


def render(k, sh, cover_png):
    if sh["kind"] == "film":
        return band_film(sh, sh["dur"], k)
    if sh["kind"] == "photo":
        return band_photo(sh, sh["dur"], k)
    return cover_shot(cover_png, sh["dur"], k)


# ---- sound ----------------------------------------------------------------------------------------------
_LUFS = {}


def lufs(path):
    if path not in _LUFS:
        log = subprocess.run(["ffmpeg", "-i", str(path), "-af", "ebur128", "-f", "null", "-"], capture_output=True,
                             text=True).stderr
        m = re.findall(r"I:\s*(-?[\d.]+) LUFS", log)
        _LUFS[path] = float(m[-1]) if m else -20.0
    return _LUFS[path]


def mix_audio(total, shots):
    """Voice (compressed, at the front) + a low battle rumble under everything + each shot's sound effect from its
    start (loudness-matched, faded, ducked under the voice) -> mix.m4a at YouTube's -14 LUFS."""
    fmt = "aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo"
    args = ["-i", "voice.mp3"]
    fc = [f"[0:a]{fmt},highpass=f=80,lowpass=f=9500,acompressor=threshold=0.1:ratio=2.5:attack=10:release=200,"
          "asplit=2[vo][key]"]
    fx = []
    bed = SFX / f"{BED}.mp3"
    if bed.exists():
        args += ["-stream_loop", "-1", "-i", str(bed.resolve())]
        g = BED_LUFS - lufs(bed) + SFX_DB
        fc.append(f"[1:a]{fmt},atrim=0:{total:.3f},volume={g:.1f}dB,afade=t=in:d=0.8,"
                  f"afade=t=out:st={max(0.0, total - 1.5):.2f}:d=1.5[bed]")
        fx.append("[bed]")
    for sh in shots:
        f = SFX / f"{sh.get('sfx')}.mp3" if sh.get("sfx") else None
        if not f or not f.exists():
            continue
        n = sum(1 for a in args if a == "-i")          # this input's index
        d = sh["dur"] + 0.35
        args += ["-i", str(f.resolve())]
        g = FX_LUFS - lufs(f) + SFX_DB
        ms = int(sh["start"] * 1000)
        fc.append(f"[{n}:a]{fmt},atrim=0:{d:.3f},asetpts=N/SR/TB,volume={g:.1f}dB,afade=t=in:d=0.06,"
                  f"afade=t=out:st={max(0.0, d - 0.35):.2f}:d=0.35,adelay={ms}|{ms}[fx{n}]")
        fx.append(f"[fx{n}]")
    if fx:
        fc.append(f"{''.join(fx)}amix=inputs={len(fx)}:duration=longest:normalize=0,apad,atrim=0:{total:.3f}[fxm]")
        fc.append("[fxm][key]sidechaincompress=threshold=0.04:ratio=2.5:attack=30:release=400[fxd]")
        fc.append(f"[vo][fxd]amix=inputs=2:duration=longest:normalize=0,"
                  f"loudnorm=I={S.LOUDNESS}:TP=-1.5:LRA=11,aresample=44100[a]")
    else:
        fc.append(f"[key]anullsink;[vo]loudnorm=I={S.LOUDNESS}:TP=-1.5:LRA=11,aresample=44100[a]")
    ff(*args, "-filter_complex", ";".join(fc), "-map", "[a]", "-t", f"{total:.3f}",
       "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "mix.m4a")


# ---- captions -------------------------------------------------------------------------------------------
def build_ass(tl, total):
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            "MarginL, MarginR, MarginV, Encoding\n" + S.caption_style() + "\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    ev = S.captions_two(tl, total, S.HEAD_TL, first=0.0, y1=CAP_Y[0], y2=CAP_Y[1])
    path = W / "pastrak.ass"
    path.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
    return path


# ---- the video ------------------------------------------------------------------------------------------
def make_video(data):
    from concurrent.futures import ThreadPoolExecutor
    spoken = S.respell(" ".join([plain(data["headline"])] + [plain(l) for l in data["lines"]]),
                       data.get("pronounce") if isinstance(data.get("pronounce"), dict) else None)
    print("voice text:", spoken[:400])
    with stage("voice + pictures"), ThreadPoolExecutor(max_workers=2) as ex:
        voice = ex.submit(narrate, spoken)
        media, cover, credits = fetch_media(data)
        words, total = voice.result()
    total = round(total + COVER_S, 3)                  # the cover holds after the last word, then the loop
    tl = S.timeline(data, words, total)
    data["sent_t"] = [0.0] + [round(l["start"], 1) for l in tl]
    S.write_srt(data, tl, total)
    shots = plan(tl, total, media, cover)
    kinds = {k: sum(s["kind"] == k for s in shots) for k in ("film", "photo", "cover")}
    print("length:", round(total, 1), "s | shots:", len(shots), kinds, "| average shot:",
          round(total / max(1, len(shots)), 1), "s")
    sents = [plain(data["headline"])] + [plain(l) for l in data["lines"]]
    data["shot_list"] = [{"t": round(s["start"], 1), "dur": round(s["dur"], 1), "kind": s["kind"],
                          "picture": (f"{pathlib.Path(str(s['path'])).name} {s['ss']:.1f}-{s['to']:.1f}"
                                      if s["kind"] == "film" else pathlib.Path(str(s["path"])).name),
                          "sfx": s.get("sfx"), "sentence": sents[s["i"]][:100]} for s in shots]
    cover_png = cover_frame(cover)
    with ThreadPoolExecutor(max_workers=1) as ex:
        audio = ex.submit(mix_audio, total, shots)
        with stage("shots"):
            parts = pmap(lambda a: render(a[0], a[1], cover_png), list(enumerate(shots)), workers=3)
        audio.result()
    (W / "shots.txt").write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    ass = build_ass(tl, total)
    with stage("final render"):
        ff("-f", "concat", "-safe", "0", "-i", "shots.txt", "-i", "mix.m4a", "-filter_complex",
           f"[0:v]ass={ass.resolve()}:fontsdir={S.FONTS_DIR},format=yuv420p[v]", "-map", "[v]", "-map", "1:a",
           "-t", f"{total:.3f}", "-r", "30", "-c:v", "libx264", "-preset", "superfast", "-crf", "22",
           "-maxrate", "6M", "-bufsize", "12M",       # grainy film is heavy: under GitHub's 100 MB (preview branch)
           "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "final.mp4")
    data["seconds"] = round(total, 1)
    credits.append("Sound effects: Mixkit (free licence)")
    return credits


def metadata(data, topic, credits, translations):
    body = J.metadata(data, topic, credits, translations)
    body["snippet"]["description"] = body["snippet"]["description"].replace(
        "Images and film via Wikimedia Commons / Wikipedia:", "Archive film and photos (public domain / free "
        "licences; film via Internet Archive):")
    return body


def main():
    from datetime import date
    stats = S.load_stats()
    S.FILE_NO = max(len(S.used), len(stats["videos"])) + 1
    try:
        creds = S.credentials()
    except (KeyError, ImportError):
        if not S.DRY_RUN:
            raise SystemExit("YouTube secrets are missing: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN")
        creds = None
    if creds:
        with stage("youtube read"):
            try:
                yt0 = S.youtube(creds)
                up = yt0.channels().list(part="contentDetails", mine=True).execute()["items"][0]
                pl = up["contentDetails"]["relatedPlaylists"]["uploads"]
                items = yt0.playlistItems().list(part="snippet", playlistId=pl, maxResults=50).execute().get("items", [])
                S.CHANNEL_TITLES[:] = [i["snippet"]["title"] for i in items]
                nums = [int(n) for i in items for n in re.findall(r"File #(\d+)", i["snippet"].get("description", ""))]
                S.FILE_NO = max([S.FILE_NO] + [n + 1 for n in nums])
            except Exception as e:
                print("recent uploads not read:", str(e)[:120])
    if env("J_PUBLISH") == "1":                        # publish the reviewed test video (preview branch -> work/)
        meta = json.loads((W / "metadata.json").read_text(encoding="utf-8"))
        if not (W / "final.mp4").exists() or not creds:
            raise SystemExit("publish: work/final.mp4 or YouTube secrets missing")
        S.set_category(meta.get("category") or "tanks")
        if meta.get("tts"):
            S.TTS_USED[:] = [meta["tts"]]
        if S.is_used(meta["topic"]):
            raise SystemExit(f"publish: {meta['topic']} is already on the channel")
        print("publishing the reviewed video:", meta["upload"]["snippet"]["title"])
        return publish(creds, stats, meta["upload"], meta["script"], meta["topic"])
    story = env("P_STORY") or ready_story()
    if not story:
        raise SystemExit("no ready pastrak story")
    print("pastrak story:", story)
    d = json.loads(pathlib.Path(story).read_text(encoding="utf-8"))
    S.set_category(d.get("category", "tanks"))
    got = S.wiki_text(d["topic"])
    if not got[0]:
        raise SystemExit(f"article not found: {d['topic']}")
    topic = S.topic_of([got])
    for extra in d.get("sources") or []:               # facts also from these articles (credited too)
        title, text = S.wiki_text(extra)
        if title:
            topic["text"] += "\n" + text
            topic["articles"].append(title)
    hard, soft = check(d, topic["text"], facts_hard=False)
    print("check: hard", hard, "| soft", soft)
    if hard:
        raise SystemExit(f"story check failed: {hard}")
    data = finish(d)
    data["story_topic"] = d["topic"]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=1) as ex:
        translations = ex.submit(S.translate, *S.texts(data))
        credits = make_video(data)
        body = metadata(data, topic, credits, translations.result())
    (W / "metadata.json").write_text(json.dumps({"upload": body, "topic": topic["key"], "category": S.CATEGORY,
                                                 "format": "pastrak", "tts": S.TTS_USED[0] if S.TTS_USED else None,
                                                 "script": {k: v for k, v in data.items() if not k.startswith("_")}},
                                                ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if S.DRY_RUN:
        print("DRY RUN: nothing uploaded. Video: work/final.mp4, title/description: work/metadata.json")
        return
    publish(creds, stats, body, data, topic["key"])


def publish(creds, stats, body, data, topic_key):
    from datetime import date
    yt = S.youtube(creds)
    with stage("upload"):
        vid = S.upload(yt, body)
    UPLOADED.append(vid)
    S.used.extend(dict.fromkeys([topic_key, data.get("story_topic") or topic_key]))
    S.USED.write_text(json.dumps(S.used, ensure_ascii=False, indent=1), encoding="utf-8")
    stats["videos"].append({"id": vid, "date": date.today().isoformat(), "category": S.CATEGORY, "hook": "pastrak",
                            "format": "pastrak", "length": "pastrak", "topic": topic_key, "title": plain(data["title"]),
                            "seconds": data.get("seconds"), "words": len(" ".join(sentences(data)).split()),
                            "headline": plain(data["headline"]), "sent_t": data.get("sent_t"),
                            "sent": [plain(x)[:70] for x in [data["headline"]] + list(data["lines"])],
                            "tts": S.TTS_USED[0] if S.TTS_USED else None})
    stats["recent"].append(plain(data["headline"]))
    S.save_stats(stats)
    with stage("playlist, comments"):
        if S.THUMB:
            clean = W / "thumb_clean.png"
            stats["videos"][-1]["thumb"] = S.set_thumbnail(yt, vid, clean.name if clean.exists() else "final.mp4")
        S.add_to_playlist(yt, vid)
        S.post_comment(yt, vid, data)
        S.upload_captions(yt, vid)
    S.save_stats(stats)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:                            # no good video possible: a classic Short in this slot
        if isinstance(e.code, str) and not UPLOADED and not S.DRY_RUN and env("J_PUBLISH") != "1":
            print("pastrak: no good video possible:", e.code)
            raise SystemExit(J.SKIP)
        raise
    except Exception:
        if UPLOADED or S.DRY_RUN or env("P_STORY") or env("J_PUBLISH") == "1":
            raise
        import traceback
        traceback.print_exc()
        print("pastrak failed before the upload -> classic Short")
        raise SystemExit(J.SKIP)
    finally:
        S.summary()
