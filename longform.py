"""LONG format (Andrii, Oct 27): 10-15 minute WW2 documentaries, 16:9, for the long-video channel. The strongest parts
of the two Shorts formats, chosen per chapter (story field `mode`):
- jurgen ("people" chapters): one person or fate, the narrator calm, photos held 4-8 s with a slow push-in, the
  person's portrait with the NAME in big letters when they enter, a dark drone under the voice.
- pastrak ("action" chapters): moving archive film, a cut every 2-4 s, every shot shows exactly the words, sound
  effects on the film over a low rumble, the music lower.
- both: a cold open on the most dramatic moment (film first), facts checked against the articles, at most 3 numbers
  in ~12 s of speech, no dead bodies, no watermarks / modern / museum pictures.
What is new for long videos: 16:9 1920x1080 pictures filling the frame (others on their own blurred copy), a title
card after the cold open, a card per chapter (= YouTube chapters in the description), lower-thirds for names and
PLACE · DATE, no burned-in captions (exact .srt uploaded instead), a 1280x720 thumbnail with 2-4 big words + flag,
an outro for the end screen.
Run: python longform.py (L_STORY=stories/long/x.json, DRY_RUN=1 = no upload);
     python longform.py check stories/long/x.json sources/a.txt [b.txt ...]  -> story check against the full articles.
"""
import json, math, pathlib, random, re, subprocess, sys

import requests

import shorts as S
import jurgen as J
import pastrak as P
from shorts import W, env, plain, stage, ff, probe_duration, pmap

SIZE = (1920, 1080)
S.VOICE = env("L_VOICE", "en-GB-RyanNeural")             # Andrii's narrator (jurgen): plain Ryan, natural pace
S.TTS_RATE = env("L_RATE", "+0%")
PAUSE = float(env("L_PAUSE", "0.75"))                   # pauses kept up to this (s): a documentary breathes
SHOT_MAX = {"action": float(env("L_SHOT_ACTION", "4.0")), "people": float(env("L_SHOT_PEOPLE", "7.5"))}
FIRST_MAX = 2.4                                         # the first shot of the video
TITLE_S, CARD_S, GAP_S, OUTRO_S = 4.5, 3.2, 0.5, float(env("L_OUTRO", "12"))   # outro = room for the end screen
WORDS_LO, WORDS_HI = 1400, 2600                         # ~140 words a minute: 10-18 min
NUM_WORDS, NUM_MAX = 33, 3                              # Andrii's standard: at most 3 numbers in ~12 s of speech
MUSIC_LUFS = {"people": -29.0, "action": -33.0}         # before the ducking under the voice
FX_LUFS = {"action": -27.0, "people": -31.0}
BED_LUFS = -38.0
GRADE = "eq=contrast=1.06:brightness=-0.01:saturation=1.0"
PUNCH = P.PUNCH
ENC = ["-r", "30", "-an", "-c:v", "libx264", "-preset", env("L_PRESET", "ultrafast"), "-crf", "18",
       "-pix_fmt", "yuv420p"]
WHIP = S.WHIP_VF.rstrip(",")
FONTS = pathlib.Path("fonts")
FONT = FONTS / "BebasNeue-Regular.ttf"                  # OFL, fonts/OFL.txt
STORIES = pathlib.Path("stories/long")
PHOTOS = W / "photos"
UPLOADED = []
ROMAN = "I II III IV V VI VII VIII IX X XI XII".split()


# ---- the story ----------------------------------------------------------------------------------------------
def chapters(d):
    return [c for c in d.get("chapters") or [] if c.get("sentences")]


def all_sentences(d):
    return [plain(s) for c in chapters(d) for s in c["sentences"]]


def check(d, text, facts_hard=True):
    """(hard, soft) problems; facts are hard against the FULL articles (the `check` command), reported in the run."""
    ss, hard, soft = all_sentences(d), [], []
    facts = hard if facts_hard else soft
    words = len(" ".join(ss).split())
    if not WORDS_LO <= words <= WORDS_HI:
        hard.append(f"{words} words (want {WORDS_LO}-{WORDS_HI})")
    body = " ".join(ss)
    if S.numbers_ok(body, text):
        facts.append(f"numbers not in the source: {S.numbers_ok(body, text)}")
    if S.names_ok(body, text):
        facts.append(f"names not in the source: {S.names_ok(body, text)}")
    if S.OVERCLAIM.search(body):
        facts.append(f"overclaim: {S.OVERCLAIM.search(body).group(0)}")
    films = d.get("films") or {}
    for k, c in enumerate(chapters(d)):
        have = {int(s["s"]) for s in c.get("shots") or [] if str(s.get("s", "")).isdigit()}
        if 1 not in have:
            hard.append(f"chapter {k}: sentence 1 has no shot")
        missing = [i for i in range(2, len(c["sentences"]) + 1) if i not in have]
        if missing:
            soft.append(f"chapter {k}: sentences without a shot (hold the last one): {missing}")
        bad = [s.get("film") for s in c.get("shots") or [] if s.get("film") and s["film"] not in films]
        if bad:
            hard.append(f"chapter {k}: shots of unknown films: {bad}")
        if c.get("mode") not in ("people", "action"):
            soft.append(f"chapter {k}: mode should be people or action")
        if k and not c.get("title"):
            hard.append(f"chapter {k}: no title (it is the chapter card and the YouTube chapter)")
    if not (d.get("thumb") or {}).get("file"):
        hard.append("no thumbnail picture")
    c = d.get("case") or {}                            # Andrii, Oct 28: every thumbnail is the house case file
    if not all((c.get(s) or {}).get("file") for s in ("left", "center", "right")):
        hard.append("no house thumbnail: story `case` needs left/center/right pictures (thumbs.py HOUSE)")
    if c and not c.get("stamp"):
        soft.append("case without a stamp word (one true word: GUILTY, SUNK, EXECUTED, MISSING...)")
    if len((c.get("label") or "")) > 32:
        soft.append("case label over 32 characters (it must fit the typed strip)")
    long = [i + 1 for i, s in enumerate(ss) if len(s.split()) > 30]
    if long:
        soft.append(f"sentences over 30 words: {long}")
    names = {f"{a} {b}" for x in ss for a, b in re.findall(r"(?<=\S\s)([A-Z][a-z]+)\s+(\d+)\b", plain(x))}
    spots, w0 = [], 0
    for i, x in enumerate(ss):
        spots += [(w0 + k, i + 1) for _, k in P.heard_numbers(x, names)]
        w0 += len(x.split())
    for a, i in spots:
        near = [j for p, j in spots if a <= p < a + NUM_WORDS]
        if len(near) > NUM_MAX:
            soft.append(f"{len(near)} numbers within ~12 s (sentences {i}-{near[-1]}): say some in words")
    return hard, soft


def ready_story():
    """The next hand-made story (lowest priority) not used yet."""
    for p in sorted(STORIES.glob("*.json"), key=lambda p: (json.loads(p.read_text(encoding="utf-8")).get("priority",
                                                                                                        99), p.name)):
        d = json.loads(p.read_text(encoding="utf-8"))
        if chapters(d) and not S.is_used(d.get("key") or d["title"]):
            return str(p)
    return None


# ---- media ----------------------------------------------------------------------------------------------
def commons_photo(name):
    """A hand-picked Commons file at up to 2400 px (16:9 at 1080p needs ~1900) -> (path, credit) or None."""
    name = str(name).replace(" ", "_")
    PHOTOS.mkdir(parents=True, exist_ok=True)
    out = PHOTOS / (re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:120] + ".jpg")
    meta = PHOTOS / (out.name + ".credit")
    if out.exists() and out.stat().st_size > 5000:
        return out.resolve(), meta.read_text(encoding="utf-8") if meta.exists() else name
    item = None
    try:
        page = requests.get(S.COMMONS, headers=S.UA, timeout=60, params={
            "action": "query", "format": "json", "formatversion": 2, "titles": "File:" + name, "prop": "imageinfo",
            "iiprop": "url|size|extmetadata", "iiurlwidth": 2400}).json()["query"]["pages"][0]
        ii = (page.get("imageinfo") or [{}])[0]
        item = J.free_item(name, ii)
        if item and ii.get("width", 0) <= 2400:          # small originals: the file itself, not an upscaled thumb
            item = (ii.get("url") if not name.lower().endswith((".tif", ".tiff", ".pdf")) else item[0], item[1])
    except Exception as ex:
        print("picture info failed:", name[:70], type(ex).__name__)
    if not item:
        item = ("https://commons.wikimedia.org/w/thumb.php?w=2400&f=" + requests.utils.quote(name),
                f"{name.replace('_', ' ')} (Wikimedia Commons)")
    for k in range(4):
        try:
            r = requests.get(item[0], headers=S.UA, timeout=90)
            if r.status_code == 429:
                import time
                time.sleep(8 * (k + 1))
                continue
            r.raise_for_status()
            from PIL import Image
            import io
            Image.open(io.BytesIO(r.content)).convert("RGB").save(out, quality=95)
            meta.write_text(item[1], encoding="utf-8")
            return out.resolve(), item[1]
        except Exception as ex:
            print("picture download failed:", name[:70], str(ex)[:100])
    return None


def fetch_media(d):
    films = {k: {**f, "path": P.film_file(k, f)} for k, f in (d.get("films") or {}).items()}
    thumbs = [f for v in thumb_specs(d) for f in thumb_files(v)]
    names = list(dict.fromkeys([str(s["file"]) for c in chapters(d) for s in c.get("shots") or [] if s.get("file")]
                               + [d["thumb"]["file"]] + thumbs))
    got = dict(zip(names, pmap(commons_photo, names, workers=3)))
    missing = [n for n in names if not got.get(n)]
    if missing:
        print("pictures missing:", missing)
    return films, got


# ---- the voice ------------------------------------------------------------------------------------------
def narrate(d):
    """One voice file per chapter (Edge's word timings stay exact on short texts), pauses calmed -> [(path, words,
    duration, sentence start times)]."""
    pron = d.get("pronounce") if isinstance(d.get("pronounce"), dict) else None

    def say(a):
        k, c = a
        path = W / f"voice{k:02d}.mp3"
        return path, S.speak(S.respell(" ".join(plain(s) for s in c["sentences"]), pron), path)

    def one(c, path, words):
        words = J.calm_pauses(path, words, keep=PAUSE)     # one at a time: it uses a fixed temp file
        dur = probe_duration(path)
        toks = [w for s in c["sentences"] for w in plain(s).split()]
        times = S.align(toks, words, dur)
        starts, i = [], 0
        for s in c["sentences"]:
            starts.append(times[i] if i < len(times) else dur)
            i += len(plain(s).split())
        starts[0] = 0.0
        return path, words, dur, starts
    said = pmap(say, list(enumerate(chapters(d))), workers=3)
    return [one(c, p, w) for c, (p, w) in zip(chapters(d), said)]


# ---- the timeline ---------------------------------------------------------------------------------------
def timeline(d, voices):
    """Segments in order: cold open (chapter 0) -> title card -> [chapter card -> chapter]... -> outro."""
    segs, t = [], 0.0
    for k, (c, v) in enumerate(zip(chapters(d), voices)):
        if k == 1:
            segs.append({"kind": "title", "start": t, "dur": TITLE_S, "chapter": 1})
            t += TITLE_S
        if k >= 1:
            segs.append({"kind": "card", "start": t, "dur": CARD_S, "chapter": k})
            t += CARD_S
        segs.append({"kind": "voice", "start": t, "dur": v[2] + GAP_S, "chapter": k, "voice": v[0],
                     "sent": [t + x for x in v[3]], "mode": c.get("mode", "people")})
        t += v[2] + GAP_S
    segs.append({"kind": "outro", "start": t, "dur": OUTRO_S, "chapter": len(voices) - 1})
    return segs, round(t + OUTRO_S, 3)


def plan(d, segs, films, got):
    """Shots: per sentence its pictures share its time; a photo held longer than ~1.25 x the chapter's SHOT_MAX
    becomes two shots (the second a closer crop); the first shot of the video is short; cards/outro are shots too."""
    shots, chs = [], chapters(d)
    for g in segs:
        if g["kind"] != "voice":
            shots.append({"kind": g["kind"], "start": g["start"], "dur": g["dur"], "chapter": g["chapter"]})
            continue
        c = chs[g["chapter"]]
        mode = g["mode"]
        by = {}
        for s in c.get("shots") or []:
            if s.get("file") in (d.get("trims") or {}) and not s.get("trim"):
                s = {**s, "trim": d["trims"][s["file"]]}   # per-file cut (watermarks, archive caption strips)
            if s.get("file") in (d.get("whole") or []):
                s = {**s, "whole": True}                   # portraits: always the whole picture, never a crop
            m = media(s, films, got)
            if m:
                by.setdefault(int(s["s"]) - 1, []).append(m)
        ends = g["sent"][1:] + [g["start"] + g["dur"]]
        for i, (a, b) in enumerate(zip(g["sent"], ends)):
            items = by.get(i) or []
            if not items:
                if shots and shots[-1]["kind"] in ("film", "photo"):
                    shots[-1]["dur"] += b - a
                elif by:
                    items = [next(iter(by.values()))[0]]
                if not items:
                    continue
            cuts = [a + (b - a) * j / len(items) for j in range(len(items))] + [b]
            if not shots and len(items) > 1:
                cuts[1] = min(cuts[1], a + FIRST_MAX)
                rest = len(items) - 1
                cuts = cuts[:2] + [cuts[1] + (b - cuts[1]) * j / rest for j in range(1, rest)] + [b]
            for j, m in enumerate(items):
                sh = {**m, "start": cuts[j], "dur": cuts[j + 1] - cuts[j], "chapter": g["chapter"], "mode": mode}
                if sh["kind"] == "photo" and sh["dur"] > SHOT_MAX[mode] * 1.25 and not sh.get("card"):
                    half = sh["dur"] / 2
                    z2 = round(float(m.get("zoom", 1.0)) * 1.22, 2)
                    shots += [{**sh, "dur": half, "name": m.get("name"), "label": m.get("label")},
                              {**sh, "start": sh["start"] + half, "dur": half, "zoom": z2, "name": None,
                               "label": None, "sfx": None}]
                else:
                    shots.append(sh)
    return shots


def media(s, films, got):
    if s.get("film"):
        f = films[s["film"]]
        return {"kind": "film", "path": f["path"], "ss": float(s["from"]), "to": float(s["to"]), "crop": f.get("crop"),
                "x": float(s.get("x", 0.5)), "y": float(s.get("y", 0.5)), "zoom": float(s.get("zoom", 1.0)),
                "sfx": s.get("sfx"), "punch": bool(s.get("punch")), "name": s.get("name"), "role": s.get("role"),
                "label": s.get("label"), "credit": f["credit"]}
    g = got.get(str(s.get("file")))
    if not g:
        return None
    return {"kind": "photo", "path": g[0], "credit": g[1], "x": float(s.get("x", 0.5)), "y": float(s.get("y", 0.5)),
            "zoom": float(s.get("zoom", 1.0)), "trim": s.get("trim"), "sfx": s.get("sfx"), "card": bool(s.get("card")),
            "whole": bool(s.get("whole")),
            "name": s.get("name"), "role": s.get("role"), "label": s.get("label")}


# ---- shots ----------------------------------------------------------------------------------------------
def render_film(m, d, k):
    """A clip filling 16:9 (crop = the picture area), slowed max 1.4x; a clip shorter than its shot also pushes in
    slowly over the whole shot, so its held last frame still moves; `zoom` = a closer look."""
    out = W / f"s{k:04d}.mp4"
    avail = max(0.3, m["to"] - m["ss"])
    slow = min(1.4, d / avail) if d > avail else 1.0
    held = d > avail * slow + 0.05
    hold = f",tpad=stop_mode=clone:stop_duration={d:.2f}" if held else ""
    z = float(m.get("zoom", 1.0))
    pre = (f"crop={m['crop']}," if m.get("crop") else "") + (f"setpts={slow:.3f}*PTS," if slow > 1.0 else "")
    w, h = round(SIZE[0] * z / 2) * 2, round(SIZE[1] * z / 2) * 2
    if held:                                           # eased push-in of up to 8% across the shot
        ease = f"(1-cos(PI*min(t/{d:.3f},1)))/2"
        size = (f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=bicubic,"
                f"scale=w='trunc({w}*(1+0.08*{ease})/2)*2':h=-2:eval=frame:flags=bicubic,")
    else:
        size = f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=bicubic,"
    fc = (f"[0:v]{pre}fps=30{hold},{size}"
          f"crop={SIZE[0]}:{SIZE[1]}:(iw-ow)*{m['x']:.2f}:(ih-oh)*{m['y']:.2f},"
          f"{PUNCH + ',' if m.get('punch') else ''}{GRADE},setsar=1,format=yuv420p{',' + WHIP if k else ''}[v]")
    ff("-ss", f"{m['ss']:.2f}", "-t", f"{avail + 0.3:.2f}", "-i", str(m["path"]), "-filter_complex", fc,
       "-map", "[v]", "-t", f"{d:.3f}", *ENC, out.name)
    return out


def blurred(im):
    from PIL import ImageEnhance, ImageFilter, ImageOps
    bg = ImageOps.fit(im, (384, 216)).filter(ImageFilter.GaussianBlur(8)).resize(SIZE)
    return ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(0.6)).enhance(0.45)


def photo_frames(m, k):
    """(background, foreground, fg position): wide pictures fill the frame; tall, square, very wide ones and
    documents ("card") sit whole on their own dark blurred copy (portraits with a name a little to the right)."""
    from PIL import Image, ImageFilter, ImageOps
    im = P.still(m["path"], m.get("trim"))
    w, h = im.size
    a = w / h
    z = float(m.get("zoom", 1.0))
    if not m.get("card") and not m.get("whole") and 1.3 <= a <= 2.3:
        fg = ImageOps.fit(im, (round(SIZE[0] / z * 1.0), round(SIZE[1] / z)), centering=(m["x"], m["y"]),
                          method=Image.LANCZOS).resize((round(SIZE[0] * 1.1), round(SIZE[1] * 1.1)), Image.LANCZOS)
        if w < 1400:
            fg = fg.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=2))
        return None, fg, None
    if z > 1.0:                                        # a closer look inside a portrait / document
        cw, ch = w / z, h / z
        cx, cy = m["x"] * (w - cw), m["y"] * (h - ch)
        im = im.crop((round(cx), round(cy), round(cx + cw), round(cy + ch)))
        w, h = im.size
    box_h = SIZE[1] * (0.92 if m.get("card") else 1.0)
    k_ = min(box_h / h, SIZE[0] * 0.9 / w)
    fg = im.resize((max(2, round(w * k_)), max(2, round(h * k_))), Image.LANCZOS)
    if w < 900:
        fg = fg.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    cx = 0.62 if m.get("name") and fg.width < SIZE[0] * 0.55 else 0.5
    pos = (round(SIZE[0] * cx - fg.width / 2), round((SIZE[1] - fg.height) / 2))
    return blurred(im), fg, pos


def render_photo(m, d, k):
    """A photo with a slow eased push-in (pull-out on every other shot): the jurgen look."""
    out = W / f"s{k:04d}.mp4"
    bg, fg, pos = photo_frames(m, k)
    fp = W / f"f{k:04d}.jpg"
    fg.save(fp, quality=94)
    ease = f"(1-cos(PI*min(t/{d:.3f},1)))/2"
    push = 0.07 if m.get("mode") == "people" else 0.10
    zexpr = f"(1.0+{push}*{ease})" if k % 2 == 0 else f"({1 + push}-{push}*{ease})"
    whip = "," + WHIP if k else ""
    if bg is None:                                     # fills the frame: fg is 110% of it, zoom inside that
        fc = (f"[0:v]scale=w='trunc({SIZE[0]}*{zexpr}/2)*2':h=-2:eval=frame:flags=bicubic,"
              f"crop={SIZE[0]}:{SIZE[1]},{GRADE},setsar=1,format=yuv420p{whip}[v]")
        ff("-loop", "1", "-framerate", "30", "-i", fp.name, "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}",
           *ENC, out.name)
        return out
    bp = W / f"b{k:04d}.jpg"
    bg.save(bp, quality=90)
    zs = f"(1.0+0.04*{ease})"
    fc = (f"[1:v]scale=w='trunc({fg.width}*{zs}/2)*2':h=-2:eval=frame:flags=bicubic,{GRADE}[fg];"
          f"[0:v][fg]overlay=x='{pos[0]}-(w-{fg.width})/2':y='{pos[1]}-(h-{fg.height})/2':eval=frame,"
          f"setsar=1,format=yuv420p{whip}[v]")
    ff("-loop", "1", "-framerate", "30", "-i", bp.name, "-loop", "1", "-framerate", "30", "-i", fp.name,
       "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}", *ENC, out.name)
    return out


def still_of(sh):
    """A PIL picture of a shot (a film's frame at its start) for the cards."""
    from PIL import Image
    if sh["kind"] == "photo":
        return P.still(sh["path"], sh.get("trim"))
    p = W / f"frame_{abs(hash((str(sh['path']), sh['ss']))) % 10 ** 8}.jpg"
    ff("-ss", f"{sh['ss'] + 0.5:.2f}", "-i", str(sh["path"]), "-frames:v", "1",
       *(["-vf", f"crop={sh['crop']}"] if sh.get("crop") else []), "-q:v", "2", p.name)
    return Image.open(p).convert("RGB")


def render_card(sh, d, k, pic):
    """Title / chapter card / outro: the picture dark and soft, slowly pushing in; the text comes from the ASS."""
    from PIL import ImageEnhance, ImageFilter, ImageOps
    out = W / f"s{k:04d}.mp4"
    im = ImageOps.fit(pic, (round(SIZE[0] * 1.08), round(SIZE[1] * 1.08)))
    if sh["kind"] == "card":
        im = im.filter(ImageFilter.GaussianBlur(6))
    im = ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(0.5)).enhance(0.42 if sh["kind"] == "card" else 0.55)
    fp = W / f"c{k:04d}.jpg"
    im.save(fp, quality=92)
    ease = f"(1-cos(PI*min(t/{d:.3f},1)))/2"
    fc = (f"[0:v]scale=w='trunc({SIZE[0]}*(1.0+0.05*{ease})/2)*2':h=-2:eval=frame,crop={SIZE[0]}:{SIZE[1]},"
          f"setsar=1,format=yuv420p,fade=t=in:st=0:d=0.5[v]")
    ff("-loop", "1", "-framerate", "30", "-i", fp.name, "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}",
       *ENC, out.name)
    return out


# ---- text on screen (ASS) -------------------------------------------------------------------------------
def ass_esc(t):
    return str(t).replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def build_ass(d, shots, segs):
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n"
            "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            "MarginL, MarginR, MarginV, Encoding\n"
            "Style: Name,Bebas Neue,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,0,3,1,0,0,0,1\n"
            "Style: Role,Bebas Neue,44,&H0070D7F5,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,3,0,1,0,2,1,0,0,0,1\n"
            "Style: Label,Bebas Neue,48,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,6,0,1,0,2,7,0,0,0,1\n"
            "Style: Part,Bebas Neue,60,&H0045B8E8,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,12,0,1,0,0,5,0,0,0,1\n"
            "Style: Card,Bebas Neue,150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,0,4,5,0,0,0,1\n"
            "Style: Sub,Bebas Neue,64,&H00E6E6E6,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,4,0,1,0,3,5,0,0,0,1\n"
            "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    t = S.ass_time
    ev, chs = [], chapters(d)
    for sh in shots:
        a, b = sh["start"], sh["start"] + sh["dur"]
        if sh.get("name"):
            a1, b1 = a + 0.35, min(b - 0.1, a + 5.5)
            ev.append(f"Dialogue: 3,{t(a1)},{t(b1)},Name,,0,0,0,,{{\\pos(110,930)\\fad(300,300)}}{ass_esc(sh['name'])}")
            ev.append(f"Dialogue: 3,{t(a1)},{t(b1)},Role,,0,0,0,,{{\\pos(114,990)\\fad(400,300)}}"
                      f"{ass_esc(sh.get('role') or '')}")
            ev.append(f"Dialogue: 2,{t(a1)},{t(b1)},Role,,0,0,0,,{{\\pos(110,840)\\fad(300,300)\\p1\\c&H0045B8E8&}}"
                      "m 0 0 l 90 0 90 6 0 6{\\p0}")
        if sh.get("label"):
            a1, b1 = a + 0.25, min(b - 0.1, a + 4.5)
            ev.append(f"Dialogue: 3,{t(a1)},{t(b1)},Label,,0,0,0,,{{\\pos(96,72)\\fad(250,300)}}{ass_esc(sh['label'])}")
    for g in segs:
        a, b = g["start"], g["start"] + g["dur"]
        if g["kind"] == "title":
            name, _, rest = plain(d["title"]).partition(":")
            ev.append(f"Dialogue: 4,{t(a + 0.3)},{t(b - 0.2)},Card,,0,0,0,,{{\\pos(960,500)\\fad(500,400)}}"
                      f"{ass_esc(name.upper())}")
            if rest.strip():
                ev.append(f"Dialogue: 4,{t(a + 0.8)},{t(b - 0.2)},Sub,,0,0,0,,{{\\pos(960,630)\\fad(500,400)}}"
                          f"{ass_esc(rest.strip().upper())}")
        elif g["kind"] == "card":
            k = g["chapter"]
            ev.append(f"Dialogue: 4,{t(a + 0.25)},{t(b - 0.15)},Part,,0,0,0,,{{\\pos(960,440)\\fad(400,300)}}"
                      f"PART {ROMAN[k - 1] if k <= len(ROMAN) else k}")
            ev.append(f"Dialogue: 4,{t(a + 0.45)},{t(b - 0.15)},Card,,0,0,0,,{{\\pos(960,560)\\fad(400,300)}}"
                      f"{ass_esc(chs[k]['title'].upper())}")
    path = W / "long.ass"
    path.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
    return path


# ---- sound ----------------------------------------------------------------------------------------------
def music_plan(d, segs):
    """A dark drone per chapter (music/jurgen), from the chapter card to the chapter's end."""
    tracks = sorted(pathlib.Path("music/jurgen").glob("*.mp3"))
    rnd = random.Random(d["title"])
    rnd.shuffle(tracks)
    out, by = [], {}
    for g in segs:
        by.setdefault(g["chapter"], []).append(g)
    for k, gs in sorted(by.items()):
        a, b = gs[0]["start"], gs[-1]["start"] + gs[-1]["dur"]
        mode = next((g["mode"] for g in gs if g["kind"] == "voice"), "people")
        if any(g["kind"] == "outro" for g in gs):
            mode = "people"
        out.append({"path": tracks[k % len(tracks)], "start": a, "end": b, "mode": mode})
    return out


def mix_audio(d, segs, shots, total):
    fmt = "aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo"
    args, fc, vo, mu, fx = [], [], [], [], []

    def inp(path, loop=False):
        args.extend((["-stream_loop", "-1"] if loop else []) + ["-i", str(pathlib.Path(path).resolve())])
        return sum(1 for x in args if x == "-i") - 1

    for g in segs:
        if g["kind"] == "voice":
            n = inp(g["voice"])
            ms = int(g["start"] * 1000)
            fc.append(f"[{n}:a]{fmt},adelay={ms}|{ms}[v{n}]")
            vo.append(f"[v{n}]")
    fc.append(f"{''.join(vo)}amix=inputs={len(vo)}:duration=longest:normalize=0,apad,atrim=0:{total:.3f},"
              "highpass=f=80,acompressor=threshold=0.1:ratio=2.5:attack=10:release=200,asplit=2[vo][key]")
    for m in music_plan(d, segs):
        n = inp(m["path"], loop=True)
        dur = m["end"] - m["start"] + 1.5
        g = MUSIC_LUFS[m["mode"]] - P.lufs(m["path"])
        ms = int(m["start"] * 1000)
        fc.append(f"[{n}:a]{fmt},atrim=0:{dur:.3f},asetpts=N/SR/TB,volume={g:.1f}dB,afade=t=in:d=2.5,"
                  f"afade=t=out:st={dur - 2.5:.2f}:d=2.5,adelay={ms}|{ms}[m{n}]")
        mu.append(f"[m{n}]")
    bed = pathlib.Path("sfx") / "low_rumble.mp3"
    for g in segs:
        if g["kind"] == "voice" and g["mode"] == "action" and bed.exists():
            n = inp(bed, loop=True)
            ms = int(g["start"] * 1000)
            fc.append(f"[{n}:a]{fmt},atrim=0:{g['dur']:.3f},asetpts=N/SR/TB,volume={BED_LUFS - P.lufs(bed):.1f}dB,"
                      f"afade=t=in:d=1.5,afade=t=out:st={max(0.0, g['dur'] - 1.5):.2f}:d=1.5,adelay={ms}|{ms}[e{n}]")
            fx.append(f"[e{n}]")
    for sh in shots:
        f = pathlib.Path("sfx") / f"{sh.get('sfx')}.mp3" if sh.get("sfx") else None
        if not f or not f.exists():
            continue
        n = inp(f)
        dd = min(sh["dur"] + 0.4, 9.0)
        g = FX_LUFS.get(sh.get("mode"), -29.0) - P.lufs(f) + P.SFX_DB
        ms = int(sh["start"] * 1000)
        fc.append(f"[{n}:a]{fmt},atrim=0:{dd:.3f},asetpts=N/SR/TB,volume={g:.1f}dB,afade=t=in:d=0.08,"
                  f"afade=t=out:st={max(0.0, dd - 0.4):.2f}:d=0.4,adelay={ms}|{ms}[x{n}]")
        fx.append(f"[x{n}]")
    back = mu + fx
    fc.append(f"{''.join(back)}amix=inputs={len(back)}:duration=longest:normalize=0,apad,atrim=0:{total:.3f}[bk]")
    fc.append("[bk][key]sidechaincompress=threshold=0.03:ratio=5:attack=25:release=1500[bkd]")
    fc.append(f"[vo][bkd]amix=inputs=2:duration=longest:normalize=0,afade=t=out:st={total - 3:.2f}:d=3,"
              f"loudnorm=I={S.LOUDNESS}:TP=-1.5:LRA=11,aresample=44100[a]")
    script = W / "mix.txt"
    script.write_text(";\n".join(fc), encoding="utf-8")
    ver = re.search(r"version n?(\d+)", subprocess.run(["ffmpeg", "-version"], capture_output=True,
                                                         text=True).stdout)
    opt = ["-/filter_complex", script.name] if ver and int(ver.group(1)) >= 7 else \
        ["-filter_complex_script", script.name]       # ffmpeg 7+ dropped -filter_complex_script (runner: 6.1)
    ff(*args, *opt, "-map", "[a]", "-t", f"{total:.3f}", "-c:a", "aac",
       "-b:a", "192k", "-ar", "44100", "-ac", "2", "mix.m4a")


# ---- thumbnail, captions, description -------------------------------------------------------------------
# Thumbnails (research Oct 28, top-12 long videos of 10 WW2 channels: Mark Felton 2.4M subs, Yarnhub 3.4M, Dark Docs
# 1.2M, The Operations Room, Simple History, History Hustle, Baz Battles...): the hits are COLOUR (colorized
# archive photos), ONE clear subject big (a face close up, or the machine in action), almost NO text (Felton,
# Dark Docs, Yarnhub: none; History Hustle: a 2-4 word tag in a box); Felton's split = person | person or object;
# Dark Docs = a red circle + arrow on the detail. Grey pictures under a big title are the weak ones (Baz Battles'
# grey 'INDIANAPOLIS' 90k vs its 2-10M). Story `thumbs` = up to 3 variants (YouTube Studio 'Test & compare' takes
# 3): cover.png (uploaded by the bot) and cover_2.png / cover_3.png for the test.
TW, TH = 1280, 720
RED = (230, 20, 30)


def thumb_panel(path, box, p):
    """One picture for a thumbnail panel: trimmed, colorized if black-and-white ("color", default on), upscaled,
    cropped to the box around x/y (zoom > 1 = closer), graded vivid."""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    src = pathlib.Path(path)
    if p.get("trim"):
        t = W / f"tt_{src.stem[:40]}_{abs(hash(tuple(p['trim']))) % 10 ** 6}.jpg"
        P.still(src, p["trim"]).save(t, quality=95)
        src = t
    if p.get("color", True) == "tone":                 # a hand-tinted-print grade instead of DDColor (small or
        src = S.warm_tone(src)                         # hard portraits: DDColor washes them out or gives up)
    elif p.get("color", True) and S.toned(src):
        done = S.colorize(src, portrait=bool(p.get("portrait")))
        src = S.warm_tone(src) if done == src else done
    src = S.upscale(src, most=int(p.get("most", 900)))
    im = P.still(src)
    z = float(p.get("zoom", 1.0))
    if z > 1.0:
        w, h = im.size
        cw, ch = w / z, h / z
        cx = min(max(0, p.get("x", 0.5) * w - cw / 2), w - cw)
        cy = min(max(0, p.get("y", 0.5) * h - ch / 2), h - ch)
        im = im.crop((round(cx), round(cy), round(cx + cw), round(cy + ch)))
    im = ImageOps.fit(im, box, centering=(float(p.get("x", 0.5)), float(p.get("y", 0.5))), method=Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(float(p.get("contrast", 1.15)))
    im = ImageEnhance.Color(im).enhance(float(p.get("saturation", 1.3)))
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))


def vignette(im, strength=0.45):
    from PIL import Image, ImageDraw, ImageFilter
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse((-TW * 0.15, -TH * 0.25, TW * 1.15, TH * 1.25), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(120))
    dark = Image.new("RGB", im.size, "black")
    return Image.composite(im, Image.blend(im, dark, strength), m)


def draw_arrow(dr, x1, y1, x2, y2, w=34):
    """A fat red arrow from (x1, y1) pointing at (x2, y2), with a black edge (Dark Docs)."""
    ang = math.atan2(y2 - y1, x2 - x1)
    L = math.hypot(x2 - x1, y2 - y1)
    head = min(110, L * 0.45)
    pts = [(0, -w / 2), (L - head, -w / 2), (L - head, -w * 1.5), (L, 0), (L - head, w * 1.5), (L - head, w / 2),
           (0, w / 2)]
    ca, sa = math.cos(ang), math.sin(ang)
    poly = [(x1 + px * ca - py * sa, y1 + px * sa + py * ca) for px, py in pts]
    dr.polygon(poly, fill=RED, outline="black", width=4)


def thumb_files(v):
    """Every picture a thumbnail spec uses (panels, case items, glow background/subject/shadow)."""
    parts = (v.get("panels") or []) + (v.get("items") or []) + [v[k] for k in ("bg", "subject", "shadow") if v.get(k)]
    return [p["file"] for p in parts + [v] if p.get("file")]


def thumb_variant(v, got, k):
    from PIL import Image, ImageDraw, ImageFont
    import thumbs
    out = W / ("cover.png" if k == 0 else f"cover_{k + 1}.png")
    if v.get("style") in thumbs.STYLES:                # the clickbait styles (thumbs.py)
        return thumbs.render(v, got, out)
    panels = v.get("panels") or [{"file": v["file"], **{a: v[a] for a in ("x", "y", "zoom", "trim") if a in v}}]
    widths = v.get("widths") or [1 / len(panels)] * len(panels)
    im, x = Image.new("RGB", (TW, TH)), 0
    for p, wf in zip(panels, widths):
        w = round(TW * wf) if p is not panels[-1] else TW - x
        im.paste(thumb_panel(got[p["file"]][0], (w, TH), p), (x, 0))
        x += w
    im = vignette(im, float(v.get("vignette", 0.4)))
    dr = ImageDraw.Draw(im)
    x = 0
    for wf in widths[:-1]:                             # Felton's split: a thin dark seam
        x += round(TW * wf)
        dr.rectangle((x - 3, 0, x + 3, TH), fill=(10, 10, 10))
    if v.get("circle"):                                # [cx, cy, rx, ry] in 0-1 of the frame
        cx, cy, rx, ry = v["circle"]
        box = (TW * (cx - rx), TH * (cy - ry), TW * (cx + rx), TH * (cy + ry))
        dr.ellipse(box, outline="black", width=16)
        dr.ellipse(box, outline=RED, width=10)
    if v.get("arrow"):                                 # [x1, y1, x2, y2] in 0-1
        a = v["arrow"]
        draw_arrow(dr, TW * a[0], TH * a[1], TW * a[2], TH * a[3])
    if v.get("tag"):                                   # History Hustle: 2-4 words on a red box
        size = int(v.get("tag_size", 96))
        font = ImageFont.truetype(str(FONT), size)
        text = str(v["tag"]).upper()
        tw = font.getlength(text)
        tx, ty = (TW * v.get("tag_x", 0.04), TH * v.get("tag_y", 0.08))
        if v.get("tag_right"):
            tx = TW - tw - 60 - TW * v.get("tag_x", 0.04)
        dr.rectangle((tx - 22, ty - 10, tx + tw + 22, ty + size + 4), fill=RED)
        dr.text((tx, ty - size * 0.06), text, font=font, fill="white")
    fx = 40
    for c in v.get("flags") or []:
        f = P.flag(c, 120, 80)
        fy = TH - 120 if v.get("flags_bottom", True) else 40
        im.paste(f, (fx, fy))
        dr.rectangle((fx, fy, fx + 119, fy + 79), outline="black", width=3)
        fx += 140
    im.save(out)
    return out


def thumb_specs(d, more=False):
    """The 3 thumbnails of the video (Test & compare takes 3): the house case file (story `case`) + up to 2 variants
    of it (`case.variants`); more=True adds `thumbs_more` (old candidates, review only)."""
    import thumbs
    if d.get("case"):
        c = {k: v for k, v in d["case"].items() if k != "variants"}
        main = [thumbs.house_case(c)] + [thumbs.house_case(c, v) for v in d["case"].get("variants") or []]
    else:
        main = d.get("thumbs") or [d["thumb"]]
    return main[:3] + ((d.get("thumbs_more") or []) if more else [])


def thumbnail(d, got, more=False):
    """cover.png (+ cover_2.png, cover_3.png for YouTube's Test & compare) from the story's `thumbs`."""
    paths = []
    for k, v in enumerate(thumb_specs(d, more)):
        try:
            paths.append(thumb_variant(v, got, k))
        except Exception as e:
            print(f"thumbnail {k + 1} failed:", type(e).__name__, str(e)[:120])
    return paths[0] if paths else None


def write_srt(d, segs, total):
    def ts(sec):
        ms = int(round(max(0.0, sec) * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    cues, chs = [], chapters(d)
    for g in segs:
        if g["kind"] != "voice":
            continue
        ss = [plain(s) for s in chs[g["chapter"]]["sentences"]]
        ends = g["sent"][1:] + [g["start"] + g["dur"] - GAP_S]
        for s, a, b in zip(ss, g["sent"], ends):
            words = s.split()                          # long sentences: two cues, split by the word share
            if len(words) > 16:
                h = len(words) // 2
                mid = a + (b - a) * h / len(words)
                cues += [(a, mid, " ".join(words[:h])), (mid, b, " ".join(words[h:]))]
            else:
                cues.append((a, b, s))
    out = [f"{i}\n{ts(a)} --> {ts(max(b, a + 0.5))}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1)]
    (W / "captions.srt").write_text("\n".join(out), encoding="utf-8")


def chapter_marks(d, segs):
    """YouTube chapters: 0:00 first, every chapter card after it (at least 10 s apart)."""
    def mmss(t):
        t = int(t)
        return f"{t // 3600}:{t // 60 % 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"
    chs = chapters(d)
    marks = [(0.0, "Intro")]
    for g in segs:
        if g["kind"] == "card" and g["start"] - marks[-1][0] >= 10:
            marks.append((g["start"], chs[g["chapter"]]["title"]))
    return [f"{mmss(a)} {name}" for a, name in marks]


def metadata(d, topic, credits, marks, translations):
    sources = ", ".join(f"https://en.wikipedia.org/wiki/{a.replace(' ', '_')}" for a in topic["articles"])
    desc = (f"{plain(d['summary'])}\n\n{plain(d.get('question', ''))} Tell me in the comments.\n\n"
            "Chapters:\n" + "\n".join(marks) + "\n\n"
            f"Sources: {sources}\n\nArchive film and photos (public domain / free licences):\n"
            + "\n".join(f"- {c}" for c in credits) +
            "\nMusic and sound effects: Mixkit (free licence). Narration: synthetic voice.\n\n"
            "#ww2 #history #documentary")
    loc = {l: {"title": v["title"][:100], "description": (v.get("summary") or "")[:4900]}
           for l, v in (translations or {}).items() if v.get("title")}
    body = {"snippet": {"title": plain(d["title"])[:100], "description": S.cut_bytes(desc),
                        "tags": S.tag_list(d, topic) if d.get("tags") else [], "categoryId": "27",
                        "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": env("L_PRIVACY", "public"), "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": False}}
    if loc:
        body["localizations"] = loc
    return body


# ---- the video ------------------------------------------------------------------------------------------
def make_video(d):
    from concurrent.futures import ThreadPoolExecutor
    with stage("voice + pictures"), ThreadPoolExecutor(max_workers=1) as ex:
        voices = ex.submit(narrate, d)
        films, got = fetch_media(d)
        voices = voices.result()
    segs, total = timeline(d, voices)
    shots = plan(d, segs, films, got)
    chs = chapters(d)
    for sh in shots:                                   # cards: the chapter's first picture; title/outro: the thumb
        if sh["kind"] in ("title", "outro"):
            sh["pic"] = P.still(got[d["thumb"]["file"]][0])
        elif sh["kind"] == "card":
            first = next((x for x in shots if x["kind"] in ("film", "photo") and x["chapter"] == sh["chapter"]), None)
            sh["pic"] = still_of(first) if first else P.still(got[d["thumb"]["file"]][0])
    kinds = {k: sum(s["kind"] == k for s in shots) for k in ("film", "photo", "card")}
    print(f"length: {total / 60:.1f} min | shots: {len(shots)} {kinds} | average shot "
          f"{total / max(1, len(shots)):.1f} s")
    d["shot_list"] = [{"t": round(s["start"], 1), "dur": round(s["dur"], 1), "kind": s["kind"],
                       "picture": (f"{pathlib.Path(str(s['path'])).name} {s['ss']:.1f}-{s['to']:.1f}"
                                   if s["kind"] == "film" else pathlib.Path(str(s.get("path", ""))).name)}
                      for s in shots]
    cover = thumbnail(d, got)
    write_srt(d, segs, total)

    def render(a):
        k, sh = a
        if sh["kind"] == "film":
            return render_film(sh, sh["dur"], k)
        if sh["kind"] == "photo":
            return render_photo(sh, sh["dur"], k)
        return render_card(sh, sh["dur"], k, sh["pic"])
    with ThreadPoolExecutor(max_workers=1) as ex:
        audio = ex.submit(mix_audio, d, segs, shots, total)
        with stage("shots"):
            parts = pmap(render, list(enumerate(shots)), workers=int(env("L_WORKERS", "4")))
        audio.result()
    (W / "shots.txt").write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    ass = build_ass(d, shots, segs)
    fonts = pathlib.Path("..") / FONTS                 # ff runs inside work/: relative paths, no Windows drive colon
    with stage("final render"):
        ff("-f", "concat", "-safe", "0", "-i", "shots.txt", "-i", "mix.m4a", "-filter_complex",
           f"[0:v]ass={ass.name}:fontsdir={fonts.as_posix()},format=yuv420p[v]", "-map", "[v]", "-map", "1:a",
           "-t", f"{total:.3f}", "-r", "30", "-c:v", "libx264", "-preset", env("L_FINAL_PRESET", "veryfast"),
           "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-pix_fmt", "yuv420p", "-c:a", "copy",
           "-movflags", "+faststart", "final.mp4")
    credits = list(dict.fromkeys([s["credit"] for s in shots if s.get("credit")]))
    d["seconds"] = round(total, 1)
    return credits, chapter_marks(d, segs), cover


def load_topic(d):
    got = S.wiki_text(d["topic"])
    if not got[0]:
        raise SystemExit(f"article not found: {d['topic']}")
    topic = S.topic_of([got])
    for extra in d.get("sources") or []:
        title, text = S.wiki_text(extra)
        if title:
            topic["text"] += "\n" + text
            topic["articles"].append(title)
    return topic


def main():
    stats = S.load_stats()
    S.set_category("events")
    if env("L_PUBLISH") == "1":                        # the reviewed dry run (its artifact unpacked into work/)
        meta = json.loads((W / "metadata.json").read_text(encoding="utf-8"))
        d = json.loads(pathlib.Path(meta["story"]).read_text(encoding="utf-8"))
        if not (W / "final.mp4").exists():
            raise SystemExit("publish: work/final.mp4 is missing")
        if S.is_used(d.get("key") or d["title"]):
            raise SystemExit(f"publish: {d['title']} is already on the channel")
        d["seconds"] = round(probe_duration(W / "final.mp4"), 1)
        print("publishing the reviewed video:", meta["upload"]["snippet"]["title"])
        return publish(stats, meta["upload"], {**d, "headline": all_sentences(d)[0]}, d)
    story = env("L_STORY") or ready_story()
    if not story:
        raise SystemExit("no ready long story")
    print("long story:", story)
    d = json.loads(pathlib.Path(story).read_text(encoding="utf-8"))
    topic = load_topic(d)
    hard, soft = check(d, topic["text"], facts_hard=False)
    print("check: hard", hard, "| soft", soft)
    if hard:
        raise SystemExit(f"story check failed: {hard}")
    data = {**d, "headline": all_sentences(d)[0], "lines": all_sentences(d)[1:]}
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=1) as ex:
        translations = ex.submit(S.translate, plain(d["title"]), plain(d.get("question", "")),
                                 plain(d.get("summary", "")), "")
        credits, marks, cover = make_video(d)
        body = metadata(d, topic, credits, marks, translations.result())
    (W / "metadata.json").write_text(json.dumps({"upload": body, "story": story, "chapters": marks,
                                                 "tts": S.TTS_USED[0] if S.TTS_USED else None,
                                                 "shot_list": d.get("shot_list")},
                                                ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("chapters:\n" + "\n".join(marks))
    if S.DRY_RUN:
        print("DRY RUN: nothing uploaded. Video: work/final.mp4, thumbnail: work/cover.png, work/metadata.json")
        return
    publish(stats, body, data, d)


def publish_at(local=None, zone="America/New_York", lead_min=20):
    """YouTube's scheduled release (Andrii, Oct 29: every video at 19:00 New York time): today's L_PUBLISH_NY in New
    York as UTC ISO; None when it is less than `lead_min` minutes away (then the video goes out as it is)."""
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    local = local if local is not None else env("L_PUBLISH_NY", "")
    if not local:
        return None
    tz = ZoneInfo(zone)
    hh, mm = (int(x) for x in local.split(":"))
    t = datetime.now(tz).replace(hour=hh, minute=mm, second=0, microsecond=0)
    if t < datetime.now(tz) + timedelta(minutes=lead_min):
        return None
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def publish(stats, body, data, d):
    from datetime import date
    at = publish_at()
    if at:                                             # uploaded now as private, YouTube releases it at `at`
        body["status"] = {**body["status"], "privacyStatus": "private", "publishAt": at}
        print("scheduled release:", at, "UTC (19:00 New York)" if env("L_PUBLISH_NY") == "19:00" else "UTC")
    else:
        body["status"]["privacyStatus"] = env("L_PRIVACY", body["status"].get("privacyStatus", "public"))
    creds = S.credentials()
    yt = S.youtube(creds)
    with stage("upload"):
        vid = S.upload(yt, body)
    UPLOADED.append(vid)
    S.used.append(d.get("key") or d["title"])
    S.USED.write_text(json.dumps(S.used, ensure_ascii=False, indent=1), encoding="utf-8")
    stats["videos"].append({"id": vid, "date": date.today().isoformat(), "format": "long", "title": plain(d["title"]),
                            "topic": d["topic"], "seconds": d.get("seconds"),
                            "words": len(" ".join(all_sentences(d)).split()),
                            "tts": S.TTS_USED[0] if S.TTS_USED else None})
    S.save_stats(stats)
    with stage("thumbnail, captions, comment"):
        stats["videos"][-1]["thumb"] = S.set_thumbnail(yt, vid, "cover.png")
        S.PLAYLIST = env("L_PLAYLIST", "WW2 Documentaries")
        S.add_to_playlist(yt, vid)
        S.upload_captions(yt, vid)
        S.post_comment(yt, vid, data)
    S.save_stats(stats)


def check_cli(story, texts):
    d = json.loads(pathlib.Path(story).read_text(encoding="utf-8"))
    text = "\n".join(pathlib.Path(t).read_text(encoding="utf-8") for t in texts)
    hard, soft = check(d, text, facts_hard=True)
    ss = all_sentences(d)
    print(f"{len(chapters(d))} chapters, {len(ss)} sentences, {len(' '.join(ss).split())} words "
          f"(~{len(' '.join(ss).split()) / 140:.1f} min at 140 wpm)")
    print("HARD:", *hard, sep="\n  ") if hard else print("HARD: none")
    print("SOFT:", *soft, sep="\n  ") if soft else print("SOFT: none")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "check":
        check_cli(sys.argv[2], sys.argv[3:])
    elif len(sys.argv) > 2 and sys.argv[1] == "thumbs":     # only the thumbnails (work/cover*.png)
        story = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
        if len(sys.argv) > 3:                          # a named list of candidates: work/<key>_1.png ...
            import thumbs
            specs = story[sys.argv[3]]
            got = {f: commons_photo(f) for f in dict.fromkeys(f for v in specs for f in thumb_files(v))}
            for k, v in enumerate(specs, 1):
                print(thumbs.render(v, got, W / f"{sys.argv[3]}_{k}.png").name, "-", v.get("note", ""))
            sys.exit()
        files = [f for v in thumb_specs(story, more=True) for f in thumb_files(v)]
        got = {f: commons_photo(f) for f in dict.fromkeys(files)}
        thumbnail(story, got, more=True)
        print("thumbnails:", sorted(x.name for x in W.glob("cover*.png")))
    else:
        try:
            main()
        finally:
            S.summary()
