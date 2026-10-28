# CLAUDE.md — WW2 long videos (ww2-long)

Owner: Andrii (Ukrainian, short army-style answers, best free option). Reply in Ukrainian.
Base: the Shorts bot `ww2-bot` (Classified 1945), its CLAUDE.md is the source of every rule below.

## Decisions (Andrii, Oct 27)
- NEW YouTube channel (own `YT_REFRESH_TOKEN`), not Classified 1945.
- NEW PUBLIC repo `ww2-long` (unlimited Actions minutes; keys only in Secrets; no tokens in files).
- 10-15 min videos, 3 a week (Mon/Wed/Fri, ~1,800-2,300 words, 5-7 chapters).
- Style = MIX of jurgen + pastrak: the strongest moments of both (below).

## What we take from each format
| From | Kept |
|---|---|
| jurgen | ONE person / fate per video; title = known name first + fate/promise (named titles 1.2-3.3k vs unnamed 70-1.2k); opening = the title read aloud, 7-14 words; sentence 2 = date + place + person; re-hook every chapter; quiet closing fact; portrait + NAME when a person enters; Ken Burns on photos; dark drone music (music/jurgen), ducked, J_MUSIC_VOL 0.35, release 1.5 s; end question pinned (not a silent card) |
| pastrak | year + need/trap -> "the answer was X" -> ONE visible oddity -> "But" flaw before 1/3 -> fate with a number -> ironic verdict -> debate question; archive FILM (Wochenschau, Signal Corps, IA) with shot = exactly the words, cut every 2-4 s in action; SFX per shot (-27 LUFS, ducked) over low_rumble; cover = the vehicle big + flag + name plate |
| both | the film opening (v2.04: first ~15 s on moving film, not photos); numbers rule: max 3 numbers per ~12 s; no dead bodies (shotscan.py); no watermarks / modern / museum / NC-IWM; facts checked against the full Wikipedia text (numbers_ok, names_ok); retention_curves -> biggest drops -> lessons |

Per chapter the mix switches: people/decision chapters = jurgen pacing (photo 4-8 s, music); battle/machine
chapters = pastrak pacing (film 2-4 s, SFX up, music down). Story field `mode: "people" | "action"` per chapter.

## Long-form specifics (new code)
- 16:9 1920x1080, 30 fps; the archive picture fills the frame (pillarbox films: blurred copy behind).
- Structure: cold open 30-45 s (the most dramatic moment, film) -> title card -> chapters with on-screen chapter
  titles -> ending (fate + question). Chapter times go into the description = YouTube chapters (first 00:00).
- Retention beats: open loop in the first 30 s, payoff promised; re-hook at every chapter start; mid-roll-free.
- Maps: world-atlas land-10m.json (already in ww2-bot/map) -> animated route / front line, 1 per chapter max.
- Captions: NO burned karaoke (long viewers watch with sound) -> `.srt` uploaded as YouTube captions + 8 translated
  titles/descriptions. Lower-thirds for names and PLACE · DATE.
- Thumbnail 1280x720: the strongest frame (cover rule v1.89: biggest thing at the most intense moment, or the face),
  upscaled (esrgan), 2-4 words of big text + flag. A/B thumbnail later (YouTube "Test & compare" by hand).
- Voice: en-GB-RyanNeural +0% (~140 wpm -> 2,000 words ≈ 14 min); Azure fallback; Kokoro for sandbox renders.
- Sound: voice -16 LUFS dialog, music bed per chapter mode, SFX on film shots, final loudnorm -14 LUFS.
- Upload: categoryId 27 (Education), chapters in description, sources + licences credited, end screen
  (set by hand in Studio once), playlist per theatre, pinned question.

## Scripts
- Gemini free quota is used by the Shorts -> long scripts are READY STORIES written and fact-checked by Claude
  (scheduled task like 'Daily jurgen scripts': one long story every ~2 days), stories/long/*.json:
  topic, sources[], title, thumb{file, text, flags, x}, chapters[{title, mode, sentences[], shots[]}], films{},
  question, summary, tags, pronounce.
- Checks before render: facts against the full articles, max 3 numbers / ~12 s, a shot for every sentence,
  >= 1 different picture per 10 s, no bodies (shotscan sheet looked at by a person).

## BUILT (Oct 27, v0.01, not on GitHub yet)
- `longform.py` imports the Shorts bot's code as libraries (shorts.py = S, jurgen.py = J, pastrak.py = P, copied
  unchanged from ww2-bot v2.06): voice (S.speak + S.respell + pronounce.json, J.calm_pauses), Commons licence
  check (J.free_item), films (P.film_file), flags (P.flag), loudness (P.lufs), upload/captions/comment (S.*).
- Story file `stories/long/*.json`: topic, sources[], title, thumb{file, text[], flags, x, y}, question, summary,
  tags, pronounce, films{key: {url, crop, credit}}, chapters[{title ('' for the cold open), mode people|action,
  sentences[], shots[{s (sentence in the chapter, 1-based), file | film+from+to, x, y, zoom, punch, card (document
  shown whole), sfx, name+role (lower-third), label (PLACE · DATE, top left)}]}].
- Timeline: cold open (chapter 0) -> title card 4.5 s -> per chapter: card 3.2 s ('PART II' + title) + narration
  (one TTS file per chapter) -> outro 12 s (end screen). Photos 1.3-2.3:1 fill the frame (push-in 7% people / 10%
  action), others whole on a blurred copy; a photo held > 1.25 x SHOT_MAX (people 7.5 s, action 4 s) splits into two
  shots, the 2nd a closer crop; films fill 16:9, slowed <= 1.3x, then a closer look at the clip's end.
- Sound: chapter voices + a jurgen drone per chapter (-29 LUFS people / -33 action) + sfx per shot (-27 / -31) +
  low_rumble under action chapters, all ducked under the voice (sidechain, release 1.5 s), loudnorm -14 LUFS.
- Outputs (work/): final.mp4, cover.png (1280x720 thumbnail: dark fade, Bebas Neue words, flag), captions.srt
  (sentence cues), metadata.json (title, description with YouTube chapters, sources, credits, categoryId 27).
- `python longform.py check story.json sources/*.txt` = facts hard against the FULL articles (numbers_ok, names_ok,
  OVERCLAIM), shots, numbers per ~12 s. In the run the facts are soft (S.wiki_text stops at 20,000 characters).
- Workflow `.github/workflows/long.yml`: cron Mon/Wed/Fri 15:05 UTC (PROPOSAL, ask Andrii), manual dry_run ->
  artifact 'long-video' (final.mp4 is ~400-700 MB: too big for a branch), publish_run=<run id> uploads that exact
  video (L_PUBLISH=1), film cache, state commit (used.json, stats.json).
- First story: indianapolis (priority 1): 9 chapters, 113 sentences, ~1,660 words, ~11 min; facts from USS
  Indianapolis (CA-35), Charles B. McVay III, Mochitsura Hashimoto (check: 0 problems); films NARA NPC-8708
  (Indianapolis at Iwo Jima 1945, Nimitz aboard) and NPC-4888 (Guam/Tinian bombardment; burnt-in timecode at the
  bottom -> crop 996:560:142:0); ~45 Commons pictures (PD, one CC BY 2.0 BUMED photo credited).
- Story-level `trims` {file: [l,t,r,b]} and `whole` [files never cropped]. Charles_B_McVay_III_portrait.jpg (the
  only McVay photo on Commons) carries a 'gettyimages / Bettmann' mark at ~64% height: trimmed 42% from the bottom
  and shown whole. Check every portrait for agency marks at full size.
- LESSONS from the first render (Oct 28): pick film seconds from 1-SECOND sheets (5 s sheets put the cold open on
  empty sky); NPC-4888's good moments are short (turret 351-354.5, explosion 71-76.5, 438-444, cloud 445-450.5);
  NPC-16243 (PBY patrol, 720p PD) = radioman 120-150, plotting 185-215, pilot 250-300, men on the wing 352-366
  (its crash/fire part after 430 s is NOT used); don't reuse one clip more than ~3 times (the storm clip was 10x).
- Render on Andrii's PC: 10.7 min video in ~3-4 min (ultrafast shots, veryfast final), 214 MB, -14.1 LUFS.
- Local Windows test: ffmpeg 9 (-/filter_complex instead of -filter_complex_script: picked by version), Edge TTS
  works here (Oct 27), fonts/BebasNeue-Regular.ttf (OFL).

## THE THUMBNAIL STANDARD (Andrii, Oct 28: 'all thumbnails in this style') - HARD RULE
Every video's thumbnail = the house CASE FILE (thumbs.py HOUSE / house_case, the approved Indianapolis cover):
manila 1945 paper, typed label strip top left ('<SUBJECT> - <MONTH YEAR>', <= 32 chars), three pinned polaroids
joined by red string - LEFT the machine or place, CENTRE the main person (biggest, the rubber stamp across him),
RIGHT the other side of the story - marker captions under each; ONE stamp word that is a fact of the story
(GUILTY, SUNK, EXECUTED, MISSING, SURRENDERED...). Story field:
  "case": {"label", "left": {file, caption, trim?, color?, x_crop?, y_crop?}, "center": {...}, "right": {...},
           "stamp": "GUILTY", "variants": [<= 2 overrides for Test & compare, same layout: notes (marker words),
           circles, arrows, strikes, stamp]}
check() blocks a story without left/center/right pictures. cover.png = the case; cover_2/cover_3 = the variants.
Indianapolis variants: 'EXONERATED 2000' over the struck-out GUILTY; I-58 circled 'NO WARNING'. Portraits that
DDColor can't colour get color 'tone'. Older styles (circle/arrow, tag, split, glow, mystery, headline) stay in
thumbs.py and the story's `thumbs_more`, not used.

## THUMBNAILS (research Oct 28: top 12 + 4 weakest long videos of 10 WW2 channels, yt-dlp lists + i.ytimg.com)
Channels: Mark Felton 2.4M subs (top 10M), Yarnhub 3.4M (33M), Simple History 5.1M, The Operations Room 1.45M
(14M), Dark Docs 1.2M (9.1M), Baz Battles 725k, History Hustle 313k, Kings and Generals, The History Guy, WW2TV.
- Hits are COLOUR: colorized archive photos (Felton, History Hustle, Dark Docs), 3D renders (Yarnhub), cartoons
  (Simple History). Grey = weak: Baz Battles' grey 'INDIANAPOLIS' got 90k vs 2-10M for its others.
- ONE clear subject, big: a face close up looking out (Himmler, Hitler, Goebbels), a group of faces with emotion
  (Soviet women POWs 10M, German POWs 2.6M), or the machine in action (Yarnhub: one plane/ship/tank, fire, smoke).
- Almost NO text: Felton, Dark Docs, Yarnhub, Simple History none; History Hustle a 2-4 word tag on a box; The
  Operations Room / Baz Battles the battle NAME only (their brand: maps). Never a sentence; the title says it.
- Felton's split: person | person (King | Saddam) or person | object (Heydrich | his dagger), thin seam.
- Dark Docs: red circle + fat red arrow on the one detail (the face, the burning tank, the man in the field).
- Weak ones: obscure objects (Felton's swords/medals 67-124k), busy compositions, grey.
- BUILT: story `thumbs` (max 3 = YouTube Studio 'Test & compare'): panels [{file, x, y, zoom, trim, color: true |
  'tone' | false, contrast, saturation}], widths, circle [cx, cy, rx, ry], arrow [x1, y1, x2, y2] (0-1 of 1280x720),
  tag (red box), flags. Pictures colorized (DDColor; when it gives up: S.warm_tone), upscaled (Real-ESRGAN),
  graded vivid (contrast 1.15, saturation 1.3), vignette. The bot uploads cover.png; cover_2/cover_3 go into the
  Studio test by hand (no public API for it). `python longform.py thumbs story.json` = only the thumbnails.
- Indianapolis: 1 survivors colorized + red circle/arrow (the strongest), 2 the ship colorized + 'NOBODY CAME' tag +
  US flag, 3 McVay | Hashimoto split (warm tone: DDColor gave McVay no colour and washed out the 303 px Hashimoto).
  `portrait: true` in colorize crops to the face when DDColor fails: don't use it for split panels.

## CLICKBAIT (research Oct 28: 11 channels outside the WW2 niche where clickbait works best)
Fern 5.6M (top 20M), MrBallen 11.3M (24M), JCS 5.6M (67M), The Infographics Show 15.5M, Magnates Media 1.9M (12M),
Barely Sociable 1.4M (13M), Wendigoon, OverSimplified, The Armchair Historian 2.5M (8.4M, WW2), History Scope.
- Fern: case board (corkboard, pinned photos, red strings, agency seals, red 'WANTED' stamp); rim-lit portrait with
  the antagonist dark behind + a question on a red box ('WORSE THAN HITLER?' 11M); one object + its NAME ('TSAR
  BOMBA', 'UNABOMBER'); red circle + red words ('CARTEL BOSS'). Weak: 'THEN/NOW', 'WHY?' + object.
- MrBallen: his reaction face + fat red arrows at the anomaly, CCTV/VHS frames (REC, timestamp). Weak: cute titles.
- Infographics: 2-3 words of STAKES on top ('NO ESCAPE', '23,000 FEET DOWN', 'TOTAL COLLAPSE'), a frightened face.
  Weak: episode-like labels ('OPTION #3', 'DAY #412', 'NIGHT #99').
- Magnates: hyper-saturated, fire/money/blood, 'DARK TRUTH'. Barely Sociable: near-black, ONE object, a handwritten
  question ('WHO IS HE?'); its weak ones are generic icons.
- Data (associations, not causes): Eden (507k videos): text on 86.6% of breakout thumbnails, text-free 25% more
  common among underperformers; a study of 1,043 channels: channels > 2M subs go text-free on 32% (smallest band
  19%) and use arrows less (9% vs 15%) - big channels can skip text, a new channel should not; vidIQ (500
  breakouts): faces on 69% of all, 80% of the top 50. YouTube's Test & compare picks the WINNER BY WATCH TIME
  SHARE, not CTR: a promise the video doesn't keep loses -> every word/stamp must be a fact of the story.
- NEW (none of the WW2 channels does these): `thumbs.py` styles case (Fern board on a 1945 manila file, polaroids,
  pins, strings, rubber stamp), glow (U2-Net-p cut-out, ~4.6 MB, red rim light, the other side huge and dark, red
  box question), mystery (pool of light on black, Permanent Marker question), headline (Infographics stakes, one
  key word on red). Fonts: Bebas Neue (OFL), Permanent Marker + Special Elite (Apache-2.0) in fonts/.
- Indianapolis Test & compare set (story `thumbs`): 1 '4 DAYS ADRIFT' over the colorized survivors, 2 McVay rim-lit
  + Hashimoto in the dark + 'SCAPEGOAT?', 3 case file with 'GUILTY' (true: convicted Nov 1945). `thumbs_more` keeps
  the earlier circle/arrow, ship+tag, split and the mystery one. `python longform.py thumbs story.json` renders all
  (cover.png ... cover_7.png).
- CASE variants (Oct 28, Andrii liked the case board): `board` manila | cork | desk (night lamp), `notes`
  (Permanent Marker, red, rotated), `circles` (hand-drawn), `arrows` (curved marker), `strikes`, `headline`.
  Story list `thumbs_case`: 1 cork, 2 GUILTY struck out + 'EXONERATED 2000', 3 night desk + Hashimoto circled 'NO
  WARNING', 4 web of blame (ship, the Navy, I-58, survivors -> McVay) + 'WHO WAS TO BLAME?', 5 'HE TESTIFIED'
  (Hashimoto at the court-martial). All facts of the story. `python longform.py thumbs story.json thumbs_case`.
- Ideas not built yet: the channel host's reaction face (MrBallen; we have no host), CCTV/REC framing for archive
  film stills, a recurring brand element (Fern's board is recognisable at a glance: our 1945 file could be ours).

## Plan
1. Repo skeleton: copy shared helpers from ww2-bot (voice, respell, Commons/IA download, dHash, upscale, upload,
   stats, retention) into `common.py`; `longform.py` = story -> 16:9 video; music/, sfx/, map/ copied.
2. First story by hand (a topic that is a hit as a Short already: Indianapolis 25k, Bormann, Göring) -> sandbox
   render with Kokoro -> Andrii watches.
3. Workflow `long.yml`: cron 3x/week, dry_run -> preview branch (video > 100 MB -> Actions artifact instead),
   publish_preview, stats_only.
4. New channel OAuth (`auth.py`, Andrii runs once), secrets in ww2-long.
5. Daily story task + retention learning after ~10 videos.
