"""EARS (Andrii, Nov 17: 'впроваджуй всі три по черзі'): earshot (github.com/Leonxlnx/earshot, MIT) lets the bot
HEAR what it made: CLAP + AST models on the CPU, in their own venv (torch is big: kept out of the bot's Python).
Install once (local PC): python -m venv %USERPROFILE%/.earshot-venv; <venv>/Scripts/python -m pip install torch
--index-url https://download.pytorch.org/whl/cpu; <venv>/Scripts/python -m pip install <earshot clone>.
Not installed (GitHub runner) -> ok() is False and every check is skipped (the run never stops on it).
- rank(desc, paths): Openverse SFX candidates sorted by how well they sound like the description (tools/sfx_fetch).
- describe(path): what a file sounds like (the period speech cut: a voice, not hiss - Truman's first cut).
- listen(video, segs): the QA of a rendered video: a listening timeline (events, loudness), silences where the
  narrator is not speaking and no beat is planned ('на 1:10 немає озвучки'), an annotated sheet PNG to look at."""
import json, os, pathlib, re, subprocess

VENV = pathlib.Path(os.environ.get("EARSHOT_VENV", pathlib.Path.home() / ".earshot-venv"))
PY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
QUIET_DB = -45.0                                       # quieter than this for > GAP_S = a hole in the sound
GAP_S = 1.5


def ok():
    return os.environ.get("L_EARS", "1") == "1" and PY.exists()


def _run(code, *args, timeout=900):
    """One earshot call in its venv -> the JSON it prints (None on any failure: ears never stop a run)."""
    try:
        r = subprocess.run([str(PY), "-c", code, *map(str, args)], capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        if r.returncode:
            print("ears failed:", (r.stderr.strip().splitlines() or ["?"])[-1][:200])
            return None
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        print("ears failed:", type(e).__name__, str(e)[:150])
        return None


def rank(desc, paths):
    """-> [{path, score (calibrated z), verdict, like}] best first."""
    js = _run("import sys,json;from earshot import api;r=api.rank(sys.argv[2:],sys.argv[1]);"
              "print(json.dumps([{'path':x['path'],'score':x['z'],'verdict':x['verdict'],"
              "'like':x['sounds_most_like']} for x in r['results']]))", desc, *paths)
    return js


def describe(path, start=None, end=None):
    """-> {summary (earshot's words), speech (AudioSet's speech probability 0-1, the highest speech label)}"""
    js = _run("import sys,json;from earshot import api;a=sys.argv;r=api.describe(a[1],"
              "float(a[2]) if a[2]!='-' else None,float(a[3]) if a[3]!='-' else None);"
              "print(json.dumps({'summary':r.get('summary','')}))",
              path, "-" if start is None else start, "-" if end is None else end)
    if not js:
        return None
    tail = js["summary"].split("AudioSet:", 1)[-1]
    sp = [float(v) for v in re.findall(r"(?:Speech|speech[^,]*|Narration[^,]*|Conversation) (0?\.\d+|1\.0)", tail)]
    return {"summary": js["summary"], "speech": max(sp, default=0.0)}


def is_voice(path, least=0.5):
    """The period speech cut is a VOICE (AudioSet speech >= 0.5), not noise. None = can't tell (no ears)."""
    if not ok():
        return None
    r = describe(path)
    return None if not r else r["speech"] >= least


def levels(path, step=0.25):
    """Short-term level (dBFS RMS) every `step` s of a media file's sound, by ffmpeg (no models)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float) / 32768.0
    n = int(8000 * step)
    return [20 * np.log10(np.sqrt(np.mean(x[i:i + n] ** 2)) + 1e-9) for i in range(0, len(x) - n, n)], step


def holes(path, segs=None):
    """Stretches quieter than QUIET_DB for > GAP_S (the whole mix: voice, music, SFX) -> [(from, to)]. Intended
    quiet (the intro's hush is a speech, not silence) is not excluded: any real hole is a fault."""
    lv, step = levels(path)
    out, a = [], None
    for i, v in enumerate(lv + [0.0]):
        if v < QUIET_DB and a is None:
            a = i * step
        elif v >= QUIET_DB and a is not None:
            if i * step - a > GAP_S and a > 0.5:
                out.append((round(a, 2), round(i * step, 2)))
            a = None
    return out


def listen(video, segs=None, sheet=None):
    """QA of a rendered video (local runs with ears): holes in the sound (no models) + earshot's timeline summary
    and its annotated sheet PNG (work/ears_sheet.png) -> list of problems (printed; soft: the run goes on)."""
    probs = [f"sound hole {a:.1f}-{b:.1f} s (quieter than {QUIET_DB:.0f} dB)" for a, b in holes(video, segs)]
    if ok():
        sheet = sheet or str(pathlib.Path(video).with_name("ears_sheet.png"))
        js = _run("import sys,json;from earshot import api;r=api.timeline(sys.argv[1],video=sys.argv[1]);"
                  "api.sheet(sys.argv[1],sys.argv[2],video=sys.argv[1]);"
                  "print(json.dumps({'summary':r.get('summary','')}, default=str))", video, sheet, timeout=1800)
        if js:
            print("ears:", js["summary"][:600])
            print("ears sheet:", sheet)
    for p in probs:
        print("EARS:", p)
    return probs
