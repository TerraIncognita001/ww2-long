"""The C5 narrator (Andrii, Nov 23: 'ось промпт для озвучки, продемонструй на тестовому відео'): a serious documentary
voice cloned from D:/ytb_bots/voices/voice_C/ref.wav by the LOCAL VoiceStudio server (engine voxcpm2, Apache-2.0),
settings fixed by the owner: seed 23, num_step 20, effect 'raw', the C5 instruct. LOCAL ONLY (the GitHub runner has no
VoiceStudio): longform uses it with L_TTS=c5.
- numbers and years as words ('1944' -> 'nineteen forty four'): the model reads words exactly;
- phrases of <= ~300 characters, ONE request at a time (the server is shared with other bots), joined with 0.4 s;
- every phrase heard back by Whisper: a phrase that says something else (the model sometimes makes up text) is made
  again with seed 31, 57, 77, 91 (nothing else changes); the closest one is kept;
- cache: the same text + settings = the same file (work/c5cache);
- loudness: loudnorm I=-15 TP=-1.5; word times for the captions from Whisper on the joined file."""
import difflib, hashlib, json, re, subprocess, threading, urllib.request, uuid
from pathlib import Path

VOICES = {   # L_TTS=<name>: the reference recording (ref.wav + ref.txt, kept OUTSIDE the public repo) + the instruct
    "c5": (Path(r"D:\ytb_bots\voices\voice_C"),
           "A young American man with a warm natural voice, realistic human delivery, close microphone. "
           "Serious, grave historical documentary narrator, slow and measured, deep and steady, respectful tone, no humor."),
    "andrii": (Path(r"D:\ytb_bots\voices\voice_andrii"),   # Andrii's own voice (Nov 23), from his YouTube video
               "Realistic human delivery, close microphone. Serious, grave historical documentary narrator, "
               "slow and measured, steady, respectful tone, no humor."),
}
VOICE = "c5"
URL = "http://localhost:3900"
SEEDS = (23, 31, 57, 77, 91)
PAUSE = 0.4
GOOD = 0.88                                            # Whisper words vs the phrase's words (difflib ratio)
CACHE = Path(__file__).resolve().parent / "work" / "c5cache"
_server, _ears = threading.Lock(), threading.Lock()
_model = []


def health():
    with urllib.request.urlopen(URL + "/health", timeout=10) as r:
        h = json.loads(r.read())
    if h.get("status") != "ok" or h.get("engine") != "voxcpm2":
        raise RuntimeError(f"VoiceStudio is not ready for C5: {h}")
    return h


def spoken(text):
    """What the model must hear: years, dates and every other number as words."""
    import shorts as S
    t = S.kokoro_say(text)                            # '1944' -> 'nineteen forty four', '6 August' -> 'the sixth of August'
    t = re.sub(r"(\d+)\s*%", r"\1 percent", t)
    t = re.sub(r"\b(\d{1,2}):(\d\d)\b", lambda m: S.spell_num(int(m.group(1))) + (
        " o'clock" if m.group(2) == "00" else " oh " + S.ONES[int(m.group(2))] if m.group(2)[0] == "0"
        else " " + S.spell_num(int(m.group(2)))), t)  # 8:15 -> eight fifteen
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)          # 130,000 -> 130000
    t = re.sub(r"\b(\d+)\.(\d+)\b", lambda m: S.spell_num(int(m.group(1))) + " point " +
               " ".join(S.ONES[int(c)] for c in m.group(2)), t)
    t = re.sub(r"\d+", lambda m: S.spell_num(int(m.group())) if int(m.group()) < 1_000_000_000 else m.group(), t)
    return re.sub(r"\s+", " ", t).strip()


def phrases(text, limit=300):
    out, cur = [], ""
    for s in re.split(r"(?<=[.!?:;])\s+", text.strip()):
        if cur and len(cur) + 1 + len(s) > limit:
            out.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
    return out + ([cur] if cur else [])


def generate(text, seed, out):
    if out.exists() and out.stat().st_size > 2000:
        return out
    b = uuid.uuid4().hex
    vdir, instruct = VOICES[VOICE]
    fields = {"text": text, "language": "en", "engine": "voxcpm2", "seed": seed, "num_step": 20,
              "effect_preset": "raw", "instruct": instruct,
              "ref_text": (vdir / "ref.txt").read_text(encoding="utf-8").strip()}
    parts = [f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items()]
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="ref_audio"; filename="ref.wav"\r\n'
                 f'Content-Type: audio/wav\r\n\r\n'.encode() + (vdir / "ref.wav").read_bytes() + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req = urllib.request.Request(URL + "/generate", data=b"".join(parts), method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with _server, urllib.request.urlopen(req, timeout=900) as r:   # one request at a time
        data = r.read()
    tmp = out.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.replace(out)
    return out


def model():
    if not _model:
        from faster_whisper import WhisperModel
        _model.append(WhisperModel("small.en", device="cpu", compute_type="int8"))   # the GPU is VoiceStudio's
    return _model[0]


def heard(path, words=False):
    with _ears:
        segs, _ = model().transcribe(str(path), language="en", word_timestamps=words, beam_size=5)
        segs = list(segs)
    if words:
        return [(w.word.strip(), w.start) for s in segs for w in s.words]
    return " ".join(s.text for s in segs)


def norm(t):
    return re.sub(r"[^a-z ]", "", spoken(t.replace("-", " ")).lower().replace("-", " ")).split()


def score(said, wanted):
    return difflib.SequenceMatcher(None, norm(said), norm(wanted)).ratio()


def phrase_wav(text):
    """The phrase with the first seed Whisper agrees with (or the closest of all seeds)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    best = None
    for seed in SEEDS:
        key = hashlib.sha1(json.dumps([text, seed, VOICE, *map(str, VOICES[VOICE]), 20, "raw"]).encode()).hexdigest()[:16]
        wav = generate(text, seed, CACHE / f"{key}.wav")
        r = score(heard(wav), text)
        if best is None or r > best[0]:
            best = (r, wav, seed)
        if r >= GOOD:
            break
        print(f"  c5: seed {seed} said something else ({r:.2f}): {text[:60]}")
    if best[0] < GOOD:
        print(f"  c5: kept seed {best[2]} ({best[0]:.2f}) for: {text[:70]}")
    return best[1]


def speak(text, path, voice=None):
    """longform's voice call: text -> path (mp3), returns [(word, start s)] like S.speak."""
    global VOICE
    VOICE = voice or VOICE
    health()
    path = Path(path)
    wavs = [phrase_wav(p) for p in phrases(spoken(text))]
    ins, chain = [], []
    for i, w in enumerate(wavs):
        ins += ["-i", str(w)]
        chain.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,"
                     f"apad=pad_dur={PAUSE if i < len(wavs) - 1 else 0.05}[a{i}]")
    fc = ";".join(chain) + ";" + "".join(f"[a{i}]" for i in range(len(wavs))) + \
        f"concat=n={len(wavs)}:v=0:a=1,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=44100[out]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-map", "[out]",
                    "-c:a", "libmp3lame", "-b:a", "192k", str(path)], check=True)
    return heard(path, words=True)
