"""Contact sheet of Commons files (numbered) -> PNG, for picking pictures by eye."""
import sys, re, pathlib, subprocess, urllib.parse, html as H, concurrent.futures as cf
sys.path.insert(0, __file__.rsplit('/',1)[0]); import commons as C
from PIL import Image, ImageDraw, ImageFont
T = pathlib.Path("/tmp/story_tools/thumbs"); T.mkdir(parents=True, exist_ok=True)
def thumb(f):
    out = T / (re.sub(r"[^A-Za-z0-9]+", "_", f)[-120:] + ".jpg")
    if out.exists() and out.stat().st_size > 1000:
        try:
            Image.open(out).verify(); return out
        except Exception:
            out.unlink()
    url = "https://commons.wikimedia.org/w/thumb.php?w=330&f=" + urllib.parse.quote(f.replace(" ", "_"))
    for i in range(5):
        r = subprocess.run(["curl", "-sS", "-m", "30", "-A", C.UA, "-o", str(out), "-w", "%{http_code}", url], capture_output=True, text=True)
        import time
        if r.stdout == "200": time.sleep(1.5); break
        time.sleep(8 * (i + 1))
    try:
        im = Image.open(out); im.thumbnail((330, 330)); im.convert("RGB").save(out); return out
    except Exception:
        return None
def sheet(files, path, cols=6):
    with cf.ThreadPoolExecutor(1) as ex: ts = list(ex.map(thumb, files))
    rows = (len(files) + cols - 1) // cols
    s = Image.new("RGB", (cols * 340, rows * 360), (30, 30, 30)); d = ImageDraw.Draw(s)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    for k, (fn, t) in enumerate(zip(files, ts)):
        x, y = (k % cols) * 340, (k // cols) * 360
        if t: s.paste(Image.open(t), (x + 5, y + 25))
        d.text((x + 5, y), f"{k}", font=f, fill=(255, 220, 0))
        d.text((x + 40, y + 4), fn[:30], font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13), fill=(200, 200, 200))
    s.save(path)
if __name__ == "__main__":
    files = [l.strip().removeprefix("File:") for l in open(sys.argv[1]) if l.strip()]
    sheet(files, sys.argv[2])
    for k, f in enumerate(files): print(k, f)
