"""OPENVERSE (Andrii, Nov 17: 'впроваджуй всі три по черзі'): api.openverse.org = one search over openly licensed
media (Flickr incl. Flickr Commons / LOC / national archives, Smithsonian, NASA, Freesound, ...). No key: 20
requests a minute, 200 a day (enough for one auto story a run).
- images(q): pictures for a chapter when Commons has too few (autostory.pictures); free licences only (public
  domain, CC0, CC BY, CC BY-SA, credited); Commons itself is skipped (searched already); modern photos (museums,
  re-enactors, air shows, models, 1960+) are dropped by their title/tags, Gemini's look (jurgen.match_pictures)
  drops the rest. A shot's file 'ov:<id>' is fetched by longform.commons_photo -> photo(id).
- sounds(q): real recordings for SFX (Freesound CC0 / public domain): tools/sfx_fetch.py.
Every result carries its credit line (title, creator, source, licence)."""
import json, pathlib, re, sys, time

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
from shorts import W

API = "https://api.openverse.org/v1"
UA = {"User-Agent": "ww2-long/1.0 (archive history videos; github.com/TerraIncognita001/ww2-long)"}
IMG_LIC = "pdm,cc0,by,by-sa"                           # no NC / ND (YouTube is commercial)
SND_LIC = "pdm,cc0"
MODERN = re.compile(r"\b(museum|musee|musée|reenact\w*|re-enact\w*|replica|memorial|air ?show|airshow|model|models|"
                    r"living history|restored|restoration|exhibit\w*|display|diorama|lego|toy|cosplay|game|render|3d|"
                    r"veterans day|anniversary|(19[6-9]|20[0-3])\d)\b", re.I)
LIC_NAME = {"pdm": "Public Domain Mark", "cc0": "CC0", "by": "CC BY", "by-sa": "CC BY-SA"}
_calls = {"n": 0, "out": False}


def _get(path, **params):
    """One API call; a refused one (429: the day's 200 are used) turns Openverse off for this run."""
    if _calls["out"]:
        return None
    for k in range(3):
        try:
            r = requests.get(f"{API}/{path}", params=params, headers=UA, timeout=40)
            _calls["n"] += 1
            if r.status_code == 429:
                _calls["out"] = True
                print("openverse: rate limit reached, off for this run")
                return None
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if k == 2:
                print("openverse failed:", type(e).__name__, str(e)[:100])
            time.sleep(3 * (k + 1))
    return None


def credit(r):
    lic = LIC_NAME.get(r.get("license"), r.get("license", "").upper())
    who = f" by {r['creator']}" if r.get("creator") else ""
    t = re.sub(r"\s+", " ", r.get("title") or "Untitled").strip()
    t = t if len(t) <= 90 else t[:90].rsplit(" ", 1)[0] + "..."
    return f"{t}{who} ({r.get('source', '').replace('_', ' ').title()}, {lic})"


def modern(r):
    text = " ".join([r.get("title") or ""] + [t.get("name", "") for t in r.get("tags") or [] if isinstance(t, dict)])
    return bool(MODERN.search(text))


def images(q, n=8, min_w=700):
    """Free-licence pictures for a search -> [{id, title, url, width, height, credit}] (no Commons, no modern)."""
    js = _get("images/", q=q, license=IMG_LIC, page_size=20, mature="false") or {}
    out = []
    for r in js.get("results") or []:
        if r.get("source") == "wikimedia" or r.get("mature") or modern(r):
            continue
        if (r.get("width") or 0) < min_w and (r.get("height") or 0) < min_w:
            continue
        out.append({"id": r["id"], "title": r.get("title") or "", "url": r["url"], "width": r.get("width"),
                    "height": r.get("height"), "credit": credit(r), "landing": r.get("foreign_landing_url")})
        if len(out) >= n:
            break
    return out


def photo(oid, out):
    """'ov:<id>' -> the picture saved as `out` (JPEG) -> (path, credit) or None."""
    r = _get(f"images/{oid}/")
    if not r or r.get("license") not in IMG_LIC.split(","):
        return None
    from PIL import Image
    import io
    for url in (r.get("url"), r.get("thumbnail")):
        try:
            b = requests.get(url, headers=UA, timeout=90)
            b.raise_for_status()
            Image.open(io.BytesIO(b.content)).convert("RGB").save(out, quality=95)
            return out, credit(r)
        except Exception as e:
            print("openverse picture failed:", oid, type(e).__name__)
    return None


def sounds(q, n=8, most=30.0):
    """Public-domain / CC0 recordings -> [{id, title, url, duration, credit, source}] (Freesound, Wikimedia audio)."""
    js = _get("audio/", q=q, license=SND_LIC, page_size=20, mature="false") or {}
    out = []
    for r in js.get("results") or []:
        dur = (r.get("duration") or 0) / 1000.0
        if r.get("mature") or not r.get("url") or not 0.3 <= dur <= most or (r.get("title") or "").startswith("LL-"):
            continue                                   # LL- = Lingua Libre: a word read aloud, not a sound
        out.append({"id": r["id"], "title": r.get("title") or "", "url": r["url"], "duration": round(dur, 1),
                    "credit": credit(r), "source": r.get("source"), "tags": [t.get("name") for t in r.get("tags") or []
                                                                             if isinstance(t, dict)][:8]})
        if len(out) >= n:
            break
    return out


if __name__ == "__main__":                             # python openverse.py images|sounds "query"
    kind, q = sys.argv[1], " ".join(sys.argv[2:])
    for x in (images(q) if kind == "images" else sounds(q)):
        print(json.dumps(x, ensure_ascii=False)[:300])
