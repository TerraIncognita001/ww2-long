"""JURGEN format (experiment, branch jurgen-experiment): a 2.5-3 minute documentary Short in the style of the
Jurgens channel (@jurgens16, 1-8 million views per Short). Run: python jurgen.py (same secrets and env as shorts.py).

What is different from the classic 15-28 s Shorts of shorts.py:
- ONE deep story (or 3-4 escalating cases) told by a calm narrator for 150-178 s (YouTube's limit is 180 s),
  ~430-470 words: names, ranks, dates, places, "according to the report of her commander...".
- Opens straight on the question of the title ("What were the strangest ways...?"), ends on the most remarkable
  fact ("...the only time in history..."), no punchline loop, no calls to action.
- Full-screen 9:16 pictures (no black bars, no channel block, no word-by-word captions): archive photos COLORIZED
  (DDColor, free, offline), portraits that slowly push in, landscapes that pan, documents and posters as cards on a
  dark background, archive film, a map with a red route; a new shot on every sentence (3-9 s), hard cuts.
- The person a sentence introduces is shown on their own Wikipedia portrait with the name in big white letters.
- On screen otherwise only a small title line at the top and small place/date labels.
- Only pictures that really belong to the story (one Gemini check of every photo and film against the story);
  no AI pictures by default.
- A deep, calm, steady narrator matched to the original by measurement (pitch ~91 Hz, steady tone, ~4.4 syllables
  a second); Andrii chose the plain en-GB-RyanNeural voice (his sample: natural pitch, pace and pauses).
- Atmospheric dark ambient drones (music/jurgen, Mixkit free licence) under the voice, no melody, no sound effects.
(Studied: "The Strangest Ways Germany Lost a U-Boat" 1.5M, "The Last Words of the Nazis Before They Were Executed"
16.7M, "What Did Adolf Hitler's Bodyguard Reveal After the War?" 8.3M, "What Happened to the German U-Boats after
the Second World War?" 7.7M views.)
- Title like "The U-Boat That Escaped to Argentina #history #ww2 #germany".
Every number and claim is still checked against Wikipedia (numbers_ok, OVERCLAIM, the editor's claims)."""
import base64, json, math, pathlib, random, re, subprocess, time, unicodedata
from urllib.parse import quote

import numpy as np
import requests

import shorts as S
from shorts import W, env, plain, gemini, pmap, stage, ff, probe_duration

MAX_LEN = float(env("J_MAX", "175"))                   # YouTube counts a vertical video up to 180 s as a Short
END_Q = float(env("J_END_Q", "0"))                     # the closing question on screen after the last word (v1.83,
# 2.2 s); v2.06 (Andrii, Oct 27): off, its silent last ~3 s lost 15-25% of the viewers still watching (Bormann 49% ->
# 37%, Häyhä 42% -> 32%; before it 36% -> 35%) and they swiped before the loop; the question stays the pinned comment
WORDS_LO, WORDS_HI, WORDS_AIM = 340, 430, "370-410"   # plain Ryan with natural pauses: ~140 words/min
# Length A/B (Andrii, Oct 18): U-234 (176 s) kept 77.8% of viewers and 1:57 average, but only 66.7% viewed:
# viewers leave before the end. 'short' tests ~130 s (the same 2 minutes of watching would be ~90%); the
# format learns from its own videos which length YouTube pushes more (stats field j_length).
J_LENGTHS = {"full": (340, 430, "370-410", "22-32", 175.0, "2 minutes 50 seconds"),
             "short": (260, 320, "280-310", "16-24", 140.0, "2 minutes 10 seconds")}
SENTS, SPOKEN = "22-32", "2 minutes 50 seconds"


def set_length(name):
    """Word target, sentence count and the voice's time limit of this video."""
    global WORDS_LO, WORDS_HI, WORDS_AIM, SENTS, MAX_LEN, SPOKEN
    WORDS_LO, WORDS_HI, WORDS_AIM, SENTS, MAX_LEN, SPOKEN = J_LENGTHS.get(name, J_LENGTHS["full"])
    if env("J_MAX"):
        MAX_LEN = float(env("J_MAX"))


def pick_length(stats):
    """full / short in turn until each has 3+ videos, then weighted by what this format's videos taught."""
    forced = (env("J_LENGTH") or "").strip().lower()
    if forced in J_LENGTHS:
        return forced
    mult = S.learned(stats, "j_length", list(J_LENGTHS), fmt="jurgen") or {k: 1.0 for k in J_LENGTHS}
    last = [v.get("j_length") for v in S.videos_of(stats, "jurgen")[-1:]]
    return random.choices(list(J_LENGTHS), weights=[mult[k] * (0.35 if k in last else 1.0) for k in J_LENGTHS])[0]


# ---- where viewers leave: YouTube Analytics retention curves ---------------------------------------------------
LESSONS = [""]                                         # filled before the script: where earlier viewers left


def retention_curves(creds, stats, most=8):
    """The audience retention curve (100 points: share of the video watched -> share of viewers still there) of the
    latest videos of every format (v2.06: classic and pastrak too, to see the second they swipe at), saved in stats
    with the 3 steepest drops mapped to the sentence being spoken (jurgen/pastrak; classic has no sentence times)."""
    from datetime import date, timedelta
    day = (date.today() - timedelta(days=1)).isoformat()
    vids = [v for fmt in ("jurgen", None, "pastrak") for v in [v for v in S.videos_of(stats, fmt)
            if v.get("id") and v.get("date", "9999") <= day][-most:]]
    if not vids or not creds:
        return
    try:
        from googleapiclient.discovery import build
        ya = build("youtubeAnalytics", "v2", credentials=creds)
    except Exception as e:
        print("retention curves skipped:", type(e).__name__)
        return
    for v in vids:
        try:
            r, why = None, ""
            for metrics in ("audienceWatchRatio,relativeRetentionPerformance", "audienceWatchRatio"):
                try:                                   # the relative metric is refused for some channels/videos
                    r = ya.reports().query(ids="channel==MINE", startDate=v["date"], endDate=date.today().isoformat(),
                                           metrics=metrics, dimensions="elapsedVideoTimeRatio",
                                           filters="video==" + v["id"]).execute()
                    break
                except Exception as e:
                    why = str(e)[:160]
            if r is None:
                raise RuntimeError(why)
            rows = sorted(r.get("rows") or [])
            if not rows:
                print("retention", v["id"], "| no rows yet (YouTube Analytics lags 2-3 days)")
            if rows:
                v["curve"] = [[round(x[0], 2), round(x[1], 3), round(x[2] if len(x) > 2 else 0, 3)] for x in rows]
                v["drops"] = biggest_drops(v)
                print("retention", v["id"], "| at the end:", round(rows[-1][1] * 100), "% | drops:",
                      [(d["t"], d["lost"]) for d in v["drops"]])
        except Exception as e:
            print("retention curve not read:", v.get("id"), str(e)[:120])


def biggest_drops(v, n=3):
    """The 3 steepest falls of the curve after the first 5% (the swipe-away is the hook's business), each with the
    second and the sentence being spoken there."""
    c, secs = v.get("curve") or [], float(v.get("seconds") or 0)
    starts, texts = v.get("sent_t") or [], v.get("sent") or []
    falls = sorted(((c[i - 1][1] - c[i][1], c[i][0]) for i in range(1, len(c)) if c[i][0] >= 0.05), reverse=True)[:n]
    out = []
    for lost, ratio in falls:
        t = ratio * secs
        k = max([j for j, x in enumerate(starts) if x <= t] or [0])
        out.append({"t": round(t), "lost": round(lost * 100, 1), "sentence": k + 1,
                    "text": texts[k] if k < len(texts) else ""})
    return out


def lessons(stats):
    """For the script writer: the sentences right where viewers of earlier videos of this format left."""
    drops = [d for v in S.videos_of(stats, "jurgen")[-6:] for d in v.get("drops") or [] if d.get("text")]
    if not drops:
        return ""
    worst = sorted(drops, key=lambda d: -d["lost"])[:6]
    return ("- RETENTION DATA from this format's earlier videos: many viewers left while these sentences were spoken "
            "(share of viewers lost): " + "; ".join(f"'{d['text']}' (-{d['lost']}%)" for d in worst)
            + ". Avoid that kind of sentence (background, lists, repeats, a beat without a new question); every "
            "sentence must pull to the next one.\n")
S.VOICE = env("J_VOICE", "en-GB-RyanNeural")            # Andrii's choice (Oct 18): the channel's British voice
S.TTS_RATE = env("J_RATE", "+0%")                       # Ryan as he is (Andrii's sample): natural pace and pauses
S.TTS_PITCH = env("J_PITCH", "+0Hz")
DEEPEN = float(env("J_DEEPEN", "1.0"))                 # <1 = deeper (0.92 = 8% lower + darker EQ); 1 = untouched
SHOT_MAX = 9.0
MIN_MATCHED = float(env("J_MIN_MATCHED", "0.4"))       # share of sentences that need a picture of their own
PIC_MIN = int(env("J_PIC_MIN", "12"))                  # a topic needs this many big free pictures (Shinano had ~3)
MIN_SIDE = 600                                         # smaller photos turn to grain when filled to 1080x1920
SECS_PER_PIC = 10.0                                    # at least one different picture per 10 s, else no video
SKIP = 3                                               # exit code: no good video possible -> a classic Short instead
UPLOADED = []                                         # one shot per sentence; only longer ones are split
SIZE = (1080, 1920)
FAST = env("J_FAST", "1") == "1"   # v1.94 (Oct 25, free Actions minutes): shots at 720x1280, scaled up once in the final
SHOT = (720, 1280) if FAST else SIZE   # render (2-3x faster; captions stay sharp: they are drawn after the scale)
SUBS = env("J_SUBS", "0") == "1"                       # 1 = small sentence subtitles (the original has none)
CAPS = env("J_CAPS", "1") == "1"                       # Andrii, Oct 24-25 (style C): two-line karaoke captions with
WHIP = env("J_WHIP", "1") == "1"                       # the title read in them, no place/date labels (S.captions_two);
                                                       # cuts open with a 2-frame sideways blur
AI_IMAGES = env("AI_IMAGES", "off")                    # off (Andrii: only real pictures of the story); auto = Gemini
                                                        # image models, then Pollinations (token)
AI_MAX = int(env("AI_MAX", "6"))                       # the originals are archive pictures; AI only fills gaps
AI_MODELS = [m.strip() for m in env("AI_IMAGE_MODELS", "gemini-2.5-flash-image,gemini-3.1-flash-image-preview")
             .split(",") if m.strip()]
POLL_TOKEN = env("POLLINATIONS_TOKEN", "")
CATS = ["events", "weapons", "people", "tanks"]   # v2.03 (Andrii, Oct 27): no classified (spy stories median 648 views)
CAT_W = {"events": 1.0, "weapons": 1.0, "people": 1.0, "classified": 0.6, "tanks": 1.6}   # Andrii, Oct 22: tanks too
# tank stories (Andrii, Oct 22): American, German and British first; Soviet ones only after them
TANK_SEEDS = ["DD tank", "Battle of Villers-Bocage", "Operation Goodwood", "Tiger 131", "Lafayette G. Pool",
              "Battle of Arracourt", "Battle of Arras (1940)", "Michael Wittmann", "Otto Carius", "Kurt Knispel",
              "Ernst Barkmann", "Battle of Kasserine Pass", "Hobart's Funnies", "Operation Totalize",
              "Operation Crusader", "Second Battle of El Alamein", "Battle of Hannut", "Siege of Bastogne"]
TANK_SEEDS_SOVIET = ["Battle of Raseiniai", "Battle of Prokhorovka", "Zinovy Kolobanov", "Dmitry Lavrinenko"]
FONT_B = pathlib.Path(S.FONTS_DIR) / "DejaVuSans-Bold.ttf"
COLORIZE = env("COLORIZE", "0") == "1"                 # v1.95 (Andrii, Oct 26): cancelled; 1 = b/w photos -> colour (DDColor)
MUSIC_J = pathlib.Path("music/jurgen")                 # dark ambient drones for this format (no melodies)
MUSIC_J_VOL = float(S.env("J_MUSIC_VOL", "0.35"))     # v2.02 (Andrii, Oct 27): half its old level (0.5); v2.05
                                                       # (Andrii, Oct 27, Goebbels test: 'too harsh and loud'): 30% less
# v2.04 (Andrii, Oct 27: ~40% of the viewers leave in the first 15 s): a story file can carry archive film like a
# PASTRAK story ("films" + film "shots"); in the style "film" its clips open the video with cuts of 2-3 s and their
# sound effects, the music starting only after them, and stand in for pictures further on. A/B: the film-equipped
# stories alternate film / photo (stats field j_style); J_STYLE=film|photo forces one.
STYLE = env("J_STYLE", "")
FILM_SHOT = 3.0                                        # a story film shot when a picture follows in its sentence
BAND = (300, 760)                                      # y and height of the film band (pastrak's), at 1080x1920
# the colourised-archive look: natural colours, a touch of contrast, soft vignette, light moving grain
GRADE = "eq=contrast=1.06:brightness=-0.015:saturation=1.04,vignette=angle=PI/5" + ("" if FAST else ",noise=alls=5:allf=t+u")
CARD_RE = re.compile(r"document|letter|telegram|order|poster|cover|newspaper|manuscript|certificate|leaflet|"
                     r"page|signature|instrument of surrender|stamp|banknote|diagram|plan|drawing|map", re.I)
SEEDS = [   # stories of the kind that reach millions on that channel (exact English Wikipedia titles)
    "German submarine U-977", "German submarine U-234", "German submarine U-1206", "German submarine U-570",
    "German submarine U-864", "German aircraft carrier Graf Zeppelin", "German battleship Scharnhorst",
    "Battle of the North Cape", "HMS Barham (04)", "Rochus Misch", "Otto Carius", "Dmitry Karbyshev",
    "Operation Sunrise (World War II)", "Lady Be Good (aircraft)", "SS Cap Arcona", "Sinking of the Wilhelm Gustloff",
    "German battleship Tirpitz", "Operation Source", "Japanese battleship Musashi", "USS Indianapolis (CA-35)",
    "HMS Glorious", "Operation Deadlight", "German submarine U-505", "Operation Gunnerside", "Battle for Castle Itter",
    "Ghost Army", "Operation Mincemeat", "Hiroo Onoda", "Tsutomu Yamaguchi", "Operation Bernhard",
    "German cruiser Admiral Graf Spee", "Laconia incident", "Japanese aircraft carrier Shinano", "Battle off Samar",
    "Operation Ten-Go", "I-400-class submarine", "Typhoon Cobra", "MV Struma", "Operation Chastise",
    "Battle of the Denmark Strait", "Operation Frankton", "Kamikaze", "Operation Pastorius", "Wojtek (bear)",
    "Juan Pujol García", "Operation Greif", "Operation Eiche", "German submarine U-1105",
    # what happened after: the channel's biggest hits (told neutrally, from the trial records and memoirs)
    "Nuremberg trials", "Führerbunker", "Flensburg Government", "Operation Paperclip", "Operation Regenbogen (U-boat)",
    "German Instrument of Surrender", "20 July plot", "Wilhelm Gustloff", "Erich Topp", "Hans Langsdorff",
    # Andrii, Oct 22 (the Jurgens hits): last moments, executions, fates after the war, insiders, the German side
    "Eddie Slovik", "Josef Jakobs", "Martin Bormann", "Erwin Rommel", "Wilhelm Canaris", "Joachim Peiper",
    "Erich Hartmann", "Shoichi Yokoi", "Teruo Nakamura", "Heinz Linge", "Otto Günsche", "Traudl Junge",
    "Hanna Reitsch", "Death of Adolf Hitler", "Heinrich Himmler", "Wilhelm Keitel", "Alfred Jodl",
]


# ---- topic ----------------------------------------------------------------------------------------------
def pick_topic():
    """A long Wikipedia article (enough facts for 3 minutes) with a gripping, little-known story; one Gemini call
    picks the story and how to tell it (one story or 3-4 escalating cases from the same article)."""
    S.set_category(env("CATEGORY") if env("CATEGORY") in CATS else
                   random.choices(CATS, weights=[CAT_W[c] for c in CATS])[0])
    if S.CATEGORY == "tanks":                          # western tank stories first, Soviet ones after them
        west = [t for t in TANK_SEEDS if not S.is_used(t)]
        east = [t for t in TANK_SEEDS_SOVIET if not S.is_used(t)]
        random.shuffle(west)
        random.shuffle(east)
        pool = west + east
    else:
        pool = [t for t in SEEDS if not S.is_used(t)]
        random.shuffle(pool)
    try:
        pool = pool[:10] + S.candidates(limit=20)
    except Exception as e:
        print("candidates skipped:", type(e).__name__)
    good, photos = [], {}
    for i in range(0, min(len(pool), 30), 6):
        new = [got for got in pmap(S.wiki_text, pool[i:i + 6]) if got[0] and len(got[1]) >= 7000 and S.usable(got)
               and all(g[0] != got[0] for g in good)]
        good += new
        photos.update(zip([t for t, _ in new], pmap(picture_supply, [t for t, _ in new])))
        # Andrii, Oct 18 (Shinano): the same few pictures over and over lose people. 3 minutes need a dozen big ones
        if sum(photos[t] >= PIC_MIN for t, _ in good) >= 4:
            break
    print("topic photos:", photos)
    rich = [g for g in good if photos[g[0]] >= PIC_MIN]
    if not rich:
        raise SystemExit(f"no topic with {PIC_MIN}+ big free pictures: {photos}")
    good = sorted(rich, key=lambda g: -photos[g[0]])[:6]
    lst = "\n\n".join(f"[{i}] {t} ({photos[t]} free photos)\n{x[:1500]}" for i, (t, x) in enumerate(good))
    ask = ("You pick stories for a World War II history Shorts channel whose ~3-minute narrated Shorts get millions "
           "of views (titles like 'The Last Words of the Nazis Before They Were Executed' 16M, 'What Did Hitler's "
           "Bodyguard Reveal After the War?' 8.5M, 'The U-Boat That Escaped to Argentina' 7.1M, 'The German General "
           "Who Refused to Save Himself' 3.6M). Viewers love: last words and final moments (executions, last stands), "
           "the fate of a person or ship AFTER the war, secrets told by insiders, the person who did the unthinkable, "
           "the only or the first time something happened, often seen from the German side; also a strange fate, an "
           "escape, a decision that doomed or saved a crew. The story "
           "must hold people for 3 minutes: real PEOPLE making DECISIONS under pressure, a question the viewer wants "
           "answered (a mystery, a secret cargo, a chase, a choice between bad options) and a payoff at the end. "
           "Avoid stories that are mostly technical details (armour, bulkheads, tonnage, machinery failures) or a "
           "list of events without a person to follow. More free photos = better (3 minutes need many different "
           "pictures). From these Wikipedia subjects pick the ONE that makes the most gripping TRUE 3-minute story. "
           "structure: 'story' (one story told in order) or 'countdown' (3-4 separate strange "
           "cases from the same text, each stranger than the last).\n"
           "openings: the 1-3 of these opening styles the story can HONESTLY carry, best first: "
           + "; ".join(f"'{k}' = {v[0]}" for k, v in J_HOOKS.items()) + ".\n"
           f"Candidates:\n{lst}\nReturn JSON: {{\"pick\": number, \"angle\": \"one sentence: the story to tell, only "
           "facts of that article\", \"structure\": \"story\", \"openings\": [\"fate\"]}}")
    pick, angle, structure, fits = 0, "", "story", []
    try:
        d = gemini(ask, lambda d: isinstance(d, dict) and str(d.get("pick", "")).isdigit()
                   and int(d["pick"]) < len(good), rounds=2, purpose="topic")
        pick, angle = int(d["pick"]), str(d.get("angle", ""))[:400]
        structure = "countdown" if d.get("structure") == "countdown" else "story"
        fits = [str(o) for o in d.get("openings") or [] if str(o) in J_HOOKS]
    except (SystemExit, KeyError, ValueError, TypeError):
        pick = max(range(len(good)), key=lambda i: S.VIEWS.get(good[i][0], 0))
    best = good[pick]
    print("topic:", best[0], "| text:", len(best[1]), "chars | structure:", structure, "| openings:", fits,
          "| angle:", angle or "-")
    return {**S.topic_of([best]), "angle": angle, "structure": structure, "fits": fits}


def picture_supply(title):
    """How many different big free pictures a topic has: the article's own images plus the subject's Commons
    category, only files at least MIN_SIDE+100 px on the short side (no maps, drawings or logos)."""
    names = set()
    try:
        imgs = S.wiki_get(action="parse", page=title, prop="images").get("parse", {}).get("images", [])
        imgs = [n for n in imgs if n.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff"))
                and not S.SKIP_IMG.search(n) and not re.search(r"map|drawing|plan|diagram|logo|flag|insignia", n, re.I)]
        pages = S.wiki_get(action="query", prop="imageinfo", iiprop="size", titles="|".join(
            "File:" + n for n in imgs[:50]))["query"]["pages"] if imgs else []
        names |= {p["title"] for p in pages if min((p.get("imageinfo") or [{}])[0].get("width", 0),
                                                   (p.get("imageinfo") or [{}])[0].get("height", 0)) >= MIN_SIDE + 100}
    except Exception:
        pass
    cat = commons_category(title)
    if cat:
        names |= {"File:" + n for n, _, _ in commons_files({"generator": "categorymembers", "gcmtitle": "Category:"
                                                            + cat, "gcmtype": "file", "gcmlimit": 60}, 40,
                                                           min_side=MIN_SIDE + 100)
                  if not WRONG_ERA.search(n) and not re.search(r"map|drawing|plan|diagram|model", n, re.I)}
    return len(names)


# ---- hooks: the 6 openings of the Jurgens channel (Andrii, Oct 22) -----------------------------------------
# All 94 Shorts of @jurgens16 (Oct 22: median 684k views, top 16M): sentence 1 is the TITLE read aloud word for word,
# ONE subject and ONE promise a viewer gets without thinking; sentence 2 opens the scene at once (date, place,
# person). Their weakest (128-170k) opened with an unknown name, an abstract label or a line that needs context.
# Our Indianapolis (25k) had the same kind of title; its spoken hook was a chain ("the captain of the ship that
# delivered the atomic bomb...") and 20% left in the first 7 s.
J_HOOKS = {
    "last_words": ("LAST WORDS / FINAL MOMENTS: the last words, last hours, last photograph or last stand of the "
                   "people of the story",
                   "'These were the last words of some of the Nazis convicted at Nuremberg.' (16M views), 'The final "
                   "moments of Ion Antonescu.'"),
    "fate": ("WHAT HAPPENED / WHAT DID X REVEAL: the fate of a person, ship or secret after the events, or what an "
             "insider told later",
             "'What did Adolf Hitler's bodyguard reveal after the war?' (8.5M), 'What happened to the German U-boats "
             "after the Second World War?' (7.8M)"),
    "the_x_who": ("THE X WHO / THAT Y: the person or thing named by the paradox of the story",
                  "'The U-boat that escaped to Argentina.' (7.1M), 'The German general who refused to save himself.' "
                  "(3.6M)"),
    "only_first": ("THE ONLY / THE FIRST / THE STRANGEST: a record the SOURCE states in so many words",
                   "'The only secret recording of Hitler's normal speaking voice.' (1.8M), 'The first German officer "
                   "executed by the Western Allies.' (2.2M)"),
    "photo": ("THE PHOTO: the video opens on one famous archive photograph of the person and sentence 1 points at "
              "it (only if the SOURCE describes that very photograph)",
              "'The man you see in this photo will be shot in about 10 minutes.' (1.6M), 'Who is this woman, and why "
              "has her image become one of the mysteries of the war?' (1.3M)"),
    "scene": ("DATED SCENE: the date first, then the person and what they do at the decisive moment, present tense",
              "'June 1946. Ion Antonescu walks towards his place of execution at Jilava Prison.' (1.3M)"),
}
HOOK_PRIOR = {"last_words": 3.0, "fate": 3.0, "the_x_who": 3.0, "only_first": 2.2, "scene": 1.6, "photo": 1.0}
DATE_RE = re.compile(r"\b(1[89]\d\d|January|February|March|April|May|June|July|August|September|October|November|"
                     r"December|spring|summer|autumn|winter)\b")
SMALL_WORDS = {"a", "an", "the", "of", "to", "in", "on", "at", "for", "and", "but", "or", "nor", "by", "from", "with",
               "as", "vs", "after"}


def title_case(text):
    """Sentence 1 as the title, like the originals: 'The U-Boat That Escaped to Argentina'."""
    out = []
    for k, w in enumerate(plain(text).strip().rstrip(".").split()):
        out.append(w.lower() if k and w.lower() in SMALL_WORDS else
                   "-".join(p[:1].upper() + p[1:] for p in w.split("-")))
    return " ".join(out)


def j_stats(stats):
    """Only this format's videos, for learning (the classic Shorts follow other rules)."""
    return {"videos": [v for v in stats.get("videos", []) if v.get("format") == "jurgen"],
            "metrics": stats.get("metrics", {})}


def pick_hook(stats, fits=None):
    """One of the 6 openings: those the story can carry (the topic pick names them), weighted by the originals'
    views x what this format's own videos taught (S.learned), the last video's opening less often."""
    forced = (env("HOOK") or "").strip().lower()
    if forced in J_HOOKS:
        return forced
    opts = [h for h in fits or [] if h in J_HOOKS] or [h for h in J_HOOKS if h != "photo"]
    mult = S.learned(stats, "j_hook", list(J_HOOKS), fmt="jurgen") or {}
    last = [v.get("j_hook") for v in j_stats(stats)["videos"][-1:]]
    return random.choices(opts, weights=[HOOK_PRIOR[h] * mult.get(h, 1.0) * (0.5 if h in last and len(opts) > 1
                                                                             else 1.0) for h in opts])[0]


def hook_rules(topic):
    hook = topic.get("hook") if topic.get("hook") in J_HOOKS else "the_x_who"
    name, examples = J_HOOKS[hook]
    return (f"- OPENING of this video (the Jurgens channel's, 1-16 million views): {name}. Examples: {examples}\n"
            "- First write 8 options of sentence 1 in 'hooks', all in this opening style, then use the clearest.\n"
            "- Sentence 1 = THE TITLE, read aloud word for word: 7-14 words, max 74 characters. ONE subject and ONE "
            "promise a viewer understands in a second without thinking: no chain of facts ('the captain of the ship "
            "that delivered the bomb...'), no name viewers do not know (a name only if it is famous: Hitler, Rommel, "
            "the Bismarck, USS Indianapolis; otherwise 'a German general', 'a U-boat'), no abstract label. Never 'Did "
            "you know', 'In World War II', 'Imagine', 'Have you ever', 'This is'. Wrap its single key word in "
            "[r]...[/r] (the only marker in the script).\n"
            "- Sentence 2 opens the scene at once: the date, the place and the person ('On the night of 16 October "
            "1946, in the gymnasium of Nuremberg Prison, ten of the main leaders of the Third Reich...'); never "
            "background or an explanation of what something was."
            + (" Sentence 1 already has the date here: sentence 2 goes on inside the scene." if hook == "scene" else "")
            + "\n"
            "- OPEN LOOP: within the first 4 sentences promise something true the viewer only gets at the end "
            "(e.g. 'and only one of the two passengers would ever see Japan's answer').\n"
            "- RE-HOOKS: a 3-minute Short loses viewers every few seconds; about every 5-6 sentences (~30 seconds) "
            "one sentence opens a NEW question with a twist the viewer did not expect: 'But...', 'Then...', "
            "'Until...', 'What nobody knew...', 'Stranger still...'. At least 4, spread over the whole script.\n"
            "- DELIVER THE PROMISE: every sentence moves toward what sentence 1 promised; the second-to-last sentence "
            "is the peak (the most surprising fact); the LAST sentence is a quiet closing fact: what became of the "
            "person or thing (when and how they died and at what age, the sentence they got, where it lies today), "
            "e.g. 'He died in September 2013, at the age of 96.'\n"
            "- Information gain: skip the most repeated fact about this subject; connect 2-3 facts of the source into "
            "one insight it never states in a single sentence.\n"
            "- title: sentence 1 word for word in Title Case, without the final period, no hashtags.\n"
            "- question: shown in big letters for the last 2 seconds and pinned as the first comment: a short opinion "
            "question about the story that people answer in the comments, max 6 words, e.g. 'Was he a scapegoat?', "
            "'Hero or traitor?', 'Justice or revenge?'.\n"
            + (f"- These openings got the MOST views on this channel; learn what makes them work, do not copy them: "
               f"{S.WINNERS}\n" if S.WINNERS else "")
            + (f"- These got the FEWEST views; avoid their style: {S.LOSERS}\n" if S.LOSERS else ""))


# ---- script ---------------------------------------------------------------------------------------------
JSON_FMT = ('{"hooks": ["8 different hook options"], "title": "...", "sentences": ["...", "..."], '
            '"summary": "...", "question": "...", '
            '"visuals": [{"sentence": 2, "search": "Germaniawerft Kiel"}], '
            '"labels": [{"sentence": 1, "text": "U-1206 · APRIL 1945"}], '
            '"people": [{"sentence": 4, "title": "Wilhelm Keitel", "name": "WILHELM KEITEL"}], '
            '"scenes": [{"sentence": 3, "prompt": "..."}], '
            '"map": {"places": [{"title": "Bergen", "label": "BERGEN"}, {"title": "Fedje", "label": "FEDJE"}], '
            '"routes": [{"from": 1, "to": 2, "side": "axis", "label": "U-864", "line": 12}]}, '
            '"related": ["..."], "image_queries": ["..."], "countries": ["..."], "hashtag": "germany", '
            '"music": ["dark", "mysterious"], "pronounce": {"Name": "Respelling"}, "tags": ["12-20 search tags"]}')


def rules(topic):
    form = ("COUNTDOWN: 3-4 separate cases from the text, each introduced as stranger than the last ('Without a "
            "doubt, the best known...', 'Stranger still was...', 'Even stranger was...', 'Yet none is stranger than "
            "...'); every case has its date, place, the commander's name and what exactly happened."
            if topic.get("structure") == "countdown" else
            "STORY: one story told in order, in 4-6 beats, each beat a new turn ('But...', 'Then...', 'Even "
            "so...'); follow the PEOPLE: who decided what, what was at stake, what they did not know yet.")
    return (f"- Length: {WORDS_AIM} words in {SENTS} sentences (about {SPOKEN} read aloud by a calm narrator).\n"
            + LESSONS[0] +
            f"- Form: {form}\n"
            + hook_rules(topic) +
            "- No preamble, no 'in this video', no greeting, no call to action.\n"
            "- Keep them watching (Andrii, Oct 18: a script full of technical detail lost people): tell it through "
            "people and their decisions; every sentence moves the story forward or raises a question the viewer wants "
            "answered. Technical details only when they decide the outcome, in plain words ('the doors that should "
            "have kept the sea out had never been fitted'), never lists of machinery, armour or tonnage. At most 1 "
            "number or date per sentence and about 10 in the whole script: only the ones that matter.\n"
            "- Voice: a calm, precise documentary narrator, past tense, plain English, flowing sentences of 12-30 "
            "words. Exact names, ranks and places. Say where a fact comes from when the text does "
            "('According to the report of her commander, ...', 'According to the survivors, ...', 'In his 2008 "
            "memoir, ...'). Quote people only with words that are in the SOURCE, in quotation marks.\n"
            "- One picture per sentence: write so each sentence shows one thing (a person, a ship, a place, a "
            "document, a moment).\n"
            "- Use ONLY facts in the SOURCE. Nothing invented: no dialogue, thoughts or weather the text does not "
            "give. Credit teams and units, not one man, unless the text does.\n"
            "- The last sentence is a quiet closing fact: the fate of the people or the thing (e.g. 'He died in "
            "September 2013, at the age of 96.'). No moral, no summary, no question to the viewer (the question is "
            "shown on screen), no call to action, no sponsor.\n"
            "- Neutral, educational tone; never glorify any regime; losses as numbers, never graphic.\n"
            "- SOUND HUMAN: no 'not X, but Y', no lists of three for rhythm, no inflated significance ('changed "
            "history forever', 'a testament to', 'pivotal'), no words like delve, tapestry, crucial, remarkable, "
            "unwavering, game-changer, showcase, underscore.\n"
            "- Numbers as digits (1,800), years as digits. Spell out abbreviations once (Royal Air Force).\n"

            "- summary: 2 short paragraphs (4-6 sentences) for the description, like a museum caption: the key names, "
            "dates, places and numbers of the story (the search text).\n"
            
            "- labels: 4-8 small on-screen tags in CAPITALS (max 26 characters), each on the sentence (1 = the first "
            "sentence) where a boat, ship, unit or place first appears with its date, e.g. 'U-1206 · APRIL 1945', "
            "'FEDJE, NORWAY'. Only names and dates of the SOURCE.\n"
            "- people: every person the story introduces (max 8): the sentence where they first appear, their exact "
            "English Wikipedia title, and the name in CAPITALS as it should appear on screen (max 24 characters). Their "
            "portrait is shown on that sentence with the name in big letters, like a documentary.\n"
            "- scenes: 3-6 cinematic illustrations for sentences no archive photo can show (inside a submarine, an "
            "officer at the periscope, a ship sinking at night, survivors in the water at dawn). Each prompt: "
            "English, 1940s, anonymous people described by role and uniform (never a real person's name), no flags, "
            "insignia, swastikas, text or logos, no blood or bodies.\n"
            "- map: if the story moves between places: 2-4 places (exact English Wikipedia titles of a port, island, "
            "city, cape or base with coordinates; never a whole sea or country), label in CAPITALS; routes 0-2 "
            "('from'/'to' are place numbers from 1, 'side' axis/allied/other, label max 3 words, 'line' = the "
            "sentence number where the move is told). Otherwise null.\n"
            "- visuals: for EVERY sentence the Wikimedia Commons search that finds a real photo of exactly what it "
            "shows: the boat's or ship's designation ('U-234', 'USS Sutton DE-771'), the person's full name, the "
            "place with the year ('Portsmouth Navy Yard 1945'), the object ('Enigma U-Boot', 'Messerschmitt Me 262'). "
            "German subjects: also German words ('U-Boot', 'Werft'), the Bundesarchiv has most photos.\n"
            "- image_queries: 6-10 Wikimedia Commons searches for archive photos of the people, ships, places and "
            "events of the story (with '1944', 'World War II' or the ship's name). related: 2-5 exact Wikipedia "
            "titles of the other people, ships or operations in the story. hashtag: one lowercase country word "
            "(germany, usa, uk, japan, russia, italy, poland, france). music: 2-4 of dark, mysterious, tense, "
            "suspense, sad, ambient, cinematic. pronounce: every non-English name or word in the sentences (German, "
            "Japanese, Russian...) -> how an English voice should say it: lowercase syllables joined by hyphens, NO "
            "capitals (capitals are read letter by letter), e.g. Fehler: fay-ler, Tomonaga: toh-moh-nah-gah, "
            "Kriegsmarine: kreegs-mah-ree-nuh.\n")


def draft_prompt(topic):
    return ("You write ~3-minute narrated YouTube Shorts for a World War II history channel in the style of the "
            f'Jurgens channel. Write one about "{topic["articles"][0]}".\n'
            f"SOURCE, the only allowed facts:\n<<<\n{topic['text']}\n>>>\n"
            + (f"The story to tell (only as far as the SOURCE supports it): {topic['angle']}\n" if topic.get("angle")
               else "")
            + f"Rules:\n{rules(topic)}Return JSON: {JSON_FMT}")


def editor_prompt(topic, draft, issues):
    return ("You are the editor and fact-checker of a World War II history channel. Make this ~3-minute narration "
            "as gripping and as accurate as possible and return the final version.\n"
            f"SOURCE, the only allowed facts:\n<<<\n{topic['text']}\n>>>\nRules:\n{rules(topic)}"
            f"DRAFT:\n{json.dumps(draft, ensure_ascii=False)}\n"
            + ("PROBLEMS FOUND BY THE CHECKER, fix every one:\n- " + "\n- ".join(issues) + "\n" if issues else "")
            + "Checklist: 1) every name, number, date and claim is in the SOURCE; fix or delete anything else. "
            "2) Sentence 1 (= the title) is the clearest of the 'hooks' and follows the opening rules; sentence 2 opens "
            "the scene (date, place, person); the open loop pays off; a re-hook about every 5-6 sentences; the peak "
            "just before the last sentence; the last sentence is a quiet closing fact. 3) It reads aloud naturally at a calm pace. 4) The word count. 5) Labels, scenes and "
            "map match the sentences they point at. 6) Read it as a World War II historian would and fix what they "
            f"would call wrong or misleading.\nReturn JSON with the same keys: {JSON_FMT[:-1]}, "
            '"claims": [{"claim": "each factual claim in the sentences", "supported": true}]}')


def sentences(d):
    return [plain(s) for s in (d.get("sentences") or []) if isinstance(s, str) and plain(s)]


def check(d, topic):
    """Hard problems block the upload; soft ones go back to the editor."""
    ss = sentences(d) if isinstance(d, dict) else []
    if len(ss) < 12:
        return ["fewer than 12 sentences"], []
    hard, soft = [], []
    text = " ".join(ss)
    for num in S.numbers_ok(text, topic["text"]):
        hard.append(f"the number {num} is not in the source: fix or remove it")
    for name in S.names_ok(text, topic["text"]):
        hard.append(f"the name '{name}' is not in the source: fix or remove it")
    for c in d.get("claims") or []:
        if isinstance(c, dict) and c.get("supported") is False:
            hard.append(f"unsupported claim, fix or remove: {str(c.get('claim', ''))[:120]}")
    for m in set(x.lower() for x in S.OVERCLAIM.findall(text)):
        if m not in topic["text"].lower():
            hard.append(f"'{m}' overstates it: credit the team or the unit the text names")
    n = len(text.split())
    if not WORDS_LO <= n <= WORDS_HI:
        soft.append(f"the sentences have {n} words; write {WORDS_AIM}")
    hook = ss[0]
    if len(hook.split()) > 16 or len(hook) > 76:
        soft.append("sentence 1 is also the title: max 14 words and 74 characters, one subject and one promise")
    if topic.get("hook") != "scene" and len(ss) > 1 and not DATE_RE.search(ss[1]):
        soft.append("sentence 2 must open the scene with its date and place ('On the night of 16 October 1946, in "
                    "the gymnasium of Nuremberg Prison, ...'), not background")
    if re.match(r"(did you know|in world war|during world war|imagine|have you ever|this is|the story of)\b",
                hook.lower()):
        soft.append("the hook starts with a banned opener (Did you know / In World War II / Imagine / This is)")
    subj = [w.lower() for w in S.key_words(topic)]
    if subj and hook.split()[0].strip(",.:").lower() in subj and len(hook.split()) > 1 and \
            hook.split()[1].lower() in ("was", "is", "had", "carried", "became"):
        soft.append("the hook starts with the plain name of the subject; open with the gap or the paradox")
    raw0 = str((d.get("sentences") or [""])[0])
    if "[r]" not in raw0:
        soft.append("wrap the key word of sentence 1 in [r]...[/r]")
    rehook = re.compile(r"^(but|then|until|yet|even so|stranger|what nobody|nobody|however|instead|only then|"
                        r"and then|still|that was when|this was when)\b", re.I)
    thirds = [ss[k * len(ss) // 3:(k + 1) * len(ss) // 3] for k in range(3)]
    if sum(bool(rehook.match(x)) for x in ss[2:]) < 4 or not all(any(rehook.match(x) for x in t) for t in thirds):
        soft.append("add re-hooks: at least 4 sentences, spread over the whole script, that open a new question "
                    "('But...', 'Then...', 'Until...', 'What nobody knew...')")
    if topic.get("hook") == "coldopen" and not S.JUMP_RE.match(ss[1]):
        soft.append("cold open: sentence 2 must start with the time jump back, e.g. 'Five weeks earlier,'")
    nums = [len(re.findall(r"\b\d[\d,.:]*\b", x)) for x in ss]
    if sum(nums) > 14 or sum(n > 2 for n in nums) > 1:
        soft.append(f"too many numbers ({sum(nums)}): keep about 10 that matter, at most 1-2 per sentence; tell "
                    "the story through people and decisions, not figures")
    long = [s for s in ss if len(s.split()) > 40]
    if long:
        soft.append(f"split these sentences, they are too long to read aloud: {[x[:60] for x in long[:2]]}")
    if not re.search(r"[.!]['\"]?$", ss[-1]):
        soft.append("the last sentence must be a complete statement ending with a period")
    if re.search(r"\b(in conclusion|overall|this shows|in summary|to summarize|this proves|all in all)\b",
                 ss[-1].lower()):
        soft.append("the last sentence sounds like a summary; end on the most remarkable fact")
    tells = sorted(set(re.findall(r"\b(delve|tapestry|testament|pivotal|crucial|remarkable|unwavering|game.changer|"
                                  r"showcas\w*|underscor\w*|changed history forever|stands as|in the annals)\b",
                                  text.lower())))
    if tells:
        soft.append(f"these sound machine-written, say it plainly: {tells[:4]}")
    if re.search(r"\b(subscribe|like and|follow for|comment below|in this video|sponsor)\b", text.lower()):
        soft.append("no calls to action or 'in this video' in the narration")
    films = d.get("films") or {}
    for sh in d.get("shots") or []:                    # v2.04: the story's own film shots
        if not sh.get("film"):
            continue
        if sh["film"] not in films or not films[sh["film"]].get("url"):
            hard.append(f"a shot of an unknown film: {sh['film']}")
        elif not (str(sh.get("sentence", "")).isdigit() and 1 <= int(sh["sentence"]) <= len(ss)):
            hard.append(f"a film shot without a sentence of the story: {sh.get('sentence')}")
        elif float(sh.get("to", 0)) - float(sh.get("from", 0)) < 1.0:
            hard.append(f"film shot {sh['film']} {sh.get('from')}-{sh.get('to')}: under 1 s of film")
        elif topic.get("hook") == "photo" and int(sh["sentence"]) == 1:
            hard.append("the 'photo' opening needs its photo on sentence 1, not film")
    q = plain(d.get("question", ""))
    if not q.endswith("?") or len(q.split()) > 7:
        soft.append("question: a short opinion question about the story, max 6 words, ending with '?' "
                    "(e.g. 'Was he a scapegoat?')")
    return hard, soft


def write_script(topic):
    """Draft -> editor rounds with the code checks; a script with hard problems is never used."""
    ok = lambda d: isinstance(d, dict) and len(sentences(d)) >= 12
    best, best_cost, d = None, 1e9, None
    try:
        d, issues = gemini(draft_prompt(topic), ok, purpose="script draft"), []
        for rnd in range(3):
            d = gemini(editor_prompt(topic, d, issues), ok, rounds=5, purpose="script editor")
            hard, soft = check(d, topic)
            print("script check:", len(hard), "hard,", len(soft), "soft", (hard + soft)[:3])
            if len(hard) * 10 + len(soft) < best_cost:
                best, best_cost = d, len(hard) * 10 + len(soft)
            if not hard and (len(soft) <= 1 or rnd >= 1):
                break
            issues = hard + soft
    except SystemExit as e:
        if best is None:
            raise
        print(e, "-> the best version so far")
    if check(best, topic)[0]:                         # last resort: drop sentences with invented numbers
        ss = [s for s in sentences(best) if not S.numbers_ok(s, topic["text"])]
        best = {**best, "sentences": ss, "claims": []}
    hard = check(best, topic)[0]
    if hard:
        raise SystemExit("script failed the quality checks: " + "; ".join(hard))
    return finish(best, topic)


def caps(t):
    """CAPITALS without accents (HOLSNØY -> HOLSNOY), keeping the middle dot of 'U-1206 · APRIL 1945'."""
    t = unicodedata.normalize("NFKD", str(t).upper().replace("Ø", "O").replace("ß", "SS"))
    return "".join(ch for ch in t if ch == "·" or (ord(ch) < 128 and not unicodedata.combining(ch)))


def short_title(t, most=76):
    """The title within YouTube's 100 characters once ' #history #ww2 #germany' is added."""
    return t if len(t) <= most else t[:most].rsplit(" ", 1)[0]


def finish(d, topic):
    """The script in the shape shorts.py's helpers expect: headline = sentence 1, lines = the rest (line k of the
    map spec = sentence k+1); labels and scenes keyed by sentence index from 0; label numbers checked."""
    ss = sentences(d)
    idx = lambda x: int(x) - 1 if str(x).strip().isdigit() and 1 <= int(x) <= len(ss) else None
    labels = {}
    for lb in d.get("labels") or []:
        if isinstance(lb, dict) and idx(lb.get("sentence")) is not None:
            t = re.sub(r"\s+", " ", caps(plain(str(lb.get("text", ""))))).strip()[:28]
            if t and S.nums_in_source(t, topic["text"]):
                labels.setdefault(idx(lb["sentence"]), t)
    scenes = {}
    for sc in d.get("scenes") or []:
        if isinstance(sc, dict) and idx(sc.get("sentence")) is not None and str(sc.get("prompt", "")).strip():
            scenes.setdefault(idx(sc["sentence"]), str(sc["prompt"])[:400])
    people = {}
    for pp in d.get("people") or []:
        if isinstance(pp, dict) and idx(pp.get("sentence")) is not None and str(pp.get("title", "")).strip():
            name = re.sub(r"\s+", " ", caps(plain(str(pp.get("name") or pp["title"])))).strip()[:26]
            people.setdefault(idx(pp["sentence"]), {"title": str(pp["title"]).strip(), "name": name})
    m = d.get("map") if isinstance(d.get("map"), dict) else None
    if m:                                             # the map spec counts lines after the headline from 1
        for r in m.get("routes") or []:
            if isinstance(r, dict) and str(r.get("line", "")).isdigit():
                r["line"] = int(r["line"]) - 1
    raw0 = str((d.get("sentences") or [ss[0]])[0])
    out = {**d, "hook_text": raw0 if plain(raw0) == ss[0] else ss[0], "headline": ss[0], "lines": ss[1:], "labels": labels, "scenes": scenes, "people": people, "map": m,
           "title": short_title(title_case(ss[0])) or topic["articles"][0]}
    return S.map_prepare(out, topic) if m else out


# ---- AI scenes (optional) -----------------------------------------------------------------------------
STYLE = (" Looks like a colorized 1940s archive photograph: photorealistic, natural muted colours, vertical 9:16 "
         "frame, soft light, film grain. No text, no logos, no flags, no "
         "insignia, no swastikas, no blood, no bodies.")


def gemini_image(prompt, path):
    """A Gemini image model (free tier where the account has it). None if no model answers with an image."""
    for model in AI_MODELS:
        if model in S.DEAD:
            continue
        S.CALLS["ai image"] = S.CALLS.get("ai image", 0) + 1
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              params={"key": env("GEMINI_API_KEY", "")}, timeout=(15, 120),
                              json={"contents": [{"parts": [{"text": prompt}]}],
                                    "generationConfig": {"responseModalities": ["IMAGE"],
                                                         "imageConfig": {"aspectRatio": "9:16"}}})
            if not r.ok:
                print(model, r.status_code, "ai image", r.text[:120].replace("\n", " "))
                if r.status_code in (400, 403, 404) or "PerDay" in r.text or "limit: 0" in r.text:
                    S.DEAD.add(model)                 # not available on this key: skip it for the run
                continue
            for part in r.json()["candidates"][0]["content"]["parts"]:
                blob = part.get("inlineData") or part.get("inline_data")
                if blob and blob.get("data"):
                    path.write_bytes(base64.b64decode(blob["data"]))
                    return path
        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            print(model, "ai image error:", type(e).__name__)
    return None


def pollinations_image(prompt, path, seed):
    """Pollinations (free with a token from auth.pollinations.ai: no logo); skipped without a token."""
    if not POLL_TOKEN:
        return None
    try:
        r = requests.get("https://image.pollinations.ai/prompt/" + quote(prompt), timeout=(15, 150),
                         params={"width": 1080, "height": 1920, "model": "flux", "nologo": "true", "seed": seed,
                                 "private": "true"}, headers={"Authorization": f"Bearer {POLL_TOKEN}"})
        if r.ok and r.headers.get("content-type", "").startswith("image") and len(r.content) > 20000:
            path.write_bytes(r.content)
            return path
        print("pollinations:", r.status_code, r.text[:100] if not r.ok else "")
    except requests.RequestException as e:
        print("pollinations error:", type(e).__name__)
    return None


def ai_scenes(scenes):
    """{sentence: path} of the generated scenes (graphic ones are dropped by the usual image check)."""
    if AI_IMAGES == "off" or not scenes:
        return {}
    out = {}
    for k, (i, prompt) in enumerate(sorted(scenes.items())[:AI_MAX]):
        p = W / f"ai{k}.jpg"
        got = (gemini_image(prompt + STYLE, p) if AI_IMAGES in ("auto", "gemini") else None) or \
            (pollinations_image(prompt + STYLE, p, 1000 + k) if AI_IMAGES in ("auto", "pollinations") else None)
        if got:
            out[i] = got
        elif k >= 1 and not out:                      # nothing works: don't spend the run trying every scene
            break
    if out:
        v = S.check_images([(p, f"ai:{p.name}:{p.stat().st_size}", "AI scene") for p in out.values()])
        out = {i: p for i, p in out.items() if v[f"ai:{p.name}:{p.stat().st_size}"]["s"]}
    print("ai scenes:", len(out), "of", len(scenes))
    return out


# ---- voice ----------------------------------------------------------------------------------------------
def calm_pauses(path, words, keep=0.8):
    """Removes the silence before the first word and shortens pauses longer than `keep` (a documentary keeps its
    breaths, unlike the tight classic Shorts); word timings follow."""
    log = subprocess.run(["ffmpeg", "-i", str(path), "-af", "silencedetect=noise=-40dB:d=0.05", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    pairs = list(zip([float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)],
                     [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]))
    cuts = [(a + keep / 2, b - keep / 2) for a, b in pairs if b - a > keep and a > 0.01]
    if pairs and pairs[0][0] <= 0.01 and pairs[0][1] > 0.1:
        cuts.insert(0, (0.0, pairs[0][1] - 0.05))
    if not cuts:
        return words
    keep_expr, prev = [], 0.0
    for a, b in cuts:
        if a > prev:
            keep_expr.append(f"between(t,{prev:.3f},{a:.3f})")
        prev = b
    keep_expr.append(f"gte(t,{prev:.3f})")
    tmp = path.with_name("voice_calm.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-af",
                    f"aselect='{'+'.join(keep_expr)}',asetpts=N/SR/TB", str(tmp)], check=True)
    tmp.replace(path)
    shift = lambda t: t - sum(b - a for a, b in cuts if b <= t + 0.001)
    return [(w[0], max(0.0, shift(w[1])), *w[2:]) for w in words]


def deepen(path):
    """The narrator a little deeper and darker: pitch and formants down by DEEPEN at the same speed (the word
    timings stay), more chest, less hiss. Measured against the original: F0 ~91 Hz, centroid ~550 Hz."""
    if DEEPEN >= 0.999:
        return
    sr = 24000
    tmp = path.with_name("voice_deep.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-af",
                    f"aresample={sr},asetrate={sr * DEEPEN:.0f},aresample={sr},atempo={1 / DEEPEN:.5f},"
                    "equalizer=f=120:t=q:w=1:g=3,highshelf=f=3500:g=-3", "-b:a", "160k", str(tmp)], check=True)
    tmp.replace(path)


def narrate(spoken):
    """The narration, under MAX_LEN: if the natural pace runs long, the voice reads again a little faster (the TTS's
    own rate sounds natural, unlike speeding up the audio); fit_length() trims what is left."""
    path, base = W / "voice.mp3", S.TTS_RATE
    pct = int(re.sub(r"[^\d-]", "", base) or 0)
    for _ in range(3):
        words = calm_pauses(path, S.speak(spoken, path))
        dur = probe_duration(path)
        if dur <= MAX_LEN or pct >= 25:
            break
        pct = min(25, pct + math.ceil((dur / MAX_LEN - 1) * 100) + 2)
        S.TTS_RATE = f"{pct:+d}%"
        print(f"voice: {dur:.0f} s is too long -> again at rate {S.TTS_RATE}")
    S.TTS_RATE = base
    deepen(path)
    return words


def fit_length(path, words):
    """A voice over MAX_LEN is sped up a little (max 15%); longer than that the script is too long."""
    dur = probe_duration(path)
    if dur <= MAX_LEN:
        return words, dur
    k = dur / MAX_LEN
    if k > 1.15:
        raise SystemExit(f"narration is {dur:.0f} s: too long for a Short (max {MAX_LEN:.0f} s)")
    tmp = path.with_name("voice_fit.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-af", f"atempo={k:.4f}", str(tmp)],
                   check=True)
    tmp.replace(path)
    print(f"voice sped up x{k:.3f} to fit {MAX_LEN:.0f} s")
    return [(w[0], w[1] / k, *w[2:]) for w in words], probe_duration(path)


# ---- map ------------------------------------------------------------------------------------------------
SEA, LAND, COAST, INK, ROUTE = (92, 128, 130), (178, 168, 132), (120, 112, 86), (32, 34, 30), (176, 30, 26)


class Map:
    """A muted atlas map (pale land, grey-teal sea) around the story's places, with a red route drawn on."""

    def __init__(self, spec):
        from PIL import Image, ImageDraw, ImageFont
        self.Image, self.Draw, self.spec = Image, ImageDraw, spec
        ps = spec["places"]
        xs, ys = [p["lon"] for p in ps], [S.merc(p["lat"]) for p in ps]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        # degrees across: every place inside the part of the map that stays on screen after the push-in (~70%)
        span = max(max(xs) - min(xs) + 8, (max(ys) - min(ys) + 8) * 9 / 16, 8) / 0.68
        self.w, self.h = 1300, 2311                    # a bit larger than the frame: room for the slow push-in
        self.k = self.w / span
        self.l0, self.t0 = cx - span / 2, cy + self.h / self.k / 2
        img = Image.new("RGB", (self.w, self.h), SEA)
        d = ImageDraw.Draw(img)
        for (bx0, by0, bx1, by1), rings in S.land_polys():
            for sh in (-360, 0, 360):
                if bx1 + sh < self.l0 or bx0 + sh > self.l0 + span or S.merc(by1) < self.t0 - self.h / self.k \
                        or S.merc(by0) > self.t0:
                    continue
                for j, ring in enumerate(rings):
                    pts = [self.px(x + sh, y) for x, y in ring]
                    if len(pts) > 2:
                        d.polygon(pts, fill=SEA if j else LAND, outline=COAST)
        self.font = ImageFont.truetype(str(FONT_B), 40)
        for p in ps:
            x, y = self.px(p["lon"], p["lat"])
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=INK)
            tw = d.textlength(p["label"], font=self.font)
            right = x + 18 + tw < self.w * 0.86          # labels near the right edge go left of the dot
            d.text((x + 18 if right else x - 18 - tw, y - 26), p["label"], font=self.font, fill=INK)
        self.base = img

    def px(self, lon, lat):
        return (lon - self.l0) * self.k, (self.t0 - S.merc(lat)) * self.k

    def frames(self, dur, route=None, prefix="map"):
        """JPEG frames: a slow push-in; the route grows as a red line in the first 1.5 s."""
        n, out = max(1, int(round(dur * 30))), []
        pts = []
        if route:
            a, b = self.spec["places"][route["from"]], self.spec["places"][route["to"]]
            (x0, y0), (x1, y1) = self.px(a["lon"], a["lat"]), self.px(b["lon"], b["lat"])
            mx, my = (x0 + x1) / 2 - (y1 - y0) * 0.15, (y0 + y1) / 2 + (x1 - x0) * 0.15   # a gentle curve
            pts = [((1 - u) ** 2 * x0 + 2 * (1 - u) * u * mx + u * u * x1,
                    (1 - u) ** 2 * y0 + 2 * (1 - u) * u * my + u * u * y1) for u in [i / 60 for i in range(61)]]
        for f in range(n):
            img = self.base.copy()
            if pts:
                shown = pts[:max(2, int(len(pts) * min(1.0, f / 45)))]
                d = self.Draw.Draw(img)
                d.line(shown, fill=ROUTE, width=12, joint="curve")
                if route.get("label") and f >= 45:
                    lx, ly = pts[len(pts) // 2]
                    d.text((lx + 20, ly + 10), route["label"], font=self.font, fill=ROUTE)
            z = 1.0 + 0.06 * f / max(1, n - 1)          # push in 6%
            cw, ch = self.w / z * 1080 / 1300, self.h / z * 1080 / 1300
            box = ((self.w - cw) / 2, (self.h - ch) / 2, (self.w + cw) / 2, (self.h + ch) / 2)
            p = W / f"{prefix}_{f:04d}.jpg"
            img.resize(SHOT, self.Image.BILINEAR, box=box).save(p, quality=90)
            out.append(p)
        return out


# ---- pictures: portraits of the people, colourised archive -------------------------------------------------
def lead_image(title):
    """(url, credit) of the article's OWN lead picture (never another picture of the article: the Hitler article
    once gave his father's photo), None if it has none or it is not free."""
    try:
        name = S.wiki_get(action="query", prop="pageimages", piprop="name", titles=title)["query"]["pages"][0] \
            .get("pageimage")
        if not name:
            return None
        page = S.wiki_get(action="query", prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=1800,
                          titles="File:" + name)["query"]["pages"][0]
        return S.image_item(name.rsplit(".", 1)[0].replace("_", " "), (page.get("imageinfo") or [{}])[0], 200)
    except Exception:
        return None


def portraits(people):
    """{sentence: (path, credit)}: the lead picture of each person's Wikipedia article (their portrait)."""
    def one(item):
        i, p = item
        got = lead_image(p["title"])
        if not got:
            return None
        url, credit = got
        path = S.download(url, f"person{i}{pathlib.Path(url.split('?')[0]).suffix.lower() or '.jpg'}")
        return (i, path, credit) if path else None
    out = {i: (p, c) for i, p, c in filter(None, pmap(one, sorted(people.items())))}
    if out:
        v = S.check_images([(p, "person:" + c[:120], c) for p, c in out.values()])
        out = {i: (p, c) for i, (p, c) in out.items() if v["person:" + c[:120]]["s"]}
    print("portraits:", len(out), "of", len(people))
    return out


_lab, _rgb, ddcolor, is_mono, colorize = S._lab, S._rgb, S.ddcolor, S.is_mono, S.colorize   # shared (shorts.py)


def colorize_all(paths):
    """{original: colourised} for every black-and-white photo (one at a time: the model uses all CPU cores)."""
    if not COLORIZE:
        return {}
    t, out = time.time(), {}
    for p in dict.fromkeys(paths):
        if p and is_mono(p):
            out[p] = colorize(p)
    print("colorized:", sum(out[p] != p for p in out), "of", len(out), "black-and-white photos |",
          round(time.time() - t, 1), "s")
    return out


WRONG_ERA = re.compile(r"world war i\b|first world war|\bww ?1\b|\bwwi\b|(?<![-\d])(191[4-8]|19[6-9]\d|20[0-2]\d)(?![-\d])|"
                       r"memorial|monument|museum|reenact|replica", re.I)


def dhash(path):
    """256-bit difference hash: the same photo under another file name, crop or scan gives (almost) the same bits.
    (8x8 was too coarse: two different Bismarck-at-sea photos matched.)"""
    from PIL import Image
    try:
        with Image.open(path) as im:
            g = np.asarray(im.convert("L").resize((17, 16)), dtype=np.int16)
        return int("".join("1" if x else "0" for x in (g[:, 1:] > g[:, :-1]).flatten()), 2)
    except Exception:
        return None


def no_duplicates(photos, near=40):
    """Keeps the biggest copy of each picture (Commons often has a photo 2-3 times: IWM scan, crop, retouch).
    Tested on 312 story pictures (Oct 22): a 3% crop of the same photo differs by 34 bits, different photos by 48+."""
    kept, hashes = [], []
    for p in sorted(photos, key=lambda p: -img_size(p)[0] * img_size(p)[1]):
        h = dhash(p)
        if h is not None and any(bin(h ^ k).count("1") <= near for k in hashes):
            continue
        kept.append(p)
        hashes += [h] if h is not None else []
    if len(kept) < len(photos):
        print("near-duplicate pictures dropped:", len(photos) - len(kept))
    return [p for p in photos if p in kept]


def match_pictures(photos, clips, faces, data, topic, credit_of=None, hint_of=None):
    """One Gemini (lite) look at every candidate picture next to the numbered sentences: which sentence each one
    shows EXACTLY (the person, ship, place as it was then, document or event named there), whether it shows the
    story's main subject, and whether it is wrong for the story (modern, a memorial, a film still, unrelated,
    graphic). Portraits are checked to really be the named person. Returns
    ({sentence: [photo]}, [subject photos], {sentence: [clip]}, faces kept); unavailable = old behaviour."""
    sents = [plain(data["headline"])] + [plain(l) for l in data["lines"]]
    credit_of = credit_of or {}
    era = [p for p in photos if WRONG_ERA.search(credit_of.get(p, "").split(" (")[0])]
    if era:                                            # World War I, post-1960, memorials: never in this story
        print("pictures of the wrong era dropped:", [credit_of[p][:50] for p in era])
        photos = [p for p in photos if p not in era]
    items = [(p, "face", i) for i, (p, _) in faces.items()] + \
        [(c["frames"][1][0], "film", c) for c in clips if len(c.get("frames") or []) > 1]
    items += [(p, "photo", None) for p in photos][:max(0, 36 - len(items))]   # portraits and films always checked
    parts, kept = [], []
    for p, kind, ref in items[:36]:
        small = W / f"rel{len(kept)}.jpg"
        if subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(p), "-vf", "scale=384:-2", "-frames:v", "1",
                           str(small)]).returncode:
            continue
        cap = (credit_of.get(p, "") if kind == "photo" else ref["credit"] if kind == "film" else "").split(" (")[0]
        hint = (hint_of or {}).get(p)
        note = (f" (claimed: a portrait of {data['people'][ref]['title']})" if kind == "face" else
                f" (a frame of archive film; file: {cap[:90]})" if kind == "film" else
                f" (file: {cap[:90]}" + (f"; found searching for sentence {hint + 1}" if hint is not None else "") + ")")
        parts += [{"text": f"Image {len(kept)}{note}:"},
                  {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(small.read_bytes()).decode()}}]
        kept.append((p, kind, ref))
    n = len(kept)
    numbered = "\n".join(f"{k + 1}. {s}" for k, s in enumerate(sents))
    try:
        d = gemini(f"A documentary narrated sentence by sentence. MAIN SUBJECT: {topic['articles'][0]}.\n"
                   f"SENTENCES:\n{numbered}\n\nEach image comes with its Wikimedia file name: trust it about WHO and "
                   "WHAT it shows and WHEN it was taken.\n"
                   f"For each of the {n} numbered images (Image 0 first) return an object:\n"
                   '- "s": the number of the ONE sentence this image shows best: the very person, ship, aircraft or '
                   "vehicle it names; the city, port or place it names as it looked in the 1930s-1940s; the event it "
                   "names (a photo of that bombing, battle, sinking, surrender or trial counts); or the document it "
                   "names. 0 if it shows none of them (a different person, another ship, generic soldiers, officials or "
                   "landscapes, a group photo that is not of the people named).\n"
                   '- "subject": true if it shows the MAIN SUBJECT itself (or, for a person, that person).\n'
                   '- "bad": true if it must not appear at all: a photo taken after 1950 (modern buildings, cars, '
                   "colour digital photos), a memorial, monument or museum, a film or TV still or poster (unless a "
                   "sentence is about that film or actor), corpses, camps or atrocities (unless the story is about "
                   "them), or nothing to do with the story; a watermark, agency logo or stamped text laid over "
                   "the picture (IWM, Getty, Alamy, 'news photo', a museum or archive name); a magazine, newspaper "
                   "or book page full of text (unless a "
                   "sentence is about that very document); a surviving vehicle, gun or ship as it looks today. For an "
                   "image claimed to be a portrait of someone: bad = true unless it really is a portrait of that "
                   "person.\n"
                   '- "cover": 0-10, how strongly it would stop a scroll as the cover of the video: 9-10 = the most '
                   "massive thing of the story (a ship, tank, aircraft, gun, a burning city) at its most intense "
                   "moment (firing, burning, exploding, sinking, crashing), big and sharp in the frame; 7-8 = the "
                   "dramatic moment with people (an execution, a charge, a rescue under fire); 5-6 = one face close "
                   "up looking into the camera, or the machine standing still; 0-3 = documents, maps, text, small "
                   "figures in a wide dull scene.\n"
                   'Return JSON {"images": [{"s": 0, "subject": false, "bad": false, "cover": 5}, ...]}',
                   lambda d: isinstance(d, dict) and isinstance(d.get("images"), list) and len(d["images"]) == n,
                   rounds=2, extra=parts, purpose="match pictures",
                   models=["gemini-flash-latest", S.MODELS[0]] + S.LITE_FIRST)   # the careful model first
    except SystemExit:
        print("picture matching unavailable: the photos are used in order")
        return {}, list(photos), {-1: list(clips)}, faces
    by_sent, subject, film_at, faces_ok, notes, covers = {}, [], {}, {}, [], []
    for (p, kind, ref), r in zip(kept, d["images"]):
        r = r if isinstance(r, dict) else {}
        s = r.get("s") if isinstance(r.get("s"), int) and 1 <= r.get("s") <= len(sents) else 0
        bad, subj = r.get("bad") is True, r.get("subject") is True
        if not bad and kind != "film" and (s or subj or kind == "face") and isinstance(r.get("cover"), (int, float)):
            covers.append((r["cover"], p))
        if kind == "face":
            if not bad:
                faces_ok[ref] = faces[ref]
            else:
                notes.append(f"portrait rejected: {data['people'][ref]['title']}")
            continue
        if bad or not (s or subj):
            notes.append(f"{kind} dropped: {pathlib.Path(str(p)).name}")
            continue
        if kind == "film":
            film_at.setdefault(s - 1 if s else -1, []).append(ref)
        else:
            if s:
                by_sent.setdefault(s - 1, []).append(p)
            if subj:
                subject.append(p)
    best = max(covers, key=lambda c: c[0], default=(0, None))
    if best[0] >= 6:                                   # Andrii, Oct 25: the most massive thing at its most intense moment
        data["_cover"] = best[1]
    print("pictures matched to sentences:", sum(map(len, by_sent.values())), "| subject photos:", len(subject),
          "| films:", sum(map(len, film_at.values())), "| portraits:", len(faces_ok), "of", len(faces),
          "| dropped:", len(notes), notes[:6])
    return by_sent, subject, film_at, faces_ok


def img_size(path):
    from PIL import Image
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return (0, 0)


def free_item(name, ii):
    """(url, credit) of a Commons file with a free licence (public domain, CC0, CC BY/BY-SA), else None."""
    meta = ii.get("extmetadata", {})
    lic = meta.get("LicenseShortName", {}).get("value", "")
    url = ii.get("thumburl") or ii.get("url")
    if not url or not re.search(r"public domain|^pd|cc0|cc[ -]by", lic, re.I):
        return None
    artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()[:60]
    return url, (f"{name.rsplit('.', 1)[0].replace('_', ' ')[:60]} ({artist + ', ' if artist else ''}{lic}) "
                 f"{ii.get('descriptionurl', '')}").strip()


def commons_files(params, limit, min_side=400):
    """Free bitmap files of a Commons query (a category or a search): [(file name, url, credit)]."""
    try:
        r = requests.get(S.COMMONS, headers=S.UA, timeout=60, params={
            "action": "query", "format": "json", "formatversion": 2, **params, "prop": "imageinfo",
            "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 1280}).json()
    except Exception:
        return []
    out = []
    for p in sorted(r.get("query", {}).get("pages", []), key=lambda p: p.get("index", 0)):
        ii = (p.get("imageinfo") or [{}])[0]
        if not str(ii.get("mime", "")).startswith("image/") or "svg" in str(ii.get("mime", "")) \
                or min(ii.get("width", 0), ii.get("height", 0)) < min_side:
            continue
        item = free_item(p["title"][5:], ii)
        if item:
            out.append((p["title"][5:], *item))
        if len(out) >= limit:
            break
    return out


def commons_category(title):
    """The subject's own Wikimedia Commons category (Wikidata P373), e.g. 'U-234 (submarine, 1943)'."""
    try:
        q = S.wiki_get(action="query", prop="pageprops", ppprop="wikibase_item", titles=title)["query"]["pages"][0] \
            .get("pageprops", {}).get("wikibase_item")
        d = requests.get("https://www.wikidata.org/w/api.php", headers=S.UA, timeout=30, params={
            "action": "wbgetclaims", "entity": q, "property": "P373", "format": "json"}).json() if q else {}
        return d["claims"]["P373"][0]["mainsnak"]["datavalue"]["value"]
    except Exception:
        return None


def story_candidates(data, topic):
    """How the U-234 pictures were found by hand, as code: the subject's own Commons category first (its photos are
    of the subject itself), then one Commons search per sentence for exactly what it shows ('visuals'), then the
    usual article/related images (S.get_images). -> [(path, file name, credit, sentence hint or None)]"""
    found, cat = [], commons_category(topic["articles"][0])
    if cat:
        found += [(n, u, c, None) for n, u, c in commons_files(
            {"generator": "categorymembers", "gcmtitle": "Category:" + cat, "gcmtype": "file", "gcmlimit": 50}, 24)]
    jobs = []
    for v in data.get("visuals") or []:
        if isinstance(v, dict) and str(v.get("search", "")).strip() and str(v.get("sentence", "")).isdigit():
            jobs.append((int(v["sentence"]) - 1, str(v["search"])[:80]))
    got = pmap(lambda j: [(n, u, c, j[0]) for n, u, c in commons_files(
        {"generator": "search", "gsrsearch": j[1] + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 6}, 3)], jobs)
    for g in got:
        found += g
    seen, uniq = set(), []
    for n, u, c, h in found:
        if n not in seen and not WRONG_ERA.search(n):
            seen.add(n)
            uniq.append((n, u, c, h))
    paths = pmap(lambda a: S.download(a[1][1], f"c{a[0]:02d}{pathlib.Path(a[1][0]).suffix.lower() or '.jpg'}"),
                 list(enumerate(uniq[:30])))
    out = [(p, n, c, h) for p, (n, u, c, h) in zip(paths, uniq[:30]) if p]
    print("story pictures:", len(out), "| commons category:", cat or "-", "| per-sentence searches:", len(jobs))
    return out


def manual_pictures(entries, data):
    """Hand-picked Wikimedia Commons pictures of a story file: [{"sentence": n, "file": "...", "name": "..."}] ->
    ({sentence: [photo]}, {sentence: (portrait, credit)}, credits, sentences whose own first picture arrived).
    Downloaded here (the Commons API with the bot's user agent); license and author come from Commons."""
    def one(k, e):
        if e.get("url"):                                # a picture saved by URL (not a Commons file)
            path = S.download(e["url"], f"m{k:02d}{pathlib.Path(str(e['url']).split('?')[0]).suffix.lower() or '.jpg'}")
            return (path, str(e.get("credit", ""))) if path else None
        name = str(e["file"]).replace(" ", "_")
        try:
            page = requests.get(S.COMMONS, headers=S.UA, timeout=60, params={
                "action": "query", "format": "json", "formatversion": 2, "titles": "File:" + name, "prop": "imageinfo",
                "iiprop": "url|size|extmetadata", "iiurlwidth": 1280}).json()["query"]["pages"][0]
            item = free_item(name, (page.get("imageinfo") or [{}])[0])   # chosen by hand: only the licence
        except Exception as ex:
            print("manual picture not found:", name[:60], type(ex).__name__)
            return None
        if not item:
            print("manual picture not free or missing:", name[:60])
            return None
        path = S.download(item[0], f"m{k:02d}{pathlib.Path(name).suffix.lower() or '.jpg'}")
        return (path, item[1]) if path else None
    entries = [e for e in entries if e.get("file") or e.get("url")]
    files = list(dict.fromkeys(str(e.get("file") or e.get("url")) for e in entries))   # one download per file: the same picture on
    fetched = dict(zip(files, pmap(lambda a: one(*a), list(enumerate(  # two sentences is one held shot
        ({"url": f} if f.startswith("http") else {"file": f}) for f in files)), workers=3)))
    got = [fetched[str(e.get("file") or e.get("url"))] for e in entries]
    by_sent, faces, credits, first_ok, seen = {}, {}, [], set(), set()
    data["_credit_of"] = {str(g[0]): g[1] for g in got if g}
    data["_file_path"] = {f.replace(" ", "_"): g[0] for f, g in fetched.items() if g}   # for the "thumb" picture
    for e, g in zip(entries, got):
        i = int(e["sentence"]) - 1
        if i not in seen and g:
            first_ok.add(i)
        seen.add(i)
        if not g:
            continue
        credits.append(g[1])
        if e.get("name") and i not in faces:
            faces[i] = g
            data.setdefault("people", {})[i] = {"title": e["file"], "name": caps(e["name"])}
        else:
            by_sent.setdefault(i, []).append(g[0])
    print("manual pictures:", sum(1 for g in got if g), "of", len(entries))
    return by_sent, faces, list(dict.fromkeys(credits)), first_ok


# ---- shots ----------------------------------------------------------------------------------------------
def pick_style(stats, d):
    """The v2.04 A/B: None for a story without film; else 'film' or 'photo', the other one than the last
    film-equipped jurgen video had (J_STYLE forces one)."""
    if not (d.get("films") and any(sh.get("film") for sh in d.get("shots") or [])):
        return None
    if STYLE in ("film", "photo"):
        return STYLE
    last = [v["j_style"] for v in S.videos_of(stats, "jurgen") if v.get("j_style")]
    return "photo" if last and last[-1] == "film" else "film"


def story_films(data):
    """The story's film shots -> ({sentence index: [clip]}, credits); each film downloaded once by pastrak's
    film_file (Internet Archive / Commons files; P_FILMS = local copies for a sandbox test)."""
    import pastrak as P                                # pastrak imports this module: here, not at the top
    films = data.get("films") or {}
    paths = {k: P.film_file(k, f) for k, f in films.items()
             if any(sh.get("film") == k for sh in data.get("shots") or [])}
    out, credits = {}, []
    for sh in data.get("shots") or []:
        if sh.get("film") not in paths:
            continue
        f = films[sh["film"]]
        out.setdefault(int(sh["sentence"]) - 1, []).append({
            "path": paths[sh["film"]], "ss": float(sh["from"]), "to": float(sh["to"]), "crop": f.get("crop"),
            "x": float(sh.get("x", 0.5)), "y": float(sh.get("y", 0.5)), "zoom": float(sh.get("zoom", 1.0)),
            "punch": bool(sh.get("punch")), "fill": bool(sh.get("fill")), "sfx": sh.get("sfx"),
            "credit": f.get("credit", ""), "story": True})
        credits.append(f.get("credit", ""))
    print("story film shots:", sum(len(c) for c in out.values()), "in sentences", [i + 1 for i in sorted(out)])
    return out, list(dict.fromkeys(c for c in credits if c))


def story_spans(sp, story):
    """v2.04: a sentence with film of its own opens on those clips (each up to FILM_SHOT s and its own length; the
    first shot of the video <= 2.4 s); the rest of the sentence goes to its picture, or, when less than 2.5 s would
    be left, the clips share the whole sentence."""
    out = []
    for i in dict.fromkeys(x[0] for x in sp):
        mine = [x for x in sp if x[0] == i]
        clips = story.get(i)
        if not clips:
            out += mine
            continue
        a, b = mine[0][1], mine[-1][2]
        want = [min(FILM_SHOT, max(0.5, c["to"] - c["ss"])) for c in clips]
        if a < 0.1:
            want[0] = min(want[0], 2.4)
        if b - a - sum(want) < 2.5:
            want = [w * (b - a) / sum(want) for w in want]
        t = a
        for c, w in zip(clips, want):
            out.append((i, t, t + w, c))
            t += w
        if b - t > 0.05:
            cap = 3.5 if t < 12 else SHOT_MAX
            parts = max(1, math.ceil((b - t) / cap))
            out += [(i, t + (b - t) * p / parts, t + (b - t) * (p + 1) / parts, None) for p in range(parts)]
    return out


def spans(tl, total):
    """(sentence index, start, end) of every shot: one per sentence (the originals hold a picture 3-9 s while its
    sentence is read), sentences over 9 s split, very short ones merged into the previous shot."""
    sent = [(0, 0.0, tl[0]["start"] if tl else total)] + [(i + 1, l["start"], l["end"]) for i, l in enumerate(tl)]
    out = []
    for i, a, b in sent:
        if out and b - a < 2.0:
            j, a0, _ = out[-1]
            out[-1] = (j, a0, b)
            continue
        cap = 2.2 if a < 0.1 else 3.5 if a < 12 else SHOT_MAX   # retention: fast cuts in the first 12 s
        parts = max(1, math.ceil((b - a) / cap))
        out += [(i, a + (b - a) * p / parts, a + (b - a) * (p + 1) / parts) for p in range(parts)]
    return out


def plan(tl, total, by_sent, subject, film_at, ai, data, faces, story=None):
    """What every shot shows, sentence by sentence: the person's portrait (with the name) on the sentence that
    introduces them; the map when a route is told; a picture or film matched to THAT sentence; otherwise a photo of
    the main subject, or the last matched picture held a little longer (never a random picture)."""
    sp = [(i, a, b, None) for i, a, b in spans(tl, total)]
    if story:                                          # v2.04: the story's own film (style "film")
        sp = story_spans(sp, story)
    m = data.get("map") or {}
    map_at = {}
    if m.get("places"):
        map_at = {r["line"]: k for k, r in enumerate(m.get("routes") or [])}
        if not map_at:                                 # no route: the map once, early
            map_at[min(3, len(sp) - 1)] = None
    pool = {i: list(ps) for i, ps in by_sent.items()}
    films = {i: list(cs) for i, cs in film_at.items()}
    loose_films = films.pop(-1, [])                    # films of the subject, no sentence of their own
    shots, last, since_film, used = [], None, 0, {}
    fresh = lambda p: used.get(p, 0) < 2 and p not in [x.get("src") for x in shots[-3:]]   # no picture 3 times
    for k, (i, a, b, clip) in enumerate(sp):
        dur, head = b - a, k == 0 or sp[k - 1][0] != i or sp[k - 1][3] is not None
        sh = None
        if clip:
            sh = {"kind": "film", "clip": clip, "matched": True}
        elif head and i in faces:
            sh = {"kind": "photo", "src": faces[i][0], "name": data["people"][i]["name"], "portrait": True,
                  "matched": True}
        elif head and i in map_at:
            r = map_at.pop(i)
            sh = {"kind": "map", "route": (m["routes"][r] if r is not None else None), "matched": True}
        elif films.get(i) and dur >= 2.5:
            sh = {"kind": "film", "clip": films[i].pop(0), "matched": True}
        elif pool.get(i):
            sh = {"kind": "photo", "src": pool[i].pop(0), "matched": True}
        elif not head and shots and shots[-1]["kind"] == "photo" and a < 12 \
                and shots[-1].get("zoom", 1.0) < 1.2:     # opening: ONE punch-in on the same picture, then hold
            sh = {k2: v for k2, v in shots[-1].items() if k2 in ("kind", "src", "portrait", "card", "matched")}
            sh["zoom"] = shots[-1].get("zoom", 1.0) + 0.22
        elif not head and shots and shots[-1]["kind"] in ("photo", "map"):   # no 2nd picture: hold this one
            shots[-1]["dur"] += dur
            continue
        elif AI_IMAGES != "off" and i in ai:
            sh = {"kind": "ai", "src": ai.pop(i)}
        elif loose_films and since_film >= 4 and dur >= 2.5:
            sh = {"kind": "film", "clip": loose_films.pop(0)}
        elif any(fresh(p) for p in subject):          # the least shown photo of the subject
            p = min((p for p in subject if fresh(p)), key=lambda p: used.get(p, 0))
            sh = {"kind": "photo", "src": p}
        elif shots and shots[-1]["kind"] in ("photo", "map") and shots[-1]["dur"] + dur <= 12:
            shots[-1]["dur"] += dur                     # Andrii (Shinano): no flicking back to the same few
            continue                                    # pictures: hold this one longer (up to 12 s)
        if sh is None:                                 # nothing fits: the least shown matched picture of the story
            rest = list(dict.fromkeys([p for ps in by_sent.values() for p in ps] + [f[0] for f in faces.values()]
                                      + list(subject)))
            if not rest:
                raise SystemExit("no pictures for the shots")
            sh = {"kind": "photo", "src": min(rest, key=lambda p: (not fresh(p), used.get(p, 0)))}
        if shots and sh.get("src") and sh["src"] == shots[-1].get("src") and not sh.get("name") \
                and not sh.get("zoom"):
            shots[-1]["dur"] += dur                     # the same picture again: one longer shot, no jump cut
            continue
        since_film = 0 if sh["kind"] == "film" else since_film + 1
        last = sh.get("src")
        if last and not sh.get("zoom"):
            used[last] = used.get(last, 0) + 1
        sh.update(i=i, start=a, dur=dur)
        shots.append(sh)
    return shots


def card_frame(src, k):
    """A document, poster, cover or drawing as a card on a dark, blurred copy of itself (not cropped away)."""
    from PIL import Image, ImageFilter, ImageOps
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    bg = ImageOps.fit(im, (1350, 2400), Image.BILINEAR).filter(ImageFilter.GaussianBlur(40))
    bg = Image.eval(bg, lambda v: int(v * 0.35))
    fg = ImageOps.contain(im, (1180, 1650), Image.LANCZOS)
    shadow = Image.new("L", (fg.width + 120, fg.height + 120), 0)
    shadow.paste(200, (60, 60, 60 + fg.width, 60 + fg.height))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    x, y = (1350 - fg.width) // 2, (2400 - fg.height) // 2 - 60
    bg.paste((0, 0, 0), (x - 60 + 18, y - 60 + 24), shadow)
    bg.paste(fg, (x, y))
    p = W / f"card{k:03d}.jpg"
    bg.save(p, quality=93)
    return p


def render_shot(k, sh):
    out = W / f"shot{k:03d}.mp4"
    d = max(sh["dur"], 0.1)
    enc = ["-r", "30", "-an", *(["-c:v", "libx264", "-preset", "ultrafast", "-crf", "16", "-pix_fmt", "yuv420p"]
                               if FAST else S.x264(18)), str(out)]   # FAST: re-encoded in the final render anyway
    sc = SHOT[0] / 1080
    ease = f"(1-cos(PI*min(t/{d:.3f},1)))/2"           # slow start and stop, like a hand-made move
    whip = "," + S.WHIP_VF.rstrip(",") if WHIP and k > 0 else ""
    if sh["kind"] == "film" and sh["clip"].get("story"):
        return story_film(sh["clip"], d, enc, whip)
    if sh["kind"] == "film":
        c = sh["clip"]
        crop = f"crop={c['crop']}," if c.get("crop") else ""
        vf = (f"{crop}scale={SHOT[0]}:{SHOT[1]}:force_original_aspect_ratio=increase,crop={SHOT[0]}:{SHOT[1]},"
              f"setsar=1,fps=30,{GRADE},format=yuv420p")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{c['ss']:.2f}", "-i", str(c["path"]),
                        "-t", f"{d:.3f}", "-vf", vf + whip, *enc], check=True)
        return out
    if sh["kind"] == "map":
        frames = sh["map"].frames(d, sh.get("route"), prefix=f"map{k:03d}")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", str(W / f"map{k:03d}_%04d.jpg"),
                        "-t", f"{d:.3f}", "-vf", f"setsar=1,{GRADE},format=yuv420p", *enc], check=True)
        for f in frames:
            f.unlink(missing_ok=True)
        return out
    from PIL import Image, ImageOps
    src = sh["src"]
    if sh.get("card"):
        src = card_frame(src, k)
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    w, h = im.size
    if sh.get("card") or sh.get("portrait") or sh.get("zoom") or w / h <= 0.8:
        # portraits, cards and tall pictures: a slow push-in (8%) on the centre, faces sit in the upper third
        cy = 0.38 if sh.get("portrait") else 0.5
        im = ImageOps.fit(im, (round(1350 * sc), round(2400 * sc)), Image.LANCZOS, centering=(0.5, cy))
        p = W / f"st{k:03d}.jpg"
        im.save(p, quality=93)
        z = f"({sh.get('zoom', 1.0):.2f}+0.08*{ease})"
        vf = (f"scale=w='trunc({SHOT[0]}*{z}/2)*2':h=-2:eval=frame:flags={'bilinear' if FAST else 'bicubic'},"
              f"crop={SHOT[0]}:{SHOT[1]},setsar=1,{GRADE},format=yuv420p")
    else:
        # landscapes: fill the height and pan slowly along the picture (~50 px/s)
        s = max(SHOT[1] / h, SHOT[0] * 1.1 / w)
        im = im.resize((max(SHOT[0], round(w * s)), max(SHOT[1], round(h * s))), Image.LANCZOS)
        p = W / f"st{k:03d}.jpg"
        im.save(p, quality=93)
        dx = im.width - SHOT[0]
        travel = min(dx, int(50 * sc * d))
        x0 = (dx - travel) // 2
        a, b = (x0, x0 + travel) if k % 2 else (x0 + travel, x0)
        vf = (f"crop={SHOT[0]}:{SHOT[1]}:x='{a}+({b - a})*{ease}':y={(im.height - SHOT[1]) // 2},"
              f"setsar=1,{GRADE},format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-i", str(p),
                    "-t", f"{d:.3f}", "-vf", vf + whip, *enc], check=True)
    return out


def story_film(c, d, enc, whip):
    """v2.04: a film shot of the story file, like PASTRAK's: the whole archive picture across the frame in a band on
    its own dark blurred copy ("fill": cropped to fill the frame instead; "zoom": a closer look around x, y); slowed
    (max 1.6x) or held on its last frame when the shot outlasts the clip."""
    w, h = SHOT
    avail = max(0.3, c["to"] - c["ss"])
    slow = min(1.6, d / avail) if d > avail else 1.0
    pre = f"crop={c['crop']}," if c.get("crop") else ""
    z = max(1.0, c.get("zoom", 1.0))
    if z > 1.0:
        pre += f"crop=iw/{z:.3f}:ih/{z:.3f}:(iw-iw/{z:.3f})*{c['x']:.2f}:(ih-ih/{z:.3f})*{c['y']:.2f},"
    pre += f"setpts={slow:.3f}*PTS," if slow > 1.0 else ""
    hold = f",tpad=stop_mode=clone:stop_duration={d:.2f}" if d > avail * slow else ""
    look = ("eq=contrast=1.45:brightness=-0.10:gamma=0.80," if c.get("punch") else "") + GRADE.split(",vignette")[0]
    x = c["x"] if z == 1.0 else 0.5
    if c.get("fill"):
        fc = (f"[0:v]{pre}fps=30{hold},scale={w}:{h}:force_original_aspect_ratio=increase,"
              f"crop={w}:{h}:(iw-ow)*{x:.2f}:(ih-oh)/2,setsar=1,{look},format=yuv420p{whip}[v]")
    else:
        y, bh = (round(v * w / 1080 / 2) * 2 for v in BAND)
        fc = (f"[0:v]{pre}fps=30{hold},setsar=1,split[a][b];"
              f"[a]scale=216:384:force_original_aspect_ratio=increase,crop=216:384,boxblur=10:2,scale={w}:{h},"
              f"eq=brightness=-0.20:saturation=0.7[bg];"
              f"[b]scale={w}:{bh}:force_original_aspect_ratio=increase,crop={w}:{bh}:(iw-ow)*{x:.2f}:(ih-oh)/2,"
              f"{look}[fg];[bg][fg]overlay=0:{y},format=yuv420p{whip}[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{c['ss']:.2f}", "-t", f"{avail + 0.2:.2f}",
                    "-i", str(c["path"]), "-filter_complex", fc, "-map", "[v]", "-t", f"{d:.3f}", *enc], check=True)
    return pathlib.Path(enc[-1])


# ---- text on screen ---------------------------------------------------------------------------------------
def hook_lines(text, size=74, width=900):
    """The hook in lines that fit the frame, its [r] key word in red (shorts.py's colours)."""
    words, lines, cur = S.styled_words(text), [], []
    for w, c in words:
        if cur and S.text_w(" ".join(x for x, _ in cur + [(w, c)]), size, 1) > width:
            lines.append(cur)
            cur = []
        cur.append((w, c))
    lines.append(cur)
    return "\\N".join(" ".join(f"{{\\c{c}}}{w}" for w, c in line) for line in lines)


def wrap_name(name, width=16):
    """A long name on two balanced lines ('JOACHIM\\NVON RIBBENTROP')."""
    ws = name.split()
    if len(name) <= width or len(ws) < 2:
        return name
    best = min(range(1, len(ws)), key=lambda c: abs(len(" ".join(ws[:c])) - len(" ".join(ws[c:]))))
    return " ".join(ws[:best]) + "\\N" + " ".join(ws[best:])


def build_ass(data, tl, total, shots):
    """A small title line at the top (from 0.5 s, so the first frame stays clean for the thumbnail), the name of a
    person in big white letters over their portrait (like the originals), small place/date labels."""
    starts = [0.0] + [l["start"] for l in tl]
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            "MarginL, MarginR, MarginV, Encoding\n"
            "Style: Top,DejaVu Sans,30,&H30FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,3,0,1,0,2,7,"
            "120,120,245,1\n"
            "Style: Hook,DejaVu Sans,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,1,0,1,5,3,8,"
            "90,90,330,1\n"
            "Style: Plate,DejaVu Sans,86,&H0000D7FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,4,0,1,5,3,5,"
            "60,60,0,1\n"
            "Style: Name,DejaVu Sans,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,1,0,0,0,100,100,1,0,1,2,4,5,"
            "100,100,0,1\n"
            "Style: Label,DejaVu Sans,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,4,0,1,0,3,2,"
            "120,120,500,1\n" + S.caption_style() + "\n" +
            "Style: Sub,DejaVu Sans,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,2,"
            "120,120,640,1\n"
            "Style: Ask,DejaVu Sans,100,&H0000D7FF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,1,0,1,6,3,5,"
            "80,80,0,1\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    hook_end = min(total, (tl[0]["start"] if tl else 3.0) + 0.35)
    ev = [f"Dialogue: 0,{S.ass_time(hook_end)},{S.ass_time(total - data.get('_end_q', 0))},Top,,0,0,0,,{{\\fad(400,0)}}"
          f"{S.clean(caps(plain(data['title'])))[:60]}"]
    if not CAPS:                                       # the hook in big letters from frame 0 (style C: the captions)
        ev.append(f"Dialogue: 2,{S.ass_time(0)},{S.ass_time(hook_end)},Hook,,0,0,0,,{{\\fad(0,250)}}"
                  f"{hook_lines(data.get('hook_text') or data['headline'])}")
    jump = S.JUMP_RE.match(plain(data["lines"][0])) if data.get("j_hook") == "coldopen" and data.get("lines") else None
    if jump and tl:                                    # cold open: the time jump back as a big plate
        ev.append(f"Dialogue: 2,{S.ass_time(tl[0]['start'])},{S.ass_time(min(total, tl[0]['start'] + 2.2))},Plate,,"
                  f"0,0,0,,{{\\pos(540,960)\\fscx70\\fscy70\\t(0,180,\\fscx100\\fscy100)\\fad(0,300)}}"
                  f"{S.clean(caps(jump.group(0).strip(' ,.:')))}")
    named = set()
    for sh in shots:
        if sh.get("name") and sh["i"] not in named:
            named.add(sh["i"])
            a, b = max(0.4, sh["start"] + 0.15), min(total - 0.1, sh["start"] + sh["dur"] - 0.1)
            ev.append(f"Dialogue: 1,{S.ass_time(a)},{S.ass_time(b)},Name,,0,0,0,,{{\\pos(540,1130)\\fad(300,250)}}"
                      f"{wrap_name(S.clean(sh['name']))}")
    shown = {sh["i"] for sh in shots if sh.get("matched")}   # a place/date label only over its own picture or map
    if "_label_ok" in data:                            # hand-picked: only over the picture chosen first for it
        shown = {i for i in shown if i in data["_label_ok"] or any(sh["i"] == i and sh["kind"] == "map" for sh in shots)}
    for i, text in sorted(data.get("labels", {}).items()):
        if i < len(starts) and i not in named and i in shown and not CAPS:   # style C: no place/date labels
            a = max(0.6, starts[i] + 0.2)                                      # (Andrii, Oct 25)
            b = min(total - 0.2, a + 3.6)
            ev.append(f"Dialogue: 1,{S.ass_time(a)},{S.ass_time(b)},Label,,0,0,0,,{{\\fad(250,300)}}"
                      f"{{\\c&H2B2BC8&}}—{{\\c&HFFFFFF&}} {S.clean(text)}")
    if CAPS:
        ev += S.captions_two(tl, total - data.get("_end_q", 0), S.HEAD_TL)
    elif SUBS:
        sents = [(0.0, tl[0]["start"] if tl else total, plain(data["headline"]))] + \
            [(l["start"], l["end"], plain(l["text"])) for l in tl]
        for a, b, t in sents:
            ws = t.split()
            parts = [ws[j:j + 7] for j in range(0, len(ws), 7)] or [[]]
            for j, p in enumerate(parts):
                pa, pb = a + (b - a) * j / len(parts), a + (b - a) * (j + 1) / len(parts)
                ev.append(f"Dialogue: 2,{S.ass_time(pa)},{S.ass_time(pb)},Sub,,0,0,0,,{S.clean(' '.join(p))}")
    if data.get("_end_q"):                             # Andrii, Oct 22: the voice ends on a fact, the screen asks
        a = S.ass_time(total - data["_end_q"])
        ev.append(f"Dialogue: 3,{a},{S.ass_time(total)},Ask,,0,0,0,,{{\\pos(0,0)\\an7\\bord0\\shad0\\1c&H000000&"
                  f"\\alpha&H50&\\fad(200,0)\\p1}}m 0 0 l 1080 0 1080 1920 0 1920{{\\p0}}")   # the picture dimmed
        ev.append(f"Dialogue: 4,{a},{S.ass_time(total)},Ask,,0,0,0,,"
                  f"{{\\pos(540,960)\\fscx80\\fscy80\\t(0,220,\\fscx100\\fscy100)\\fad(200,0)}}"
                  + "\\N".join(hook_lines(S.clean(plain(data["question"])), 100, 880).split("\\N")).replace(
                      "{\\c&H00FFFFFF&}", ""))
    path = W / "jurgen.ass"
    path.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
    return path


# ---- music ------------------------------------------------------------------------------------------------
def pick_music(stats):
    """A quiet dramatic track from music/jurgen (piano, strings, drones like the originals' Epidemic Sound picks),
    long enough for the video if possible, not the one of the last video."""
    tracks = sorted(MUSIC_J.glob("*.mp3"))
    if not tracks:
        return None, None
    recent = [v.get("music") for v in stats.get("videos", [])[-3:] if v.get("format") == "jurgen"]
    fresh = [t for t in tracks if t.name not in recent] or tracks
    long = [t for t in fresh if probe_duration(t) >= 150] or fresh
    t = random.choice(long)
    name = re.sub(r"^mixkit-|-\d+$", "", t.stem).replace("-", " ").title()
    print("music:", t.name)
    return t, f"{name} (Mixkit, free licence)"


def mix_audio(total, music, punch_at=0.0, fx=(), music_from=0.0):
    """Voice + music at an even level under it (every track is loudness-matched first, then ducked a little
    while the voice speaks), a gentle fade at both ends, the whole mix at YouTube's -14 LUFS -> mix.m4a.
    A track shorter than the video is looped with a 4 s crossfade. v2.04: `fx` = (start, length, sfx name) of the
    story's film shots, mixed like PASTRAK's; `music_from` = the music comes in only after the film opening."""
    fmt = "aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo"
    args = ["-i", "voice.mp3"]
    fc = [f"[0:a]{fmt},highpass=f=80,lowpass=f=9000,acompressor=threshold=0.1:ratio=2.5:attack=10:release=200,"
          "asplit=3[vo][key][key2]"]
    mix = ["[vo]"]
    if music:
        md = probe_duration(music)
        args += ["-i", str(pathlib.Path(music).resolve())]
        if md < total + 1:
            args += ["-i", str(pathlib.Path(music).resolve())]
            fc.append(f"[1:a]{fmt}[m1];[2:a]{fmt}[m2];[m1][m2]acrossfade=d=4[mloop]")
            src = "[mloop]"
        else:
            fc.append(f"[1:a]{fmt}[m0]")
            src = "[m0]"
        ms = int(music_from * 1000)                   # v2.05: after the film opening the track starts from its
        lead = f"adelay={ms}|{ms}," if ms else ""     # own quiet beginning (it was faded in at an already loud part)
        fc.append(f"{src}loudnorm=I=-27:TP=-6:LRA=7,volume={MUSIC_J_VOL},{lead}"
                  f"afade=t=in:st={music_from:.2f}:d={3.0 if music_from else 1.0},"
                  f"afade=t=out:st={max(0.0, total - 2.5):.2f}:d=2.5[mraw]")
        gap = (f",volume=enable='between(t,{punch_at - 0.45:.2f},{punch_at - 0.05:.2f})':volume=0.15"
               if punch_at > 5 else "")              # a beat of near silence before the last line (classic punch)
        # v2.05: release 1.5 s (was 0.6): the music stays down between sentences instead of surging in every pause
        # (the final loudnorm lifted those surges: 'too harsh and loud', Andrii, Oct 27)
        fc.append(f"[mraw][key]sidechaincompress=threshold=0.03:ratio=3:attack=40:release=1500{gap}[mu]")
        mix.append("[mu]")
    else:
        fc.append("[key]anullsink")
    fxs = []
    if fx:
        import pastrak as P                            # its sound effects, loudness and level (v1.99)
        for a, d, name in fx:
            f = P.SFX / f"{name}.mp3" if name else None
            if not f or not f.exists():
                continue
            n = sum(1 for x in args if x == "-i")      # this input's index
            d += 0.35
            args += ["-i", str(f.resolve())]
            g = P.FX_LUFS - P.lufs(f) + P.SFX_DB
            ms = int(a * 1000)
            fc.append(f"[{n}:a]{fmt},atrim=0:{d:.3f},asetpts=N/SR/TB,volume={g:.1f}dB,afade=t=in:d=0.06,"
                      f"afade=t=out:st={max(0.0, d - 0.35):.2f}:d=0.35,adelay={ms}|{ms}[fx{n}]")
            fxs.append(f"[fx{n}]")
    if fxs:
        fc.append(f"{''.join(fxs)}amix=inputs={len(fxs)}:duration=longest:normalize=0,apad,atrim=0:{total:.3f}[fxm]")
        fc.append("[fxm][key2]sidechaincompress=threshold=0.04:ratio=2.5:attack=30:release=400[fxd]")
        mix.append("[fxd]")
    else:
        fc.append("[key2]anullsink")
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,"
              f"loudnorm=I={S.LOUDNESS}:TP=-1.5:LRA=11,aresample=44100[a]")
    ff(*args, "-filter_complex", ";".join(fc), "-map", "[a]", "-t", f"{total:.3f}",
       "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "mix.m4a")


# ---- the video ----------------------------------------------------------------------------------------------
def make_video(data, topic, stats=None):
    from concurrent.futures import ThreadPoolExecutor
    story = {}
    spoken = S.respell(" ".join([plain(data["headline"])] + [plain(l) for l in data["lines"]]),
                     data.get("pronounce") if isinstance(data.get("pronounce"), dict) else None)
    print("voice text:", spoken[:400])
    S.LENGTH[0] = "fact"                                # get_images: 10 s film stretches that show the subject
    S.MAX_CLIPS = int(env("MAX_CLIPS", "6"))
    with stage("voice + pictures"), ThreadPoolExecutor(max_workers=4) as ex:
        voice = ex.submit(narrate, spoken)
        scenes = ex.submit(ai_scenes, data.get("scenes") or {})
        faces_f = ex.submit(portraits, data.get("people") or {})
        mp = ex.submit(Map, data["map"]) if (data.get("map") or {}).get("places") else None
        if data.get("pictures"):                       # a story file with hand-picked pictures per sentence
            faces_f.result()
            by_sent, faces, credits, data["_label_ok"] = manual_pictures(data["pictures"], data)
            photos = [p for ps in by_sent.values() for p in ps]
            credit_of = {p: data["_credit_of"].get(str(p), "") for p in photos}
            subject, film_at, clips = by_sent.get(0, [])[:1], {}, []
            if data.get("j_style") == "film":         # v2.04: the story's own archive film
                story, film_credits = story_films(data)
                credits += film_credits
        else:
            cand = story_candidates(data, topic)
            (photos, *_), credits, clips = S.get_images(data, topic, 18)
            credit_of = {**dict(zip(photos, credits)), **{p: c for p, _, c, _ in cand}}
            hint_of = {p: h for p, _, _, h in cand if h is not None}
            name_of = {p: n for p, n, _, _ in cand}
            photos = list(dict.fromkeys([p for p, _, _, _ in cand] + list(photos)))
            small = [p for p in photos if min(img_size(p)) < MIN_SIDE
                     and not CARD_RE.search(credit_of.get(p, "").split(" (")[0])]   # documents sit on a card
            if small:
                print("small pictures dropped:", len(small))
                photos = [p for p in photos if p not in small]
            photos = no_duplicates(photos)
            faces = faces_f.result()
            by_sent, subject, film_at, faces = match_pictures(photos, clips, faces, data, topic, credit_of, hint_of)
            data["pictures"] = [{"sentence": i + 1, **({"file": name_of[p]} if p in name_of else
                                                       {"credit": credit_of.get(p, "")})}
                                for i, ps in sorted(by_sent.items()) for p in ps] + \
                [{"sentence": i + 1, "credit": c, "name": data["people"][i]["name"]} for i, (_, c) in faces.items()]
            data["_auto_pictures"] = True                  # saved for review / reuse as a story file
            n_sent = 1 + len(data["lines"])
            shown = len(set(by_sent) | set(faces)) + len((data.get("map") or {}).get("routes") or [])
            print(f"sentences with their own picture: {shown} of {n_sent}")
            if data.get("j_hook") == "photo" and 0 not in by_sent and 0 not in faces:
                raise SystemExit("the 'photo' opening has no photo of its own for sentence 1")
            if shown < MIN_MATCHED * n_sent:           # nobody reviews the nightly videos: no weak ones
                raise SystemExit(f"only {shown} of {n_sent} sentences have a picture of their own")
            photos = list(dict.fromkeys([p for ps in by_sent.values() for p in ps] + subject))
            clips = [c for cs in film_at.values() for c in cs]
            credits = [credit_of[p] for p in photos] + [c["credit"] for c in clips]
        cards = {p for p in photos if CARD_RE.search(credit_of[p].split(" (")[0])}
        with stage("colorize"):
            col = colorize_all(list(photos) + [p for p, _ in faces.values()])
        photos = [col.get(p, p) for p in photos]
        by_sent = {i: [col.get(p, p) for p in ps] for i, ps in by_sent.items()}
        subject = [col.get(p, p) for p in subject]
        cards = {col.get(p, p) for p in cards}
        faces = {i: (col.get(p, p), c) for i, (p, c) in faces.items()}
        credits += [c for _, c in faces.values() if c not in credits]
        words = voice.result()
        words, total = fit_length(W / "voice.mp3", words)
        ai = scenes.result()
        try:
            data["_map"] = mp.result() if mp else None
        except Exception as e:
            print("map skipped:", type(e).__name__, str(e)[:120])
            data["_map"] = None
    S.LENGTH[0] = "long"
    data["_end_q"] = END_Q if plain(data.get("question", "")) else 0.0
    total = round(total + 0.4 + data["_end_q"], 3)     # a breath after the last word, then the question on screen
    if len(photos) + len(faces) < 4:
        raise SystemExit(f"only {len(photos) + len(faces)} pictures really belong to the story: not enough for 3 minutes")
    if not data["_map"]:
        data["map"] = None
    tl = S.timeline(data, words, total)
    data["sent_t"] = [0.0] + [round(l["start"], 1) for l in tl]   # for the retention curve: who left where
    S.write_srt(data, tl, total)
    shots = plan(tl, total, by_sent, subject, film_at, ai, data, faces, story)
    distinct = len({str(sh.get("src") or (sh.get("clip") or {}).get("credit") or sh["kind"]) for sh in shots})
    print(f"different pictures: {distinct} for {total:.0f} s")
    if data.get("_auto_pictures") and distinct < total / SECS_PER_PIC:   # Shinano: the same few again and again
        raise SystemExit(f"only {distinct} different pictures for {total:.0f} s")
    for sh in shots:
        if sh["kind"] == "map":
            sh["map"] = data["_map"]
        if sh.get("src") in cards:
            sh["card"] = True
    kinds = {k: sum(s["kind"] == k for s in shots) for k in ("photo", "film", "ai", "map")}
    print("length:", round(total, 1), "s | shots:", len(shots), kinds, "| portraits:", sum(bool(s.get("name"))
          for s in shots), "| cards:", sum(bool(s.get("card")) for s in shots), "| photos:", len(photos),
          "| clips:", len(clips), "| average shot:", round(total / max(1, len(shots)), 1), "s")
    names = {str(p): c for p, c in credit_of.items()}
    names.update({str(col.get(p, p)): c for p, c in credit_of.items()})
    names.update({str(p): c for p, c in faces.values()})
    sents = [plain(data["headline"])] + [plain(l) for l in data["lines"]]
    data["shot_list"] = [{"t": round(sh["start"], 1), "dur": round(sh["dur"], 1), "kind": sh["kind"],
                          "picture": (sh["clip"]["credit"] + (f" {sh['clip']['ss']:g}-{sh['clip']['to']:g} s"
                                                               if sh["clip"].get("story") else "")
                                      if sh["kind"] == "film" else "map" if sh["kind"] == "map"
                                      else names.get(str(sh.get("src")), str(sh.get("src", ""))))[:140],
                          "sentence": sents[sh["i"]][:120]} for sh in shots]   # for review before publishing
    data["ai_used"] = kinds["ai"]
    if kinds["ai"]:
        credits.append("Some scenes are AI-generated illustrations")
    if col:
        credits.append("Black-and-white photos colorized with DDColor (AI colorization)")
    music, credit = pick_music(stats or {})
    data["music_credit"], data["music_file"] = credit, (music.name if music else None)
    with ThreadPoolExecutor(max_workers=1) as ex:
        own = [sh for sh in shots if sh["kind"] == "film" and sh["clip"].get("story")]
        opening = max([sh["start"] + sh["dur"] for sh in own if sh["start"] < 15] or [0.0])
        audio = ex.submit(mix_audio, total, music, tl[-1]["start"] if tl else 0.0,
                          [(sh["start"], sh["dur"], sh["clip"].get("sfx")) for sh in own], opening)
        with stage("shots"):
            parts = pmap(lambda a: render_shot(*a), list(enumerate(shots)), workers=3)
        audio.result()
    (W / "shots.txt").write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    try:                                               # thumbnail: the first picture without the hook text
        thumb = (data.get("_file_path") or {}).get(str(data.get("thumb") or "").replace(" ", "_"))
        face = faces[min(faces)][0] if faces and S.CATEGORY == "people" else None
        pick = thumb or face or data.get("_cover")     # the story's "thumb"; a story about a person: their portrait
        if pick:                                       # (Andrii, Oct 25); else the strongest cover Gemini scored:
            # colorized (a tinted print too), 4x sharper, filling the whole frame (v1.89: the object big)
            person = S.CATEGORY == "people" and pick in (thumb, face)   # a portrait: face crop / warm tone
            pick = (S.enhance_cover(pick, color=S.COVER_COLOR, portrait=person) if not S.COVER_COLOR or
                    col.get(pick, pick) == pick else S.upscale(col[pick]))   # v1.93: the original, upscaled
            cx = min(1.0, max(0.0, float(data.get("thumb_x", 0.5))))   # thumb_x = where the crop is centred
            ff("-i", str(pick), "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,"
               f"crop=1080:1920:(iw-ow)*{cx:.2f}:(ih-oh)*0.35", "-frames:v", "1", "thumb_clean.png")   # head kept
            print("thumbnail:", data.get("thumb") or ("the portrait " if face and pick else "the strongest cover ")
                  + pathlib.Path(str(pick)).name)
        else:
            ff("-ss", "0.3", "-i", parts[0].name, "-vf", f"scale={SIZE[0]}:{SIZE[1]}", "-frames:v", "1", "thumb_clean.png")
    except Exception as e:
        print("clean thumbnail skipped:", type(e).__name__)
    ass = build_ass(data, tl, total, shots)
    with stage("final render"):
        ff("-f", "concat", "-safe", "0", "-i", "shots.txt", "-i", "mix.m4a", "-filter_complex",
           f"[0:v]{f'scale={SIZE[0]}:{SIZE[1]}:flags=bicubic,' if SHOT != SIZE else ''}"
           f"ass={ass.resolve()}:fontsdir={S.FONTS_DIR},format=yuv420p[v]", "-map", "[v]", "-map", "1:a",
           "-t", f"{total:.3f}", "-r", "30", *(["-c:v", "libx264", "-preset", "superfast", "-crf", "20", "-pix_fmt", "yuv420p"]
                                               if FAST else S.x264(20)), "-c:a", "copy", "-movflags", "+faststart", "final.mp4")
    data["seconds"] = round(total, 1)
    return credits


def metadata(data, topic, credits, translations):
    """shorts.py's description and localizations; the title carries the channel's hashtags like the original."""
    body = S.metadata(data, topic, credits, translations)
    tag = re.sub(r"[^a-z]", "", str(data.get("hashtag", "")).lower())[:12]
    tail = " #history #ww2" + (f" #{tag}" if tag else "")
    body["snippet"]["title"] = S.safe_text(plain(data["title"]))[:100 - len(tail)] + tail
    if data.get("ai_used"):
        body["status"]["containsSyntheticMedia"] = True   # YouTube's label for realistic AI scenes
    return body


def main():
    from datetime import date
    stats = S.load_stats()
    S.FILE_NO = max(len(S.used), len(stats["videos"])) + 1
    try:
        creds = S.credentials()
    except (KeyError, ImportError):
        if not S.DRY_RUN:
            raise SystemExit("YouTube secrets are missing: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN")
        creds = None
    if creds:
        with stage("youtube read"):
            try:
                yt0 = S.youtube(creds)
                up = yt0.channels().list(part="contentDetails", mine=True).execute()["items"][0]
                S.CHANNEL_ID = up.get("id", "")
                pl = up["contentDetails"]["relatedPlaylists"]["uploads"]
                items = yt0.playlistItems().list(part="snippet", playlistId=pl, maxResults=50).execute().get("items", [])
                S.CHANNEL_TITLES[:] = [i["snippet"]["title"] for i in items]
                nums = [int(n) for i in items for n in re.findall(r"File #(\d+)", i["snippet"].get("description", ""))]
                S.FILE_NO = max([S.FILE_NO] + [n + 1 for n in nums])
            except Exception as e:
                print("recent uploads not read:", str(e)[:120])
            if S.LEARN:
                S.refresh_stats(creds, stats)
                retention_curves(creds, stats)
    LESSONS[0] = lessons(stats)
    if env("J_PUBLISH") == "1":                        # publish the reviewed test video (preview branch -> work/)
        meta = json.loads((W / "metadata.json").read_text(encoding="utf-8"))
        if not (W / "final.mp4").exists() or not creds:
            raise SystemExit("publish: work/final.mp4 or YouTube secrets missing")
        S.set_category(meta.get("category") or "events")
        if meta.get("tts"):
            S.TTS_USED[:] = [meta["tts"]]
        data = meta["script"]
        if S.is_used(meta["topic"]):
            raise SystemExit(f"publish: {meta['topic']} is already on the channel")
        print("publishing the reviewed video:", meta["upload"]["snippet"]["title"])
        return publish(creds, stats, meta["upload"], data, meta["topic"])
    story = env("J_STORY") or env("J_SCRIPT") or ready_story()
    if story:                                          # a ready story file (stories/*.json) or a test script
        print("ready story:", story)
        d = json.loads(pathlib.Path(story).read_text(encoding="utf-8"))
        S.set_category(d.get("category", "events"))
        got = S.wiki_text(d["topic"])
        hook = d.get("hook") if d.get("hook") in J_HOOKS else "the_x_who"
        topic = {**S.topic_of([got]), "structure": d.get("structure", "story"), "hook": hook,
                 "title_format": hook, "j_length": d.get("length", "full")}
        set_length(topic["j_length"])
        data = finish(d, topic)
        data["story_topic"] = d["topic"]
        data["j_style"] = pick_style(stats, data)     # v2.04 A/B: None = a story without film
        print("style:", data["j_style"] or "no film in this story")
    else:
        with stage("topic"):
            topic = S.research(pick_topic())
        hook = pick_hook(stats, topic.get("fits"))
        topic.update(hook=hook, title_format=hook, j_length=pick_length(stats))   # the title is the opening
        set_length(topic["j_length"])
        S.WINNERS[:], S.LOSERS[:] = S.winners(stats, fmt="jurgen")
        print("opening:", topic["hook"], "| length:", topic["j_length"],
              f"({WORDS_AIM} words, max {MAX_LEN:.0f} s)")
        with stage("script"):
            data = write_script(topic)
    data["j_hook"], data["title_format"], data["j_length"] = topic.get("hook"), topic.get("title_format"), \
        topic.get("j_length")
    print(json.dumps({k: v for k, v in data.items() if not k.startswith("_")}, ensure_ascii=False)[:3000])
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=1) as ex:
        translations = ex.submit(S.translate, *S.texts(data))
        credits = make_video(data, topic, stats)
        body = metadata(data, topic, credits, translations.result())
    (W / "metadata.json").write_text(json.dumps({"upload": body, "topic": topic["key"], "category": S.CATEGORY,
                                                 "tts": S.TTS_USED[0] if S.TTS_USED else None,
                                                 "script": {k: v for k, v in data.items() if not k.startswith("_")}},
                                                ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if S.DRY_RUN:
        print("DRY RUN: nothing uploaded. Video: work/final.mp4, title/description: work/metadata.json")
        return
    publish(creds, stats, body, data, topic["key"])


def ready_story():
    """Andrii (Oct 19): the hand-made stories (stories/*.json: fact-checked script + hand-picked pictures) come
    first, lowest "priority" first; the bot writes its own story only when every one of them is on the channel."""
    for p in sorted(pathlib.Path("stories").glob("*.json"),
                    key=lambda p: (json.loads(p.read_text(encoding="utf-8")).get("priority", 99), p.name)):
        d = json.loads(p.read_text(encoding="utf-8"))
        names = {plain(d.get("title", "")).lower()} | ({short_title(title_case(d["sentences"][0])).lower()}
                                                      if d.get("sentences") else set())
        on_air = any(n and t.lower().startswith(n) for n in names       # the channel itself, not only used.json:
                     for t in S.CHANNEL_TITLES + [v.get("title", "") for v in S.load_stats()["videos"]])   # Oct 19
        if d.get("topic") and d.get("sentences") and d.get("pictures") and not S.is_used(d["topic"]) and not on_air:
            return str(p)
    return None


def publish(creds, stats, body, data, topic_key):
    """Upload + stats + thumbnail, playlist, pinned question, captions."""
    from datetime import date
    yt = S.youtube(creds)
    with stage("upload"):
        vid = S.upload(yt, body)
    UPLOADED.append(vid)
    S.used.append(topic_key)
    if data.get("story_topic") and data["story_topic"] != topic_key:   # Oct 21: "Operation Ten-Go" was saved as its
        S.used.append(data["story_topic"])                            # redirect "Operation Kikusui I" -> re-post risk
    S.USED.write_text(json.dumps(S.used, ensure_ascii=False, indent=1), encoding="utf-8")
    stats["videos"].append({"id": vid, "date": date.today().isoformat(), "category": S.CATEGORY, "hook": "jurgen",
                            "format": "jurgen", "length": "long", "topic": topic_key, "title": plain(data["title"]),
                            "seconds": data.get("seconds"), "words": len(" ".join(S.all_lines(data)).split()) +
                            len(plain(data["headline"]).split()), "music": data.get("music_file"),
                            "headline": plain(data["headline"]), "ai_scenes": data.get("ai_used", 0),
                            "j_hook": data.get("j_hook"), "title_format": data.get("title_format"),
                            "j_length": data.get("j_length"), "j_style": data.get("j_style"),
                            "sent_t": data.get("sent_t"),
                            "sent": [plain(x)[:70] for x in [data["headline"]] + list(data["lines"])],
                            "tts": S.TTS_USED[0] if S.TTS_USED else None})
    stats["recent"].append(plain(data["headline"]))
    S.save_stats(stats)
    with stage("playlist, comments"):
        if S.THUMB:
            clean = S.W / "thumb_clean.png"        # Andrii: no text on the thumbnail
            stats["videos"][-1]["thumb"] = S.set_thumbnail(yt, vid, clean.name if clean.exists() else "final.mp4")
        S.add_to_playlist(yt, vid)
        S.post_comment(yt, vid, data)
        S.upload_captions(yt, vid)
    S.to_tiktok(stats, body)
    S.save_stats(stats)


if __name__ == "__main__":
    import sys
    sys.modules.setdefault("jurgen", sys.modules[__name__])   # pastrak (story film) imports this running module
    try:
        main()
    except SystemExit as e:
        # a 3-minute video that can't be made well (no rich topic, script checks, too few matching pictures,
        # narration too long, Gemini down): the workflow makes a classic Short in this slot instead (exit code 3)
        if isinstance(e.code, str) and not UPLOADED and not S.DRY_RUN and env("J_PUBLISH") != "1":
            print("jurgen: no good video possible:", e.code)
            raise SystemExit(SKIP)
        raise
    except Exception:                                  # e.g. a ready story's picture or article fetch failed:
        if UPLOADED or S.DRY_RUN or env("J_PUBLISH") == "1" or env("J_STORY"):   # the night slot still gets
            raise                                                                # a classic Short
        import traceback
        traceback.print_exc()
        print("jurgen failed before the upload -> classic Short")
        raise SystemExit(SKIP)
    finally:
        S.summary()
