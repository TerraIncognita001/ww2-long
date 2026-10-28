"""Find the usable seconds of an archive film: picture area, scene cuts, numbered contact sheets you LOOK at.
  python3 filmsheet.py URL_or_file [every_s=2] [from_s=0] [to_s=end]
Downloads a URL once to /tmp/story_tools/films/. Prints the duration, the picture area for the story's film "crop"
(cropdetect: pillarbox/letterbox bars) and the scene cuts; writes /tmp/story_tools/films/<name>_sheetNN.jpg
(8 x 6 frames, every `every_s` seconds, time stamped). Tip: make sheets from the small 480p copy of an item, the
HD file has the same timeline (check both durations); then a finer sheet (every 1 s) of the parts you want.
Avoid title cards, captions burnt into the film, logos and watermarks; a shot needs >= 2 s of the same scene."""
import pathlib, re, subprocess, sys, urllib.request

D = pathlib.Path("/tmp/story_tools/films")
D.mkdir(parents=True, exist_ok=True)
src = sys.argv[1]
every = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
a = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
b = float(sys.argv[4]) if len(sys.argv) > 4 else None
if src.startswith("http"):
    path = D / re.sub(r"[^A-Za-z0-9.]+", "_", src.rsplit("/", 1)[-1])[-120:]
    if not path.exists() or path.stat().st_size < 100_000:
        print("downloading", src)
        req = urllib.request.Request(src, headers={"User-Agent": "Classified1945ShortsBot/1.0 (story research)"})
        with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as out:
            while chunk := r.read(1 << 20):
                out.write(chunk)
else:
    path = pathlib.Path(src)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True).stdout.strip() or 0)
size = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                       "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
b = min(b or dur, dur)
print(f"file: {path} | {dur:.1f} s | {size}")
crops = []
for t in [a + (b - a) * k / 6 for k in range(1, 6)]:
    log = subprocess.run(["ffmpeg", "-ss", f"{t:.1f}", "-i", str(path), "-t", "1", "-vf",
                          "cropdetect=limit=24:round=2:reset=0", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"crop=(\d+:\d+:\d+:\d+)", log)
    if m:
        crops.append(m[-1])
print("picture area (crop):", max(set(crops), key=crops.count) if crops else "?", "| samples:", crops)
log = subprocess.run(["ffmpeg", "-ss", f"{a:.1f}", "-to", f"{b:.1f}", "-i", str(path), "-vf",
                      "select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
cuts = [a + float(x) for x in re.findall(r"pts_time:([\d.]+)", log)]
print("scene cuts (s):", " ".join(f"{c:.1f}" for c in cuts))
stem = D / (path.stem[:60] + f"_{int(a)}")
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.2f}", "-to", f"{b:.2f}", "-i", str(path), "-vf",
                f"fps=1/{every},scale=240:-2,drawtext=fontfile={font}:text='%{{eif\\:t+{a:.0f}\\:d}}':x=3:y=3:"
                "fontsize=16:fontcolor=yellow:box=1:boxcolor=black,tile=8x6", f"{stem}_sheet%02d.jpg"], check=True)
print("sheets:", " ".join(str(p) for p in sorted(D.glob(stem.name + "_sheet*.jpg"))))
