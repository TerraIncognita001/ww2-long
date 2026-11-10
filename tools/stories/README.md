# Tools for hand-made long stories (stories/long/*.json; not part of the bot)

Wikipedia/Commons give 429 to the sandbox API, so everything goes through HTML pages. Caches live in /tmp/story_tools.

- `python3 wikitext.py Page.html` -> plain article text (close to what the bot checks against).
  Get the page with: `curl -sS -A "$UA" -o Page.html https://en.wikipedia.org/wiki/Title`
- `python3 commons.py cat "Category name"` / `search "query"` / `info "File_a.jpg|File_b.jpg"` (licence, size, date).
- `python3 commons.py search "query" | python3 batch.py` -> FREE/no, size, licence, date, description per file.
- `python3 sheet.py list.txt sheet.png` -> numbered contact sheet (thumbnails via commons.wikimedia.org/w/thumb.php).
- `python3 ia.py search "query"` / `ia.py files IDENTIFIER` -> Internet Archive film items and their video files.
- `python3 filmsheet.py URL_or_file [every_s] [from_s] [to_s]` -> picture area (the film's "crop"), scene cuts and
  time-stamped contact sheets in /tmp/story_tools/films/ that you LOOK at; then a 1-SECOND sheet of the parts you
  want. Use the small copy for sheets, the HD/biggest file as the story's film url (same timeline).
- `python3 shotscan.py story.json` -> every film range at 2 frames a second on /tmp/story_tools/shotscan.jpg: LOOK
  for dead bodies (zoom into anything lying on the ground), scene changes, title cards, captions.
- Facts and shots: `python longform.py check story.json sources/*.txt` (in the repo root).
