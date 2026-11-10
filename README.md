# ww2-long

WW2 long-form documentaries (10-15 min, 16:9), built from the Classified 1945 Shorts bot. See CLAUDE.md.

- `longform.py` - story -> video, thumbnail, captions, upload (`python longform.py check|thumbs story.json`)
- `autostory.py` - the bot writes its own story when the queue is empty; `thumbs.py` - case-file thumbnails
- `stories/long/` - the stories; `used.json`, `stats.json` - state; `pronounce.json` - names for the voice
- `lib/` - shorts.py, jurgen.py, pastrak.py from ww2-bot, used as libraries (voice, films, sound, upload)
- `tools/` - auth_secrets.py (YouTube login -> GitHub secrets), stories/ (tools for writing stories)
- `fonts/`, `map/` - assets; `docs/` - privacy/terms pages (GitHub Pages); music/ and sfx/ come from the private ww2-bot in the workflow