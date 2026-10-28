# The daily scripts task (Andrii, Oct 26): 2 jurgen + 1 pastrak, London 06:39

Scheduled task 'Daily scripts: 2 jurgen + 1 pastrak' (trig_01Vnc25NdeRPHV3usBjxFMWr) wakes the persistent session
'Daily jurgen scripts (ww2-bot)' every day at 06:39 London. These are its instructions (they win over an older prompt).

Start clean: `git pull --rebase origin main`, re-read CLAUDE.md (STATUS, '## PASTRAK', READY STORIES, THE JURGENS
OPENINGS, COVERS) and tools/stories/README.md. Work carefully (maximum effort): every fact true to the source. Commit
everything to `main` before 12:00 London (the night slots start at 22:20). If time or limits run short, the PASTRAK
story comes first: the bot writes its own jurgen if none is ready, but it cannot write a pastrak (that slot then
becomes a classic Short).

## A) ONE pastrak story: stories/pastrak/NAME.json (made like stories/pastrak/cologne.json; copy its fields)
1. Topic: an armour story that fits PastTrack's skeleton (year + trap or need -> 'the answer was' -> ONE visible
   oddity -> 'But/However' before a third -> the fight or fate with a number -> a quiet ironic verdict -> the spoken
   debate question + 'Let me know in the comments'), ONE scene, not a career summary; German or extreme vehicles
   first (PastTrack: German median 80k views vs 36k). Not on the channel: stats.json titles, used.json,
   stories/pastrak/*.json and stories/*.json topics. It must have MOVING FILM of that vehicle or event: find the
   film FIRST (ia.py: Wochenschau episodes 'YYYY-MM-DD-Die-Deutsche-Wochenschau-NNN' are allowed by Andrii, their
   German description lists the subjects; US public-domain reels; Commons video; never the 'youtube-...' [ENG-SUB]
   re-uploads), then filmsheet.py contact sheets that you LOOK at. No good film -> another topic.
2. Facts only from the English Wikipedia article(s) (topic + sources; curl the page + wikitext.py), 14-22 sentences,
   170-280 words; `python3 tools/stories/pcheck.py story.json article.txt [source.txt]` -> hard [] and soft []; then
   re-read every sentence against the text by hand and soften anything stronger than the source.
   NUMBERS (Andrii's standard, Oct 27: 'too many figures within 10-15 seconds are hard to listen to; two in one
   sentence are fine'): at most 3 numbers in any ~12 s of speech (33 words; pcheck flags more; years, days of dates
   and names like T-34 do not count); keep figures for the punchlines, say the rest in plain words ('half', 'most
   of them', 'a small part') or spread them through the story; a list of figures becomes one plain sentence
   (Panther: '41 operational, 56 burned out, 85 repairable' -> 'By 20 July, most of them had burned out in battle
   or were waiting for repairs').
3. Shots: two per sentence longer than ~10 words (a cut every 2-3 s), mostly film (from-to seconds inside ONE scene;
   no title cards, burnt-in captions, logos, watermarks) plus free Commons photos (PD/CC0/CC BY/CC BY-SA; no modern,
   museum, AI-looking or graphic pictures); every shot shows exactly what its sentence says; an sfx per shot from
   sfx/ where it fits (tank_old, tank_engine_long, tank_gun, battle_explosion, explosion_massive, explosion_far,
   radio_static, tank_hatch; none on quiet shots); "punch": true on hazy grey film; "trim" for caption strips and
   borders; the film's "crop" from filmsheet.py; cover = the vehicle big at its most intense moment (a free Commons
   photo, never a museum piece) + label (vehicle name or 'X vs Y', max ~22 chars) + flags; priority = the next
   number in stories/pastrak.
4. `python3 tools/stories/shotscan.py stories/pastrak/NAME.json` and LOOK at /tmp/story_tools/shotscan.jpg (every
   film range at 2 frames a second): NO DEAD BODIES (Andrii, Oct 27: a body lay in a trench clip of the Panther story;
   zoom into anything lying on the ground), no scene change, title card or caption inside a range.
5. Test render: `python3 tools/stories/prender.py stories/pastrak/NAME.json article.txt [source.txt]`, LOOK at
   /tmp/story_tools/render_sheet.jpg, fix and render again until every shot is right. Never commit work/.

## B) TWO jurgen stories (as before)
Famous WW2 persons/events not on the channel, 25 sentences ~385-405 words, hand-picked free Commons pictures for
every sentence, `python3 tools/stories/jcheck.py stories/NAME.json article.txt` hard [] and soft [] against the full
article plus a sentence-by-sentence check by hand; priorities = the next numbers after the highest stories/*.json.
TITLE = THE FAMOUS NAME FIRST (Andrii, Oct 27; channel data: titles with the name, Bormann 3,278 / Rommel 1,737 /
Göring 1,209 views, beat 'The X Who...' titles without it, Hess 70 / Yamamoto 161 / Stauffenberg 283): sentence 1 and
the title start with the person's or ship's known name, e.g. 'Joseph Goebbels: chancellor of Germany for just one
day.', 'What happened to Heinrich Himmler after...'; then don't repeat the full name in sentence 2.
FILM OPENING (v2.04, Andrii, Oct 27: ~40% of the viewers leave in the first 15 s): give each jurgen story archive
film for its first 2-3 sentences, made like a pastrak story's: "films" {key: {url (the archive.org/download/...
file), crop (filmsheet.py), credit}} + "shots" [{sentence, film, from, to, sfx?, zoom?, x?, y?, punch?, fill?}]
(stories/goebbels.json is the example). Rules: 1-2 films per story (each is downloaded in the run); sentence 1 = 2
clips of 2-3 s that show its subject (the person speaking, the ship, the tank), sentences 2-3 one or two clips each
of exactly what they say (the place, the event); a clip may also replace a picture later where the film shows
exactly that sentence (Hitler in March 1945, Volkssturm training). "zoom" 1.2-1.6 + x/y (0-1) = a closer look at a
small figure (720x544 Wochenschau: not above 1.6); "sfx" only where the picture makes that sound (explosion_far,
distant_war, tank_engine_long, plane_flyby...; none on speeches and crowds). No dead bodies (shotscan.py, look
at every frame), no title cards or captions, no scenes from after the war. No good film of the subject -> leave
"films"/"shots" out: the story still works (photo opening). Check with jcheck.py (film fields: hard problems),
shotscan.py, and jrender.py (LOOK at render_sheet.jpg). The bot alternates film/photo between film-equipped stories
(A/B, stats j_style), so every film you add is used in every second one.

## C) Commit
The 3 stories + CLAUDE.md STATUS (the ready jurgen list and a ready pastrak list: name, priority, title, date) to
`main` (stories only, no version number), with the Co-Authored-By / Claude-Session lines; `git pull --rebase origin
main` right before the push.

## D) Report
To Andrii in Ukrainian (titles, priorities, number of pictures/clips, anything that worried you) and the same short
summary as a mobile push notification (PushNotification tool); if anything blocks you, push-notify him the exact
reason at once. Do not publish videos, run workflows, change the schedule or the bot's code.
