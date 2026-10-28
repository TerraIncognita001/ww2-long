"""Commons via HTML (the API gives 429 here): category listings, search, licence + size of a file."""
import re, sys, time, json, urllib.parse, subprocess, html as H, pathlib
UA = "Classified1945ShortsBot/1.0 (https://terraincognita001.github.io/terra-incognita/)"
CACHE = pathlib.Path("/tmp/story_tools/ccache"); CACHE.mkdir(parents=True, exist_ok=True)

def get(url):
    key = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", url)[-180:] + ".html")
    if key.exists() and key.stat().st_size > 500:
        return key.read_text(encoding="utf-8", errors="replace")
    for i in range(4):
        r = subprocess.run(["curl", "-sS", "-A", UA, "-w", "\n%{http_code}", url], capture_output=True, text=True)
        body, code = r.stdout.rsplit("\n", 1)
        if code == "200":
            key.write_text(body, encoding="utf-8"); time.sleep(0.7); return body
        time.sleep(3 * (i + 1))
    return ""

def files_in(html):
    return list(dict.fromkeys(H.unescape(urllib.parse.unquote(m)) for m in re.findall(r'href="/wiki/(File:[^"#?]+)"', html)))

def category(name):
    h = get("https://commons.wikimedia.org/wiki/Category:" + urllib.parse.quote(name.replace(" ", "_")))
    subs = list(dict.fromkeys(H.unescape(urllib.parse.unquote(m)) for m in re.findall(r'href="/wiki/Category:([^"#?]+)"', h)))
    return files_in(h), subs

def search(q, n=100):
    h = get("https://commons.wikimedia.org/w/index.php?search=" + urllib.parse.quote(q) + f"&ns6=1&fulltext=1&limit={n}")
    return files_in(h)

def info(f):
    """licence short name, width x height, description, date, author of a File:"""
    t = f if f.startswith("File:") else "File:" + f
    h = get("https://commons.wikimedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")))
    lic = [re.sub("<[^>]+>", "", x).strip() for x in re.findall(r'class="licensetpl(?:_|&#95;)short[^"]*"[^>]*>(.*?)</span>', h)]
    sizes = [(int(a.replace(",", "")), int(b.replace(",", ""))) for a, b in re.findall(r'([\d,]+) (?:×|&times;|&#215;) ([\d,]+) pixels', h)]
    w, hh = max(sizes, key=lambda x: x[0] * x[1]) if sizes else (0, 0)
    desc = re.search(r'<td class="description">(.*?)</td>', h, re.S)
    date = re.search(r'>\s*Date\s*</td>\s*<td[^>]*>(.*?)</td>', h, re.S)
    auth = re.search(r'>\s*Author\s*</td>\s*<td[^>]*>(.*?)</td>', h, re.S)
    clean = lambda m: re.sub(r"\s+", " ", H.unescape(re.sub("<[^>]+>", " ", m.group(1)))).strip()[:300] if m else ""
    cats = [H.unescape(urllib.parse.unquote(c)) for c in re.findall(r'href="/wiki/Category:([^"#?]+)"', h)]
    return {"file": t[5:], "lic": list(dict.fromkeys(lic)), "w": w, "h": hh, "desc": clean(desc), "date": clean(date),
            "author": clean(auth), "cats": cats[:25]}

FREE = re.compile(r"public domain|^pd|cc0|cc[ -]by", re.I)
def free(i):
    return any(FREE.search(l) and not re.search(r"nc|nd", l, re.I) for l in i["lic"])

if __name__ == "__main__":
    cmd, arg = sys.argv[1], " ".join(sys.argv[2:])
    if cmd == "cat":
        fs, subs = category(arg); print("SUBS:", subs[:60]); print("\n".join(fs))
    elif cmd == "search":
        print("\n".join(search(arg)))
    elif cmd == "info":
        for f in arg.split("|"):
            i = info(f.strip()); print(json.dumps(i, ensure_ascii=False))
