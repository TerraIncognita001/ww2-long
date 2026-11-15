"""THE PERIOD SPEECH (Andrii, Nov 15, HARD RULE): every video's intro plays a recording of the time, spoken by a
KNOWN person (a head of state, a general, a minister, a famous reporter) and DIRECTLY about the video's topic.
find(topic, queries) searches Wikimedia Commons for free (public domain / CC) audio, lets Gemini LISTEN to each
candidate (who speaks, is it about the topic, the exact words and seconds of one 6-9 s sentence), checks that the
chosen seconds really hold speech (loudness, little silence) and returns the story's `period_audio` entry + the cut.
No speech found -> None: autostory takes the next topic (Andrii: no video without a speech).
Run: python speech.py "Korean War" "Truman Korea" "MacArthur farewell address"   (prints what it finds)"""
import base64, json, pathlib, re, subprocess, sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
import shorts as S
import jurgen as J
from shorts import W

AUDIO = re.compile(r"\.(ogg|oga|opus|mp3|wav|flac|webm)$", re.I)
MAX_FILES, MAX_LISTEN = 8, 600                         # candidates per topic, seconds of each sent to Gemini


def commons_audio(query, limit=5):
    """Free audio files of a Commons search -> [(file name, url, credit, description)]."""
    try:
        r = requests.get(S.COMMONS, headers=S.UA, timeout=60, params={
            "action": "query", "format": "json", "formatversion": 2, "generator": "search",
            "gsrsearch": f"{query} filetype:audio", "gsrnamespace": 6, "gsrlimit": 10,
            "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime"}).json()
    except Exception:
        return []
    out = []
    for p in sorted(r.get("query", {}).get("pages", []), key=lambda p: p.get("index", 0)):
        name = p["title"][5:]
        ii = (p.get("imageinfo") or [{}])[0]
        if not AUDIO.search(name) or ii.get("size", 0) > 120_000_000:
            continue
        item = J.free_item(name, {**ii, "thumburl": None})
        if not item:
            continue
        meta = ii.get("extmetadata", {})
        desc = re.sub(r"<[^>]+>", " ", meta.get("ImageDescription", {}).get("value", ""))
        out.append((name, ii.get("url"), item[1], re.sub(r"\s+", " ", desc).strip()[:400]))
        if len(out) >= limit:
            break
    return out


def listen(path, name, desc, topic):
    """Gemini listens to the first MAX_LISTEN s -> {speaker, known, about_topic, from, to, text, date} or None."""
    small = W / "speech_listen.mp3"
    if subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", str(MAX_LISTEN), "-i", str(path), "-ac", "1",
                       "-ar", "16000", "-b:a", "32k", str(small)]).returncode:
        return None
    part = {"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(small.read_bytes()).decode()}}
    prompt = (f"This is a historical recording from Wikimedia Commons, file '{name}'. Its description: {desc or '-'}\n"
              f"TOPIC of our documentary: {topic}.\nListen to the recording and return JSON:\n"
              '{"speaker": "the full name of who speaks (from the voice and the words; the file name and description '
              'help)", "known": true if the speaker is a famous person of that time (a head of state, a general, an '
              'admiral, a minister, a famous war reporter), "about_topic": true if the words are DIRECTLY about the '
              f'topic ({topic}), "from": seconds, "to": seconds, "text": "the exact words of ONE complete sentence, '
              '6 to 9 seconds long, the most dramatic one about the topic", "date": "month and year of the recording, '
              'e.g. JUNE 1950, or the year"}. If nobody speaks clearly about the topic: {"known": false}.')
    try:
        d = S.gemini(prompt, lambda d: isinstance(d, dict) and "known" in d, rounds=2, extra=[part],
                     purpose="speech", read=240)
    except SystemExit:
        return None
    return d if isinstance(d, dict) else None


def is_speech(path, a, b):
    """The cut holds speech: not quiet (mean > -40 dB) and under 35 % silence."""
    log = subprocess.run(["ffmpeg", "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}", "-i", str(path), "-af",
                          "volumedetect,silencedetect=noise=-38dB:d=0.3", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"mean_volume: (-?[\d.]+) dB", log)
    quiet = sum(float(x) for x in re.findall(r"silence_duration: ([\d.]+)", log))
    return bool(m) and float(m.group(1)) > -40 and quiet < 0.35 * (b - a)


def find(topic, queries=()):
    """-> {"key", "file", "credit", "from", "to", "speaker", "text", "date"} or None."""
    seen, cands = set(), []
    for q in [topic, *queries]:
        for c in commons_audio(str(q)[:80]):
            if c[0] not in seen:
                seen.add(c[0])
                cands.append(c)
    print(f"speech: {len(cands)} recordings on Commons for {topic}: {[c[0][:50] for c in cands[:MAX_FILES]]}")
    (W / "speech").mkdir(parents=True, exist_ok=True)
    for k, (name, url, credit, desc) in enumerate(cands[:MAX_FILES]):
        path = W / "speech" / f"s{k}{pathlib.Path(name).suffix.lower()}"
        try:
            r = requests.get(url, headers=S.UA, timeout=180)
            r.raise_for_status()
            path.write_bytes(r.content)
        except Exception as e:
            print("speech: download failed:", name[:60], type(e).__name__)
            continue
        d = listen(path, name, desc, topic)
        if not d or d.get("known") is not True or d.get("about_topic") is not True:
            print("speech: not a known person about the topic:", name[:60], (d or {}).get("speaker"))
            continue
        try:
            a, b = float(d["from"]), float(d["to"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (5.0 <= b - a <= 10.0) or not is_speech(path, a, b):
            print(f"speech: the cut {a}-{b} is not a clear 5-10 s of speech:", name[:60])
            continue
        print(f"speech found: {d.get('speaker')} ({d.get('date')}) {a}-{b} s: \"{d.get('text')}\" | {name}")
        return {"key": "speech", "file": name, "credit": credit, "from": round(a - 0.15, 2), "to": round(b + 0.2, 2),
                "speaker": str(d.get("speaker", ""))[:60], "text": str(d.get("text", ""))[:200],
                "date": str(d.get("date", ""))[:20]}
    return None


if __name__ == "__main__":
    print(json.dumps(find(sys.argv[1], sys.argv[2:]), ensure_ascii=False, indent=1))
