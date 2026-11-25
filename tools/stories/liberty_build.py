"""The Liberty ships, Nov 25 (Andrii: '1 так'): genre 1 (machines) in the NEW FORMAT (CLAUDE.md, Nov 23): voice No. 3,
President Roosevelt's Liberty Fleet Day message (27 September 1941) as the speech after sentence 1, one open question
(why do they break in half?), chapters that follow one named person, 2 cliff teasers.
Facts: Wikipedia 'Liberty ship', 'SS Patrick Henry', 'SS Robert E. Peary', 'Henry J. Kaiser', 'Kaiser Shipyards',
'Richmond Shipyards', 'Emergency Shipbuilding Program', 'Ocean ship', 'SS Stephen Hopkins', 'German auxiliary cruiser
Stier', 'SS Booker T. Washington', 'Hugh Mulzac', 'SS Schenectady', 'SS John P. Gaines', 'Constance Tipper',
'SS John Harvey', 'Air raid on Bari', 'SS Paul Hamilton', 'Port Chicago disaster', 'SS Richard Montgomery', 'Texas City
disaster', 'SS Jeremiah O'Brien' (whole, sources/*.txt).
Films (public domain): the Robert E. Peary launch (California Revealed), Marinship's colour 'Tanker' film (its first
ship is the Liberty William A. Richardson), United News 'Last Liberty Ship Launched', NARA NPC-5153 (launch of the Liberty
Deborah Gannett), NPC-16151 (Armed Guard, December 1941), NPC-4814 (Port Chicago), NPC-4420 (Normandy), 'A Ship Is Born'
(US Maritime Commission 1942).
Run: python tools/stories/liberty_build.py"""
import json, pathlib

IA = "https://archive.org/download/"
PHENRY = "SS Patrick Henry Liberty ship 1941.jpg"
KAISER = "pics/henry_kaiser.jpg"
B01 = "Liberty ship construction 01 keel blocks.jpg"
B02 = "Liberty ship construction 02 keel laying.jpg"
B03 = "Liberty ship construction 03 keel plates.jpg"
B04 = "Liberty ship construction 04 bottom.jpg"
B05 = "Liberty ship construction 05 midship bulkhead.jpg"
B08 = "Liberty ship construction 08 collision bulkhead.jpg"
B09 = "Liberty ship construction 09 lower decks.jpg"
B10 = "Liberty ship construction 10 upper decks.jpg"
B11 = "Liberty ship construction 11 prepared for launch.jpg"
B12 = "Liberty ship construction 12 SS Muhlenberg stern.jpg"
B16 = "Liberty ship construction 16 slipways.jpg"
ENGINE = "Liberty ship 140-ton VTE engine.jpg"
WELD2 = "Electric welders at work on the Liberty ship USS Frederick Douglass (1943).jpg"
WENDY = "Wendy Welder Richmond Shipyards.jpg"
WENDYC = "Wendy Welder Richmond Shipyards (cropped).jpg"
SCALER = "Liberty Ship scaler HD-SN-99-02466.JPG"
ARRIVE = "Workers arriving at the Bethlehem Fairfield shipyard 8d15862v.jpg"
SHIFT = "Second shift workers leaving the Bethlehem Fairfield shipyard 8d27854v.jpg"
EIGHTEEN = "Eighteen hundred workers are carried from the Bethlehem Fairfield shipyard 8d28049v.jpg"
DEWEY = '80-G-84349 SS George Dewey ("Liberty " ship).jpg'
OVERMAN = 'SC 231831 S.S. LEE S. OVERMAN ("Liberty" Ship) sunk in France, November 18, 1944.jpg'
BURNETT = "Peter H Burnett hull damage at Sutherland Dock, February 1943.jpg"
STARR = "Starr King (AWM 128144).jpg"
SCHEN = "TankerSchenectady.jpg"
BARI = "Atak lotniczy na flotę w Bari (2-2443).jpg"
JU88 = "Captured German Junkers Ju 88A-4 at Foggia, Italy, October 1943 (342-FH-3A23116-53226AC).jpg"
ALGIERS = "USS Savannah (CL-42) with burning Liberty ships Algiers 1943.jpg"
BTW = "Ss-booker-t-washington-1943.jpg"
ANDERSON = "Marian Anderson christens the liberty ship Booker T. Washington.jpg"
ANDERSON2 = "Marian Anderson and Mary McLeod Bethune at the launching of the SS Booker T Washington - 29 Sept 1942.jpg"
MULZAC = "Hugh Mulzac.jpg"
HAMILTON = "SS Paul Hamilton destroyed 20 Apr 1944.jpg"
PC1 = "Portchicago.jpg"
PCWORK = "PortChicagoAmmowork1943.jpg"
PCBOX = "PortChicagoBoxcarRevetment.jpg"
PC2 = "Portchicago2.jpg"
RESERVE = "Aerial view of the Beaumont Reserve Fleet, Texas (USA) on 23 February 1950 (80-G-412809).jpg"
WSA = "WSA Photo 4235.jpg"
TXCARS = "Txcitydisasterparkinglot.jpg"
TXBOAT = "Txcitydisasterboat.jpg"
BROWNAIR = "SS John W. Brown aerial photo.jpg"
BROWN16 = "SS John W. Brown docks at Norfolk (Virginia) in May 2016.JPG"
OBRIEN = "Liberty Ship S.S. Jeremiah O'Brien, San Francisco, California LCCN2011631366.tif"
OBRIEN94 = "Jeremiah O'Brien (IMO 5171749).jpg"
SAMTWEED = "Samtweed Liberty ship.jpg"
HALE = "Eugene Hale 1943 Liberty ship.tif"

F_SRC = "PRESIDENT ROOSEVELT · LIBERTY FLEET DAY, SEPTEMBER 1941"

M_HOP = {"places": [{"label": "CAPE TOWN", "lat": -33.9, "lon": 18.4, "side": "blue"},
                    {"label": "PARAMARIBO", "lat": 5.85, "lon": -55.2, "side": "blue"},
                    {"label": "BRAZIL", "lat": -12.0, "lon": -45.0}],
         "routes": [[0, 1, "blue", 0.15]], "pad": 0.25}
M_BARI = {"places": [{"label": "BARI", "lat": 41.13, "lon": 16.87, "side": "blue"},
                     {"label": "NAPLES", "lat": 40.85, "lon": 14.27, "side": "blue"},
                     {"label": "ORAN", "lat": 35.7, "lon": -0.63, "side": "blue"}],
          "routes": [[2, 0, "blue", 0.2]], "pad": 0.3}


def film(s, key, x, n=6, **k):
    return {"s": s, "film": key, "from": x, "to": x + n, **k}


def pic(s, f, **k):
    return {"s": s, "file": f, **k}


def beat(after, *shots):
    return {"after": after, "shots": [{"dur": d, "film": f, "from": x, "to": x + d, **({"sfx": s} if s else {})}
                                      for d, f, x, s in shots]}


def voice(after, a, b, *shots):
    return {"after": after, "audio": {"src": "fdr", "from": a, "to": b}, "source": F_SRC,
            "shots": [{"dur": d, "film": f, "from": x, "to": x + d, "source": F_SRC} for d, f, x in shots]}


C = [
 {"title": "", "mode": "action", "sentences": [
  "On 12 November 1942, in Richmond, California, a ship goes down the slipway, less than five days after her keel was laid.",
  "She is a Liberty ship, one of 2,710, the largest number ever built to a single design.",
  "The man behind the record is Henry Kaiser, who left school at thirteen.",
  "But why do some of these ships crack, and a few break in half without warning?",
  "It all begins with a ship that the president calls a dreadful looking object."],
  "shots": [
   film(1, "lb_peary", 15, 3.4, stamp=["RICHMOND"]),
   film(1, "lb_peary", 19, 3.4),
   film(2, "lb_mar", 396, 2.8, note="2,710 SHIPS"),
   film(2, "lb_gan", 144, 4),
   pic(3, KAISER, reveal=[0.75, 0.34], name="HENRY KAISER", role="SHIPBUILDER"),
   film(4, "lb_conv", 152, 3),
   pic(4, SCHEN, trim=[0, 0.02, 0, 0.05]),
   film(5, "lb_last", 80, 3.3)],
  "beats": [voice(1, 19.75, 24.9, (2.6, "lb_peary", 23.1), (2.55, "lb_mar", 399))]},

 {"title": "The Ugly Duckling", "mode": "people", "stamp": ["1940"], "sentences": [
  "But in 1940 there is no such ship, and German U-boats sink British merchant ships faster than Britain can replace them.",
  "A British mission crosses the ocean to find someone to build more.",
  "The American yards already have all the work they can take.",
  "So new yards must be built first, and in December 1940 the contracts are signed, for 60 ships.",
  "The design comes from Sunderland, in England: a simple tramp steamer, cheap to build and cheap to run.",
  "The Americans take it, and change it to make it even quicker and cheaper.",
  "The boilers burn oil, and welding replaces much of the riveting.",
  "The engine is obsolete, and it is chosen for that reason.",
  "It weighs 140 tons, it gives a speed of about 11 knots, and the seamen already know it.",
  "The new ships look so plain that Time magazine calls one an Ugly Duckling.",
  "To win the public over, 27 September 1941 becomes Liberty Fleet Day.",
  "That day, the first Liberty ship, the Patrick Henry, is launched in Baltimore.",
  "Roosevelt recalls the words of the man she is named after, give me liberty or give me death, and that gives the Liberty ships their name.",
  "But the Patrick Henry has taken 244 days to build."],
  "shots": [
   film(1, "menace", 32, 4),
   film(1, "convoy42", 184, 4, label="THE ATLANTIC"),
   film(2, "lb_conv", 372, 6),
   film(3, "lb_born", 84, 5),
   film(4, "lb_mar", 114, 3),
   film(4, "lb_mar", 101, 4, note="60 SHIPS"),
   pic(5, HALE, label="A LIBERTY SHIP · 1943"),
   film(6, "lb_born", 72, 4),
   film(7, "lb_mar", 1160, 6),
   pic(8, ENGINE, y=0.3, label="THE LIBERTY SHIP ENGINE"),
   pic(9, ENGINE, zoom=1.5, y=0.6, note="11 KNOTS"),
   pic(10, SAMTWEED, trim=[0.05, 0.1, 0.05, 0.1]),
   film(11, "lb_last", 35, 2.8, stamp=["SEPTEMBER 27"]),
   pic(12, PHENRY, label="SS PATRICK HENRY · 1941"),
   film(13, "lb_guard", 24, 4),
   film(13, "lb_guard", 69, 5),
   film(14, "lb_gan", 216, 5, note="244 DAYS")],
  "beats": [voice(11, 12.7, 19.5, (3.4, "lb_gan", 134), (3.4, "lb_mar", 400))]},

 {"title": "The Dam Builder", "mode": "people", "stamp": ["RICHMOND"], "sentences": [
  "But the construction companies that come to Richmond, California, have no experience of building ships.",
  "They know highways, bridges and dams, the Hoover Dam among them.",
  "One of the men behind them is Henry Kaiser, the son of a shoemaker.",
  "On 14 January 1941 they break the ground for the new yard.",
  "Only 78 days later, the first keel is laid.",
  "One of Kaiser's associates visits a Ford assembly plant, and it leads to a decision to weld the ships.",
  "Welding takes less strength than riveting, and it is easier to teach.",
  "Until then, hundreds of workers crowded together to complete a ship.",
  "Now they put together whole sections, and huge cranes lift them into place.",
  "The first Liberty ships take about 230 days to build.",
  "By 1943, the median is 39.",
  "And 18 shipyards, on the Atlantic, the Pacific and the Gulf, are building the same ship."],
  "shots": [
   film(1, "lb_mar", 95, 5),
   film(2, "lb_mar", 111.4, 2.4),
   film(2, "lb_mar", 107, 3),
   pic(3, KAISER, zoom=1.25, y=0.3, name="HENRY KAISER", role="SON OF A SHOEMAKER"),
   film(4, "lb_mar", 117, 4, label="A NEW SHIPYARD IN CALIFORNIA"),
   pic(5, B01, note="78 DAYS"),
   film(6, "lb_mar", 1102, 4.5),
   pic(6, B02),
   film(7, "lb_mar", 1324, 5.5),
   film(8, "lb_mar", 603, 6),
   film(9, "lb_mar", 1536, 2.8),
   film(9, "lb_mar", 1601.5, 6),
   pic(10, B03, y=0.45, note="230 DAYS"),
   pic(11, B04, y=0.5, note="39 DAYS"),
   film(12, "lb_mar", 292, 6, label="MARINSHIP, CALIFORNIA")],
  "beats": [beat(9, (3.0, "lb_mar", 1464, "boom-drop"), (3.0, "lb_mar", 1552, None))]},

 {"title": "Wendy the Welder", "mode": "people", "stamp": ["1942"], "sentences": [
  "But by 1942, the yards are short of something that no crane can lift: people.",
  "For nearly two decades there has been little shipbuilding, and experienced builders are few.",
  "So the recruiters go inland, and whole families come, from places like the Dust Bowl of Texas and Oklahoma.",
  "In three years, Richmond grows from 20,000 people to over 100,000.",
  "There is not enough housing, and there are not enough schools.",
  "Before the war, shipbuilding was only for men.",
  "Now women are welding the ships, and in these yards they are called Wendy the Welder.",
  "For many of them, it is the first time they work and earn money.",
  "But women and minorities still get unequal pay, and are put into separate auxiliary unions.",
  "Kaiser also opens a hospital for his yards, paid for in advance, and by August 1944 more than nine in ten workers at Richmond have joined the plan.",
  "Today it is called Kaiser Permanente.",
  "In 1943, three Liberty ships are completed every day."],
  "shots": [
   film(1, "lb_mar", 701, 6),
   film(2, "lb_mar", 712, 6),
   film(3, "lb_mar", 622, 6),
   pic(3, EIGHTEEN, trim=[0.1, 0.1, 0.06, 0.1]),
   film(4, "lb_mar", 567, 6, note="100,000 PEOPLE"),
   film(5, "lb_mar", 572, 5),
   pic(6, ARRIVE, trim=[0, 0.06, 0, 0]),
   pic(7, WENDY, x=0.6, y=0.4, label="RICHMOND SHIPYARDS · 1943"),
   pic(8, WENDYC, y=0.25),
   pic(9, SCALER, x=0.7, y=0.35, label="A SHIP SCALER · 1943"),
   pic(9, WELD2, y=0.45),
   film(10, "lb_mar", 645.6, 1.8),
   film(10, "lb_mar", 688, 4),
   film(11, "lb_mar", 672, 4),
   film(12, "lb_last", 73, 3, note="3 SHIPS A DAY"),
   film(12, "lb_gan", 160, 4)],
  "beats": [voice(8, 201.15, 205.75, (2.4, "lb_born", 65.6), (2.2, "lb_mar", 1166))]},

 {"title": "Four Days", "mode": "action", "stamp": ["SEPTEMBER 1942"], "sentences": [
  "But in September 1942, an Oregon yard builds a Liberty ship in only ten days, and the yards compete.",
  "A reporter asks Henry Kaiser if it could be done quicker.",
  "In eight days, he replies, but the ship was delayed to allow President Roosevelt to attend.",
  "Then Roosevelt agrees to a proposal: a ship in half the time.",
  "At 12:01 am on 8 November, in Richmond, the keel is laid.",
  "The sections weigh 250 tons each, and the engines are already in place.",
  "By mid-morning, the boilers are in.",
  "On the second day, the upper deck is completed.",
  "On the third day come the masts, the derricks and the superstructure.",
  "On the final day they finish the wiring, the welding and the painting.",
  "That afternoon, the Robert E Peary is launched.",
  "It has taken 4 days, 15 hours and 29 minutes.",
  "Some call her a stunt ship, and there is not enough steel to build them all at such a pace.",
  "Kaiser calls her an incentive ship.",
  "The message is that America can build ships faster than they can be sunk.",
  "And she really sails: to Guadalcanal, and on D-Day to Omaha Beach."],
  "shots": [
   film(1, "lb_born", 336, 3.5),
   film(2, "lb_mar", 354, 4.5),
   film(3, "lb_last", 49, 2.8),
   film(3, "lb_mar", 360, 4),
   pic(4, B16, zoom=1.15),
   pic(5, B02, zoom=1.3, x=0.4, stamp=["12:01 A.M."]),
   pic(6, B05, y=0.4, note="250 TONS"),
   pic(7, B08, y=0.35),
   pic(8, B10, y=0.5),
   film(9, "lb_mar", 1546, 5),
   film(10, "lb_mar", 1168, 3.5),
   film(11, "lb_peary", 5.3, 1.6, stamp=["3:27 P.M."]),
   film(11, "lb_peary", 13.1, 1.8),
   film(12, "lb_peary", 9.1, 3.6),
   film(13, "lb_mar", 1228, 5),
   film(13, "lb_mar", 1240, 4),
   pic(14, B11, y=0.4),
   film(15, "lb_mar", 407, 5),
   film(16, "lb_norm", 354.4, 5, label="LIBERTY SHIPS OFF NORMANDY · 1944")],
  "beats": [beat(11, (3.4, "lb_peary", 15.1, "ov/crowd_cheer"), (3.0, "lb_peary", 19.2, None))]},

 {"title": "One Gun", "mode": "action", "stamp": ["SOUTH ATLANTIC"], "sentences": [
  "But on 27 September 1942, in the South Atlantic, a Liberty ship meets a German raider in the fog.",
  "The Stephen Hopkins sails from Cape Town, and her biggest gun is a single 4-inch.",
  "The raider, the Stier, is heavily armed, and a second German ship, the Tannenfels, is with her.",
  "They are only 2 miles apart when they sight each other.",
  "The Hopkins is ordered to stop, and refuses to surrender.",
  "Stier opens fire.",
  "As the gunners fall, volunteers from the crew take their places at the gun.",
  "They damage the raider's engines and her steering gear.",
  "Cadet Edwin O'Hara fires the last shots.",
  "At 10 o'clock, the Stephen Hopkins sinks.",
  "But the Stier cannot make headway and does not answer the helm, and her own crew scuttle her.",
  "Captain Paul Buck of the Hopkins is dead, and so is O'Hara.",
  "Fifteen survivors drift in a lifeboat for 31 days, until they reach Brazil.",
  "Theirs is the only American merchant ship to sink a German surface combatant in this war."],
  "shots": [
   film(1, "lb_conv", 156, 4),
   film(1, "lb_conv", 68, 4),
   {"s": 2, "map": M_HOP},
   film(3, "wg_639", 141, 3),
   film(4, "lb_conv", 236, 4, note="2 MILES"),
   film(5, "lb_guard", 360, 4),
   film(6, "wg_639", 112, 3, sfx="tank_gun"),
   film(7, "lb_guard", 436, 4),
   film(7, "lb_guard", 447, 4, sfx="tank_gun"),
   film(8, "lb_guard", 474, 4.5, sfx="explosion_close"),
   film(9, "lb_guard", 494, 5, note="THE LAST SHOTS"),
   pic(10, STARR, label="A LIBERTY SHIP SINKING · 1943"),
   film(11, "lb_conv", 84, 5),
   pic(12, BURNETT, trim=[0, 0, 0, 0.06]),
   film(13, "lb_conv", 72, 6, note="31 DAYS"),
   pic(14, DEWEY, y=0.4)],
  "beats": [beat(8, (3.2, "lb_guard", 502, "explosion_far"), (3.0, "lb_conv", 108, None))]},

 {"title": "The Captain", "mode": "people", "stamp": ["LOS ANGELES"], "sentences": [
  "But two days later, in Los Angeles, the launch of another Liberty ship makes a different kind of history.",
  "She is the Booker T Washington, the first of 17 Liberty ships named after African Americans.",
  "The singer Marian Anderson christens her.",
  "Her captain is Hugh Mulzac.",
  "In 1918 he earned a master's certificate, the first ever issued to an African American.",
  "But for two decades, the only work he could get on ships was in the steward's department.",
  "Now he is offered a ship, and he refuses, because the crew is to be all black.",
  "The authorities relent.",
  "His crew is integrated, black and white, and it sails together.",
  "Those who began the experiment, Mulzac thinks, expect it to fail.",
  "It does not, and the ship carries over 18,000 troops around the world.",
  "After the war, Mulzac cannot get another ship as captain.",
  "He is blacklisted, and at 74 he is back at sea, as a night mate."],
  "shots": [
   film(1, "lb_born", 340, 5),
   pic(2, ANDERSON2, y=0.4),
   pic(3, ANDERSON, x=0.35, y=0.3, name="MARIAN ANDERSON", role="SINGER"),
   pic(4, MULZAC, reveal=[0.7, 0.3], name="HUGH MULZAC", role="CAPTAIN, SS BOOKER T. WASHINGTON"),
   pic(5, MULZAC, zoom=1.4, y=0.25, note="1918"),
   film(6, "lb_guard", 96, 5),
   film(7, "lb_born", 308, 4.5),
   film(8, "lb_mar", 384, 3),
   pic(9, BTW, label="THE OFFICERS OF THE BOOKER T. WASHINGTON"),
   pic(10, BTW, zoom=1.5, x=0.45, y=0.35),
   film(11, "lb_norm", 372, 5, note="18,000 TROOPS"),
   pic(12, SAMTWEED, zoom=1.2, trim=[0.05, 0.1, 0.05, 0.1]),
   film(13, "lb_guard", 426, 5)],
  "beats": [{"after": 7, "quote": {"text": "Under no circumstances will I command a Jim Crow.", "name": "HUGH MULZAC",
                                   "role": "CAPTAIN"},
             "shots": [{"dur": 4.0, "film": "lb_mar", "from": 382, "to": 386}]}]},

 {"title": "Broken in Two", "mode": "action", "stamp": ["PORTLAND"], "sentences": [
  "But on 16 January 1943, in Portland, Oregon, in calm weather, a new tanker cracks almost in half at her dock.",
  "The noise is heard at least a mile away.",
  "The Schenectady is not a Liberty ship, but she comes from a Kaiser yard, and ten other war-built ships have had major fractures before her.",
  "The whole city can see her.",
  "The Liberty ships crack too.",
  "In the war there are nearly 1,500 serious fractures, and twelve ships break in half without warning, three of them Liberty ships.",
  "On 24 November 1943, off the Aleutian Islands, the John P Gaines breaks in two, and 10 people die.",
  "Suspicion falls on the shipyards, on the haste and the inexperienced workers.",
  "In Cambridge, the scientist Constance Tipper shows that the fractures do not start in the welds.",
  "The steel itself turns brittle in the cold.",
  "In a riveted ship, a crack stops at the edge of a plate.",
  "But a welded hull is like one continuous sheet of steel, and the crack runs on.",
  "Many of the ships are also grossly overloaded.",
  "Twenty years earlier, Tipper won a Royal Society medal, and could not attend the dinner, because she was a woman.",
  "Her test makes ships safer, and modern ships avoid the square corners where the cracks began."],
  "shots": [
   pic(1, SCHEN, trim=[0, 0.02, 0, 0.05], label="PORTLAND, OREGON · JANUARY 1943"),
   film(2, "lb_mar", 543, 4),
   film(3, "lb_mar", 912, 4),
   film(3, "lb_mar", 936, 6, note="10 SHIPS BEFORE HER"),
   pic(4, DEWEY, zoom=1.4, x=0.6),
   film(5, "lb_norm", 416, 4),
   film(6, "lb_conv", 400, 5, note="1,500 FRACTURES"),
   pic(6, OVERMAN, y=0.45, label="A LIBERTY SHIP WRECK · 1944"),
   film(7, "lb_conv", 84, 4, stamp=["NOVEMBER 24"]),
   film(7, "lb_conv", 76, 4),
   film(8, "lb_mar", 1164, 4),
   film(8, "lb_mar", 1124, 3),
   film(9, "lb_mar", 1332, 4, note="NOT THE WELDS"),
   film(10, "lb_mar", 1244, 2),
   film(10, "lb_conv", 88, 3),
   pic(11, B09, y=0.5),
   film(12, "lb_gan", 231, 5),
   film(13, "lb_norm", 364, 5),
   pic(14, B12, y=0.35),
   film(15, "lb_gan", 171, 5)],
  "beats": [beat(7, (3.0, "lb_conv", 160, "submarine_hit"), (3.0, "lb_conv", 68, "low_rumble"))]},

 {"title": "The Secret Cargo", "mode": "action", "stamp": ["BARI"], "sentences": [
  "But in Bari, in Italy, on 2 December 1943, a Liberty ship waits with a secret in her holds.",
  "The John Harvey carries 2,000 mustard gas bombs.",
  "Captain Elwin Knowles wants to tell the port commander and unload them, but secrecy prevents it.",
  "That afternoon, Air Marshal Arthur Coningham says that the Germans have lost the air war.",
  "That evening the German bombers come, and the harbor is brightly lit.",
  "Two ammunition ships explode, and windows are shattered 7 miles away.",
  "In all, 28 merchant ships are sunk or destroyed.",
  "The John Harvey goes up in a huge explosion, and nearly all her crew, who could explain the danger, are killed.",
  "Sailors are covered in oil mixed with mustard.",
  "Within a day, 628 patients have symptoms of the poison, and the medical staff do not know the cause.",
  "Then a chemical warfare expert, Lieutenant Colonel Stewart Alexander, notes where each victim was, and it leads him to the John Harvey.",
  "By the end of the month, 83 of them are dead.",
  "Churchill orders the British documents purged, and the deaths are described as burns due to enemy action.",
  "But Alexander has kept tissue samples, and after the war they help to develop an early form of chemotherapy."],
  "shots": [
   pic(1, BROWNAIR, label="A LIBERTY SHIP · 1943"),
   {"s": 2, "map": M_BARI, "note": "2,000 BOMBS"},
   film(3, "lb_norm", 261.6, 4),
   film(4, "lb_norm", 280, 5),
   pic(5, JU88, label="A JUNKERS JU 88 · ITALY, 1943", stamp=["7:25 P.M."]),
   film(6, "convoy42", 196, 4, sfx="explosion_massive"),
   pic(7, BARI, x=0.4, label="BARI · 2 DECEMBER 1943", note="28 SHIPS"),
   pic(8, BARI, zoom=1.6, x=0.35, y=0.6, sfx="explosion_massive"),
   pic(9, ALGIERS, zoom=1.25, x=0.55, label="BURNING LIBERTY SHIPS · 1943"),
   film(10, "lb_norm", 86, 4, note="628 PATIENTS"),
   film(10, "lb_norm", 104, 5),
   film(11, "lb_norm", 116, 6),
   film(12, "lb_conv", 412, 5, note="83 DEAD"),
   film(13, "lb_mar", 86, 5),
   film(14, "lb_mar", 688, 5)],
  "beats": [{"after": 4, "quote": {"text": "I would consider it as a personal insult if the enemy should send so much as one plane over the city.",
                                   "name": "ARTHUR CONINGHAM", "role": "AIR MARSHAL · 2 DECEMBER 1943"},
             "shots": [{"dur": 4.0, "film": "lb_norm", "from": 288, "to": 292},
                       {"dur": 4.0, "film": "lb_norm", "from": 382, "to": 386}]},
            beat(8, (3.0, "menace", 36, "explosion_far"), (3.0, "lb_conv", 132, "low_rumble"))]},

 {"title": "Deadly Cargo", "mode": "action", "stamp": ["APRIL 20", "1944"], "sentences": [
  "But the cargo kills again: on 20 April 1944, near Algiers, a torpedo from a German plane hits the Paul Hamilton.",
  "She carries high explosives, bombs, and 580 men.",
  "Everyone on board is lost.",
  "Of the 580 men, only one body is recovered.",
  "Three months later, at Port Chicago in California, sailors are loading bombs into the Liberty ship E A Bryan.",
  "Most of them are African American.",
  "At 10:18 pm on 17 July, there is an explosion on the pier, and seconds later the ship goes up in a fireball seen for miles.",
  "All 320 men at the pier die instantly.",
  "A month later, the other sailors are marched to load munitions again, and hundreds refuse.",
  "They are afraid, and they will not work under the same officers and conditions as before.",
  "Fifty of them are convicted of mutiny and sentenced to 15 years.",
  "In 2024, the US Navy exonerates them."],
  "shots": [
   film(1, "convoy42", 74, 4),
   film(1, "lb_guard", 192, 4),
   film(2, "lb_norm", 354, 5, note="580 MEN"),
   pic(3, HAMILTON, label="SS PAUL HAMILTON · 20 APRIL 1944", sfx="explosion_massive"),
   pic(4, HAMILTON, zoom=1.5, x=0.75, y=0.35, note="ONE BODY"),
   pic(5, PCWORK, label="PORT CHICAGO · 1943"),
   pic(6, PCWORK, zoom=1.5, x=0.5, y=0.35),
   film(7, "lb_chi", 24, 3, stamp=["10:18 P.M."], sfx="explosion_massive"),
   film(7, "lb_chi", 99, 5),
   film(8, "lb_chi", 92, 5, note="320 MEN"),
   pic(9, PCBOX, y=0.6, trim=[0, 0.12, 0, 0]),
   film(9, "lb_chi", 207, 4),
   film(10, "lb_chi", 387, 5),
   pic(11, PC1, note="MUTINY"),
   film(12, "lb_chi", 231, 5)],
  "beats": [beat(8, (3.2, "lb_chi", 12, "explosion_far"), (3.2, "lb_chi", 138, None))]},

 {"title": "The Last Two", "mode": "people", "stamp": ["1945"], "sentences": [
  "But in 1945, when the war ends, more than 2,400 Liberty ships are still alive.",
  "They were designed to last five years.",
  "Greek owners buy hundreds of them, and men like Aristotle Onassis start their fleets with Liberty ships.",
  "One becomes the Grandcamp, and in 1947 her cargo of fertilizer explodes in Texas City and kills at least 581 people.",
  "Another, the Richard Montgomery, still lies in the Thames Estuary, with about 1,400 tonnes of explosives on board.",
  "Her masts stood above the water until September 2026.",
  "The Patrick Henry makes 12 wartime voyages, and is scrapped in Baltimore, where she was built.",
  "The Robert E Peary, built in less than five days, is scrapped in Baltimore too, in 1963.",
  "Only two Liberty ships still sail: the John W Brown and the Jeremiah O'Brien.",
  "In 1994, the O'Brien goes back to Normandy, the only large ship of the original fleet to return.",
  "Her engine was even filmed for Titanic.",
  "They were plain, slow and cheap, and out of 2,710, more than 2,400 outlived the war."],
  "shots": [
   pic(1, WSA, trim=[0, 0, 0.47, 0], note="2,400 SHIPS"),
   pic(2, RESERVE, y=0.5, label="A RESERVE FLEET, TEXAS · 1950"),
   pic(3, RESERVE, zoom=1.6, x=0.5, y=0.55),
   pic(4, TXCARS, trim=[0.05, 0.05, 0.05, 0.05], label="TEXAS CITY · APRIL 1947"),
   pic(4, TXBOAT, y=0.4),
   film(5, "lb_gan", 252, 5, note="1,400 TONNES"),
   film(6, "lb_conv", 280, 5),
   pic(7, PHENRY, zoom=1.2, x=0.5),
   film(8, "lb_peary", 23.1, 2.6),
   pic(8, B11, y=0.4),
   pic(9, BROWN16, label="SS JOHN W. BROWN"),
   pic(10, OBRIEN94, label="SS JEREMIAH O'BRIEN · 1994"),
   pic(11, OBRIEN, label="SAN FRANCISCO"),
   film(12, "lb_last", 80, 3.3),
   film(12, "lb_gan", 174, 3)]},
]

STORY = {
 "priority": 10, "format": "entire", "voice": "andrii", "intro_beats": True,
 "topic": "Liberty ship",
 "sources": ["Liberty ship", "SS Patrick Henry", "SS Robert E. Peary", "Henry J. Kaiser", "Kaiser Shipyards",
             "Richmond Shipyards", "Emergency Shipbuilding Program", "Ocean ship", "Sinking of the SS Stephen Hopkins",
             "German auxiliary cruiser Stier", "SS Booker T. Washington", "Hugh Mulzac", "SS Schenectady",
             "SS John P. Gaines", "Constance Tipper", "SS John Harvey", "Air raid on Bari", "SS Paul Hamilton",
             "Port Chicago disaster", "SS Richard Montgomery", "Texas City disaster", "SS Jeremiah O'Brien"],
 "title": "The ENTIRE History of the Liberty Ships in {N} Minutes",
 "question": "Was the four-day ship a stunt, or the weapon that beat the U-boats?",
 "summary": "From a plain British tramp steamer and Henry Kaiser's four-day ship to the hulls that broke in half, the "
            "secret mustard gas at Bari, Port Chicago and the last two that still sail, this is the whole story of the "
            "Liberty ships, told with archive film and President Roosevelt's own voice.",
 "tags": ["Liberty ships", "Liberty ship", "Henry Kaiser", "SS Robert E. Peary", "Bari air raid", "Port Chicago",
          "Constance Tipper", "SS Stephen Hopkins", "Hugh Mulzac", "merchant navy", "WW2 history", "world war 2"],
 "pronounce": {"Schenectady": "Skeh-neck-tuh-dee", "Mulzac": "Mull-zack", "Tannenfels": "Tah-nen-fels", "Stier": "Shteer",
               "Coningham": "Cunning-um", "Bari": "Bah-ree", "Permanente": "Per-muh-nen-tay", "Aleutian": "Uh-loo-shun",
               "Onassis": "Oh-nass-iss", "Grandcamp": "Grahn-kahm", "Peary": "Peer-ee"},
 "films": {
  "lb_peary": {"url": IA + "cubanc_000024/cubanc_000024_access.HD.mp4", "mono": True, "crop": "696:392:12:68",
               "credit": "Robert E. Peary launch (Richmond, November 1942): California Revealed (public domain, via Internet Archive)"},
  "lb_mar": {"url": IA + "chi_00005/chi_00005_access.HD.mp4", "crop": "628:353:6:62",
             "credit": "Tanker, Marinship Corporation (1944-45): California Audiovisual Preservation Project (public domain, via Internet Archive)"},
  "lb_last": {"url": IA + "ARC-39018/ARC-39018.mp4", "mono": True,
              "credit": "Last Liberty Ship Launched, United News (1944): OWI / NARA 39018 (public domain, via Internet Archive)"},
  "lb_gan": {"url": IA + "NPC-5153/NPC-5153.mov", "mono": True, "crop": "934:526:173:0",
             "credit": "Launching of SS Deborah Gannett, Bethlehem-Fairfield, Baltimore (1944): US Navy / NARA 428-NPC-5153 (public domain, via Internet Archive)"},
  "lb_guard": {"url": IA + "NPC-16151/NPC-16151.mp4", "mono": True,
               "credit": "Armed Guard on Merchant Ship (December 1941): US Navy / NARA 428-NPC-16151 (public domain, via Internet Archive)"},
  "lb_born": {"url": IA + "AShipIsBorn/AShipIsBorn.mp4", "mono": True, "crop": "512:288:8:56",
              "credit": "A Ship Is Born (1942): U.S. Maritime Commission and U.S. Coast Guard (public domain mark, via Internet Archive)"},
  "lb_conv": {"url": IA + "NPC-16082/NPC-16082.mp4", "mono": True,
              "credit": "Atlantic Convoy Underway (1941): US Navy / NARA 428-NPC-16082 (public domain, via Internet Archive)"},
  "lb_chi": {"url": IA + "NPC-4814/NPC-4814.mov", "mono": True, "crop": "1012:570:134:0",
             "credit": "Damage at Port Chicago (July 1944): US Navy / NARA 428-NPC-4814 (public domain, via Internet Archive)"},
  "lb_norm": {"url": IA + "NPC-4420/428-npc-4420.mov", "mono": True, "crop": "1012:570:134:0",
              "credit": "Invasion of France (June 1944): US Coast Guard / NARA 428-NPC-4420 (public domain, via Internet Archive)"},
  "convoy42": {"url": IA + "428-npc-16081/428-npc-16081.mp4", "mono": True, "crop": "704:360:8:60",
               "credit": "North Atlantic Convoy (1942): US Navy / NARA 428-NPC-16081 (public domain, via Internet Archive)"},
  "menace": {"url": IA + "1945-05-17_U-Boat_Menace_Ended/1945-05-17_U-Boat_Menace_Ended.mpeg", "mono": True,
             "crop": "688:344:16:68",
             "credit": "U-Boat Menace Ended (17 May 1945): Universal Newsreel (public domain, via Internet Archive)"},
  "wg_639": {"url": IA + "1942-12-02-Die-Deutsche-Wochenschau-639/1942-12-02-DieDeutscheWochenschauNr.63918m26s720x544.mkv",
             "mono": True, "crop": "690:388:15:75",
             "credit": "Die Deutsche Wochenschau 639 (December 1942) (public domain in the US as seized enemy property, via Internet Archive)"}},
 "period_audio": {
  "fdr": {"file": "Roosevelt Liberty Fleet Day 1941.mp3",
          "url": "https://upload.wikimedia.org/wikipedia/commons/9/91/Washington%2C_DC_-_Liberty_Fleet_Day_Message_-_DPLA_-_d509a29a080b15ab2783ffe488f2b37d.mp3",
          "speaker": "Franklin D. Roosevelt", "date": "SEPTEMBER 1941",
          "credit": "President Roosevelt, Liberty Fleet Day Message (September 1941): NARA / DPLA (public domain, Wikimedia Commons)",
          "text": "And among them is the first Liberty ship, the Patrick Henry."}},
 "pre": [{"dur": 2.8, "film": "lb_peary", "from": 7.1, "to": 8.9, "stamp": ["NOVEMBER 12", "1942"], "sfx": "ov/ship_horn"}],
 "whole": [KAISER, MULZAC, ENGINE, B03, B04, B05, B08, B09, B10, B11, B12],
 "tone": [KAISER, MULZAC],
 "thumb": {"file": DEWEY},
 "cover": {"file": OVERMAN, "x": 0.5, "y": 0.0, "zoom": 1.1, "color": False,
           "text": ["HISTORY OF THE", "LIBERTY SHIPS", "IN {N} MINUTES"], "key": ["LIBERTY", "SHIPS"], "sizes": [96, 150, 96],
           "mono": True},
 "promos": [
  {"id": "liberty_bari", "chapter": 8,
   "sentences": ["A Liberty ship waits in Italy with a secret cargo.",
                 "Her captain may not tell the port.",
                 "Then bombers hit the harbor, and the secret spills out: mustard gas."],
   "shots": [pic(1, BROWNAIR), film(2, "lb_norm", 280, 4), pic(3, BARI, x=0.4)],
   "top": "THE SECRET OF|THE JOHN HARVEY", "key": ["SECRET"],
   "cta": {"kind": "redacted", "line": "SHE CARRIES", "hidden": "MUSTARD GAS"}, "end": "WHAT DID SHE CARRY?",
   "name": "The Liberty Ship With a Secret in Her Holds"},
  {"id": "liberty_half", "chapter": 7,
   "sentences": ["In calm weather, a new ship cracks almost in half.",
                 "Everyone blames the welders.",
                 "Then a scientist in Cambridge finds the real cause: the steel itself."],
   "shots": [pic(1, SCHEN, trim=[0, 0.02, 0, 0.05]), film(2, "lb_mar", 1164, 4), film(3, "lb_mar", 1228, 5)],
   "top": "WHY DID SHE|BREAK IN HALF?", "key": ["HALF"],
   "cta": {"kind": "number", "big": "1,500", "line": "FRACTURES. WHAT WAS THE CAUSE?"}, "end": "WHAT WAS THE CAUSE?",
   "name": "Why the Ships of World War II Broke in Half"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "liberty.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
import collections
n = collections.Counter(s["file"] for c in C for s in c["shots"] + [x for b in c.get("beats", []) for x in b["shots"]] if s.get("file"))
print("photos used > 2:", {k: v for k, v in n.items() if v > 2})
