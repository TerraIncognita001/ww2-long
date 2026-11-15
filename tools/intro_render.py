"""Renders an intro candidate (docs/intro/*.json): the `pre` block (film with no narrator: date/place stamps, the
period recording's own voice with its source line), then chapter 0 (`intro`) read by the narrator, then the title
card. Output: work/intro/<name>.mp4. Uses longform's own shot renderers, ASS styles and mix.
New in candidate 2 (Nov 14, reference: HISTORY 'The Minutes that Changed World War II'):
- `stamp`: ["AUGUST 6", "1945"] = the date / place huge in dark red over the film (the 2nd line biggest);
- `audio`: {"src", "from", "to"} = a cut of a period recording (period_audio) played as a voice, the music ducks
  under it; `source` = its small caption at the bottom ('PRESIDENT TRUMAN · NEWSREEL, AUGUST 1945');
- photo `reveal`: [y_from, y_to] = a slow eased tilt over a tall portrait (the medals up to the face).
Run: python tools/intro_render.py docs/intro/cand2_b29.json"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import os
os.chdir(ROOT)
import longform as L
from longform import S, P, W, ff, probe_duration, ass_esc, SIZE, ENC, GRADE

OUT = W / "intro"


def period_cut(spec, src, k):
    """A cut of a Commons recording, levelled like the narrator (-16 LUFS), as mp3 in work/."""
    import requests
    p = W / ("period_" + src["file"].replace(" ", "_"))
    if not p.exists():
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + requests.utils.quote(src["file"])
        r = requests.get(url, headers=S.UA, timeout=120)
        r.raise_for_status()
        p.write_bytes(r.content)
    out = W / f"period{k:02d}.mp3"
    a, b = float(spec["from"]), float(spec["to"])
    ff("-ss", f"{a:.2f}", "-t", f"{b - a:.2f}", "-i", p.name, "-af",
       "highpass=f=120,lowpass=f=6000,loudnorm=I=-16:TP=-2:LRA=7,afade=t=in:d=0.05,afade=t=out:st="
       f"{max(0, b - a - 0.15):.2f}:d=0.15", "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", out.name)
    return out


def render_reveal(m, d, k):
    """A tall portrait fitted to the width, tilting eased from y_from to y_to (0-1 = the picture's height)."""
    from PIL import Image
    out = W / f"s{k:04d}.mp4"
    im = P.still(m["path"])
    wid = round(SIZE[0] * 1.12)
    im = im.resize((wid, round(im.height * wid / im.width)), Image.LANCZOS)
    fp = W / f"f{k:04d}.jpg"
    im.save(fp, quality=94)
    y0, y1 = (min(max(0, f * im.height - SIZE[1] / 2), im.height - SIZE[1]) for f in m["reveal"])
    ease = f"(1-cos(PI*min(t/{d:.3f},1)))/2"
    fc = (f"[0:v]crop={SIZE[0]}:{SIZE[1]}:{(wid - SIZE[0]) // 2}:'{y0:.0f}+({y1 - y0:.0f})*{ease}',"
          f"{GRADE},setsar=1,format=yuv420p,{L.WHIP}[v]")
    ff("-loop", "1", "-framerate", "30", "-i", fp.name, "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}",
       *ENC, out.name)
    return out


def extra_ass(shots):
    t = S.ass_time
    st = ("Style: Stamp,Bebas Neue,190,&H001A1AA8,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,0,0,0,1\n"
          "Style: Stamp2,Bebas Neue,560,&H001A1AA8,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,0,0,0,1\n"
          "Style: Source,Bebas Neue,48,&H00F0F0F0,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,5,0,1,0,2,2,0,0,0,1\n")
    ev = []
    for sh in shots:
        a, b = sh["start"], sh["start"] + sh["dur"]
        lines = sh.get("stamp") or []
        if lines:                                      # dark red, 'printed' on the film: quick in, slight grow
            grow = "\\t(0,{0},\\fscx104\\fscy104)".format(round(sh["dur"] * 1000))
            if len(lines) == 1:
                ev.append(f"Dialogue: 6,{t(a + 0.1)},{t(b)},Stamp2,,0,0,0,,{{\\pos(960,560)\\fs400\\alpha&H18&\\fad(120,0){grow}}}"
                          f"{ass_esc(lines[0])}")
            else:
                ev.append(f"Dialogue: 6,{t(a + 0.1)},{t(b)},Stamp,,0,0,0,,{{\\pos(960,250)\\alpha&H18&\\fad(120,0){grow}}}"
                          f"{ass_esc(lines[0])}")
                ev.append(f"Dialogue: 6,{t(a + 0.1)},{t(b)},Stamp2,,0,0,0,,{{\\pos(960,560)\\alpha&H18&\\fad(120,0){grow}}}"
                          f"{ass_esc(lines[1])}")
    runs = []                                          # one caption over shots in a row with the same source
    for sh in shots:
        if sh.get("source") and runs and runs[-1][2] == sh["source"] and abs(runs[-1][1] - sh["start"]) < 0.05:
            runs[-1][1] = sh["start"] + sh["dur"]
        elif sh.get("source"):
            runs.append([sh["start"], sh["start"] + sh["dur"], sh["source"]])
    for a, b, s in runs:
        ev.append(f"Dialogue: 6,{t(a + 0.4)},{t(b - 0.1)},Source,,0,0,0,,{{\\pos(960,1015)\\alpha&H10&\\fad(400,300)}}"
                  f"{ass_esc(s)}")
    return st, ev


def main(path):
    spec = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    d = json.loads(pathlib.Path(spec["story"]).read_text(encoding="utf-8"))
    d["title"] = d["title"].replace("{N}", "13")
    intro = spec["intro"]
    intro["shots"] = [{**s, "card": True} if s.get("reveal") else s for s in intro["shots"]]  # one tilt, never split
    d["chapters"] = [intro, {"title": "x", "mode": "action", "sentences": ["x"]}]   # chapter 1 only for the title card
    OUT.mkdir(parents=True, exist_ok=True)
    films = {k: {**f, "path": P.film_file(k, f)} for k, f in (d.get("films") or {}).items()}
    names = list(dict.fromkeys([s["file"] for s in intro["shots"] if s.get("file")] + [d["thumb"]["file"]]))
    got = {n: L.commons_photo(n) for n in names}
    L.say_minutes({"chapters": [intro]}, 13)          # the B-29 video is 13 min (the real run: longform.make_video)
    voice = L.narrate({**d, "chapters": [intro]})[0]
    # the pre block: no narrator
    shots, segs, t = [], [], 0.0
    for k, p in enumerate(spec.get("pre") or []):
        m = L.media(p, films, got)
        sh = {**m, "start": t, "dur": float(p["dur"]), "chapter": 0, "mode": "action", "stamp": p.get("stamp"),
              "source": p.get("source")}
        shots.append(sh)
        if p.get("audio"):
            a = p["audio"]
            cut = period_cut(a, spec["period_audio"][a["src"]], k)
            segs.append({"kind": "voice", "start": t + 0.15, "dur": probe_duration(cut), "chapter": 0, "voice": cut,
                         "sent": [t], "mode": "action", "period": True})
        t += float(p["dur"])
    pre = t + 0.3
    vseg = {"kind": "voice", "start": pre, "dur": voice[2] + L.GAP_S, "chapter": 0, "voice": voice[0],
            "sent": [pre + x for x in voice[3]], "mode": intro.get("mode", "action")}
    tseg = {"kind": "title", "start": pre + vseg["dur"], "dur": L.TITLE_S, "chapter": 1}
    total = round(tseg["start"] + tseg["dur"], 3)
    if shots:
        shots[-1]["dur"] += pre - t                    # the 0.3 s breath before the narrator
    planned = L.plan(d, [vseg, tseg], films, got)
    for sh in planned:
        if sh["kind"] == "title":
            sh["pic"] = P.still(got[d["thumb"]["file"]][0])
    shots += planned
    by_file = {str(s.get("file")): s for s in intro["shots"] if s.get("reveal")}
    for sh in shots:
        if sh["kind"] == "photo":
            src = next((s for f, s in by_file.items() if got.get(f) and got[f][0] == sh["path"]), None)
            if src:
                sh["reveal"] = src["reveal"]
    print(f"intro: {total:.1f} s (pre {pre:.1f} s, narrator {voice[2]:.1f} s) | {len(shots)} shots")
    for sh in shots:
        print(f"  {sh['start']:5.1f} +{sh['dur']:4.1f} {sh['kind']:5} "
              f"{pathlib.Path(str(sh.get('path', ''))).name[:50]} {sh.get('ss', '')} {sh.get('stamp') or sh.get('note') or ''}")

    def render(a):
        k, sh = a
        if sh["kind"] == "film":
            return L.render_film(sh, sh["dur"], k)
        if sh["kind"] == "photo" and sh.get("reveal"):
            return render_reveal(sh, sh["dur"], k)
        if sh["kind"] == "photo":
            return L.render_photo(sh, sh["dur"], k)
        return L.render_card(sh, sh["dur"], k, sh["pic"])
    parts = L.pmap(render, list(enumerate(shots)), workers=4)
    L.mix_audio(d, segs + [vseg, tseg], shots, total)
    (W / "shots.txt").write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    ass = L.build_ass(d, shots, [vseg, tseg])
    st, ev = extra_ass(shots)
    txt = ass.read_text(encoding="utf-8").replace("\n[Events]", st + "\n[Events]", 1)
    ass.write_text(txt.rstrip("\n") + "\n" + "\n".join(ev) + "\n", encoding="utf-8")
    name = pathlib.Path(path).stem + ".mp4"
    fonts = pathlib.Path("..") / L.FONTS
    ff("-f", "concat", "-safe", "0", "-i", "shots.txt", "-i", "mix.m4a", "-filter_complex",
       f"[0:v]ass={ass.name}:fontsdir={fonts.as_posix()},format=yuv420p[v]", "-map", "[v]", "-map", "1:a",
       "-t", f"{total:.3f}", "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt",
       "yuv420p", "-c:a", "copy", "-movflags", "+faststart", f"intro/{name}")
    print("saved:", OUT / name, f"| loudness {P.lufs(OUT / name):.1f} LUFS")


if __name__ == "__main__":
    main(sys.argv[1])
