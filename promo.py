"""PROMO SHORTS = THE SHORTS DESIGN from Nov 15 on (CLAUDE.md, PROMO TEASERS; Andrii, Nov 15: the Shorts are ADS for the long video: <= 15 s, the point = 'the main thing is in
the long version'). Replaces the old 25-60 s cuts of clips.py.
A promo = a 16:9 piece (the long video's intro, or a 3-sentence teaser rendered by tools/intro_render.py) cut
from..to, vertical 1080x1920: the frame whole in the middle on its blurred copy, 2-4 top words with the topic's
NAME on red, burned captions (Shorts are watched muted), then END_S of an end card: the frame frozen, dark and
blurred, the LONG VIDEO'S OWN THUMBNAIL in the middle (the viewer knows it again in the feed / the related-video
link), the open question above it, 'FULL VIDEO · N MIN' on red + 'LINK BELOW' with an arrow under it.
YouTube's 'Related video' (the link under a Short) is NOT in the Data API: set it in Studio by hand.
Spec (docs/promo/*.json or story `promos`): [{"source": "work/intro/x.mp4", "from": s, "to": s, "top": "WORDS",
  "key": ["NAME"], "caps": [[t0, t1, "text"], ...] (source seconds) | "srt": "path", "end": "THE OPEN QUESTION",
  "part": "PART V · STALIN'S COPY", "minutes": 13, "cover": "work/promo/x_cover.png", "name": "the Short's title"}]
Run: python promo.py docs/promo/b29.json -> work/promo/<id>.mp4"""
import json, pathlib, re, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
from shorts import W, plain

VW, VH, FG_H = 1080, 1920, 608
END_S = 3.0
MAX_S = 15.0
FONT = "Bebas Neue"
STAMP = "&H1E1EBE&"                                  # the red of the long video's stamps (a touch lighter)
KEY, WHITE = r"{\c&H1E1EBE&}", r"{\c&HFFFFFF&}"


def t_(t):
    cs = int(round(max(0.0, t) * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def srt_caps(path, a, b):
    out = []
    for block in re.split(r"\n\s*\n", pathlib.Path(path).read_text(encoding="utf-8").strip()):
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            x, y = [sum(float(v) * m for v, m in zip(s.replace(",", ".").split(":"), (3600, 60, 1)))
                    for s in lines[1].split(" --> ")]
            if y > a and x < b:
                out.append([x, min(y, b), " ".join(lines[2:])])
    return out


def ass(p, cut, dur):
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
            "MarginR, MarginV, Encoding\n"
            # Andrii, Nov 15: the font of the long video's red DATE / PLACE stamps (Bebas, no edge, slightly
            # see-through), in WHITE; the key word in the stamps' red
            f"Style: Top,{FONT},150,&H10FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,2,0,1,0,4,8,50,50,280,1\n"
            f"Style: Cap,{FONT},116,&H00FFFFFF,&H0000E0FF,&H00000000,&H50000000,0,0,0,0,100,100,2,0,1,0,7,2,70,70,470,1\n"
            f"Style: End,{FONT},130,&H10FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,2,0,1,0,4,5,40,40,0,1\n"
            f"Style: Big,{FONT},380,&H001E1EBE,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,2,0,1,0,5,5,40,40,0,1\n"
            f"Style: Small,{FONT},64,&H00D8D8D8,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,4,0,1,0,3,5,40,40,0,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    key = set(p.get("key") or [])
    top = r"\N".join(" ".join(KEY + w + WHITE if w.strip("?!.,\":") in key else w for w in line.split())
                     for line in p["top"].split("|"))
    ev = [f"Dialogue: 1,{t_(0)},{t_(cut)},Top,,0,0,0,,{top}"]
    caps = p.get("caps") or (srt_caps(p["srt"], p["from"], p["to"]) if p.get("srt") else [])
    for x, y, s in caps:                               # chunks of up to 3 words, timed by their length
        x, y = max(0.0, x - p["from"]), min(cut, y - p["from"])
        words = plain(s).split()
        chunks = [words[i:i + 3] for i in range(0, len(words), 3)]
        total, t = sum(len(" ".join(c)) + 2 for c in chunks), x
        for c in chunks:
            e = t + (y - x) * (len(" ".join(c)) + 2) / total
            ev.append(f"Dialogue: 0,{t_(t)},{t_(e)},Cap,,0,0,0,,{' '.join(c).upper()}")
            t = e
    ev += end_card(p, cut + 0.1, dur)
    return head + "\n".join(ev) + "\n"


def end_card(p, e0, dur):
    """The last 3 s: the long video's thumbnail in the middle (y 650-1190) + ONE way to send the viewer to it
    (`cta`): question | redacted | number | timestamp (Andrii, Nov 15: intrigue, a cut at the interesting moment,
    or a question)."""
    c = p.get("cta") or {"kind": "question"}
    k = c.get("kind", "question")
    d = lambda layer, st, style, pos, txt, fad=200: \
        f"Dialogue: {layer},{t_(e0 + st)},{t_(dur)},{style},,0,0,0,,{{\\pos(540,{pos})\\fad({fad},0)}}{txt}"
    ev = []
    if k == "question":                                # the open question of the teaser over the thumbnail
        ev.append(d(2, 0, "End", 560, p["end"]))
    elif k == "redacted":                              # the answer shown but blacked out, like a classified file
        ev.append(d(2, 0, "End", 400, c["line"]))
        w = 46 * len(c["hidden"]) + 40
        ev.append(f"Dialogue: 3,{t_(e0 + 0.35)},{t_(dur)},End,,0,0,0,,{{\\an5\\pos(540,560)\\bord0\\shad0"
                  f"\\c&H2A2A2A&\\3c{STAMP}\\bord4\\fad(120,0)\\p1}}m 0 0 l {w} 0 {w} 120 0 120{{\\p0}}")
        ev.append(f"Dialogue: 4,{t_(e0 + 0.35)},{t_(dur)},Small,,0,0,0,,{{\\pos(540,560)\\frz-6\\c{STAMP}"
                  f"\\3c{STAMP}\\bord3\\shad0\\fad(120,0)}}CLASSIFIED")
    elif k == "number":                                # one number of the answer, without what it counts
        ev.append(d(2, 0, "Big", 380, c["big"]))
        ev.append(d(2, 0.3, "End", 590, c["line"]))
    elif k == "timestamp":                             # where in the long video the answer is
        ev.append(d(2, 0, "End", 440, p["end"]))
        ev.append(d(2, 0.3, "End", 580, f"THE ANSWER: {KEY}{c['at']}{WHITE}"))
    if p.get("part") and k != "timestamp":
        ev.append(d(2, 0.2, "Small", 1290, p["part"], 250))
    ev.append(d(2, 0.35, "End", 1430, f"FULL VIDEO · {KEY}{p.get('minutes', '')} MIN{WHITE}"))
    ev.append(d(2, 0.6, "Small", 1600, "LINK BELOW"))
    ev.append(f"Dialogue: 2,{t_(e0 + 0.6)},{t_(dur)},Small,,0,0,0,,{{\\an8\\bord0\\shad0\\c{STAMP}"
              r"\fad(200,0)\move(540,1650,540,1680,0,600)\p1}m 0 0 l 70 0 35 50{\p0}")
    return ev


def render(p, out):
    a, b = float(p["from"]), float(p["to"])
    cut = b - a
    dur = cut + END_S
    if dur > MAX_S + 0.05:
        raise SystemExit(f"promo {out.name}: {dur:.1f} s (Andrii: <= {MAX_S:.0f} s)")
    sub = out.with_suffix(".ass")
    sub.write_text(ass(p, cut, dur), encoding="utf-8")
    cw, ch = 960, 540
    vf = (f"[0:v]fps=30,tpad=stop_mode=clone:stop_duration={END_S},split[a][b];"
          f"[a]scale=-2:{VH},crop={VW}:{VH},boxblur=28:2,eq=brightness=-0.22[bg];"
          f"[b]scale={VW}:{FG_H}[fg];[bg][fg]overlay=0:{(VH - FG_H) // 2}[v1];"
          f"[v1]boxblur=30:3:enable='gte(t,{cut:.3f})',eq=brightness=-0.45:enable='gte(t,{cut:.3f})'[v2];"
          f"[2:v]scale={cw}:{ch},format=rgba,fade=t=in:st={cut + 0.05:.3f}:d=0.3:alpha=1[cv];"
          f"[v2][cv]overlay=(W-w)/2:{(VH - ch) // 2 - 20}:enable='gte(t,{cut:.3f})',"
          f"subtitles={sub.as_posix()}:fontsdir=fonts[v];"
          f"[0:a]afade=t=out:st={cut - 0.3:.3f}:d=0.3,apad=pad_dur={END_S}[va];"
          f"[1:a]atrim=0:{END_S},asetpts=PTS-STARTPTS,volume=0.6,afade=t=in:d=0.2,"
          f"afade=t=out:st={END_S - 0.8}:d=0.8,adelay={int(cut * 1000)}:all=1[sx];"
          f"[va][sx]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aud]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-t", f"{cut:.3f}", "-i", p["source"],
                    "-i", "sfx/low_rumble.mp3", "-loop", "1", "-t", f"{dur:.3f}", "-i", p["cover"],
                    "-filter_complex", vf, "-map", "[v]", "-map", "[aud]", "-t", f"{dur:.3f}", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-ar", "48000", str(out)], check=True)
    return round(dur, 1)


def make(spec):
    ps = json.loads(pathlib.Path(spec).read_text(encoding="utf-8"))
    ps = ps.get("promos", ps) if isinstance(ps, dict) else ps
    (W / "promo").mkdir(parents=True, exist_ok=True)
    for p in ps:
        out = W / "promo" / f"{p['id']}.mp4"
        print(f"{out}: {render(p, out)} s - {p.get('name', '')}")


if __name__ == "__main__":
    make(sys.argv[1])
