"""SOUND EFFECTS FROM OPENVERSE (Andrii, Nov 17): real recordings (Freesound CC0 / public domain) for the war
sounds the Mixkit set lacks -> sfx/ov/<name>.mp3 (a shot's "sfx": "ov/<name>").
The candidates are LISTENED to by earshot (ears.rank: how well each fits the description; ears.describe) when it is
installed, else the first one is taken. Each pick is trimmed (silence off the start, <= 12 s), mono, faded out and
its credit kept in sfx/ov/openverse.json (CC0 needs none; kept anyway).
Run: python tools/sfx_fetch.py morse_code "morse code" "a telegraph key tapping morse code"
     python tools/sfx_fetch.py --all    (the starter list below)"""
import json, pathlib, subprocess, sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import openverse
import ears
import shorts as S

STARTER = [   # name, Openverse query, what it must sound like (earshot)
    ("morse_code", "telegraph morse", "a telegraph key tapping morse code"),
    ("machine_gun", "machine gun burst", "a burst of machine gun fire"),
    ("ship_horn", "ship horn", "a deep ship horn blowing"),
    ("crowd_cheer", "crowd cheering", "a large crowd cheering and applauding"),
    ("church_bells", "church bells", "church bells ringing"),
    ("prop_plane", "propeller airplane engine", "a propeller airplane engine droning"),
    ("ocean_waves", "waves beach", "sea waves breaking on a beach"),
    ("gunfire_distant", "distant gunfire", "distant gunfire and explosions of a battle"),
]


def fetch(name, query, desc, n=6):
    cands = openverse.sounds(query, n=n, most=40.0)
    if not cands:
        print(f"{name}: nothing for '{query}'")
        return None
    folder = ROOT / "work" / "sfx_cand" / name
    folder.mkdir(parents=True, exist_ok=True)
    files = []
    for k, c in enumerate(cands):
        p = folder / f"{k}{pathlib.Path(c['url'].split('?')[0]).suffix or '.mp3'}"
        try:
            if not p.exists():
                r = requests.get(c["url"], headers=S.UA if "wikimedia" in c["url"] else openverse.UA, timeout=90)
                r.raise_for_status()
                p.write_bytes(r.content)
            files.append((p, c))
        except Exception as e:
            print(f"  {c['title'][:50]}: download failed {type(e).__name__}")
    if not files:
        return None
    order = ears.rank(desc, [str(p) for p, _ in files]) if ears.ok() else None
    if order and order[0]["verdict"] in ("no match", "weak"):   # ears: none of them sounds like it (a stun gun zap
        print(f"{name}: none sounds like '{desc}' (best {order[0]['score']:+.2f}, {order[0]['like']})")  # for gunfire)
        return None
    best = next((f for f in files if str(f[0]) == order[0]["path"]), files[0]) if order else files[0]
    if order:
        for o in order[:4]:
            print(f"  {o['score']:+.2f} {pathlib.Path(o['path']).name} {o.get('verdict', '')}")
    out = ROOT / "sfx" / "ov" / f"{name}.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(best[0]), "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,atrim=0:12,afade=t=out:st=11:d=1",
                    "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "160k", str(out)], check=True)
    reg = ROOT / "sfx" / "ov" / "openverse.json"
    data = json.loads(reg.read_text(encoding="utf-8")) if reg.exists() else {}
    c = best[1]
    data[name] = {"title": c["title"], "credit": c["credit"], "id": c["id"], "url": c["url"], "query": query,
                  "desc": desc, "score": order[0]["score"] if order else None}
    reg.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{name}: {c['title'][:60]} -> {out.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    if sys.argv[1] == "--all":
        for a in STARTER:
            fetch(*a)
    else:
        fetch(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else sys.argv[2])
