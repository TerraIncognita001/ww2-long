"""Check a PASTRAK story file (stories/pastrak/*.json) like the hand review: pastrak.check() with the facts HARD
against the full article text(s), word count, shots per sentence, film ranges.
Usage: python3 pcheck.py story.json article.txt [more_article.txt ...]"""
import sys, json, os, pathlib
args = sys.argv[1:]
sys.argv = sys.argv[:1]
ROOT = pathlib.Path(__file__).resolve().parents[2]; os.chdir(ROOT); sys.path.insert(0, str(ROOT))
import pastrak as P
d = json.load(open(args[0], encoding="utf-8"))
full = "\n".join(open(f, encoding="utf-8").read() for f in args[1:])
hard, soft = P.check(d, full, facts_hard=True)
print(f"hard {hard}\nsoft {soft}")
ss = P.sentences(d)
print("sentences:", len(ss), "| words:", len(" ".join(ss).split()), "| at ~160 wpm:", round(len(" ".join(ss).split()) / 160 * 60), "s")
shots = d.get("shots") or []
per = {}
for s in shots:
    per.setdefault(int(s["sentence"]), []).append(s)
print("shots:", len(shots), "| films:", sum(1 for s in shots if s.get("film")), "| photos:", sum(1 for s in shots if s.get("file")),
      "| distinct photos:", len({s["file"] for s in shots if s.get("file")}))
for i, s in enumerate(ss, 1):
    items = per.get(i, [])
    desc = ", ".join((f"{x['film']} {x['from']}-{x['to']}" if x.get("film") else x["file"][:38]) + (f" [{x['sfx']}]" if x.get("sfx") else "") for x in items)
    print(f"{i:2d} {len(s.split()):2d}w | {desc or ('COVER' if i == len(ss) else '-')}")
slow = [i for i, s in enumerate(ss[:-1], 1) if len(s.split()) / max(1, len(per.get(i, []))) > 10]
if slow:
    print("sentences with one shot per more than 10 words (~3.7 s; PastTrack cuts every 2-3 s):", slow)
bad = [s for s in shots if s.get("film") and not float(s["to"]) > float(s["from"])]
if bad:
    print("film ranges to <= from:", bad)
