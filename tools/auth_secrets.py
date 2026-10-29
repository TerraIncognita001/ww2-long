"""One-time YouTube login for the long-video channel -> GitHub Actions secrets, without printing the token.
Run from the repo root: .venv\\Scripts\\python tools\\auth_secrets.py
Needs client_secret.json (Google Cloud project ww2-long, OAuth client 'Desktop app') and a logged-in gh CLI.
On Google's screen pick the NEW channel (brand account); if it says 'Google hasn't verified this app':
Advanced -> Go to ww2-long (unsafe)."""
import shutil, subprocess, sys

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

REPO = "TerraIncognita001/ww2-long"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl",        # comments, playlists, captions, own stats
          "https://www.googleapis.com/auth/yt-analytics.readonly"]   # retention curves

gh = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
c = flow.run_local_server(port=0, access_type="offline", prompt="consent")
if not c.refresh_token:
    sys.exit("No refresh token came back: run again and accept every permission.")
me = build("youtube", "v3", credentials=c).channels().list(part="snippet,statistics", mine=True).execute()
items = me.get("items") or []
if not items:
    sys.exit("This Google account has no YouTube channel selected: run again and pick the channel.")
ch = items[0]
print(f"\nChannel: {ch['snippet']['title']}  (id {ch['id']}, {ch['statistics'].get('subscriberCount', '?')} subs)")
if input("Save this channel's login as the ww2-long secrets? [y/N] ").strip().lower() not in ("y", "yes", "т", "так"):
    sys.exit("Nothing saved.")
values = {"YT_CLIENT_ID": c.client_id, "YT_CLIENT_SECRET": c.client_secret, "YT_REFRESH_TOKEN": c.refresh_token}
ok = subprocess.run([gh, "auth", "status"], capture_output=True).returncode == 0
if ok:
    for name, value in values.items():
        subprocess.run([gh, "secret", "set", name, "-R", REPO], input=value, text=True, check=True,
                       stdout=subprocess.DEVNULL)
        print("saved", name)
    print("Done. The token itself was never printed.")
else:                                                  # gh not logged in here: hand the values over in a file
    import json, pathlib                               # inside work/ (git-ignored), set + deleted by the caller
    out = pathlib.Path("work/yt_login.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({**values, "channel": ch["snippet"]["title"]}), encoding="utf-8")
    print(f"gh is not logged in in this terminal: saved to {out} for the secrets step (delete it afterwards).")
