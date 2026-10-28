"""Check a story file like the hand review: jurgen.check() (hard + soft), numbers/names vs the article text,
labels kept by finish() against the bot's 20,000-character text, word count."""
import sys, json, os, pathlib
sys.argv, story, textfile = sys.argv[:1], sys.argv[1], sys.argv[2]
ROOT = pathlib.Path(__file__).resolve().parents[2]; os.chdir(ROOT); sys.path.insert(0, str(ROOT))
import shorts as S, jurgen as J
d = json.load(open(story, encoding="utf-8"))
full = open(textfile, encoding="utf-8").read()
J.set_length(d.get("length", "full"))
for name, text in (("full article", full), ("bot's first 20,000 chars", full[:20000])):
    topic = {"articles": [d["topic"]], "key": d["topic"], "text": text, "hook": d.get("hook"), "structure": "story"}
    hard, soft = J.check(d, topic)
    print(f"== {name}: hard {hard}\n   soft {soft}")
    fin = J.finish(d, topic)
    print("   labels kept:", fin["labels"], "| title:", fin["title"])
ss = J.sentences(d)
print("sentences:", len(ss), "| words:", len(" ".join(ss).split()), "| first:", len(ss[0].split()), "words", len(ss[0]), "chars")
pics = d.get("pictures") or []
have = {int(p["sentence"]) for p in pics}
print("pictures:", len(pics), "| distinct files:", len({p['file'] for p in pics}), "| sentences without:", [i for i in range(1, len(ss) + 1) if i not in have])
