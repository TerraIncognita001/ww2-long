"""Change the release queue on YouTube (Andrii, Nov 23: 'видали відео про атомну бомбу з черги і запости нове вже
сьогодні'). NOTHING IS DELETED and nothing already public is touched: only PRIVATE videos with a release time.
  python tools/yt_move.py ID=2026-11-24T00:00:00Z ...   -> the private video is released at that UTC time
  python tools/yt_move.py show:ID ...                    -> only prints its status and release time
  python tools/yt_move.py hold:ID ...                    -> the release time is removed, the video stays private
stats.json follows (release / publish_at / comment_due), so the cron and the pinned question see the new queue."""
import json, pathlib, subprocess, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import shorts as S

STATS = ROOT / "stats.json"
yt = S.youtube()
stats = json.loads(STATS.read_text(encoding="utf-8"))
held = []
for arg in sys.argv[1:]:
    hold = arg.startswith("hold:")
    vid, _, at = (arg[5:], "", "") if hold else (arg[5:], "", "") if arg.startswith("show:") else arg.partition("=")
    got = yt.videos().list(part="status,snippet", id=vid).execute().get("items") or []
    if not got:
        print(vid, "not found"); continue
    st = got[0]["status"]
    print(vid, "before:", st.get("privacyStatus"), st.get("publishAt"), "|", got[0]["snippet"]["title"])
    if st.get("privacyStatus") != "private":
        print(vid, "is", st.get("privacyStatus"), "- not touched"); continue
    if hold:
        held.append(vid)
        continue
    keep = {k: st[k] for k in ("embeddable", "license", "publicStatsViewable", "selfDeclaredMadeForKids",
                                "containsSyntheticMedia") if k in st}
    if not at:                                    # show:ID = read only
        continue
    r = yt.videos().update(part="status", body={"id": vid, "status": {**keep, "privacyStatus": "private",
                                                                       "publishAt": at}}).execute()
    print(vid, "update answered:", r["status"].get("privacyStatus"), r["status"].get("publishAt"))
    time.sleep(8)                                 # the list right after an update can still show the old time
    st = yt.videos().list(part="status", id=vid).execute()["items"][0]["status"]
    print(vid, "after:", st.get("privacyStatus"), st.get("publishAt"))
    for v in stats.get("videos", []):
        if v.get("id") == vid:
            for k in ("release", "publish_at"):
                if k in v:
                    v[k] = at
            if v.get("comment_due"):
                v["comment_due"]["at"] = at
if held:                                          # tools/yt_hold.py: null clears the time, else parked on 2028
    subprocess.run([sys.executable, str(ROOT / "tools" / "yt_hold.py"), *held], check=True)
    for v in stats.get("videos", []):
        if v.get("id") in held:
            v.pop("release", None); v.pop("publish_at", None); v.pop("comment_due", None)
            v["held"] = "Andrii, Nov 23: taken out of the queue (private, not deleted)"
STATS.write_text(json.dumps(stats, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
