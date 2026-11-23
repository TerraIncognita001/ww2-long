"""Retention test of the atomic bomb story (Andrii, Nov 23: 'погане утримання... зроби дослідження... відрендери').
Our curves: half the viewers leave in the first ~25 s (D-Day 50 % at 0:26, B-29 72 % at 0:23). Research (Rene
Ritchie / YouTube, George Blackman, Mario Joos, vidIQ): the first seconds must pay off the title IN WORDS, no summary
of every chapter, no repeating the title, short wordless parts, a fast ending. This builds docs/retention/atomic_r.json
(NOT in stories/long: the cron never takes it):
- the narrator speaks at ~3 s over the bomb film (was 15 s of stamps + silence);
- Truman's sentence right after the first line (a beat in the intro), then ONE open question paid off in 'Nagasaki';
- no 'This is the entire history of...' (the title card shows the title under the last line), title card min 2.5 s;
- chapter stamps 2.0 s (were 3.2 s), outro 6 s (was 12 s);
- silent film beats cut to ~6 s (papers keep one page, quotes and period recordings stay)."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
d = json.loads((ROOT / "stories/long/atomic.json").read_text(encoding="utf-8"))
src = "PRESIDENT TRUMAN · STATEMENT ON THE ATOMIC BOMB, AUGUST 1945"
d["pre"] = [{"dur": 2.8, "film": "naga", "from": 2, "to": 6, "stamp": ["AUGUST 6", "1945"], "sfx": "explosion_massive"}]
d["intro_beats"], d["voice"] = True, "andrii"          # title card 2.5 s, stamps 2 s, outro 6 s: the defaults since Nov 23
ch0 = d["chapters"][0]
ch0["sentences"] = [
    "At 8:15 in the morning, one bomb destroys the city of Hiroshima.",
    "Building it takes three years, secret cities and nearly 130,000 people.",
    "Its bomb laboratory is led by the physicist J. Robert Oppenheimer.",
    "Three days later, a second bomb is meant for a different city, yet it falls on Nagasaki.",
    "And it all begins with a letter to the president.",
]
ch0["shots"] = [
    {"s": 1, "film": "airwar", "from": 699, "to": 703.5, "stamp": ["HIROSHIMA"]},
    {"s": 2, "film": "vj", "from": 343, "to": 348, "note": "130,000 PEOPLE"},
    {"s": 3, "file": "J. R. Oppenheimer Los Alamos ID.jpg", "reveal": [0.7, 0.25], "name": "J. Robert Oppenheimer",
     "role": "Director, Los Alamos Laboratory"},
    {"s": 4, "film": "naga", "from": 28, "to": 34, "sfx": "explosion_far"},
    {"s": 5, "film": "trinity", "from": 547, "to": 551},
]
ch0["beats"] = [{"after": 1, "audio": {"src": "truman", "from": 23.3, "to": 32.55}, "shots": [
    {"dur": 3.4, "film": "airwar", "from": 704, "to": 707.8, "source": src},
    {"dur": 3.0, "film": "strikes", "from": 264, "to": 268, "source": src},
    {"dur": 3.2, "film": "airwar", "from": 689, "to": 693.5, "source": src}]}]
for c in d["chapters"][1:]:                            # silent film beats: ~6 s
    for b in c.get("beats") or []:
        if b.get("audio") or b.get("quote"):
            continue
        keep, tot = [], 0.0
        for s in b["shots"]:
            if tot >= 5.0 or (keep and s.get("focus") and keep[-1].get("focus")):
                break
            keep.append(s)
            tot += float(s["dur"])
        b["shots"] = keep
d["priority"] = 0
out = ROOT / "docs/retention/atomic_r.json"
out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved", out, "| beats:", [(k, b["after"], round(sum(float(s["dur"]) for s in b["shots"]), 1))
                                 for k, c in enumerate(d["chapters"]) for b in c.get("beats") or []])
