"""Test render of a JURGEN story in the sandbox, to LOOK at before committing it (nothing is uploaded).
  python3 jrender.py stories/x.json article.txt [film|photo]
The article text of the story's "topic" (from wikitext.py). film|photo = the v2.04 style (default film: the story's
"films" + film "shots" open the video). Uses: DRY_RUN=1, the offline Kokoro voice (the real run speaks with Edge
Ryan), the story's pictures fetched slowly through commons.wikimedia.org/w/thumb.php into /tmp/story_tools/photos
(the Commons API gives 429 here), films downloaded once into /tmp/story_tools/films (named by their key, as
pastrak.film_file names them). Output: work/final.mp4 + work/metadata.json (shot list), work/thumb_clean.png and a
contact sheet every 3 s: /tmp/story_tools/render_sheet.jpg. ~10-20 min here. work/ is git-ignored."""
import json, os, pathlib, subprocess, sys, time, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
T = pathlib.Path("/tmp/story_tools")
PHOTOS, FILMS = T / "photos", T / "films"
PHOTOS.mkdir(parents=True, exist_ok=True)
FILMS.mkdir(parents=True, exist_ok=True)
story, text = sys.argv[1], sys.argv[2]
style = sys.argv[3] if len(sys.argv) > 3 else "film"
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
d = json.load(open(story, encoding="utf-8"))

files = list(dict.fromkeys(str(p["file"]) for p in d.get("pictures") or [] if p.get("file")))
for f in files:                                       # slowly: thumb.php answers 429 to bursts
    out = PHOTOS / f.replace(" ", "_")
    if out.exists() and out.stat().st_size > 5000:
        continue
    for w in (1280, 960, 640):
        for k in range(4):
            code = subprocess.run(["curl", "-sSL", "-m", "60", "-A", "Classified1945ShortsBot/1.0 (story research)",
                                   "-o", str(out), "-w", "%{http_code}",
                                   f"https://commons.wikimedia.org/w/thumb.php?w={w}&f=" + urllib.parse.quote(f)],
                                  capture_output=True, text=True).stdout
            if code == "200" and out.stat().st_size > 5000:
                break
            time.sleep(6 * (k + 1))
        if out.exists() and out.stat().st_size > 5000:
            break
    print("photo", "ok " if out.exists() and out.stat().st_size > 5000 else "MISSING", f[:70])
    time.sleep(2)

os.environ.update(DRY_RUN="1", TTS="kokoro", J_STORY=story, J_STYLE=style, P_FILMS=str(FILMS), LEARN="0",
                  GEMINI_API_KEY="")
import shorts as S
import jurgen as J

article = open(text, encoding="utf-8").read()
S.wiki_text = lambda t: (t, article[:20000])
S.translate = lambda *a: {}


def local_pictures(entries, data):
    """jurgen.manual_pictures with the local thumb.php copies instead of the Commons API."""
    by_sent, faces, credits, first_ok, seen = {}, {}, [], set(), set()
    data["_credit_of"], data["_file_path"] = {}, {}
    for e in entries:
        if not e.get("file"):
            continue
        f = str(e["file"]).replace(" ", "_")
        p, i = PHOTOS / f, int(e["sentence"]) - 1
        ok = p.exists() and p.stat().st_size > 5000
        if i not in seen and ok:
            first_ok.add(i)
        seen.add(i)
        if not ok:
            continue
        c = "Wikimedia Commons: " + f
        data["_credit_of"][str(p)] = c
        data["_file_path"][f] = p
        credits.append(c)
        if e.get("name") and i not in faces:
            faces[i] = (p, c)
            data.setdefault("people", {})[i] = {"title": e["file"], "name": J.caps(e["name"])}
        else:
            by_sent.setdefault(i, []).append(p)
    return by_sent, faces, list(dict.fromkeys(credits)), first_ok


J.manual_pictures = local_pictures
import pastrak as P                                   # the films: downloaded once into /tmp/story_tools/films
P.FILMS = FILMS
J.main()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/final.mp4", "-vf",
                "fps=1/3,scale=180:320,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                "text='%{pts\\:hms}':x=3:y=3:fontsize=13:fontcolor=yellow:box=1:boxcolor=black,tile=12x5",
                "-frames:v", "1", str(T / "render_sheet.jpg")], check=True)
m = json.load(open("work/metadata.json", encoding="utf-8"))
for s in m["script"]["shot_list"]:
    print(f"{s['t']:5.1f} {s['dur']:4.1f} {s['kind']:5} {s['picture'][:60]:60} | {s['sentence'][:40]}")
print("style:", m["script"].get("j_style"), "| sheet:", T / "render_sheet.jpg", "| video: work/final.mp4",
      round(os.path.getsize("work/final.mp4") / 1e6), "MB")
