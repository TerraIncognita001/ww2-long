"""Test render of a PASTRAK story in the sandbox, to LOOK at before committing it (nothing is uploaded).
  python3 prender.py stories/pastrak/x.json topic_article.txt [source_article.txt ...]
The article texts in the order of the story's "topic" then "sources" (from wikitext.py). Uses: DRY_RUN=1, the offline
Kokoro voice (Edge does not work here; the real run speaks with Azure Ryan, ~10% faster), the story's photos fetched
slowly through commons.wikimedia.org/w/thumb.php into /tmp/story_tools/photos (the Commons API gives 429 here),
films downloaded once into /tmp/story_tools/films. Output: work/final.mp4 + work/metadata.json (shot list) and a
contact sheet every 2 s: /tmp/story_tools/render_sheet.jpg. ~4 min. work/ is git-ignored."""
import json, os, pathlib, subprocess, sys, time, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
T = pathlib.Path("/tmp/story_tools")
PHOTOS, FILMS = T / "photos", T / "films"
PHOTOS.mkdir(parents=True, exist_ok=True)
FILMS.mkdir(parents=True, exist_ok=True)
story, texts = sys.argv[1], sys.argv[2:]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
d = json.load(open(story, encoding="utf-8"))

files = list(dict.fromkeys([s["file"] for s in d.get("shots", []) if s.get("file")] + [d["cover"]["file"]]))
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

os.environ.update(DRY_RUN="1", TTS="kokoro", P_STORY=story, P_PHOTOS=str(PHOTOS), P_FILMS=str(FILMS), LEARN="0",
                  GEMINI_API_KEY="")
import shorts as S
import pastrak as P

titles = [d["topic"]] + list(d.get("sources") or [])
text_of = {t: open(f, encoding="utf-8").read() for t, f in zip(titles, texts)}
S.wiki_text = lambda t: (t, text_of[t][:20000]) if t in text_of else (None, None)
S.translate = lambda *a: {}
for key, f in (d.get("films") or {}).items():         # download each film once (P.film_file names it)
    P.FILMS = FILMS
    P.film_file(key, f)
P.main()
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/final.mp4", "-vf",
                "fps=1/2,scale=180:320,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                "text='%{pts\\:hms}':x=3:y=3:fontsize=13:fontcolor=yellow:box=1:boxcolor=black,tile=12x5",
                "-frames:v", "1", str(T / "render_sheet.jpg")], check=True)
m = json.load(open("work/metadata.json", encoding="utf-8"))
for s in m["script"]["shot_list"]:
    print(f"{s['t']:5.1f} {s['dur']:4.1f} {s['kind']:5} {s['picture'][:48]:48} {str(s['sfx'] or ''):17} | {s['sentence'][:40]}")
print("sheet:", T / "render_sheet.jpg", "| video: work/final.mp4", round(os.path.getsize("work/final.mp4") / 1e6), "MB")
