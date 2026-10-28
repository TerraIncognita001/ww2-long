"""Merges this run's state files into the newest ones on the branch (v1.84). Two runs that overlap (a manual run
and a late scheduled one, Oct 23: run #169) both append to used.json/stats.json; a git rebase then stops on a
conflict and the second video was never recorded. Here the union is kept: used topics, videos by id, metrics,
music plays and picture verdicts. Usage: python merge_state.py <dir with this run's files> (in the checkout)."""
import json
import pathlib
import sys

OURS = pathlib.Path(sys.argv[1])


def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def union(theirs, ours):
    return list(theirs) + [x for x in ours if x not in theirs]


def merge(name, theirs, ours):
    if theirs is None or ours is None:
        return ours if ours is not None else theirs
    if name == "used.json":
        return union(theirs, ours)
    if name == "stats.json":
        out = {**theirs, **ours}
        ids = {v.get("id"): v for v in ours.get("videos", [])}
        seen = {v.get("id") for v in theirs.get("videos", [])}
        out["videos"] = [{**v, **ids.get(v.get("id"), {})} for v in theirs.get("videos", [])] + \
            [v for v in ours.get("videos", []) if v.get("id") not in seen]
        out["metrics"] = {**theirs.get("metrics", {}), **ours.get("metrics", {})}
        out["recent"] = union(theirs.get("recent", []), ours.get("recent", []))[-60:]
        rt, ro = theirs.get("replies") or {}, ours.get("replies") or {}
        if isinstance(rt, dict) and isinstance(ro, dict):
            out["replies"] = {**rt, **ro, "done": union(rt.get("done", []), ro.get("done", []))[-300:]}
        return out
    if isinstance(theirs, dict) and isinstance(ours, dict):      # safety.json, music/tracks.json
        return {**theirs, **ours}
    return ours


for p in OURS.rglob("*.json"):
    name = str(p.relative_to(OURS))
    target = pathlib.Path(name)
    merged = merge(name, load(target) if target.exists() else None, load(p))
    if merged is not None:
        target.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
        print("merged", name)
