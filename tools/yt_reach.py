"""Thumbnail impressions + click rate per video (Andrii, Nov 21: 'підключай Reporting API'). The Analytics API has
no impressions, the YouTube Reporting API has them in the daily 'channel_reach_basic_a1' bulk reports. The first run
creates the reporting job (once, kept on the channel; YouTube then also writes ~30 days of history, first files in
~1-2 days); every run downloads the files there are and sums them per video -> work/yt_reach.json + a table.
Read-only otherwise. Runs in the 'stats' workflow (keys only in Secrets)."""
import csv, io, json, pathlib, sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import shorts as S                                        # noqa: E402
from googleapiclient.discovery import build              # noqa: E402
from google.auth.transport.requests import Request      # noqa: E402
import requests                                          # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
TYPE = "channel_reach_basic_a1"
creds = S.credentials()
yr = build("youtubereporting", "v1", credentials=creds)

jobs = [j for j in yr.jobs().list().execute().get("jobs", []) if j["reportTypeId"] == TYPE]
if not jobs:
    types = [t["id"] for t in yr.reportTypes().list().execute().get("reportTypes", [])]
    if TYPE not in types:
        sys.exit(f"{TYPE} is not offered to this channel; report types: {', '.join(types)}")
    job = yr.jobs().create(body={"reportTypeId": TYPE, "name": "ww2-long reach"}).execute()
    print("reporting job created:", job["id"], "- YouTube writes the first files in ~1-2 days (with ~30 days of history)")
    sys.exit(0)
job = jobs[0]
reports = []
req = yr.jobs().reports().list(jobId=job["id"])
while req is not None:
    res = req.execute()
    reports += res.get("reports", [])
    req = yr.jobs().reports().list_next(req, res)
print(f"job {job['id']}: {len(reports)} daily report files")
if not reports:
    sys.exit(0)

creds.refresh(Request())
imp, clicks, days = defaultdict(float), defaultdict(float), defaultdict(set)
for rep in reports:                                    # each file = one day, CSV, at its own download URL
    r = requests.get(rep["downloadUrl"], headers={"Authorization": "Bearer " + creds.token}, timeout=120)
    r.raise_for_status()
    for row in csv.DictReader(io.StringIO(r.content.decode("utf-8"))):
        n = float(row.get("video_thumbnail_impressions") or 0)
        vid = row.get("video_id")
        imp[vid] += n
        clicks[vid] += n * float(row.get("video_thumbnail_impressions_ctr") or 0)
        days[vid].add(row.get("date"))

stats = json.loads((ROOT / "stats.json").read_text(encoding="utf-8"))
names = {v["id"]: v for v in stats["videos"] if v.get("id")}
out = {v: {"impressions": int(imp[v]), "ctr": round(100 * clicks[v] / imp[v], 2) if imp[v] else None,
           "days": len(days[v]), "title": names.get(v, {}).get("title"), "format": names.get(v, {}).get("format")}
       for v in imp}
(ROOT / "work").mkdir(exist_ok=True)
(ROOT / "work" / "yt_reach.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{'fmt':5} {'impressions':>11} {'ctr%':>6} {'days':>4}  title")
for v, o in sorted(out.items(), key=lambda x: (x[1]["format"] or "~", -x[1]["impressions"])):
    print(f"{(o['format'] or '?')[:5]:5} {o['impressions']:>11} {o['ctr'] if o['ctr'] is not None else '-':>6} "
          f"{o['days']:>4}  {(o['title'] or v)[:70]}")
