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
  present tense, marker notes of the key names/numbers, 3-5 maps); thumbnail = the house photo (the cover picture)
  in black and white with the title in 3 lines: 'HISTORY OF THE' / '<NAME>' (on red) / 'IN {N} MINUTES'.
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
          '"intro": {"date": "FEBRUARY 12", "year": "1941", "place": "TRIPOLI"}, '
          '"promos": [{"chapter": 5, "sentences": ["...", "...", "..."], "top": "STALIN KEPT|3 B-29 BOMBERS", '
          '"key": ["B-29"], "hook": "number", "big": "847", "line": "OF WHAT?", "hidden": "", "end": "", '
          '"name": "..."}, ...], '
          '"shorts": [{"chapter": 0, "from": 1, "to": 5, "title": "...", "key": ["NAME"], "name": "..."}, ...], '
          '"chapters": [{"title": "", "mode": "action", "sentences": ["..."], "visuals": ["..."], '
          '"notes": ["", "ERWIN ROMMEL", ...], "map": {"sentence": 3, "places": ["Wikipedia title", ...], '
          '"labels": ["TRIPOLI", ...], "routes": [[0, 1]]}}, ...]}')


def topics():
    """The unused SEEDS, most viewed first."""
    used = {p.stem for p in STORIES.glob("*.json")}
    done = set()
    for p in STORIES.glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        done |= {d.get("topic", ""), d.get("title", "")}
    left = [t for t in SEEDS if t not in done and not S.is_used(t) and slug(t) not in used]
    views = S.page_views(left) if left else {}
    left.sort(key=lambda t: -views.get(t, 0))
    print("auto story candidates:", [(t, int(views.get(t, 0))) for t in left[:6]])
    return left


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
        "the story's most famous moment first (sentence 1 = what the viewer has just seen happen at that date and "
        "place), then one sentence per main chapter going back to how it came to this, then as its LAST sentence "
        "'This is the entire history of <name>.' (said over the title card). 'intro' = that moment as the screen "
        "shows it before the narrator: date ('AUGUST 6'), year ('1945'), place ('HIROSHIMA'), all in the article. "
        "Then 7-10 "
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

        "SHORTS (2 YouTube Shorts cut from the video, released the same day): each = ONE chapter's sentences "
        "from..to (chapter index 0 = the cold open, sentences 1-based), 60-140 words, ending on a CLIFFHANGER just "
        "before the answer or payoff (the Short then says 'full video on the channel'). Short 1 = the cold open "
        "without its last sentence; Short 2 = the most dramatic run of another chapter. title = 2-5 words on top "
        "of the Short with the topic's NAME (key = the name word(s)); name = the Short's YouTube title, max 80 "
        "characters, a fact of the story.\n"
        "PROMOS (2 YouTube Shorts that advertise the video, max 15 s each): from 2 DIFFERENT chapters (index 1+), "
        "each the most surprising fact of that chapter in 3 short sentences, 20-28 words in total, present tense, "
        "facts of the article, ending BEFORE the answer (the Short then sends the viewer to the full video). top = "
        "2 lines split by '|', 2-4 words each, with the topic's name (key = that word, without ?/:). hook = how the "
        "end card teases the answer, the 2 promos use 2 different hooks: 'number' (big = a number of the answer, "
        "line = 'OF WHAT?' or '<THING> IN <TIME>. HOW?'), 'redacted' (line = the answer's sentence without its last "
        "word(s), hidden = those word(s), shown blacked out), 'question' (end = the open question, max 5 words). "
        "name = the Short's YouTube title, max 80 characters, a fact.\n"
        "question = the debate question (max 8 words); summary = 3-5 factual sentences for the description; tags = "
        "12-15 search tags.\nReturn JSON " + J_KEYS)


def ok(d):
    return isinstance(d, dict) and isinstance(d.get("chapters"), list) and len(d["chapters"]) >= 6 and \
        all(isinstance(c, dict) and isinstance(c.get("sentences"), list) and c["sentences"] for c in d["chapters"]) \
        and "{N}" in str(d.get("title", ""))


def probe(d):
    """The draft as check() sees a finished entire story (the pictures come later)."""
    import copy                                        # the pictures come later: a shot per sentence for check()
    d = copy.deepcopy(d)
    for c in d.get("chapters") or []:
        if isinstance(c, dict) and isinstance(c.get("sentences"), list):
            c["shots"] = [{"s": i + 1, "file": "x"} for i in range(len(c["sentences"]))]
    for n, g in enumerate(d.get("promos") or []):
        if isinstance(g, dict):
            g.setdefault("id", f"p{n + 1}")
            g["shots"] = [{"s": 1, "file": "x"}]
    return {**d, "format": "entire", "thumb": {"file": "x"}, "cover": {"file": "x"},   # the speech is added later
            "pre": [{"dur": 2.8, "file": "x", "stamp": ["X", "1"]}, {"dur": 3, "file": "x", "stamp": ["X"],
                                                                     "audio": {"src": "speech", "from": 0, "to": 7}}],
            "period_audio": {"speech": {"file": "x", "speaker": "x"}}}


def write(topic, text):
    import longform as L
    art = text[:90000]
    d = S.gemini(rules(topic) + "\n\nARTICLE:\n" + art, ok, purpose="long script", read=300, tokens=32768)
    for rnd in range(3):
        hard, soft = L.check(probe(d), text)
        print(f"auto script round {rnd + 1}: hard {hard} | soft {soft[:4]}")
        if not hard and len(soft) <= 2:
            return d
        d = S.gemini(rules(topic) + "\n\nARTICLE:\n" + art + "\n\nYOUR DRAFT:\n" + json.dumps(d, ensure_ascii=False)
                     + "\n\nFIX THESE PROBLEMS (remove or rewrite every fact that is not in the article; keep the "
                     "length): " + "; ".join(hard + soft), ok, purpose="long editor", read=300, tokens=32768)
    hard, _ = L.check(probe(d), text)
    if hard:
        raise SystemExit(f"auto story check failed: {hard}")
    return d


def pictures(d, topic):
    """{(chapter, sentence): [file names]}, subject files, cover file -> the story's shots and cover.
    Nov 15: CHAPTER BY CHAPTER (jurgen's finder was built for a 60 s Short: <= 30 pictures and one Gemini look at
    <= 36 for the whole story = ~8 sentences with a picture out of 130). Each chapter: its own Commons searches
    ('visuals') + the subject's category, one Gemini look; a picture is used in one chapter only."""
    files, subj, covers, used = {}, [], [], set()
    for k, c in enumerate(d["chapters"]):
        sents = [plain(s) for s in c["sentences"]]
        vis = (c.get("visuals") or [])[:len(sents)]
        flat = {"headline": sents[0], "lines": sents[1:], "people": {},
                "visuals": [{"sentence": str(n + 1), "search": v} for n, v in enumerate(vis)]}
        try:
            cands = J.story_candidates(flat, {"articles": [topic]})
        except Exception as e:
            print(f"chapter {k}: pictures failed: {type(e).__name__}")
            continue
        name_of = {str(p): n for p, n, cr, h in cands}
        cands = [x for x in cands if x[1] not in used]
        credit_of = {p: cr for p, n, cr, h in cands}
        hint_of = {p: h for p, n, cr, h in cands}
        by_sent, subject, _, _ = J.match_pictures([p for p, *_ in cands], [], {}, flat, {"articles": [topic]},
                                                  credit_of=credit_of, hint_of=hint_of)
        for n, ps in by_sent.items():
            names = [name_of[str(x)] for x in ps if str(x) in name_of and name_of[str(x)] not in used][:2]
            if 0 <= n < len(sents) and names:
                files[(k, n)] = names
                used.update(names)
        subj += [name_of[str(x)] for x in subject if str(x) in name_of and name_of[str(x)] not in subj]
        if flat.get("_cover") and str(flat["_cover"]) in name_of:
            covers.append(name_of[str(flat["_cover"])])
        print(f"chapter {k}: {sum(1 for (ck, _) in files if ck == k)} of {len(sents)} sentences with a picture")
    return files, subj, (covers[0] if covers else None)


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
        out.append({"from": [0, 1], "to": [0, len(chs[0]["sentences"]) - 1], "title": cover["text"][0],
                    "key": cover["key"], "name": plain(chs[0]["sentences"][0])[:90]})
    return out[:2]


class Skip(Exception):
    """This topic cannot make a video by the rules: the next topic is tried."""


def make():
    """Andrii, Nov 15: a video only by the rules: a period SPEECH of a known person about the topic (speech.py), no
    photo longer than 10 s (>= 3 pictures in every chapter) -> topics are tried in order until one passes."""
    tried = []
    for topic in topics()[:4]:
        try:
            return make_one(topic)
        except Skip as e:
            print(f"auto story: {topic} skipped: {e}")
            tried.append(topic)
    raise SystemExit(f"auto story: no topic passed the rules: {tried}")


def make_one(topic):
    import speech
    title, text = S.wiki_text(topic, limit=90000)     # the whole article (the checker uses the same text)
    if not title:
        raise Skip("article not found")
    print("auto story topic:", title)
    sp = speech.find(title, [f"{title} speech", f"{title} address", f"{title} radio broadcast"])
    if not sp:                                         # first: no speech, no video (and no Gemini script spent)
        raise Skip("no period speech of a known person about it on Commons")
    d = write(title, text)
    files, subj, cover = pictures(d, title)
    if len(files) < 15 or not subj:
        raise Skip(f"too few pictures ({len(files)} sentences, {len(subj)} subject photos)")
    pool, k = subj[:], 0
    for ci, c in enumerate(d["chapters"]):
        shots = []
        for i in range(len(c["sentences"])):
            got = files.get((ci, i))
            if not got and i == 0:                     # every chapter opens on a picture
                got, k = [pool[k % len(pool)]], k + 1
            for f in got or []:
                shots.append({"s": i + 1, "file": f})
        have = {s["file"] for s in shots}              # Andrii, Nov 15: no photo > 10 s -> >= 3 pictures a chapter
        free = [i for i in range(len(c["sentences"])) if not files.get((ci, i)) and i]
        for i in free[1::2]:
            if len(have) >= 3 and len(have) * 3 >= len(c["sentences"]):
                break
            f = next((x for x in pool[k:] + pool[:k] if x not in have), None)
            if not f:
                break
            k = (pool.index(f) + 1) % len(pool)
            shots.append({"s": i + 1, "file": f})
            have.add(f)
        if len(have) < 3:
            raise Skip(f"chapter {ci}: only {len(have)} pictures (a photo would stay over 10 s)")
        c["shots"] = sorted(shots, key=lambda s: s["s"])
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
    intro = d.pop("intro", None)                       # INTRO rule (Nov 15): film-less here: the cold open's own
    pics = [s["file"] for s in d["chapters"][0]["shots"] if s.get("file")]   # pictures under the DATE / PLACE stamps
    if isinstance(intro, dict) and len(pics) >= 2 and intro.get("year") and intro.get("place") and \
            str(intro["year"]) in text and str(intro["place"]).lower() in text.lower():   # facts of the article
        date = str(intro.get("date") or "").upper()[:20]
        stamp1 = [date, str(intro["year"])[:9]] if date else [str(intro["year"])[:9]]
        d["pre"] = [{"dur": 2.6, "file": pics[0], "sfx": "explosion_far"},
                    {"dur": 2.8, "file": pics[1], "stamp": stamp1},
                    {"dur": 3.0, "file": pics[2 % len(pics)], "stamp": [str(intro["place"]).upper()[:14]]}]
    else:                                              # no date/place of the article: the speech without stamps
        d["pre"] = [{"dur": 2.6, "file": pics[0], "sfx": "explosion_far"},
                    {"dur": 3.0, "file": pics[1 % len(pics)]}]
    src = " · ".join(x for x in (sp["speaker"].upper(), sp["date"].upper()) if x)
    d["period_audio"] = {"speech": {k_: sp[k_] for k_ in ("file", "credit", "speaker", "text", "date")}}
    d["pre"][-1].update({"hush": True, "audio": {"src": "speech", "from": sp["from"], "to": sp["to"]}, "source": src})
    rest = sp["to"] - sp["from"] - d["pre"][-1]["dur"] + 0.8   # the speech alone, over 1-2 more pictures
    while rest > 0.3:
        dur = min(4.0, rest)
        d["pre"].append({"dur": round(dur, 2), "file": pics[len(d["pre"]) % len(pics)], "source": src})
        rest -= dur
    promos = []                                       # PROMO TEASERS (Nov 15): Gemini's 2 -> story `promos`
    for n, g in enumerate(d.pop("promos", None) or []):
        try:
            k = int(g["chapter"])
            sents = [str(x) for x in g["sentences"]][:3]
            pics = [s for s in d["chapters"][k]["shots"] if s.get("file")][:3]
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        if not 1 <= k < len(d["chapters"]) or len(sents) < 2 or not pics or len(" ".join(sents).split()) > 30:
            continue
        hook = str(g.get("hook") or "question")
        cta = ({"kind": "number", "big": str(g.get("big", ""))[:6], "line": str(g.get("line", "")).upper()[:28]}
               if hook == "number" and g.get("big") else
               {"kind": "redacted", "line": str(g.get("line", "")).upper()[:24], "hidden": str(g.get("hidden", "")).upper()[:12]}
               if hook == "redacted" and g.get("hidden") else {"kind": "question"})
        promos.append({"id": f"p{n + 1}", "chapter": k, "sentences": sents,
                       "shots": [{**s, "s": i + 1} for i, s in enumerate(pics)][:len(sents)],
                       "top": str(g.get("top", "")).upper()[:40], "key": [str(x).upper() for x in g.get("key") or []],
                       "cta": cta, "end": str(g.get("end") or "WHAT HAPPENS NEXT?").upper()[:30],
                       "name": plain(str(g.get("name") or sents[0]))[:90]})
    if promos:
        d["promos"] = promos[:2]
    d.pop("thumb", None)
    left = cover or subj[0]
    d.pop("short", None)
    d["format"] = "entire"
    d["cover"] = {"file": left}                        # longform.entire_cover writes the words from the title
    L_ = __import__("longform")
    L_.entire_cover(d)
    d["clips"] = shorts_of(d, d.pop("shorts", None), d["cover"])
    d.update({"priority": 99, "topic": title, "sources": [], "thumb": {"file": left}, "pronounce": {},
              "films": {}, "auto": True})
    path = STORIES / (slug(title) + ".json")
    path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("auto story written:", path)
    return str(path)
