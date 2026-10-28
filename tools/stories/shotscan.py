"""Every film range of a PASTRAK story at 2 frames a second on one sheet, to LOOK at before the test render:
no dead bodies (Andrii, Oct 27: a body lay in a trench clip), no scene change, title card or caption inside a range.
  python3 shotscan.py stories/pastrak/x.json        -> /tmp/story_tools/shotscan.jpg
Films are downloaded once into /tmp/story_tools/films (the same files prender.py uses)."""
import json, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
os.chdir(ROOT); sys.path.insert(0, str(ROOT))
FILMS = pathlib.Path("/tmp/story_tools/films"); FILMS.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("DRY_RUN", "1")
import pastrak as P
from PIL import Image, ImageDraw
d = json.load(open(sys.argv[1], encoding="utf-8"))
P.FILMS = FILMS
path = {k: P.film_file(k, f) for k, f in (d.get("films") or {}).items()}
rows = []
for s in d.get("shots") or []:
    if not s.get("film"):
        continue
    a, b = float(s["from"]), float(s["to"])
    out = FILMS / f"scan_{len(rows):02d}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a}", "-t", f"{b - a}", "-i", str(path[s["film"]]), "-vf",
                    "fps=2,scale=180:-2,tile=12x1", "-frames:v", "1", str(out)], check=True)
    im = Image.open(out).convert("RGB")
    ImageDraw.Draw(im).text((4, 4), f"s{s['sentence']} {s['film']} {a}-{b}", fill="yellow")
    rows.append(im)
W, H = max(r.width for r in rows), sum(r.height for r in rows)
sheet = Image.new("RGB", (W, H)); y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height
sheet.save("/tmp/story_tools/shotscan.jpg")
print("film ranges:", len(rows), "| sheet: /tmp/story_tools/shotscan.jpg")
