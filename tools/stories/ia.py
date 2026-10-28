"""Internet Archive for archive film (pastrak stories): search items, list an item's video files.
  python3 ia.py search "query" [rows]      e.g. 'identifier:1944-03* AND title:(wochenschau)', 'cologne panther'
  python3 ia.py files IDENTIFIER            video files (size, length, width x height) + description/licence
Wochenschau: ~1,083 items; use the 'YYYY-MM-DD-Die-Deutsche-Wochenschau-NNN' ones (720x544 .mkv/.mp4; their German
description lists the episode's subjects: search it for the vehicle, e.g. 'Panther', 'Tiger', 'Sturmgeschütz'),
NOT the 'youtube-...' [ENG-SUB] re-uploads (burnt-in subtitles, someone else's restoration). US film is public
domain (gov.archives.arc.*, ADC-*, Universal Newsreels, Signal Corps reels)."""
import json, sys, urllib.parse, urllib.request

UA = {"User-Agent": "Classified1945ShortsBot/1.0 (story research)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def search(q, rows=30):
    url = ("https://archive.org/advancedsearch.php?q=" + urllib.parse.quote(f"({q}) AND mediatype:movies")
           + "&fl[]=identifier&fl[]=title&fl[]=date&fl[]=downloads&sort[]=downloads+desc"
           + f"&rows={rows}&output=json")
    d = get(url)["response"]
    print("found", d["numFound"])
    for x in d["docs"]:
        print(f"{x['identifier']} | {str(x.get('title'))[:100]} | {str(x.get('date', ''))[:10]} | {x.get('downloads')}")


def files(ident):
    d = get("https://archive.org/metadata/" + ident)
    m = d.get("metadata", {})
    print("title:", m.get("title"))
    print("description:", str(m.get("description", ""))[:600].replace("\n", " "))
    print("licence:", m.get("licenseurl"), "| rights:", str(m.get("rights", ""))[:200])
    for f in d.get("files", []):
        if f["name"].lower().endswith((".mp4", ".mpeg4", ".ogv", ".mkv", ".avi", ".mov", ".webm", ".m4v")):
            print(f"  {f['name']} | {f.get('format')} | {int(f.get('size', 0)) / 1e6:.1f} MB | {f.get('length')} s"
                  f" | {f.get('width')}x{f.get('height')}")
    print("download URL: https://archive.org/download/" + ident + "/<file name>")


if __name__ == "__main__":
    if sys.argv[1] == "search":
        search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 30)
    else:
        files(sys.argv[2])
