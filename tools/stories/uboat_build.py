"""Hitler's U-boats, Nov 23 (Andrii: 'так, пиши, роендери і випускай щойно готове'): the first hand story in the NEW
FORMAT (CLAUDE.md, Nov 23): voice No. 3 ('andrii', voice pack), the narrator at ~3 s, President Roosevelt's 'rattlesnakes
of the Atlantic' as a beat right after sentence 1, one open question (why does Dönitz call the boats home two months
after his best month?), short wordless parts, names and notes in the stamp look, 2 cliff teasers.
Facts: Wikipedia 'Battle of the Atlantic', 'U-boat', 'Karl Dönitz', 'Günther Prien', 'German submarine U-47 (1938)',
'Second Happy Time', 'Wolfpack (naval tactic)', 'Black May (1943)', 'Laconia incident', 'USS Greer',
'German submarine U-505' (whole, sources/*.txt).
Films (public domain, NARA / Universal Newsreel via Internet Archive): 428-NPC-16081 'North Atlantic Convoy' (1942),
NPC-1849b 'Aerial Views of Convoy' (1943), NPC-2667 'Firing Depth Charges' (1944), NPC-15381 'Planes Bomb Sub Off East
Coast' (1943), NPC-1832 'Blimp Patrol Over Convoy', Universal Newsreel 'U-Boat Menace Ended' (17 May 1945). The NARA
transfers carry a burnt-in timecode at the bottom: cropped away. NOT used: the Commons R. P. Resor film (a stock
company's 'Buyout Footage' mark = Content ID risk).
Speech: FDR, Fireside Chat on Freedom of the Seas, 11 September 1941 (NARA 2192567, public domain, Internet Archive).
Run: python tools/stories/uboat_build.py"""
import json, pathlib

DONITZ = "Karl Dönitz.jpg"
DONITZ2 = "Bundesarchiv Bild 146-1976-127-06A, Karl Dönitz (cropped).jpg"
DONITZ3 = "Nazi Personalities- Grossadmiral Karl Doenitz (1891-1984) A14899.jpg"
PRIEN = "Bundesarchiv Bild 183-2006-1130-500, Kapitänleutnant Günther Prien.jpg"
U47 = "German submarine U-47, in 1939-1940 (NH 102539).jpg"
ROYAL_OAK = "HMS Royal Oak (08).jpg"
ATHENIA = "Sinking of Ss Athenia, September 1939 HU51008.jpg"
ATHENIA2 = "Sinking of Ss Athenia, 1939 HU51009.jpg"
COURAGEOUS = "HMS Courageous sinking.jpg"
KRETSCHMER = "Bundesarchiv Bild 183-L22207, Kapitänleutnant Otto Kretschmer.jpg"
U99 = "Bundesarchiv Bild 101II-MW-0951-24A, Kapitänleutnant Otto Kretschmer, Besatzung-U 99.jpg"
U110 = "U-110 and HMS Bulldog.jpg"
ENIGMA = 'Bundesarchiv Bild 101II-MW-4222-01A, "Enigma" auf U-Boot U-124.jpg'
BOMBE = "Wartime picture of a Bletchley Park Bombe.jpg"
BUNKER = "Bundesarchiv Bild 101II-MW-3936-08A, Frankreich, Lorient, U-Bootbunker im Bau.jpg"
U37 = "Bundesarchiv Bild 101II-MW-1032-11A, Lorient, U-37.jpg"
U31 = "Bundesarchiv Bild 101II-MW-1031-28, Lorient, U-31.jpg"
U123 = "Bundesarchiv Bild 101II-MW-3983-23, Lorient, Einlaufen von U-123.jpg"
RESOR = "R. P. Resor burning.jpg"
RESOR2 = "Wrecked R. P. Resor rear view.jpg"
OTTAWA = "HMCS Ottawa H60 River class destroyer North Atlantic convoy escort sunk by U91 14 Sep 1942.jpg"
FURY = "On Board the Destroyer HMS Fury Off Iceland, 1942. A8087.jpg"
LIBERATOR = "Consolidated B-24 Liberator - Royal Air Force Coastal Command in the Azores, 1943-1945. CA99.jpg"
U266 = "German aubmarine U-266 under attack in the Bay of Biscay, 15 March 1943 (C 3575).jpg"
U243 = "German submarine U-243 under attack by RAAF Sunderland aircraft in the Bay of Biscay, 8 July 1944 (C4603).jpg"
U534 = "U 534 under attack 5 May 1945.jpg"
U387 = "German submarine U-387 underway in the Atlantic Ocean on 20 October 1943 (80-G-207651).jpg"
U505 = "Captured German submarine U-505 lies near USS Guadalcanal (CVE-60) on 4 June 1944 (80-G-49170).jpg"
U505_SALV = ("U.S. Navy salvage crew working to save the captured German submarine U-505, 4 June 1944 "
             "(80-G-324313).jpg")
GALLERY = ("Captain Daniel V. Gallery, USN, on the bridge of the captured German submarine U-505 on 4 June 1944 "
           "(80-G-49176).jpg")
KING = "Ernest King.jpg"
CHURCHILL_LIV = ("Winston Churchill addressing merchant ships' crews and dockers at Liverpool, April 1941. "
                 "H9155.jpg")
FDR = "FDR 1944 Color Portrait.jpg"
GREER = "USS Greer;0514502.jpg"
LACONIA = "RMS Laconia.jpg"
SURRENDER = ("WW2 German Navy U-boat submarines (Kriegsmarine Unterseeboote U-boote) etc wartime contemporary photo "
             "U-BOAT SURRENDER LISAHALLY 1945 (1).jpg")

FDR_SRC = "PRESIDENT ROOSEVELT · FIRESIDE CHAT, 11 SEPTEMBER 1941"

M_DRUM = {"places": [{"label": "LORIENT", "lat": 47.75, "lon": -3.37},
                     {"label": "NEW YORK", "lat": 40.7, "lon": -74.0, "side": "blue"}],
          "routes": [[0, 1, "red", 0.2]], "pad": 0.25}
M_GAP = {"places": [{"label": "NEWFOUNDLAND", "lat": 47.6, "lon": -52.7, "side": "blue"},
                    {"label": "ICELAND", "lat": 64.1, "lon": -21.9, "side": "blue"},
                    {"label": "NORTHERN IRELAND", "lat": 54.6, "lon": -5.9, "side": "blue"},
                    {"label": "AIR GAP", "lat": 56.0, "lon": -35.0}],
         "routes": [[0, 2, "blue", 0.15]], "pad": 0.3}

C = [
 {"title": "", "mode": "action", "sentences": [
  "In the early hours of 14 January 1942, a U-boat sinks a tanker within sight of Long Island.",
  "In this war, 3,500 merchant ships and 175 warships go down in the Atlantic.",
  "The man who sends the U-boats out is Admiral Karl Dönitz.",
  "In March 1943, his boats come closer than ever to cutting Britain off from America, yet two months later, he calls them home.",
  "It begins on the first day of the war."],
  "shots": [
   {"s": 1, "film": "convoy42", "from": 184, "to": 190, "stamp": ["LONG ISLAND"]},
   {"s": 2, "file": RESOR, "note": "3,500 SHIPS"},
   {"s": 3, "file": DONITZ, "reveal": [0.72, 0.26], "name": "KARL DÖNITZ", "role": "COMMANDER OF THE U-BOATS"},
   {"s": 4, "film": "subbomb", "from": 32, "to": 38, "sfx": "explosion_far"},
   {"s": 5, "film": "menace", "from": 44, "to": 47.5}],
  "beats": [{"after": 1, "audio": {"src": "fdr", "from": 1239.6, "to": 1246.3}, "source": FDR_SRC, "shots": [
   {"dur": 3.5, "film": "menace", "from": 32, "to": 36, "source": FDR_SRC},
   {"dur": 3.5, "film": "subbomb", "from": 16, "to": 20, "source": FDR_SRC, "sfx": "explosion_far"}]}]},

 {"title": "The First Day", "mode": "action", "stamp": ["SEPTEMBER 3", "1939"], "sentences": [
  "But when the war begins, Dönitz has only 57 U-boats, and only 27 of them can reach the Atlantic from their German bases.",
  "By his own calculations, he needs 300.",
  "With them, he could sink a million tons of ships a month.",
  "Within hours of the declaration of war, U-30 sinks the passenger liner Athenia, against its orders.",
  "Dönitz's first major action is to cover the sinking up.",
  "Then U-29 sinks the aircraft carrier Courageous.",
  "Dönitz wants a victory for his own command: the Royal Navy's base at Scapa Flow.",
  "On 14 October 1939, Günther Prien takes U-47 inside.",
  "He sees two battleships, but there is only one, the Royal Oak.",
  "She sinks within 15 minutes, with the loss of 835 men and boys.",
  "Prien and his crew are flown to Berlin aboard Hitler's personal aircraft.",
  "Hitler awards him the Knight's Cross, and the propaganda makes him a hero."],
  "shots": [
   {"s": 1, "file": U31},
   {"s": 2, "file": DONITZ2, "note": "300 BOATS"},
   {"s": 3, "film": "convoy42", "from": 74, "to": 80},
   {"s": 4, "file": ATHENIA, "label": "ATLANTIC · 3 SEPTEMBER 1939"},
   {"s": 5, "file": ATHENIA2},
   {"s": 6, "file": COURAGEOUS},
   {"s": 7, "film": "convoy42", "from": 138, "to": 144},
   {"s": 8, "file": PRIEN, "name": "GÜNTHER PRIEN", "role": "COMMANDER, U-47"},
   {"s": 9, "file": ROYAL_OAK, "label": "SCAPA FLOW · 14 OCTOBER 1939"},
   {"s": 10, "film": "depth", "from": 104, "to": 110, "sfx": "explosion_far", "note": "835 MEN AND BOYS"},
   {"s": 11, "file": U47},
   {"s": 12, "file": U31, "zoom": 1.35, "x": 0.45}],
  "beats": [
   {"after": 10, "shots": [{"dur": 3.0, "film": "subbomb", "from": 38, "to": 41, "sfx": "low_rumble"},
                           {"dur": 3.0, "film": "convoy42", "from": 216, "to": 219}]}]},

 {"title": "The Happy Time", "mode": "people", "stamp": ["LORIENT"], "sentences": [
  "But in the spring of 1940, off Norway, the U-boats' torpedoes fail them.",
  "Only one British warship is sunk by U-boats in more than 38 attacks.",
  "Prien loses faith in his main weapons.",
  "Then France falls, and Germany gains U-boat bases at Lorient, Brest, Saint-Nazaire, La Pallice and Bordeaux.",
  "They are about 450 miles closer to the Atlantic than the bases on the North Sea.",
  "Britain has lost destroyers off Norway and at Dunkirk, and the convoys sail with few escorts.",
  "From June until October 1940, over 270 Allied ships are sunk.",
  "The U-boat crews call it the Happy Time."],
  "shots": [
   {"s": 1, "film": "convoy42", "from": 254, "to": 260},
   {"s": 2, "film": "depth", "from": 12, "to": 18},
   {"s": 3, "file": PRIEN, "zoom": 1.25, "y": 0.28},
   {"s": 4, "file": BUNKER, "label": "LORIENT · FRANCE"},
   {"s": 5, "file": U37},
   {"s": 6, "film": "convoy42", "from": 314, "to": 318},
   {"s": 7, "film": "convoy42", "from": 100, "to": 106, "note": "270 SHIPS"},
   {"s": 8, "file": U37, "zoom": 1.35, "x": 0.4}]},

 {"title": "Wolf Packs", "mode": "action", "stamp": ["SEPTEMBER 1940"], "sentences": [
  "But against a convoy, one U-boat can do little, so Dönitz sends them in packs.",
  "On 21 September, convoy HX 72 of 42 merchant ships is attacked by a pack of four U-boats.",
  "Over two nights, they sink eleven ships.",
  "In October, the slow convoy SC 7, with an escort of two sloops and two corvettes, loses 59 percent of its ships.",
  "The most daring commanders, such as Otto Kretschmer, slip through the escort screen.",
  "They attack from within the columns of merchant ships.",
  "In London, Winston Churchill watches the losses grow."],
  "shots": [
   {"s": 1, "film": "convoyair", "from": 110, "to": 116},
   {"s": 2, "film": "blimp", "from": 120, "to": 126},
   {"s": 3, "film": "menace", "from": 36, "to": 41},
   {"s": 4, "film": "blimp", "from": 134, "to": 140, "note": "59 PERCENT"},
   {"s": 5, "file": KRETSCHMER, "name": "OTTO KRETSCHMER", "role": "COMMANDER, U-99"},
   {"s": 6, "film": "convoy42", "from": 112, "to": 118},
   {"s": 7, "file": CHURCHILL_LIV, "name": "WINSTON CHURCHILL", "role": "PRIME MINISTER"}],
  "beats": [
   {"after": 4, "shots": [{"dur": 3.0, "film": "subbomb", "from": 18, "to": 21, "sfx": "explosion_far"},
                          {"dur": 3.0, "film": "convoy42", "from": 204, "to": 208, "sfx": "low_rumble"}]},
   {"after": 7, "quote": {"text": "The only thing that really frightened me during the war was the U-boat peril.",
                          "name": "WINSTON CHURCHILL", "role": "PRIME MINISTER"},
    "shots": [{"dur": 4.5, "file": CHURCHILL_LIV, "zoom": 1.3, "y": 0.35}]}]},

 {"title": "The Aces Fall", "mode": "action", "stamp": ["MARCH 1941"], "sentences": [
  "But in March 1941, the escorts strike back.",
  "Prien dies when U-47 is lost on 8 March.",
  "U-100 is detected by the primitive radar on the destroyer Vanoc, rammed and sunk.",
  "Within the space of several days, Prien and Schepke are dead, and Kretschmer is a prisoner.",
  "Dönitz has lost his three leading aces.",
  "Then, on 9 May, crew members of the destroyer Bulldog board U-110.",
  "They recover current Enigma keys, the settings of the U-boats' cipher.",
  "From then on, the British can read the naval Enigma, and reroute convoys around the U-boats."],
  "shots": [
   {"s": 1, "film": "depth", "from": 120, "to": 126},
   {"s": 2, "file": U47, "zoom": 1.3, "x": 0.45},
   {"s": 3, "film": "depth", "from": 62, "to": 68},
   {"s": 4, "file": U99},
   {"s": 5, "file": KRETSCHMER, "zoom": 1.3, "y": 0.3, "note": "THREE ACES"},
   {"s": 6, "file": U110, "label": "NORTH ATLANTIC · 9 MAY 1941"},
   {"s": 7, "file": ENIGMA, "note": "ENIGMA"},
   {"s": 8, "file": BOMBE}],
  "beats": [
   {"after": 3, "shots": [{"dur": 3.0, "film": "depth", "from": 14, "to": 17, "sfx": "explosion_far"},
                          {"dur": 3.0, "film": "depth", "from": 52, "to": 55}]}]},

 {"title": "Shoot on Sight", "mode": "people", "stamp": ["SEPTEMBER 1941"], "sentences": [
  "But the United States is still neutral.",
  "On 4 September 1941, a German submarine fires a torpedo at the American destroyer Greer.",
  "It misses.",
  "A week later, President Roosevelt speaks to the nation on the radio.",
  "He announces what becomes known as his shoot-on-sight order.",
  "American warships begin escorting Allied convoys as far as Iceland.",
  "On 11 December 1941, Hitler declares war on the United States."],
  "shots": [
   {"s": 1, "film": "convoy42", "from": 232, "to": 238},
   {"s": 2, "film": "depth", "from": 62, "to": 66, "label": "NORTH ATLANTIC · 4 SEPTEMBER 1941"},
   {"s": 3, "film": "depth", "from": 66, "to": 70},
   {"s": 4, "file": FDR, "name": "FRANKLIN D. ROOSEVELT", "role": "PRESIDENT OF THE UNITED STATES"},
   {"s": 5, "file": FDR, "zoom": 1.3, "y": 0.3, "note": "SHOOT ON SIGHT"},
   {"s": 6, "film": "convoy42", "from": 20, "to": 26},
   {"s": 7, "film": "convoy42", "from": 242, "to": 248}],
  "beats": [
   {"after": 4, "audio": {"src": "fdr", "from": 209.5, "to": 216.3}, "source": FDR_SRC,
    "shots": [{"dur": 3.5, "film": "convoy42", "from": 40, "to": 44, "source": FDR_SRC},
              {"dur": 3.5, "film": "depth", "from": 0, "to": 4, "source": FDR_SRC}]}]},

 {"title": "Drumbeat", "mode": "action", "stamp": ["NEW YORK"], "sentences": [
  "But Dönitz has only five Type IX boats able to reach the American coast.",
  "No charts or sailing directions are available.",
  "Reinhard Hardegen of U-123 is given two tourist guides to New York.",
  "In the early hours of 14 January, he sinks the tanker Norness within sight of Long Island.",
  "There are 13 destroyers idle in New York Harbor, yet none is sent against him.",
  "The coast has no blackout, and the U-boats pick out ships against the lights of the cities.",
  "Admiral Ernest King rejects British calls for a blackout or convoys.",
  "On 26 February, U-578 sinks the American tanker R. P. Resor, and 47 of its 49 crew die.",
  "The Germans call it the second happy time.",
  "The U-boats sink 397 ships."],
  "shots": [
   {"s": 1, "map": M_DRUM},
   {"s": 2, "film": "blimp", "from": 36, "to": 42},
   {"s": 3, "file": U123, "name": "REINHARD HARDEGEN", "role": "COMMANDER, U-123"},
   {"s": 4, "film": "convoy42", "from": 196, "to": 200, "label": "LONG ISLAND · 14 JANUARY 1942"},
   {"s": 5, "film": "convoy42", "from": 8, "to": 14, "note": "13 DESTROYERS"},
   {"s": 6, "film": "blimp", "from": 44, "to": 50},
   {"s": 7, "file": KING, "name": "ERNEST KING", "role": "ADMIRAL, COMMANDER IN CHIEF, U.S. FLEET"},
   {"s": 8, "file": RESOR, "label": "NEW JERSEY · 26 FEBRUARY 1942"},
   {"s": 9, "file": RESOR2},
   {"s": 10, "film": "convoyair", "from": 52, "to": 57, "note": "397 SHIPS"}],
  "beats": [
   {"after": 8, "shots": [{"dur": 3.5, "file": RESOR2, "zoom": 1.3, "x": 0.5, "sfx": "low_rumble"},
                          {"dur": 3.0, "film": "blimp", "from": 28, "to": 31}]}]},

 {"title": "The Air Gap", "mode": "people", "stamp": ["SEPTEMBER 1942"], "sentences": [
  "But in the middle of the ocean, no aircraft can reach the convoys.",
  "On 12 September 1942, U-156 sinks the British ship Laconia, carrying mostly Italian prisoners of war.",
  "Its commander, Werner Hartenstein, immediately begins a rescue.",
  "His boat is crammed with nearly 200 survivors, and 200 more in lifeboats in tow.",
  "Then an American Liberator bomber attacks it.",
  "Dönitz orders his crews not to rescue survivors again.",
  "In October 1942, 56 ships are sunk in the air gap between Greenland and Iceland."],
  "shots": [
   {"s": 1, "map": M_GAP},
   {"s": 2, "file": LACONIA, "label": "WEST AFRICA · 12 SEPTEMBER 1942"},
   {"s": 3, "film": "menace", "from": 54, "to": 58},
   {"s": 4, "film": "convoy42", "from": 54, "to": 59, "note": "200 SURVIVORS"},
   {"s": 5, "file": LIBERATOR},
   {"s": 6, "file": DONITZ3},
   {"s": 7, "film": "convoyair", "from": 28, "to": 33, "note": "56 SHIPS"}]},

 {"title": "The Crisis", "mode": "action", "stamp": ["MARCH 1943"], "sentences": [
  "But on 10 March 1943, the Germans add a refinement to the U-boat Enigma key.",
  "The code breakers at Bletchley Park are blind for 9 days.",
  "That month, 120 Allied ships are sunk.",
  "Britain considers abandoning the convoy system itself.",
  "On 18 March, Roosevelt orders King to send 60 Liberators from the Pacific to the Atlantic.",
  "It is one of only two direct orders he gives his commanders in the whole war.",
  "Very long range aircraft begin to close the air gap.",
  "And the escorts carry Huff-Duff, which finds a U-boat by its own radio signals."],
  "shots": [
   {"s": 1, "file": ENIGMA, "zoom": 1.3, "x": 0.45, "label": "10 MARCH 1943"},
   {"s": 2, "file": BOMBE, "zoom": 1.25, "note": "9 DAYS"},
   {"s": 3, "film": "depth", "from": 100, "to": 106, "note": "120 SHIPS"},
   {"s": 4, "film": "convoy42", "from": 120, "to": 126},
   {"s": 5, "file": LIBERATOR, "label": "18 MARCH 1943", "note": "60 LIBERATORS"},
   {"s": 6, "file": KING, "zoom": 1.3, "y": 0.3},
   {"s": 7, "film": "blimp", "from": 84, "to": 90},
   {"s": 8, "film": "blimp", "from": 72, "to": 78}],
  "beats": [
   {"after": 3, "shots": [{"dur": 3.5, "film": "depth", "from": 110, "to": 114, "sfx": "explosion_far"},
                          {"dur": 3.0, "film": "blimp", "from": 140, "to": 143, "sfx": "low_rumble"}]}]},

 {"title": "Black May", "mode": "action", "stamp": ["MAY 1943"], "sentences": [
  "But this time, the convoys fight back.",
  "Convoy ONS 5, of 43 merchant ships, is attacked by a pack of 30 U-boats.",
  "It loses thirteen merchant ships, but six U-boats are sunk.",
  "Then five U-boats are sunk attacking convoy SC 130, while no convoy ships are lost.",
  "Among the dead is Peter, the son of Admiral Dönitz, aboard U-954.",
  "In May, 43 U-boats are lost, a quarter of their operational strength.",
  "On 24 May, Dönitz orders the suspension of Atlantic operations.",
  "This is the answer: in two months, the hunters have become the hunted."],
  "shots": [
   {"s": 1, "film": "depth", "from": 128, "to": 134},
   {"s": 2, "film": "convoyair", "from": 8, "to": 14, "label": "NORTH ATLANTIC · MAY 1943", "note": "30 U-BOATS"},
   {"s": 3, "file": U266, "sfx": "explosion_far"},
   {"s": 4, "film": "subbomb", "from": 38, "to": 43, "sfx": "explosion_far"},
   {"s": 5, "file": DONITZ, "zoom": 1.3, "y": 0.3},
   {"s": 6, "file": U243, "note": "43 U-BOATS"},
   {"s": 7, "file": DONITZ2, "label": "24 MAY 1943"},
   {"s": 8, "film": "subbomb", "from": 10, "to": 14}],
  "beats": [
   {"after": 6, "shots": [{"dur": 3.0, "film": "subbomb", "from": 22, "to": 25, "sfx": "explosion_far"},
                          {"dur": 3.5, "film": "depth", "from": 56, "to": 59.5}]}]},

 {"title": "The Hunted", "mode": "people", "stamp": ["JUNE 1944"], "sentences": [
  "But Dönitz keeps sending the boats out.",
  "On 4 June 1944, an American task group captures U-505 at sea.",
  "Its commander, Captain Daniel Gallery, has long been keen to capture a U-boat.",
  "Admiral King is furious, because it endangers the secret of the Enigma decrypts.",
  "On D-Day, the U-boats are sent against the invasion.",
  "They sink only eight of the 5,339 vessels.",
  "On 29 April 1945, Hitler names Dönitz his successor.",
  "When Germany surrenders, 222 U-boats are scuttled by their crews, and 174 surrender.",
  "Between 1939 and 1945, 72,200 Allied naval and merchant seamen die.",
  "Of the 40,000 men who served in U-boats, around 30,000 never come home.",
  "The Atlantic stays open, and the armies that free Europe cross it."],
  "shots": [
   {"s": 1, "file": U387},
   {"s": 2, "file": U505, "label": "OFF WEST AFRICA · 4 JUNE 1944"},
   {"s": 3, "file": GALLERY},
   {"s": 4, "file": U505_SALV},
   {"s": 5, "film": "convoy42", "from": 304, "to": 310},
   {"s": 6, "film": "convoy42", "from": 210, "to": 216, "note": "8 OF 5,339"},
   {"s": 7, "file": DONITZ3, "zoom": 1.25, "y": 0.3},
   {"s": 8, "file": SURRENDER, "label": "LISAHALLY · MAY 1945"},
   {"s": 9, "film": "convoy42", "from": 260, "to": 266, "note": "72,200 SEAMEN"},
   {"s": 10, "film": "menace", "from": 76, "to": 82},
   {"s": 11, "film": "convoy42", "from": 184, "to": 190}],
  "beats": [
   {"after": 8, "shots": [{"dur": 3.5, "film": "menace", "from": 58, "to": 62},
                          {"dur": 3.0, "film": "menace", "from": 70, "to": 74}]}]},
]


def after(ch, prefix, sentence, shot):
    """Insert `sentence` right after the sentence of chapter `ch` that starts with `prefix` ('' = before the first);
    later shots and beats move down by one."""
    c = C[ch]
    pos = 1 if prefix == "" else next(i for i, s in enumerate(c["sentences"]) if s.startswith(prefix)) + 2
    c["sentences"].insert(pos - 1, sentence)
    for s in c["shots"]:
        if s["s"] >= pos:
            s["s"] += 1
    for b in c.get("beats", []):
        if b["after"] >= pos:
            b["after"] += 1
    c["shots"].append({"s": pos, **shot})
    c["shots"].sort(key=lambda s: s["s"])


after(1, "But when the war begins", "In the First World War, Dönitz himself commanded a U-boat, UB-68, and attacked a convoy near Malta.",
      {"film": "convoy42", "from": 160, "to": 166})
after(1, "With them, he could", "He recommends the Type VII as the ideal submarine.", {"file": U387})
after(1, "Dönitz wants a victory", "From air and sea reports, he finds an 18-yard gap between the blockships at its northeast entrance.",
      {"film": "convoy42", "from": 286, "to": 292})
after(1, "On 14 October 1939", "Prien ignores Dönitz's advice, and sails between two of the blockships.",
      {"film": "menace", "from": 28, "to": 32})
after(2, "Britain has lost destroyers", "Slowly, old ex-American destroyers and new Flower-class corvettes come into service.",
      {"film": "convoy42", "from": 202, "to": 208})
after(2, "Slowly, old", "The corvettes can detect and defend, but they are not fast enough to attack.",
      {"film": "depth", "from": 74, "to": 80})
after(3, "But against a convoy", "The boat that finds a convoy shadows it, waiting for the cover of night to attack.",
      {"film": "convoyair", "from": 14, "to": 20})
after(3, "In October, the slow convoy", "The battle for convoy HX 79 in the following days is in many ways worse for the escorts.",
      {"film": "blimp", "from": 146, "to": 152})
C[4]["sentences"][1] = "Prien dies when U-47 is lost on 8 March, probably sunk by the destroyer Wolverine, west of Ireland."
after(3, "In London, Winston", "Yet the convoys keep sailing.", {"film": "convoyair", "from": 120, "to": 126})
after(4, "They recover current Enigma", "At Bletchley Park, only Frank Birch and the mathematician Alan Turing had believed that naval Enigma could be broken.",
      {"film": "blimp", "from": 74, "to": 78})
after(5, "But the United States", "In April 1941, Roosevelt extends the Pan-American Security Zone east, almost as far as Iceland.",
      {"film": "convoy42", "from": 26, "to": 32})
after(5, "It misses.", "But the Greer had held contact with the submarine for 3 hours and 28 minutes before it fired.",
      {"film": "depth", "from": 4, "to": 8, "note": "3 HOURS 28 MINUTES"})
after(5, "American warships begin", "In December, convoy HG 76 sails with the first escort carrier, Audacity, and the escort group of Captain Frederic John Walker.",
      {"film": "blimp", "from": 152, "to": 158})
after(5, "In December, convoy HG 76", "The five-day battle costs the Germans five U-boats, and the British only two merchant ships, a destroyer and Audacity.",
      {"film": "depth", "from": 80, "to": 86})
after(6, "But Dönitz has only five", "He calls the operation Paukenschlag, Drumbeat.", {"file": U123, "zoom": 1.3, "x": 0.5})
after(6, "He calls the operation", "New York is 3,000 miles to the west of the U-boat bases in Brittany.",
      {"film": "blimp", "from": 20, "to": 26})
after(6, "In the early hours of 14 January", "The next night, he sinks the British tanker Coimbra off Sandy Hook.",
      {"film": "convoy42", "from": 290, "to": 294})
after(6, "The U-boats sink 397", "The second happy time reaches its peak in June.",
      {"film": "convoyair", "from": 40, "to": 46})
after(6, "The second happy time", "Only when the Americans finally arrange convoys do the losses quickly drop.",
      {"film": "convoy42", "from": 126, "to": 132})
after(6, "Only when the Americans", "On 19 July 1942, Dönitz orders the last boats to withdraw from the American coast.",
      {"film": "menace", "from": 44, "to": 47.5})
after(7, "But in the middle of the ocean", "The convoys rely on aircraft from Northern Ireland and Iceland, but none can reach the middle.",
      {"film": "subbomb", "from": 0, "to": 6})
after(7, "In October 1942", "And since February, the U-boats use a new four-rotor Enigma machine.", {"film": "blimp", "from": 70, "to": 74})
after(7, "And since February", "Bletchley Park cannot read it until December 1942.", {"film": "convoy42", "from": 232, "to": 236})
after(8, "Britain considers abandoning", "The Admiralty later reports that the Germans never came so near to cutting the new world off from the old.",
      {"film": "convoy42", "from": 146, "to": 150})
after(8, "And the escorts carry Huff-Duff", "New weapons arrive, such as the Hedgehog, which throws its bombs ahead of the ship.",
      {"film": "depth", "from": 136, "to": 142})
after(8, "New weapons arrive", "And the Leigh Light lets aircraft attack U-boats on the surface at night.",
      {"film": "subbomb", "from": 44, "to": 50})
after(9, "Then five U-boats are sunk", "Escort carriers and support groups now hunt the U-boats, free from any convoy.",
      {"film": "blimp", "from": 88, "to": 94})
after(9, "Among the dead is Peter", "A year later, his other son, Klaus, is dead too.", {"file": U243, "zoom": 1.3, "x": 0.5})
after(10, "They sink only eight", "Dönitz places much faith in a new boat, the Type XXI.", {"film": "menace", "from": 12, "to": 18})
after(10, "Dönitz places much faith", "But few are ready in time, and many have technical problems.", {"film": "menace", "from": 4, "to": 10})
after(10, "When Germany surrenders", "121 of them are sunk in 1945 and 1946, in Operation Deadlight.", {"file": SURRENDER, "zoom": 1.3, "x": 0.5})
after(10, "121 of them", "At Nuremberg, Dönitz is sentenced to ten years in prison.", {"film": "menace", "from": 120, "to": 126})

STORY = {
 "priority": 10,
 "format": "entire",
 "voice": "andrii",
 "intro_beats": True,
 "topic": "Battle of the Atlantic",
 "sources": ["U-boat", "Karl Dönitz", "Günther Prien", "German submarine U-47 (1938)", "Second Happy Time",
             "Wolfpack (naval tactic)", "Black May (1943)", "Laconia incident", "USS Greer", "German submarine U-505"],
 "title": "The ENTIRE History of Hitler's U-boats in {N} Minutes",
 "question": "Could the U-boats have won the war for Germany if Dönitz had his 300 boats in 1939?",
 "summary": ("From Günther Prien's raid on Scapa Flow and the wolf packs of 1940 to the U-boats off New York in 1942 "
             "and the Black May of 1943, this is the whole story of Hitler's U-boats in the Battle of the Atlantic, "
             "told with the archive film of the time and President Roosevelt's own voice."),
 "tags": ["U-boat", "U-boats", "Battle of the Atlantic", "Karl Dönitz", "Günther Prien", "Scapa Flow", "wolf pack",
          "Operation Drumbeat", "Black May", "Enigma", "U-505", "Kriegsmarine", "WW2 documentary", "World War 2",
          "history"],
 "pronounce": {"Dönitz": "Der-nits", "Prien": "Preen", "Kretschmer": "Kretch-mer", "Schepke": "Shep-keh",
               "Hardegen": "Har-day-gen", "Hartenstein": "Har-ten-shtine", "Lorient": "Lor-ee-ahn",
               "Saint-Nazaire": "San Nah-zair", "La Pallice": "Lah Pah-leese", "Norness": "Nor-ness",
               "Athenia": "Ah-thee-nee-ah", "Laconia": "La-coh-nee-ah", "Scapa Flow": "Skah-pah Flow"},
 "films": {
  "convoy42": {"url": "https://archive.org/download/428-npc-16081/428-npc-16081.mp4", "mono": True,
               "crop": "704:360:8:60",
               "credit": "North Atlantic Convoy (1942): US Navy / NARA 428-NPC-16081 (public domain, via Internet Archive)"},
  "convoyair": {"url": "https://archive.org/download/NPC-1849b/NPC-1849b.mov", "mono": True, "crop": "996:560:142:0",
                "credit": "Aerial Views of Convoy (1943): US Navy / NARA 428-NPC-1849 (public domain, via Internet Archive)"},
  "depth": {"url": "https://archive.org/download/NPC-2667/NPC-2667.mov", "mono": True, "crop": "996:560:142:0",
            "credit": "Firing Depth Charges (1944): US Navy / NARA 428-NPC-2667 (public domain, via Internet Archive)"},
  "subbomb": {"url": "https://archive.org/download/NPC-15381/428-NPC-15381%20Planes%20Bomb%20Sub%20Off%20East%20Coast%20Of%20United%20States%201943.mov",
              "mono": True, "crop": "1120:630:80:20",
              "credit": "Planes Bomb Sub Off East Coast of United States (1943): US Navy / NARA 428-NPC-15381 (public domain, via Internet Archive)"},
  "blimp": {"url": "https://archive.org/download/NPC-1832/NPC-1832.mp4", "mono": True, "crop": "498:280:71:0",
            "credit": "Blimp Patrol Over Convoy (1943): US Navy / NARA 428-NPC-1832 (public domain, via Internet Archive)"},
  "menace": {"url": "https://archive.org/download/1945-05-17_U-Boat_Menace_Ended/1945-05-17_U-Boat_Menace_Ended.mpeg",
             "mono": True, "crop": "688:344:16:68",
             "credit": "U-Boat Menace Ended (17 May 1945): Universal Newsreel (public domain, via Internet Archive)"}},
 "period_audio": {
  "fdr": {"file": "FDROnFreedomOfTheSeas.mp3",
          "url": ("https://archive.org/download/FDROnFreedomOfTheSeas/President%20Roosevelt%2527s%20Fireside%20Chat"
                  "%20on%20Freedom%20of%20the%20Seas%2C%2009%3A11%3A1941.mp3"),
          "speaker": "Franklin D. Roosevelt", "date": "SEPTEMBER 1941",
          "credit": "President Roosevelt's Fireside Chat on Freedom of the Seas (11 September 1941): NARA 2192567 (public domain, via Internet Archive)",
          "text": "These Nazi submarines and raiders are the rattlesnakes of the Atlantic."}},
 "pre": [{"dur": 2.8, "film": "depth", "from": 52, "to": 56, "stamp": ["JANUARY 14", "1942"],
          "sfx": "explosion_massive"}],
 "whole": [FDR, DONITZ, KING],
 "tone": [DONITZ],                      # DDColor paints his face cyan and red
 "trims": {U37: [0, 0, 0, 0.17], BUNKER: [0, 0, 0, 0.07]},
 "thumb": {"file": U47},
 "cover": {"file": U47, "x": 0.5, "y": 0.62, "zoom": 1.0, "color": False,
           "text": ["HISTORY OF", "HITLER'S U-BOATS", "IN {N} MINUTES"], "key": ["U-BOATS"], "sizes": [96, 150, 96],
           "mono": True},
 "promos": [
  {"id": "uboat_newyork", "chapter": 6,
   "sentences": ["In January 1942, a U-boat sails to attack New York.",
                 "Its commander has no charts of the coast.",
                 "So he uses something else: two tourist guides to New York."],
   "shots": [{"s": 1, "file": U123}, {"s": 2, "film": "blimp", "from": 36, "to": 42},
             {"s": 3, "film": "convoy42", "from": 186, "to": 192}],
   "top": "A U-BOAT|AT NEW YORK", "key": ["U-BOAT"],
   "cta": {"kind": "redacted", "line": "HE NAVIGATES WITH", "hidden": "TOURIST GUIDES"}, "end": "WITH WHAT?",
   "name": "The U-boat That Found New York With Tourist Guides"},
  {"id": "uboat_blackmay", "chapter": 9,
   "sentences": ["In May 1943, the U-boats lose a quarter of their strength.",
                 "One boat sunk is U-954.",
                 "Among its dead is a famous name: Peter, the son of Admiral Dönitz."],
   "shots": [{"s": 1, "file": U266}, {"s": 2, "film": "subbomb", "from": 36, "to": 42},
             {"s": 3, "file": DONITZ, "zoom": 1.3, "y": 0.3}],
   "top": "THE U-BOAT|ADMIRAL'S SON", "key": ["U-BOAT"],
   "cta": {"kind": "timestamp"}, "end": "WHO WAS ABOARD?",
   "name": "The U-boat Admiral Who Lost His Own Son"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "uboat.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
