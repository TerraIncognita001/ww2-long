"""Read-only channel numbers (Andrii, Nov 21: 'проаналізуй кількість показів на відео'): per video of stats.json
the YouTube Analytics totals (views, watch time, average % viewed, likes, shares, new subscribers), the traffic
sources and, when the API gives them, thumbnail impressions + click rate. Writes work/yt_stats.json and prints a
table. Runs in the 'stats' workflow (the OAuth keys live only in Secrets). Changes nothing on YouTube."""
import json, pathlib, sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import shorts as S                                        # noqa: E402
from googleapiclient.discovery import build              # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
stats = json.loads((ROOT / "stats.json").read_text(encoding="utf-8"))
vids = [v for v in stats["videos"] if v.get("id")]
creds = S.credentials()
yt = S.youtube(creds)
ya = build("youtubeAnalytics", "v2", credentials=creds)
start, end = min(v["date"] for v in vids), date.today().isoformat()
out = {}

for i in range(0, len(vids), 50):                          # public counters + privacy state
    for it in yt.videos().list(part="statistics,status", id=",".join(v["id"] for v in vids[i:i + 50])).execute()["items"]:
        out[it["id"]] = {"views": int(it["statistics"].get("viewCount", 0)),
                         "likes": int(it["statistics"].get("likeCount", 0)),
                         "privacy": it["status"]["privacyStatus"]}


def query(metrics, dims, vid, **kw):
    return ya.reports().query(ids="channel==MINE", startDate=start, endDate=end, metrics=metrics,
                              dimensions=dims, filters=f"video=={vid}", **kw).execute()


tried_imp = None
for v in vids:
    o = out.setdefault(v["id"], {})
    try:
        r = query("views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,shares,subscribersGained",
                  "video", v["id"])
        if r.get("rows"):
            o.update(dict(zip([h["name"] for h in r["columnHeaders"]][1:], r["rows"][0][1:])))
        r = query("views", "insightTrafficSourceType", v["id"], sort="-views")
        o["sources"] = {row[0]: row[1] for row in r.get("rows", [])}
    except Exception as e:
        o["error"] = str(e)[:160]
    if v.get("format") == "long":                          # retention curve: share of viewers left at each 1 % of the video
        try:
            r = query("audienceWatchRatio,relativeRetentionPerformance", "elapsedVideoTimeRatio", v["id"])
            o["curve"] = [[row[0], round(row[1], 3), round(row[2], 3)] for row in r.get("rows", [])]
        except Exception as e:
            o["curve_error"] = str(e)[:160]
    if tried_imp is not False:                            # impressions: not every API version has them
        try:
            r = query("videoThumbnailImpressions,videoThumbnailImpressionsClickRate", "video", v["id"])
            if r.get("rows"):
                o["impressions"], o["ctr"] = r["rows"][0][1], r["rows"][0][2]
            tried_imp = True
        except Exception as e:
            tried_imp = False
            print("impressions not in the Analytics API:", str(e)[:160])

(ROOT / "work").mkdir(exist_ok=True)
(ROOT / "work" / "yt_stats.json").write_text(json.dumps({v["id"]: {**out.get(v["id"], {}), "title": v["title"],
                                                         "format": v["format"], "date": v["date"]} for v in vids},
                                                        ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{'date':10} {'fmt':5} {'views':>6} {'apv%':>5} {'avgs':>5} {'subs':>4} {'imp':>6} {'ctr':>5}  sources | title")
for v in vids:
    o = out.get(v["id"], {})
    src = ", ".join(f"{k}:{n}" for k, n in sorted(o.get("sources", {}).items(), key=lambda x: -x[1])[:4])
    print(f"{v['date']:10} {v['format'][:5]:5} {o.get('views', '-'):>6} {round(o.get('averageViewPercentage') or 0):>5} "
          f"{round(o.get('averageViewDuration') or 0):>5} {o.get('subscribersGained', '-'):>4} "
          f"{o.get('impressions', '-'):>6} {o.get('ctr', '-'):>5}  {src} | {o.get('privacy', '')} {v['title'][:60]}"
          + (f" | {o['error']}" if o.get("error") else ""))
print("\nretention (share of viewers still watching at 5/10/20/30/50/75 % of the long videos; dur s):")
for v in vids:
    c = out.get(v["id"], {}).get("curve") or []
    if c:
        at = lambda x: next((round(100 * r[1]) for r in c if r[0] >= x), "-")
        print(f"{v['title'][:44]:44} " + " ".join(f"{at(x):>4}" for x in (0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75)))
