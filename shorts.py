import array, asyncio, html, json, math, os, pathlib, random, re, subprocess, time, unicodedata, wave
import requests

W = pathlib.Path("work")
W.mkdir(exist_ok=True)
USED = pathlib.Path("used.json")
used = json.loads(USED.read_text(encoding="utf-8")) if USED.exists() else []
env = os.getenv

# ---- Categories: label, accent, kind, playlist, topic, story, tags ------------------------------------
# Focus: key events, legendary tanks, legendary people, legendary weapons. Force one with env CATEGORY.
CATEGORIES = {
    "events": ("KEY BATTLES", "0xE53935", "single", "Key Battles & Events",
               "a major, famous World War II battle, operation, campaign or event that changed the war "
               "(turning points, invasions, sieges, decisive naval and air battles)",
               "Tell ONE surprising, little-known moment or decision of it (a trick, a mistake, an odd detail) and "
               "why it mattered, not a summary of the whole battle. Losses only as totals, never graphic.",
               ["WW2 battles", "military history", "turning point"]),
    "tanks": ("LEGENDARY TANKS", "0xFFB300", "single", "Legendary Tanks",
              "a legendary World War II tank, tank destroyer or assault gun",
              "Tell ONE surprising, little-known detail of it (a hidden feature, a strange design choice, an odd "
              "origin, an unexpected use or a fatal flaw) and what it meant in battle, not a spec sheet.",
              ["WW2 tanks", "tank history", "legendary tanks"]),
    "people": ("WAR LEGENDS", "0x4FC3F7", "single", "War Legends",
               "a legendary World War II person: a decorated soldier, pilot, sniper, medic, resistance fighter, "
               "spy, codebreaker, rescuer or a famous commander. Never Nazi party or SS members, war criminals, "
               "or anyone known for atrocities",
               "ONE defining moment: the trick, the decision or the risk that made them famous, told as a story, "
               "not a biography. Respectful, never glorify killing; commanders of any side only in a neutral, "
               "factual tone.",
               ["WW2 heroes", "war legends", "history"]),
    "weapons": ("LEGENDARY WEAPONS", "0xFF7043", "single", "Legendary Weapons",
                "a legendary World War II weapon or war machine: rifle, machine gun, submachine gun, artillery, "
                "rocket, fighter, bomber, battleship, aircraft carrier or submarine",
                "Tell ONE surprising, little-known detail of it (a hidden feature, a strange design choice, an odd "
                "origin, an unexpected use or a fatal flaw) and what it meant in battle, not a spec sheet.",
                ["WW2 weapons", "military technology", "legendary weapons"]),
    "versus": ("VERSUS", "0x7E57C2", "versus", "WW2 Versus",
               "two famous World War II rivals of the same type that faced each other or are often compared "
               "(tank vs tank, fighter vs fighter, battleship vs battleship, rifle vs rifle)",
               "Compare them on the ONE difference that decided their fight (armor, speed, reliability, numbers "
               "built...), with at most 2 numbers, then give a fair verdict based on the text.",
               ["WW2 versus", "military comparison"]),
    "quiz": ("GUESS THE MACHINE", "0x66BB6A", "quiz", "Guess the Machine",
             "a famous, visually recognizable World War II tank, aircraft, warship or weapon",
             "The headline asks viewers to name it (e.g. 'Can you name this fighter?'). Give clues (role, "
             "country, a famous record) WITHOUT the name. Only the LAST line reveals it: \"It's the [r]Name[/r]!\". "
             "Nothing before the last line may reveal the name.",
             ["WW2 quiz", "guess the tank"]),
    "myth": ("MYTH VS TRUTH", "0x26A69A", "single", "WW2 Myth vs Truth",
             "a famous World War II battle, tank, weapon or person surrounded by a popular myth or misconception "
             "that its Wikipedia article corrects",
             "Line 1 states the popular myth starting with 'Myth:'. Then 'Truth:' and the real facts from "
             "the text, with numbers and names. Only use a myth the text itself addresses.",
             ["WW2 myths", "history myths"]),
    "classified": ("CLASSIFIED FILES", "0x9E9E9E", "single", "Classified Files",
                   "a famous secret or failed World War II operation, or a secret research program or "
                   "unethical human experimentation by Nazi Germany or Imperial Japan",
                   "Explain the goal, what went wrong or what was done, who was responsible, and the consequences: "
                   "trials, punishment, cover-ups or deals after the war. Describe experiments only in general "
                   "factual terms, never graphic details, respectful to victims.",
                   ["secret history", "WW2 mysteries"]),
    "ranking": ("RANKED", "0xFFD54F", "single", "WW2 Ranked",
                "a World War II subject that can be ranked or called out as extreme: the weakest army, the worst tank, "
                "the most produced weapon, the shortest-lived design, the most overrated machine, the deadliest "
                "single weapon type, or a famous 'why they never mass-produced X' case",
                "Open with a bold ranking claim the source supports (weakest / worst / most / never / only). "
                "Then give 2-3 concrete reasons from the text. End with a punchline that locks the ranking. "
                "Never invent rankings the article does not support.",
                ["WW2 ranked", "military ranking", "worst tank", "WW2 facts"]),
    "surrender": ("SURRENDER FILES", "0xBDBDBD", "surrender", "WW2 Surrenders",   # every 4th video, see SURRENDER
                  "a real World War II surrender filmed at the time", "Archive film only, captions, music.",
                  ["WW2 surrender", "archive footage"]),
}
# Ranking + machines first: tops win on ranking/myth/shock; tanks/versus still convert well.
# Once enough videos have stats, learned() shifts these weights toward what YouTube actually pushes.
ROTATION = ["tanks", "ranking", "weapons", "versus", "myth", "tanks", "events", "weapons",   # v2.03 (Andrii, Oct 27):
            "ranking", "weapons", "versus", "tanks", "myth", "people", "ranking"]          # no quiz, no classified
SCALE = env("SCALE", "0") == "1"                        # 1 = old style: every video built around a huge number
LOOP = env("LOOP", "punch")                             # punch = ends on a punchline; bridge / callback = old loops
HOOKS = {   # hook types; the bot rotates them and learns which ones bring more views
    # === TOP-tier (highest priority for learning / viral potential) ===
    "shock_claim": "ONE bold, specific, almost unbelievable claim in the first 4 words, then the subject. "
                   "Example: 'This tank killed more of its own crews than the enemy.' or "
                   "'Hitler’s best pilot never shot down a single plane.'",
    "nobody_knows": "Start with 'Nobody talks about...' / 'Historians almost never mention...' / "
                    "'They never taught you this about...' + the subject + the hidden detail. "
                    "Example: 'Nobody talks about the grenade launcher on the Tiger II’s roof.'",
    "wrong": "Open by contradicting the common belief hard: 'Everything you know about the Tiger is wrong.' "
             "or 'The T-34 was not the best tank of the war.' Then deliver the real reason.",
    "you_inside": "Put the viewer inside the machine/person in present tense: "
                  "'You are inside this tank as the first shell hits.' or "
                  "'You are the pilot who just realized the Zero has no armor.'",
    "one_detail": "Name the subject in the first 3 words, then drop ONE extremely specific, visual, "
                  "almost weird detail that creates an instant gap. "
                  "Example: 'The Tiger II had a weapon you could easily miss.' "
                  "'The Flak 88 was built to shoot down planes — then it hunted tanks.'",
    "scale_paradox": "Biggest number + immediate paradox or question. "
                     "Example: '3.8 million men. Six months. And they still lost.' "
                     "'1,347 tanks. And one design mistake killed most of them.'",
    "record": "Lead with a first/last/only/most: 'The first jet fighter that ever saw combat.' "
              "'The only tank that scared its own crews more than the enemy.'",
    "origin_weird": "Surprising maker or origin that feels wrong: "
                    "'This gun was built by a car headlight factory.' "
                    "'This battleship was designed by a man who had never seen the sea.'",
    # === Special formats ===
    "coldopen": "COLD OPEN: start at the climax as a mystery in present tense, then rewind. "
                "Headline must be max 8 words and end on a paradox or unanswered question.",
    "map": "MAP: the video opens on a real map zooming into the place. "
           "Headline points at that place and creates a gap: 'This tiny island decided the Pacific War.'",
    "action": "Drop the viewer into the middle of the action, present tense, no setup: "
              "'Midnight. British gliders land in total silence.' "
              "'The first shell hits the Tiger’s side. The crew has 4 seconds.'",
    "contrarian": "Hard contradiction of a popular myth, backed by the source. "
                  "Example: 'The Tiger was not the deadliest tank of the war.'",
    # === Lower priority / legacy ===
    "curiosity": "Classic curiosity gap: the thing + a hidden twist without giving it away.",
    "number": "One shocking, specific number from the source up front.",
    "fact": "ONE FACT: the thing + its surprising detail in one plain sentence.",
}
COLD_BEATS = ("headline = the climax as a mystery (present tense, max 8 words) -> REWIND -> "
              "1) the time jump + set-up -> 2) the stakes: the plan, the target, what everyone expects -> "
              "3) the twist: 'But...' -> 4) the reason almost nobody knows -> "
              "5) the payoff: the concrete answer with a number -> "
              "6) the conclusion that answers the headline and ends on its subject so the loop feels seamless")
BEATS = {   # story structure per category: ONE story, mandatory mid RE-HOOK, punchline that loops well
    "events": "the surprising moment the headline promises -> what was at stake -> RE-HOOK (But.../Until...): the "
              "detail almost nobody knows -> what it changed -> PUNCHLINE: consequence or irony, echo the headline",
    "tanks": "the hidden detail the headline promises -> why it was built that way -> RE-HOOK (But...): the twist, how "
             "it worked or failed in battle -> PUNCHLINE: consequence or irony, echo the headline",
    "people": "who they were in one short phrase -> the ONE defining moment the headline promises -> HOW they did it "
              "(tactic/trick/decision) -> RE-HOOK: the risk or twist inside that same moment -> "
              "PUNCHLINE: the result in one short line, echo the headline. No biography, no later life",
    "weapons": "the hidden detail the headline promises -> why it was built that way -> RE-HOOK (But...): a flaw or "
               "surprising use -> PUNCHLINE: consequence or irony, echo the headline",
    "versus": "the ONE difference that decided it -> A's side -> B's side -> RE-HOOK: the factor nobody compares -> "
              "PUNCHLINE: fair verdict from the source, one short line",
    "quiz": "clue 1 (role and country) -> clue 2 (a famous record or number) -> clue 3, the strongest -> reveal",
    "myth": "'Myth:' the popular belief -> 'Truth:' what the source says -> the evidence -> RE-HOOK: why the myth "
            "exists -> PUNCHLINE that lands the truth in one short line",
    "classified": "the secret goal -> how it worked or failed -> RE-HOOK: the detail that stayed hidden -> "
                  "PUNCHLINE: the consequence in one short line",
    "ranking": "bold ranking claim the source supports (worst/weakest/most/never) -> reason 1 with a concrete fact -> "
               "RE-HOOK: reason 2 that surprises -> PUNCHLINE that locks the ranking in one short line",
}
FACT_BEATS = ("ONE FACT, 15-18 seconds: headline = the thing + surprising detail -> line 1: how/why, concrete and "
              "visual, starts with conflict not background -> line 2: one more concrete detail or stakes -> "
              "last line: PUNCHLINE (consequence/irony) that rewards a replay")

# ---- Settings (override in the workflow env) ----------------------------------
MUSIC_DIR = pathlib.Path("music")                       # your tracks: music/*.mp3 (subfolders allowed)
MUSIC_INDEX = MUSIC_DIR / "tracks.json"                 # moods per track, written by the bot (editable)
MUSIC_OLD = pathlib.Path("music.mp3")                   # old single track, used only if music/ is empty
MUSIC_AI = env("MUSIC_AI", "1") == "1"                  # Gemini listens to new tracks and tags their mood
MOODS = ["epic", "heroic", "dramatic", "dark", "tense", "suspense", "mysterious", "sad", "emotional", "hopeful",
         "triumphant", "aggressive", "action", "heavy", "powerful", "calm", "playful", "upbeat", "military",
         "march", "cinematic", "orchestral", "rock", "electronic", "ambient", "piano", "drums"]
CAT_MOODS = {   # what each category should sound like
    "events": ["epic", "dramatic", "cinematic", "military", "orchestral", "powerful"],
    "tanks": ["heavy", "powerful", "aggressive", "drums", "rock", "military", "epic"],
    "people": ["heroic", "emotional", "hopeful", "triumphant", "cinematic", "piano"],
    "weapons": ["powerful", "action", "aggressive", "heavy", "drums", "military"],
    "versus": ["aggressive", "action", "rock", "drums", "epic", "powerful"],
    "quiz": ["suspense", "mysterious", "playful", "upbeat", "tense"],
    "myth": ["mysterious", "suspense", "playful", "dramatic"],
    "classified": ["dark", "tense", "suspense", "mysterious", "ambient", "electronic"],
    "ranking": ["aggressive", "powerful", "dramatic", "epic", "drums", "military"],
    "surrender": ["sad", "emotional", "dramatic", "cinematic", "ambient", "piano"],
}
CHANNEL = env("CHANNEL", "CLASSIFIED 1945")             # channel block at the top of every frame
HANDLE = env("HANDLE", "@Classified1945")
AVATAR = pathlib.Path("avatar.png")                     # channel avatar for the top block (optional)
FILE_NO = len(used) + 1                                 # running number shown on screen
NARRATION = env("NARRATION", "1") == "1"
VOICE = env("VOICE", "en-US-AndrewNeural")
TTS_ENGINE = env("TTS", "auto")                         # auto = Edge TTS, Azure (if a key is set), offline Kokoro
AZURE_KEY, AZURE_REGION = env("AZURE_SPEECH_KEY", ""), env("AZURE_SPEECH_REGION", "")   # free F0: 0.5M chars/month
TTS_USED = []                                           # which engine read this video (saved in stats)
KOKORO_DIR = pathlib.Path(env("KOKORO_DIR", str(pathlib.Path.home() / "kokoro")))
KOKORO_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
KOKORO_FILES = ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin")   # Kokoro-82M, Apache 2.0, ~115 MB, cached
KOKORO_VOICE = env("KOKORO_VOICE", "bm_george")         # calm British male, close to Edge's Ryan
MUSIC_VOL = float(env("MUSIC_VOL", "0.065" if NARRATION else "0.09"))  # v2.02 (Andrii, Oct 27): half of 0.13/0.18
SFX = env("SFX", "1") == "1"
SFX_VOL = float(env("SFX_VOL", "1.0"))                   # 0.5 = quieter, 2 = louder
LANGS = [l.strip() for l in env("LANGS", "es,pt,de,fr,it,pl,uk,tr").split(",") if l.strip()]
FUNNY = float(env("FUNNY", "0.35"))                     # chance of one silly sound (myth/versus)
MIN_SEC, MAX_SEC, SHOT_SEC, MAX_IMAGES = 15.0, 40.0, 1.5, 14  # floor 15 s; new picture every ~1.5 s
FACT_MIN = 15.0                                         # ONE FACT videos run 15-18 s (never shorter)
OPENING = env("OPENING", "punch")                       # punch = sharp photo pushing in; tease = old blurred start
PUNCH_SEC, TEASE_SEC = 1.6, 1.3
TTS_RATE = env("TTS_RATE", "+7%")                       # Andrii, Oct 21: +14% was too fast; ~155 words per minute
COLD_RATE = env("COLD_RATE", "+12%")                    # cold-open videos: a little punchier (was +20%)
TTS_PITCH = env("TTS_PITCH", "+0Hz")                    # voice pitch for Edge/Azure, e.g. -22Hz (a deeper voice)
REWIND = 0.55                                           # cold open: tape rewind right after the first sentence
COLD = {}                                               # cold-open timings of the video being made
COVER = env("COVER", "1") == "1"                       # opens on the main photo full screen, then it shrinks in
BACKDROP = env("BACKDROP", "1") == "1"
BG = env("BG", "black")                                # black = black background; blur = the old blurred photo
COVER_SEC, MORPH_SEC, TAIL_SEC = 0.3, 0.35, 0.5        # full-screen hold, shrink into the frame, grow back at the end
COVER_T = COVER_SEC + MORPH_SEC
BRAND_SEC = 1.8                                        # category + channel after the hook has landed (hook alone first)
LOOK = {}                                              # this video: cover / backdrop on or off
LOUDNESS = float(env("LOUDNESS", "-14"))                # LUFS, the level YouTube plays videos at
STATS = pathlib.Path("stats.json")                     # uploads + their views, used to learn what works
LEARN = env("LEARN", "1") == "1"
CAPTIONS = env("CAPTIONS", "1") == "1"                 # upload exact English subtitles (400 API units)
FOOTAGE = env("FOOTAGE", "1") == "1"                   # archive film clips between the photos
MAX_CLIPS = int(env("MAX_CLIPS", "4"))
SERIES_RATE = float(env("SERIES", "0.15"))             # two-part = lower completion; keep rare
LENGTH_MODE = env("LENGTH", "ab")                      # ab = mix of ONE FACT (15-18 s) and longer stories
                                                        # (22-28 s); fact / short / normal force one
LENGTH = ["normal"]                                     # the length picked for this video (saved in stats)
FACT_FILM = [False]                                     # ONE FACT: archive film of the subject was found
THUMB = env("THUMB", "1") == "1"                       # the first frame (full-screen cover, no text) as the thumbnail
REPLIES = int(env("REPLIES", "0"))                     # replies to viewer comments per day: 0 = off (e.g. 5 to turn on)
PART, SERIES_INFO = 0, {}                              # 1 or 2 when this video is part of a two-part story
WINNERS, LOSERS = [], []                               # headlines of the channel's best and worst videos
CHANNEL_ID = ""
DRY_RUN = env("DRY_RUN", "0") == "1"                   # 1 = make the video + work/metadata.json, upload nothing
UA = {"User-Agent": "Classified1945ShortsBot/1.0 (https://terraincognita001.github.io/terra-incognita/)"}
WIKI, COMMONS = "https://en.wikipedia.org/w/api.php", "https://commons.wikimedia.org/w/api.php"

# ---- Layout 1080x1920: black bar | picture | black bar ------------------------
TOP_BAR, MID_H = 560, 700                                # picture in the eye-line zone
STYLE_A = env("STYLE", "a") == "a"                     # Andrii, Oct 24 (v1.85): the Jurgens look: picture full screen,
if STYLE_A:                                            # only a small white title top left
    TOP_BAR, MID_H = 0, 1920
CAPS = env("CAPS", "1") == "1"                         # Andrii, Oct 24-25 (@EisernesKreuz look): two-line captions as in
CAP_BOX = "&H2E10C8&"                                  # the jurgen Shorts, the word being spoken on a crimson box, the
WHIP = env("WHIP", "1") == "1"                         # spoken title captioned too; cuts open with a 2-frame blur
WHIP_VF = "avgblur=sizeX=45:sizeY=1:enable='lt(t,0.02)',avgblur=sizeX=22:sizeY=1:enable='lt(t,0.05)',"
HEAD_TL = []                                           # the spoken headline's words with times (set by timeline())
BOT_Y = TOP_BAR + MID_H
# iPhones crop ~100 px from each side and YouTube's icons cover the top ~250 px, so everything important sits
# inside x 120..960: channel block between YouTube's icons, category line, headline box, then the photo
BLOCK_Y, AV_SIZE, LABEL_Y, HEAD_TOP, HEAD_W = 150, 58, 290, 338, 840
CHAR_W = [348, 456, 521, 838, 696, 1002, 872, 306, 457, 457, 523, 838, 380, 415, 380, 365, 696, 696, 696, 696, 696,
          696, 696, 696, 696, 696, 400, 400, 838, 838, 838, 580, 1000, 774, 762, 734, 830, 683, 683, 821, 837, 372,
          372, 775, 637, 995, 837, 850, 733, 850, 770, 720, 682, 812, 774, 1103, 771, 724, 725, 457, 365, 457, 838,
          500, 500, 675, 716, 593, 716, 678, 435, 716, 712, 343, 343, 665, 343, 1042, 712, 687, 716, 716, 493, 595,
          478, 712, 652, 924, 645, 652, 582, 712, 365, 712, 838]   # DejaVu Sans Bold widths, chars 32-126, 1/1000 em
WHITE, RED, YELLOW = "&H00FFFFFF&", "&H003539E5&", "&H0000D7FF&"   # ASS colours (BGR)
FONT = pathlib.Path("font.ttf")
FONTS_DIR = str(FONT.resolve().parent) if FONT.exists() else "/usr/share/fonts/truetype/dejavu"
SKIP_IMG = re.compile(r"flag|logo|icon|symbol|emblem|seal|coat.of.arms|signature|stub|commons-|wiki|"
                      r"question.book|edit-|ambox|portal|padlock|crystal|nuvola|disambig|"
                      r"corpse|dead bodies|mass.grave|cremat|autopsy|execution|executed|hanged|"
                      r"massacre of|atrocit", re.I)   # only clearly graphic filenames; wounded/killed soldiers OK
# Reject modern namesakes (e.g. BAE Archer 2010s vs WW2 Archer SP).
# Do NOT match bare 20xx years — Commons DateTime is almost always the upload date of a PD scan.
MODERN_BRAND = re.compile(
    r"\b(bae systems|hanwha|rheinmetall ag|general dynamics|lockheed martin|"
    r"modern army|nato exercise|peacekeeping|iraq war|afghanistan war|"
    r"smartphone|selfie|drone footage|go.?pro|digital camo|multicam|"
    r"re-?enact\w*|living history|air ?show|motherland calls|mamayev|victory day parade 20\d\d)\b",
    re.I)                                              # Oct 24 dry run: a reenactment T-34 and the Motherland statue
# in the FILE NAME only: museum pieces and memorials today (archives' categories often say "museum" for old photos)
MODERN_NAME = re.compile(r"(?<!war.)museum|memorial|monument|statue|replica|denkmal|ehrenmal|gedenk", re.I)
# Year in the FILE NAME only (e.g. Archer_2016_Sweden.jpg) — not in upload metadata
MODERN_YEAR_NAME = re.compile(r"(?:^|[_\-\s])(20[0-2]\d)(?:[_\-\s.]|$)", re.I)
WW2_HINT = re.compile(
    r"\b(world war\s*i{1,2}|ww\s*i{1,2}|193[9]|194[0-5]|wehrmacht|red army|allied|"
    r"axis|normandy|stalingrad|pacific war|eastern front|western front|"
    r"panzer|spitfire|messerschmitt|sherman|tiger|kampf|battleship|destroyer|"
    r"imperial japanese|ijn |us navy|royal navy)\b", re.I)


def set_category(name):
    """Sets the category globals used everywhere (label, colours, prompts)."""
    global CATEGORY, LABEL, ACCENT, KIND, PLAYLIST, TOPIC, STORY, CAT_TAGS, ACC_ASS
    CATEGORY = name
    LABEL, ACCENT, KIND, PLAYLIST, TOPIC, STORY, CAT_TAGS = CATEGORIES[name]
    ACC_ASS = f"&H00{ACCENT[6:8]}{ACCENT[4:6]}{ACCENT[2:4]}&"


set_category(env("CATEGORY") or ROTATION[len(used) % len(ROTATION)])   # learning may change it at start-up


def x264(crf):
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p"]


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True, cwd=W)


def probe_duration(path):
    try:
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "default=nw=1:nk=1", str(path)],
                                    capture_output=True, text=True, check=True).stdout.strip())
    except Exception:
        return 0.0


def font_family():
    try:
        out = subprocess.run(["fc-scan", "--format", "%{family}", str(FONT)],
                             capture_output=True, text=True, check=True).stdout
        return out.split(",")[0].strip() or "DejaVu Sans"
    except Exception:
        return "DejaVu Sans"


# ---- Gemini ------------------------------------------------------------------
# every model has its own free daily quota (it resets at midnight Pacific = 08:00 London); a model that does not
# exist answers 404 once and is skipped for the rest of the run
MODELS = [env("GEMINI_MODEL", "gemini-3.5-flash"), "gemini-flash-latest", "gemini-3.1-flash-lite", "gemini-2.5-flash",
          "gemini-flash-lite-latest", "gemini-2.5-flash-lite"]
LITE_FIRST = ["gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-flash-latest",
              MODELS[0], "gemini-2.5-flash"]            # checks, tags, translation: keep the big models' quota
COOL, DEAD, CALLS, TIMES = {}, set(), {}, {}            # model cooldowns, missing models, requests, stage seconds
T0 = time.time()


class stage:
    """with stage("render"): ... adds the time to the summary printed at the end."""
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.t = time.time()

    def __exit__(self, *exc):
        TIMES[self.name] = TIMES.get(self.name, 0) + time.time() - self.t


def gemini(prompt, ok, rounds=6, extra=None, purpose="script", models=None):
    """JSON from Gemini. A 429/5xx puts that model on cooldown and moves to the next one at once; a used-up daily
    quota skips the model for the rest of the run. Waits only when every model is cooling down (exponential
    backoff with jitter, honours retryDelay). Every request is counted per purpose for the summary."""
    models, delay = models or MODELS, 5
    for rnd in range(rounds):
        for model in models:
            if model in DEAD or COOL.get(model, 0) > time.time():
                continue
            CALLS[purpose] = CALLS.get(purpose, 0) + 1
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  params={"key": os.environ["GEMINI_API_KEY"]}, timeout=(15, 90),
                                  json={"contents": [{"parts": [{"text": prompt}] + (extra or [])}],
                                        "generationConfig": {"responseMimeType": "application/json"}})
                if r.status_code == 429 and "PerDay" in r.text:
                    DEAD.add(model)
                    print(f"{model}: daily quota used up ({purpose}) -> next model")
                    continue
                if r.status_code == 429 or r.status_code >= 500:
                    m = re.search(r'retryDelay"\s*:\s*"(\d+)', r.text)
                    COOL[model] = time.time() + min(120, int(m.group(1)) if m else (60 if r.status_code == 429 else 20))
                    print(f"{model} {r.status_code} ({purpose}) -> next model")
                    continue
                if not r.ok:
                    if r.status_code == 404 or "not found" in r.text.lower():
                        DEAD.add(model)
                    print(model, r.status_code, purpose, r.text[:120].replace("\n", " "))
                    continue
                data = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
                if ok(data):
                    return data
                print(model, "incomplete JSON", purpose)
            except (requests.Timeout, requests.ConnectionError) as e:
                COOL[model] = time.time() + 20               # slow or unreachable: try the other models first
                print(model, "error:", type(e).__name__, purpose)
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as e:
                print(model, "error:", type(e).__name__, purpose)
        if rnd < rounds - 1:
            live = [COOL.get(m, 0) for m in models if m not in DEAD]
            if not live:
                break
            soonest = min(live) - time.time()
            if soonest <= 0:                                  # a model is free (bad answer): retry almost at once
                time.sleep(1 + random.random())
                continue
            wait = min(60, max(delay, soonest)) + random.uniform(0, 2)
            print(f"gemini: all models busy, waiting {wait:.0f} s ({purpose})")
            time.sleep(wait)
            delay = min(60, delay * 2)
    raise SystemExit(f"Gemini unavailable ({purpose}), try later")


def pmap(fn, items, workers=4):
    """Parallel map for network calls (Wikipedia, Commons, downloads); keeps the order of the items."""
    from concurrent.futures import ThreadPoolExecutor
    items = list(items)
    if len(items) < 2:
        return [fn(x) for x in items]
    with ThreadPoolExecutor(max_workers=min(workers, len(items))) as ex:
        return list(ex.map(fn, items))


# ---- Wikipedia / Commons images ----------------------------------------------
def wiki_get(**p):
    return requests.get(WIKI, params={**p, "format": "json", "formatversion": 2, "redirects": 1},
                        headers=UA, timeout=60).json()


def wiki_text(title):
    try:
        page = wiki_get(action="query", prop="extracts", explaintext=1, titles=title)["query"]["pages"][0]
    except Exception:
        return None, None
    if page.get("missing") or not page.get("extract"):
        return None, None
    return page["title"], re.split(r"\n==\s*(?:See also|References|Notes|Further reading|External links|"
                                   r"Bibliography)\s*==", page["extract"])[0][:20000]


SENSITIVE = re.compile(r"corpse|dead bodies|mass.grave|cremat|autopsy|execut(ion|ed)|hanged|hanging|"
                       r"extermination.camp|death.camp|holocaust victims|genocide|"
                       r"auschwitz|birkenau|treblinka|sobib|majdanek|unit.731|"
                       r"starv(ed|ing)|emaciat|skelet|human remains|"
                       r"massacre of|atrocit", re.I)   # only truly graphic; soldiers, wounded, camps as locations OK


def _meta_text(name, ii, keys=None):
    """Filename + selected metadata fields (HTML stripped) for filtering."""
    meta = ii.get("extmetadata", {}) if isinstance(ii, dict) else {}
    keys = keys or ("Categories", "ImageDescription", "ObjectName", "Credit")
    bits = [name]
    for k in keys:
        bits.append(re.sub(r"<[^>]+>", " ", str(meta.get(k, {}).get("value", ""))))
    return " ".join(bits)


def image_item(name, ii, min_side, require_period=False):
    """(url, credit) for a free-licensed, non-graphic image of sufficient size, else None.
    Wikipedia article images (require_period=False): only drop graphic + clear modern brands.
    Commons search (require_period=True): also prefer WW2 hints; drop post-1945 years in name/desc."""
    meta = ii.get("extmetadata", {}) if isinstance(ii, dict) else {}
    about = _meta_text(name, ii)                     # no DateTime — that is upload date, not photo date
    if SENSITIVE.search(about):
        return None
    # modern brand names (BAE Archer, etc.) always out
    if MODERN_BRAND.search(about) or MODERN_YEAR_NAME.search(name) or MODERN_NAME.search(name):
        return None
    if require_period:
        # drop only if description/categories loudly say post-war year AND no WW2 hint
        if not WW2_HINT.search(about) and re.search(r"\b(19[6-9]\d|20\d{2})\b", about):
            return None
    lic = meta.get("LicenseShortName", {}).get("value", "")
    if not re.search(r"public domain|^pd|cc0|cc[ -]by", lic, re.I) or \
            min(ii.get("width", 0), ii.get("height", 0)) < min_side:
        return None
    artist = re.sub(r"<[^>]+>", "", html.unescape(meta.get("Artist", {}).get("value", ""))).strip()[:60]
    page = ii.get("descriptionshorturl") or ii.get("descriptionurl") or ""
    return ii.get("thumburl") or ii.get("url"), f"{name[:60]} ({artist + ', ' if artist else ''}{lic}) {page}".strip()


def wiki_images(title, limit=MAX_IMAGES):
    """Photos (and one map) from the article in page order, lead image first, map second.
    Prefer article images — they are almost always of the correct historical subject."""
    try:
        names = wiki_get(action="parse", page=title, prop="images").get("parse", {}).get("images", [])
        lead = wiki_get(action="query", prop="pageimages", piprop="name", titles=title)["query"]["pages"][0]
        if lead.get("pageimage") in names:
            names.remove(lead["pageimage"])
            names.insert(0, lead["pageimage"])
        names = [n for n in names if not SKIP_IMG.search(n) and (
            n.lower().endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff")) or
            (n.lower().endswith(".svg") and "map" in n.lower()))]
        pages = wiki_get(action="query", prop="imageinfo", iiprop="url|size|extmetadata", iiurlwidth=1800,
                         titles="|".join("File:" + n for n in names[:50]))["query"]["pages"] if names else []
    except Exception:
        return []
    info = {p["title"][5:].replace(" ", "_"): (p.get("imageinfo") or [{}])[0] for p in pages}
    out, has_map = [], False
    for n in names:
        is_map = "map" in n.lower()
        item = image_item(n.rsplit(".", 1)[0].replace("_", " "), info.get(n.replace(" ", "_"), {}),
                          0 if is_map else 200, require_period=False)
        if not item or (is_map and has_map):
            continue
        if is_map:
            has_map = True
            out.insert(min(1, len(out)), item)
        else:
            out.append(item)
        if len(out) >= limit:
            break
    return out


def _period_query(query):
    """Force every Commons search into the WW2 era so modern namesakes are less likely to rank."""
    q = (query or "").strip()
    if not q:
        return "World War II"
    if WW2_HINT.search(q):
        return q
    return f"{q} World War II"


def commons_images(query, need, strict=True):
    """Search Wikimedia Commons for period photos. Always bias to WW2; drop modern matches."""
    try:
        pages = requests.get(COMMONS, headers=UA, timeout=60, params={
            "action": "query", "format": "json", "formatversion": 2, "generator": "search",
            "gsrsearch": f"{_period_query(query)} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 40,
            "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1800}).json()["query"]["pages"]
    except Exception:
        return []
    out = []
    for p in sorted(pages, key=lambda p: p.get("index", 99)):
        title = p.get("title", "")
        if SKIP_IMG.search(title):
            continue
        item = image_item(title.replace("File:", ""), (p.get("imageinfo") or [{}])[0], 300,
                          require_period=strict)
        if item:
            out.append(item)
        if len(out) >= need:
            break
    return out


def extra_jobs(data):
    """Related articles + story-specific Commons searches + countries — all forced into WW2 period."""
    qs = []
    for q in data.get("image_queries", [])[:10]:
        if not isinstance(q, str) or len(q) < 3:
            continue
        qs.append(q)
        # also try explicit period variants if the script forgot them
        if not WW2_HINT.search(q):
            qs.append(f"{q} 1944")
            qs.append(f"{q} World War II")
    # unique, keep order
    seen, uniq = set(), []
    for q in qs:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(q)
    return ([lambda t=t: wiki_images(t)[:4] for t in data.get("related", [])[:6]]
            + [lambda q=q: commons_images(q, 5, strict=True) for q in uniq[:12]]
            + [lambda c=c: commons_images(f"{c} World War II soldiers", 4, strict=True)
               for c in data.get("countries", [])[:4]])


def _ascii_title(t):
    """Japanese battleship Fusō → Fuso (Commons search often uses ASCII)."""
    return unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().strip()


def main_images(article):
    """Article images first (correct subject). Commons as filler with WW2 bias; never return empty if Commons has anything."""
    main = wiki_images(article, limit=MAX_IMAGES)
    base = article.split("(")[0].strip()
    ascii_base = _ascii_title(base)
    if len(main) >= 5:
        return main
    extra = []
    queries = [
        f"{base} World War II", f"{base} 1944", f"{base} 1941",
        f"{ascii_base} World War II", f"{ascii_base} 1944", ascii_base,
        f"{base} battleship", f"{base} warship", f"{ascii_base} battleship",
        f"{base} tank", f"{base} aircraft", f"{base} artillery",
    ]
    # first pass: strict period; second pass: loose if still too few
    for strict in (True, False):
        for q in queries:
            if len(main) + len(extra) >= MAX_IMAGES:
                break
            extra += commons_images(q, 5, strict=strict)
        if len(main) + len(extra) >= 3:
            break
    seen = {u.split("/")[-1].lower() for u, _ in main}
    for item in extra:
        key = item[0].split("/")[-1].lower()
        if key not in seen:
            seen.add(key)
            main.append(item)
    return main[:MAX_IMAGES]


def interleave(main, extras, need):
    """Main photos first (lead + map), then mix in related/context photos, no duplicates."""
    seen, result, rest, pools = set(), [], main[3:], [list(p) for p in extras if p]

    def add(item):
        key = item[0].split("/")[-1].lower()
        if key not in seen and len(result) < need:
            seen.add(key)
            result.append(item)

    for item in main[:3]:
        add(item)
    while len(result) < need and (rest or any(pools)):
        for p in pools + [rest]:
            if p:
                add(p.pop(0))
    return result


def download(url, name):
    """A picture to work/; Wikimedia answers 429 (too many requests) to bursts: wait and try again, up to 4 times
    (Oct 22: the DD tank story lost 4 of 32 hand-picked pictures to a single 429 each)."""
    p = W / name
    for attempt in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = r.headers.get("Retry-After", "")
                time.sleep(min(float(wait) if wait.isdigit() else 4 * 2 ** attempt, 30) + random.random() * 2)
                continue
            r.raise_for_status()
            p.write_bytes(r.content)
            subprocess.run(["ffprobe", "-v", "error", str(p)], check=True, capture_output=True)
            return p.resolve()
        except requests.RequestException as e:
            if attempt == 3 or isinstance(e, requests.HTTPError):   # 404/403: trying again won't help
                print("skip image:", e)
                return None
            time.sleep(3 * (attempt + 1))
        except Exception as e:
            print("skip image:", e)
            return None


SAFETY = pathlib.Path("safety.json")                   # picture key -> verdict, so nothing is checked twice
CHECK_V = 3                                            # +1 when the check's rules change (2 = v1.85 museums/memorials,
                                                       # 3 = v1.89 cover: the most massive thing, most intense moment)


def verdict(v):
    """Cached verdict -> dict; old caches stored only True/False (safe). "a": shows a machine or soldiers."""
    return {"a": True, **v} if isinstance(v, dict) else {"s": bool(v), "h": 0, "c": False, "a": True}


def check_images(items):
    """items [(path, key, credit)] -> {key: {"s": safe, "h": hook 1-10, "c": title card/blank}}. Gemini looks at all
    new pictures of a video in ONE request (cached by key): graphic content, text/blank frames, and how strongly
    each would stop a scroll as the first frame. Unsure, unreadable or unavailable = not safe."""
    import base64
    try:
        cache = json.loads(SAFETY.read_text(encoding="utf-8"))
    except Exception:
        cache = {}
    fresh = lambda k: isinstance(cache.get(k), dict) and cache[k].get("v", 0) >= CHECK_V   # v1.86: verdicts from
    todo = list({it[1]: it for it in items if not fresh(it[1])}.values())    # before the museum rule: again
    for i in range(0, len(todo), 24):                # up to 24 pictures per request (= all of one video)
        parts, keys = [], []
        for p, key, _ in todo[i:i + 24]:
            small = p.with_name(p.stem + "_check.jpg")
            try:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(p), "-vf", "scale=384:-2",
                                "-frames:v", "1", str(small)], check=True)
                parts += [{"text": f"Image {len(keys)}:"},
                          {"inline_data": {"mime_type": "image/jpeg",
                                           "data": base64.b64encode(small.read_bytes()).decode()}}]
                keys.append(key)
            except Exception:
                pass
        if not keys:
            continue
        n = len(keys)
        try:
            d = gemini(f"For each of the {n} numbered images return four lists in the same order (Image 0 first):\n"
                       "- graphic: true ONLY if it clearly shows dead bodies, corpses, human remains, skeletal or "
                       "starving people, executions or hangings. Soldiers in combat, wounded (but living), damaged "
                       "vehicles, explosions and battle scenes are NOT graphic.\n"
                       "- modern: true if the photo is CLEARLY post-1950 modern military equipment (modern digital "
                       "camo, wheeled self-propelled guns from the 2000s, drones, jet fighters with afterburners, "
                       "smartphones, LED lights, modern trucks), OR any photo taken after 1950 of WW2 things: a "
                       "restored tank or plane at a museum, show or reenactment (modern clothes, modern colour "
                       "photo), a memorial, monument or statue, a modern view of a battlefield or city. Black-and-white or period color WW2 tanks, guns, "
                       "aircraft, ships and soldiers are NOT modern even if the photo was scanned recently.\n"
                       "- card: true if it is mostly text, a title card, a blank or nearly black frame;\n"
                       "- hook: 1-10, how strongly it would stop someone scrolling as the FIRST frame (the cover) "
                       "of a video: 9-10 = the most massive machine (tank, ship, aircraft, big gun) at its most "
                       "intense moment (firing, burning, exploding, charging), big and sharp; 6-8 = a big machine "
                       "in action or a dramatic moment; 4-5 = a machine standing still or a face; 1-3 = maps, "
                       "documents, blurry or tiny subjects;\n"
                       "- action: true if a tank, gun, aircraft, ship, vehicle or soldiers are clearly visible (not a "
                       "talking head, a crowd of civilians, a map, a document or an empty landscape).\n"
                       'Return JSON {"graphic": [...], "modern": [...], "card": [...], "hook": [...], "action": [...]}',
                       lambda d: isinstance(d, dict) and isinstance(d.get("graphic"), list) and len(d["graphic"]) == n,
                       rounds=3, extra=parts, purpose="image check", models=LITE_FIRST)
            card = d.get("card") if isinstance(d.get("card"), list) and len(d["card"]) == n else [False] * n
            hook = d.get("hook") if isinstance(d.get("hook"), list) and len(d["hook"]) == n else [0] * n
            act = d.get("action") if isinstance(d.get("action"), list) and len(d["action"]) == n else [True] * n
            mod = d.get("modern") if isinstance(d.get("modern"), list) and len(d["modern"]) == n else [False] * n
            for key, g, m, c, h, a in zip(keys, d["graphic"], mod, card, hook, act):
                # graphic always out; modern only when model is sure (True), unsure/None → keep
                # (B&W PD scans of WW2 ships must not be dropped as "modern")
                cache[key] = {"v": CHECK_V, "s": (g is not True) and (m is not True), "c": c is True,
                              "h": int(h) if isinstance(h, (int, float)) else 0, "a": a is not False}
        except SystemExit:
            print("image check unavailable: keeping pictures that passed the filename/metadata filter")
    try:
        SAFETY.write_text(json.dumps(dict(list(cache.items())[-4000:]), indent=0), encoding="utf-8")
    except Exception:
        pass
    # unchecked (Gemini down) → allow if it already passed SENSITIVE/SKIP_IMG
    out = {it[1]: verdict(cache[it[1]]) if it[1] in cache else {"s": True, "h": 5, "c": False, "a": True}
           for it in items}
    for p, key, credit in items:
        if not out[key]["s"]:
            print("skip picture (graphic/modern):", credit[:60])
    return out


def safe_images(items):
    """items [(path, url, credit)] -> only the safe ones."""
    v = check_images(items)
    return [it for it in items if v[it[1]]["s"]]


# ---- Archive film from Wikimedia Commons ------------------------------------------------------------
def video_item(name, info):
    """(download url, credit) for a free, non-graphic film on Commons; a small transcode when one exists."""
    meta = info.get("extmetadata", {})
    about = " ".join([name] + [re.sub(r"<[^>]+>", " ", str(meta.get(k, {}).get("value", "")))
                               for k in ("Categories", "ImageDescription", "ObjectName")])
    lic = meta.get("LicenseShortName", {}).get("value", "")
    if SENSITIVE.search(about) or not re.search(r"public domain|^pd|cc0|cc[ -]by", lic, re.I) \
            or info.get("width", 640) < 320 or not 6 <= float(info.get("duration") or 60) <= 3600:
        return None
    dur, options = float(info.get("duration") or 300), []
    for dv in info.get("derivatives") or []:         # Commons transcodes: 360p/480p/720p webm
        tag = f"{dv.get('transcodekey', '')} {dv.get('title', '')} {dv.get('shorttitle', '')}"
        h = dv.get("height") or int((re.search(r"(\d{3,4})[pP]", tag) or [0, 0])[1])
        if dv.get("src") and 300 <= h <= 720:
            bps = float(dv.get("bandwidth") or {360: 4e5, 480: 7e5}.get(h, h * 2000))
            options.append((abs(h - 480), bps * dur / 8, dv["src"]))
    fits = [o for o in options if o[1] <= 55e6]      # 480p if the whole film stays under ~55 MB, else 360p
    url = min(fits)[2] if fits else None
    if not url and info.get("size", 1e12) < 60e6:   # no transcode: the original if it is small enough
        url = info.get("url")
    if not url:
        return None
    artist = re.sub(r"<[^>]+>", "", html.unescape(meta.get("Artist", {}).get("value", ""))).strip()[:60]
    page = info.get("descriptionshorturl") or info.get("descriptionurl") or ""
    return url, f"Film: {name[:60]} ({artist + ', ' if artist else ''}{lic}) {page}".strip()


def commons_videos(query, need=3):
    """Free archive films on Wikimedia Commons for a search, best matches first."""
    pages = []
    for prop, key in (("videoinfo", "viprop"), ("imageinfo", "iiprop")):   # videoinfo also lists small transcodes
        try:
            pages = requests.get(COMMONS, headers=UA, timeout=60, params={
                "action": "query", "format": "json", "formatversion": 2, "generator": "search",
                "gsrsearch": f"{query} filetype:video", "gsrnamespace": 6, "gsrlimit": 12, "prop": prop,
                key: "url|size|extmetadata" + ("|derivatives" if prop == "videoinfo" else "")}).json()["query"]["pages"]
        except Exception:
            pages = []
        if any(p.get(prop) for p in pages):
            break
    out = []
    for p in sorted(pages, key=lambda p: p.get("index", 99)):
        info = (p.get("videoinfo") or p.get("imageinfo") or [{}])[0]
        item = video_item(p.get("title", "").replace("File:", "").rsplit(".", 1)[0], info) if info else None
        out += [item] if item else []
        if len(out) >= need:
            break
    return out


def film_found(topic):
    """ONE FACT: is there free archive film of the subject on Commons? (one search, no Gemini)"""
    if not FOOTAGE or KIND != "single":
        return False
    found = commons_videos(re.sub(r"\(.*?\)", "", topic["articles"][0]).strip(), need=1)
    print("one fact: archive film of the subject", "found" if found else "not found")
    return bool(found)


def film_jobs(data, topic):
    """Film searches: the subject first (with WW2 bias), then the story's photo searches."""
    if not FOOTAGE or KIND != "single":
        return []
    subject = re.sub(r"\(.*?\)", "", topic["articles"][0]).strip()
    queries = [f"{subject} World War II", subject]
    queries += [q for q in data.get("image_queries", [])[:3] if isinstance(q, str)]
    # dedupe
    seen, uniq = set(), []
    for q in queries:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(q)
    return [lambda q=q: commons_videos(q) for q in uniq]


def download_video(url, name, cap=60_000_000):
    """Streams a film to work/ (max 60 MB); None if it fails or is too short."""
    p = W / name
    try:
        with requests.get(url, headers=UA, timeout=(15, 90), stream=True) as r:
            r.raise_for_status()
            size = 0
            with open(p, "wb") as f:
                for chunk in r.iter_content(1 << 20):
                    size += len(chunk)
                    if size > cap:
                        raise ValueError("film too big")
                    f.write(chunk)
        return p.resolve() if probe_duration(p) >= 6 else None
    except Exception as e:
        print("skip film:", type(e).__name__, str(e)[:80])
        p.unlink(missing_ok=True)


def film_stats(path, ss, length):
    """(mean brightness, crop "w:h:x:y" without black borders) of a stretch of film."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{ss:.2f}", "-t", f"{length:.2f}", "-i", str(path),
                          "-vf", "fps=4,cropdetect=24:2:0,signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                          "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    lum = [float(x) for x in re.findall(r"YAVG=([\d.]+)", log)]
    crops = re.findall(r"crop=(\d+:\d+:\d+:\d+)", log)
    return (min(lum) if lum else 0.0), (crops[-1] if crops else None)


def prepare_film(path, credit, url, need=SHOT_SEC + 1.5):
    """A usable stretch of a film: skips the opening titles, avoids dark frames, cuts away black borders.
    Returns {"path", "ss", "crop", "credit", "frames": [(jpg, key, credit)]} or None."""
    dur = probe_duration(path)
    if dur < need + 2:
        return None
    for _ in range(4):
        ss = random.uniform(dur * 0.1, max(dur * 0.1, dur * 0.85 - need))
        lum, crop = film_stats(path, ss, need)
        if lum > 28:
            frames = []
            for j, t in enumerate((ss + 0.3, ss + need / 2, ss + need - 0.4)):
                jpg = path.with_name(f"{path.stem}_f{j}.jpg")
                if subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(path),
                                   "-frames:v", "1", "-vf", "scale=640:-2", str(jpg)]).returncode == 0:
                    frames.append((jpg, f"{url}@{t:.1f}", credit))
            if len(frames) == 3:
                return {"path": path, "ss": ss, "crop": crop, "credit": credit, "frames": frames}
    return None


def get_images(data, topic, need):
    """Pictures for each side (versus has two) and archive film clips. Main article photos first, then
    related/context photos; lists and downloads run in parallel; one Gemini request checks every new picture and
    film frame and rates which photo of the subject is the strongest first frame (it moves to the front).
    Returns ([paths per side], credits, clips)."""
    arts = topic["articles"]
    fjobs = film_jobs(data, topic)
    got = pmap(lambda job: job(), [lambda a=a: main_images(a) for a in arts] + extra_jobs(data) + fjobs)
    films = got[len(got) - len(fjobs):] if fjobs else []
    got = got[:len(got) - len(fjobs)] if fjobs else got
    mains, extras, n = got[:len(arts)], got[len(arts):], len(arts)
    plan = []                                         # (file name, url, credit, side, is a subject photo)
    for k, main in enumerate(mains):                  # versus: the extras are split between both sides
        subject = {u for u, _ in main}
        picks = interleave(main, extras[k::n], (need + 1) // 2 if n > 1 else need)
        plan += [(f"{'ab'[k]}{i}{pathlib.Path(url.split('?')[0]).suffix.lower() or '.jpg'}", url, credit, k,
                  url in subject) for i, (url, credit) in enumerate(picks)]
    cands = list({u: (u, c) for fl in films for u, c in fl}.values())[:MAX_CLIPS]
    jobs = [lambda x=x: download(x[1], x[0]) for x in plan] + \
           [lambda i=i, u=u: download_video(u, f"film{i}{pathlib.Path(u.split('?')[0]).suffix or '.webm'}")
            for i, (u, _) in enumerate(cands)]
    paths = pmap(lambda job: job(), jobs)
    photo_paths, film_paths = paths[:len(plan)], paths[len(plan):]
    need_film = 10.0 if LENGTH[0] == "fact" else SHOT_SEC + 1.5  # ONE FACT ≥15 s: film can carry ~8-10 s
    prepared = [f for f in pmap(lambda a: prepare_film(a[0], a[1][1], a[1][0], need_film) if a[0] else None,
                                list(zip(film_paths, cands))) if f]
    v = check_images([(p, x[1], x[2]) for p, x in zip(photo_paths, plan) if p]
                     + [fr for f in prepared for fr in f["frames"]])
    sides, credits = [], []
    for k in range(n):
        side = [(p, x) for p, x in zip(photo_paths, plan) if p and x[3] == k and v[x[1]]["s"]]
        # last-resort: if safety wiped everything, keep non-card downloads (better than failing the run)
        if not side:
            side = [(p, x) for p, x in zip(photo_paths, plan)
                    if p and x[3] == k and not v.get(x[1], {}).get("c")]
            if side:
                print("image safety empty → keeping", len(side), "non-card downloads as fallback")
        subj = [i for i, (_, x) in enumerate(side) if x[4]]
        if subj and CATEGORY != "people":             # strongest subject photo first (ties keep the lead photo;
                                                      # people: the lead portrait stays first, Andrii, Oct 25)
            best = max(subj, key=lambda i: (v[side[i][1][1]]["h"], -i))
            side.insert(0, side.pop(best))
        sides.append([p for p, _ in side])
        credits += [x[2] for _, x in side]
    print("photos kept:", [len(s) for s in sides], "| planned:", len(plan),
          "| downloaded:", sum(1 for p in photo_paths if p))
    clips = [f for f in prepared if all(v[key]["s"] and not v[key]["c"] for _, key, _ in f["frames"])]
    acts = lambda f: sum(v[key].get("a", True) for _, key, _ in f["frames"])
    clips = sorted(clips, key=lambda f: -acts(f))          # films that show the machine / the soldiers first
    if LENGTH[0] == "fact":
        clips = [f for f in clips if acts(f) >= 2]      # the middle of a ONE FACT must show the thing
    clips = clips[:MAX_CLIPS]
    credits += [f["credit"] for f in clips]
    if fjobs:
        print("film clips:", len(clips), "of", len(cands), "found")
    return sides, credits, clips


# ---- Topic & script ----------------------------------------------------------
SEEDS = {   # famous subjects (exact English Wikipedia titles), always in the candidate pool
    "events": ["Normandy landings", "Battle of Stalingrad", "Battle of Midway", "Attack on Pearl Harbor",
               "Battle of Britain", "Dunkirk evacuation", "Battle of Kursk", "Battle of the Bulge",
               "Battle of Iwo Jima", "Battle of Okinawa", "Second Battle of El Alamein", "Operation Barbarossa",
               "Siege of Leningrad", "Operation Market Garden", "Battle of Berlin", "Battle of the Atlantic",
               "Guadalcanal campaign", "Battle of Monte Cassino", "Warsaw Uprising", "Battle of Moscow",
               "Battle of Leyte Gulf", "Last battle of the battleship Bismarck", "Doolittle Raid", "Operation Torch",
               "Dieppe Raid", "Invasion of Poland", "Battle of France", "Battle of Westerplatte",
               "Battle of the Coral Sea", "Battle of Hürtgen Forest", "Battle of Crete", "Operation Chastise",
               "Battle of Prokhorovka", "Operation Bagration", "Battle of Anzio", "Siege of Tobruk",
               "Operation Mincemeat", "Operation Fortitude", "Battle of Saipan", "Battle of the Philippine Sea",
               "St Nazaire Raid", "Atomic bombings of Hiroshima and Nagasaki", "Battle of Arnhem",
               "Battle of Iwo Jima", "Battle of Narvik", "Operation Overlord", "Battle of Kharkov"],
    "tanks": ["Tiger I", "Tiger II", "Panther tank", "T-34", "M4 Sherman", "IS-2", "KV-1", "KV-2", "Panzer IV",
              "Panzer III", "Sturmgeschütz III", "M26 Pershing", "Sherman Firefly", "Jagdpanther",
              "Panzer VIII Maus", "Elefant", "Jagdtiger", "Churchill tank", "Cromwell tank", "Comet tank",
              "Matilda II", "Valentine tank", "M18 Hellcat", "M10 tank destroyer", "M3 Lee", "M24 Chaffee",
              "SU-100", "SU-152", "ISU-152", "T-34-85", "Hetzer", "Nashorn", "Type 97 Chi-Ha"],
    "people": ["Audie Murphy", "Simo Häyhä", "Lyudmila Pavlichenko", "Vasily Zaytsev", "Desmond Doss",
               "Witold Pilecki", "Irena Sendler", "Douglas Bader", "Richard Bong", "Ivan Kozhedub",
               "Alexander Pokryshkin", "Nancy Wake", "Violette Szabo", "Juan Pujol García", "Alan Turing",
               "Chiune Sugihara", "Oskar Schindler", "Jack Churchill", "John Basilone", "Daniel Inouye",
               "Hiroo Onoda", "Raoul Wallenberg", "Georgy Zhukov", "Dwight D. Eisenhower", "Bernard Montgomery",
               "Erwin Rommel", "Chester W. Nimitz", "George S. Patton", "Isoroku Yamamoto", "Pappy Boyington",
               "Noor Inayat Khan", "Marian Rejewski", "Stanisław Skalski", "Witold Urbanowicz", "Wojtek (bear)",
               "Charles Upham", "Matt Urban", "Roza Shanina", "Lydia Litvyak", "Nadezhda Popova",
               "Adrian Carton de Wiart", "Josef František", "Leo Major", "Joseph Beyrle", "Teresa Bracco",
               "Theodore Roosevelt Jr.", "Ernest E. Evans", "Jan Karski"],
    "weapons": ["M1 Garand", "MP 40", "PPSh-41", "StG 44", "Karabiner 98k", "Mosin–Nagant",
                "Thompson submachine gun", "MG 42", "Bren light machine gun", "Lee–Enfield", "Sten",
                "M2 Browning", "8.8 cm Flak 18/36/37/41", "Katyusha rocket launcher", "Panzerfaust", "Bazooka",
                "V-2 rocket", "V-1 flying bomb", "Supermarine Spitfire", "North American P-51 Mustang",
                "Messerschmitt Bf 109", "Focke-Wulf Fw 190", "Mitsubishi A6M Zero", "Ilyushin Il-2",
                "Boeing B-17 Flying Fortress", "Boeing B-29 Superfortress", "Avro Lancaster", "Messerschmitt Me 262",
                "Junkers Ju 87", "Hawker Hurricane", "Vought F4U Corsair", "Grumman F6F Hellcat",
                "Lockheed P-38 Lightning", "Republic P-47 Thunderbolt", "de Havilland Mosquito",
                "Japanese battleship Yamato", "German battleship Bismarck", "USS Enterprise (CV-6)",
                "USS Missouri (BB-63)", "HMS Hood", "Type VII submarine", "Schwerer Gustav", "M1911 pistol",
                "Walther P38", "Luger pistol", "Browning Automatic Rifle", "M1 carbine", "PIAT", "Nebelwerfer",
                "Enigma machine", "Willys MB", "Higgins boat"],
}
SEEDS["quiz"] = SEEDS["tanks"] + SEEDS["weapons"]
SEEDS["myth"] = SEEDS["events"][:20] + SEEDS["tanks"][:12] + SEEDS["weapons"][:20] + SEEDS["people"][:12]
SEEDS["classified"] = ["Operation Mincemeat", "Operation Fortitude", "Operation Paperclip", "Unit 731",
                       "Operation Valkyrie", "Operation Anthropoid", "Operation Greif", "Operation Gunnerside",
                       "Operation Pastorius", "Operation Sea Lion", "Operation Unthinkable", "Manhattan Project",
                       "German nuclear weapons program", "Operation Tabarin", "Operation Gladio", "Project Habakkuk",
                       "Operation Bernhard", "Operation Pied Piper", "Operation Eiche", "Operation Jubilee"]
# Ranking subjects: machines/events with clear extremes the article supports (worst/most/never/only)
SEEDS["ranking"] = (SEEDS["tanks"][:18] + SEEDS["weapons"][:18] +
                    ["Royal Italian Army during World War II", "Maginot Line", "Schwerer Gustav",
                     "V-3 cannon", "Japanese battleship Yamato", "Tiger II", "Messerschmitt Me 163",
                     "Heinkel He 177", "Panzer VIII Maus", "Type 94 tankette", "Bob Semple tank",
                     "Tsar Tank", "Krummlauf", "Karl-Gerät"])
PAIRS = [("Tiger I", "M4 Sherman"), ("T-34", "Panzer IV"), ("Panther tank", "T-34"), ("IS-2", "Tiger II"),
         ("Supermarine Spitfire", "Messerschmitt Bf 109"), ("North American P-51 Mustang", "Focke-Wulf Fw 190"),
         ("Mitsubishi A6M Zero", "Grumman F6F Hellcat"), ("Japanese battleship Yamato", "Iowa-class battleship"),
         ("German battleship Bismarck", "HMS Hood"), ("M1 Garand", "Karabiner 98k"), ("PPSh-41", "MP 40"),
         ("MG 42", "M1919 Browning machine gun"), ("Thompson submachine gun", "MP 40"),
         ("Avro Lancaster", "Boeing B-17 Flying Fortress"), ("Messerschmitt Me 262", "Gloster Meteor"),
         ("Hawker Hurricane", "Supermarine Spitfire"), ("Sherman Firefly", "Tiger I"), ("Lee–Enfield", "Mosin–Nagant"),
         ("StG 44", "M1 carbine"), ("Panzerfaust", "Bazooka"), ("KV-1", "Panzer III"), ("Ilyushin Il-2", "Junkers Ju 87"),
         ("Yakovlev Yak-3", "Focke-Wulf Fw 190"), ("Vought F4U Corsair", "Mitsubishi A6M Zero"),
         ("M26 Pershing", "Panther tank"), ("Churchill tank", "Panzer IV"), ("Matilda II", "Panzer III"),
         ("Boeing B-29 Superfortress", "Avro Lancaster"), ("Bren light machine gun", "MG 42"),
         ("Katyusha rocket launcher", "Nebelwerfer"), ("Jagdpanther", "SU-100"), ("Elefant", "SU-152")]
CATS = {   # English Wikipedia categories that add more candidates (missing ones are skipped)
    "events": ["Category:Battles of World War II", "Category:Military operations of World War II"],
    "tanks": ["Category:World War II tanks", "Category:World War II tank destroyers",
              "Category:World War II assault guns"],
    "people": ["Category:World War II recipients of the Medal of Honor", "Category:Heroes of the Soviet Union",
               "Category:World War II flying aces", "Category:Female resistance members of World War II"],
    "weapons": ["Category:World War II infantry weapons", "Category:World War II fighter aircraft",
                "Category:World War II bombers", "Category:World War II battleships",
                "Category:World War II aircraft carriers", "Category:World War II artillery"],
    "quiz": ["Category:World War II tanks", "Category:World War II fighter aircraft",
             "Category:World War II battleships"],
    "myth": ["Category:World War II tanks", "Category:Military operations of World War II"],
    "classified": ["Category:Cancelled military operations of World War II", "Category:World War II espionage"],
}
NOT_LEGENDS = re.compile(r"Rudel|Wittmann|Peiper|Skorzeny|Barkmann|Heydrich|Himmler|Hitler|G[öo]ring|Goebbels|"
                         r"Mengele|Eichmann|Dirlewanger|Bormann|Kaltenbrunner|Tojo|Ishii|Waffen-SS|SS-", re.I)


BAD_TITLE = re.compile(r"^(list|timeline|outline|category)\b|order of battle|aftermath|casualties|in popular culture|"
                       r"bibliography|historiography|memorial|museum|monument|cemetery|commemorat|reenact|"
                       r"\((film|novel|book|song|album|video game|tv series|miniseries|documentary)\)", re.I)
PERP = re.compile(r"Waffen-SS|Schutzstaffel|\bSS[- ](officer|member|man|Obersturm|Hauptsturm|Sturmbann|Standarten)|"
                  r"Nazi Party|NSDAP|war criminal|war crimes", re.I)
TRENDING, VIEWS = {}, {}                               # title -> times above normal interest / weighted views


def page_views(titles):
    """Interest per canonical title: Wikipedia views over 30 days, boosted when the last 3 days jumped above the
    usual level (anniversaries, films, news), because that is when people search for the subject."""
    views, titles = {}, list(dict.fromkeys(titles))

    def chunk(i):
        try:
            return wiki_get(action="query", prop="pageviews", pvipdays=30,
                            titles="|".join(titles[i:i + 50]))["query"]["pages"]
        except Exception:
            return []
    for pages in pmap(chunk, range(0, len(titles), 50)):
        for p in pages:
            if not p.get("missing"):
                days = [v or 0 for _, v in sorted((p.get("pageviews") or {}).items())]
                base = sum(days[:-3]) / max(1, len(days) - 3)
                trend = (sum(days[-3:]) / 3) / max(base, 1) if len(days) > 6 else 1.0
                if trend >= 1.5 and sum(days) > 1000:
                    TRENDING[p["title"]] = round(trend, 1)
                views[p["title"]] = sum(days) * max(0.7, min(trend, 6.0)) ** 1.2
    VIEWS.update(views)
    return views


CHANNEL_TITLES = []                                    # titles of the channel's latest uploads (read at start)


def on_channel(title):
    """True if a recent upload's title already names this subject (protects even if used.json was not saved)."""
    words = [w for w in re.findall(r"[a-z0-9]+", re.sub(r"\(.*?\)", "", title.lower())) if w not in STOP]
    return bool(words) and any(set(words) <= set(re.findall(r"[a-z0-9]+", t.lower())) for t in CHANNEL_TITLES)


def is_used(title):
    t = title.lower()
    return any(t == u.lower() or t in u.lower().split(" vs ") for u in used) or on_channel(title)


def candidates(limit=30):
    """Famous seeds + category members, unused, ranked by real interest (Wikipedia views), top ones first."""
    def members(cat):
        try:
            return wiki_get(action="query", list="categorymembers", cmtitle=cat, cmtype="page|subcat",
                            cmlimit=500).get("query", {}).get("categorymembers", [])
        except Exception:
            return []
    pool, subs = list(SEEDS.get(CATEGORY, [])), []
    for got in pmap(members, CATS.get(CATEGORY, [])):  # categories and 3 random subcategories each, in parallel
        pool += [m["title"] for m in got if m.get("ns") == 0]
        sub = [m["title"] for m in got if m.get("ns") == 14]
        subs += random.sample(sub, min(3, len(sub)))
    for got in pmap(members, subs):
        pool += [m["title"] for m in got if m.get("ns") == 0]
    pool = [t for t in dict.fromkeys(pool) if not BAD_TITLE.search(t)
            and not (CATEGORY != "classified" and NOT_LEGENDS.search(t))]
    views = page_views(pool)
    if views:                                         # most viewed first, random pick among the top ones
        ranked = [t for t in sorted(views, key=views.get, reverse=True) if not is_used(t)][:limit * 2]
        top = sorted(random.sample(ranked, min(limit, len(ranked))), key=views.get, reverse=True)
        print("top candidates:", [(t, int(views[t])) for t in top[:5]], "| trending:", TRENDING)
        return top
    seeds = [t for t in SEEDS.get(CATEGORY, []) if not is_used(t)]       # fallback: seeds first
    return (random.sample(seeds, min(limit, len(seeds))) or random.sample(pool, min(limit, len(pool))))


BIG = re.compile(r"\b\d{1,3}(?:,\d{3})+\b|\b\d+(?:\.\d+)?\s+(?:million|thousand)\b", re.I)   # 1,347 / 3.8 million


def topic_of(got):
    """[(title, text)] -> topic; versus gets both articles, each shortened."""
    arts = [a for a, _ in got]
    text = got[0][1] if len(got) == 1 else "\n\n".join(f"=== {a} ===\n{x[:6500]}" for a, x in got)
    return {"articles": arts, "key": " vs ".join(arts), "text": text}


def usable(got, pair=False):
    """True for a long article that fits the channel and (single topics) was not covered yet."""
    title, text = got
    return bool(title) and len(text) > 1500 and not BAD_TITLE.search(title) and (pair or not is_used(title)) \
        and not (CATEGORY != "classified" and NOT_LEGENDS.search(title))


def drawn_topic(cands):
    """No Gemini needed: candidates are drawn at random weighted by Wikipedia interest (trending ones are already
    boosted). With SCALE the first drawn article full of big numbers wins. People outside the hand-picked list
    are skipped if their lead mentions Nazi party/SS membership or war crimes."""
    weight = lambda t: max(1.0, VIEWS.get(t, 1.0)) ** 0.8
    order = sorted(cands, key=lambda t: math.log(random.random() or 1e-12) / weight(t), reverse=True)
    good = []
    for i in range(0, min(len(order), 12), 4):       # 4 articles at a time, in parallel
        if len(good) >= 6 or (good and KIND == "quiz"):
            break
        for got in pmap(wiki_text, order[i:i + 4]):
            if not usable(got):
                continue
            if CATEGORY == "people" and got[0] not in SEEDS["people"] and PERP.search(got[1][:1500]):
                print("topic skipped (Nazi party/SS or war crimes in the lead):", got[0])
                continue
            good.append(got)
    if not good:
        return None
    pick, angle = choose_story(good) if KIND != "quiz" else (0, "")
    best = good[pick] if angle else (next((g for g in good if len(BIG.findall(g[1])) >= 3), good[0]) if SCALE else good[0])
    print("topic drawn:", best[0], "| interest:", int(VIEWS.get(best[0], 0)), "| big numbers:",
          len(BIG.findall(best[1])), "| trending:", TRENDING.get(best[0], "-"), "| angle:", angle or "-")
    return {**topic_of([best]), "angle": angle}


GENERIC = re.compile(r"^(World War (I|II)|Allies of World War II|Axis powers|United States|United Kingdom|Germany|"
                     r"Nazi Germany|Soviet Union|Empire of Japan|Japan|France|Italy|Poland|Europe|Asia|Africa|"
                     r"Adolf Hitler|Winston Churchill|Joseph Stalin|Franklin D\. Roosevelt|Benito Mussolini|"
                     r"English language|German language|\d+.*)$", re.I)


def related_context(title, text, n=3, chars=2500):
    """Openings of the articles this one leans on most (people, units, projects named again and again): the script
    sees who else took part and what came before, so a team's work is not credited to one man."""
    links, cont = [], {}
    for _ in range(4):
        try:
            d = wiki_get(action="query", prop="links", titles=title, plnamespace=0, pllimit="max", **cont)
        except Exception:
            break
        links += [l["title"] for l in d.get("query", {}).get("pages", [{}])[0].get("links", [])]
        cont = d.get("continue", {})
        if not cont:
            break
    low, score = text.lower(), {}
    for t in links:
        key = re.sub(r"\s*\(.*?\)", "", t).lower()
        if t != title and len(key) > 3 and not GENERIC.search(t) and not BAD_TITLE.search(t):
            c = low.count(key)
            if c >= 2:
                score[t] = c
    top = sorted(score, key=score.get, reverse=True)[:n]
    if not top:
        return ""
    try:
        pages = wiki_get(action="query", prop="extracts", exintro=1, explaintext=1, titles="|".join(top))["query"]["pages"]
    except Exception:
        return ""
    return "\n\n".join(f"=== {p['title']} ===\n{p['extract'][:chars]}" for p in pages if p.get("extract"))


def research(topic):
    """Adds the related articles to the allowed facts (one topic, not versus)."""
    if len(topic["articles"]) != 1:
        return topic
    ctx = related_context(topic["articles"][0], topic["text"])
    if ctx:
        print("research: +", len(ctx), "chars from", re.findall(r"=== (.+?) ===", ctx))
        topic = {**topic, "text": topic["text"] + "\n\nRELATED ARTICLES (context, also allowed facts):\n" + ctx}
    return topic


def choose_story(good):
    """One Gemini call picks the candidate with the most gripping TRUE story and the angle to tell it from."""
    if len(good) < 2:
        return 0, ""
    lst = "\n\n".join(f"[{i}] {t}\n{x[:1200]}" for i, (t, x) in enumerate(good))
    fact = LENGTH[0] == "fact"
    ask = ("You pick topics for a World War II YouTube Shorts channel watched mostly by American men who love "
           "military history. From these Wikipedia subjects pick the ONE that makes the most gripping "
           + ("15-18 second ONE FACT Short: a single surprising, little-known, TRUE and visual detail told in a few "
              "tight sentences (a hidden feature, a strange design choice, an odd origin or maker, an unexpected use, "
              "a trick or a fatal flaw), e.g. 'The Flak 88 was built to shoot down planes, then it hunted tanks.' "
              if fact else
              "22-28 second story: ONE surprising, little-known but TRUE detail or turn of events with a clear payoff "
              "(a hidden feature, a trick, a mistake, an odd origin, an unexpected use), not a biography, not a "
              "summary and not a list of specifications. ")
           + ("Prefer stories with big concrete numbers. " if SCALE else "")
           + "Avoid angles a historian would call misleading: one person credited for a team's work, popular myths, "
           f"exaggerations.\nCandidates:\n{lst}\nReturn JSON: {{\"pick\": number, \"angle\": \"one sentence: the "
           f"surprising true {'fact' if fact else 'story'} to tell, using only facts from that article\"}}")
    try:
        d = gemini(ask, lambda d: isinstance(d, dict) and str(d.get("pick", "")).isdigit()
                   and int(d["pick"]) < len(good), rounds=2, purpose="topic")
        pick = int(d["pick"])
        return (pick, str(d.get("angle", ""))[:300]) if 0 <= pick < len(good) else (0, "")
    except (SystemExit, KeyError, ValueError, TypeError):
        return 0, ""


def versus_topic():
    """A classic match-up nobody has seen on the channel yet (no Gemini)."""
    pairs = [p for p in PAIRS if " vs ".join(p) not in used and " vs ".join(p[::-1]) not in used
             and not (on_channel(p[0]) and on_channel(p[1]))]
    for pair in random.sample(pairs, min(4, len(pairs))):
        got = pmap(wiki_text, pair)
        arts = [a for a, _ in got]
        if all(usable(g, pair=True) for g in got) and arts[0] != arts[1] \
                and " vs ".join(arts) not in used and " vs ".join(arts[::-1]) not in used:
            print("versus drawn:", " vs ".join(arts))
            return topic_of(got)
    return None


def pick_topic():
    """Battles, tanks, people, weapons, quiz and versus are drawn without Gemini; myth and classified (which need
    judgement) and anything the draw cannot fill go to Gemini."""
    cands = None
    if KIND == "versus":
        t = versus_topic()
    elif CATEGORY in ("myth", "classified"):
        t = None
    else:
        cands = candidates()
        t = drawn_topic(cands)
    return t or gemini_topic(cands)


def gemini_topic(cands=None):
    keys = ["article", "article2"] if KIND == "versus" else ["article"]
    if KIND == "versus":
        pairs = [f"{a} vs {b}" for a, b in PAIRS if f"{a} vs {b}" not in used and f"{b} vs {a}" not in used]
        ask = (f"Suggest ONE pair for a World War II comparison Short: {TOPIC}. Each must have its own detailed "
               "English Wikipedia article with photos. "
               + (f"Strongly prefer one of these famous match-ups: {random.sample(pairs, min(15, len(pairs)))}. "
                  if pairs else ""))
        fmt = ('{"article": "exact English Wikipedia title of the first", '
               '"article2": "exact English Wikipedia title of the second"}')
    else:
        ask = ("Suggest ONE specific World War II subject for a YouTube Short. It must have its own detailed "
               f"English Wikipedia article with photos. Category: {TOPIC}. "
               + ("Strongly prefer subjects of huge scale with big, concrete numbers in the article (millions of "
                  "soldiers, thousands of tanks or aircraft, record production, giant distances). " if SCALE else ""))
        fmt = '{"article": "exact English Wikipedia article title"}'
        cands = candidates() if cands is None else cands
        if len(cands) >= 5:
            ask += (f"Choose ONLY from this list of exact page titles, most popular first: {cands}. Prefer the "
                    "famous, high-impact subjects history fans search for most (near the top of the list) and "
                    "tell them from a fresh angle. ")
            hot = {t: x for t, x in TRENDING.items() if t in cands}
            if hot:
                ask += f"Trending right now (interest x times above normal), a strong choice: {hot}. "
    for _ in range(5):
        t = gemini(ask + f"Do NOT use any of these: {used[-150:]}. Also not the subjects of these recent "
                         f"videos: {CHANNEL_TITLES[:30]}. Return JSON: {fmt}",
                   lambda d: isinstance(d, dict) and all(d.get(k) for k in keys), purpose="topic")
        got = pmap(wiki_text, [t[k] for k in keys])
        arts = [a for a, _ in got]
        if all(usable(g, pair=len(keys) > 1) for g in got) and len(set(arts)) == len(keys) \
                and " vs ".join(arts) not in used and " vs ".join(arts[::-1]) not in used:
            return topic_of(got)
        print("topic rejected:", t)
    raise SystemExit("No usable Wikipedia article")


def plain(t):
    return re.sub(r"\[/?[ry]\]", "", str(t)).strip()


def clean(t):
    return str(t).replace("\\", "").replace("{", "").replace("}", "").replace("\n", " ")


def to_ass(t):
    t = clean(t)
    for tag, col in (("r", RED), ("y", YELLOW)):
        t = re.sub(rf"\[{tag}\](.*?)\[/{tag}\]", lambda m: f"{{\\c{col}}}{m.group(1)}{{\\c{WHITE}}}", t)
    return plain(t)


def all_lines(data):
    """Spoken lines; the viewer question lives in the description and comment, so the end can loop."""
    return [l for l in data.get("lines", []) if plain(l)]


STOP = {"the", "of", "and", "battle", "operation", "siege", "tank", "class", "battleship", "aircraft", "rifle", "gun",
        "german", "japanese", "british", "soviet", "american", "italian", "machine", "submachine", "uss", "hms"}


def key_words(topic):
    """Searchable words of the subject's name, e.g. 'Battle of Stalingrad' -> Stalingrad."""
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9-]*", " ".join(re.sub(r"\(.*?\)", "", a) for a in topic["articles"]))
    return [w for w in words if len(w) > 2 and w.lower() not in STOP] or words


def cold_rules():
    """The cold-open format: climax first, rewind, the story up to it, a complete answer that flows into line 1."""
    return ("- COLD OPEN FORMAT: the video starts AT the climax, rewinds like a tape, then shows how it came to "
            "that and gives a clear answer.\n"
            "- headline: the cold open, max 8 words, present tense: the climax moment told as a mystery or a paradox "
            "the video answers, e.g. 'This carrier should be at Pearl Harbor.' or 'Pearl Harbor is burning. Japan "
            "already missed.' It is spoken FIRST, then the picture rewinds. Never 'Did you know', never a question "
            "that line 1 answers.\n"
            "- lines: exactly 6, max 12 words each, present tense, headline + lines = 55-75 words:\n"
            "  1) the time jump back from the climax, starting with exactly how long before it, from the source's "
            "dates, e.g. '[r]11 days[/r] earlier, 6 Japanese carriers sail for Hawaii in secret.';\n"
            "  2) the stakes: the plan, the target or what everyone expects;\n"
            "  3) the twist, starting with 'But';\n"
            "  4) the reason almost nobody knows: it answers the headline's mystery;\n"
            "  5) the payoff: the concrete result with a number;\n"
            "  6) the conclusion: ONE complete sentence that answers the headline and ends on the headline's subject, "
            "so the replay flows into the headline (e.g. 'One day of bad weather saved the carrier that turned the "
            "war.' -> 'This carrier should be at Pearl Harbor.'). No goodbye, no question.\n"
            "- plates: documentary time stamps on screen, CAPITALS, max 32 characters, only dates, times, places and "
            "distances that are in the source: one for the headline (line 0: date and time of the climax, plus "
            "'red': a 2-4 word status, e.g. 'PEARL HARBOR UNDER ATTACK'), one for line 1 (date and place the story "
            "jumps back to, e.g. 'NOV 26, 1941 · HITOKAPPU BAY'), optionally one for line 4.\n"
            "- cards: 0-2 list cards that make the story visual, only if the story names 2-6 things of one kind from "
            "the source (ships, units, targets, aircraft). A card appears on a word ('at') of its line; later its "
            "'mark' hits some items on a word of the mark line: style 'stamp' stamps a short label next to each "
            "marked item (max 3 items, e.g. 'NOT HERE'); style 'strike' strikes them through with the label under "
            "them (up to 6 items, e.g. 'SUNK'). Items: names in CAPITALS, max 14 characters, spelled as in the "
            "source. Item numbers start at 1. The marks must match the narration exactly.\n"
            "- alarm: true only if the climax is an air raid or a bombing (a siren plays under the cold open).\n")


def map_rules():
    """The map hook: the headline points at a real place; the map, its routes and the distance come from the source."""
    return ("- MAP OPENING: the video opens on a real map that zooms into the place where it happened, with a red "
            "target on it. The headline points at that place, max 8 words, e.g. 'This tiny island decided the "
            "Pacific War.' or 'This quiet bay hid 6 aircraft carriers.' Describe the place, never say 'this map'.\n"
            "- map.places: 2-4 places named in the source, each with its exact English Wikipedia article title (an "
            "article with coordinates: an island, a city, a bay, a port, a base or a battlefield; never a person or a "
            "whole country, a whole sea or an ocean: use the bank, strait, island or port). The FIRST place is the "
            "target: where the headline's main event happened (the battle, the sinking, the raid), not the base the "
            "forces left from; the headline points at it. The places are at least 100 km "
            "apart: never a town on the target island or inside the target city. label: its short name in "
            "CAPITALS as the source spells it, max 16 characters.\n"
            "- map.routes: 0-2 movements the narration describes (a fleet sailing, an army advancing, a raid): "
            "'from' (where the force came from: a port, a base, a country's coast) and 'to' are place numbers "
            "starting at 1, 'side' is 'axis', 'allied' or 'other', 'label' max 3 "
            "words in CAPITALS (e.g. 'JAPANESE FLEET'), 'line' = the narration line that describes it (1 = the "
            "first line after the headline). The route appears on screen while that line is spoken.\n"
            "- map.distance: only if the source states the distance between two of the places: from, to, the label "
            "with the number and unit exactly as in the source (e.g. '1,300 MILES') and its line; otherwise null.\n")


def json_keys(hook):
    """The JSON the script must come back as (the cold open adds time stamps, list cards and the siren flag; the
    map hook adds the places, routes and distance on the map)."""
    if hook == "map":
        return JSON_KEYS[:-1] + (', "map": {"places": [{"title": "Midway Atoll", "label": "MIDWAY"}, {"title": '
                                 '"Pearl Harbor", "label": "PEARL HARBOR"}, {"title": "Hashirajima", "label": '
                                 '"HASHIRAJIMA"}], "routes": [{"from": 3, "to": 1, "side": "axis", "label": '
                                 '"JAPANESE FLEET", "line": 2}], "distance": {"from": 1, "to": 2, "label": '
                                 '"1,300 MILES", "line": 1}}}')
    if hook != "coldopen":
        return JSON_KEYS
    return JSON_KEYS[:-1] + (', "plates": [{"line": 0, "text": "DEC 7, 1941 · 07:48", "red": "PEARL HARBOR UNDER '
                             'ATTACK"}, {"line": 1, "text": "NOV 26, 1941 · HITOKAPPU BAY"}], "cards": [{"line": 2, '
                             '"at": "America\'s", "title": "TARGET LIST", "items": ["ENTERPRISE", "LEXINGTON", '
                             '"SARATOGA"], "mark": {"line": 3, "at": "all", "label": "NOT HERE", "items": [1, 2, 3], '
                             '"style": "stamp"}}], "alarm": false}')


def script_rules(hook, recent):
    """Everything a script must do, shared by the writer and the editor."""
    cold, mp, fact = hook == "coldopen", hook == "map", LENGTH[0] == "fact"
    r = (cold_rules() if cold else map_rules() if mp else
         "- headline: the hook, max 10 words, spoken FIRST and shown on screen the whole time: it asks viewers to "
         "name the machine without naming it, in plain words, no numbers (e.g. 'Can you name this heavy British "
         "tank?').\n" if KIND == "quiz" else
         "- headline: the hook, max 10 words, spoken FIRST and shown on screen the whole time. "
         "A scrolling viewer must get it in under 1 second with no knowledge of the war. "
         "NO numbers in the headline (a name like T-34 or Flak 88 is fine), no abbreviations, no jargon. "
         "Never start with 'Did you know', 'In World War II', 'Imagine', 'Have you ever' or 'This is'.\n")
    r += ("- HOOK RULES (non-negotiable for virality):\n"
          "  • First 4–6 words must create a gap, paradox, shock or contradiction.\n"
          "  • Never start with the plain name of the subject alone ('The Tiger I...').\n"
          "  • Prefer present tense and concrete visual language.\n"
          "  • The headline must be understandable with the sound OFF (on-screen text is the first filter).\n"
          "  • If the hook type is shock_claim / nobody_knows / wrong / one_detail / you_inside — "
          "the first line after the headline must immediately raise the stakes or deepen the mystery.\n"
          "- title, headline and first words share the same key words and open a question; they never reveal "
          "the payoff.\n")
    if fact:
        r += ("- lines: 2-3 narration lines after the headline, max 14 words each; headline + lines = 40-55 words "
              "(about 15-18 seconds). ONE FACT FORMAT: one surprising fact told in full; no long set-up, no biography. "
              "Line 1 says how or why in concrete visual words; add one more concrete detail; the last line is the "
              "punchline. Never write fewer than ~40 words — the video must be at least 15 seconds.\n")
    elif not cold:
        r += ("- lines: 3-4 narration lines after the headline, max 12 words each; headline + lines = 42-58 words "
              "(about 15-20 seconds). SHORT FORMAT: no set-up line, start with the strongest fact; squeeze the beats "
              "into the decisive fact, the twist and the payoff. Never under ~40 words (15 seconds).\n"
              if LENGTH[0] == "short" else
              "- lines: 4-6 narration lines after the headline, max 12 words each; headline + lines = 55-70 words "
              "(about 22-28 seconds).\n")
    r += ("- PEOPLE, NOT SPECS: tell what it meant for the men who used it or faced it; if the source describes "
          "what they felt or endured (cold, cramped, deafening noise, mud, fear), use it, never invent it.\n"
          "- Line 1 right after the headline brings the CONFLICT or the MYSTERY (a problem, a danger, a 'but'), "
          "not background or context.\n")
    r += ("- DELIVER THE PROMISE: the headline asks a question or makes a promise; EVERY line moves toward answering "
          "exactly that, and the peak line gives the concrete answer (the tactic, the reason, the number). Never "
          "drift to another topic, biography, politics or what happened years later.\n"
          "- Every line adds NEW information and pulls forward to the next (but, until, then, so). No filler, no "
          "recap, no greeting, never ask to like or subscribe.\n")
    if not cold and not fact:
        r += ("- RE-HOOK (mandatory): around the middle, one line MUST open a new question with a twist, contradiction "
              "or surprising 'But...' / 'Until...' / 'Then...' that the viewer did not expect from the headline. "
              "Without a mid-video re-hook retention collapses.\n")
    r += ("- ACCURACY OVER DRAMA: never credit one person with what a team, a unit or earlier work achieved. If the "
          "texts name collaborators, a team or an earlier breakthrough, say so (e.g. 'Turing and the Bletchley Park "
          "team, building on Polish codebreakers'). Never 'alone', 'single-handedly', 'one man', 'by himself' or "
          "'won the war' unless the text says exactly that; prefer the precise claim ('helped shorten the war'). "
          "No popular myths. Fans check everything and call out exaggerations in the comments.\n"
          + ("- NUMBERS: at most " + ("1 number" if fact else "2 numbers") + " in the whole script, never in the "
             "headline, and only when the number IS the surprise. Make it felt with a plain comparison the source "
             "supports (e.g. 'twice as heavy as a Sherman' only if both weights are in the source). No spec lists: "
             "no armor millimeters, calibers, ranges or production totals just to sound precise.\n"
             if not SCALE else "- A number in the headline counts something impressive (2 or more); never '1 man', "
             "'1 cipher'.\n"))
    r += ("- Information gain: skip the most repeated fact about this famous subject; tell the detail most fans "
         "have never heard.\n" if fact else
         "- Information gain: skip the most repeated fact about this famous subject. Connect 2-3 facts from the "
         "source into one insight the source never states in a single sentence (e.g. '...which means...').\n")
    r += ("- SOUND HUMAN (no AI tells): no 'not X, but Y' framing, no lists of three for rhythm, no inflated "
          "significance ('changed history forever', 'a testament to', 'pivotal', 'legacy'), no AI words (delve, "
          "tapestry, crucial, remarkable, unwavering, game-changer, showcase, underscore), no vague experts ('historians "
          "say'), no sales language. Say what happened, plainly, with the concrete detail.\n")
    r += ("- Write for the ear: short sentences, contractions, active voice, simple words a 14-year-old knows. No "
         "parentheses, slashes, abbreviations, military jargon or Roman numerals: write 'Tiger One', 'Panzer Four', "
         "'kilometers an hour', 'armor-piercing shells' (not APDS). Numbers as digits.\n"
         "- Neutral, educational tone; no glorification of any regime; losses only as numbers, never graphic.\n"
         "- In the headline and in every line wrap the single most important detail (name, number or date) in "
         "[r]...[/r] and at most one secondary detail in [y]...[/y].\n")
    if KIND == "quiz":
        r += ("- The headline asks viewers to guess; the clues get stronger line by line; only the LAST line names "
              "it. The title must not reveal it either.\n")
    elif not cold:
        r += (f"- Hook type for this video: {HOOKS.get(hook, HOOKS['curiosity'])}.\n"
              + ("" if fact else "- The second-to-last line is the peak: the most surprising fact.\n")
              + ("- PART 1 OF 2: cover only the build-up and the first turning point; do NOT reveal the final "
                 "outcome. The LAST line is a cliffhanger that makes viewers want Part 2 (e.g. 'But nobody saw "
                 "what was coming next.'). No goodbye. The title ends with '(Part 1)'.\n" if PART == 1 else
                 f"- PART 2 OF 2: Part 1 ended with: \"{SERIES_INFO.get('last', '')}\". Pick up right after that "
                 "cliffhanger: what happened next, the outcome in numbers and why it mattered; do not repeat Part 1. "
                 "The title ends with '(Part 2)'.\n" if PART == 2 else "")
              + ("" if PART == 1 else "- PUNCHLINE ENDING: the LAST line is a short, complete sentence (max 12 words) "
                 "that lands the consequence or irony. Prefer a callback that echoes 1-2 key words from the headline "
                 "so the loop feels intentional when the video replays. Ends with . or !. "
                 "Examples: 'So the gun built for planes ruled the desert.' / "
                 "'If it treated its own crew that way, imagine the other side.' "
                 "No question, no cliffhanger, no summary, no goodbye.\n"
                 if LOOP == "punch" else
                 "- SEAMLESS LOOP: the LAST line is an unfinished bridge with no final punctuation that leads "
                 "straight back into the headline, so the replay sounds like one sentence (e.g. last line 'And that is "
                 "exactly how' + headline '3.8 million men lost in 6 months?'). No goodbye, no question, no summary.\n"
                 if LOOP == "bridge" else
                 "- The LAST line pays off the headline and echoes its key words (a callback), so the opening hits "
                 "differently when the video loops. No goodbye, no question, no summary in the last line.\n"))
    if SCALE and KIND != "quiz" and not cold and not mp:
        r += ("- HOOK = NUMBER + TENSION: the headline joins the most impressive number with a paradox or an open "
              "question the video answers, e.g. 'How did 3.8 million men fail in 6 months?', '1,347 tanks scared a "
              "whole army. Why?'. A big number alone is not enough; the viewer must want the answer.\n"
              "- SCALE: the video is built around big numbers. The headline contains the most impressive number in "
              "the source (soldiers, tanks, aircraft, ships, kilometers, production, days), written in digits, and at "
              f"least {2 if LENGTH[0] == 'short' else 3} lines carry a concrete number. Make numbers feel huge with a comparison from the source "
              "(e.g. 'more than the whole British army'). Losses only as totals, never graphic.\n")
    if fact and FACT_FILM[0]:
        r += ("- Archive film of the subject plays under the narration: you may point at it once with 'Watch' + the "
              "subject itself (e.g. 'Watch this gun.'), never at a detail the film may not show.\n")
    if (cold or mp) and SCALE:
        r += "- At least 2 lines carry a concrete number from the source.\n"
    if not fact:
        r += ("- If the source names a famous film, series or book about this subject, one late line may name it "
              "(e.g. 'Hollywood told this story in [y]Title (Year)[/y]').\n")
    r += ("- question: an either/or question viewers can answer in one or two words (e.g. 'Tiger or Sherman?', "
          "'Genius or reckless?'), max 10 words, no markers.\n"
          + title_rules() +
          "- American English spelling everywhere (Harbor, armor, defense): most viewers are American.\n"
          "- pronounce: for every non-English name or word in the narration, how an English voice should say it: "
          "lowercase syllables joined by hyphens, NO capitals (capitals are read letter by letter), no spaces "
          "(e.g. {\"Zhukov\": \"zhoo-koff\", \"Rokossovsky\": \"ro-ko-soff-skee\"}); {} if none.\n"
          "- summary: one plain sentence for search with the subject's full name, the year and the key fact, "
          "max 150 characters.\n"
          "- related: 2-4 exact English Wikipedia titles of people, units, places, battles or equipment named in "
          "your lines (not the main subject), to show their photos.\n"
          "- image_queries: 6-8 short English Wikimedia Commons searches that match ONLY this subject in 1939-1945. "
          "Always include the specific type + year or 'World War II' (e.g. 'Archer tank destroyer 1944', "
          "'SP 17-pounder Valentine Italy', 'British self-propelled gun 1944'). NEVER a bare modern brand alone "
          "(never just 'Archer' — that returns 2010s artillery). Prefer: full vehicle/weapon name, crew with the "
          "machine, factory, front-line photo, museum exhibit of THAT exact WW2 type.\n"
          "- countries: 1-3 countries whose forces or people are in the story.\n"
          "- tags: 8-12 search phrases people really type: the subject's full name, its short name, common alternate "
          "spellings (e.g. 'Pearl Harbour'), the subject + 'WW2', the country, the year, the theater (e.g. 'Pacific "
          "War', 'Eastern Front'); no hashtags.\n"
          f"- music: 2-4 words from this list for the background music mood: {MOODS}.\n")
    if WINNERS and not fact:
        r += (f"- These headlines got the MOST views on this channel; learn what makes them work, but do not copy "
              f"their wording or subject{'' if SCALE else ', and ignore their numbers: the headline rules above win'}"
              f": {WINNERS}\n")
    if LOSERS:
        r += f"- These got the FEWEST views; avoid their style: {LOSERS}\n"
    if recent:
        r += f"- Recent headlines on this channel; do NOT reuse their wording or sentence pattern: {recent[-25:]}\n"
    return r


JSON_KEYS = ('{"hooks": ["8 different headline options"], "headline": "...", "lines": ["...", "..."], '
             '"question": "...", "title": "...", "summary": "...", "related": ["..."], "image_queries": ["..."], '
             '"countries": ["..."], "music": ["..."], "pronounce": {"Name": "Respelling"}, "tags": ["8-12 search tags"]}')


TITLE_FORMATS = {   # title A/B formats — power words match top Shorts (NEVER / WRONG / SECRET / WORST)
    "detail": "'Subject: Hidden Detail', e.g. 'Tiger II: The Grenade Launcher on Its Roof'",
    "the_x_that_y": "'Subject: The X That Y', e.g. 'Flak 88: Built for Planes, Feared by Tanks', 'Tiger I: The Tank "
                    "That Broke Itself', 'Midway: 5 Minutes That Doomed Japan'",
    "question": "'Subject: Why/How Question', e.g. 'Tiger II: Why Crews Feared Their Own Tank'",
    "shock": "'Subject: NEVER/WRONG/SECRET claim', e.g. 'Tiger I: The Tank Crews NEVER Trusted', "
             "'Yamato: Why Japan NEVER Mass-Produced Its Best Idea', 'Maus: The Tank That Was Already Dead'",
    "versus": "'A vs B: The Real Difference', e.g. 'Tiger I vs Sherman: The Real Difference Was Not Armor'",
    "myth": "'Myth vs Truth: Subject', e.g. 'Myth vs Truth: The Invincible Tiger'",
    "ranking": "'The WORST/WEAKEST/MOST X', e.g. 'The Worst Tank Germany Ever Built', "
               "'Why This Was the Weakest Army in WW2', 'The Most Overrated Fighter of the War'",
}
TITLE_FMT = ["detail"]                                  # the format picked for this video


def pick_title_format():
    """Versus, myth, quiz, ranking have fixed formats; the rest rotate (detail / the_x_that_y / question / shock)."""
    if KIND == "quiz":
        return "quiz"
    if KIND == "versus":
        return "versus"
    if CATEGORY == "myth":
        return "myth"
    if CATEGORY == "ranking":
        return "ranking"
    first = {"tanks": "shock", "weapons": "shock", "events": "the_x_that_y", "classified": "shock",
             "people": "question"}.get(CATEGORY, "detail")
    opts = ["detail", "the_x_that_y", "question", "shock"]
    # shock titles (NEVER/WRONG/SECRET style) get extra weight — tops use this pattern
    weights = [2.2 if o == first else (1.6 if o == "shock" else 1.0) for o in opts]
    return random.choices(opts, weights=weights)[0]


def title_rules():
    fmt = TITLE_FMT[0]
    return ("- title (the promise for search and the feed, max 60 characters): "
            + ("asks viewers to name it without naming it, e.g. 'Can You Name This British Tank?'. "
               if fmt == "quiz" else
               f"format {TITLE_FORMATS.get(fmt, TITLE_FORMATS['detail'])}. The subject's common name is usually "
               "the first 2-3 words (or after The WORST/WEAKEST for ranking). Use ONE power word from: "
               "NEVER, WRONG, SECRET, HIDDEN, FATAL, ONLY, WORST, WEAKEST, MOST, FAILED, BROKE. "
               "Title Case is fine; at most TWO words in ALL CAPS for emphasis (NEVER / WRONG / SECRET / WORST). "
               "Everything the title promises is named and shown in the video. ")
            + "At most one number, only if it is the intrigue, and only in the second half. Never start with Did you "
            "know, In WW2, Imagine, This is, The story of. No 'You won't believe', no emojis, no hashtags, "
            "max one exclamation mark. It must NOT repeat the headline: the title is the promise, the headline "
            "is the on-screen hook.\n")


def beats_for(hook):
    return COLD_BEATS if hook == "coldopen" else FACT_BEATS if LENGTH[0] == "fact" else BEATS[CATEGORY]


def draft_prompt(topic, hook, recent):
    secs = {"fact": "15-18", "short": "15-20"}.get(LENGTH[0], "22-28")
    return ("You are a top YouTube Shorts scriptwriter for a World War II history channel narrated by a calm, "
            f'confident documentary voice. Write a {secs} second Short about "{" vs ".join(topic["articles"])}".\n'
            "Use ONLY facts stated in this Wikipedia text; keep names, dates and numbers exact:\n"
            f"<<<\n{topic['text']}\n>>>\nFormat: {STORY}\n"
            + (f"Story angle picked for this video (use it only as far as the text supports it): {topic['angle']}\n"
               if topic.get("angle") else "")
            + f"Beats (about one line each): {beats_for(hook)}\n"
            f"Rules:\n{script_rules(hook, recent)}"
            "First write 8 different headline options in 'hooks' (different angles: hidden detail, flaw, origin, irony, "
            "conflict), then use the one that would stop the scroll "
            f"best as 'headline'. Return JSON: {json_keys(hook)}")


def editor_prompt(topic, hook, recent, draft, issues):
    return ("You are the editor and fact-checker of a World War II Shorts channel. Make this script as gripping "
            "and as accurate as possible and return the final version.\n"
            f"SOURCE, the only allowed facts:\n<<<\n{topic['text']}\n>>>\n"
            f"Format: {STORY}\nBeats: {beats_for(hook)}\n"
            f"Rules:\n{script_rules(hook, recent)}"
            f"DRAFT:\n{json.dumps(draft, ensure_ascii=False)}\n"
            + ("PROBLEMS FOUND BY THE CHECKER, fix every one:\n- " + "\n- ".join(issues) + "\n" if issues else "")
            + "Checklist: 1) every name, number, date and claim is in the SOURCE; fix or delete anything else. "
            "2) The headline is the strongest scroll-stopper (improve it or take a better option from 'hooks'). "
            "3) Every line serves the headline's promise and the peak answers it; cut drift, filler, biography. "
            + ("4) The 6 lines follow the cold-open order and the last one answers the headline. "
               "5) Plates and cards use only names, dates and places from the SOURCE and match the narration. "
               if hook == "coldopen" else "4) ONE fact only, nothing else. 5) The last line is the punchline. "
               if LENGTH[0] == "fact" else "4) One re-hook in the middle. 5) The ending follows the rules; the map places, "
               "routes and distance are named in the SOURCE and match the narration. " if hook == "map" else
               "4) One re-hook in the middle. 5) The ending follows the rules. ")
            + "6) It sounds natural read aloud. 7) Word limits and markers. 8) Read it as a World War II historian "
            "writing a comment would: put in 'objections' everything they would call wrong, exaggerated or "
            "misleading (one man credited for a team's work, missing context, myths) and fix each one.\n"
            f"Return JSON with the same keys: {json_keys(hook)[:-1]}, "
            '"objections": ["what a historian would criticise and how you fixed it"], '
            '"claims": [{"claim": "each factual claim in the final headline and lines", "supported": true}]}')


ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def spell_num(n):
    """91 -> 'ninety one', 120 -> 'one hundred twenty' (how the article may write it, hyphens and 'and' dropped)."""
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + spell_num(n % 100))
    return spell_num(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + spell_num(n % 1000))


def numbers_ok(text, source):
    """Numbers in the script that do not appear in the source (catches invented figures). A number the article writes
    in words ('Ninety-one units were built') counts as found."""
    src = re.sub(r"(?<=\d)[,\s](?=\d{3}\b)", "", source)
    spelled, bad = None, []
    for num in re.findall(r"\d+(?:[.,]\d+)*", text):
        n = re.sub(r"(?<=\d),(?=\d)", "", num).rstrip(".,")
        if not n or re.search(rf"(?<![\d.]){re.escape(n)}(?![\d]|\.\d)", src):   # whole number, '8' is not in '1938'
            continue
        if n.isdigit() and 2 <= int(n) < 1_000_000:
            if spelled is None:
                spelled = re.sub(r"\s+", " ", re.sub(r"\band\b|[-\u2010-\u2014]", " ", source.lower()))
            if re.search(rf"\b{spell_num(int(n))}\b", spelled):
                continue
        bad.append(num)
    return bad


NAME_OK = {"I", "II", "III", "IV", "V", "VI", "VII", "D-Day", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December", "Monday", "Tuesday", "Wednesday",
           "Thursday", "Friday", "Saturday", "Sunday", "World", "War", "Allied", "Allies", "Axis", "Nazi", "Nazis",
           "God", "Mr", "Mrs", "Sir", "Lady", "Lord", "General", "Admiral", "Captain", "Colonel", "Major",
           "Lieutenant", "Sergeant", "Commander", "Marshal", "Air", "Field", "Private", "Corporal", "Navy", "Army",
           "Brigadier", "Ensign", "Petty", "Officer", "Chief", "Rear", "Vice", "Fleet"}


def names_ok(text, source):
    """Capitalized names inside a sentence that the source never mentions (catches invented people, units and
    places, like numbers_ok does for figures). The first word of a sentence is skipped (capitalized anyway); tested
    on the 12 hand-checked jurgen stories with 0 false alarms (Oct 22)."""
    fold = lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    src, bad = fold(source), []
    for sent in re.split(r"(?<=[.!?])\s+", re.sub(r"\[/?[a-z]\]", "", text)):
        for k, w in enumerate(re.findall(r"[A-Za-z\u00c0-\u00ff][\w'\u2019.-]*", sent)):
            w = w.strip(".'\u2019-")
            if k == 0 or not w or not w[0].isupper() or w in NAME_OK or w.isupper() and len(w) <= 4:
                continue
            base = re.sub(r"['\u2019]s$", "", w)
            parts = [re.sub(r"(?<=[a-z]{3})s$", "", x) for x in base.split("-") if x]   # Americans -> American
            if not all(re.search(rf"\b{re.escape(fold(x))}", src) for x in parts):
                bad.append(base)
    return sorted(set(bad))


def nums_in_source(text, src):
    """Every number in a short on-screen label ('1,300 MILES', '07:48') is a whole number in the source."""
    src_n = re.sub(r"(?<=\d)[,\s](?=\d{3}\b)", "", src)
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    return all(re.search(rf"(?<![\d.]){int(x)}(?![\d]|\.\d)", src_n) for x in re.findall(r"\d+", t))


OVERCLAIM = re.compile(r"\b(single-handedly|single handedly|by himself|by herself|on his own|on her own|"
                       r"all alone|alone|one man|one woman|1 man|1 woman|lone genius|won the war)\b", re.I)
NUM_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
WORD_NUM = {v: k for k, v in NUM_WORDS.items() if len(k) > 2}
JUMP_RE = re.compile(r"^\s*(?:(\d+|" + "|".join(NUM_WORDS) + r")\s+)?(minute|hour|day|week|month|year)s?\s+"
                     r"(earlier|before)\b[,.:]?\s*", re.I)


DESIGNATION = re.compile(r"\b[A-Za-z]{1,4}-\d+[A-Za-z]?\b|\b[A-Z]{1,3}\d+[A-Za-z]?\b|\b(?:Flak|Pak|KwK|Me|Bf|Ju|He|Fw|"
                         r"Do|Type|Panzer|Pz|MG|MP|StG|Il|Yak|La|Ki|Mk|Mark|Tiger|U|Model|No)\.? ?\d+[A-Za-z]?\b")


def designations(text, topic):
    """The text without names that contain digits (T-34, Flak 88, Bf 109, M4) or the subject's own name."""
    t = DESIGNATION.sub(" ", text)
    for w in key_words(topic):
        if re.search(r"\d", w):
            t = re.sub(rf"\b{re.escape(w)}\b", " ", t)
    return t


def min_lines():
    return 2 if LENGTH[0] == "fact" else 3


def check_script(d, topic, recent=(), hook=None):
    """Hard problems block the upload; soft ones go back to the editor."""
    if not isinstance(d, dict) or not plain(d.get("headline", "")) or len(all_lines(d)) < min_lines():
        return ["missing headline or lines"], []
    hard, soft = [], []
    cold = hook == "coldopen"
    head, lines = plain(d["headline"]), [plain(l) for l in all_lines(d)]
    spoken = " ".join([head] + lines)
    checked = " ".join([head, JUMP_RE.sub("", lines[0], 1)] + lines[1:]) if cold else spoken
    for num in numbers_ok(checked, topic["text"]):   # the jump ('11 days earlier') is checked against the dates later
        hard.append(f"the number {num} is not in the source: fix or remove it")
    for c in d.get("claims") or []:
        if isinstance(c, dict) and c.get("supported") is False:
            hard.append(f"unsupported claim, fix or remove: {str(c.get('claim', ''))[:120]}")
    for m in set(x.lower() for x in OVERCLAIM.findall(spoken)):
        if m not in topic["text"].lower():
            hard.append(f"'{m}' overstates it: credit the team, the unit or the earlier work the text names")
    if KIND == "quiz":
        early = " ".join([head, plain(d.get("title", ""))] + lines[:-1]).lower()
        leaked = [w for w in key_words(topic) if w.lower() in early]
        if leaked:
            hard.append(f"the answer is revealed before the last line ({', '.join(leaked)})")
    n = len(spoken.split())
    lo, hi, aim = ((38, 58, "40-55") if LENGTH[0] == "fact" and not cold else
                   (40, 60, "42-58") if LENGTH[0] == "short" and not cold else (48, 80, "55-70"))
    if not lo <= n <= hi:
        soft.append(f"headline + lines have {n} words; write {aim}")
    if len(head.split()) > (9 if cold or hook == "map" else 11):
        soft.append(f"the headline is longer than {8 if cold or hook == 'map' else 10} words")
    if not SCALE:
        if re.search(r"\d", designations(head, topic)):
            soft.append("no numbers in the headline: name the thing and its twist in plain words")
        nums = {re.sub(r"[,.]", "", x) for x in re.findall(r"\d[\d,.]*\d|\d", designations(checked, topic))}
        nums = {x for x in nums if not (len(x) == 4 and 1900 <= int(x) <= 1950)}   # years are dates, not stats
        most = 3 if cold or hook == "map" else 1 if LENGTH[0] == "fact" else 2
        if len(nums) > most and KIND != "quiz":
            soft.append(f"{len(nums)} different numbers; keep at most {most}, only the one(s) that are the surprise")
    abbr = sorted(set(re.findall(r"\b[A-Z]{3,5}\b", spoken)) - {"USS", "HMS", "RAF", "USSR", "NATO", "SOE", "OSS",
                                                              "USA", "HMAS", "WWII", "IJN", "RAAF", "RCAF", "NKVD"})
    if abbr:
        soft.append(f"say these in plain words, viewers don't know them: {abbr[:4]}")
    if not cold and re.match(r"(in|during|by|after|before|at the start of|the story of|on)\s+(\d|the year|world war|"
                             r"january|february|march|april|may|june|july|august|september|october|november|december)",
                             lines[0].lower()):
        soft.append("line 1 starts too slowly with a date or setting; start with the action or the key fact")
    if re.search(r"\b(in conclusion|overall|this shows|in summary|to summarize|this proves|all in all)\b",
                 lines[-1].lower()):
        soft.append("the last line sounds like a summary; end on the consequence or the irony")
    tells = sorted(set(re.findall(r"\b(delve|tapestry|testament|pivotal|crucial|remarkable|unwavering|game.changer|"
                                  r"showcas\w*|underscor\w*|changed history forever|stands as|in the annals)\b",
                                  spoken.lower())))
    if tells:
        soft.append(f"these sound machine-written, say it plainly: {tells[:4]}")
    if re.search(r"\b(honestly|hot take)\b", spoken.lower()):
        soft.append("drop the 'Honestly' / 'Hot take' opinion line; state the fact plainly")
    if LOOP == "punch" and not cold and PART != 1 and KIND != "quiz" and not re.search(r"[.!]['\"]?$", lines[-1].strip()):
        soft.append("the last line must be a complete punchline sentence ending with a period")
    long = [l for l in lines if len(l.split()) > 13]
    if long:
        soft.append(f"these lines are longer than 12 words: {long[:2]}")
    if re.match(r"(did you know|in world war|imagine|have you ever|this is)\b", head.lower()):
        soft.append("the headline starts with a banned opener")
    if cold:
        if not 5 <= len(lines) <= 7:
            soft.append("write exactly 6 lines in the cold-open order")
        if not JUMP_RE.match(lines[0]):
            soft.append("line 1 must start with the time jump back from the climax, e.g. '11 days earlier,'")
        if not re.search(r"[.!]$", lines[-1].strip()):
            soft.append("the last line must be one complete sentence that answers the headline")
    elif hook == "map":
        m = d.get("map") if isinstance(d.get("map"), dict) else {}
        ps = [p for p in m.get("places") or [] if isinstance(p, dict) and p.get("title")]
        if not ps:
            soft.append("map.places is missing: 2-4 places with their exact Wikipedia titles, the target first")
        elif not re.search(r"\b(this|these|here)\b", head.lower()) and \
                ascii_up(plain(str(ps[0].get("label") or ps[0]["title"]))) not in ascii_up(head):
            soft.append("map hook: the headline must point at the target place ('This tiny island...' or its name)")
    elif SCALE and KIND != "quiz" and not re.search(r"\b(?!1\b)\d[\d,.]*", head):
        soft.append("the headline must contain the most impressive number from the source, in digits")
    elif SCALE and KIND != "quiz" and not re.search(r"\?|\b(but|yet|why|how|still|only|never|lost|failed)\b", head.lower()):
        soft.append("the headline needs tension: add a paradox or a question to the number (how/why/but/yet)")
    if "[r]" not in str(d["headline"]) or sum("[r]" in str(l) for l in all_lines(d)) < len(lines) / 2:
        soft.append("mark the key detail of the headline and of each line with [r]...[/r]")
    first = " ".join(head.lower().split()[:3])
    if any(first == " ".join(plain(r).lower().split()[:3]) for r in recent):
        soft.append("the headline starts like a recent video; change its wording")
    title = plain(d.get("title", ""))
    if not title or len(title) > 60:
        soft.append("the title is missing or longer than 60 characters")
    elif KIND != "quiz" and CATEGORY != "myth" and not any(
            w.lower() in " ".join(title.lower().split()[:3]) for w in key_words(topic)):
        soft.append("the title must start with the subject's common name (first 2-3 words)")
    if title and KIND != "quiz":
        tl = title.lower()
        if re.match(r"(did you know|in ww ?2|in world war|imagine|this is|the story of|why|how|what)\b", tl):
            soft.append("the title must not start with a question word or a banned opener; subject first")
        if re.search(r"[#\U0001F000-\U0001FFFF\u2600-\u27BF]|!!", title) or \
                [w for w in re.findall(r"\b[A-Z]{4,}\b", title) if w not in ("WWII", "USSR", "NATO")]:
            soft.append("no emojis, hashtags, CAPS words or double exclamation marks in the title")
        half = designations(title[:len(title) // 2], topic)
        if re.search(r"\d", half):
            soft.append("a number in the title belongs in its second half, after the subject")
        if plain(d.get("headline", "")).lower().strip(" .?!") == tl.strip(" .?!"):
            soft.append("the title repeats the headline; make it the promise, not the hook")
    if re.search(r"\b(subscribe|like and|follow for|comment below)\b", spoken.lower()):
        soft.append("no calls to action in the narration")
    return hard, soft


def drop_bad_lines(d, topic):
    """Last resort: remove lines with invented numbers or unsupported claims if at least 3 lines remain."""
    lines = list(all_lines(d))
    for c in d.get("claims") or []:
        if isinstance(c, dict) and c.get("supported") is False and len(lines) > min_lines():
            cw = set(plain(c.get("claim", "")).lower().split())
            worst = max(lines, key=lambda l: len(cw & set(plain(l).lower().split())))
            lines.remove(worst)
    lines = [l for l in lines if not numbers_ok(JUMP_RE.sub("", plain(l), 1), topic["text"])] \
        if len(lines) > min_lines() else lines
    if len(lines) >= min_lines():
        d = {**d, "lines": lines, "claims": []}
    return d


def write_script(topic, hook, recent):
    """Draft -> editor + fact-check -> code checks -> fix rounds. A script with hard problems is never uploaded.
    If Gemini goes down after the draft (overloaded, quota used up), the best version so far is used when it passes
    the hard checks, instead of losing the time slot."""
    ok = lambda d: isinstance(d, dict) and bool(plain(d.get("headline", ""))) and len(d.get("lines", [])) >= min_lines()
    best, best_cost, d = None, 1e9, None

    def score_it(x):
        nonlocal best, best_cost
        hard, soft = check_script(x, topic, recent, hook)
        print("script check:", len(hard), "hard,", len(soft), "soft", (hard + soft)[:3])
        if len(hard) * 10 + len(soft) < best_cost:
            best, best_cost = x, len(hard) * 10 + len(soft)
        return hard, soft
    try:
        # fact videos are short: fewer Gemini editor rounds (saves quota + latency)
        drafts, edit_rounds = (1, 2) if LENGTH[0] == "fact" else (2, 3)
        for _ in range(drafts):
            d, issues = gemini(draft_prompt(topic, hook, recent), ok, purpose="script draft"), []
            for rnd in range(edit_rounds):
                d = gemini(editor_prompt(topic, hook, recent, d, issues), ok, rounds=5, purpose="script editor")
                hard, soft = score_it(d)
                if not hard and (len(soft) <= 1 or rnd >= 1):
                    return d
                issues = hard + soft
    except SystemExit as e:
        if d is None:                                # not even a draft: nothing to check
            raise
        print(e, "-> the best version so far, if it passes the checks")
        score_it(d)
    if check_script(best, topic, recent, hook)[0]:
        best = drop_bad_lines(best, topic)
    hard = check_script(best, topic, recent, hook)[0]
    if hard:
        raise SystemExit("script failed the quality checks: " + "; ".join(hard))
    return best


# ---- Cold open: time stamps, list cards and the rewind stamp, all checked against the source -------------
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def ascii_up(t):
    """'Sōryū' -> 'SORYU', so names on screen can be found in the article."""
    return unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().upper()


def plate_date(text):
    """(year, month, day, minutes) from a time stamp like 'DEC 7, 1941 · 07:48', '7 DECEMBER 1941', 'JUNE 1942'."""
    t, mon = ascii_up(text), r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\.?"
    hm = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    mins = int(hm.group(1)) * 60 + int(hm.group(2)) if hm else None
    for pat, order in ((mon + r"\s+(\d{1,2}),?\s+(1[89]\d\d)", "mdy"), (r"\b(\d{1,2})\s+" + mon + r"\s+(1[89]\d\d)", "dmy")):
        m = re.search(pat, t)
        if m:
            g = m.groups()
            mo, d = (g[0], g[1]) if order == "mdy" else (g[1], g[0])
            return int(g[2]), MONTHS.index(mo) + 1, int(d), mins
    m = re.search(mon + r"\s+(1[89]\d\d)", t)
    if m:
        return int(m.group(2)), MONTHS.index(m.group(1)) + 1, None, mins
    m = re.search(r"\b(1[89]\d\d)\b", t)
    return (int(m.group(1)), None, None, mins) if m else None


def jump_between(a, b):
    """(number, unit) from the time stamp of line 1 (b) forward to the climax (a), e.g. (11, 'day')."""
    from datetime import date
    if not a or not b:
        return None
    (ya, ma, da, ta), (yb, mb, db, tb) = a, b
    try:
        if ma and mb and da and db:
            days = (date(ya, ma, da) - date(yb, mb, db)).days
            if days == 0 and ta is not None and tb is not None and ta > tb:
                return (round((ta - tb) / 60), "hour") if ta - tb >= 60 else (ta - tb, "minute")
            if 1 <= days <= 60:
                return days, "day"
            if 60 < days <= 730:
                return round(days / 30.44), "month"
            return (round(days / 365.25), "year") if days > 730 else None
    except ValueError:
        return None
    if ma and mb and (ya, ma) != (yb, mb):
        months = (ya - yb) * 12 + ma - mb
        return ((months, "month") if months <= 24 else (round(months / 12), "year")) if months > 0 else None
    return (ya - yb, "year") if ya > yb else None


def marked(words):
    """[(word, colour)] back to text with [r]/[y] markers."""
    out, cur, buf = [], WHITE, []
    for w, c in words + [("", None)]:
        if c != cur and buf:
            tag = {RED: "r", YELLOW: "y"}.get(cur)
            out.append(f"[{tag}]{' '.join(buf)}[/{tag}]" if tag else " ".join(buf))
            buf = []
        cur = c
        if w:
            buf.append(w)
    return " ".join(out)


def cold_prepare(data, topic):
    """Keeps only time stamps and list items that are in the article, and makes the rewind stamp ('11 DAYS
    EARLIER') agree with the dates: the number in line 1 is recomputed from the stamps, or dropped if unknown."""
    src, src_up = topic["text"], ascii_up(topic["text"])
    src_n = re.sub(r"(?<=\d)[,\s](?=\d{3}\b)", "", src)
    in_src = lambda t: all(re.search(rf"(?<![\d.]){int(x)}(?![\d]|\.\d)", src_n) for x in re.findall(r"\d+", t))
    lines = list(all_lines(data))
    n = len(lines)
    plates = []
    for p in data.get("plates") or []:
        try:
            ln = int(p.get("line"))
        except (AttributeError, TypeError, ValueError):
            continue
        text = re.sub(r"\s+", " ", plain(p.get("text", ""))).strip().upper()[:34]
        red = re.sub(r"\s+", " ", plain(p.get("red", "") or "")).strip().upper()[:30] if ln == 0 else ""
        if 0 <= ln <= n and text and in_src(f"{text} {red}") and all(q["line"] != ln for q in plates):
            plates.append({"line": ln, "text": text, "red": red})   # '07:48' passes when the article says '7:48'
    plates = sorted(plates, key=lambda q: q["line"])[:4]
    stamp = {q["line"]: q["text"] for q in plates}
    calc = jump_between(plate_date(stamp.get(0, "")), plate_date(stamp.get(1, "")))
    jump = "EARLIER"
    if lines:
        words = styled_words(lines[0])
        m = JUMP_RE.match(" ".join(w for w, _ in words[:4]))
        k = (1 if m and m.group(1) else 0) + 2 if m else 0      # words used by the jump phrase
        said = m and m.group(1) and (int(m.group(1)) if m.group(1).isdigit() else NUM_WORDS[m.group(1).lower()])
        if calc and m:
            num, unit = calc
        elif m and said and re.search(rf"\b({said}|{m.group(1)}|{WORD_NUM.get(said, said)})\s+{m.group(2)}s?\b", src, re.I):
            num, unit = said, m.group(2).lower()               # the article itself says '3 days' / 'three days'
        elif m:
            num, unit = None, m.group(2).lower()                # unknown: 'Days earlier,'
        if m:
            tail = words[k - 1][0][len(re.match(r"[A-Za-z]+", words[k - 1][0]).group()):]   # ',' after 'earlier'
            unit_w = unit + ("s" if num != 1 else "")
            lead = [(str(num), RED), (unit_w, RED)] if num else [(unit_w.capitalize(), RED)]
            words = lead + [(words[k - 1][0].rstrip(",.:") + (tail or ","), words[k - 1][1])] + words[k:]
            lines[0] = marked(words)
            jump = (f"{num} {unit_w} earlier" if num else f"{unit_w} earlier").upper()
        elif calc:
            num, unit = calc
            jump = f"{num} {unit}{'s' if num != 1 else ''} earlier".upper()
    cards = []
    for c in data.get("cards") or []:
        if not isinstance(c, dict):
            continue
        try:
            ln = int(c.get("line"))
        except (TypeError, ValueError):
            continue
        items = []
        for it in c.get("items") or []:
            name = re.sub(r"\s+", " ", plain(str(it))).strip().upper()
            key = [w for w in re.findall(r"[A-Z0-9]+", ascii_up(name)) if w not in ("USS", "HMS", "THE", "OF")]
            if 1 < len(name) <= 16 and key and all(re.search(rf"\b{w}\b", src_up) for w in key) and name not in items:
                items.append(name)
        if not 1 <= ln <= n or not 2 <= len(items) <= 6 or (cards and ln <= cards[-1]["until"]):
            continue
        title = re.sub(r"\s+", " ", plain(c.get("title", ""))).strip().upper()[:28]
        mk, mark = c.get("mark") if isinstance(c.get("mark"), dict) else {}, None
        try:
            ml = int(mk.get("line", 0))
            idx = sorted({int(i) - 1 for i in mk.get("items") or [] if 1 <= int(i) <= len(items)})
        except (TypeError, ValueError):
            ml, idx = 0, []
        label = re.sub(r"\s+", " ", plain(mk.get("label", ""))).strip().upper()[:12]
        style = "stamp" if mk.get("style") == "stamp" and len(items) <= 3 else "strike"
        if ln <= ml <= n and idx and label and in_src(label):
            mark = {"line": ml, "at": str(mk.get("at", "")), "label": label, "items": idx, "style": style}
        cards.append({"line": ln, "at": str(c.get("at", "")), "title": title if in_src(title) else "",
                      "items": items, "mark": mark, "until": mark["line"] if mark else ln})
        if len(cards) == 2:
            break
    return {**data, "lines": lines, "cold": True, "jump": jump, "plates": plates, "cards": cards,
            "alarm": data.get("alarm") is True}


# ---- Shots -------------------------------------------------------------------
# ---- Covers: colour (DDColor-tiny, Apache-2.0) and sharpness (Real-ESRGAN, BSD-3) -----------------------------
DDCOLOR_DIR = pathlib.Path(env("DDCOLOR_DIR", str(pathlib.Path.home() / "ddcolor")))
DDCOLOR_URL = "https://huggingface.co/edgetools/ddcolor/resolve/main/ddcolor-tiny-fp16.onnx"   # ~130 MB, cached
ESRGAN_URL = "https://huggingface.co/TheGuy444/Real-ESRGAN-ONNX/resolve/main/onnx/"           # general x4v3


def _lab(rgb):
    """sRGB [0,1] -> CIE Lab (OpenCV float convention, D65), what DDColor was trained on."""
    import numpy as np
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = lin @ np.array(_M).T / np.array(_WP)
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def _rgb(lab):
    import numpy as np
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    xyz = np.where(f > 0.206893, f ** 3, (f - 16 / 116) / 7.787) * np.array(_WP)
    lin = xyz @ np.linalg.inv(np.array(_M)).T
    return np.clip(np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.clip(lin, 0, None) ** (1 / 2.4) - 0.055), 0, 1)


_M = ((0.412453, 0.357580, 0.180423), (0.212671, 0.715160, 0.072169), (0.019334, 0.119193, 0.950227))
_WP = (0.950456, 1.0, 1.088754)
_SESS = {}


def ddcolor():
    """The DDColor-tiny ONNX session (downloaded once, ~130 MB, kept in the Actions cache)."""
    if "ddcolor" in _SESS:
        return _SESS["ddcolor"]
    import onnxruntime as ort
    f = DDCOLOR_DIR / "ddcolor-tiny-fp16.onnx"
    if not f.exists() or f.stat().st_size < 100_000_000:
        DDCOLOR_DIR.mkdir(parents=True, exist_ok=True)
        print("ddcolor: downloading the model")
        tmp = f.with_suffix(".part")
        with requests.get(DDCOLOR_URL, stream=True, timeout=(15, 300)) as r, open(tmp, "wb") as out:
            r.raise_for_status()
            for chunk in r.iter_content(1 << 20):
                out.write(chunk)
        tmp.replace(f)
    opts = ort.SessionOptions()
    opts.log_severity_level = 3                        # no constant-folding warnings in the log
    _SESS["ddcolor"] = ort.InferenceSession(str(f), opts, providers=["CPUExecutionProvider"])
    return _SESS["ddcolor"]


def is_mono(path):
    """True for a black-and-white or sepia photo (its colours hardly vary)."""
    import numpy as np
    from PIL import Image
    try:
        lab = _lab(np.asarray(Image.open(path).convert("RGB").resize((96, 96)), dtype=np.float32) / 255)
    except Exception:
        return False
    return float(lab[..., 1].std()) < 4.0 and float(lab[..., 2].std()) < 4.0


def colorize(path, portrait=False):
    """A colourised copy of a black-and-white photo: DDColor predicts the colour at 512x512, the photo keeps its
    own full-resolution brightness. The original path if it fails. DDColor sometimes gives up on a whole picture
    (the Hess and Doss portraits came out grey): it tries again on a contrast-equalized copy, and for a portrait
    (a cover) on its upper middle (face and shoulders), which then becomes the picture."""
    import numpy as np
    from PIL import Image, ImageOps
    try:
        sess = ddcolor()
        im = Image.open(path).convert("RGB")
        def predict(src):                              # DDColor's colour (ab) for a 512x512 grey copy
            small = np.asarray(src.convert("RGB").resize((512, 512), Image.BICUBIC), dtype=np.float32) / 255
            ls = _lab(small)[..., :1]
            gray = _rgb(np.concatenate([ls, np.zeros_like(ls), np.zeros_like(ls)], -1)).astype(np.float32)
            return sess.run(None, {sess.get_inputs()[0].name: gray.transpose(2, 0, 1)[None]})[0][0]
        ab = predict(im)
        if float(np.abs(ab).mean()) < 2:
            ab = predict(ImageOps.equalize(im.convert("L")))
        if float(np.abs(ab).mean()) < 2 and portrait:
            w, h = im.size
            im = im.crop((int(w * 0.1), 0, int(w * 0.9), int(h * 0.65)))
            ab = predict(ImageOps.equalize(im.convert("L")))
        if float(np.abs(ab).mean()) < 2:
            print("colorize: no colour found for", pathlib.Path(path).name[:60])
            return path
        img = np.asarray(im, dtype=np.float32) / 255
        h, w = img.shape[:2]
        ab = np.stack([np.asarray(Image.fromarray(ab[c]).resize((w, h), Image.BICUBIC)) for c in range(2)], -1)
        out = path.with_name(path.stem + "_col.jpg")
        Image.fromarray((_rgb(np.concatenate([_lab(img)[..., :1], ab], -1)) * 255).astype(np.uint8)).save(out, quality=93)
        return out
    except Exception as e:
        print("colorize skipped:", type(e).__name__, str(e)[:100])
        return path


def esrgan():
    """The Real-ESRGAN general x4v3 ONNX session (BSD-3, ~5 MB: 128x128 tiles in, 512x512 out), downloaded once."""
    if "esrgan" in _SESS:
        return _SESS["esrgan"]
    import onnxruntime as ort
    d = DDCOLOR_DIR / "esrgan"
    d.mkdir(parents=True, exist_ok=True)
    for name in ("model.onnx", "model.data"):          # the weights sit next to the graph (external data)
        f = d / name
        if not f.exists() or f.stat().st_size < 30_000:
            r = requests.get(ESRGAN_URL + name, timeout=(15, 120))
            r.raise_for_status()
            f.write_bytes(r.content)
    opts = ort.SessionOptions()
    opts.log_severity_level = 3
    _SESS["esrgan"] = ort.InferenceSession(str(d / "model.onnx"), opts, providers=["CPUExecutionProvider"])
    return _SESS["esrgan"]


def upscale(path, most=900, tile=128, pad=12):
    """4x sharper copy of a picture (Real-ESRGAN, tile by tile with an overlap; the longest side first brought to at
    most `most` px, so a portrait takes ~10-30 s on the runner). The original path if it fails."""
    import numpy as np
    from PIL import Image
    try:
        sess = esrgan()
        name, step = sess.get_inputs()[0].name, tile - 2 * pad
        im = Image.open(path).convert("RGB")
        if max(im.size) > most:
            im.thumbnail((most, most), Image.LANCZOS)
        img = np.asarray(im, dtype=np.float32) / 255
        h, w = img.shape[:2]
        big = np.pad(img, ((pad, -h % step + pad), (pad, -w % step + pad), (0, 0)), mode="reflect")
        out = np.zeros((h * 4, w * 4, 3), np.float32)
        for y in range(0, h, step):
            for x in range(0, w, step):
                t = np.ascontiguousarray(big[y:y + tile, x:x + tile].transpose(2, 0, 1)[None])
                r = sess.run(None, {name: t})[0][0].transpose(1, 2, 0)[pad * 4:(pad + step) * 4, pad * 4:(pad + step) * 4]
                hh, ww = min(step, h - y) * 4, min(step, w - x) * 4
                out[y * 4:y * 4 + hh, x * 4:x * 4 + ww] = r[:hh, :ww]
        dst = pathlib.Path(path).with_name(pathlib.Path(path).stem + "_x4.jpg")
        Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(dst, quality=94)
        return dst
    except Exception as e:
        print("upscale skipped:", type(e).__name__, str(e)[:100])
        return path


def toned(path):
    """True for a black-and-white, sepia or tinted print (one colour cast, no real colours): colour it for a cover."""
    import numpy as np
    from PIL import Image
    try:
        lab = _lab(np.asarray(Image.open(path).convert("RGB").resize((96, 96)), dtype=np.float32) / 255)
    except Exception:
        return False
    return float(lab[..., 1].std()) < 8.0 and float(lab[..., 2].std()) < 8.0


def warm_tone(path):
    """A colour grade for a portrait DDColor could not colour: cool shadows, warm skin midtones, light highlights
    (the look of a hand-tinted print), the photo's own brightness kept."""
    import numpy as np
    from PIL import Image
    try:
        img = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255
        L = _lab(img)[..., 0]
        a = np.interp(L, (0, 30, 60, 85, 100), (1, 6, 12, 7, 2))
        b = np.interp(L, (0, 30, 60, 85, 100), (-4, 6, 18, 12, 4))
        out = pathlib.Path(path).with_name(pathlib.Path(path).stem + "_tone.jpg")
        Image.fromarray((_rgb(np.stack([L, a, b], -1)) * 255).astype(np.uint8)).save(out, quality=93)
        return out
    except Exception as e:
        print("warm tone skipped:", type(e).__name__, str(e)[:100])
        return path


COVER_COLOR = env("COVER_COLOR", "0") == "1"   # v1.93 (Andrii, Oct 25): covers only upscaled, not colorized


def enhance_cover(path, color=True, portrait=False):
    """The cover picture (Andrii, Oct 25): a black-and-white or tinted photo colorized (color=True), then upscaled.
    A portrait DDColor cannot colour as a whole is coloured on its face crop, else given a warm tone."""
    if color and toned(path):
        done = colorize(pathlib.Path(path), portrait=portrait)
        path = warm_tone(path) if portrait and done == pathlib.Path(path) else done
    return upscale(path)


def plan_shots(total, a, b, clips=()):
    """punch: sharp main photo zooming in (a strong first frame, no blur); single: Ken Burns; pixel: quiz, sharper
    each shot; split: versus; outro: main photo zooming back out so the last frame matches the first (clean loop);
    clip: archive film, alternating with the photos in the middle. OPENING=tease brings back the old blurred
    'wait for it' start."""
    shot = lambda kind, imgs, dur, **kw: {"kind": kind, "imgs": imgs, "dur": dur, **kw}
    if KIND == "versus" and b:
        head, tail = min(3.0, total * 0.15), min(3.0, total * 0.15)
        mid = total - head - tail
        n = max(2, round(mid / SHOT_SEC))
        side = lambda i: (a, b)[i % 2]
        return ([shot("split", [a[0], b[0]], head)]
                + [shot("single", [side(i)[(i // 2 + 1) % len(side(i))]], mid / n) for i in range(n)]
                + [shot("split", [a[0], b[0]], tail)])
    pay = min(3.0, max(2.0, total * 0.12))
    if KIND == "quiz":                                 # pixelated photo gets sharper, answer in the last shot
        n = max(2, round((total - pay) / SHOT_SEC))
        return ([shot("pixel", [a[0]], (total - pay) / n, px=int(14 * 4 ** (i / max(1, n - 1)))) for i in range(n)]
                + [shot("single", [a[0]], pay)])
    cover = LOOK.get("cover")
    pay += TAIL_SEC if cover else 0
    if COLD.get("at"):                                 # cold open: the climax, the tape rewinding it, the story
        head = [shot("punch", [a[0]], COLD["at"], cold=True), shot("rewind", [a[0]], COLD["end"] - COLD["at"])]
        last = shot("outro", [a[0]], pay, cold=True)
    elif LOOK.get("map_art"):                          # map hook: the map opens and closes the video
        head = [shot("map", [], PUNCH_SEC + (COVER_T if cover else 0), mode=("target",))]
        last = shot("map", [], pay, mode=("target",))
    else:
        head = [shot("tease", [a[0]], TEASE_SEC) if OPENING == "tease" else
                shot("punch", [a[0]], PUNCH_SEC + (COVER_T if cover else 0))]
        last = shot("single", [a[0]], pay) if OPENING == "tease" else shot("outro", [a[0]], pay)
    rest, mid = total - sum(h["dur"] for h in head) - pay, a[1:] or a
    n = max(1, min(16, round(rest / SHOT_SEC)))
    body = [shot("single", [mid[i % len(mid)]], rest / n) for i in range(n)]
    if LENGTH[0] == "fact" and clips:                  # ONE FACT: the film shows the thing for the whole middle
        k = min(len(clips), 2 if rest > 5.5 else 1)
        body = [shot("clip", [c["path"]], rest / k, ss=c["ss"], crop=c.get("crop")) for c in clips[:k]]
        n = len(body)
    else:                                              # film right after the opening photo, then every second shot
        for k, c in zip(range(0, n, 2), clips):
            body[k] = shot("clip", [c["path"]], rest / n, ss=c["ss"], crop=c.get("crop"))
    if LOOK.get("map_art"):                            # a route / the distance is drawn on the shot under its line
        h0, step = sum(h["dur"] for h in head), rest / n
        for at, mode in LOOK.get("map_marks", []):
            k = max(0, min(n - 1, int((at - h0) // step)))
            if at - h0 - k * step > step - 1.6 and k < n - 1:   # too late in that shot to finish the line
                k += 1
            while k < n - 1 and body[k]["kind"] == "map":
                k += 1
            if body[k]["kind"] != "map":                 # the line starts drawing when it is spoken
                body[k] = shot("map", [], step, mode=mode, lead=max(0.0, min(step - 1.5, at - h0 - k * step)))
    shots = head + body + [last]
    if cover:                                          # the first and last moments become the cover morphs
        shots[0] = {**shots[0], "dur": shots[0]["dur"] - COVER_T, "cover": True}
        shots[-1] = {**shots[-1], "dur": shots[-1]["dur"] - TAIL_SEC, "cover": True}
        shots = [shot("cover", [a[0]], COVER_T)] + shots + [shot("tail", [a[0]], TAIL_SEC)]
    if LOOK.get("map_art"):                            # radar rings run on without a jump into and out of the cover
        first, end = shots[1 if cover else 0], shots[-2 if cover else -1]
        first["t0"], end["t0"] = (COVER_T if cover else 0.0), (MAP_LOOP_T if cover else 0.0) - end["dur"]
    return shots


def render_shot(i, sh):
    """One 1080 x MID_H picture shot (the black bars are added once, in the final pass)."""
    if sh["kind"] == "map":
        return render_map_shot(i, sh)
    fr = int(sh["dur"] * 30) + 2
    tail = "eq=contrast=1.08:saturation=0.9,setsar=1[v]"
    if STYLE_A and WHIP and sh["kind"] in ("single", "clip"):   # the cut lands with a 2-frame sideways blur
        tail = WHIP_VF + tail
    if sh["kind"] == "clip":                          # archive film: black borders cut, fills the picture area
        fc = (f"[0:v]{'crop=' + sh['crop'] + ',' if sh.get('crop') else ''}fps=30,"
              f"scale=1080:{MID_H}:force_original_aspect_ratio=increase,crop=1080:{MID_H},format=yuv420p,")
        ff("-ss", f"{sh['ss']:.2f}", "-t", f"{sh['dur'] + 0.5:.2f}", "-i", str(sh["imgs"][0]), "-filter_complex",
           fc + tail, "-map", "[v]", "-t", f"{sh['dur']:.3f}", "-an", "-c:v", "utvideo", "-pix_fmt", "yuv420p",
           f"shot{i}.mkv")
        return f"shot{i}.mkv"
    center = f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d={fr}:s=1080x{MID_H}:fps=30,"
    if sh["kind"] == "split":
        fc = "".join(f"[{k}:v]scale=1080:{2 * MID_H}:force_original_aspect_ratio=increase,crop=1080:{2 * MID_H},"
                     "format=yuv420p,"
                     f"zoompan=z='1+0.08*on/{fr}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d={fr}:s=540x{MID_H}"
                     f":fps=30[s{k}];" for k in range(2))
        fc += f"[s0][s1]hstack,drawbox=x=537:y=0:w=6:h={MID_H}:color={ACCENT}@1:t=fill,"
    else:   # blurred fill behind the whole photo, then motion
        ch = 2 * MID_H                              # canvas with the same shape as the shot
        fc = (f"[0:v]split[a][b];[a]scale=2160:{ch}:force_original_aspect_ratio=increase,crop=2160:{ch},"
              f"boxblur=30:3,eq=brightness=-0.25[bg];[b]scale=2160:{ch}:force_original_aspect_ratio=decrease[fg];"
              "[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p,")
        if sh.get("cover") or STYLE_A:               # next to the cover (and in style A): the photo fills the frame
            fc = (f"[0:v]scale=2160:{ch}:force_original_aspect_ratio=increase,"
                  f"crop=2160:{ch}:(iw-ow)/2:'max(0,min(ih-oh,ih*0.4-oh/2))',format=yuv420p,")
        if sh["kind"] == "pixel":
            fc += f"scale={sh.get('px', 54)}:-2,scale=2160:{ch}:flags=neighbor,zoompan=z='1':{center}"
        elif sh["kind"] == "tease":
            fc += f"boxblur=60:4,eq=brightness=-0.15,zoompan=z='1+0.05*on/{fr}':{center}"
        elif sh["kind"] == "punch" and sh.get("cold") and sh.get("cover"):   # cold open after the cover morph
            fc += f"zoompan=z='1.04+0.16*(1-pow(1-on/{fr},2))':{center}"
        elif sh["kind"] == "punch" and sh.get("cold"):  # cold open: push-in with an impact flash and a short shake
            fc += (f"zoompan=z='1.04+0.16*(1-pow(1-on/{fr},2))':"
                   "x='(iw-iw/zoom)/2+if(lt(on,12),34*sin(on*2.9)*(1-on/12),0)':"
                   f"y='(ih-ih/zoom)/2+if(lt(on,12),24*sin(on*3.7)*(1-on/12),0)':d={fr}:s=1080x{MID_H}:fps=30,"
                   "eq=brightness='0.22*max(0,1-t/0.13)':eval=frame,")
        elif sh["kind"] == "rewind":                  # the push-in plays backwards on tape: grey, noisy, jittering
            fc += (f"zoompan=z='1.20-0.16*on/{fr}':{center}hue=s=0,"
                   "eq=brightness='0.07*sin(n*2.3)':contrast=1.3:eval=frame,noise=alls=55:allf=t,"
                   f"rgbashift=rh=-18:bh=18:rv=5,crop=1080:{MID_H - 12}:0:'6+6*sin(n*1.9)',scale=1080:{MID_H},")
        elif sh["kind"] == "punch":                   # fast ease-out push-in from the exact loop frame
            fc += f"zoompan=z='1+0.16*(1-pow(1-on/{fr},2))':{center}"
        elif sh["kind"] == "outro":                   # eases back to the first frame's zoom
            fc += f"zoompan=z='{1.04 if sh.get('cold') else 1}+0.16*pow(1-on/{fr},2)':{center}"
        else:
            # smooth Ken Burns only — no micro-jump halfway through the shot
            z = f"1+0.10*on/{fr}" if i % 2 == 0 else f"1.10-0.10*on/{fr}"
            pan = ["(iw-iw/zoom)/2", f"(iw-iw/zoom)*on/{fr}", f"(iw-iw/zoom)*(1-on/{fr})"][i % 3]
            fc += f"zoompan=z='{z}':x='{pan}':y='(ih-ih/zoom)/2':d={fr}:s=1080x{MID_H}:fps=30,"
    ff(*sum((["-i", str(p)] for p in sh["imgs"]), []), "-filter_complex", fc + tail, "-map", "[v]",
       "-t", f"{sh['dur']:.3f}", "-c:v", "utvideo", "-pix_fmt", "yuv420p", f"shot{i}.mkv")   # lossless, fast
    return f"shot{i}.mkv"


def build_background(shots):
    """Shots render in parallel (one ffmpeg per CPU core) into lossless files; the final pass reads them in order,
    so the picture is compressed only once."""
    from concurrent.futures import ThreadPoolExecutor
    todo = [(i, sh) for i, sh in enumerate(shots) if sh["kind"] not in ("cover", "tail")]
    with ThreadPoolExecutor(max_workers=max(1, min(len(todo), os.cpu_count() or 2))) as ex:
        parts = list(ex.map(lambda a: render_shot(*a), todo))
    (W / "bg.txt").write_text("\n".join(f"file '{p}'" for p in parts), encoding="utf-8")


def fit_box(w, h, aspect, cy=0.5):
    """Largest crop of a w x h picture with this width/height, centred across, at cy of the height."""
    cw, chh = (h * aspect, h) if w / h > aspect else (w, w / aspect)
    x0, y0 = (w - cw) / 2, min(max(0.0, h * cy - chh / 2), h - chh)
    return (x0, y0, x0 + cw, y0 + chh)


def cover_assets(photo, z_end=1.0, clips=True):
    """Pillow: the blurred, darkened main photo behind the text (backdrop.png) and, with the cover, the opening
    (photo full screen 9:16, then it shrinks into the frame while the rest blurs: cover.mkv) and the closing (it
    grows back, so the last frame is the first: tail.mkv)."""
    from PIL import Image, ImageEnhance, ImageFilter
    im = Image.open(photo).convert("RGB")
    if im.height > 2000:                               # big Commons scans: only as sharp as the screen needs
        im = im.resize((round(im.width * 2000 / im.height), 2000), Image.Resampling.LANCZOS)
    w, h = im.size
    s_full, s_win = fit_box(w, h, 9 / 16, 0.45), fit_box(w, h, 1080 / MID_H, 0.4)
    bd = im.crop(tuple(int(v) for v in s_full)).resize((540, 960)).filter(ImageFilter.GaussianBlur(14))
    bd = ImageEnhance.Brightness(bd.resize((1080, 1920), Image.Resampling.BILINEAR)).enhance(0.45)
    if BG == "black":                                  # plain black around the picture (Andrii, Oct 14)
        bd = Image.new("RGB", (1080, 1920), (0, 0, 0))
    bd.save(W / "backdrop.png")
    if not clips:
        return
    ease = lambda p: 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, p)))
    lerp = lambda a, b, p: tuple(x + (y - x) * p for x, y in zip(a, b))
    zoom = lambda r, z: ((r[0] + r[2]) / 2 - (r[2] - r[0]) / z / 2, (r[1] + r[3]) / 2 - (r[3] - r[1]) / z / 2,
                         (r[0] + r[2]) / 2 + (r[2] - r[0]) / z / 2, (r[1] + r[3]) / 2 + (r[3] - r[1]) / z / 2)
    sharp = ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(1.08)).enhance(0.9)   # same colour as the shots
    cut = lambda src, size: sharp.transform(size, Image.Transform.EXTENT, src, Image.Resampling.BILINEAR)

    def frame(p, z_full):
        full = cut(zoom(s_full, z_full), (1080, 1920))
        if p <= 0:
            return full
        e = ease(p)
        img = Image.blend(full, bd, e)
        dst = lerp((0, 0, 1080, 1920), (0, TOP_BAR, 1080, TOP_BAR + MID_H), e)
        img.paste(cut(lerp(zoom(s_full, z_full), zoom(s_win, z_end), e), (1080, int(round(dst[3] - dst[1])))),
                  (0, int(round(dst[1]))))
        return img

    def clip(name, frames):
        pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                               "1080x1920", "-r", "30", "-i", "-", "-c:v", "utvideo", "-pix_fmt", "yuv420p", name],
                              stdin=subprocess.PIPE, cwd=W)
        for f in frames:
            pr.stdin.write(f.tobytes())
        pr.stdin.close()
        if pr.wait():
            raise RuntimeError("cover clip failed")
    n1, n2, nt = round(COVER_SEC * 30), round(MORPH_SEC * 30), round(TAIL_SEC * 30)
    clip("cover.mkv", [frame(0, 1 + 0.04 * k / n1) for k in range(n1)] + [frame((k + 1) / n2, 1.04) for k in range(n2)])
    clip("tail.mkv", [frame(1 - (k + 1) / nt, 1.0) for k in range(nt)])


# ---- Map hook: a real map (Natural Earth) zooms into the place of the story ----------------------------
MAP_FILE = pathlib.Path("map/land-10m.json")
LAND = []                                              # [(bbox, [outer ring, holes...])], decoded once
OCEAN_T, OCEAN_B, LAND_C, COAST_C, GRID_C = (16, 34, 54), (8, 18, 32), (74, 88, 72), (150, 172, 150), (32, 60, 88)
SIDE_C = {"axis": (229, 57, 53), "allied": (79, 195, 247)}


def land_polys():
    """Natural Earth land polygons from the TopoJSON in map/ (lon, lat), with their bounding boxes."""
    if LAND:
        return LAND
    topo = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    (sx, sy), (tx, ty) = topo["transform"]["scale"], topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x, y = x + dx, y + dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        raw = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            raw.extend(a if not raw else a[1:])
        out, off = [], 0.0                             # rings across the date line stay in one piece (Siberia)
        for x, y in raw:
            if out and abs(x + off - out[-1][0]) > 180:
                off += 360 if out[-1][0] > x + off else -360
            out.append((x + off, y))
        if abs(out[-1][0] - out[0][0]) > 180:          # round the whole globe (Antarctica): close along the pole
            pole = -89.9 if sum(y for _, y in out) < 0 else 89.9
            out += [(out[-1][0], pole), (out[0][0], pole)]
        return out
    for g in topo["objects"]["land"]["geometries"]:
        for poly in ([g["arcs"]] if g["type"] == "Polygon" else g["arcs"]):
            rings = [ring(r) for r in poly]
            xs, ys = [p[0] for p in rings[0]], [p[1] for p in rings[0]]
            LAND.append(((min(xs), min(ys), max(xs), max(ys)), rings))
    return LAND


def wiki_coords(titles):
    """{requested title: (lat, lon)} from the coordinates of English Wikipedia articles."""
    try:
        q = wiki_get(action="query", prop="coordinates", titles="|".join(titles[:20]))["query"]
    except Exception:
        return {}
    final = {t: t for t in titles}
    for step in ("normalized", "redirects"):
        moves = {m["from"]: m["to"] for m in q.get(step, [])}
        final = {t: moves.get(f, f) for t, f in final.items()}
    got = {p["title"]: (p["coordinates"][0]["lat"], p["coordinates"][0]["lon"])
           for p in q.get("pages", []) if p.get("coordinates")}
    return {t: got[f] for t, f in final.items() if f in got}


GEO_WORDS = {"ATOLL", "ISLAND", "ISLANDS", "BAY", "HARBOR", "HARBOUR", "CITY", "PORT", "BASE", "NAVAL", "AIR",
             "STATION", "CAPE", "STRAIT", "SEA", "RIVER", "GULF", "AIRFIELD", "FIELD", "MOUNT", "LAKE", "PENINSULA",
             "BEACH", "CANAL", "FORT", "NORTH", "SOUTH", "EAST", "WEST", "NEW", "BATTLE", "SIEGE", "OPERATION", "THE",
             "OF", "AND"}


def map_prepare(data, topic):
    """Keeps places the article mentions that have Wikipedia coordinates, routes between them and a distance whose
    number is in the article. No map if the target (the first place, the one the headline points at) fails."""
    m = data.get("map") if isinstance(data.get("map"), dict) else {}
    src = topic["text"]
    src_up = ascii_up(src)
    raw = [p if isinstance(p, dict) else {"title": p} for p in (m.get("places") or [])[:5]
           if isinstance(p, (dict, str)) and str(p.get("title", "") if isinstance(p, dict) else p).strip()]
    titles = [str(p["title"]).strip() for p in raw]
    coords = wiki_coords(titles) if titles else {}
    keep, places = {}, []                              # asked place number -> kept place number
    for i, (p, title) in enumerate(zip(raw, titles)):
        name = re.sub(r"\s+", " ", ascii_up(re.sub(r"\s*\(.*?\)", "", title))).strip()
        words = re.findall(r"[A-Z0-9]+", name)
        key = [w for w in words if w not in GEO_WORDS and len(w) > 2] or words
        if title not in coords or not any(re.search(rf"\b{re.escape(w)}\b", src_up) for w in key) \
                or re.search(r"\b(SEA|OCEAN)$", name):
            continue                                   # no coordinates, never named, or a whole sea (no single point)
        lat, lon = coords[title]
        if any(111 * math.hypot(((lon - q["lon"] + 180) % 360 - 180) * math.cos(math.radians(lat)), lat - q["lat"]) < 60
               for q in places):
            continue                                   # the same spot again (a town on the target island)
        label = re.sub(r"\s+", " ", ascii_up(plain(str(p.get("label") or "")))).strip()[:18]
        if not label or (label not in src_up and label not in name):
            label = name[:18]
        keep[i] = len(places)
        places.append({"title": title, "label": label, "lat": lat, "lon": lon})
    head_up = ascii_up(plain(data.get("headline", "")))
    named = [k for k, p in enumerate(places) if re.search(rf"\b{re.escape(p['label'])}\b", head_up)]
    target = named[0] if len(named) == 1 else keep.get(0)   # a place the headline names is the target
    if target is None:
        print("map: the target has no coordinates or is not in the article -> photo opening instead")
        return {**data, "map": None}
    order = [target] + [k for k in range(len(places)) if k != target]
    places, keep = [places[k] for k in order], {i: order.index(k) for i, k in keep.items()}
    for p in places[1:]:                               # across the date line: stay next to the target
        p["lon"] += 360 * round((places[0]["lon"] - p["lon"]) / 360)
    n = len(all_lines(data))

    def ok_label(t):
        t = re.sub(r"\s+", " ", ascii_up(plain(t or ""))).strip()[:22]
        return t if t and nums_in_source(t, src) else ""

    def ref(x):
        try:
            return keep.get(int(x) - 1)
        except (TypeError, ValueError):
            return None

    def line(x):
        try:
            k = int(x)
        except (TypeError, ValueError):
            return None
        return k if 1 <= k <= n else None
    routes = []
    for r in (m.get("routes") or [])[:2]:
        if isinstance(r, dict):
            a, b, ln = ref(r.get("from")), ref(r.get("to")), line(r.get("line"))
            if a is not None and b is not None and a != b and ln:
                routes.append({"from": a, "to": b, "line": ln, "label": ok_label(r.get("label")),
                               "side": r.get("side") if r.get("side") in SIDE_C else "other"})
    d, dist = m.get("distance") if isinstance(m.get("distance"), dict) else {}, None
    if d:
        a, b, ln, lab = ref(d.get("from")), ref(d.get("to")), line(d.get("line")), ok_label(d.get("label"))
        if a is not None and b is not None and a != b and ln and lab:
            dist = {"from": a, "to": b, "line": ln, "label": lab}
    print("map:", [p["label"] for p in places], "| routes:", len(routes), "| distance:", bool(dist))
    return {**data, "map": {"places": places, "routes": routes, "distance": dist}}


def merc(lat):
    lat = max(-84.0, min(84.0, lat))
    return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def view_rect(v, w, h):
    """(lon left, mercator top, lon right, mercator bottom) of the view (lon, lat, width) on a w x h screen."""
    lon, lat, vw = v
    vh, cy = vw * h / w, merc(lat)
    return lon - vw / 2, cy + vh / 2, lon + vw / 2, cy - vh / 2


def map_views(spec):
    """Close (the target), wide (the region, where the cover starts) and a view for any two places."""
    ps = spec["places"]
    lons, lats = [p["lon"] for p in ps], [p["lat"] for p in ps]
    span = max(max(lons) - min(lons), (max(lats) - min(lats)) * 1.4, 1.0)
    close = (ps[0]["lon"], ps[0]["lat"], max(10.0, min(26.0, span * 0.45)))
    wide = ((sum(lons) / len(lons) + ps[0]["lon"]) / 2, (sum(lats) / len(lats) + ps[0]["lat"]) / 2,
            max(close[2] * 2.5, min(45.0, span * 1.3)))

    def pair(i, j):
        a, b = ps[i], ps[j]
        w = max(close[2], abs(a["lon"] - b["lon"]) * 1.6, abs(merc(a["lat"]) - merc(b["lat"])) * 1.6 * 1080 / MID_H)
        return (a["lon"] + b["lon"]) / 2, (a["lat"] + b["lat"]) / 2, w
    return close, wide, pair


class MapArt:
    """The map of one video: land and ocean drawn once over every view it needs, then cut per frame."""

    def __init__(self, spec):
        from PIL import Image, ImageDraw
        self.Image, self.spec = Image, spec
        self.close, self.wide, self.pair = map_views(spec)
        views = [(self.wide, 1080, 1920), (self.close, 1080, 1920), (self.close, 1080, MID_H)]
        views += [(self.pair(r["from"], r["to"]), 1080, MID_H) for r in spec["routes"]]
        if spec.get("distance"):
            views.append((self.pair(spec["distance"]["from"], spec["distance"]["to"]), 1080, MID_H))
        rects = [view_rect(*v) for v in views]
        l0, t0 = min(r[0] for r in rects), max(r[1] for r in rects)
        l1, b1 = max(r[2] for r in rects), min(r[3] for r in rects)
        mx, my = (l1 - l0) * 0.06, (t0 - b1) * 0.06
        self.l0, self.t0, l1, b1 = l0 - mx, t0 + my, l1 + mx, b1 - my
        need = 1.1 * 1080 / min(v[0][2] for v in views)               # px per degree for the closest view
        self.k = min(need, math.sqrt(30e6 / ((l1 - self.l0) * (self.t0 - b1))))
        W, H = int((l1 - self.l0) * self.k), int((self.t0 - b1) * self.k)
        g = Image.linear_gradient("L").resize((W, H))
        base = Image.composite(Image.new("RGB", (W, H), OCEAN_B), Image.new("RGB", (W, H), OCEAN_T), g)
        d = ImageDraw.Draw(base)
        px = lambda lon, lat: ((lon - self.l0) * self.k, (self.t0 - merc(lat)) * self.k)
        step = 10 if l1 - self.l0 > 30 else 5
        for lon in range(int(self.l0 // step * step), int(l1) + step, step):
            d.line([px(lon, 84), px(lon, -84)], fill=GRID_C, width=2)
        for lat in range(-80, 81, step):
            d.line([px(self.l0, lat), px(l1, lat)], fill=GRID_C, width=2)
        lat_lo, lat_hi = -84, 84
        for (bx0, by0, bx1, by1), rings in land_polys():
            for sh in (-360, 0, 360):
                if bx1 + sh < self.l0 or bx0 + sh > l1 or by1 < lat_lo or by0 > lat_hi:
                    continue
                if merc(by1) < b1 or merc(by0) > self.t0:
                    continue
                d.polygon([px(x + sh, y) for x, y in rings[0]], fill=LAND_C)
                for hole in rings[1:]:
                    d.polygon([px(x + sh, y) for x, y in hole], fill=OCEAN_T)
                d.line([px(x + sh, y) for x, y in rings[0]], fill=COAST_C, width=3)
        self.mips = [base]
        for _ in range(3):
            self.mips.append(self.mips[-1].reduce(2))
        self.vig = {}

    def picture(self, v, w, h):
        lo, top, hi, bot = view_rect(v, w, h)
        x0, y0, x1, y1 = (lo - self.l0) * self.k, (self.t0 - top) * self.k, (hi - self.l0) * self.k, (self.t0 - bot) * self.k
        lvl = max(0, min(3, int(math.log2(max(1.0, (x1 - x0) / w)))))
        f = 2 ** lvl
        img = self.mips[lvl].transform((w, h), self.Image.Transform.EXTENT, (x0 / f, y0 / f, x1 / f, y1 / f),
                                       self.Image.Resampling.BICUBIC)
        if (w, h) not in self.vig:                     # darker edges, like an old chart under a lamp
            g = self.Image.radial_gradient("L").resize((w, h)).point(lambda p: max(0, p - 120) * 1.5)
            self.vig[(w, h)] = g
        return self.Image.composite(self.Image.new("RGB", (w, h)), img, self.vig[(w, h)])

    def xy(self, v, lon, lat, w, h, k=1):
        lo, top, hi, bot = view_rect(v, w, h)
        return (lon - lo) / (hi - lo) * w * k, (top - merc(lat)) / (top - bot) * h * k


def map_overlay(art, v, w, h, t, mode=None, k=2, label_a=1.0):
    """Places, the pulsing target, and the route or distance being drawn, supersampled k times."""
    from PIL import Image, ImageDraw, ImageFont
    ov = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    font = lambda s: ImageFont.truetype(str(FONT) if FONT.exists() else FONTS_DIR + "/DejaVuSans-Bold.ttf", int(s * k))
    ps = art.spec["places"]

    def text(xy, txt, size, col, anchor="lm", a=1.0, stroke=5):
        d.text(xy, txt, font=font(size), fill=col + (int(255 * a),), anchor=anchor, stroke_width=int(stroke * k),
               stroke_fill=(0, 0, 0, int(255 * a)))

    taken = []                                         # label boxes: a place name never covers another

    def centred(x, y, txt, size, col, anchor, a=1.0, stroke=5, avoid=False):   # kept inside the frame
        half = d.textlength(txt, font=font(size)) / 2 + 12 * k
        x = max(half, min(w * k - half, x))
        box = d.textbbox((x, y), txt, font=font(size), anchor=anchor, stroke_width=int(stroke * k))
        if avoid and any(box[0] < b[2] and b[0] < box[2] and box[1] < b[3] and b[1] < box[3] for b in taken):
            return
        taken.append(box)
        text((x, y), txt, size, col, anchor, a, stroke)

    def dashed(a, b, p, col, arrow):
        (ax, ay), (bx, by) = a, b
        ln = math.hypot(bx - ax, by - ay)
        if ln < 1 or p <= 0:
            return
        ux, uy, end, pos = (bx - ax) / ln, (by - ay) / ln, ln * min(1.0, p), 0.0
        while pos < end:
            q = min(end, pos + 20 * k)
            d.line([(ax + ux * pos, ay + uy * pos), (ax + ux * q, ay + uy * q)], fill=col + (255,), width=int(4 * k))
            pos += 33 * k
        if arrow:
            tx_, ty_, nx, ny = ax + ux * end, ay + uy * end, -uy, ux
            d.polygon([(tx_ + ux * 17 * k, ty_ + uy * 17 * k), (tx_ + nx * 11 * k, ty_ + ny * 11 * k),
                       (tx_ - nx * 11 * k, ty_ - ny * 11 * k)], fill=col + (255,))
    tx, ty = art.xy(v, ps[0]["lon"], ps[0]["lat"], w, h, k)
    t_right = tx < w * k * 0.62
    t_pos = (tx + 25 * k, ty - 22 * k) if t_right else (tx - 25 * k, ty - 22 * k)
    if label_a > 0:                                    # the target's name has the first claim on the space
        taken.append(d.textbbox(t_pos, ps[0]["label"], font=font(48), anchor="lm" if t_right else "rm",
                                stroke_width=int(6 * k)))
    for p in ps[1:]:                                   # the other places: white dot, grey name under it
        x, y = art.xy(v, p["lon"], p["lat"], w, h, k)
        if 0 <= x <= w * k and 0 <= y <= h * k:
            r = 5.5 * k
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=int(2 * k))
            centred(x, y + 14 * k, p["label"], 30, (215, 215, 215), "mt", avoid=True)
    if mode and mode[0] in ("route", "distance"):
        item = art.spec["routes"][mode[1]] if mode[0] == "route" else art.spec["distance"]
        a, b = art.xy(v, ps[item["from"]]["lon"], ps[item["from"]]["lat"], w, h, k), \
            art.xy(v, ps[item["to"]]["lon"], ps[item["to"]]["lat"], w, h, k)
        col = SIDE_C.get(item.get("side"), (255, 255, 255))
        dashed(a, b, (t - 0.3) / 1.1, col, mode[0] == "route")
        la = max(0.0, min(1.0, (t - 1.2) / 0.25))
        if la and item.get("label"):                   # beside the middle of the line, on its upper side
            ln = max(1.0, math.hypot(b[0] - a[0], b[1] - a[1]))
            nx, ny = (b[1] - a[1]) / ln, -(b[0] - a[0]) / ln
            nx, ny = (nx, ny) if ny <= 0 else (-nx, -ny)
            off = 34 * k + abs(nx) * d.textlength(item["label"], font=font(34)) / 2
            centred((a[0] + b[0]) / 2 + nx * off, (a[1] + b[1]) / 2 + ny * off, item["label"], 34, col, "mm", la, 6)
    x, y = art.xy(v, ps[0]["lon"], ps[0]["lat"], w, h, k)   # the target: radar rings and a red dot
    for ph in ((t * 1.1) % 1, (t * 1.1 + 0.5) % 1):
        r = (12 + 75 * ph) * k
        d.ellipse((x - r, y - r, x + r, y + r), outline=(229, 57, 53, int(255 * (1 - ph))), width=int(3.5 * k))
    r = 10 * k
    d.ellipse((x - r, y - r, x + r, y + r), fill=(229, 57, 53, 255), outline=(255, 255, 255, 255), width=int(3 * k))
    if label_a > 0:
        text(t_pos, ps[0]["label"], 48, (255, 255, 255), "lm" if t_right else "rm", label_a, 6)
    return ov.resize((w, h), Image.Resampling.LANCZOS) if k != 1 else ov


def map_frame(art, v, w, h, t, mode=None, k=2, label_a=1.0):
    img = art.picture(v, w, h)
    ov = map_overlay(art, v, w, h, t, mode, k, label_a)
    img.paste(ov, (0, 0), ov)
    return img


def frames_to(name, frames, w, h):
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                           "-r", "30", "-i", "-", "-vf", "noise=alls=6:allf=t", "-c:v", "utvideo", "-pix_fmt",
                           "yuv420p", name], stdin=subprocess.PIPE, cwd=W)
    for f in frames:
        pr.stdin.write(f.tobytes())
    pr.stdin.close()
    if pr.wait():
        raise RuntimeError("map frames failed: " + name)


def log_lerp(a, b, p):
    e = 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, p)))
    return (a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e, math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * e))


MAP_LOOP_T = 100.0 - round(TAIL_SEC * 30) / 30         # ring clock of the tail: it ends in phase with frame 0


def map_cover_assets(art, clips=True):
    """The map version of the cover: full screen, zooming from the region into the target, then it shrinks into
    the frame over a blurred map; at the end it grows back and zooms out (last frame = first frame)."""
    from PIL import ImageEnhance, ImageFilter
    Image = art.Image
    bd = map_frame(art, art.close, 1080, 1920, 0, k=1, label_a=0).resize((540, 960)).filter(ImageFilter.GaussianBlur(10))
    bd = ImageEnhance.Brightness(bd.resize((1080, 1920), Image.Resampling.BILINEAR)).enhance(0.45)
    if BG == "black":                                  # plain black around the picture (Andrii, Oct 14)
        bd = Image.new("RGB", (1080, 1920), (0, 0, 0))
    bd.save(W / "backdrop.png")
    if not clips:
        return
    ease = lambda p: 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, p)))

    def frame(v, e, t, label_a):
        full = map_frame(art, v, 1080, 1920, t, k=1, label_a=label_a * (1 - e))
        if e <= 0:
            return full
        img = Image.blend(full, bd, e)
        y0, y1 = TOP_BAR * e, 1920 + (TOP_BAR + MID_H - 1920) * e
        win = map_frame(art, v, 1080, int(round(y1 - y0)), t, k=1, label_a=label_a)
        img.paste(win, (0, int(round(y0))))
        return img
    n = round(COVER_T * 30)
    frames_to("cover.mkv", (frame(log_lerp(art.wide, art.close, i / (n - 1)), ease((i / 30 - COVER_SEC) / MORPH_SEC),
                                  i / 30, min(1.0, max(0.0, (i / 30 - 0.35) / 0.3))) for i in range(n)), 1080, 1920)
    nt = round(TAIL_SEC * 30)
    frames_to("tail.mkv", (frame(log_lerp(art.close, art.wide, (i + 1) / nt), ease(1 - (i + 1) / nt),
                                 MAP_LOOP_T + i / 30, 1 - (i + 1) / nt) for i in range(nt)), 1080, 1920)


def render_map_shot(i, sh):
    """The target with its radar rings, or a route / the distance being drawn while the map opens up to show both."""
    art, mode, t0 = LOOK["map_art"], sh.get("mode", ("target",)), sh.get("t0", 0.0)
    n = max(1, round(sh["dur"] * 30))
    if mode[0] == "target":
        frames = (map_frame(art, art.close, 1080, MID_H, t0 + f / 30) for f in range(n))
    else:
        it = art.spec["routes"][mode[1]] if mode[0] == "route" else art.spec["distance"]
        v = art.pair(it["from"], it["to"])
        lead = sh.get("lead", 0.0) - 0.3                 # the line starts drawing 'lead' s into the shot
        frames = (map_frame(art, log_lerp(art.close, v, f / 15), 1080, MID_H, f / 30 - lead, mode) for f in range(n))
    frames_to(f"shot{i}.mkv", frames, 1080, MID_H)
    return f"shot{i}.mkv"


def build_map_sfx(total, path):
    """A sonar ping when the map locks onto the target, a softer one on every map shot."""
    sr = 22050
    buf = [0.0] * int(sr * (total + 0.3))

    def ping(at, amp):
        i0 = int(at * sr)
        for k in range(int(1.2 * sr)):
            if i0 + k < len(buf):
                tt = k / sr
                buf[i0 + k] += amp * (math.sin(2 * math.pi * 1350 * tt) * math.exp(-tt * 4.5)
                                      + 0.4 * math.sin(2 * math.pi * 2700 * tt) * math.exp(-tt * 9))
    ping(COVER_SEC + 0.25 if LOOK.get("cover") else 0.4, 0.22)
    for at in LOOK.get("map_pings", []):
        ping(at, 0.12)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(array.array("h", (int(max(-1.0, min(1.0, v)) * 32000) for v in buf)).tobytes())


# ---- Captions ----------------------------------------------------------------
def ass_time(sec):
    cs = int(round(max(0, sec) * 100))
    return f"{cs // 360000}:{(cs // 6000) % 60:02d}:{(cs // 100) % 60:02d}.{cs % 100:02d}"


def styled_words(t):
    """[(word, colour)] keeping the red/yellow marker colours."""
    out, col = [], WHITE
    for tok in re.split(r"(\[/?[ry]\])", str(t)):
        if tok in ("[r]", "[y]"):
            col = RED if tok == "[r]" else YELLOW
        elif tok in ("[/r]", "[/y]"):
            col = WHITE
        else:
            for w in tok.split():
                if out and not re.search(r"[0-9A-Za-z]", w):   # '[y]James Bond[/y].' -> 'Bond.' not 'Bond .'
                    out[-1] = (out[-1][0] + clean(w), out[-1][1])
                else:
                    out.append((clean(w), col))
    return out


def align(tokens, words, total):
    """Start time of every on-screen word, matched to the voice letter by letter (robust to 'T-34', '1,100')."""
    norm = lambda s: re.sub(r"[^0-9a-z]", "", s.lower())
    stream = [t for w, t, *_ in words for _ in norm(w)]
    need = sum(len(norm(x)) for x in tokens)
    spoken = [w for w in words if norm(w[0])]
    if spoken and len(spoken) == len([x for x in tokens if norm(x)]):   # same word count: match word by word
        it, out = iter(spoken), []
        for tok in tokens:
            out.append(next(it)[1] if norm(tok) else (out[-1] if out else 0.0))
        return out
    voiced = bool(stream) and abs(len(stream) - need) <= max(4, need // 20)
    out, pos = [], 0
    for tok in tokens:
        out.append(stream[min(pos, len(stream) - 1)] if voiced else 0.15 + (total - 0.4) * pos / max(1, need))
        pos += len(norm(tok))
    return out


def timeline(data, words, total):
    """Per spoken line: text, start, end and the start time of every word."""
    head = styled_words(data["headline"])
    body = [styled_words(l) for l in all_lines(data)]
    times = align([w for w, _ in head] + [w for line in body for w, _ in line], words, total)
    HEAD_TL[:] = [(w, c, t) for (w, c), t in zip(head, times[:len(head)])]
    out, k = [], len(head)
    for raw, line in zip(all_lines(data), body):
        ts = times[k:k + len(line)]
        k += len(line)
        out.append({"text": raw, "start": ts[0] if ts else 0.0, "words": [(w, c, t) for (w, c), t in zip(line, ts)]})
    for i, l in enumerate(out):
        l["end"] = out[i + 1]["start"] if i + 1 < len(out) else total
    return out


def text_w(t, size, spacing=0):
    """Width in px of bold DejaVu text drawn by libass at this font size (its line height = size)."""
    return sum(CHAR_W[ord(c) - 32] if 32 <= ord(c) < 127 else 720 for c in t) * size / 1165 + len(t) * spacing


def fit_head(headline):
    """Headline in the box between the category line and the photo: the biggest size whose lines fit, centred.
    Returns (ASS text with line breaks, font size, top y)."""
    words, room = styled_words(headline), TOP_BAR - 20 - HEAD_TOP
    for size in range(78, 38, -2):
        lines, cur = [], []
        for w, c in words:
            if cur and text_w(" ".join(x for x, _ in cur + [(w, c)]), size, 1) > HEAD_W:
                lines.append(cur)
                cur = []
            cur.append((w, c))
        lines.append(cur)
        if len(lines) * size <= room and all(text_w(" ".join(x for x, _ in l), size, 1) <= HEAD_W for l in lines):
            break
    text = "\\N".join(" ".join(f"{{\\c{c}}}{w}" for w, c in line) for line in lines)
    return text, size, HEAD_TOP + (room - len(lines) * size) // 2


def block_x():
    """Left x of the centred channel block: [avatar] CHANNEL."""
    w = text_w(CHANNEL, 40) + (AV_SIZE + 14 if AVATAR.exists() else 0)
    return int(540 - w / 2)


def cold_events(total):
    """Cold open, drawn by libass over the picture: the rewind stamp, documentary time stamps and list cards
    (names appear, then get stamped or struck out on the narrator's word)."""
    T, H = TOP_BAR, MID_H
    ev = lambda layer, s, e, txt: f"Dialogue: {layer},{ass_time(s)},{ass_time(e)},Card,,0,0,0,,{txt}"
    box = lambda x0, y0, x1, y1: f"m {x0} {y0} l {x1} {y0} {x1} {y1} {x0} {y1}"
    plain_box = "\\an7\\pos(0,0)\\p1\\bord0\\shad0"
    out = []
    a, b = COLD["at"], COLD.get("stamp_end", COLD["end"] + 1.0)
    pop = "\\fscx125\\fscy125\\t(0,120,\\fscx100\\fscy100)"
    out.append(ev(4, a, b, f"{{{plain_box}\\1c&H000000&\\1a&H91&}}{box(0, T, 1080, T + H)}"))
    out.append(ev(5, a, b, f"{{\\an5\\pos(540,{T + H // 2 - 60})\\p1\\bord5\\shad0\\1c{RED}\\3c&H000000&{pop}}}"
                           "m 0 50 l 80 0 80 100 m 80 50 l 160 0 160 100"))       # ◀◀ drawn, any font works
    jump, size = COLD.get("jump") or "EARLIER", 95
    while size > 50 and text_w(jump, size) > 900:
        size -= 5
    out.append(ev(5, a, b, f"{{\\an5\\pos(540,{T + H // 2 + 70})\\fs{size}\\bord6\\shad0\\c{WHITE}\\3c&H000000&{pop}}}{jump}"))
    for p in COLD.get("plates", []):                 # documentary time stamp, top-left inside the picture
        s0, e0, y0 = p["start"], p["end"], T + 24
        w = int(max(len(p["text"]) * 0.602 * 35 * 1000 / 1165, text_w(p.get("red", ""), 35)) + 40)   # mono width
        h, fad = (96 if p.get("red") else 54), ("\\fad(120,0)" if s0 > 0.05 else "")   # full on the first frame
        out.append(ev(4, s0, e0, f"{{{plain_box}\\1c&H000000&\\1a&H4B&{fad}}}{box(124, y0, 124 + w, y0 + h)}"))
        out.append(ev(5, s0, e0, f"{{{plain_box}\\1c{RED}{fad}}}{box(124, y0, 131, y0 + h)}"))
        out.append(ev(5, s0, e0, f"{{\\an4\\pos(148,{y0 + 27})\\fnDejaVu Sans Mono\\fs35\\bord0\\shad0\\c{WHITE}"
                                 f"{fad}}}{p['text']}"))
        if p.get("red"):
            out.append(ev(5, s0, e0, f"{{\\an4\\pos(148,{y0 + 69})\\fs35\\bord0\\shad0\\c{RED}{fad}}}{p['red']}"))
    for c in COLD.get("cards", []):
        on, off, items, mk = c["on"], c["off"], c["items"], c.get("mark") or {}
        stamp, n = mk.get("style") == "stamp", len(items)
        two = n > 3
        size = 72
        while size > 44 and max(text_w(x, size) for x in items) > (470 if stamp else 400 if two else 800):
            size -= 2
        out.append(ev(4, on, off, f"{{{plain_box}\\1c&H000000&\\1a&H41&\\fad(100,100)}}{box(0, T, 1080, T + H)}"))
        if c.get("title"):
            out.append(ev(5, on, off, f"{{\\an5\\pos(540,{T + 105})\\fs35\\fsp6\\bord0\\shad0\\c{ACC_ASS}"
                                      f"\\fad(100,100)}}{c['title']}"))
        per, pos = ((n + 1) // 2 if two else n), []
        for i, name in enumerate(items):
            col, row = (i // per, i % per) if two else (0, i)
            x, y = ((320, 760)[col] if two else 150 if stamp else 540), T + 235 + row * 140 + (3 - per) * 70
            pos.append((x, y))
            out.append(ev(5, on + 0.12 * i, off, f"{{\\an{4 if stamp else 5}\\pos({x},{y})\\fs{size}\\bord0\\shad0"
                                                 f"\\c{WHITE}\\fad(80,100)}}{name}"))
        for i, t in zip(mk.get("items", []), c.get("marks", [])):
            x, y = pos[i]
            if stamp:                                 # a rubber stamp slams in next to the name
                bw, slam = int(text_w(mk["label"], 51) + 32), "\\fscx145\\fscy145\\t(0,70,\\fscx100\\fscy100)"
                rot = f"\\an5\\pos(790,{y})\\org(790,{y})\\frz8"
                out.append(ev(6, t, off, f"{{{rot}\\p1\\bord5\\shad0\\1a&HFF&\\3c{RED}{slam}}}{box(0, 0, bw, 64)}"))
                out.append(ev(6, t, off, f"{{{rot}\\fs51\\bord0\\shad0\\c{RED}{slam}}}{mk['label']}"))
            else:                                     # struck through (thicker for 2 frames), the label under it
                w = text_w(items[i], size) / 2 + 24
                pts = lambda d: (f"m {x - w:.0f} {y + 9 - d:.0f} l {x + w:.0f} {y - 9 - d:.0f} "
                                 f"{x + w:.0f} {y - 9 + d:.0f} {x - w:.0f} {y + 9 + d:.0f}")
                for th, s1, e1 in ((15, t, t + 0.07), (11, t + 0.07, off)):
                    out.append(ev(6, s1, e1, f"{{{plain_box}\\1c&H000000&}}{pts(th / 2 + 3)}"))
                    out.append(ev(7, s1, e1, f"{{{plain_box}\\1c{RED}}}{pts(th / 2)}"))
                out.append(ev(6, t, off, f"{{\\an5\\pos({x},{y + 54})\\fs35\\bord0\\shad0\\c{RED}}}{mk['label']}"))
    return out


CAP_SMALL = {"the", "a", "an", "and", "but", "or", "of", "to", "in", "on", "at", "for", "by", "with", "from", "into",
             "that", "this", "these", "those", "was", "were", "had", "has", "have", "his", "her", "their", "its",
             "they", "them", "then", "than", "there", "which", "when", "what", "would", "could", "about", "after",
             "before", "every", "while", "where", "who", "whom", "just", "only", "still", "never", "because"}


def cap_phrases(lines, most=4):
    """Spoken lines [(words [(w, colour, t)], end)] cut into short phrases (cut after punctuation, never after a
    small word or inside a name, no single word left over): [(words, start, end)]."""
    out = []
    for ws, end in lines:
        ws = [x for x in ws if re.search(r"[0-9A-Za-z]", x[0])]
        parts, cur = [], []
        weak = lambda w, nxt: (re.sub(r"\W", "", w).lower() in CAP_SMALL      # 'HELD THE' / 'IRON' | 'CROSS':
                               or w[:1].isupper() and nxt[:1].isupper())        # no cut after these
        for j, x in enumerate(ws):
            cur.append(x)
            if len(cur) >= 2 and re.search(r"[,.;:!?\u2014]$", x[0]):
                parts.append(cur)
                cur = []
            elif len(cur) >= most and not (len(cur) == most and j + 1 < len(ws)   # '... DOUBTED HIM,' waits
                                               and re.search(r"[,.;:!?\u2014]$", ws[j + 1][0])):
                k, nxt = len(cur), ws[j + 1][0] if j + 1 < len(ws) else ""   # cut after the last strong word
                while k > 1 and weak(cur[k - 1][0], cur[k][0] if k < len(cur) else nxt):
                    k -= 1
                k = k if k > 1 else len(cur)
                parts.append(cur[:k])
                cur = cur[k:]
        if len(cur) == 1 and parts:                    # never a single word left over
            parts[-1] = parts[-1] + cur
        elif cur:
            parts.append(cur)
        for j, p in enumerate(parts):
            out.append((p, p[0][2], parts[j + 1][0][2] if j + 1 < len(parts) else end))
    return out


def cap_word(w):
    return re.sub(r"[,.;:]+$", "", w).upper()


def cap_lit(ws, b):
    """Karaoke timing of a phrase [(w, colour, t)] shown until b: each word lit from its start to the next one."""
    ts = [t for _, _, t in ws] + [b]
    return [(ts[i], max(ts[i], ts[i + 1])) for i in range(len(ws))]


def cap_line(ws, lit, y, size, t0, t1, layer=6, fade=70, width=860):
    """One line of words centred at the top y, shown from t0 to t1; the word being spoken (lit = its (start, end)
    per word) sits on a crimson box drawn under the text, word by word (Andrii, Oct 25)."""
    ws = [cap_word(w) for w in ws]
    size = int(min(size, size * width / max(1.0, text_w(" ".join(ws), size))))
    sp, wid = text_w(" ", size), [text_w(w, size) for w in ws]
    x0, pad = 540 - (sum(wid) + sp * (len(ws) - 1)) / 2, size * 0.22
    cuts = sorted({t0, t1} | {t for se in lit for t in se if t0 < t < t1})
    out = []
    for p, q in zip(cuts, cuts[1:]):
        if q - p < 0.01:
            continue
        k = next((i for i, (s0, s1) in enumerate(lit) if s0 <= p < s1), -1)
        fad = f"\\fad({fade},0)" if p == t0 else ""   # fades in once, then only the box moves
        ev = lambda l, txt: f"Dialogue: {l},{ass_time(p)},{ass_time(q)},Cap,,0,0,0,,{txt}"
        if k >= 0:
            bx = x0 + sum(wid[:k]) + sp * k
            out.append(ev(layer, f"{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{CAP_BOX}{fad}}}"
                                 f"m {bx - pad:.0f} {y + size * 0.04:.0f} l {bx + wid[k] + pad:.0f} {y + size * 0.04:.0f} "
                                 f"{bx + wid[k] + pad:.0f} {y + size * 0.96:.0f} {bx - pad:.0f} {y + size * 0.96:.0f}"
                                 "{\\p0}"))
        words = [f"{{\\bord0\\shad0}}{w}{{\\bord3\\shad2}}" if i == k else w for i, w in enumerate(ws)]
        out.append(ev(layer + 1, f"{{\\an8\\pos(540,{y})\\fs{size}{fad}}}" + " ".join(words)))
    return out


def caption_style():
    return (f"Style: Cap,DejaVu Sans,64,{WHITE},{WHITE},&H00000000&,&H90000000&,-1,0,0,0,100,100,0,0,1,3,2,"
            "8,0,0,0,1")


def captions_two(tl, until, head=(), first=0.0, y1=1240, y2=1310):
    """The captions of both formats (Andrii, Oct 24-25): phrases of up to 5 words in two lines, like a headline: the
    start small and white, the last one or two words big under it; the word being spoken on its crimson box, word by
    word. head = the spoken title with its word times, captioned the same way (one text, not a title on top plus
    captions); the first phrase from `first` s (classic: 0.35, the clean first frame is the thumbnail)."""
    out = []
    lines = ([(list(head), tl[0]["start"] if tl else until)] if head else []) + [(l["words"], l["end"]) for l in tl]
    for k, (ws, a, b) in enumerate(cap_phrases(lines, most=5)):
        a, b = (first if k == 0 else max(first, a)), min(until - 0.05, b)
        if b - a <= 0.08:
            continue
        words, lit = [w for w, _, _ in ws], cap_lit(ws, b)
        fits = lambda ws: text_w(" ".join(map(cap_word, ws)), 80) <= 860
        cut = len(words) - (2 if len(words) > 2 and fits(words[-2:]) else 1)
        if cut == 1 and fits(words):                   # no lonely 'IN' on the small line
            cut = 0
        if cut > 0:
            out += cap_line(words[:cut], lit[:cut], y1, 56, a, b)
        out += cap_line(words[cut:], lit[cut:], y2, 80, a, b)
    return out


def build_ass_a(data, total, tl=()):
    """Style A: the captions (the spoken title first), then the title in small spaced white capitals top left once
    the title has been read, like the jurgen Shorts (Andrii, Oct 25)."""
    title = clean(plain(data.get("title") or data["headline"])).upper()
    t0 = min(total, (tl[0]["start"] if tl else 0.0) + 0.35) if CAPS else 0.35   # frame 0 clean: the thumbnail
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0",
             "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
             "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
             "Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: Title,{font_family()},46,{WHITE},{WHITE},&H00000000&,&H90000000&,-1,0,0,0,100,100,7,0,1,0,3,"
             "7,70,150,250,1", caption_style(), "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
             f"Dialogue: 1,{ass_time(t0)},{ass_time(total)},Title,,0,0,0,,{{\\fad(250,0)}}{title}"]
    for k in range(12):                                # a soft dark fade behind the title (light skies)
        a = format(0x70 + k * 0x0B, "02X")
        lines.append(f"Dialogue: 0,{ass_time(t0)},{ass_time(total)},Title,,0,0,0,,{{\\an7\\pos(0,{k * 45})\\p1"
                     f"\\bord0\\shad0\\1c&H000000&\\1a&H{a}&}}m 0 0 l 1080 0 1080 45 0 45{{\\p0}}")
    if CAPS:
        lines += captions_two(tl, total, HEAD_TL, first=0.35)
    path = W / "subs.ass"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_ass(data, tl, shots, total):
    if STYLE_A:
        return build_ass_a(data, total, tl)
    fam = font_family()
    cs, ce = (COVER_SEC + MORPH_SEC * 0.4, total - TAIL_SEC + 0.2) if LOOK.get("cover") else (0, total)
    bs, bfad = max(cs, min(BRAND_SEC, total / 4)), "{\\fad(250,250)}"   # frame 0: the hook alone
    style = lambda name, size, col, sp, out, sh, al, ml, mr, mv, back="&H00000000&": (
        f"Style: {name},{fam},{size},{col},{col},&H00000000&,{back},-1,0,0,0,100,100,{sp},0,1,{out},{sh},"
        f"{al},{ml},{mr},{mv},1")
    ev = lambda layer, s, e, st, txt: f"Dialogue: {layer},{ass_time(s)},{ass_time(e)},{st},,0,0,0,,{txt}"
    lines = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 0",
             "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
             "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
             "Alignment, MarginL, MarginR, MarginV, Encoding",
             style("Label", 40, ACC_ASS, 6, 0, 0, 8, 60, 60, LABEL_Y),
             style("Head", 76, WHITE, 1, 4, 2, 8, 120, 120, HEAD_TOP),   # outline: readable over the cover too
             style("Body", 58, WHITE, 0, 3, 0, 8, 170, 170, BOT_Y + 24),   # centered, clear of the buttons; thin outline
             style("Big", 150, WHITE, 4, 9, 4, 5, 0, 0, 0, "&H64000000&"),
             style("Wait", 96, ACC_ASS, 6, 8, 4, 5, 0, 0, 0, "&H64000000&"),
             style("Chan", 40, WHITE, 0, 0, 0, 4, 0, 0, 0),
             style("Handle", 30, "&H00AAAAAA&", 0, 0, 0, 8, 0, 0, 0),
             style("Card", 72, WHITE, 0, 0, 0, 5, 0, 0, 0),
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
             ev(0, bs, ce, "Label", bfad + (f"{LABEL}  ·  PART {PART}/2" if PART else f"{LABEL}  ·  #{FILE_NO}")),
             ev(3, bs, ce, "Chan", f"{{\\pos({block_x() + (AV_SIZE + 14 if AVATAR.exists() else 0)},"
                                   f"{BLOCK_Y + AV_SIZE // 2}){bfad[1:-1]}}}{CHANNEL}"),
             ev(3, bs, ce, "Handle", f"{{\\pos(540,{BLOCK_Y + AV_SIZE + 6}){bfad[1:-1]}}}{HANDLE}")]
    head, size, top = fit_head(data["headline"])                       # visible on the very first frame
    lines.append(f"Dialogue: 0,{ass_time(0)},{ass_time(ce)},Head,,0,0,{top},,{{\\q2\\fs{size}\\fad(0,250)}}{head}")
    for l in tl:   # word by word: spoken words solid, the current one pops, upcoming ones dimmed
        ws = l["words"]
        for j, (w, col, t) in enumerate(ws):
            end = ws[j + 1][2] if j + 1 < len(ws) else l["end"]
            if end - t < 0.02:
                continue
            parts = [f"{{\\c{c}\\alpha&H00&\\fscy100}}{x}" if i < j else
                     f"{{\\c{c}\\alpha&H00&\\fscy118\\t(0,110,\\fscy100)}}{x}" if i == j else
                     f"{{\\c{c}\\alpha&H88&\\fscy100}}{x}" for i, (x, c, _) in enumerate(ws)]
            lines.append(ev(1, t, end, "Body", " ".join(parts)))
    t, cy = 0.0, TOP_BAR + MID_H // 2
    for sh in shots:
        if sh["kind"] == "split":
            lines.append(ev(2, t, t + sh["dur"], "Big",
                            f"{{\\pos(540,{cy})\\c{ACC_ASS}\\fscx40\\fscy40\\t(0,180,\\fscx100\\fscy100)}}VS"))
        elif sh["kind"] == "pixel":
            lines.append(ev(2, t, t + sh["dur"], "Big",
                            f"{{\\pos(540,{cy})\\c{ACC_ASS}\\t(0,{int(sh['dur'] * 1000)},\\fscx125\\fscy125)}}?"))
        elif sh["kind"] == "punch" and SCALE and not sh.get("cold"):   # the headline's number slams in
            m = re.search(r"\d[\d,.]*\d|\d", plain(data["headline"]))
            val = int(re.sub(r"[^\d]", "", m.group())) if m and "." not in m.group() else 0
            if val >= 100 and not (1900 <= val <= 1950):          # skip years
                # full number on the very first frame (it is the hook), slamming in, then a short shake
                lines.append(ev(2, t, t + sh["dur"], "Big",
                                f"{{\\pos(540,{cy})\\c{ACC_ASS}\\fscx135\\fscy135\\t(0,160,\\fscx90\\fscy90)"
                                f"\\t(160,260,\\fscx100\\fscy100)\\t({int(sh['dur'] * 1000) - 250},{int(sh['dur'] * 1000)},"
                                f"\\alpha&HFF&)}}{val:,}"))
        elif sh["kind"] == "tease":
            lines.append(ev(2, t, t + sh["dur"], "Wait",
                            f"{{\\pos(540,{cy})\\fscx70\\fscy70\\t(0,200,\\fscx100\\fscy100)"
                            f"\\t(600,1300,\\alpha&H40&)}}WAIT FOR IT"))
        t += sh["dur"]
    if PART == 1:                                    # part 1 ends by sending viewers to part 2
        lines.append(ev(2, max(0, total - 2.2), total, "Wait", f"{{\\pos(540,{cy})\\fad(250,0)\\fs84}}PART 2"
                                                              f"{{\\fs40}}\\NON THE CHANNEL"))
    if COLD.get("at"):
        lines += cold_events(total)
    path = W / "subs.ass"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---- Audio -------------------------------------------------------------------
async def _tts(text, path):
    import edge_tts
    rate = COLD_RATE if COLD.get("fast") else TTS_RATE
    try:
        comm = edge_tts.Communicate(text, VOICE, rate=rate, pitch=TTS_PITCH, boundary="WordBoundary")
    except TypeError:
        comm = edge_tts.Communicate(text, VOICE, rate=rate, pitch=TTS_PITCH)
    words = []
    with open(path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append((chunk["text"], chunk["offset"] / 1e7))
    return words


def azure_tts(text, path):
    """Microsoft's official Speech service: the same neural voice as Edge (VOICE, e.g. en-GB-RyanNeural), the same
    rate, real word timings. Free tier F0 = 0.5 million characters a month (about 70k are needed)."""
    import azure.cognitiveservices.speech as sdk
    cfg = sdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
    cfg.set_speech_synthesis_output_format(sdk.SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3)
    syn = sdk.SpeechSynthesizer(speech_config=cfg, audio_config=sdk.audio.AudioOutputConfig(filename=str(path)))
    words = []
    syn.synthesis_word_boundary.connect(lambda e: words.append((e.text, e.audio_offset / 1e7))
                                        if e.boundary_type == sdk.SpeechSynthesisBoundaryType.Word else None)
    rate = COLD_RATE if COLD.get("fast") else TTS_RATE
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{"-".join(VOICE.split("-")[:2])}">'
            f'<voice name="{VOICE}"><prosody rate="{rate}" pitch="{TTS_PITCH}">{html.escape(text)}</prosody></voice></speak>')
    r = syn.speak_ssml_async(ssml).get()
    del syn                                            # closes the mp3 file
    if r.reason != sdk.ResultReason.SynthesizingAudioCompleted:
        det = r.cancellation_details if r.reason == sdk.ResultReason.Canceled else None
        raise RuntimeError(f"{r.reason} {getattr(det, 'error_details', '') or ''}"[:200])
    return words


LEXICON = pathlib.Path("pronounce.json")               # names the voice gets wrong -> how to say them
DIGIT = "oh one two three four five six seven eight nine".split()
LETTER = {"A": "ay", "B": "bee", "C": "see", "D": "dee", "E": "ee", "F": "eff", "G": "gee", "H": "aitch", "I": "eye",
          "J": "jay", "K": "kay", "L": "el", "M": "em", "N": "en", "O": "oh", "P": "pee", "Q": "cue", "R": "ar",
          "S": "ess", "T": "tee", "U": "you", "V": "vee", "W": "double-you", "X": "ex", "Y": "why", "Z": "zed"}
SAY_PREFIX = {"Me": "em-ee", "Bf": "bee-eff", "Ju": "yoo", "He": "aitch-ee", "Fw": "eff-double-you", "Do": "dee-oh",
              "Ar": "ay-ar", "Hs": "aitch-ess", "Ki": "kee", "Il": "eel", "Yak": "yak", "La": "lah"}


MACRONS = str.maketrans("āēīōūĀĒĪŌŪ", "aeiouAEIOU")


def respell(text, extra=None):
    """The narration as the voice should say it (captions keep the real spelling). Measured on Ryan (Oct 18):
    syllables in CAPITALS are read letter by letter ('TOH-moh-NAH-gah' 1.7 s instead of 0.8 s), 'U-234' as two
    hundred thirty-four, 'DE-771' as D E seven hundred... So: U-boats and hull numbers digit by digit
    ('U-two-three-four', 'dee-ee-seven-seven-one'), aircraft types by letters ('em-ee two-six-two'), then the curated
    lexicon pronounce.json, then Gemini's suggestions, all lowercase syllables joined by hyphens."""
    word = lambda n: "-".join(DIGIT[int(c)] for c in n)
    # Andrii, Oct 22 (Yamato test, A/B by ear): plain names beat hyphenated syllables ('Kosaku Aruga', not
    # 'koh-sah-koo ah-roo-gah', which sounded spelled out). Macrons go (Itō -> Ito, Ōi -> Oi) and the writer's
    # respellings are used only for names with other non-English letters (Lütjens, Schön); the lexicon still wins.
    text = text.translate(MACRONS)
    t = re.sub(r"\bU-(\d{2,4})\b", lambda m: "U-" + word(m.group(1)), text)
    t = re.sub(r"\b([A-Z]{2,3})-(\d{1,4})\b", lambda m: "-".join(LETTER[c] for c in m.group(1)) + "-" + word(m.group(2)), t)
    t = re.sub(r"\b(" + "|".join(SAY_PREFIX) + r") (\d{2,3})\b", lambda m: SAY_PREFIX[m.group(1)] + " " + word(m.group(2)), t)
    lex = {}
    try:
        lex = {k: v for k, v in json.loads(LEXICON.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    except Exception as e:
        print("pronounce.json not read:", type(e).__name__)
    pairs, taken = list(lex.items()), {n.lower() for k in lex for n in k.split("|")}
    for name, say in (extra or {}).items():            # Gemini's respellings, made safe: lowercase, no spaces
        name, say = str(name).strip().translate(MACRONS), re.sub(r"\s+", "-", str(say).strip().lower())
        if name.isascii():                             # plain Latin letters: the voice reads it right as written
            continue
        if name and name.lower() not in taken and re.fullmatch(r"[a-z'-]{2,40}", say):
            pairs.append((name, say))
    for names, say in sorted(pairs, key=lambda p: -len(p[0])):   # longest first: 'Johann-Heinrich' before 'Johann'
        for n in names.split("|"):
            t = re.sub(rf"(?<![\w-]){re.escape(n)}(?![\w-])", say, t)
    return t


def speak(text, path, tries=3):
    """Edge TTS first (free, no account; Microsoft refuses it with 403 since Oct 10, 2026 - edge-tts is installed
    unpinned, so a fixed release brings it back by itself) -> Azure Speech (official, the same Ryan voice, if a key
    is set) -> the offline Kokoro voice, so the video is always made. The engine used goes into the stats."""
    TTS_USED[:] = []
    if TTS_ENGINE in ("auto", "edge"):
        for k in range(tries):
            try:
                words = asyncio.run(_tts(text, path))
                if path.exists() and path.stat().st_size > 1000:
                    TTS_USED.append("edge")
                    return words
                raise RuntimeError("no audio received")
            except Exception as e:
                print("Edge voice failed:", type(e).__name__, str(e)[:120])
                if TTS_ENGINE == "edge" and k == tries - 1:
                    raise
                if "403" in str(e) or k == tries - 1:  # refused: retrying does not help
                    break
                time.sleep(5 * (k + 1))
    if AZURE_KEY and AZURE_REGION and TTS_ENGINE in ("auto", "azure"):
        for k in range(2):
            try:
                words = azure_tts(text, path)
                if path.exists() and path.stat().st_size > 1000 and words:
                    TTS_USED.append("azure")
                    return words
                raise RuntimeError("no audio or no word timings")
            except Exception as e:
                print("Azure voice failed:", type(e).__name__, str(e)[:160])
                time.sleep(3)
    print("voice: Edge and Azure unavailable -> offline Kokoro voice")
    TTS_USED.append("kokoro")
    return kokoro_tts(text, path)


ORDS = ("first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth fourteenth "
        "fifteenth sixteenth seventeenth eighteenth nineteenth").split()
MONTH_NAMES = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"


def say_ordinal(n):
    """5 -> 'fifth', 20 -> 'twentieth', 31 -> 'thirty-first'."""
    if n < 20:
        return ORDS[n - 1]
    return TENS[n // 10][:-1] + "ieth" if n % 10 == 0 else TENS[n // 10] + "-" + ORDS[n % 10 - 1]


def kokoro_say(text):
    """Years and dates as a person says them, for the Kokoro voice only (its espeak reads '1943' as 'one thousand
    nine hundred and forty-three' and '5 July' as 'five July'; Edge/Azure Ryan read them right):
    '1943' -> 'nineteen forty three', '1905' -> 'nineteen oh five', '5 July' -> 'the fifth of July',
    'March 6' -> 'March sixth'."""
    year = lambda m: ONES[int(m.group(1))] + " " + (
        "hundred" if m.group(2) == "00" else "oh " + ONES[int(m.group(2))] if m.group(2)[0] == "0"
        else spell_num(int(m.group(2))))
    t = re.sub(r"(?<![\d,.])\b(1[1-9])(\d\d)\b(?![,.]?\d)", year, text)
    day = lambda n: say_ordinal(int(n)) if 1 <= int(n) <= 31 else n
    t = re.sub(rf"\b(?:([Tt]he)\s+)?(\d{{1,2}})\s+({MONTH_NAMES})\b",
               lambda m: f"{m.group(1) or 'the'} {day(m.group(2))} of {m.group(3)}", t)
    return re.sub(rf"\b({MONTH_NAMES})\s+(\d{{1,2}})\b(?![,.]?\d)", lambda m: f"{m.group(1)} {day(m.group(2))}", t)


def kokoro_tts(text, path):
    """Kokoro-82M on the CPU (free, offline). It gives no word times, so each sentence is spoken on its own (silence
    trimmed) and its words share the sentence's time by their phoneme length, plus pauses after punctuation."""
    import numpy as np
    from kokoro_onnx import Kokoro
    KOKORO_DIR.mkdir(parents=True, exist_ok=True)
    for name in KOKORO_FILES:
        f = KOKORO_DIR / name
        if not f.exists() or f.stat().st_size < 1_000_000:
            print("kokoro: downloading", name)
            tmp = f.with_name(name + ".part")
            with requests.get(KOKORO_URL + name, stream=True, timeout=(15, 120)) as r, open(tmp, "wb") as out:
                r.raise_for_status()
                for chunk in r.iter_content(1 << 20):
                    out.write(chunk)
            tmp.replace(f)
    k = Kokoro(str(KOKORO_DIR / KOKORO_FILES[0]), str(KOKORO_DIR / KOKORO_FILES[1]))
    rate = COLD_RATE if COLD.get("fast") else TTS_RATE
    speed = 1.05 + int(re.sub(r"[^\d-]", "", rate) or 0) / 100   # its pace is a bit slower than Edge's
    sr, parts, words, t = 24000, [], [], 0.0
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        ws = sent.split()
        if not ws:
            continue
        a, sr = k.create(kokoro_say(sent), voice=KOKORO_VOICE, speed=speed, lang="en-gb")
        loud = np.nonzero(np.abs(a) > 0.02)[0]
        if len(loud):
            a = a[max(0, loud[0] - int(0.02 * sr)):loud[-1] + int(0.05 * sr)]
        wt = [len(k.tokenizer.phonemize(kokoro_say(w), "en-gb").replace(" ", "")) + 1.0 for w in ws]
        ps = [3.0 if w[-1] in ".:!?" else 1.5 if w[-1] in ",;" else 0.0 for w in ws]
        tot, acc, dur = sum(wt) + sum(ps[:-1]), 0.0, len(a) / sr
        for w, x, p in zip(ws, wt, ps):
            words.append((w.strip(".,:;!?\"'"), t + acc / tot * dur))
            acc += x + p
        gap = np.zeros(int(0.15 * sr), dtype=a.dtype)
        parts += [a, gap]
        t += dur + len(gap) / sr
    wav = path.with_suffix(".wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(np.concatenate(parts), -1, 1) * 32767).astype("<i2").tobytes())
    ff("-i", str(wav.resolve()), "-b:a", "128k", str(path.resolve()))
    print("voice: Kokoro", KOKORO_VOICE, "|", len(words), "words |", round(t, 1), "s")
    return words


def tighten(path, words):
    """Removes the silence before the first word (the voice starts on frame 1) and cuts every pause longer than
    0.18 s down to ~0.08 s; the word timings are shifted to match."""
    log = subprocess.run(["ffmpeg", "-i", str(path), "-af", "silencedetect=noise=-40dB:d=0.05", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    pairs = list(zip([float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", log)],
                     [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]))
    cuts = [(a + 0.04, b - 0.04) for a, b in pairs if b - a > 0.18 and a > 0.01]   # pauses -> ~0.08 s
    if pairs and pairs[0][0] <= 0.01 and pairs[0][1] > 0.04:   # leading silence
        cuts.insert(0, (0.0, pairs[0][1] - 0.02))
    if not cuts:
        return words
    keep, prev = [], 0.0
    for a, b in cuts:
        if a > prev:
            keep.append(f"between(t,{prev:.3f},{a:.3f})")
        prev = b
    keep.append(f"gte(t,{prev:.3f})")
    tmp = path.with_name("voice_tight.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-af",
                    f"aselect='{'+'.join(keep)}',asetpts=N/SR/TB", str(tmp)], check=True)
    tmp.replace(path)
    shift = lambda t: t - sum(b - a for a, b in cuts if b <= t + 0.001)
    return [(w[0], max(0.0, shift(w[1])), *w[2:]) for w in words]


def insert_rewind(path, at, dur=REWIND):
    """Cold open: right after the first sentence the tape rewinds: that sentence plays backwards and fast (pitch
    up, like a cassette) with a whine, in a gap of `dur` seconds; everything after it moves later by `dur`."""
    k = max(1.5, at / dur)
    tmp = path.with_name("voice_cold.mp3")
    fc = (f"[0:a]aresample=44100,asplit=3[a][b][c];[a]atrim=0:{at:.3f},asetpts=PTS-STARTPTS[h];"
          f"[b]atrim=0:{at:.3f},asetpts=PTS-STARTPTS,areverse,asetrate={44100 * k:.0f},aresample=44100,"
          f"atrim=0:{dur:.3f},volume=0.55[rv];"
          f"aevalsrc='0.16*sin(2*PI*(2600*t-{900 / dur:.2f}*t*t))*(0.7+0.3*sin(2*PI*33*t))':s=44100:d={dur:.3f}[wh];"
          f"[rv][wh]amix=inputs=2:normalize=0:duration=longest,apad=whole_dur={dur:.3f},atrim=0:{dur:.3f},"
          f"afade=t=in:d=0.04,afade=t=out:st={dur - 0.06:.3f}:d=0.06[rw];"
          f"[c]atrim=start={at:.3f},asetpts=PTS-STARTPTS[r];[h][rw][r]concat=n=3:v=0:a=1[out]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-filter_complex", fc, "-map", "[out]",
                    "-ac", "1", "-b:a", "128k", str(tmp)], check=True)
    tmp.replace(path)


def word_time(line, word):
    """When `word` is spoken in a timeline line (None if it is not in that line)."""
    key = re.sub(r"[^a-z0-9']", "", str(word).lower().replace("’", "'"))
    for w, _, t in line["words"]:
        if key and re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'")) == key:
            return t
    return None


def cold_times(data, tl, total):
    """Cold open on the timeline: the rewind stamp, the time stamps, the list cards and their marks, the ticking."""
    out = {"alarm": data.get("alarm") is True, "jump": data.get("jump") or "EARLIER", "plates": [], "cards": [],
           "marks": []}
    if not tl:
        return out
    t_jump = next((t for w, _, t in tl[0]["words"] if re.match(r"(earlier|before)\b", w.lower())), None)
    out["stamp_end"] = max(COLD.get("end", 0) + 0.7,       # readable even if the word timing is off
                           min(tl[0]["end"], (t_jump + 0.4) if t_jump is not None else tl[0]["start"] + 1.0))
    out["payoff"] = tl[-2]["start"] if len(tl) >= 2 else total
    for c in data.get("cards") or []:
        if c["line"] > len(tl):
            continue
        ln = tl[c["line"] - 1]
        on = word_time(ln, c.get("at")) or ln["start"] + 0.3
        off, marks = ln["end"], []
        mk = c.get("mark")
        if mk and mk["line"] <= len(tl):
            ml = tl[mk["line"] - 1]
            first = max(on + 0.3, word_time(ml, mk.get("at")) or ml["start"] + 0.35 * (ml["end"] - ml["start"]))
            step = max(0.12, min(0.3, (ml["end"] - 0.25 - first) / max(1, len(mk["items"]) - 1)))
            marks = [first + i * step for i in range(len(mk["items"]))]
            off = max(ml["end"], marks[-1] + 0.6)
        out["cards"].append({**c, "on": on, "off": min(off, total - 0.3), "marks": marks})
        out["marks"] += marks
    for p in data.get("plates") or []:
        if p["line"] == 0:
            spans = ([(COVER_T, COLD.get("at", 1.5))] if LOOK.get("cover") else
                     [(0.0, COLD.get("at", 1.5)), (total - 0.5, total)])
        elif p["line"] <= len(tl):
            spans = [(tl[p["line"] - 1]["start"] + 0.15, tl[p["line"] - 1]["end"])]
        else:
            continue
        for a, b in spans:                            # never on top of a card
            for c in out["cards"]:
                if c["on"] < b and c["off"] > a:
                    a, b = (a, c["on"]) if c["on"] > a else (c["off"], b)
            if b - a > 0.3:
                out["plates"].append({**p, "start": a, "end": b})
    return out


def build_sfx(total, timed, cuts, shots, path, real=False):
    """Synthesized sounds. Discrete effects never closer than 1 s (the most important wins); under them a low
    tension bed that keeps rising and cuts off on the last frame, so the loop restarts the tension."""
    sr = 22050
    buf = [0.0] * int(sr * (total + 0.05))
    rnd = random.Random(len(timed) * 31 + int(total * 10))

    def add(start, samples, gain=1.0):
        i0 = int(start * sr)
        for k, v in enumerate(samples[:max(0, len(buf) - i0)]):
            buf[i0 + k] += v * gain

    def noise(n, alpha):                              # low-passed noise
        y, out = 0.0, []
        for _ in range(n):
            y += alpha * (rnd.uniform(-1, 1) - y)
            out.append(y)
        return out

    def tap():
        n = int(0.05 * sr)
        nz = noise(n, 0.18)
        return [nz[k] * math.exp(-k / (0.008 * sr)) * 0.9 +
                0.25 * math.sin(2 * math.pi * 180 * k / sr) * math.exp(-k / (0.012 * sr)) for k in range(n)]

    def whoosh(d=0.5):
        n, y, out = int(d * sr), 0.0, []
        for k in range(n):
            p = k / n
            y += (0.03 + 0.2 * math.sin(math.pi * p)) * (rnd.uniform(-1, 1) - y)
            out.append(y * math.sin(math.pi * p) ** 2)
        return out

    def boom(f0=55, d=1.4, nmix=0.3):
        n, ph, out = int(d * sr), 0.0, []
        nz = noise(n, 0.05)
        for k in range(n):
            t = k / sr
            ph += 2 * math.pi * f0 * (1 - 0.35 * t / d) / sr
            out.append((math.sin(ph) + nmix * nz[k] * 3) * math.exp(-t / (d * 0.3)))
        return out

    def funny():                                       # a silly sound that does not match the picture
        kind, n, ph, out = rnd.choice(["boing", "fart", "slide"]), int(0.6 * sr), 0.0, []
        for k in range(n):
            t = k / sr
            if kind == "boing":
                f = 180 + 120 * math.sin(2 * math.pi * 9 * t) * math.exp(-t * 4)
                v = math.sin(ph) * math.exp(-t * 4)
            elif kind == "fart":
                f = 70 + 25 * rnd.uniform(-1, 1) - 30 * t
                v = (2 * (ph / (2 * math.pi) % 1) - 1) * min(1, t * 30) * math.exp(-t * 3)
            else:
                f = 400 + 900 * t
                v = math.sin(ph) * min(1, t * 20, (0.6 - t) * 10)
            ph += 2 * math.pi * f / sr
            out.append(0.8 * v)
        return out

    events = []                                        # (time, priority, samples, gain)
    if not real:                                       # real sounds (real_sfx) replace the synthesized booms
        events.append((0.0, 9, boom(60, 1.0, 0.3), 0.8))
    for idx, (text, s, _) in enumerate(timed):
        events.append((s, 5 if "[r]" in text else 2, boom(80, 0.5, 0.15) if "[r]" in text and not real else tap(),
                       0.3 if "[r]" in text and not real else 0.55))
    for t in cuts:
        events.append((max(0, t - 0.2), 3, whoosh(0.45), 0.45))
    t = 0.0
    for sh in shots:
        if sh["kind"] == "split":
            events.append((t + 0.05, 7, boom(60, 0.9, 0.35), 0.6))
        t += sh["dur"]
    if not real:
        events.append((max(0, total - shots[-1]["dur"]), 8, boom(70, 0.8, 0.3), 0.7))   # payoff hit
    if CATEGORY == "classified":                     # soft Morse ... --- ...
        morse = []
        for d in [0.07] * 3 + [0.21] * 3 + [0.07] * 3:
            n = int(d * sr)
            morse += [0.35 * math.sin(2 * math.pi * 650 * k / sr) * min(1, k / 80, (n - k) / 80) for k in range(n)]
            morse += [0.0] * int(0.07 * sr)
        events.append((0.5, 6, morse, 0.5))
    if KIND != "quiz" and CATEGORY in ("myth", "versus") and len(timed) > 2 and rnd.random() < FUNNY:
        events.append((timed[1][1] + 0.3, 8, funny(), 0.6))
    taken = []
    for t, prio, smp, g in sorted(events, key=lambda e: -e[1]):
        if all(abs(t - u) >= 1.0 for u in taken):      # max 1 effect per second
            taken.append(t)
            add(t, smp, g)
    bed = noise(len(buf), 0.006)                       # rising tension bed + slow low drone, hard cut at end
    ph = 0.0
    for k in range(len(buf)):
        p = k / len(buf)
        ph += 2 * math.pi * (42 + 14 * p) / sr
        buf[k] += (bed[k] * 1.8 + 0.12 * math.sin(ph)) * (0.25 + 1.6 * p * p) * min(1, k / (0.3 * sr))
    peak = max(1e-6, max(abs(v) for v in buf))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(array.array("h", (int(v / peak * 26000) for v in buf)).tobytes())


SFX_DIR = pathlib.Path("sfx")                          # real sound effects (Mixkit free licence), see sfx/README.md
SFX_WORDS = [   # (word pattern in the script, sound file) - first match per line wins
    (r"explo|blast|blew up", "explosion_battle"), (r"\bbomb", "bomb_drop"), (r"shell|artiller|cannon|howitzer|\bgun\b|guns\b|flak",
     "artillery"), (r"torpedo|submarine|u-boat|depth charge", "submarine_hit"),
    (r"tank|panzer|tiger|sherman|panther|armou?r|tracks", "tank_engine"), (r"siren|air raid|blitz", "air_raid_siren"),
    (r"plane|aircraft|bomber|fighter|flew|pilot|squadron|luftwaffe|spitfire|mustang", "plane_flyby"),
    (r"\bship|\bsea\b|navy|naval|carrier|battleship|fleet|ocean|harbou?r", "sea"),
    (r"rifle|bullet|sniper|pistol|shot\b|shots\b|fired", "rifle_bolt"),
    (r"secret|code|cipher|document|spy|forg|file|orders|enigma|report", "typewriter"),
    (r"radio|signal|message|transmi|broadcast", "radio_static"), (r"march|troops|army|soldiers|infantry", "army_march"),
    (r"snow|winter|frozen|cold|storm", "storm_wind")]
SFX_OPEN = {"tanks": "tank_engine", "weapons": "artillery", "events": "explosion_far", "classified": "typewriter",
            "people": "war_drums", "versus": "explosion_close", "quiz": "radio_static", "myth": "war_drums"}


def real_sfx(data, timed, total, path):
    """Real sound effects on the words of the script: an opening sound for the headline's subject, then up to 3 more
    on lines that name an explosion, a tank, a plane, a ship... (each sound once, 1.5 s apart), and a hit on the
    punchline. Mixed under the voice; returns the sounds used."""
    if not SFX_DIR.exists():
        return []
    have = {p.stem: p for p in SFX_DIR.glob("*.mp3")}
    pick = lambda text: next((f for pat, f in SFX_WORDS if re.search(pat, plain(text), re.I) and f in have), None)
    events, used = [], set()
    first = pick(data.get("headline", "")) or SFX_OPEN.get(CATEGORY)
    if first in have:
        events.append((0.0, first, 0.9))
        used.add(first)
    for text, start, _ in timed[:-1]:
        f = pick(text)
        if f and f not in used and len(events) < 4 and all(abs(start - t) >= 1.5 for t, _, _ in events):
            events.append((max(0.0, start - 0.05), f, 0.7))
            used.add(f)
    if timed and "explosion_close" in have and total - timed[-1][1] > 1.0 and PART != 1:
        events.append((timed[-1][1], "explosion_close" if CATEGORY in ("events", "tanks", "weapons", "versus")
                       else "war_drums", 0.6))   # the punchline lands on a hit
    if not events:
        return []
    args, fc = [], []
    for k, (t, f, g) in enumerate(events):
        args += ["-i", str(have[f].resolve())]
        ms = int(t * 1000)
        fc.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=mono,volume={g},adelay={ms}|{ms}[s{k}]")
    fc.append("".join(f"[s{k}]" for k in range(len(events))) + f"amix=inputs={len(events)}:normalize=0:duration=longest,"
              f"apad=whole_dur={total:.3f},atrim=0:{total:.3f}[o]")
    ff(*args, "-filter_complex", ";".join(fc), "-map", "[o]", "-ar", "44100", "-ac", "1", str(path.resolve()))
    print("real sounds:", [(round(t, 1), f) for t, f, _ in events])
    return [f for _, f, _ in events]


def build_cold_sfx(total, path):
    """Cold-open sounds at fixed levels (mixed next to the voice): an air-raid siren under the first sentence if
    the climax is a raid, the tape stopping after the rewind, a clock ticking until the payoff and a hit on every
    stamp or strike of a list card."""
    sr = 22050
    buf = [0.0] * int(sr * (total + 0.3))
    rnd = random.Random(7)

    def add(start, samples):
        i0 = int(start * sr)
        for k, v in enumerate(samples[:max(0, len(buf) - i0)]):
            buf[i0 + k] += v

    def tone(f, d, decay, amp):
        return [amp * math.sin(2 * math.pi * f * k / sr) * math.exp(-k / sr * decay) for k in range(int(d * sr))]

    def hit(amp):                                       # low thump + a short click of noise
        th, nz = tone(130, 0.22, 18, amp), [0.3 * rnd.uniform(-1, 1) * math.exp(-k / sr * 110) for k in range(int(0.03 * sr))]
        return [a + (nz[k] if k < len(nz) else 0.0) for k, a in enumerate(th)]

    if COLD.get("alarm"):
        d, ph, out = COLD["at"], 0.0, []
        for k in range(int(d * sr)):
            t = k / sr
            ph += 2 * math.pi * (520 + 170 * math.sin(2 * math.pi * 0.4 * t - math.pi / 2)) / sr
            out.append(0.07 * (math.sin(ph) + 0.4 * math.sin(2 * ph) + 0.2 * math.sin(3 * ph))
                       * min(1.0, t / 0.4, (d - t) / 0.12))
        add(0.0, out)
    add(COLD["end"] - 0.02, tone(85, 0.14, 28, 0.55))   # the tape stops
    t, k = COLD["end"] + 0.3, 0
    while t < COLD.get("payoff", total) - 0.1:
        add(t, [v + 0.05 * rnd.uniform(-1, 1) * math.exp(-i / sr * 600) for i, v in
                enumerate(tone(3200 if k % 2 == 0 else 2300, 0.012, 400, 0.11))])
        t, k = t + 0.5, k + 1
    for i, m in enumerate(sorted(COLD.get("marks", []))):
        add(m, hit(0.6 if i == 0 else 0.45))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(array.array("h", (int(max(-1.0, min(1.0, v)) * 32000) for v in buf)).tobytes())


# ---- Music: picks a track from music/ that fits the category and the story ---------------------------
def music_tracks():
    exts = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")
    return sorted(p for p in MUSIC_DIR.rglob("*") if p.suffix.lower() in exts) if MUSIC_DIR.is_dir() else []


def path_words(key):
    return set(re.findall(r"[a-z]+", key.lower()))


SYNONYMS = {"tension": "tense", "war": "military", "battle": "military", "army": "military", "victory": "triumphant",
            "hero": "heroic", "spy": "mysterious", "mystery": "mysterious", "drum": "drums", "orchestra": "orchestral",
            "trailer": "cinematic", "horror": "dark", "fight": "action", "chase": "action", "sorrow": "sad",
            "melancholy": "sad", "inspiring": "hopeful", "inspirational": "hopeful", "funny": "playful",
            "happy": "upbeat", "relax": "calm", "ambience": "ambient", "guitar": "rock", "synth": "electronic"}


def name_moods(key):
    """Moods hinted by folder and file name, e.g. 'music/tanks/Heavy Drums.mp3' -> heavy, drums."""
    words = path_words(key)
    words |= {SYNONYMS[w] for w in words if w in SYNONYMS}
    return [m for m in MOODS if m in words or (len(m) > 4 and any(w.startswith(m[:5]) for w in words))]


def tag_track(path):
    """Gemini listens to 30 s from the middle of the track and tags its mood. None if unavailable."""
    import base64
    clip = W / "music_probe.mp3"
    try:
        start = max(0.0, probe_duration(path) * 0.4 - 15)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.1f}", "-t", "30", "-i", str(path),
                        "-ac", "1", "-b:a", "48k", str(clip)], check=True)
        audio = [{"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(clip.read_bytes()).decode()}}]
        d = gemini(f"Listen to this background music. Pick 3-6 words from this list that describe its mood, energy "
                   f"and style: {MOODS}. Rate its energy from 1 (calm) to 5 (intense). "
                   'Return JSON: {"moods": ["..."], "energy": 3}',
                   lambda d: isinstance(d, dict) and any(m in MOODS for m in d.get("moods", [])), rounds=1, extra=audio,
                   purpose="music tag", models=LITE_FIRST)
        return {"moods": [m for m in d["moods"] if m in MOODS], "energy": int(d.get("energy", 3))}
    except (SystemExit, Exception) as e:
        print("music tagging skipped:", type(e).__name__)
        return None


def best_start(path, length):
    """Start of the most energetic stretch of the track that is as long as the video."""
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "4000", "-f", "s16le", "-"],
                             capture_output=True, check=True).stdout
    except Exception:
        return 0.0
    a = array.array("h")
    a.frombytes(raw[:len(raw) // 2 * 2])
    hop = 2000                                       # 0.5 s blocks
    rms = [math.sqrt(sum(x * x for x in a[i:i + hop]) / hop) for i in range(0, len(a) - hop, hop)]
    n = max(1, int(length * 2))
    if len(rms) <= n:
        return 0.0
    win = sum(rms[:n])
    best, best_i = win, 0
    for i in range(1, len(rms) - n):
        win += rms[i + n - 1] - rms[i - 1]
        if win > best:
            best, best_i = win, i
    return best_i * 0.5


def pick_music(data):
    """Best track for this video: category moods + story moods + folder name, avoiding recent repeats."""
    tracks = {p.relative_to(MUSIC_DIR).as_posix(): p for p in music_tracks()}
    if not tracks:
        return (MUSIC_OLD, MUSIC_OLD.stem) if MUSIC_OLD.exists() else (None, None)
    try:
        index = json.loads(MUSIC_INDEX.read_text(encoding="utf-8"))
    except Exception:
        index = {}
    index, tagged = {k: index.get(k, {}) for k in tracks}, 0
    for key, e in index.items():
        if e.get("source") in ("gemini", "manual"):
            continue
        res = tag_track(tracks[key]) if MUSIC_AI and tagged < 4 else None   # max 4 new tracks per run (quota)
        tagged += 1
        e.update(res or {"moods": name_moods(key), "energy": e.get("energy", 3)})
        e["source"] = "gemini" if res else "name"
        print("music tagged:", key, e["moods"])
    story = {m for m in data.get("music", []) if m in MOODS}
    cat = set(CAT_MOODS.get(CATEGORY, []))

    def fit(key):                                    # story moods count double, folder named after category +4
        moods = set(index[key].get("moods", [])) | set(name_moods(key))
        return 2 * len(moods & story) + len(moods & cat) + (4 if CATEGORY in path_words(key) else 0)

    match = {k: fit(k) for k in tracks}
    top = max(match.values())
    good = [k for k in tracks if top > 0 and match[k] >= top - 1] or list(tracks)
    # among the best-fitting tracks take the one played longest ago, so the same song does not repeat
    key = min(good, key=lambda k: (index[k].get("last", -999), -match[k], random.random()))
    index[key]["plays"] = index[key].get("plays", 0) + 1
    index[key]["last"] = FILE_NO
    if not DRY_RUN:
        MUSIC_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print("music:", key, "| moods:", index[key].get("moods"), "| wanted:", sorted(story | cat))
    credit = tracks[key].with_suffix(".txt")         # optional attribution text next to the track
    return tracks[key], (credit.read_text(encoding="utf-8").strip() if credit.exists() else tracks[key].stem)


def mix_audio(total, music=None, music_start=0.0):
    """Voice + music that ducks under the voice + effects, normalized to YouTube's loudness -> mix.m4a.
    Runs in the background while the shots render; the final pass copies it as is."""
    args, fc, mix, k = [], [], [], -1
    fmt = "aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo"
    if NARRATION:
        args += ["-i", "voice.mp3"]
        k += 1
        fc.append(f"[{k}:a]{fmt},highpass=f=90,lowpass=f=8500,deesser=i=0.6,asplit=2[vo][key]")
        mix.append("[vo]")
    if music:
        args += ["-ss", f"{music_start:.2f}", "-stream_loop", "-1", "-i", str(pathlib.Path(music).resolve())]
        k += 1
        fc.append(f"[{k}:a]{fmt},volume={MUSIC_VOL},afade=t=in:d=0.3[mraw]")
        gap = (f",volume=enable='between(t,{LOOK['punch_at'] - 0.16:.3f},{LOOK['punch_at'] - 0.04:.3f})':volume=0"
               if LOOK.get("punch_at", 0) > 2 else "")   # a beat of silence before the punchline
        fc.append(f"[mraw][key]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=350{gap}[mu]" if NARRATION
                  else f"[mraw]anull{gap}[mu]")
        mix.append("[mu]")
    elif NARRATION:
        fc.append("[key]anullsink")
    if SFX and (W / "sfx.wav").exists():
        args += ["-i", "sfx.wav"]
        k += 1
        fc.append(f"[{k}:a]{fmt},lowpass=f=6000,volume={0.12 * SFX_VOL:.3f}[fx]")
        mix.append("[fx]")
    if SFX and (W / "real.wav").exists():             # real sound effects on the script's words
        args += ["-i", "real.wav"]
        k += 1
        fc.append(f"[{k}:a]{fmt},volume={0.55 * SFX_VOL:.3f}[rs]")
        mix.append("[rs]")
    if (W / "cold.wav").exists():                     # cold-open sounds: siren, tape stop, clock, card hits
        args += ["-i", "cold.wav"]
        k += 1
        fc.append(f"[{k}:a]{fmt},volume={SFX_VOL:.3f}[cd]")
        mix.append("[cd]")
    if not mix:
        args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        k += 1
        fc.append(f"[{k}:a]anull[sil]")
        mix.append("[sil]")
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=longest:normalize=0,"
              f"loudnorm=I={LOUDNESS}:TP=-1.5:LRA=11,aresample=44100[a]")
    ff(*args, "-filter_complex", ";".join(fc), "-map", "[a]", "-t", f"{total:.3f}",
       "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "mix.m4a")


IMPACT = re.compile(r"^(explo|blast|bomb|shell|hit|struck|strik|sank|sunk|sink|fire[ds]?$|fired|firing|shot|"
                    r"crash|destroy|boom|torpedo|artiller|burst|smash|slam|rammed|blew)", re.I)


def impact_times(tl, most=4):
    """Times of words like 'explosion', 'hit', 'fired' (max 4, 1.5 s apart): the frame shakes there."""
    out = []
    for l in tl:
        for w, _, t in l["words"]:
            if IMPACT.match(re.sub(r"[^A-Za-z]", "", w)) and all(abs(t - u) >= 1.5 for u in out) and t > 0.8:
                out.append(t)
    return out[:most]


def render(ass_path, total):
    """Blurred backdrop (or black bars), accent lines, progress bar and captions over the picture shots, with the
    cover morphs at the start and end, + the premixed audio."""
    cover, back = LOOK.get("cover"), LOOK.get("backdrop")
    on = f":enable='between(t,{COVER_T:.3f},{total - TAIL_SEC:.3f})'" if cover else ""
    inputs = []

    def add(*args):
        inputs.extend(args)
        return sum(1 for x in inputs if x == "-i") - 1
    ci = add("-i", "cover.mkv") if cover else None
    si = add("-f", "concat", "-safe", "0", "-i", "bg.txt")
    if back:
        bi = add("-i", "backdrop.png")                # decoded once, repeated as a still
        fc = f"[{bi}:v]format=yuv420p,setsar=1,loop=loop=-1:size=1,setpts=N/30/TB[bd];[bd][{si}:v]overlay=0:{TOP_BAR}:shortest=1,setsar=1,format=yuv420p[mid];"
    else:
        fc = f"[{si}:v]pad=1080:1920:0:{TOP_BAR}:black,setsar=1,format=yuv420p[mid];"
    if cover:
        ti = add("-i", "tail.mkv")
        fc += (f"[{ci}:v]setsar=1,format=yuv420p[c0];[{ti}:v]setsar=1,format=yuv420p[c1];"
               f"[mid]trim=duration={total - COVER_T - TAIL_SEC:.3f},setpts=PTS-STARTPTS[m2];"   # the tail always ends
               "[c0][m2][c1]concat=n=3:v=1:a=0,setpts=N/30/TB[base];")   # one clean 30 fps clock
    else:
        fc += "[mid]null[base];"
    hits = LOOK.get("impacts") or []
    if hits:                                           # a short shake on impact words (whole frame, before captions)
        win = "+".join(f"between(t,{a:.2f},{a + 0.3:.2f})*(1-(t-{a:.2f})/0.3)" for a in hits)
        fc += (f"[base]crop=1056:1878:'12+({win})*11*sin(t*97)':'21+({win})*9*sin(t*83)',"
               "scale=1080:1920,setsar=1[shk];")
    if STYLE_A:                                      # no accent lines, progress bar or channel block
        fc += f"[{'shk' if hits else 'base'}]null"
    else:
        fc += (f"[{'shk' if hits else 'base'}]drawbox=x=0:y={TOP_BAR - 6}:w=1080:h=6:color={ACCENT}@1:t=fill{on},"
               f"drawbox=x=0:y={BOT_Y}:w=1080:h=6:color={ACCENT}@0.3:t=fill{on}[p0];"
               f"color=c={ACCENT}:s=1080x6:r=30:d={total:.3f}[pb];"   # progress bar fills the line under the photo
               f"[p0][pb]overlay=x='-w+w*t/{total:.3f}':y={BOT_Y}:eof_action=pass{on}")
    if AVATAR.exists() and not STYLE_A:                              # round avatar of the channel block
        r = AV_SIZE / 2
        ai = add("-i", str(AVATAR.resolve()))
        fc += (f"[b];[{ai}:v]scale={AV_SIZE}:{AV_SIZE},format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
               f"a='if(lte(hypot(X-{r - 0.5},Y-{r - 0.5}),{r - 0.5}),alpha(X,Y),0)'[av];"
               f"[b][av]overlay={block_x()}:{BLOCK_Y}:enable='between(t,{max(COVER_T if cover else 0, min(BRAND_SEC, total / 4)):.3f},"
               f"{(total - TAIL_SEC) if cover else total + 1:.3f})'")
    fc += f",ass={ass_path.resolve()}:fontsdir={FONTS_DIR}[v]"
    mi = add("-i", "mix.m4a")
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", f"{mi}:a", "-t", f"{total:.3f}", "-r", "30", *x264(21),
       "-c:a", "copy", "-movflags", "+faststart", "final.mp4")


def make_audio(data, tl, shots, total):
    """Sound effects, the best-fitting music and the audio mix (runs next to the shot rendering). Effects and
    music are extras: if they fail, the video is still made."""
    t0, timed = time.time(), [(l["text"], l["start"], l["end"]) for l in tl]
    LOOK["punch_at"] = tl[-1]["start"] if tl and PART != 1 else 0
    (W / "sfx.wav").unlink(missing_ok=True)
    (W / "cold.wav").unlink(missing_ok=True)
    (W / "real.wav").unlink(missing_ok=True)
    if SFX:
        real = []
        try:
            real = real_sfx(data, timed, total, W / "real.wav")
        except Exception as e:
            print("real sounds skipped:", type(e).__name__, str(e)[:160])
            (W / "real.wav").unlink(missing_ok=True)
        try:
            cuts = [sum(s["dur"] for s in shots[:k + 1]) for k in range(len(shots) - 1)]
            cuts = [c for c in cuts if not COLD.get("at", -9) - 0.1 <= c <= COLD.get("end", -9) + 0.1]  # tape has its own sound
            build_sfx(total, timed, cuts, shots, W / "sfx.wav", real=bool(real))
            if COLD.get("at"):
                build_cold_sfx(total, W / "cold.wav")
            elif LOOK.get("map_art"):
                build_map_sfx(total, W / "cold.wav")
        except Exception as e:
            print("sound effects skipped:", type(e).__name__, str(e)[:120])
            (W / "sfx.wav").unlink(missing_ok=True)
            (W / "cold.wav").unlink(missing_ok=True)
    try:
        music, data["music_credit"] = pick_music(data)
        start = float(env("MUSIC_START")) if env("MUSIC_START") else (best_start(music, total) if music else 0.0)
    except Exception as e:
        print("music skipped:", type(e).__name__, str(e)[:120])
        music, data["music_credit"], start = None, None, 0.0
    data["music_file"], data["seconds"] = (music.name if music else ""), round(total, 1)
    data["tts"] = TTS_USED[0] if TTS_USED else None   # which voice engine read it (also in work/metadata.json)
    mix_audio(total, music, start)
    TIMES["audio (parallel)"] = time.time() - t0


def write_srt(data, tl, total):
    """Exact English subtitles with the voice's own timing: YouTube reads the real names (Nagumo, Kriegsmarine)
    instead of guessing them from the audio."""
    def ts(sec):
        ms = int(round(max(0.0, sec) * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    cues = [(0.0, tl[0]["start"] if tl else total, plain(data["headline"]))]
    cues += [(l["start"], l["end"], plain(l["text"])) for l in tl]
    out = [f"{i}\n{ts(a)} --> {ts(max(b, a + 0.4))}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1) if t]
    (W / "captions.srt").write_text("\n".join(out), encoding="utf-8")


def make_video(data, topic):
    """Voice and pictures are fetched at the same time; while the shots render, a second thread makes the
    effects, picks the music and mixes the audio; one final pass adds the bars and captions."""
    from concurrent.futures import ThreadPoolExecutor
    lines, words = all_lines(data), []
    spoken = respell(plain(data["headline"]) + ". " + " ".join(plain(l) for l in lines),   # captions keep the
                     data.get("pronounce") if isinstance(data.get("pronounce"), dict) else None)   # real spelling
    low = FACT_MIN if LENGTH[0] == "fact" else MIN_SEC   # never below 15 s
    # ~0.36 s/word at +14% rate; floor ensures short scripts still render ≥15 s
    total = min(MAX_SEC, max(low, 1 + len(spoken.split()) * 0.36))
    need = max(6, min(14, round(total / SHOT_SEC) + 2))  # always request extra so filtering still leaves variety
    COLD.clear()
    COLD["fast"] = bool(data.get("cold"))            # cold open: punchier narration (COLD_RATE)
    LOOK.clear()
    LOOK.update(backdrop=BACKDROP and KIND != "quiz", cover=BACKDROP and COVER and KIND == "single" and OPENING == "punch")
    with stage("voice + pictures"), ThreadPoolExecutor(max_workers=2) as ex:
        voice = ex.submit(lambda: tighten(W / "voice.mp3", speak(spoken, W / "voice.mp3"))) \
            if NARRATION else None
        art = ex.submit(MapArt, data["map"]) if data.get("map") else None   # the map is drawn meanwhile
        (imgs_a, *rest), credits, clips = get_images(data, topic, need)
        imgs_b = rest[0] if rest else []
        if voice:
            words = voice.result()
            total = min(MAX_SEC, max(low, probe_duration(W / "voice.mp3") + 0.15))   # no tail: seamless loop
        if art:
            try:
                LOOK["map_art"] = art.result()
                map_frame(LOOK["map_art"], LOOK["map_art"].close, 108, 70, 0)   # draws at all?
            except Exception as e:                       # no map: the photo opening as usual
                print("map skipped:", type(e).__name__, str(e)[:120])
                LOOK.pop("map_art", None)
    if data.get("cover"):                              # a ready script's own first frame (= the thumbnail)
        got = commons_picture(str(data["cover"]).replace(" ", "_"), "cover" + pathlib.Path(str(data["cover"])).suffix.lower())
        if got:
            imgs_a = [got[0]] + [p for p in imgs_a if p != got[0]]
            credits = [got[1]] + list(credits)
            print("cover: the script's own picture", data["cover"])
    if not imgs_a:
        raise SystemExit("No images found for " + topic["articles"][0])
    with stage("cover"):                               # the first frame is the cover: sharp, a person in colour
        imgs_a[0] = enhance_cover(imgs_a[0], color=COVER_COLOR and CATEGORY == "people", portrait=True)
    tl = timeline(data, words, total)
    if data.get("cold") and voice and tl:              # cold open: the first sentence, then the tape rewinds
        at = max(0.8, min(tl[0]["start"] - 0.05, total - 4))
        insert_rewind(W / "voice.mp3", at)
        words = [(w[0], w[1] + REWIND if w[1] >= at - 0.01 else w[1], *w[2:]) for w in words]
        total = min(MAX_SEC + REWIND, total + REWIND)
        tl = timeline(data, words, total)
        COLD.update(at=at, end=at + REWIND)
        COLD.update(cold_times(data, tl, total))
        print("cold open: rewind at", round(at, 2), "s |", COLD["jump"], "|", len(COLD["cards"]), "cards")
    if LOOK.get("cover") and COLD.get("at") and COLD["at"] < COVER_T + 0.4:
        LOOK["cover"] = False                            # a very short cold open: no room for the cover
    if LOOK.get("map_art") and LOOK.get("backdrop"):
        try:
            with stage("cover"):
                map_cover_assets(LOOK["map_art"], clips=bool(LOOK.get("cover")))
        except Exception as e:                           # the map failed: the photo opening instead
            print("map cover skipped:", type(e).__name__, str(e)[:120])
            LOOK.pop("map_art", None)
    if LOOK.get("backdrop") and not LOOK.get("map_art"):
        try:
            with stage("cover"):
                cover_assets(imgs_a[0], 1.04 if COLD.get("at") else 1.0, clips=bool(LOOK.get("cover")))
        except Exception as e:                           # Pillow missing or a bad photo: the old black bars
            print("cover/backdrop skipped:", type(e).__name__, str(e)[:120])
            LOOK.update(cover=False, backdrop=False)
    if COLD.get("at"):
        COLD.update(cold_times(data, tl, total))         # time stamps depend on the cover
    print("images:", len(imgs_a) + len(imgs_b), "| length:", round(total, 1), "s | cover:", bool(LOOK.get("cover")),
          "| map:", bool(LOOK.get("map_art")))
    write_srt(data, tl, total)
    if LOOK.get("map_art"):                              # when each route / the distance is spoken
        sp = LOOK["map_art"].spec
        marks = [(r["line"], ("route", k)) for k, r in enumerate(sp["routes"])]
        marks += [(sp["distance"]["line"], ("distance", 0))] if sp.get("distance") else []
        LOOK["map_marks"] = sorted((tl[ln - 1]["start"], mode) for ln, mode in marks if ln <= len(tl))
    shots = plan_shots(total, imgs_a, imgs_b, clips)
    if LOOK.get("map_art"):                              # a soft sonar ping on every later map shot
        t, LOOK["map_pings"] = 0.0, []
        for k, sh in enumerate(shots):
            if sh["kind"] == "map" and k > (1 if LOOK.get("cover") else 0):
                LOOK["map_pings"].append(t + (sh.get("lead", 0.0) if sh["mode"][0] != "target" else 0.05))
            t += sh["dur"]
    with ThreadPoolExecutor(max_workers=1) as ex:
        audio = ex.submit(make_audio, data, tl, shots, total)
        with stage("shots"):
            build_background(shots)
        ass = build_ass(data, tl, shots, total)
        audio.result()
    LOOK["impacts"] = impact_times(tl)
    with stage("final render"):
        render(ass, total)
    return credits


# ---- YouTube: credentials, learning from stats -------------------------------
def credentials():
    from google.oauth2.credentials import Credentials
    return Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token",
                       client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"])


def youtube(creds=None):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=creds or credentials())


# Old hook names in stats (before the viral-hook rewrite) → current HOOKS keys
HOOK_ALIASES = {
    "scale": "scale_paradox",
    "you": "you_inside",
    "origin": "origin_weird",
    "curiosity": "curiosity",
    "number": "number",
    "action": "action",
    "contrarian": "contrarian",
    "record": "record",
    "fact": "fact",
    "coldopen": "coldopen",
    "map": "map",
}


def normalize_hook(h):
    """Map legacy hook names to current ones so learning weights stay valid."""
    if not h:
        return h
    h = str(h).strip().lower()
    return HOOK_ALIASES.get(h, h)


def load_stats():
    try:
        s = json.loads(STATS.read_text(encoding="utf-8"))
    except Exception:
        s = {}
    s = {"videos": [], "metrics": {}, "recent": [], **s}
    # one-time migration of legacy hook names so learned() sees the same keys as pick_hook()
    for v in s.get("videos", []):
        if v.get("hook"):
            v["hook"] = normalize_hook(v["hook"])
    return s


def save_stats(s):
    s["videos"], s["recent"] = s["videos"][-300:], s["recent"][-40:]
    ids = {v.get("id") for v in s["videos"]}
    s["metrics"] = {k: v for k, v in s["metrics"].items() if k in ids}
    STATS.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def refresh_stats(creds, stats):
    """Latest numbers of recent uploads: views, likes, comments (works with the current token) and, if the
    analytics permission was granted in auth.py, engaged views, average % viewed, shares and new subscribers."""
    from datetime import date
    recent = [v for v in stats["videos"][-80:] if v.get("id")]
    ids = [v["id"] for v in recent]
    if not ids:
        return
    try:
        yt = youtube(creds)
        for i in range(0, len(ids), 50):
            for it in yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute().get("items", []):
                s = it.get("statistics", {})
                stats["metrics"].setdefault(it["id"], {}).update(
                    views=int(s.get("viewCount", 0)), likes=int(s.get("likeCount", 0)),
                    comments=int(s.get("commentCount", 0)))
        print("stats: views of", len(ids), "videos")
    except Exception as e:
        print("stats: views not read:", str(e)[:150])
    try:
        from googleapiclient.discovery import build
        ya = build("youtubeAnalytics", "v2", credentials=creds)
        res, why = None, ""
        for metrics in ("views,engagedViews,averageViewPercentage,shares,subscribersGained",
                        "views,averageViewPercentage,shares,subscribersGained"):
            try:
                res = ya.reports().query(ids="channel==MINE", startDate=min(v.get("date", "2026-01-01") for v in recent),
                                         endDate=date.today().isoformat(), metrics=metrics, dimensions="video",
                                         filters="video==" + ",".join(ids), sort="-views", maxResults=200).execute()
                break
            except Exception as e:
                if "insufficient" in str(e).lower() or "forbidden" in str(e).lower() or "403" in str(e):
                    raise
                why = str(e)
        if res is None:                                # both queries refused: say why (was "local variable 'res'")
            raise RuntimeError(why[:200])
        heads = [h["name"] for h in res.get("columnHeaders", [])]
        for row in res.get("rows", []):
            r = dict(zip(heads, row))
            stats["metrics"].setdefault(r.pop("video"), {}).update({f"a_{k}": v for k, v in r.items()})
        print("stats: analytics of", len(res.get("rows", [])), "videos")
    except Exception as e:
        print("stats: analytics off (optional; re-run auth.py to allow):", str(e)[:120])


def score(m):
    """How much YouTube pushed a video: retention first (APV), then engaged views, shares and subs; views as fallback.
    APV is weighted heavily because Shorts distribution is gated by early retention + completion."""
    if m.get("a_engagedViews") or m.get("a_averageViewPercentage") is not None and m.get("a_views"):
        ev = m.get("a_engagedViews") or m.get("a_views") or 0
        apv = m.get("a_averageViewPercentage", 0) or 0
        return (math.log1p(ev) + apv / 28          # ~2x stronger weight on retention than before
                + 25 * m.get("a_shares", 0) / max(ev, 50)
                + 40 * m.get("a_subscribersGained", 0) / max(ev, 50))
    v = m.get("views", 0)
    # likes+comments still help when analytics scope is missing
    return math.log1p(v) + 10 * (m.get("likes", 0) + 2.5 * m.get("comments", 0)) / max(v, 300)


def videos_of(stats, fmt=None):
    """Videos of one format: None = these classic Shorts, 'jurgen' = the 3-minute ones (jurgen.py). Each format
    learns only from its own videos: a 3-minute story and a 20-second Short are judged differently."""
    return [v for v in stats["videos"] if v.get("format") == fmt]


def learned(stats, field, options, fmt=None):
    """Weight per option from its videos' average score vs the channel average (0.5x-2x); None until there
    are 8+ videos older than 3 days. Options with fewer than 3 videos stay at 1x so they keep being tested."""
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=3)).isoformat()
    rows = [(v.get(field), score(stats["metrics"][v["id"]])) for v in videos_of(stats, fmt)[-120:]
            if v.get("id") in stats["metrics"] and v.get("date", "9999") <= cutoff]
    if len(rows) < 8:
        return None
    avg = sum(s for _, s in rows) / len(rows)
    out = {}
    for o in options:
        ss = [s for f, s in rows if f == o]
        out[o] = max(0.5, min(2.0, math.exp(sum(ss) / len(ss) - avg))) if len(ss) >= 3 else 1.0
    return out


def pick_category(stats):
    mult = learned(stats, "category", CATEGORIES)
    if not mult:
        return ROTATION[len(used) % len(ROTATION)]
    last = [v.get("category") for v in videos_of(stats)[-2:]]
    w = {c: ROTATION.count(c) * mult[c] * (0.3 if c in last else 1.0) for c in CATEGORIES}
    for c in ("classified", "quiz"):                     # v2.03 (Andrii, Oct 27): the weakest (medians 305 / 1,006 views),
        w[c] = 0                                         # never drawn (a manual CATEGORY input still works)
    w["tanks"] = w.get("tanks", 0) * 1.7                # Oct 22: tanks median 1,794, the top category (was x1.4)
    print("category weights:", {c: round(x, 2) for c, x in w.items()})
    return random.choices(list(w), weights=list(w.values()))[0]


def pick_length(stats, hook):
    """Prefer shorter stories: higher completion + loop rate. coldopen stays normal (needs room for rewind)."""
    if LENGTH_MODE == "short" and hook != "coldopen" and not PART:
        return "short"
    if LENGTH_MODE == "normal":
        return "normal"
    # ab mode: ~35% short among non-fact story videos (shorter = better APV in 2026 data)
    if hook != "coldopen" and not PART and random.random() < 0.35:
        return "short"
    return "normal"


def fact_turn(stats):
    """More ONE FACT videos: they loop better and hit higher APV. ~55% of single non-series videos when ab."""
    if LENGTH_MODE == "fact":
        return KIND == "single"
    if LENGTH_MODE != "ab" or KIND != "single":
        return False
    recent = [v.get("length") for v in videos_of(stats) if v.get("category") != "surrender"][-4:]
    facts = sum(1 for x in recent if x == "fact")
    # keep roughly half fact; if last 4 had <2 facts, force one
    if facts < 2:
        return True
    if facts >= 3:
        return False
    return random.random() < 0.55


def pick_hook(stats):
    if KIND == "quiz":
        return None
    if CATEGORY == "myth":
        return "wrong"          # hard myth-busting works best for this category
    if CATEGORY == "ranking":
        # ranking shorts from tops open on bold claim / wrong / scale
        return random.choices(
            ["shock_claim", "wrong", "scale_paradox", "nobody_knows", "one_detail"],
            weights=[3.5, 3.0, 2.0, 2.0, 1.5])[0]
    # Top hooks that drive the highest swipe-stop + retention in history/military Shorts
    top_tier = ["shock_claim", "nobody_knows", "wrong", "you_inside", "one_detail", "scale_paradox"]
    mid_tier = ["record", "origin_weird", "action", "coldopen", "map", "contrarian"]
    low_tier = ["curiosity", "number", "fact"]
    opts = [h for h in HOOKS if (h != "coldopen" or (KIND == "single" and not PART))
            and (h != "map" or (KIND == "single" and not PART and CATEGORY in ("events", "classified")))
            and (SCALE or h not in ("number", "scale_paradox"))]
    forced = normalize_hook((env("HOOK") or "").strip().lower())
    if forced in opts:  # forced for a test run (incl. legacy aliases: you→you_inside, scale→scale_paradox)
        return forced
    # Aggressive base priorities (learning will refine them over time)
    prior = {}
    for h in opts:
        if h in top_tier:
            prior[h] = 4.5 if SCALE and h == "scale_paradox" else 3.8
        elif h in mid_tier:
            prior[h] = 2.2
        else:
            prior[h] = 0.7
    if "coldopen" in prior:
        prior["coldopen"] = 3.2   # cliffhanger-drop style: strong retention in history/military
    if "map" in prior:
        prior["map"] = 2.6
    # classified + events: lean slightly more into shock / nobody_knows (tops style)
    if CATEGORY in ("classified", "events"):
        for h in ("shock_claim", "nobody_knows", "wrong"):
            if h in prior:
                prior[h] *= 1.25
    for h, k in (("curiosity", 1.4), ("scale_paradox", 1.4), ("you_inside", 0.7), ("coldopen", 0.75)):
        if h in prior:                                  # Andrii, Oct 20 (50 classic videos): curiosity 1,484 and
            prior[h] *= k                               # scale_paradox 1,430 median views; you_inside 1,034, coldopen 1,119
    mult = learned(stats, "hook", opts) or {h: 1.0 for h in opts}
    last = [v.get("hook") for v in videos_of(stats)[-2:]]   # avoid repeating the last 2
    weights = [prior[h] * mult[h] * (0.25 if h in last else 1.0) for h in opts]
    return random.choices(opts, weights=weights)[0]


# ---- YouTube: upload, localization, playlist, comment ------------------------
def texts(data):
    """Title, viewer question, search summary and the story text of the description."""
    return (plain(data["title"]), plain(data.get("question", "")), plain(data.get("summary", "")),
            plain(data["headline"]) + "\n" + "\n".join(plain(l) for l in data["lines"]))


def translate(title, question, summary, story):
    """Localized title/description so YouTube shows them in the viewer's language. Optional: {} on any error."""
    if not LANGS:
        return {}
    try:
        tr = gemini(
            f"Translate this YouTube Short metadata about World War II into these languages: {', '.join(LANGS)} "
            "(ISO 639-1 codes). Natural, catchy wording for each language, keep names, numbers and dates exact, "
            f"title max 80 characters, keep the subject's name at the start, no hashtags.\nTITLE: {title}\nQUESTION: {question}\nSUMMARY: {summary}\n"
            f"STORY:\n{story}\n"
            'Return JSON: {"<code>": {"title": "...", "question": "...", "summary": "...", "story": "..."}, ...}',
            lambda d: isinstance(d, dict) and sum(isinstance(d.get(l), dict) and bool(d[l].get("title"))
                                                  for l in LANGS) >= len(LANGS) // 2,
            rounds=2, purpose="translate", models=LITE_FIRST)
        return {l: v for l, v in tr.items() if l in LANGS and isinstance(v, dict) and v.get("title")}
    except (SystemExit, Exception) as e:
        print("translation skipped:", type(e).__name__)
        return {}


def safe_text(t, line=True):
    """YouTube rejects < and > in titles, descriptions and tags."""
    t = str(t).replace("<", "‹").replace(">", "›")
    return re.sub(r"\s+", " ", t).strip() if line else t.strip()


def cut_bytes(t, limit=4900):
    """Descriptions are limited to 5000 BYTES; Ukrainian or Polish letters take 2 bytes each."""
    return t.encode("utf-8")[:limit].decode("utf-8", "ignore")


def tag_list(data, topic):
    """Subject names first (YouTube uses tags mainly for names and alternate spellings), then the WWII terms the
    US audience types, the category and the channel; at most 500 characters counted the YouTube way
    (commas between tags, quotes around tags with spaces)."""
    raw = ([re.sub(r"\(.*?\)", "", a).strip() for a in topic["articles"]]
           + [t for t in data.get("tags", []) if isinstance(t, str)]
           + [c for c in data.get("countries", [])[:2] if isinstance(c, str)]
           + ["WWII", "WW2", "World War 2", "World War II", "military history", "history shorts"]
           + CAT_TAGS + [CHANNEL.title()])
    out, seen, size = [], set(), 0
    for t in raw:
        t = re.sub(r'[<>#,"]', "", t).strip()[:60]
        cost = len(t) + (2 if " " in t else 0) + (1 if out else 0)
        if t and t.lower() not in seen and size + cost <= 490:
            seen.add(t.lower())
            out.append(t)
            size += cost
    return out


def hashtags(topic):
    """5 focused hashtags (more dilutes them): #Shorts #WWII #WW2 #Subject #CategoryTag."""
    camel = lambda x: "#" + "".join(w[:1].upper() + w[1:] for w in re.findall(r"[A-Za-z0-9]+", x))[:30]
    subject = [] if KIND == "quiz" else [camel(re.sub(r"\(.*?\)", "", topic["articles"][0]))]   # quiz: no spoiler
    return " ".join(dict.fromkeys(["#Shorts", "#WWII", "#WW2"] + subject + [camel(CAT_TAGS[0])]))


def metadata(data, topic, credits, translations):
    """The upload body. Description: search sentence, question, story, hashtags, then the channel line, sources
    with links (CC BY-SA attribution), image credits with file links, music, file number."""
    title, q, summary, story = texts(data)
    if PART and f"part {PART}" not in title.lower():
        title = f"{title[:88]} (Part {PART})"
    if PART == 2 and SERIES_INFO.get("id"):
        summary += f"\n\n▶ Part 1: {SERIES_INFO.get('title', '')} https://youtube.com/shorts/{SERIES_INFO['id']}"
    wiki = lambda a: "https://en.wikipedia.org/wiki/" + a.replace(" ", "_")
    tail = ("\n\n" + hashtags(topic)
            + f"\n\n📁 A new declassified WWII file every day: follow {HANDLE}"
            + "\n\nSource: Wikipedia (CC BY-SA 4.0): " + "; ".join(f"{a} {wiki(a)}" for a in topic["articles"])
            + "\nImages and film via Wikimedia Commons / Wikipedia:\n" + "\n".join("- " + c for c in credits)
            + (f"\nMusic: {data['music_credit']}" if data.get("music_credit") else "")
            + f"\n\nFile #{FILE_NO}")
    head = lambda s, qq: (s + "\n\n" if s else "") + (f"{qq} Tell me in the comments!\n\n" if qq else "")
    desc = lambda s, qq, st: cut_bytes(safe_text(head(safe_text(s), safe_text(qq)) + safe_text(st, False) + tail,
                                                 False))
    body = {"snippet": {"title": safe_text(title)[:100], "tags": tag_list(data, topic), "categoryId": "27",
                        "description": desc(summary, q, story),
                        "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": env("PRIVACY", "public"), "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": env("SYNTHETIC", "0") == "1"}}   # real archive photos, no fakes
    loc = {l: {"title": safe_text(plain(t["title"]))[:100],
               "description": desc(t.get("summary", ""), t.get("question", ""), t.get("story", ""))}
           for l, t in translations.items() if safe_text(plain(t.get("title", "")))}
    if loc:
        body["localizations"] = loc
        print("localized:", ", ".join(loc))
    return body


def upload(yt, body):
    """Resumable upload; network hiccups are retried inside the same upload session (never a second video). Only
    a 400 'bad request' about the extras is retried without translations, tags and the AI-content flag."""
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    send = lambda part: yt.videos().insert(part=part, body=body, media_body=MediaFileUpload(
        str(W / "final.mp4"), chunksize=-1, resumable=True)).execute(num_retries=3)["id"]
    try:
        vid = send("snippet,status" + (",localizations" if body.get("localizations") else ""))
    except HttpError as e:
        if getattr(e.resp, "status", 0) != 400 or "uploadLimitExceeded" in str(e) or "quota" in str(e).lower():
            raise                                    # limits, quota, auth: a retry cannot help
        print("upload retry without extras:", str(e)[:200])
        body.pop("localizations", None)
        body["status"].pop("containsSyntheticMedia", None)
        body["snippet"].pop("tags", None)
        vid = send("snippet,status")
    print("uploaded:", vid)
    return vid


def to_tiktok(stats, body):
    """The same video as a draft in Andrii's TikTok inbox (tiktok.py; does nothing without the TikTok secrets).
    The caption (title + the description's hashtags) is printed and saved: drafts can't take one through the API."""
    if env("TIKTOK", "0") != "1":                      # v1.95 (Andrii, Oct 26): TikTok drafts cancelled; TIKTOK=1 = on
        print("tiktok: off")
        return
    import tiktok
    sn = body.get("snippet", {})
    tags = [t for t in re.findall(r"#\w+", sn.get("description", "")) if t.lower() != "#shorts"]
    with stage("tiktok"):
        r = tiktok.send(W / "final.mp4", tiktok.caption(sn.get("title", ""), tags))
    if r:
        stats["videos"][-1]["tiktok"] = r


def set_thumbnail(yt, vid, src="final.mp4"):
    """The very first frame (the full-screen cover photo or map, no text) becomes the custom thumbnail: shown on the
    channel page, in search and when shared. 50 API units; needs a phone-verified channel; any error only skips it.
    Custom Shorts thumbnails roll out from July 25, 2026, Partner Program channels first, so YouTube may refuse it:
    the answer is saved in stats ("thumb") to see when the channel gets access."""
    from googleapiclient.http import MediaFileUpload
    try:
        jpg = W / "thumb.jpg"
        for q in (2, 4, 8):                            # YouTube takes up to 2 MB
            ff("-i", src, "-frames:v", "1", "-q:v", str(q), "thumb.jpg")
            if jpg.stat().st_size < 1_900_000:
                break
        r = yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(jpg), mimetype="image/jpeg")).execute()
        print("thumbnail: first frame,", jpg.stat().st_size // 1000, "KB |", json.dumps(r)[:200])
        return "ok"
    except Exception as e:
        why = str(getattr(e, "reason", "") or e)
        try:                                           # YouTube's own reason, e.g. 'forbidden: ... custom thumbnails'
            err = json.loads(e.content)["error"]
            why = f"{err.get('code')} {(err.get('errors') or [{}])[0].get('reason', '')}: {err.get('message', '')}"
        except Exception:
            pass
        print("thumbnail skipped:", why[:300])
        return "error: " + why[:200]


def add_to_playlist(yt, vid):
    try:
        items = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])
        pl = next((i["id"] for i in items if i["snippet"]["title"] == PLAYLIST), None) or \
            yt.playlists().insert(part="snippet,status", body={
                "snippet": {"title": PLAYLIST, "description": f"{PLAYLIST}: World War II Shorts."},
                "status": {"privacyStatus": "public"}}).execute()["id"]
        yt.playlistItems().insert(part="snippet", body={"snippet": {
            "playlistId": pl, "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
        print("playlist:", PLAYLIST)
    except Exception as e:
        print("playlist skipped (re-run auth.py with new scopes):", str(e)[:200])


def upload_captions(yt, vid):
    """Exact English subtitles (optional: CAPTIONS=0 turns them off; costs 400 of the 10,000 daily API units)."""
    from googleapiclient.http import MediaFileUpload
    srt = W / "captions.srt"
    if not (CAPTIONS and srt.exists()):
        return
    try:
        yt.captions().insert(part="snippet", body={"snippet": {"videoId": vid, "language": "en", "name": "English",
                                                               "isDraft": False}},
                             media_body=MediaFileUpload(str(srt), mimetype="application/octet-stream")).execute()
        print("captions uploaded")
    except Exception as e:
        print("captions skipped:", str(e)[:150])


def post_comment(yt, vid, data):
    q = plain(data.get("question", ""))
    try:
        if q:
            yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid, "topLevelComment": {
                "snippet": {"textOriginal": f"{q} 👇"}}}}).execute()
            print("comment posted")
    except Exception as e:
        print("comment skipped (re-run auth.py with new scopes):", str(e)[:200])


def winners(stats, n=5, fmt=None):
    """Headlines of the best and the 3 worst videos by score (2+ days old); empty until 8 videos have stats."""
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=2)).isoformat()
    rows = sorted(((score(stats["metrics"][v["id"]]), v.get("headline") or v.get("title", ""))
                   for v in videos_of(stats, fmt)[-150:] if v.get("id") in stats["metrics"]
                   and v.get("date", "9999") <= cutoff and (v.get("headline") or v.get("title"))), reverse=True)
    return ([h for _, h in rows[:n]], [h for _, h in rows[-3:]]) if len(rows) >= 8 else ([], [])


def link_parts(yt, series, vid, title):
    """Adds 'Part 2: ...' to the top of part 1's description, so viewers of part 1 find the ending."""
    try:
        sn = yt.videos().list(part="snippet", id=series["id"]).execute()["items"][0]["snippet"]
        desc = cut_bytes(f"▶ Part 2: {safe_text(title)} https://youtube.com/shorts/{vid}\n\n" + sn.get("description", ""))
        yt.videos().update(part="snippet", body={"id": series["id"], "snippet": {
            "title": sn["title"], "categoryId": sn.get("categoryId", "27"), "description": desc,
            "tags": sn.get("tags", []), "defaultLanguage": sn.get("defaultLanguage", "en"),
            "defaultAudioLanguage": sn.get("defaultAudioLanguage", "en")}}).execute()
        print("part 1 linked to part 2")
    except Exception as e:
        print("part 1 not linked:", str(e)[:150])


def reply_comments(yt, stats):
    """Answers real viewer comments with facts from the video's Wikipedia source: max REPLIES a day and 2 per run,
    newest first, questions first; skips own comments, threads already answered, spam and trolling."""
    from datetime import date, datetime, timedelta, timezone
    st = stats.setdefault("replies", {})
    if st.get("date") != date.today().isoformat():
        st.update(date=date.today().isoformat(), count=0)
    left = min(2, REPLIES - st.get("count", 0))
    if left <= 0 or not CHANNEL_ID:
        return
    done = set(st.get("done", []))
    try:
        items = yt.commentThreads().list(part="snippet,replies", allThreadsRelatedToChannelId=CHANNEL_ID, maxResults=50,
                                         order="time", textFormat="plainText").execute().get("items", [])
    except Exception as e:
        print("comments not read:", str(e)[:150])
        return
    since = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    videos = {v.get("id"): v for v in stats["videos"]}
    todo = []
    for t in items:
        top = t["snippet"]["topLevelComment"]["snippet"]
        text = top.get("textDisplay", "").strip()
        ours = lambda c: c.get("authorChannelId", {}).get("value") == CHANNEL_ID
        if t["id"] in done or ours(top) or top.get("publishedAt", "") < since or len(text.split()) < 3 \
                or "http" in text or any(ours(r["snippet"]) for r in t.get("replies", {}).get("comments", [])):
            continue
        todo.append({"id": t["id"], "video": t["snippet"].get("videoId", ""), "comment": text[:500]})
    todo.sort(key=lambda c: "?" not in c["comment"])                  # questions first
    todo = todo[:left * 2]
    if not todo:
        return
    texts_ = {}
    for c in todo:
        v = videos.get(c["video"], {})
        c["title"] = v.get("title", "")
        arts = [a for a in v.get("topic", "").split(" vs ") if a]
        for a in arts:
            if a not in texts_:
                texts_[a] = (wiki_text(a)[1] or "")[:3500]
        c["source"] = " ".join(texts_.get(a, "") for a in arts)[:5000]
    try:
        d = gemini("You run the YouTube channel Classified 1945 (World War II history Shorts). Write short, friendly "
                   "replies to these viewer comments. Use ONLY facts from each comment's source; if the source does not "
                   "answer a question, share a related fact from it. Max 200 characters, plain text, no links, no "
                   "hashtags, never ask to like or subscribe, no politics, never praise any regime. Vary the wording. "
                   'Reply "" to spam, insults, trolling or anything you cannot answer well.\n'
                   f"COMMENTS: {json.dumps(todo, ensure_ascii=False)}\n"
                   'Return JSON {"replies": [{"id": "...", "reply": "..."}]}',
                   lambda d: isinstance(d, dict) and isinstance(d.get("replies"), list), rounds=2,
                   purpose="comment replies")
    except SystemExit:
        print("comment replies skipped: Gemini unavailable")
        return
    ids = {c["id"] for c in todo}
    for r in d["replies"]:
        text = safe_text(r.get("reply", "")) if isinstance(r, dict) else ""
        if left <= 0 or r.get("id") not in ids or not 3 <= len(text) <= 300 or "http" in text:
            continue
        try:
            yt.comments().insert(part="snippet", body={"snippet": {"parentId": r["id"], "textOriginal": text}}).execute()
            print("replied:", text[:80])
            st["count"] = st.get("count", 0) + 1
            left -= 1
        except Exception as e:
            print("reply skipped:", str(e)[:150])
        done.add(r["id"])
    st["done"] = list(done)[-300:]


# ---- SURRENDER: every 4th video is a 15 s archive film of a WW2 surrender, captions + music, no voice -------
SURRENDER_EVERY = int(env("SURRENDER_EVERY", "4"))     # 0 = off; force one with CATEGORY=surrender (Oct 22: 5 -> 4)
SURRENDER_SEC = 15.0
# Europe-first queries: Japanese ceremony footage dominates Commons/IA rankings and was repeating on the channel
SURRENDER_Q = [
    "German soldiers surrender 1945", "German troops surrender Western Front",
    "German army surrenders 1945", "German generals surrender", "Wehrmacht surrender 1945",
    "Kapitulation 1945", "German prisoners of war 1945", "U-boat surrender 1945",
    "Italian soldiers surrender 1943", "Italian armistice 1943", "Italian troops surrender",
    "French troops surrender 1940", "surrender Normandy 1944", "German surrender Ruhr 1945",
    "surrender Stalingrad 1943", "German surrender Tunisia 1943", "Afrika Korps surrender",
    "white flag surrender 1945", "surrender ceremony 1945 Europe", "capitulation 1945 Europe",
    "Japanese soldiers surrender 1945", "Japanese garrison surrenders", "Japanese surrender 1945",
    "surrender World War II film", "prisoners of war World War II film",
]
SURR_RE = re.compile(r"surrender|capitulat|kapitulation|prisoners? of war|\bPOWs?\b|taken prisoner|captured|"
                     r"give themselves up|gave themselves up|white flag", re.I)
# Region tags for diversity (Japan archive is over-represented online)
SURR_REGION = {
    "japan": re.compile(r"\b(japan|japanese|japs?\b|nippon|tokyo|osaka|missouri|macarthur|"
                        r"hirohito|pacific island|okinawa|iwo|saipan|manila|singapore|"
                        r"burma|sumatra|padang|hong kong|formosa|taiwan)\b", re.I),
    "german": re.compile(r"\b(german|germany|wehrmacht|reich|berlin|hamburg|munich|ruhr|"
                         r"stalingrad|tunisia|afrika korps|u-?boat|kriegsmarine|luftwaffe|"
                         r"normandy|arnhem|remagen|rhine|ve day|v-e)\b", re.I),
    "italian": re.compile(r"\b(italian|italy|rome|sicily|salerno|mussolini|armistice)\b", re.I),
    "other": re.compile(r"."),
}


def surr_region(text):
    t = text or ""
    for key in ("japan", "german", "italian"):
        if SURR_REGION[key].search(t):
            return key
    return "other"


def surrender_used_set():
    """All prior surrender keys from used.json + stats (so repeats cannot slip past via different spelling)."""
    keys = set()
    for u in used:
        if isinstance(u, str) and u.lower().startswith("surrender:"):
            keys.add(u.split(":", 1)[-1].strip().lower())
            keys.add(u.lower())
    try:
        s = json.loads(STATS.read_text(encoding="utf-8"))
        for v in s.get("videos", []):
            if v.get("category") != "surrender":
                continue
            for field in (v.get("topic"), v.get("title"), v.get("headline")):
                if not field:
                    continue
                keys.add(str(field).lower())
                if "surrender:" in str(field).lower():
                    keys.add(str(field).split(":", 1)[-1].strip().lower())
    except Exception:
        pass
    return keys


def surrender_already_used(name, ident=None):
    """True if this film (or a near-duplicate name) was already posted."""
    keys = surrender_used_set()
    candidates = [c for c in (name, ident) if c]
    for c in candidates:
        cl = c.lower().strip()
        if cl in keys or f"surrender: {cl}" in keys:
            return True
        # normalize alnum only — catches 'JapsSurrende' vs full title, Missouri newsreel variants
        compact = re.sub(r"[^a-z0-9]", "", cl)
        if len(compact) < 10:
            continue
        for k in keys:
            kc = re.sub(r"[^a-z0-9]", "", k)
            if len(kc) < 10:
                continue
            if compact in kc or kc in compact or compact[:16] == kc[:16]:
                return True
    return False


def recent_surrender_regions(n=6):
    """Regions of the last n surrender uploads — used to de-prioritize Japan when it dominates."""
    out = []
    try:
        s = json.loads(STATS.read_text(encoding="utf-8"))
        for v in reversed(s.get("videos", [])):
            if v.get("category") != "surrender":
                continue
            out.append(surr_region(f"{v.get('topic', '')} {v.get('title', '')} {v.get('headline', '')}"))
            if len(out) >= n:
                break
    except Exception:
        pass
    return out


def commons_video_pages(query, limit=12):
    """[(file name, info)] for a Commons video search (videoinfo also lists the small transcodes)."""
    for prop, key in (("videoinfo", "viprop"), ("imageinfo", "iiprop")):
        try:
            pages = requests.get(COMMONS, headers=UA, timeout=60, params={
                "action": "query", "format": "json", "formatversion": 2, "generator": "search",
                "gsrsearch": f"{query} filetype:video", "gsrnamespace": 6, "gsrlimit": limit, "prop": prop,
                key: "url|size|extmetadata" + ("|derivatives" if prop == "videoinfo" else "")}).json()["query"]["pages"]
        except Exception:
            pages = []
        if any(p.get(prop) for p in pages):
            return [(p.get("title", "").replace("File:", "").rsplit(".", 1)[0], (p.get(prop) or [{}])[0])
                    for p in sorted(pages, key=lambda p: p.get("index", 99))]
    return []


IA = "https://archive.org"
IA_PD = {"prelinger", "fedflix", "universal_newsreels", "universalnewsreels", "universal-newsreels", "nara",
         "usnationalarchives", "nationalarchives", "armypictorialcenter", "army_pictorial_center", "usgovernmentfilms",
         "pdfilms", "public_domain_films", "publicdomainmovies", "moviesandfilms_publicdomain", "iwm"}
IA_FORMATS = ("h.264", "mpeg4", "h.264 ia", "512kb mpeg4", "ogg video", "webm")   # preferred first
WW2_WORDS = re.compile(r"\b19(39|4[0-5])\b|world war (ii|2|two)|\bww ?(ii|2)\b|wehrmacht|waffen|nazi|third reich|"
                       r"luftwaffe|kriegsmarine|imperial japanese|red army|v-e day|v-j day", re.I)
WW2_SURRENDER = lambda name, text, date: (bool(SURR_RE.search(text)) and bool(WW2_WORDS.search(text))
                                          and not re.search(r"\b(19[5-9]\d|20\d\d)\b", f"{name} {date}")
                                          and not re.search(r"anniversar|reenact|re-enact|commemorat|memorial", text, re.I))


def ia_candidates(seen):
    """Internet Archive films about a WW2 surrender (Universal Newsreels, US government films, Prelinger...): only
    public domain or free licences; the file is picked when a film is tried (ia_file)."""
    clean = lambda v: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", " ".join(v) if isinstance(v, list)
                                                                 else str(v or "")))).strip()
    q = ("(title:(surrender OR surrenders OR surrendered OR capitulation OR capitulates) OR "
         "description:(surrender OR surrenders OR surrendered OR capitulation)) AND mediatype:(movies)")
    try:
        docs = requests.get(f"{IA}/advancedsearch.php", headers=UA, timeout=60, params=[
            ("q", q), ("rows", "200"), ("output", "json"), ("sort[]", "downloads desc")]
            + [("fl[]", f) for f in ("identifier", "title", "description", "date", "year", "licenseurl", "rights",
                                      "collection")]).json()["response"]["docs"]
    except Exception as e:
        print("surrender: Internet Archive search failed:", type(e).__name__, str(e)[:100])
        return []
    out, nolic = [], {}
    for d in docs:
        ident, name = d.get("identifier", ""), clean(d.get("title"))[:120]
        desc, date = clean(d.get("description"))[:4000], clean(d.get("date"))[:40]
        if not ident or ident in seen or surrender_already_used(name, ident):
            continue
        seen.add(ident)
        if SENSITIVE.search(f"{name} {desc}") or not WW2_SURRENDER(name, f"{name} {desc} {date}", date[:4] if
                                                                   re.match(r"19[5-9]|20", date) else ""):
            continue
        colls = {c.lower() for c in (d.get("collection") if isinstance(d.get("collection"), list)
                                     else [d.get("collection") or ""])}
        lic = str(d.get("licenseurl") or "")
        free = re.search(r"publicdomain|/zero/|cc0|/licenses/by(-sa)?/", lic, re.I) or (colls & IA_PD)
        if not free:
            for c in colls:
                nolic[c] = nolic.get(c, 0) + 1
            continue
        region = surr_region(f"{name} {desc}")
        out.append({"name": name, "ia": ident, "url": None, "desc": desc, "cats": ", ".join(sorted(colls))[:300],
                    "date": date, "dur": 600.0, "region": region,
                    "credit": f"Film: {name[:60]} (Internet Archive, {lic or 'public domain collection'}) "
                              f"{IA}/details/{ident}",
                    "rank": (0 if SURR_RE.search(name) else 1, True, 600.0)})
    print("surrender: Internet Archive", len(docs), "found |", len(out), "free | no licence by collection:",
          dict(sorted(nolic.items(), key=lambda x: -x[1])[:8]))
    return out


def ia_file(ident, cap=150_000_000):
    """Download URL of the best video file of an Internet Archive item that is at most 150 MB."""
    try:
        meta = requests.get(f"{IA}/metadata/{ident}", headers=UA, timeout=60).json()
    except Exception:
        return None
    files = []
    for f in meta.get("files", []):
        fmt, size = str(f.get("format", "")).lower(), int(float(f.get("size") or 0))
        if fmt in IA_FORMATS and 0 < size <= cap:
            files.append((IA_FORMATS.index(fmt), size, f["name"]))
    if not files:
        return None
    from urllib.parse import quote
    return f"{IA}/download/{ident}/{quote(min(files)[2])}"


def surrender_candidates(limit=60):
    """Free WW2 archive films about a surrender, not used before. Europe first when Japan recently dominated."""
    seen, out = set(), []
    clean = lambda v: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(v or "")))).strip()
    recent_reg = recent_surrender_regions(6)
    japan_heavy = recent_reg.count("japan") >= max(1, len(recent_reg) // 2) if recent_reg else False
    print("surrender: recent regions", recent_reg or "-", "| japan_heavy", japan_heavy)
    for q in SURRENDER_Q:
        for name, info in commons_video_pages(q):
            if name in seen or surrender_already_used(name):
                continue
            seen.add(name)
            meta = info.get("extmetadata", {})
            desc = clean(meta.get("ImageDescription", {}).get("value"))[:4000]
            cats = clean(meta.get("Categories", {}).get("value")).replace("|", ", ")[:600]
            date = clean(meta.get("DateTimeOriginal", {}).get("value"))[:80]
            if not WW2_SURRENDER(name, f"{name} {desc} {cats} {date}", date):
                continue
            item = video_item(name, info)
            if not item:
                continue
            dur = float(info.get("duration") or 600)
            region = surr_region(f"{name} {desc} {cats}")
            out.append({"name": name, "url": item[0], "credit": item[1], "desc": desc, "cats": cats, "date": date,
                        "dur": dur, "region": region,
                        "rank": (0 if SURR_RE.search(name) else 1, dur > 240, dur)})
        if len(out) >= limit:
            break
    print("surrender: Commons", len(out), "films")
    out += ia_candidates(seen)

    def sort_key(c):
        region = c.get("region") or surr_region(f"{c.get('name', '')} {c.get('desc', '')}")
        # when Japan already filled recent slots, push Japan to the back
        region_penalty = 2 if (japan_heavy and region == "japan") else (0 if region == "german" else
                                                                        1 if region in ("italian", "other") else 2)
        r = c.get("rank") or (1, True, 600)
        return (region_penalty, r[0], r[1], r[2])

    ranked = sorted(out, key=sort_key)
    print("surrender: top after diversity",
          [(c["name"][:40], c.get("region") or surr_region(c["name"])) for c in ranked[:8]])
    return ranked


def surrender_caption(c):
    """Captions from the film's OWN description only: WHO surrenders, TO WHOM, WHERE, WHEN.
    None if the description is not about soldiers surrendering."""
    ask = ("You write on-screen captions for a short World War II archive film Short with NO narration. "
           "Use ONLY facts written in this film's own description; invent nothing.\n"
           f"FILE NAME: {c['name']}\nDATE FIELD: {c['date']}\nCATEGORIES: {c['cats']}\n"
           f"DESCRIPTION:\n<<<\n{c['desc']}\n>>>\n"
           "Return JSON:\n"
           '{"ok": true/false, "who": "...", "to_whom": "...", "place": "...", "date": "...", '
           '"top": "...", "look_for": "...", "title": "...", "question": "...", "tags": ["..."]}\n'
           "- ok: true only if the description is about soldiers, troops, a pilot, a crew, a garrison or a commander "
           "surrendering / giving up / being taken prisoner in WW2. Otherwise false.\n"
           "- who: WHO SURRENDERS, CAPITALS, max 40 chars. Concrete unit or side from the text "
           "(e.g. 'GERMAN 6TH ARMY', 'JAPANESE GARRISON', 'U-BOAT CREW', 'ITALIAN TROOPS'). Never vague "
           "'ENEMY SOLDIERS'.\n"
           "- to_whom: WHO ACCEPTS the surrender, CAPITALS, max 36 chars, from the text "
           "(e.g. 'TO US 7TH ARMY', 'TO THE SOVIETS', 'TO BRITISH 8TH ARMY'). Empty string if the description "
           "does not say. Never put the surrendering side after TO.\n"
           "- place: WHERE, CAPITALS, max 36 chars ('STALINGRAD', 'REIMS, FRANCE', 'USS MISSOURI'). "
           "Empty if the description names no place.\n"
           "- date: WHEN, CAPITALS, as precise as the text ('2 SEPTEMBER 1945', 'MAY 1945', '1945'). Empty if none.\n"
           "- top: one CAPS line for the screen: WHO + SURRENDERS + TO WHOM if known, max 90 chars. "
           "Example: 'GERMAN 6TH ARMY SURRENDERS TO THE SOVIETS'.\n"
           "- look_for: one sentence of what the surrender looks like on film.\n"
           "- title: YouTube title, max 70 chars, e.g. 'German 6th Army Surrenders at Stalingrad, 1943'. No hashtags.\n"
           "- question: either/or question for comments, max 10 words.\n"
           "- tags: 6-10 search phrases (e.g. 'German surrender 1945', 'WW2 archive footage').")
    okj = lambda d: isinstance(d, dict) and "ok" in d
    lite = False
    try:
        d = gemini(ask, okj, rounds=4, purpose="surrender caption", models=[m for m in MODELS if "lite" not in m])
    except SystemExit:
        try:
            d = gemini(ask + "\n- IMPORTANT: fill who; leave to_whom empty if unsure.", okj, rounds=3,
                       purpose="surrender caption", models=LITE_FIRST)
            lite = True
        except SystemExit:
            return None
    src = ascii_up(f"{c['name']} {c['desc']} {c['cats']} {c['date']}")
    up = lambda k, n: re.sub(r"\s+", " ", plain(str(d.get(k) or ""))).strip().upper()[:n]
    who, to_whom = up("who", 44), up("to_whom", 40)
    place, date = up("place", 36), up("date", 24)
    top = up("top", 100)
    if lite:
        to_whom = ""
        top = re.split(r"\s+TO\s+(?!THE\s+(?:GROUND|ENEMY\b))", top)[0].strip()
    # rebuild top from structured fields when possible (clearer who / to whom)
    if who:
        if to_whom and not to_whom.startswith("TO "):
            to_whom = "TO " + to_whom
        top = f"{who} SURRENDERS {to_whom}".strip() if to_whom else (
            top if who in top else f"{who} SURRENDERS")
        top = re.sub(r"\s+", " ", top)[:100]
    # place / date must appear in the film's text
    words = [w for w in re.findall(r"[A-Z]{3,}", ascii_up(place)) if w not in {"THE", "AND"}]
    if not words or not all(re.search(rf"\b{w}\b", src) for w in words):
        place = ""
    year = re.search(r"\b19(39|4[0-5])\b", date)
    if not year or year.group(0) not in src or not nums_in_source(date, f"{c['desc']} {c['date']} {c['name']}"):
        years = sorted(set(re.findall(r"\b19(?:39|4[0-5])\b", src)))
        date = years[0] if len(years) == 1 else ""
    giving_up = re.search(r"SURRENDER|CAPITULAT|GIVES? (THEMSELVES )?UP|GAVE (THEMSELVES )?UP|TAKEN PRISONER|"
                          r"\bCAPTURED\b|LAYS? DOWN (THEIR |HIS )?ARMS", top)
    why = ("not a surrender" if d.get("ok") is not True or not giving_up
           or re.search(r"LIBERAT|\bFREED\b|RELEASED|RETURN|REPATRIAT|RESCUED", top)
           else "a number not in the description" if not nums_in_source(top, f"{c['desc']} {c['date']} {c['name']}")
           else "")
    if why:
        print("surrender: skip", c["name"][:60], "|", why)
        return None
    # title prefers who + place + year
    title_bits = [who.title() if who else "", "Surrenders"]
    if to_whom:
        title_bits.append(to_whom.replace("TO ", "to ").title())
    if place:
        title_bits.append(("at " + place.title()) if not place.lower().startswith("uss") else place.title())
    if date:
        title_bits.append(date.title())
    auto_title = re.sub(r"\s+", " ", " ".join(title_bits)).strip(" ,")[:90]
    title = re.sub(r"\s+", " ", plain(str(d.get("title") or auto_title)))[:90] or auto_title
    print(f"surrender caption: who={who!r} to={to_whom!r} place={place!r} date={date!r}")
    return {"top": top, "who": who, "to_whom": to_whom, "place": place, "date": date,
            "look_for": str(d.get("look_for") or "")[:200], "title": title,
            "question": (lambda q: q if re.search(r"\bor\b", q, re.I) and q.endswith("?") else "")(
                plain(str(d.get("question") or "")).strip())[:90],
            "tags": [t for t in (d.get("tags") or []) if isinstance(t, str)][:10]}


def surrender_context(c, cap):
    """Andrii (Oct 15): 'JAPAN SURRENDERS' alone is dry. The bot finds the event on Wikipedia and writes a stronger
    caption: what / who / to whom + one short fact line (e.g. 'AFTER 3 YEARS AND 8 MONTHS OF WAR IN THE PACIFIC'),
    and fills a missing place or date. Only facts from that article or the film's description; numbers are checked.
    Any doubt keeps the plain caption. One main-model request."""
    q = re.sub(r"\s+", " ", f"{cap['top']} {cap['place']} {cap['date']} World War II surrender").lower()
    try:
        hits = wiki_get(action="query", list="search", srsearch=q, srlimit=5)["query"]["search"]
    except Exception:
        hits = []
    titles = [h["title"] for h in hits if not BAD_TITLE.search(h["title"])]
    titles.sort(key=lambda t: 0 if re.search(r"surrender|capitulat", t, re.I) else 1)
    title, text = wiki_text(titles[0]) if titles else (None, None)
    if not text:
        print("surrender: no Wikipedia article for the context")
        return cap
    ask = ("You write the on-screen captions of a silent World War II archive film Short (music only). The plain "
           f"caption is: \"{cap['top']}\" | place: \"{cap['place']}\" | date: \"{cap['date']}\".\n"
           f"FILM DESCRIPTION:\n<<<\n{c['desc'][:2500]}\n>>>\nWIKIPEDIA ARTICLE \"{title}\":\n<<<\n{text[:6000]}\n>>>\n"
           "Return JSON {\"same_event\": true/false, \"top\": \"...\", \"sub\": \"...\", \"place\": \"...\", "
           "\"date\": \"...\"}\n"
           "- same_event: true only if the article is about the surrender the film shows (same forces, same place "
           "or the same capitulation). If false, leave the rest empty.\n"
           "- top: CAPITALS, max 60 characters: WHAT happened, WHO surrenders and TO WHOM, gripping and concrete, "
           "e.g. 'JAPAN SURRENDERS TO THE ALLIES' or 'THE GERMAN 6TH ARMY SURRENDERS AT STALINGRAD'. The side that "
           "gives up surrenders TO the winners.\n"
           "- sub: CAPITALS, max 70 characters: the ONE most striking fact around it, from the article, e.g. 'AFTER "
           "162 DAYS OF FIGHTING' or 'THE WAR IN THE PACIFIC IS OVER'. No opinions, nothing graphic.\n"
           "- place: CAPITALS, max 32 characters ('TOKYO BAY, JAPAN'); date: CAPITALS ('2 SEPTEMBER 1945').\n"
           "Use ONLY facts written in the article or the description.")
    try:
        d = gemini(ask, lambda d: isinstance(d, dict) and "same_event" in d, rounds=3, purpose="surrender context",
                   models=[m for m in MODELS if "lite" not in m])
    except SystemExit:
        return cap
    if d.get("same_event") is not True:
        print("surrender: Wikipedia article", title, "is another event -> plain caption")
        return cap
    src = f"{text} {c['desc']} {c['name']} {c['date']}"
    up = lambda k, n: re.sub(r"\s+", " ", plain(str(d.get(k) or ""))).strip().upper()[:n]
    top, sub, place, date = up("top", 64), up("sub", 74), up("place", 34), up("date", 20)
    out = dict(cap)
    if top and re.search(r"SURRENDER|CAPITULAT|GIVES? UP|GAVE UP|LAY(S)? DOWN|TAKEN PRISONER", top) \
            and not re.search(r"LIBERAT|\bFREED\b|RELEASED", top) and nums_in_source(top, src):
        out["top"], out["who"], out["to_whom"] = top, "", ""   # the context caption replaces who / to whom
    if sub and nums_in_source(sub, src) and not SENSITIVE.search(sub):
        out["sub"] = sub
    words = lambda t: [w for w in re.findall(r"[A-Z]{3,}", ascii_up(t)) if w not in {"THE", "AND"}]
    if (not out["place"] or out["place"] in place) and place and words(place) and all(re.search(rf"\b{w}\b", ascii_up(src)) for w in words(place)):
        out["place"] = place
    if (not out["date"] or out["date"] in date) and date and re.search(r"\b19(39|4[0-5])\b", date) and nums_in_source(date, src):
        out["date"] = date
    out["wiki"] = title
    print("surrender: context from", title, "|", out["top"], "|", out.get("sub", ""))
    return out


WM_TEXT = {}                                           # film path -> the watermark text read from its frames


def frames_check(path, times, look_for):
    """Gemini (lite) looks at frames of a film: does each one show the surrender itself, anything graphic, or a
    title card / black frame? -> [(t, surrender, bad)]"""
    import base64
    parts, keep = [], []
    for i, t in enumerate(times):
        jpg = path.with_name(f"{path.stem}_s{i}.jpg")
        if subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1",
                           "-vf", "scale=384:-2", str(jpg)]).returncode == 0 and jpg.exists():
            parts += [{"text": f"Frame {len(keep)}:"},
                      {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(jpg.read_bytes()).decode()}}]
            keep.append(t)
    if not keep:
        return []
    n = len(keep)
    ask = (f"These are {n} numbered frames of a World War II archive film. The film shows: {look_for}\n"
           f"For each frame (Frame 0 first) return three lists of {n} booleans:\n"
           "- surrender: true if the frame shows the surrender itself: soldiers with raised hands, white flags, "
           "men handing over weapons, being searched or disarmed, prisoners being led away by their captors, or "
           "officers at the surrender ceremony or signing the surrender;\n"
           "- graphic: true if it shows dead bodies, wounds, blood or anything a teenager should not see;\n"
           "- card: true if it is a title card, text, a black or blank frame;\n"
           "- watermark: true if a website address, a channel name or a logo is printed over the film.\n"
           "Also watermark_text: the exact website address or channel name printed over the film, '' if none.\n"
           'Return JSON {"surrender": [...], "graphic": [...], "card": [...], "watermark": [...], "watermark_text": ""}')
    ok = lambda d: isinstance(d, dict) and all(isinstance(d.get(k), list) and len(d[k]) == n
                                               for k in ("surrender", "graphic", "card", "watermark"))
    try:
        d = gemini(ask, ok, rounds=3, extra=parts, purpose="surrender frames", models=LITE_FIRST)
    except SystemExit:
        return []
    yes = lambda v: v is True or str(v).strip().lower() in ("true", "yes", "1")   # the lite model writes "true" too
    wt = re.sub(r"[^\w.\-/: ]", "", str(d.get("watermark_text") or "")).strip()[:80]
    if wt:
        WM_TEXT[str(path)] = wt
    return [(t, yes(d["surrender"][i]), yes(d["graphic"][i]), yes(d["card"][i]), yes(d["watermark"][i]))
            for i, t in enumerate(keep)]


def scene_cuts(path, ss, length):
    """Times of the hard cuts between shots in a stretch of film (ffmpeg scene detection)."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{ss:.2f}", "-t", f"{length:.2f}", "-i", str(path), "-vf",
                          "select='gt(scene,0.35)',showinfo", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [ss + float(t) for t in re.findall(r"pts_time:([\d.]+)", log)]


def bright_start(path, ss, limit=2.0):
    """Moves the start past a dark fade-in (the first frame is the loop start and the thumbnail)."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{ss:.2f}", "-t", f"{limit + 0.5:.2f}", "-i", str(path), "-vf",
                          "fps=8,signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    lum = [float(x) for x in re.findall(r"YAVG=([\d.]+)", log)]
    k = next((i for i, v in enumerate(lum) if v >= 45), None)
    return ss + (k / 8 if k is not None else 0.0)


def surrender_window(path, cap, length=SURRENDER_SEC, shortest=6.0):
    """Only the surrender scene itself: a coarse pass over the whole film finds it, a fine pass (2 s steps) finds
    where it starts and ends; the clip is that scene (8-15 s), never the neighbouring stories of a newsreel.
    Nothing graphic, no other site's watermark. None if the scene is shorter than 8 s."""
    dur = probe_duration(path)
    if dur < shortest:
        return None
    n = int(max(8, min(24, dur / 6)))
    coarse = frames_check(path, [dur * 0.03 + i * dur * 0.94 / (n - 1) for i in range(n)], cap["look_for"])
    print(f"surrender: coarse {n} frames | surrender {sum(f[1] for f in coarse)} | graphic {sum(f[2] for f in coarse)}"
          f" | cards {sum(f[3] for f in coarse)}")
    wm = sum(f[4] for f in coarse) * 2 >= len(coarse) > 0   # another site's watermark: used only as a last resort
    hits = [f[0] for f in coarse if f[1] and not f[2]]
    if not hits:
        print("surrender: no frame shows it")
        return None
    best = max(hits, key=lambda t: sum(1 for u in hits if t - 1 <= u <= t + length))
    fine = frames_check(path, sorted({min(dur - 0.3, max(0.0, best - 8 + 2 * k)) for k in range(9)}), cap["look_for"])
    print("surrender: fine", " ".join(f"{f[0]:.0f}{'S' if f[1] else ''}{'G' if f[2] else ''}{'C' if f[3] else ''}"
                                      for f in fine))
    runs, cur = [], []                                 # runs of consecutive surrender frames
    for f in fine:
        if f[1] and not f[2]:
            cur.append(f)
        else:
            runs, cur = runs + ([cur] if cur else []), []
    runs += [cur] if cur else []
    if not runs:
        print("surrender: the fine pass does not show it")
        return None
    run = max(runs, key=len)
    start = max(0.0, run[0][0] - 0.6)
    end = dur if run[-1] is fine[-1] else min(dur, run[-1][0] + 1.6)   # the scene may go on after the last frame
    span = min(length, end - start)
    if span < shortest:
        print(f"surrender: the scene lasts only {span:.1f} s")
        return None
    if any(f[2] for f in coarse + fine if start - 0.1 <= f[0] <= start + span + 0.1):
        print("surrender: something graphic in the scene")
        return None
    cuts = scene_cuts(path, start, min(dur - start, span + 3))
    head = [t for t in cuts if start < t <= start + 2.5]
    if head and min(length, end - head[-1]) >= shortest:   # a cut right after the start: begin on the new shot
        start = head[-1] + 0.04
    span = min(length, end - start)
    tail = [t for t in cuts if start + span - 2.5 <= t < start + span]
    if tail and tail[0] - start >= shortest:          # a cut just before the end: stop before the next shot
        span = tail[0] - start - 0.04
    end = start + span
    ss = bright_start(path, start, limit=max(0.0, min(2.0, span - shortest)))
    span = min(length, end - ss)
    lum, crop = film_stats(path, ss, span)
    print(f"surrender: scene {ss:.1f}-{ss + span:.1f} s of {dur:.0f} s | {len(run)} frames | lum {lum:.0f}")
    return {"ss": ss, "len": span, "crop": crop, "wm": wm} if lum > 15 else None


def find_surrender(tries=10):
    """The first candidate film that passes every check: caption from its description, a clean surrender stretch."""
    cands = surrender_candidates()
    print("surrender: candidates", len(cands), [c["name"][:45] for c in cands[:5]])
    t0, fallback = time.time(), None
    for k, c in enumerate(cands[:tries]):         # frames first (lite, cheap), the caption only for a clean film
        if time.time() - t0 > 300:                     # Gemini overloaded: do not hold up the slot
            print("surrender: 5 minutes spent -> stop searching")
            break
        url = c["url"] or (ia_file(c["ia"]) if c.get("ia") else None)
        if not url:
            continue
        ext = re.search(r"\.(webm|ogv|ogg|mp4|mpg|mpeg|m4v)(?:\?|$)", url, re.I)
        path = download_video(url, f"surrender{k}.{ext.group(1).lower() if ext else 'mp4'}",
                              cap=150_000_000 if c.get("ia") else 60_000_000)
        win = surrender_window(path, {"look_for": (c["desc"] or c["name"])[:400]}) if path else None
        if win and win["wm"]:
            win["wm_text"] = WM_TEXT.get(str(path), "")
            print("surrender: another site's watermark on the film -> only if nothing else is found |", win["wm_text"])
            fallback = fallback or (c, path, win)
            continue
        cap = surrender_caption(c) if win else None
        if cap:
            cap = surrender_context(c, cap)
            return {**c, **cap, **win, "path": path, "name": c.get("ia") or c["name"]}
    if fallback:
        c, path, win = fallback
        cap = surrender_caption(c)
        if cap:
            cap = surrender_context(c, cap)
            print("surrender: using the watermarked film")
            return {**c, **cap, **win, "path": path, "name": c.get("ia") or c["name"]}
    return None


def wrap_caps(text, size, width):
    """Greedy word wrap with the libass width table."""
    lines, cur = [], ""
    for w in text.split():
        if cur and text_w(cur + " " + w, size, 1) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + ([cur] if cur else [])


SURR_TOP, SURR_H = 520, 960                            # film box: full width, 520..1480


def surrender_ass(clip, total):
    """On-screen: WHO SURRENDERS [TO WHOM] above the film; WHERE • WHEN under it; channel block from BRAND_SEC."""
    fam = font_family()
    # prefer structured who + to_whom when present (clearer than a single long top)
    who = (clip.get("who") or "").strip()
    to_whom = (clip.get("to_whom") or "").strip()
    if who:
        head = f"{who} SURRENDERS" + (f" {to_whom}" if to_whom else "")
        head = re.sub(r"\s+", " ", head).strip()[:100]
    else:
        head = clip.get("top") or "SURRENDER"
    sub = clip.get("sub", "")
    for size in range(66, 38, -2):
        lines = wrap_caps(head, size, 960)
        if len(lines) <= (2 if size > 54 else 3) or size <= 40:
            break
    h = int(size * 1.18)
    ssize = next((z for z in range(40, 28, -2) if len(wrap_caps(sub, z, 960)) <= 2), 30) if sub else 0
    slines = wrap_caps(sub, ssize, 960) if sub else []
    sh = int(ssize * 1.2)
    y0 = SURR_TOP - 40 - h * len(lines)
    # under film: PLACE • DATE (always show both when known)
    where = " • ".join(x for x in (clip.get("place"), clip.get("date")) if x) or "WORLD WAR II"
    bsize = next((s for s in range(70, 40, -2) if text_w(where, s, 1) <= 980), 40)
    st = lambda name, size, col: (f"Style: {name},{fam},{size},{col},{col},&H00000000&,&H00000000&,-1,0,0,0,100,100,"
                                  f"1,0,1,0,0,8,0,0,0,1")
    ev = lambda style, x, y, txt: f"Dialogue: 0,{ass_time(0)},{ass_time(total)},{style},,0,0,0,,{{\\pos({x},{y})}}{txt}"
    out = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
           "MarginR, MarginV, Encoding",
           st("Top", size, WHITE), st("Where", bsize, WHITE), st("Sub", ssize or 34, YELLOW),
           f"Style: Chan,{fam},40,{WHITE},{WHITE},&H00000000&,&H00000000&,-1,0,0,0,100,100,0,0,1,0,0,4,0,0,0,1",
           f"Style: Handle,{fam},30,&H00AAAAAA&,&H00AAAAAA&,&H00000000&,&H00000000&,-1,0,0,0,100,100,0,0,1,0,0,8,0,0,0,1",
           "",
           "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    out += [ev("Top", 540, y0 + i * h, l) for i, l in enumerate(lines)]
    out += [ev("Sub", 540, SURR_TOP + SURR_H + 30 + i * sh, l) for i, l in enumerate(slines)]   # the fact under the film
    out.append(ev("Where", 540, SURR_TOP + SURR_H + (36 if not slines else 30 + sh * len(slines) + 22), where))
    bs = min(BRAND_SEC, total / 4)                     # channel block as in every other video
    brand = lambda style, x, y, txt: (f"Dialogue: 0,{ass_time(bs)},{ass_time(total)},{style},,0,0,0,,"
                                      f"{{\\pos({x},{y})\\fad(250,0)}}{txt}")
    out += [brand("Chan", block_x() + (AV_SIZE + 14 if AVATAR.exists() else 0), BLOCK_Y + AV_SIZE // 2, CHANNEL),
            brand("Handle", 540, BLOCK_Y + AV_SIZE + 6, HANDLE)]
    path = W / "surrender.ass"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def render_surrender(clip, music=None, music_start=0.0):
    """One ffmpeg pass: the film stretch fills the box (black borders cut), captions, music only, loudness -14."""
    total = clip["len"]
    ass = surrender_ass(clip, total)
    vf = ("setpts=PTS-STARTPTS," + (f"crop={clip['crop']}," if clip.get("crop") else "") +   # frame 1 at t=0, no black
          f"fps=30,scale=1080:{SURR_H}:force_original_aspect_ratio=increase,crop=1080:{SURR_H},setsar=1,"
          "eq=contrast=1.08:saturation=0.9,format=yuv420p")
    fc = f"[0:v]{vf}[f];color=c=black:s=1080x1920:r=30:d={total:.3f}[bg];[bg][f]overlay=0:{SURR_TOP}:shortest=1"
    args = ["-ss", f"{clip['ss']:.2f}", "-t", f"{total:.3f}", "-i", str(clip["path"])]
    if AVATAR.exists():                                # round avatar of the channel block, as in the other videos
        r = AV_SIZE / 2
        args += ["-i", str(AVATAR.resolve())]
        fc += (f"[b];[1:v]scale={AV_SIZE}:{AV_SIZE},format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
               f"a='if(lte(hypot(X-{r - 0.5},Y-{r - 0.5}),{r - 0.5}),alpha(X,Y),0)'[av];"
               f"[b][av]overlay={block_x()}:{BLOCK_Y}:enable='gte(t,{min(BRAND_SEC, total / 4):.3f})'")
    fc += f",ass={ass.resolve()}:fontsdir={FONTS_DIR}[v];"
    ai = 2 if AVATAR.exists() else 1                    # the audio input after the film (and the avatar)
    if music:
        args += ["-ss", f"{music_start:.2f}", "-stream_loop", "-1", "-i", str(pathlib.Path(music).resolve())]
        fc += (f"[{ai}:a]aresample=44100,aformat=channel_layouts=stereo,atrim=0:{total:.3f},afade=t=in:d=0.3,"
               f"afade=t=out:st={max(0.0, total - 0.8):.3f}:d=0.8,loudnorm=I={LOUDNESS}:TP=-1.5:LRA=11,aresample=44100[a]")
    else:
        args += ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={total:.3f}"]
        fc += f"[{ai}:a]anull[a]"
    ff(*args, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-r", "30", *x264(20),
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "final.mp4")
    return total


def surrender_body(data, translations):
    """Upload body: title, the captions as the description, film + music credits, hashtags, file number."""
    tail = ("\n\n#Shorts #WWII #WW2 #Surrender #ArchiveFootage"
            + f"\n\n📁 A new declassified WWII file every day: follow {HANDLE}"
            + "\n\nReal archive film (public domain / free licence):\n- " + data["film_credit"]
            + (f"\n- Original source of this footage: {data['wm_text']} (its mark is visible in the film)"
               if data.get("wm_text") else "\n- The mark visible in the film belongs to the original source of this "
               "footage, credited above" if data.get("wm") else "")
            + (f"\nMusic: {data['music_credit']}" if data.get("music_credit") else "")
            + f"\n\nFile #{FILE_NO}")
    desc = lambda s, q: cut_bytes(safe_text(safe_text(s, False) + "\n\n" + (f"{safe_text(q)} Tell me in the comments!"
                                                                       if q else "") + tail, False))
    base = (data["title"] + ("\n" + data["sub"].capitalize() if data.get("sub") else "") + "\n"
            + (" • ".join(x for x in (data["place"], data["date"]) if x) or "World War II"))
    tags = list(dict.fromkeys([re.sub(r'[<>#,"]', "", t).strip()[:60] for t in data["tags"]]
                              + ["WW2 surrender", "WWII", "World War 2", "archive footage", "history shorts",
                                 CHANNEL.title()]))
    body = {"snippet": {"title": safe_text(data["title"])[:100], "tags": [t for t in tags if t][:15],
                        "categoryId": "27", "description": desc(base, data.get("question", "")),
                        "defaultLanguage": "en"},
            "status": {"privacyStatus": env("PRIVACY", "public"), "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": False}}
    loc = {l: {"title": safe_text(plain(t["title"]))[:100],
               "description": desc(t.get("summary", "") or base, t.get("question", ""))}
           for l, t in translations.items() if safe_text(plain(t.get("title", "")))}
    if loc:
        body["localizations"] = loc
    return body


def surrender_video(clip, stats, creds):
    """Makes, (dry run: saves) or uploads the surrender video and records it like any other video."""
    from datetime import date
    data = {"title": clip["title"], "top": clip["top"], "place": clip.get("place", ""), "date": clip.get("date", ""),
            "who": clip.get("who", ""), "to_whom": clip.get("to_whom", ""),
            "question": clip["question"], "tags": clip["tags"], "film_credit": clip["credit"], "headline": clip["top"],
            "wm": bool(clip.get("wm")), "wm_text": clip.get("wm_text", ""), "sub": clip.get("sub", ""),
            "lines": [], "music": ["sad", "emotional", "dramatic", "cinematic"], "source": clip["name"]}
    print("surrender:", json.dumps({k: data[k] for k in ("title", "who", "to_whom", "place", "date")},
                                   ensure_ascii=False))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=1) as ex:
        tr = ex.submit(translate, data["title"], data["question"], f"{data['top']}. {data['place']}, {data['date']}.", "")
        with stage("final render"):
            try:
                music, data["music_credit"] = pick_music(data)
                start = best_start(music, clip["len"]) if music else 0.0
            except Exception as e:
                print("music skipped:", type(e).__name__, str(e)[:120])
                music, data["music_credit"], start = None, None, 0.0
            data["music_file"] = music.name if music else ""
            data["seconds"] = round(render_surrender(clip, music, start), 1)
        body = surrender_body(data, tr.result())
    (W / "metadata.json").write_text(json.dumps({"upload": body, "script": data}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    if DRY_RUN:
        print("DRY RUN: nothing uploaded or saved. Video: work/final.mp4, title/description: work/metadata.json")
        return
    yt = youtube(creds)
    with stage("upload"):
        vid = upload(yt, body)
    # record every identifier so Japan / Missouri variants cannot reappear under a different spelling
    for key in dict.fromkeys([clip.get("name"), clip.get("ia"), data.get("title")]):
        if key:
            entry = f"surrender: {key}"
            if entry not in used:
                used.append(entry)
    USED.write_text(json.dumps(used, ensure_ascii=False, indent=1), encoding="utf-8")
    stats["videos"].append({"id": vid, "date": date.today().isoformat(), "category": "surrender", "hook": None,
                            "length": "film", "topic": f"surrender: {clip['name']}", "title": plain(data["title"]),
                            "seconds": data["seconds"], "words": 0, "music": data.get("music_file"),
                            "opening": "film", "headline": data["top"], "clips": 1, "tts": None,
                            "region": surr_region(f"{clip.get('name', '')} {data.get('title', '')} {data.get('top', '')}"),
                            "place": data.get("place"), "who": data.get("who")})
    save_stats(stats)
    with stage("playlist, comments, replies"):
        if THUMB:
            stats["videos"][-1]["thumb"] = set_thumbnail(yt, vid)
        add_to_playlist(yt, vid)
        post_comment(yt, vid, data)
        reply_comments(yt, stats)
    to_tiktok(stats, body)
    save_stats(stats)


READY_DIR = pathlib.Path("stories/classic")


def ready_script():
    """Andrii, Oct 21: hand-made classic scripts (stories/classic/*.json: topic, category, hook, length,
    title_format, the script keys and an optional "cover" Commons file for the first frame = the thumbnail) come
    first, lowest "priority" first; Gemini writes only when none is left. -> (topic, hook, data) or None."""
    for p in sorted(READY_DIR.glob("*.json"), key=lambda p: (json.loads(p.read_text(encoding="utf-8"))
                                                             .get("priority", 99), p.name)):
        d = json.loads(p.read_text(encoding="utf-8"))
        title = plain(d.get("title", "")).lower()
        if not d.get("topic") or is_used(d["topic"]) or (title and any(t.lower().startswith(title) for t in CHANNEL_TITLES
                                                                       + [v.get("title", "") for v in load_stats()["videos"]])):
            continue
        got = wiki_text(d["topic"])
        if not got or not got[0]:
            print("ready script skipped (article not read):", p.name)
            continue
        print("ready script:", p.name)
        set_category(d.get("category", "tanks"))
        LENGTH[0] = d.get("length", "normal")
        TITLE_FMT[0] = d.get("title_format", "detail")
        data = {k: v for k, v in d.items() if k not in ("priority", "topic", "category", "length", "hook",
                                                         "title_format", "note")}
        data["story_topic"] = d["topic"]
        return research(topic_of([got])), d.get("hook", "curiosity"), data
    return None


def commons_picture(name, out):
    """A hand-picked Wikimedia Commons file (free licence only) -> (path, credit) or None."""
    try:
        page = requests.get(COMMONS, headers=UA, timeout=60, params={
            "action": "query", "format": "json", "formatversion": 2, "titles": "File:" + name, "prop": "imageinfo",
            "iiprop": "url|size|extmetadata", "iiurlwidth": 1600}).json()["query"]["pages"][0]
        item = image_item(name.rsplit(".", 1)[0].replace("_", " "), (page.get("imageinfo") or [{}])[0], 0)
        path = download(item[0], out) if item else None
        return (path, item[1]) if path else None
    except Exception as e:
        print("cover not loaded:", name[:60], type(e).__name__)
        return None


def main():
    global FILE_NO, PART, CHANNEL_ID
    from concurrent.futures import ThreadPoolExecutor
    from datetime import date, timedelta
    PART = 0
    LENGTH[0], FACT_FILM[0] = "normal", False
    SERIES_INFO.clear()
    COLD.clear()
    stats = load_stats()
    FILE_NO = max(len(used), len(stats["videos"])) + 1
    try:
        creds = credentials()
    except KeyError:
        if not DRY_RUN:
            raise SystemExit("YouTube secrets are missing: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN")
        creds = None                                 # a test run works without YouTube access
    if creds:
        with stage("youtube read"):
            try:                                     # latest uploads straight from the channel
                yt0 = youtube(creds)
                up = yt0.channels().list(part="contentDetails", mine=True).execute()["items"][0]
                CHANNEL_ID = up.get("id", "")
                pl = up["contentDetails"]["relatedPlaylists"]["uploads"]
                items = yt0.playlistItems().list(part="snippet", playlistId=pl, maxResults=50).execute().get("items", [])
                CHANNEL_TITLES[:] = [i["snippet"]["title"] for i in items]
                nums = [int(n) for i in items for n in re.findall(r"File #(\d+)", i["snippet"].get("description", ""))]
                FILE_NO = max([FILE_NO] + [n + 1 for n in nums])   # numbering continues even if used.json was not saved
                print("recent uploads:", len(CHANNEL_TITLES))
            except Exception as e:
                print("recent uploads not read:", str(e)[:120])
            if LEARN:
                refresh_stats(creds, stats)
    series = stats.get("series") if SERIES_RATE > 0 else None
    if series and series.get("date", "") < (date.today() - timedelta(days=2)).isoformat():
        print("series expired:", series.get("key"))
        stats.pop("series", None)
        series = None
    if env("CATEGORY") == "surrender" or (not env("CATEGORY") and not series and SURRENDER_EVERY > 0
                                           and (len(videos_of(stats)) + 1) % SURRENDER_EVERY == 0):
        with stage("surrender"):                   # every 4th video: a real surrender on archive film, music only
            clip = find_surrender()
        if clip:
            set_category("surrender")
            print("category: surrender | film:", clip["name"])
            return surrender_video(clip, stats, creds)
        if DRY_RUN and env("CATEGORY") == "surrender":
            raise SystemExit("surrender test: no usable archive film found")
        print("surrender: no usable archive film -> a normal video in this slot")
    ready = None if (series or env("CATEGORY") or env("HOOK")) else ready_script()
    if ready:                                        # a hand-made script: no topic or script Gemini calls
        topic, hook, data = ready
    else:
        with stage("topic"):
            if series and not env("CATEGORY"):             # part 2 of yesterday's or today's two-part story
                set_category(series["category"])
                got = pmap(wiki_text, series["articles"])
                if all(usable(g, pair=True) for g in got):
                    topic, PART = topic_of(got), 2
                    SERIES_INFO.update(series)
                else:
                    stats.pop("series", None)
            if PART != 2:
                if not env("CATEGORY") or env("CATEGORY") == "surrender":
                    set_category(pick_category(stats))
                forced = normalize_hook((env("HOOK") or "").strip().lower())
                if forced == "fact" or (forced in ("", "auto") and fact_turn(stats)):
                    LENGTH[0] = "fact" if KIND == "single" else "normal"   # ONE FACT: decided before the topic
                topic = pick_topic()
                if CATEGORY == "events" and KIND == "single" and LENGTH[0] != "fact" and len(topic["text"]) >= 9000 \
                        and not series and random.random() < SERIES_RATE:
                    PART = 1                                 # a big battle: told in two parts
        with stage("research"):
            topic = research(topic)
        TITLE_FMT[0] = pick_title_format()
        if LENGTH[0] == "fact":
            hook = "fact"
            FACT_FILM[0] = film_found(topic)             # lets the narration say 'Watch...'
        else:
            forced = normalize_hook((env("HOOK") or "").strip().lower())
            # allow workflow to force any current hook by name (incl. legacy aliases)
            if forced and forced not in ("", "auto", "fact") and forced in HOOKS:
                hook = forced
            else:
                hook = pick_hook(stats)
            LENGTH[0] = pick_length(stats, hook)
        WINNERS[:], LOSERS[:] = winners(stats)
        print("category:", CATEGORY, "| hook:", hook, "| length:", LENGTH[0], "| title:", TITLE_FMT[0], "| topic:", topic["key"],
              f"| part {PART}/2" if PART else "")
        with stage("script"):
            data = write_script(topic, hook, stats["recent"])
            if hook == "coldopen":
                data = cold_prepare(data, topic)
            elif hook == "map":
                data = map_prepare(data, topic)
    print(json.dumps(data, ensure_ascii=False))
    with ThreadPoolExecutor(max_workers=1) as ex:
        translations = ex.submit(translate, *texts(data))   # translated while the video renders
        credits = make_video(data, topic)
        body = metadata(data, topic, credits, translations.result())
    if hook == "map" and not LOOK.get("map_art"):
        hook = "map-fallback"                        # the map could not be drawn: keep it out of the hook learning
    (W / "metadata.json").write_text(json.dumps({"upload": body, "script": data}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    if DRY_RUN:
        print("DRY RUN: nothing uploaded or saved. Video: work/final.mp4, title/description: work/metadata.json")
        return
    yt = youtube(creds)
    with stage("upload"):
        vid = upload(yt, body)
    used.append(topic["key"])
    if data.get("story_topic") and data["story_topic"] != topic["key"]:   # a ready script's own name (redirects)
        used.append(data["story_topic"])
    USED.write_text(json.dumps(used, ensure_ascii=False, indent=1), encoding="utf-8")
    stats["videos"].append({"id": vid, "date": date.today().isoformat(), "category": CATEGORY, "hook": hook,
                            "length": LENGTH[0],
                            "topic": topic["key"], "title": plain(data["title"]), "seconds": data.get("seconds"),
                            "words": len((plain(data["headline"]) + " " + " ".join(map(plain, all_lines(data)))).split()),
                            "music": data.get("music_file"), "opening": OPENING, "headline": plain(data["headline"]),
                            "part": PART or None, "clips": sum(c.startswith("Film:") for c in credits),
                            "tts": TTS_USED[0] if TTS_USED else None, "title_format": TITLE_FMT[0]})
    stats["recent"].append(plain(data["headline"]))
    if PART == 1:
        stats["series"] = {"key": topic["key"], "articles": topic["articles"], "category": CATEGORY, "id": vid,
                           "title": body["snippet"]["title"], "last": plain(all_lines(data)[-1]),
                           "date": date.today().isoformat()}
    elif PART == 2:
        stats.pop("series", None)
    save_stats(stats)
    with stage("playlist, comments, replies"):
        if THUMB:
            stats["videos"][-1]["thumb"] = set_thumbnail(yt, vid)
        add_to_playlist(yt, vid)
        post_comment(yt, vid, data)
        upload_captions(yt, vid)
        if PART == 2:
            link_parts(yt, SERIES_INFO, vid, body["snippet"]["title"])
        reply_comments(yt, stats)
    to_tiktok(stats, body)
    save_stats(stats)


def summary():
    """Where the time went and how many Gemini requests the run used (printed even if the run failed)."""
    TIMES["total"] = time.time() - T0
    print("\n== timing:", " | ".join(f"{k} {v:.1f}s" for k, v in TIMES.items()))
    print("== gemini requests:", sum(CALLS.values()), CALLS or "", "| models out for this run:", sorted(DEAD) or "-")


if __name__ == "__main__":
    try:
        main()
    finally:
        summary()
