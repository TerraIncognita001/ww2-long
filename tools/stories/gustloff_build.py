"""The Wilhelm Gustloff, Nov 24 (Andrii: genre 2, sea disasters; Thu 26.11 02:00 London): a hand story in the NEW
FORMAT (CLAUDE.md, Nov 23): voice No. 3, the narrator at ~3 s, Hitler's last radio address (30 January 1945, the day
of the sinking) as a beat after sentence 1, one open question (who is to blame? answered in the last chapter).
Facts: the Wikipedia articles of STORY['sources'] (whole, sources/*.txt). The death toll is disputed: both counts told.
Films (Internet Archive): Schiff ohne Klassen (1938), Die Deutsche Wochenschau 639, 751, 752, 754, NPC-3844, NPC-3641 (US
Navy). Run: python tools/stories/gustloff_build.py"""
import json, pathlib

GIRLS = "KdF-Schiff Wilhelm Gustloff 1938.jpg"
POOL = 'Bundesarchiv Bild 146-1988-107-05, KdF-Schiff "Wilhelm Gustloff", Schwimmbad.jpg'
DANZIG = 'Bundesarchiv Bild 183-H27992, Lazarettschiff "Wilhelm Gustloff" in Danzig.jpg'
STETTIN = 'Bundesarchiv B 145 Bild-P094443, Stettin, "Wilhelm Gustloff" als Lazarettschiff.jpg'
HOSP_SIDE = 'Bundesarchiv Bild 183-L12207, Lazarettschiff "Wilhelm Gustloff".jpg'
HOSP_BOW = 'Bundesarchiv Bild 183-L12212, Lazarettschiff "Wilhelm Gustloff".jpg'
HOSP_LIFT = 'Bundesarchiv Bild 183-L05763, Lazarettschiff "Wilhelm Gustloff".jpg'
HOSP_CARS = 'Bundesarchiv Bild 183-L12211, Lazarettschiff "Wilhelm Gustloff".jpg'
HOSP_BEDS = 'Bundesarchiv Bild 183-L12208, Lazarettschiff "Wilhelm Gustloff".jpg'
OSLO = 'Bundesarchiv Bild 121-0665, Oslo, "Wilhelm Gustloff".jpg'
MAN = "Wilhelm-Gustloff.jpg"
FELDPOST = "Feldpost 6 1945.png"
STAMP_M = "RUSMARKA-1926.jpg"
STAMP_S13 = "Russian stamp 304 S-13 1996.jpg"
UKAZ = "Указ Президента СССР о присвоении звания Героя Советского Союза.png"
CREW = "Shch-402's crew (1942).jpg"
S54 = "Soviet submarine S-54 in 1942.jpg"
S55 = "Soviet submarine S-55 in 1942.jpg"
S54B = "Soviet submarine S-54 in 1942 2.jpg"
M1 = "Soviet submarine M-1 1934.jpg"
CART = "Bundesarchiv Bild 175-S00-00326, Flüchtlinge aus Ostpreußen auf Pferdewagen.jpg"
DECK = "Bundesarchiv Bild 146-1972-092-33, Flüchtlinge auf Schiff.jpg"
PILLAU = "Bundesarchiv Bild 146-1989-033-33, Pillau, Hafen, Flüchtlinge.jpg"
PILLAU_SAILORS = "Bundesarchiv Bild 146-1989-033-35, Pillau, Hafen, Marinesoldaten, Flüchtlinge.jpg"
ASHORE = "Bundesarchiv Bild 146-2001-019-10, Ausschiffung von Flüchtlingen.jpg"
TREK = "Bundesarchiv Bild 146-1979-084-06, Flüchtlingstreck.jpg"
GANGWAY = "Bundesarchiv Bild 146-2004-0127, Ausschiffung von Flüchtlingen.jpg"
EMBARK = "Bundesarchiv Bild 146-1972-093-51, Pillau, Einschiffung von Flüchtlingen.jpg"
QUAY = "Bundesarchiv Bild 146-1972-093-59, Pillau, Einschiffung von Flüchtlingen.jpg"
STEUBEN = "General-Von-Steuben-Franz-Grasser0df hauptkatalog 0760980.jpg"
T35 = "T 35 as DD 935 in US seas August 1945.jpg"
HIPPER = "German cruiser Admiral Hipper off Norway 1942.jpg"
DOENITZ = "Karl Dönitz.jpg"
GDYNIA_AIR = "Aerial reconnaissance photo of Gdynia, Poland, in June 1942 (NH 91655).jpg"
GDYNIA = "Henryk Poddębski - Gdynia - port (131-D-1-4).jpg"

H_SRC = "ADOLF HITLER · RADIO, 30 JANUARY 1945 · 'I EXPECT ALL WOMEN AND GIRLS TO SUPPORT THIS FIGHT'"

M_ICE = {"places": [{"label": "KÖNIGSBERG", "lat": 54.71, "lon": 20.51, "side": "blue"},
                    {"label": "ELBING", "lat": 54.16, "lon": 19.40, "side": "red"},
                    {"label": "GOTENHAFEN", "lat": 54.52, "lon": 18.53, "side": "blue"}],
         "routes": [[0, 2, "blue", 0.12]], "pad": 0.5}
M_ROUTE = {"places": [{"label": "GOTENHAFEN", "lat": 54.52, "lon": 18.53, "side": "blue"},
                      {"label": "S-13", "lat": 55.07, "lon": 17.42, "side": "red"},
                      {"label": "KIEL", "lat": 54.32, "lon": 10.14, "side": "blue"}],
           "routes": [[0, 1, "blue", -0.2]], "pad": 0.4}


def film(s, key, x, n=6, **k):
    return {"s": s, "film": key, "from": x, "to": x + n, **k}


def pic(s, f, **k):
    return {"s": s, "file": f, **k}


def beat(after, *shots):
    return {"after": after, "shots": [{"dur": d, "film": f, "from": x, "to": x + d, **({"sfx": s} if s else {})}
                                      for d, f, x, s in shots]}


C = [
 {"title": "", "mode": "action", "sentences": [
  "On 30 January 1945, in the Baltic Sea, three torpedoes hit the Wilhelm Gustloff, a ship full of people running from the war.",
  "More than 10,000 may be on board, and 1,252 are rescued.",
  "The man who fires is Alexander Marinesko, a Soviet captain who is waiting for his own trial.",
  "This is the deadliest sinking of a single ship in history, and who is to blame for it?",
  "It all begins with a ship built for holidays."],
  "shots": [
   film(1, "wg_752", 230.9, 3, stamp=["BALTIC SEA"]),
   film(1, "wg_752", 219.5, 4),
   film(2, "wg_752", 215.9, 3.4, note="10,000 ON BOARD"),
   pic(3, STAMP_M, zoom=1.5, x=0.5, y=0.45, name="ALEXANDER MARINESKO", role="CAPTAIN, SUBMARINE S-13"),
   film(4, "wg_752", 261.8, 2.2),
   film(4, "wg_ship", 1253, 4),
   film(5, "wg_ship", 208, 6)],
  "beats": [{"after": 1, "audio": {"src": "hitler", "from": 12.25, "to": 19.95}, "source": H_SRC, "shots": [
   {"dur": 4.0, "film": "wg_754", "from": 308.6, "to": 312, "source": H_SRC},
   {"dur": 3.7, "film": "wg_754", "from": 319, "to": 322, "source": H_SRC}]}]},

 {"title": "The Holiday Ship", "mode": "people", "stamp": ["5 MAY 1937"], "sentences": [
  "But on 5 May 1937, the ship that is launched at Blohm and Voss is made to be loved.",
  "She is the first cruise ship built for Strength Through Joy, the Nazi organization that gives workers their holidays.",
  "There are concerts, sunny decks and a swimming pool.",
  "Her real job is to show the world a more acceptable image of the Reich.",
  "She is meant to be called the Adolf Hitler.",
  "Then Wilhelm Gustloff, the leader of the Swiss Nazis, is shot dead by a Jewish student, David Frankfurter.",
  "At the memorial service Hitler sits next to the widow, and the ship gets the dead man's name.",
  "In April 1938, in a storm, the British freighter Pegaway is sinking, and it is the Gustloff that comes.",
  "One by one, 19 men jump into the sea, and her lifeboat takes them all.",
  "That same month she anchors off Tilbury, in England, as a floating polling station.",
  "Germans and Austrians vote on board for the union of their countries: 1,968 for it, and ten against.",
  "On the cruise to Madeira, her captain, Carl Lübbe, dies on the bridge of a heart attack.",
  "First Officer Friedrich Petersen takes over, and he will be her captain again, on the last voyage.",
  "By August 1939, she has carried over 80,000 people on 60 voyages."],
  "shots": [
   film(1, "wg_ship", 188, 6),
   film(2, "wg_ship", 603, 4),
   film(3, "wg_ship", 810, 5),
   pic(4, GIRLS, label="ABOARD THE WILHELM GUSTLOFF · 1938"),
   film(5, "wg_ship", 1242, 5),
   pic(6, MAN, reveal=[0.6, 0.25], name="WILHELM GUSTLOFF", role="LEADER OF THE SWISS NAZI PARTY"),
   film(7, "wg_ship", 950.9, 6),
   film(8, "wg_639", 269.5, 3.5, sfx="storm_wind"),
   film(9, "wg_639", 273, 3, note="19 MEN SAVED"),
   film(10, "wg_ship", 211, 3.2),
   pic(11, OSLO),
   film(12, "wg_ship", 147.9, 3, label="1938"),
   film(13, "wg_ship", 250, 2.5),
   film(13, "wg_ship", 1239, 3),
   film(14, "wg_ship", 824, 7, note="80,000 PASSENGERS")]},

 {"title": "Grey", "mode": "people", "stamp": ["SEPTEMBER 1939"], "sentences": [
  "But in September 1939, the holidays are over, and the white ship becomes a hospital.",
  "For a year she takes the wounded on board, with a green stripe along her side.",
  "Then, in November 1940, the beds are carried off, and she is painted the grey of the navy.",
  "She is tied up at Gdynia, a Polish port that the Germans have taken, and renamed Gotenhafen.",
  "About 1,000 trainees live on her, the men of the Second Submarine Training Division.",
  "They are learning how to sink ships.",
  "In 1942, a film crew comes to the harbor.",
  "The Nazis are making a movie about the Titanic, and another liner, the Cap Arcona, plays the doomed ship.",
  "The submarine men are the extras.",
  "They act in the most famous shipwreck in the world, and then they go back to their own ship.",
  "The Gustloff lies at that pier for more than four years."],
  "shots": [
   pic(1, DANZIG, label="HOSPITAL SHIP · DANZIG 1939"),
   pic(2, HOSP_BEDS),
   pic(3, HOSP_LIFT, y=0.4),
   pic(4, GDYNIA_AIR, label="GOTENHAFEN · 1942"),
   film(5, "wg_639", 17.5, 2, note="1,000 TRAINEES"),
   film(5, "wg_639", 236.8, 3),
   film(6, "wg_639", 26, 5),
   pic(7, GDYNIA, trim=[0, 0, 0, 0.03]),
   film(8, "wg_639", 157.8, 2.2),
   film(8, "wg_639", 152.4, 3),
   film(9, "wg_639", 240, 3),
   film(10, "wg_639", 246, 3.5),
   pic(10, HOSP_BOW, y=0.35),
   pic(11, STETTIN)]},

 {"title": "Over the Ice", "mode": "action", "stamp": ["EAST PRUSSIA"], "sentences": [
  "But in January 1945, in East Prussia, it is already too late to leave.",
  "The Red Army attacks on the 13th, and it comes fast.",
  "Nazi propaganda has shown everyone what Soviet soldiers did in the village of Nemmersdorf.",
  "Still, the man who rules here, Gauleiter Erich Koch, forbids the people to go.",
  "Anyone who tries to flee without permission is to be shot.",
  "He waits until 20 January.",
  "Three days later, Soviet troops reach the coast near Elbing, and the land route to the west is cut.",
  "There is one way left: over the frozen water of the Vistula Lagoon.",
  "Long columns of wagons go out on the ice, most of them with women and children.",
  "Soviet planes attack them.",
  "Many wagons break through the ice where the bombs have fallen.",
  "Thousands die on the way.",
  "The others reach the harbors, Danzig and Gotenhafen, and look for a ship."],
  "shots": [
   film(1, "wg_754", 301.9, 3.5, label="VISTULA LAGOON · 1945"),
   film(2, "wg_752", 197, 4),
   film(3, "wg_751", 137, 5),
   film(4, "wg_751", 148.8, 1.6),
   film(4, "wg_751", 153, 4),
   film(5, "wg_752", 192, 5),
   film(6, "wg_751", 142.7, 3.5),
   {"s": 7, "map": M_ICE},
   film(8, "wg_754", 295, 5),
   film(9, "wg_754", 311.7, 1.6),
   film(9, "wg_754", 314.7, 1.8),
   film(10, "wg_754", 306, 2, sfx="explosion_far"),
   film(11, "wg_754", 303, 3),
   pic(12, TREK),
   film(13, "wg_751", 165.9, 2.3),
   pic(13, CART)],
  "beats": [beat(12, (3.0, "wg_754", 316, "storm_wind"), (3.2, "wg_754", 297, None))]},

 {"title": "The Passengers", "mode": "people", "stamp": ["GOTENHAFEN"], "sentences": [
  "But in Gotenhafen, the biggest hope is a ship that has not moved for four years.",
  "On 23 January, Grand Admiral Karl Dönitz gives the order to evacuate by sea: Operation Hannibal.",
  "The Gustloff has to go, and everyone wants to be on her.",
  "There are 918 men of the training division, going to Kiel.",
  "There are 373 women of the naval auxiliary, and they are lodged in the drained swimming pool.",
  "There are wounded soldiers, Gestapo men, Nazi officials with their families, and thousands of refugees.",
  "The lists say 6,050, but many people board without being on any list.",
  "Heinz Schön is a member of the crew, and he will survive to count them.",
  "After years of research, his number is 10,582.",
  "The German documents say 4,922, and the argument goes on to this day.",
  "Inside it is so hot and so full that people take off their life jackets, against orders.",
  "At 12:30 in the afternoon of 30 January, she leaves.",
  "It is the birthday of the man whose name is on her bow."],
  "shots": [
   pic(1, GDYNIA_AIR, zoom=1.5, x=0.3, y=0.6),
   pic(2, DOENITZ, reveal=[0.25, 0.6], name="KARL DÖNITZ", role="GRAND ADMIRAL, GERMAN NAVY"),
   pic(3, QUAY, label="REFUGEES · 1945"),
   film(4, "wg_639", 203.9, 2.6, note="918 SUBMARINERS"),
   pic(5, POOL, card=True, note="373 WOMEN"),
   pic(6, HOSP_CARS),
   film(6, "wg_751", 168.8, 2.2),
   film(7, "wg_751", 179, 4, note="6,050?"),
   pic(8, EMBARK),
   pic(9, DECK, note="10,582?"),
   film(10, "wg_751", 182.9, 3, note="4,922?"),
   film(11, "wg_ship", 262.9, 1.8),
   film(11, "wg_ship", 247, 2.5),
   film(12, "wg_752", 212.9, 2, stamp=["12:30 P.M."], sfx="ov/ship_horn"),
   film(13, "wg_ship", 200.7, 1.8)],
  "beats": [beat(7, (5.0, "wg_752", 216.5, None))]},

 {"title": "Four Captains", "mode": "action", "stamp": ["30 JANUARY 1945"], "sentences": [
  "But on 30 January 1945, the Gustloff has four captains, and they do not agree.",
  "Friedrich Petersen, the man who once replaced the dead captain, commands the ship.",
  "Two more come from the merchant marine.",
  "The fourth, Lieutenant Commander Wilhelm Zahn, leads the submarine men, and he knows how a submarine hunts.",
  "Zahn wants to stay close to the shore, in shallow water, with no lights.",
  "Petersen says no, and turns out into deep water.",
  "Another liner should be with them, the Hansa, and two torpedo boats.",
  "The Hansa breaks down, and so does one of the torpedo boats.",
  "One escort is left, the Löwe, and ice has put her submarine sensor out of action.",
  "Her anti-aircraft guns are frozen too.",
  "Then a radio message comes: German minesweepers are on the way toward them.",
  "Petersen is afraid of a collision in the dark.",
  "He turns on the navigation lights, red and green.",
  "Now she is easy to see."],
  "shots": [
   film(1, "wg_752", 229, 1.2),
   film(1, "wg_752", 232, 4),
   film(2, "wg_ship", 151, 1.4),
   film(2, "wg_ship", 143, 2.5),
   film(3, "wg_ship", 117.8, 1.5),
   film(4, "wg_639", 112, 3, note="WILHELM ZAHN"),
   film(4, "wg_639", 123, 2.5),
   film(5, "wg_639", 128, 4, note="NO LIGHTS"),
   {"s": 6, "map": M_ROUTE},
   film(7, "wg_752", 226.2, 2.4),
   film(8, "wg_ship", 159.8, 4),
   film(9, "wg_752", 255, 3),
   film(10, "wg_752", 245, 2),
   film(11, "wg_639", 120.8, 2, sfx="ov/morse_code"),
   film(12, "wg_752", 238, 1.5),
   film(13, "wg_ship", 1256, 4, note="LIGHTS ON"),
   film(14, "wg_ship", 1259, 3)],
  "beats": [beat(13, (2.2, "wg_752", 261.8, "ov/ocean_waves"), (3.0, "wg_ship", 1253.5, None))]},

 {"title": "The Captain on Trial", "mode": "people", "stamp": ["HANKO"], "sentences": [
  "But in Hanko, in Finland, on 5 January, a Soviet captain goes missing.",
  "Alexander Marinesko is 32, the son of a Romanian sailor and a Ukrainian mother, born in Odessa.",
  "His first boat was rated the best of its brigade in torpedo firing, and the head of the navy gave him a gold watch.",
  "He also drinks.",
  "The party threw him out for it, and took him back.",
  "Now he leaves his submarine, S-13, without permission, and is caught drinking with another officer.",
  "In wartime this counts as desertion, and he can be sentenced to death.",
  "The fleet decides to put him before a tribunal.",
  "Marinesko asks for one thing: to make up for it in battle.",
  "No new captain can be found quickly, so Admiral Vladimir Tributs puts off the trial until after the next patrol.",
  "S-13 is later described as the only penal submarine in the Soviet Navy.",
  "On 11 January she sails.",
  "From the 21st to the 29th, Marinesko finds several targets, and attacks none.",
  "He has nothing yet to show his judges."],
  "shots": [
   pic(1, S54B, label="SOVIET S-CLASS SUBMARINE"),
   pic(2, STAMP_M, card=True, name="ALEXANDER MARINESKO", role="CAPTAIN, SUBMARINE S-13"),
   pic(3, M1, label="SOVIET M-CLASS SUBMARINE"),
   pic(4, CREW, x=0.4, label="A SOVIET SUBMARINE CREW · 1942"),
   pic(5, CREW, zoom=1.5, x=0.7, y=0.55),
   pic(6, STAMP_S13, card=True, note="S-13"),
   pic(7, S55, trim=[0, 0.12, 0, 0.1]),
   pic(8, S54, trim=[0, 0.12, 0, 0.12]),
   film(9, "wg_639", 182, 2),
   film(10, "menace", 40, 3),
   film(10, "menace", 36, 4),
   film(11, "wg_639", 172, 5),
   film(12, "wg_silent", 96, 4),
   film(13, "wg_639", 141, 3),
   film(13, "wg_639", 166.9, 3.5),
   film(14, "wg_silent", 126, 5)]},

 {"title": "Three Torpedoes", "mode": "action", "stamp": ["S-13"], "sentences": [
  "But that evening, S-13 is on the surface, and she sees a ship with its lights on.",
  "The Gustloff goes straight ahead, at a constant speed, without zigzagging.",
  "For two hours, Marinesko follows.",
  "He is on the side of the open sea, where an attack can be expected.",
  "So he steers around her stern, to the side of the shore, where it is not.",
  "At around nine in the evening, he orders four torpedoes.",
  "Three leave their tubes, and all three hit.",
  "The first hits the bow, and the watertight doors lock before the sleeping crew can get out.",
  "The second hits the swimming pool.",
  "The tiles are torn off, and fly through the room.",
  "Of the 373 women there, three survive.",
  "The third hits the engine room.",
  "All power and all communications are gone."],
  "shots": [
   film(1, "wg_ship", 1257, 4),
   film(2, "wg_ship", 932.5, 6),
   film(3, "wg_silent", 84, 5),
   film(4, "wg_639", 264.3, 2.5),
   film(5, "wg_silent", 111, 5),
   film(6, "wg_sub", 40, 4, stamp=["9:00 P.M."]),
   film(7, "wg_sub", 62, 4),
   film(8, "wg_ship", 194, 4, note="THE BOW"),
   film(9, "wg_ship", 796, 3, note="THE POOL", sfx="submarine_hit"),
   pic(10, POOL, zoom=1.0, y=0.7),
   film(11, "wg_ship", 812, 3.5, note="3 OF 373"),
   film(12, "wg_ship", 163, 4, note="THE ENGINES", sfx="submarine_hit"),
   film(13, "wg_ship", 175, 1.8),
   film(13, "wg_ship", 1259.2, 3)],
  "beats": [beat(7, (3.0, "wg_silent", 57, "explosion_massive"), (3.0, "wg_ship", 1257, "explosion_far"))]},

 {"title": "Fifty Minutes", "mode": "action", "stamp": ["FIFTY MINUTES"], "sentences": [
  "But it takes about fifty minutes for the Gustloff to go down, and for those inside it is not enough.",
  "On the stairs, people are trampled in the panic.",
  "Reportedly, only nine lifeboats can be lowered, because the others are frozen in place.",
  "After 20 minutes, the ship leans over so far that boats from the high side crash against her hull.",
  "The people in them fall into the sea.",
  "The air is at least ten degrees below zero, and ice floes cover the water.",
  "Most of the victims die of the cold.",
  "In less than 40 minutes, she is lying on her side.",
  "Ten minutes later she sinks, bow first, in 44 meters of water.",
  "The heavy cruiser Admiral Hipper arrives, fears a submarine attack, and leaves.",
  "Her torpedo boat, the T36, stays, and saves 564 people.",
  "The Löwe saves 472.",
  "A patrol boat finds one survivor: a baby.",
  "In all, 1,252 are rescued, and 13 of them die soon after."],
  "shots": [
   film(1, "wg_ship", 135.3, 1.5),
   film(1, "wg_ship", 1254, 4),
   film(2, "wg_ship", 245, 4),
   pic(3, HOSP_CARS, zoom=1.6, x=0.45, y=0.2, note="NINE LIFEBOATS"),
   pic(4, HOSP_SIDE, trim=[0, 0, 0, 0.05]),
   pic(5, HOSP_SIDE, zoom=1.6, x=0.6, y=0.35),
   film(6, "wg_752", 224.8, 1.4),
   film(6, "wg_752", 226.6, 1.8),
   film(7, "wg_752", 233, 4),
   film(8, "wg_ship", 1260, 2),
   film(9, "wg_752", 261.5, 2.4),
   film(10, "wg_752", 239.6, 2.3, label="GERMAN HEAVY CRUISER · 1945"),
   pic(10, HIPPER),
   pic(11, T35, label="SISTER SHIP OF T36", note="564 SAVED"),
   film(12, "wg_752", 256, 3),
   film(13, "wg_752", 247, 2),
   film(13, "wg_639", 263, 2.5),
   pic(14, ASHORE, trim=[0, 0, 0, 0.04], note="1,252 RESCUED")],
  "beats": [beat(9, (2.2, "wg_752", 261.8, "storm_wind"), (3.0, "wg_639", 272, "ov/ocean_waves")),
            {"after": 13, "shots": [{"dur": 5.5, "file": FELDPOST, "focus": [0.69, 0.55, 0.845, 0.71], "sfx": "typewriter"}]}]},

 {"title": "Eleven Days Later", "mode": "action", "stamp": ["10 FEBRUARY"], "sentences": [
  "But on 10 February, eleven days later, S-13 is still out there, and another liner comes.",
  "She is the Steuben, full of wounded soldiers and refugees.",
  "She is darkened, and she changes her course again and again.",
  "Marinesko hunts her for more than four hours, much of the time by listening.",
  "He thinks she is a cruiser, the Emden.",
  "He fires two torpedoes, and she sinks.",
  "About 4,500 people are killed.",
  "In April, another submarine sinks the Goya, with the loss of over 6,000.",
  "And still the ships go out.",
  "In fifteen weeks, they carry more than 800,000 civilians and 350,000 soldiers over the Baltic Sea.",
  "It is one of the largest evacuations by sea in history."],
  "shots": [
   film(1, "wg_silent", 102, 5),
   pic(2, STEUBEN, label="GENERAL VON STEUBEN"),
   pic(3, STEUBEN, zoom=1.5, x=0.6, y=0.5),
   film(4, "wg_639", 101, 4),
   film(5, "wg_639", 158.4, 1.5),
   film(6, "wg_sub", 73, 4, sfx="submarine_hit"),
   film(7, "wg_639", 655.2, 2, note="4,500 DEAD"),
   film(8, "wg_silent", 120, 5),
   pic(9, PILLAU, label="PILLAU"),
   film(10, "wg_752", 226.2, 2.3),
   pic(10, PILLAU_SAILORS),
   pic(11, GANGWAY)],
  "beats": [beat(6, (3.0, "wg_silent", 60, "explosion_far"), (3.0, "wg_639", 660, None))]},

 {"title": "Not Suitable to Be a Hero", "mode": "people", "stamp": ["TURKU"], "sentences": [
  "But in Turku, where S-13 comes home, they do not know what to do with her captain.",
  "The trial is dropped, and his commander asks for the highest award, Hero of the Soviet Union.",
  "He gets a lower one, the Order of the Red Banner.",
  "Soviet propaganda says that the women on the Gustloff were SS personnel from the concentration camps, and it is not true.",
  "In 1945, Marinesko goes on drinking, loses his submarine and is demoted.",
  "In 1949, he is sentenced to three years for taking peat, and even a bed, from the institute where he works.",
  "He dies of cancer in 1963, at the age of 50.",
  "In 1990, Mikhail Gorbachev names him a Hero of the Soviet Union."],
  "shots": [
   pic(1, S54, zoom=1.5, x=0.6, y=0.45, trim=[0, 0.12, 0, 0.12]),
   pic(2, S54B, zoom=1.4, x=0.6, y=0.5),
   pic(3, STAMP_S13, zoom=1.3, x=0.4),
   film(4, "wg_639", 188, 1),
   film(4, "wg_639", 255, 2),
   film(5, "menace", 64, 4),
   pic(6, S55, zoom=1.5, x=0.6, y=0.5, trim=[0, 0.12, 0, 0.1]),
   pic(7, M1, zoom=1.4, x=0.55, y=0.6),
   {"s": 8, "file": UKAZ, "card": True, "note": "HERO, 1990"}]},

 {"title": "Who Is to Blame?", "mode": "people", "stamp": ["GERMANY"], "sentences": [
  "But in Germany, the navy opens an inquiry against just one officer, Wilhelm Zahn, the captain who wanted no lights.",
  "All four captains have survived.",
  "The Reich collapses before there is an answer.",
  "So was it a crime?",
  "The Gustloff had anti-aircraft guns, and she was not marked as a hospital ship.",
  "She carried men of the navy, and under international law, nothing protected her.",
  "The naval historian Miroslav Morozov calls her a legitimate military target.",
  "The German writer Günter Grass says it in his own way.",
  "Nobody knows how many died.",
  "It may be 3,700, and by Heinz Schön's count it is 9,343 men, women and children.",
  "She lies off the Polish coast, as a war grave, and no one may dive within 500 meters.",
  "And Gauleiter Koch, who had forbidden the people to leave, was among the first to flee.",
  "She was built to show the happy face of the Reich, and she went down with the people it had told to stay."],
  "shots": [
   film(1, "wg_639", 224, 3),
   film(1, "wg_639", 134, 1.8),
   film(2, "wg_ship", 105, 4),
   film(3, "wg_751", 258, 5),
   film(4, "wg_ship", 932.5, 5),
   film(5, "wg_752", 253, 2),
   pic(5, OSLO, zoom=1.4, x=0.3, y=0.5),
   film(6, "wg_639", 243.2, 2.6),
   pic(7, DANZIG, zoom=1.4, x=0.4, y=0.4),
   pic(8, DECK, zoom=1.2, y=0.3),
   pic(9, EMBARK, zoom=1.4, x=0.35, y=0.6),
   film(10, "wg_752", 220, 3, note="3,700 OR 9,343"),
   pic(10, QUAY, zoom=1.5, x=0.4, y=0.7),
   film(11, "wg_752", 261.8, 2.1, note="WAR GRAVE"),
   film(11, "wg_639", 270, 3),
   film(12, "wg_754", 301.9, 3.4),
   film(13, "wg_ship", 625, 3.5),
   film(13, "wg_ship", 1253, 4)],
  "beats": [{"after": 8, "quote": {
    "text": "They said the tragedy of Wilhelm Gustloff was a war crime. It wasn't. It was terrible, but it was a result of war, a terrible result of war.",
    "name": "GÜNTER GRASS", "role": "THE NEW YORK TIMES, 2003"},
   "shots": [{"dur": 5.0, "film": "wg_752", "from": 233, "to": 237}, {"dur": 5.0, "file": GANGWAY, "zoom": 1.4}]}]},
]

IA = "https://archive.org/download/"
WO = "(via Internet Archive)"
STORY = {
 "priority": 10,
 "format": "story",
 "voice": "andrii",
 "intro_beats": True,
 "topic": "MV Wilhelm Gustloff",
 "sources": ["MV Wilhelm Gustloff", "Alexander Marinesko", "Soviet submarine S-13", "Operation Hannibal",
             "Evacuation of East Prussia", "Wilhelm Gustloff", "SS General von Steuben", "MV Goya", "Strength Through Joy",
             "SS Cap Arcona", "East Prussian offensive"],
 "title": "Wilhelm Gustloff: The Deadliest Sinking in History, and Who Was to Blame",
 "question": "The Wilhelm Gustloff: whose fault was it, Petersen's lights, Marinesko's torpedoes, or Koch's orders?",
 "summary": ("On 30 January 1945, the Soviet submarine S-13 sank the Wilhelm Gustloff in the Baltic Sea, a former Nazi "
             "cruise ship full of refugees from East Prussia. This is the story of the ship, the four captains who could "
             "not agree, the submarine captain awaiting his own trial, and the question of who was to blame."),
 "tags": ["Wilhelm Gustloff", "deadliest shipwreck", "Operation Hannibal", "Alexander Marinesko", "S-13 submarine",
          "East Prussia 1945", "sea disaster", "Steuben", "Goya", "Baltic Sea", "Titanic", "Strength Through Joy",
          "WW2 documentary", "World War 2", "history"],
 "pronounce": {"Wilhelm Gustloff": "Vill-helm Goost-loff", "Gustloff": "Goost-loff", "Wilhelm": "Vill-helm",
               "Marinesko": "Mah-ree-ness-ko", "Gotenhafen": "Goat-en-hah-fen", "Löwe": "Lurr-veh", "Zahn": "Tsahn",
               "Schön's": "Shurns", "Schön": "Shurn", "Dönitz": "Durr-nits", "Tributs": "Tree-boots",
               "Lübbe": "Loo-beh", "Steuben": "Shtoy-ben", "Gauleiter": "Gow-lighter", "Koch": "Kokh",
               "Gdynia": "Guh-din-ya", "Elbing": "El-bing", "Grass": "Grahss", "Günter": "Goon-ter", "Reich": "Rike",
               "Hansa": "Han-za", "Morozov": "Mah-roh-zoff", "Turku": "Toor-koo", "Blohm and Voss": "Blome and Foss",
               "T36": "T thirty-six", "S-13": "S thirteen"},
 "films": {
  "wg_ship": {"url": IA + "1938-SchiffOhneKlassen-DieWilhelmGustloff/1938-SchiffOhneKlassen-DieWilhelmGustloff.avi",
              "mono": True, "crop": "464:261:86:20", "credit": "Schiff ohne Klassen: Die Wilhelm Gustloff (1938) " + WO},
  "wg_752": {"url": IA + "1945-02-17-Die-Deutsche-Wochenschau-752/1945-02-17-DieDeutscheWochenschauNr.75210m16s720x544.mkv",
             "mono": True, "crop": "690:388:15:75", "credit": "Die Deutsche Wochenschau 752 (February 1945) " + WO},
  "wg_754": {"url": IA + "1945-03-16-Die-Deutsche-Wochenschau-754/1945-03-16-DieDeutscheWochenschauNr.75413m18s720x544.mkv",
             "mono": True, "crop": "690:388:15:75", "credit": "Die Deutsche Wochenschau 754 (March 1945) " + WO},
  "wg_751": {"url": IA + "1945-02-10-Die-Deutsche-Wochenschau-751/1945-02-10-DieDeutscheWochenschauNr.75110m16s720x544.mkv",
             "mono": True, "crop": "690:388:15:75", "credit": "Die Deutsche Wochenschau 751 (February 1945) " + WO},
  "wg_639": {"url": IA + "1942-12-02-Die-Deutsche-Wochenschau-639/1942-12-02-DieDeutscheWochenschauNr.63918m26s720x544.mkv",
             "mono": True, "crop": "690:388:15:75", "credit": "Die Deutsche Wochenschau 639 (December 1942) " + WO},
  "wg_silent": {"url": IA + "NPC-3844/428-npc-3844%20Supplements%20Silent%20Service.mp4", "mono": True,
                "credit": "Supplements to 'Silent Service' (1945): US Navy / NARA 428-NPC-3844 (public domain, via Internet Archive)"},
  "wg_sub": {"url": IA + "NPC-3641b/NPC-3641b.mov", "mono": True, "crop": "1008:567:136:0",
             "credit": "Submarine scenes: US Navy / NARA 428-NPC-3641 (public domain, via Internet Archive)"},
  "menace": {"url": IA + "1945-05-17_U-Boat_Menace_Ended/1945-05-17_U-Boat_Menace_Ended.mpeg", "mono": True,
             "crop": "688:344:16:68", "credit": "U-Boat Menace Ended (17 May 1945): Universal Newsreel (public domain, via Internet Archive)"}},
 "period_audio": {
  "hitler": {"file": "Hitler 30 January 1945.mp3",   # only from period/ (the excerpt 925-955 s of the IA file)
             "url": IA + "adolf-hitlers-last-speech_202205/period_excerpt_is_in_the_repo",
             "speaker": "Adolf Hitler", "date": "30 JANUARY 1945",
             "credit": "Adolf Hitler, radio address, 30 January 1945 (Internet Archive, public domain mark)",
             "text": "Ich erwarte von allen Frauen und Mädchen, dass sie diesen Kampf mit äußerstem Fanatismus unterstützen."}},
 "pre": [{"dur": 2.8, "film": "wg_ship", "from": 1256, "to": 1259, "stamp": ["JANUARY 30", "1945"], "sfx": "explosion_massive"}],
 "whole": [STAMP_M, STAMP_S13, UKAZ],
 "tone": [MAN, DOENITZ],
 "thumb": {"file": DANZIG},
 "cover": {"file": DANZIG, "x": 0.5, "y": 0.0, "zoom": 1.0, "color": False, "mono": True, "sizes": [120, 90],
           "text": ["GUSTLOFF", "DEADLIER THAN TITANIC"], "key": ["GUSTLOFF"],
           "note": "even the lowest count of the dead is more than twice the Titanic's"},
 "promos": [
  {"id": "gustloff_lights", "chapter": 5,
   "sentences": ["Four captains command one ship.",
                 "One is a submariner, and he wants no lights.",
                 "But her master does the opposite, and in the dark he turns on: the navigation lights."],
   "shots": [film(1, "wg_752", 232, 3), film(2, "wg_639", 112, 3), film(3, "wg_ship", 1254, 5)],
   "top": "FOUR CAPTAINS|ONE SHIP", "key": ["CAPTAINS"],
   "cta": {"kind": "redacted", "line": "IN THE DARK HE TURNED ON", "hidden": "THE LIGHTS"}, "end": "WHAT DID HE TURN ON?",
   "name": "Four Captains, One Doomed Ship: the Wilhelm Gustloff"},
  {"id": "gustloff_pool", "chapter": 7,
   "sentences": ["373 women live in a ship's empty swimming pool.",
                 "A Soviet submarine follows in the dark.",
                 "A torpedo hits the pool, and these are the survivors: three."],
   "shots": [film(1, "wg_ship", 796, 3), film(2, "wg_silent", 84, 4), film(3, "wg_ship", 812, 4)],
   "top": "THE WOMEN|IN THE POOL", "key": ["POOL"],
   "cta": {"kind": "number", "big": "373", "line": "WOMEN. HOW MANY SURVIVED?"}, "end": "HOW MANY SURVIVED?",
   "name": "373 Women in the Pool of the Wilhelm Gustloff"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "gustloff.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
