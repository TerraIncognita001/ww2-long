"""Renders only the intro of a story (or an intro candidate file, docs/intro/*.json) through longform's own code:
`pre` (film with no narrator: DATE / PLACE stamps, the period speech alone in the silence), chapter 0 read by the
narrator, its last line over the title card. Output: work/intro/<name>.mp4 (a preview before a full render).
Run: python tools/intro_render.py docs/intro/cand2_b29.json   (a candidate: {story, pre, period_audio, intro})
     python tools/intro_render.py stories/long/x.json          (a story's own intro)"""
import json, os, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["L_INTRO_ONLY"] = "1"
import longform as L


def main(path):
    spec = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    full = json.loads(pathlib.Path(spec.get("story", path)).read_text(encoding="utf-8"))
    d = json.loads(json.dumps(full))
    if "story" in spec:                                # a candidate file on top of a story
        for k in ("pre", "period_audio", "title_on_last"):
            if k in spec:
                d[k] = spec[k]
        d["chapters"] = [spec["intro"]]
    else:
        d["chapters"] = L.chapters(d)[:1]
    d["title"] = d["title"].replace("{N}", str(L.minutes_guess(full)))
    L.make_video(d)
    out = L.W / "intro" / (pathlib.Path(path).stem + ".mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(L.W / "final.mp4", out)
    for s in d["shot_list"]:
        print(f"  {s['t']:5.1f} +{s['dur']:4.1f} {s['kind']:5} {s['picture'][:60]}")
    print("saved:", out, f"| {L.probe_duration(out):.1f} s | loudness {L.P.lufs(out):.1f} LUFS")


if __name__ == "__main__":
    main(sys.argv[1])
