"""Hold scheduled uploads: a private video with a publishAt stays private, its release time is removed
(Andrii, Nov 14: 'Зупини вихід шорт'). Nothing is deleted. Usage: python tools/yt_hold.py ID [ID ...]"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import shorts as S

FAR = "2028-01-01T00:00:00Z"                    # not a release: a parking date, moved/deleted only on his order
yt = S.youtube()
for vid in sys.argv[1:]:
    got = yt.videos().list(part="status,snippet", id=vid).execute().get("items") or []
    if not got:
        print(vid, "not found"); continue
    st = got[0]["status"]
    print(vid, "before:", st.get("privacyStatus"), st.get("publishAt"), "|", got[0]["snippet"]["title"])
    if st.get("privacyStatus") != "private":
        print(vid, "already", st.get("privacyStatus"), "- not touched"); continue
    keep = {k: st[k] for k in ("embeddable", "license", "publicStatsViewable", "selfDeclaredMadeForKids",
                                "containsSyntheticMedia") if k in st}
    for at in (None, FAR):                            # null clears the release time; if YouTube keeps it, push it far away
        yt.videos().update(part="status", body={"id": vid, "status": {**keep, "privacyStatus": "private",
                                                                       "publishAt": at}}).execute()
        st = yt.videos().list(part="status", id=vid).execute()["items"][0]["status"]
        print(vid, "after:", st.get("privacyStatus"), st.get("publishAt"))
        if not st.get("publishAt") or st["publishAt"].startswith(FAR[:4]):
            break
