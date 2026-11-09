"""AUTO STORY (Andrii, Nov 9: 'write the ready stories yourself; when they run out, the bot writes its own'): when
stories/long/ has no unused story, the bot writes one in the same format with Gemini, from Wikipedia, and pictures
from Wikimedia Commons, then longform.py renders it like a hand-made one.
- Topic: SEEDS (subjects that reach millions on the big WW2 channels: last days, trials, fates, famous ships and
  battles), the most viewed on Wikipedia in the last 30 days that is not used yet.
- Script: Gemini writes 7-10 chapters (mode people|action, 1,500-1,900 words) only from the article text; the same
  check() as the hand-made stories (numbers_ok, names_ok, OVERCLAIM, numbers per ~12 s) sends problems back to
  an editor round; hard problems after the last round -> exit 3 (no video, nothing published).
- Pictures: the subject's own Commons category + one Commons search per sentence (Gemini's 'visual'), then one
  Gemini look at all of them (jurgen.match_pictures: which sentence each shows, wrong era, watermarks, bodies).
- Thumbnail: the house case file (left = the subject's best picture, centre = the main person's portrait,
  right = the other side's portrait; stamp = one true word chosen by Gemini).
- No archive film (picking film seconds needs a person); photos only. The story file is saved under
  stories/long/auto-*.json (committed by the workflow) so it can be reviewed and fixed by hand later.
Gemini quota: ~4-6 requests (script, 1-2 editor rounds, pictures, translations)."""
import json, pathlib, re
from urllib.parse import unquote

import shorts as S
import jurgen as J
from shorts import W, env, plain, pmap

STORIES = pathlib.Path("stories/long")
SEEDS = [   # exact English Wikipedia titles
    "Heinrich Himmler", "Joseph Goebbels", "Martin Bormann", "Reinhard Heydrich", "Erwin Rommel", "Rudolf Hess",
    "Benito Mussolini", "Hideki Tojo", "Josef Mengele", "Adolf Eichmann", "Klaus Barbie", "Albert Speer",
    "Karl Dönitz", "Wilhelm Keitel", "Claus von Stauffenberg", "Eva Braun", "Isoroku Yamamoto", "Hiroo Onoda",
    "German battleship Bismarck", "German battleship Tirpitz", "Japanese battleship Musashi", "Sinking of the Wilhelm Gustloff",
    "German submarine U-505", "German submarine U-234", "Attack on Pearl Harbor", "Battle of Stalingrad",
    "Battle of the Bulge", "Operation Market Garden", "Normandy landings", "Battle of Iwo Jima",
    "Doolittle Raid", "Operation Vengeance", "Operation Mincemeat", "Gran Sasso raid", "Lady Be Good (aircraft)",
    "Enola Gay", "Bockscar", "Battle of Berlin", "Battle of Okinawa", "Siege of Leningrad", "Dunkirk evacuation",
    "Japanese aircraft carrier Shinano", "Operation Valkyrie", "Simo Häyhä", "Desmond Doss", "Audie Murphy",
    "Michael Wittmann", "Otto Skorzeny", "Joachim Peiper", "Hermann Fegelein", "Wernher von Braun",
]
J_KEYS = ('{"title": "...", "question": "...", "summary": "...", "tags": ["..."], '
          '"case": {"label": "...", "stamp": "...", "left_caption": "...", "center_person": "Wikipedia title", '
          '"center_caption": "...", "right_person": "Wikipedia title", "right_caption": "..."}, '
          '"chapters": [{"title": "", "mode": "action", "sentences": ["..."], "visuals": ["..."]}, ...]}')


def pick():
    used = {p.stem for p in STORIES.glob("*.json")}
    done = set()
    for p in STORIES.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        done |= {d.get("topic", ""), d.get("title", "")}
    left = [t for t in SEEDS if t not in done and not S.is_used(t) and slug(t) not in used]
    views = S.page_views(left) if left else {}
    left.sort(key=lambda t: -views.get(t, 0))
    print("auto story candidates:", [(t, int(views.get(t, 0))) for t in left[:6]])
    return left[0] if left else None


def slug(t):
    return "auto-" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40]


def rules(topic):
    return (
        f"Write a 10-12 minute YouTube documentary script about: {topic}. Use ONLY facts in the ARTICLE below: every "
        "number, date, name and quote must appear there (a checker rejects anything else). Calm, clear narration "
        "for an English-speaking audience, no hype words, no 'you', no rhetorical questions except the last line.\n"
        "STRUCTURE: chapter 1 = cold open with title '' and mode 'action': 5-7 sentences, the most dramatic moment "
        "first (date + place in sentence 1), then why it still matters, then 'This is the story of ...'. Then 6-9 "
        "chapters with short titles (2-4 words), each 7-12 sentences, in time order; mode 'people' for decisions, "
        "characters and fates, 'action' for battles, attacks and sinkings. Open each chapter with a re-hook. The "
        "last chapter ends with a quiet closing fact, then ONE final sentence: a debate question to the viewer that "
        "ends with 'Tell me what you think in the comments.'\n"
        "LENGTH: 1,500-1,900 words in total. Sentences of 8-26 words. At most 3 numbers in any 30 words: say the "
        "rest in words ('half', 'most of them', 'a few hours'). Years and the day of a date do not count.\n"
        "For EVERY sentence give a 'visual': 2-5 words to search Wikimedia Commons for a 1930s-1940s photo that shows "
        "exactly that sentence (a person's full name, a ship's name, a place + year), same order as the sentences.\n"
        "TITLE: the famous name first, then a colon and the promise or fate, max 70 characters (like 'Hermann Göring: "
        "How He Cheated the Hangman at Nuremberg').\n"
        "CASE (the thumbnail, a 1945 case file with three pinned photos): label = 'SUBJECT - MONTH YEAR' (max 30 "
        "characters, capitals); stamp = ONE true word for the centre photo (GUILTY, SUNK, EXECUTED, MISSING, SUICIDE, "
        "SHOT DOWN, DECODED...); left_caption = the place or machine; center_person = the Wikipedia title of the "
        "main person; right_person = the Wikipedia title of the other side of the story; captions max 18 "
        "characters.\n"
        "question = the debate question (max 8 words); summary = 3-5 factual sentences for the description; tags = "
        "12-15 search tags.\nReturn JSON " + J_KEYS)


def ok(d):
    return isinstance(d, dict) and isinstance(d.get("chapters"), list) and len(d["chapters"]) >= 6 and \
        all(isinstance(c, dict) and isinstance(c.get("sentences"), list) and c["sentences"] for c in d["chapters"]) \
        and isinstance(d.get("case"), dict) and d.get("title")


def write(topic, text):
    import longform as L
    art = text[:24000]
    d = S.gemini(rules(topic) + "\n\nARTICLE:\n" + art, ok, purpose="long script")
    for rnd in range(2):
        hard, soft = L.check({**d, "thumb": {"file": "x"}, "case": {"left": {"file": "x"}, "center": {"file": "x"},
                                                                    "right": {"file": "x"}, "stamp": "x"}}, text)
        print(f"auto script round {rnd + 1}: hard {hard} | soft {soft[:4]}")
        if not hard and len(soft) <= 2:
            return d
        d = S.gemini(rules(topic) + "\n\nARTICLE:\n" + art + "\n\nYOUR DRAFT:\n" + json.dumps(d, ensure_ascii=False)
                     + "\n\nFIX THESE PROBLEMS (remove or rewrite every fact that is not in the article; keep the "
                     "length): " + "; ".join(hard + soft), ok, purpose="long editor")
    hard, _ = L.check({**d, "thumb": {"file": "x"}, "case": {"left": {"file": "x"}, "center": {"file": "x"},
                                                             "right": {"file": "x"}, "stamp": "x"}}, text)
    if hard:
        raise SystemExit(f"auto story check failed: {hard}")
    return d


def file_of(url):
    """Commons file name from an upload URL (thumb or original)."""
    parts = unquote(url.split("?")[0]).split("/")
    return parts[-2] if "/thumb/" in url else parts[-1]


def pictures(d, topic):
    """{(chapter, sentence): [file names]}, subject files, cover file -> the story's shots and case."""
    sents, where = [], []
    for k, c in enumerate(d["chapters"]):
        for i, s in enumerate(c["sentences"]):
            sents.append(plain(s))
            where.append((k, i))
    flat = {"headline": sents[0], "lines": sents[1:], "people": {},
            "visuals": [{"sentence": str(n + 1), "search": v}
                        for n, v in enumerate(v for c in d["chapters"] for v in (c.get("visuals") or []))][:len(sents)]}
    cands = J.story_candidates(flat, {"articles": [topic]})
    name_of = {str(p): n for p, n, c, h in cands}
    credit_of = {p: c for p, n, c, h in cands}
    hint_of = {p: h for p, n, c, h in cands}
    by_sent, subject, _, _ = J.match_pictures([p for p, *_ in cands], [], {}, flat, {"articles": [topic]},
                                              credit_of=credit_of, hint_of=hint_of)
    files = {}
    for n, ps in by_sent.items():
        if 0 <= n < len(where):
            files[where[n]] = [name_of[str(p)] for p in ps if str(p) in name_of][:2]
    subj = [name_of[str(p)] for p in subject if str(p) in name_of]
    cover = name_of.get(str(flat.get("_cover"))) if flat.get("_cover") else None
    return files, subj, cover


def make():
    topic = pick()
    if not topic:
        raise SystemExit("auto story: no topic left in SEEDS")
    title, text = S.wiki_text(topic)
    if not title:
        raise SystemExit(f"auto story: article not found: {topic}")
    print("auto story topic:", title)
    d = write(title, text)
    files, subj, cover = pictures(d, title)
    if len(files) < 15 or not subj:
        raise SystemExit(f"auto story: too few pictures ({len(files)} sentences, {len(subj)} subject photos)")
    pool, k = subj[:], 0
    for ci, c in enumerate(d["chapters"]):
        shots = []
        for i in range(len(c["sentences"])):
            got = files.get((ci, i))
            if not got and i == 0:                     # every chapter opens on a picture
                got, k = [pool[k % len(pool)]], k + 1
            for f in got or []:
                shots.append({"s": i + 1, "file": f})
        c["shots"] = shots
        c.pop("visuals", None)
    cs = d.pop("case")

    def portrait(t):
        got = J.lead_image(t) if t else None
        return file_of(got[0]) if got else None
    center, right = portrait(cs.get("center_person")), portrait(cs.get("right_person"))
    left = cover or subj[0]
    d["case"] = {"label": str(cs.get("label", title))[:32].upper(),
                 "left": {"file": left, "caption": str(cs.get("left_caption", ""))[:18].upper()},
                 "center": {"file": center or subj[min(1, len(subj) - 1)], "color": "tone",
                            "caption": str(cs.get("center_caption", ""))[:18].upper()},
                 "right": {"file": right or subj[-1], "color": "tone",
                           "caption": str(cs.get("right_caption", ""))[:18].upper()},
                 "stamp": str(cs.get("stamp", "CLASSIFIED")).upper()[:12]}
    d.update({"priority": 99, "topic": title, "sources": [], "thumb": {"file": left}, "pronounce": {},
              "films": {}, "auto": True})
    path = STORIES / (slug(title) + ".json")
    path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("auto story written:", path)
    return str(path)
