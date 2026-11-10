"""SHORTS FROM THE LONG VIDEOS (Andrii, Nov 10: the long videos are rarely recommended on their own -> 1-2 Shorts
per long video from its strongest moments, cut off at a cliffhanger, then the frame blurred and 'FULL VIDEO ON THE
CHANNEL' across the screen).
- Story field `clips`: [{"from": [chapter, sentence], "to": [chapter, sentence], "title": "TOP WORDS", "key": [...],
  "name": "Short title"}] (chapters as in the story, sentences 1-based, both inside ONE chapter: no chapter card).
- Cut from the rendered work/final.mp4 at the sentence times of work/captions.srt (the final timeline), no new
  voice: the Short sounds exactly like the long video (voice, music, SFX).
- 1080x1920: the 16:9 picture zoomed whole in the middle, a blurred copy of it behind, the words on top (the topic's
  name on red), burned captions under the picture (Shorts are watched muted), then END_S of the last frame
  frozen, blurred and dark with 'FULL VIDEO / ON THE CHANNEL' and a low rumble.
  python clips.py story.json  -> work/clip_1.mp4, work/clip_2.mp4 (+ clips.json: titles for the upload)"""
import json, pathlib, re, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))  # shorts/jurgen/pastrak from ww2-bot
from shorts import W, plain

VW, VH, FG_H, ZOOM = 1080, 1920, 608, 1.0     # the whole 16:9 frame: zoomed, the PLACE · DATE labels and name plates were cut
END_S, TAIL_S = 3.2, 0.15
FONT = "Bebas Neue"


def srt_cues(path):
    out = []
    for block in re.split(r"\n\s*\n", pathlib.Path(path).read_text(encoding="utf-8").strip()):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        a, b = [sum(float(x) * m for x, m in zip(t.replace(",", ".").split(":"), (3600, 60, 1)))
                for t in lines[1].split(" --> ")]
        out.append((a, b, " ".join(lines[2:])))
    return out


def sentence_times(d, srt):
    """{(chapter, sentence 1-based): (start, end)} in the final video, from captions.srt (longform.write_srt splits a
    sentence of more than 16 words into two cues)."""
    cues, k, out = srt_cues(srt), 0, {}
    for ci, c in enumerate(d["chapters"]):
        for si, s in enumerate(c["sentences"], 1):
            n = 2 if len(plain(s).split()) > 16 else 1
            out[(ci, si)] = (cues[k][0], cues[k + n - 1][1])
            k += n
    if k != len(cues):
        raise SystemExit(f"captions.srt has {len(cues)} cues, the story makes {k}: not this story's video?")
    return out


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass(clip, sents, dur):
    """Top words (name on red), captions in chunks of up to 3 words, the end card text."""
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
            "MarginR, MarginV, Encoding\n"
            f"Style: Top,{FONT},132,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,7,0,8,60,60,330,1\n"
            f"Style: Cap,{FONT},124,&H00FFFFFF,&H0000E0FF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,7,0,2,70,70,460,1\n"
            f"Style: End,{FONT},170,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,9,0,5,60,60,0,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    red = r"{\3c&H1E14E1&\bord22}"                     # the name: white on a thick red edge = a red box
    key = set(clip.get("key") or [])
    top = " ".join((red + w + r"{\3c&H000000&\bord7}") if w.strip("?!.,\":") in key else w
                   for w in clip["title"].split())
    ev = [f"Dialogue: 1,{ass_time(0)},{ass_time(dur)},Top,,0,0,0,,{top}"]
    for a, b, s in sents:
        words = plain(s).split()
        chunks = [words[i:i + 3] for i in range(0, len(words), 3)]
        total = sum(len(" ".join(c)) + 2 for c in chunks)
        t = a
        for c in chunks:
            e = t + (b - a) * (len(" ".join(c)) + 2) / total
            ev.append(f"Dialogue: 0,{ass_time(t)},{ass_time(e)},Cap,,0,0,0,,{' '.join(c).upper()}")
            t = e
    end = dur - END_S
    ev.append(f"Dialogue: 2,{ass_time(end + 0.15)},{ass_time(dur)},End,,0,0,0,,"
              r"{\fad(200,0)}" + red + r"FULL VIDEO{\3c&H000000&\bord9}\NON THE CHANNEL")
    return head + "\n".join(ev) + "\n"


def render(d, clip, times, final, out, n):
    (c0, s0), (c1, s1) = clip["from"], clip["to"]
    if c0 != c1 or s1 < s0:
        raise SystemExit(f"clip {n}: from/to must be in one chapter, in order")
    a = times[(c0, s0)][0]
    b = times[(c1, s1)][1] + TAIL_S
    cut = b - a
    dur = cut + END_S
    sents = [(times[(c0, i)][0] - a, min(times[(c0, i)][1], b) - a, d["chapters"][c0]["sentences"][i - 1])
             for i in range(s0, s1 + 1)]
    sub = W / f"clip_{n}.ass"
    sub.write_text(ass(clip, sents, dur), encoding="utf-8")
    vf = (f"[0:v]fps=30,tpad=stop_mode=clone:stop_duration={END_S},split[a][b];"
          f"[a]scale=-2:{VH},crop={VW}:{VH},boxblur=28:2,eq=brightness=-0.22[bg];"
          f"[b]scale={round(VW * ZOOM / 2) * 2}:{round(VW * ZOOM * 9 / 16 / 2) * 2},crop={VW}:{FG_H}[fg];"
          f"[bg][fg]overlay=0:{(VH - FG_H) // 2}[v1];"
          f"[v1]boxblur=30:3:enable='gte(t,{cut:.3f})',eq=brightness=-0.35:enable='gte(t,{cut:.3f})',"
          f"subtitles={sub.as_posix()}:fontsdir=fonts[v];"
          f"[0:a]afade=t=out:st={cut - 0.25:.3f}:d=0.25,apad=pad_dur={END_S}[va];"
          f"[1:a]atrim=0:{END_S},asetpts=PTS-STARTPTS,volume=0.6,afade=t=in:d=0.2,"
          f"afade=t=out:st={END_S - 0.8}:d=0.8,adelay={int(cut * 1000)}:all=1[sx];"
          f"[va][sx]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aud]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-t", f"{cut:.3f}", "-i", str(final),
           "-i", "sfx/low_rumble.mp3", "-filter_complex", vf, "-map", "[v]", "-map", "[aud]", "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a",
           "160k", "-ar", "48000", str(out)]
    subprocess.run(cmd, check=True)
    return round(dur, 1)


def make(story, final=None, srt=None):
    d = json.loads(pathlib.Path(story).read_text(encoding="utf-8"))
    final, srt = pathlib.Path(final or W / "final.mp4"), pathlib.Path(srt or W / "captions.srt")
    times = sentence_times(d, srt)
    meta = []
    for n, clip in enumerate(d.get("clips") or [], 1):
        out = W / f"clip_{n}.mp4"
        dur = render(d, clip, times, final, out, n)
        meta.append({"file": out.name, "seconds": dur, "title": clip.get("name") or d["title"],
                     "long_title": d["title"]})
        print(f"{out.name}: {dur} s - {clip['title']}")
    (W / "clips.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


# ---- upload: the same day as the long video (Andrii, Nov 10) ---------------------------------------------------
OFFSETS_MIN = (30, 180)            # after the long video's release: 19:30 and 22:00 New York on a 19:00 release
LEAD_MIN = 20                      # publishAt must be in the future


def release_of(yt, long_id):
    """The long video's release (its publishAt while scheduled, else when it was published) as UTC datetime."""
    from datetime import datetime
    it = yt.videos().list(part="status,snippet", id=long_id).execute()["items"][0]
    t = it["status"].get("publishAt") or it["snippet"]["publishedAt"]
    return datetime.fromisoformat(t.replace("Z", "+00:00"))


def times_for(release, n):
    """publishAt (UTC ISO) of each Short: release + OFFSETS_MIN; a time already gone -> now + LEAD_MIN (+ the gap)."""
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    out, last = [], None
    for k in range(n):
        t = release + timedelta(minutes=OFFSETS_MIN[min(k, len(OFFSETS_MIN) - 1)])
        if t < now + timedelta(minutes=LEAD_MIN):
            t = now + timedelta(minutes=LEAD_MIN + (OFFSETS_MIN[min(k, 1)] - OFFSETS_MIN[0]))
        if last and t <= last:
            t = last + timedelta(minutes=60)
        out.append(t)
        last = t
    return [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in out]


def body_of(d, meta, clip, long_id, at):
    first = plain(d["chapters"][clip["from"][0]]["sentences"][clip["from"][1] - 1])
    desc = (f"{first}\n\nFull video: {plain(d['title'])}\nhttps://www.youtube.com/watch?v={long_id}\n\n"
            "Narration: synthetic voice. Archive film and photos: public domain / free licences.\n\n"
            "#shorts #ww2 #history")
    tags = [t for t in (d.get("tags") or []) if isinstance(t, str)][:12] + ["shorts", "ww2", "history"]
    return {"snippet": {"title": plain(meta["title"])[:100], "description": desc[:4900], "tags": tags,
                        "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": "private", "publishAt": at, "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": False}}


def upload_all(yt, d, long_id, stats, release=None):
    """Uploads work/clip_N.mp4 (from clips.json) as Shorts, scheduled after the long video's release; each one in
    stats as format 'short' with its long video's id. The 'related video' link to the long video is NOT in the API:
    set it by hand in Studio (Short -> Details -> Related video)."""
    from datetime import date
    from googleapiclient.http import MediaFileUpload
    meta = json.loads((W / "clips.json").read_text(encoding="utf-8"))
    release = release or release_of(yt, long_id)
    ats = times_for(release, len(meta))
    ids = []
    for m, clip, at in zip(meta, d.get("clips") or [], ats):
        body = body_of(d, m, clip, long_id, at)
        vid = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(
            str(W / m["file"]), chunksize=-1, resumable=True)).execute(num_retries=3)["id"]
        print(f"short uploaded: {vid} | release {at} UTC | {body['snippet']['title']}")
        stats["videos"].append({"id": vid, "date": date.today().isoformat(), "format": "short", "long": long_id,
                                "title": body["snippet"]["title"], "seconds": m["seconds"], "publish_at": at})
        ids.append(vid)
    return ids


if __name__ == "__main__":
    make(*sys.argv[1:])
