# Tools for hand-made jurgen and pastrak stories (not part of the bot)

Used to write `stories/*.json` (Wikipedia/Commons give 429 to the sandbox API, so everything goes through HTML pages).
Caches live in /tmp/story_tools.

- `python3 wikitext.py Page.html` -> plain article text (close to what the bot checks against).
  Get the page with: `curl -sS -A "$UA" -o Page.html https://en.wikipedia.org/wiki/Title`
- `python3 commons.py cat "Category name"` / `search "query"` / `info "File_a.jpg|File_b.jpg"` (licence, size, date).
- `python3 commons.py search "query" | python3 batch.py` -> FREE/no, size, licence, date, description per file.
- `python3 sheet.py list.txt sheet.png` -> numbered contact sheet (thumbnails via commons.wikimedia.org/w/thumb.php).
- `python3 jcheck.py story.json article.txt` -> jurgen.check() hard/soft problems against the full text and the bot's
  first 20,000 characters, labels kept, word count, sentences without a picture.

## PASTRAK stories (stories/pastrak/*.json; format and rules: CLAUDE.md '## PASTRAK', example: cologne.json)
- `python3 ia.py search "query"` / `ia.py files IDENTIFIER` -> Internet Archive film items and their video files.
- `python3 filmsheet.py URL_or_file [every_s] [from_s] [to_s]` -> picture area (the film's "crop"), scene cuts and
  time-stamped contact sheets in /tmp/story_tools/films/ that you LOOK at; then a finer sheet (every 1 s) of the
  parts you want. Use the small copy for sheets, the HD/biggest file as the story's film url (same timeline).
- `python3 pcheck.py story.json article.txt [source.txt ...]` -> facts hard against the full articles, words,
  shots per sentence (warns at > 10 words per shot: PastTrack cuts every 2-3 s), film ranges; soft: more than 3
  numbers within ~12 s of speech (33 words; Andrii's standard: figures only for the punchlines, or spread them).
- `python3 shotscan.py story.json` -> every film range at 2 frames a second on /tmp/story_tools/shotscan.jpg: LOOK
  for dead bodies (zoom into anything lying on the ground), scene changes, title cards, captions.
- `python3 prender.py story.json article.txt [source.txt ...]` -> a test render (Kokoro voice, nothing uploaded):
  work/final.mp4 + /tmp/story_tools/render_sheet.jpg (a frame every 2 s) and the shot list. LOOK at the sheet:
  every shot must show what its sentence says, no title cards/captions/logos from the film, no hazy grey shots
  (use "punch": true or another clip), the cover plate readable.
- `python3 jrender.py stories/x.json article.txt [film|photo]` -> the same for a JURGEN story (v2.04): its pictures
  via thumb.php, its "films" + film "shots" (style film) or none (photo); work/final.mp4, work/thumb_clean.png,
  /tmp/story_tools/render_sheet.jpg (a frame every 3 s) and the shot list. shotscan.py works on jurgen stories too.
