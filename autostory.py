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
- Format (Andrii, Nov 10): The Entire War ('The ENTIRE History of X in {N} Minutes', 1,900-2,300 words in the
  present tense, marker notes of the key names/numbers, 3-5 maps); thumbnail thumbs.py `entire` (the cover picture,
  the main person's Wikipedia portrait cut out, the NAME in yellow stencil + years).
- No archive film (picking film seconds needs a person); photos only. The story file is saved under
  stories/long/auto-*.json (committed by the workflow) so it can be reviewed and fixed by hand later.
Gemini quota: ~4-6 requests (script, 1-2 editor rounds, pictures, translations)."""
import json, pathlib, re
from urllib.parse import unquote

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))  # shorts/jurgen/pastrak from ww2-bot
import shorts as S
import jurgen as J
from shorts import W, env, plain, pmap

STORIES = pathlib.Path("stories/long")
SEEDS = [   # exact English Wikipedia titles: whole subjects (The Entire War format, Andrii, Nov 10)
    "Boeing B-29 Superfortress", "Boeing B-17 Flying Fortress", "Panther tank", "T-34", "Panzer IV",
    "Messerschmitt Bf 109", "Supermarine Spitfire", "Junkers Ju 87", "Messerschmitt Me 262", "V-2 rocket",
    "Fallschirmjäger", "Royal Air Force Bomber Command", "Flying Tigers", "101st Airborne Division",
    "Imperial Japanese Army", "Gestapo", "Hitler Youth", "Volkssturm", "Italian Army in World War II",
    "Manhattan Project", "Enigma machine", "German battleship Bismarck", "Atlantic Wall", "Battle of Britain",
    "Battle of the Atlantic", "Battle of Stalingrad", "Battle of the Bulge", "Battle of Okinawa", "Battle of Iwo Jima",
    "Guadalcanal campaign", "Burma campaign", "Winter War", "Korean War", "Operation Barbarossa", "Normandy landings",
    "Liberty ship", "PT boat", "Higgins boat", "Willys MB", "M1 Garand",
]
J_KEYS = ('{"name": "the Afrika Korps", "title": "The ENTIRE History of the Afrika Korps in {N} Minutes", '
          '"question": "...", "summary": "...", "tags": ["..."], '
          '"thumb": {"name": ["AFRIKA", "KORPS"], "years": "1941 – 1943", "person": "Wikipedia title"}, '
          '"shorts": [{"chapter": 0, "from": 1, "to": 5, "title": "...", "key": ["NAME"], "name": "..."}, ...], '
          '"chapters": [{"title": "", "mode": "action", "sentences": ["..."], "visuals": ["..."], '
          '"notes": ["", "ERWIN ROMMEL", ...], "map": {"sentence": 3, "places": ["Wikipedia title", ...], '
          '"labels": ["TRIPOLI", ...], "routes": [[0, 1]]}}, ...]}')


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
        f"Write a 12-17 minute YouTube documentary script: the ENTIRE history of: {topic}, from its beginning to its "
        "end. Use ONLY facts in the ARTICLE below: every number, date, name and quote must appear there (a checker "
        "rejects anything else). Clear narration for an English-speaking audience, told in the PRESENT tense ('In "
        "February 1941, a German general lands in Tripoli...'), no hype words, no 'you', no rhetorical questions "
        "except the last line.\n"
        "STRUCTURE: chapter 1 = cold open with title '' and mode 'action': 4-6 sentences, ONE odd, visible detail of "
        "the story first (date + place in sentence 1), then 'This is the entire history of <name>.' Then 7-10 "
        "chapters in time order with short titles (2-4 words), each 8-14 sentences; mode 'people' for decisions and "
        "leaders, 'action' for battles. Open each chapter with a re-hook. The last chapter ends with a quiet closing "
        "fact, then ONE final sentence: a debate question to the viewer that ends with 'Tell me what you think in "
        "the comments.'\n"
        "LENGTH: 1,900-2,300 words in total. Sentences of 8-26 words. At most 3 numbers in any 30 words: say the "
        "rest in words ('half', 'most of them'). Years and the day of a date do not count.\n"
        "For EVERY sentence give a 'visual': 2-5 words to search Wikimedia Commons for a 1930s-1940s photo that shows "
        "exactly that sentence (a person's full name, a ship's name, a place + year), same order as the sentences.\n"
        "NOTES: per chapter 'notes', one per sentence ('' for none): the key NAME or NUMBER of that sentence written "
        "on screen in marker (like 'ERWIN ROMMEL', '130,000 PRISONERS'), exactly as in the sentence, at most one in "
        "three sentences.\n"
        "MAPS: in 3-5 chapters a 'map' for the sentence that moves armies or ships: places = 2-4 English Wikipedia "
        "titles of towns, islands or ports that have coordinates, labels = their short names in capitals, routes = "
        "pairs of place indexes in order (like [[0, 1], [1, 2]]).\n"
        "TITLE: exactly 'The ENTIRE History of <name> in {N} Minutes' ({N} stays as it is: the bot puts the real "
        "length in), or for a whole war 'The <War> Explained in {N} Minutes'; name = the subject as said in a "
        "sentence ('the Afrika Korps').\n"
        "THUMB: name = the subject's short NAME in capitals in 1-2 lines; years = 'YYYY – YYYY' of its story; "
        "person = the English Wikipedia title of the person most tied to it (its commander, designer or hero).\n"
        "SHORTS (2 YouTube Shorts cut from the video, released the same day): each = ONE chapter's sentences "
        "from..to (chapter index 0 = the cold open, sentences 1-based), 60-140 words, ending on a CLIFFHANGER just "
        "before the answer or payoff (the Short then says 'full video on the channel'). Short 1 = the cold open "
        "without its last sentence; Short 2 = the most dramatic run of another chapter. title = 2-5 words on top "
        "of the Short with the topic's NAME (key = the name word(s)); name = the Short's YouTube title, max 80 "
        "characters, a fact of the story.\n"
        "question = the debate question (max 8 words); summary = 3-5 factual sentences for the description; tags = "
        "12-15 search tags.\nReturn JSON " + J_KEYS)


def ok(d):
    return isinstance(d, dict) and isinstance(d.get("chapters"), list) and len(d["chapters"]) >= 6 and \
        all(isinstance(c, dict) and isinstance(c.get("sentences"), list) and c["sentences"] for c in d["chapters"]) \
        and isinstance(d.get("thumb"), dict) and d["thumb"].get("name") and "{N}" in str(d.get("title", ""))


def probe(d):
    """The draft as check() sees a finished entire story (the pictures come later)."""
    return {**d, "format": "entire", "thumb": {"file": "x"}, "thumb_entire": {"bg": {"file": "x"}, "name": ["X"]}}


def write(topic, text):
    import longform as L
    art = text[:24000]
    d = S.gemini(rules(topic) + "\n\nARTICLE:\n" + art, ok, purpose="long script")
    for rnd in range(2):
        hard, soft = L.check(probe(d), text)
        print(f"auto script round {rnd + 1}: hard {hard} | soft {soft[:4]}")
        if not hard and len(soft) <= 2:
            return d
        d = S.gemini(rules(topic) + "\n\nARTICLE:\n" + art + "\n\nYOUR DRAFT:\n" + json.dumps(d, ensure_ascii=False)
                     + "\n\nFIX THESE PROBLEMS (remove or rewrite every fact that is not in the article; keep the "
                     "length): " + "; ".join(hard + soft), ok, purpose="long editor")
    hard, _ = L.check(probe(d), text)
    if hard:
        raise SystemExit(f"auto story check failed: {hard}")
    return d


def pictures(d, topic):
    """{(chapter, sentence): [file names]}, subject files, cover file -> the story's shots and cover."""
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


def shorts_of(d, got, cover):
    """Gemini's 2 Shorts -> story `clips` (checked: one chapter, in range, 50-150 words); the cold open (without its
    'This is the story of' line) when Gemini's are missing or wrong."""
    chs, out = d["chapters"], []
    for s in got if isinstance(got, list) else []:
        try:
            c, a, b = int(s["chapter"]), int(s["from"]), int(s["to"])
            part = chs[c]["sentences"][a - 1:b]
            key = s.get("key") or []
            key = [key] if isinstance(key, str) else key
            if 1 <= a <= b <= len(chs[c]["sentences"]) and 50 <= len(" ".join(part).split()) <= 150 and s.get("title"):
                out.append({"from": [c, a], "to": [c, b], "title": str(s["title"]).upper()[:40],
                            "key": [str(k).upper().strip("?!.,\":") for k in key],
                            "name": plain(str(s.get("name") or d["title"]))[:90]})
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    if not out and len(chs[0]["sentences"]) >= 3:
        out.append({"from": [0, 1], "to": [0, len(chs[0]["sentences"]) - 1], "title": " ".join(cover["name"]),
                    "key": [w for line in cover["name"] for w in line.split()], "name": plain(chs[0]["sentences"][0])[:90]})
    return out[:2]


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
    for c in d["chapters"]:                            # marker notes: only words that are in their sentence
        notes = c.pop("notes", None)
        notes = notes if isinstance(notes, list) else []
        for s in c["shots"]:
            n = notes[s["s"] - 1] if s["s"] - 1 < len(notes) else ""
            if n and str(n).upper() in plain(c["sentences"][s["s"] - 1]).upper() and not any(
                    x.get("note") for x in c["shots"] if x["s"] == s["s"]):
                s["note"] = str(n).upper()[:28]
        m = c.pop("map", None)
        if isinstance(m, dict) and isinstance(m.get("places"), list) and 2 <= len(m["places"]) <= 5:
            coords = S.wiki_coords([str(x) for x in m["places"]])
            labels = m.get("labels") or []
            ps = [{"label": str(labels[n] if n < len(labels) else x).upper()[:18], "lat": coords[x][0], "lon": coords[x][1]}
                  for n, x in enumerate(m["places"]) if x in coords]
            try:
                at = int(m.get("sentence", 1))
            except (TypeError, ValueError):
                at = 1
            if len(ps) == len(m["places"]) and 1 <= at <= len(c["sentences"]):
                routes = [r for r in (m.get("routes") or []) if isinstance(r, list) and len(r) == 2
                          and all(isinstance(x, int) and 0 <= x < len(ps) for x in r)]
                c["shots"].append({"s": at, "map": {"places": ps, "routes": routes}})
                c["shots"].sort(key=lambda s: s["s"])
    th = d.pop("thumb")
    left = cover or subj[0]
    person = None
    if th.get("person"):
        got = J.lead_image(str(th["person"]))
        person = unquote(got[0].split("?")[0]).split("/")[-2 if "/thumb/" in got[0] else -1] if got else None
    name = th.get("name") or [title]
    name = [name] if isinstance(name, str) else name
    d["format"] = "entire"
    d["thumb_entire"] = {"bg": {"file": left}, "name": [str(x).upper() for x in name][:2],
                         "years": str(th.get("years") or "")[:15]}
    if person:
        d["thumb_entire"]["person"] = {"file": person, "color": "tone", "x": 0.76, "h": 1.0}
    d["clips"] = shorts_of(d, d.pop("shorts", None), d["thumb_entire"])
    d.update({"priority": 99, "topic": title, "sources": [], "thumb": {"file": left}, "pronounce": {},
              "films": {}, "auto": True})
    path = STORIES / (slug(title) + ".json")
    path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("auto story written:", path)
    return str(path)
