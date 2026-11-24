"""The Kamikaze, Nov 23 (Andrii: 'так, пиши Kamikaze на середу'): a hand story in the NEW FORMAT (CLAUDE.md, Nov 23):
voice No. 3 ('andrii', voice pack), the narrator at ~3 s, Emperor Hirohito's surrender broadcast ('enduring the
unendurable') as a beat right after sentence 1 (Ugaki's last flight hours after it), one open question (volunteers or
ordered? answered in 'The Volunteers'), short wordless parts, names and notes in the stamp look, 2 cliff teasers.
Facts: Wikipedia 'Kamikaze', 'Takijirō Ōnishi', 'Yukio Seki', 'USS St. Lo', 'Battle of Okinawa', 'USS Bunker Hill
(CV-17)', 'Yokosuka MXY-7 Ohka', 'Matome Ugaki', 'USS Laffey (DD-724)', 'USS Missouri (BB-63)' (whole, sources/*.txt).
Films (public domain, US Navy / NARA 428-NPC via Internet Archive): NPC-69 (a suicide plane crashes into an Essex-class
carrier), NPC-8131 (suicide dive on Ticonderoga), NPC-6973 (suicide planes attack BBs and CVLs, 6 Jan 1945), NPC-11755
(task group under attack off Okinawa, 16 Apr 1945), NPC-11705 (CV hit by kamikaze), NPC-7969 (Bunker Hill afire),
NPC-11212 (Essex gun crews), NPC-11549 (attack on Enterprise's task force), NPC-7606 ('Baka' bomb, Okinawa), NPC-7818
(suicide plane shot down). The NPC transfers with a burnt-in timecode at the bottom are cropped above it.
Speech: Emperor Hirohito, Imperial Rescript on the Termination of the War, 15 August 1945 (Commons, public domain):
'...堪ヘ難キヲ堪ヘ忍ヒ難キヲ忍ヒ' = 'enduring the unendurable and suffering what is insufferable'.
Run: python tools/stories/kamikaze_build.py"""
import json, pathlib

ONISHI = "Takijirō Ōnishi.jpg"
ONISHI2 = "Takijiro Onishi.jpg"
ONISHI_SEKI = "19441025 onishi seki farewell.png"
SEKI = "Yukio seki.jpg"
SEKI_GROUP = "Seki photo ma1944-10-20.jpg"
FAREWELL = "19441025 pilots of japanese 201 naval air corps farewell.jpg"
UGAKI = "Matome Ugaki.jpg"
UGAKI_D4Y = ("Admiral Matome Ugaki with Yokosuka D4Y3 before final Kamikaze attack off Okinawa 15 August 1945.jpg")
UGAKI_FINAL = "Ugaki Matome final mission.jpg"
CIVILIANS = "Japanese civilians listening to the surrender broadcast.jpg"
STLO = "Explosion on USS St. Lo (CVE-63) during Battle off Samar, 25 October 1944 (80-G-270516).jpg"
STLO2 = "St. Lo First Kamikaze attack sl1a.jpg"
BH_HIT = "USS Bunker Hill hit by two Kamikazes.jpg"
BH_AFIRE = "USS Bunker Hill (CV-17) afire after being hit by Kamikazes off Okinawa, 11 May 1945 (80-G-274266).jpg"
BH_SECOND = "Second kamikaze hits USS Bunker Hill (CV-17) 11 May 1945.jpg"
YASUNORI = "Seizō Yasunori and Zero (cropped, b&w).jpg"
OGAWA = "Ensign Kiyoshi Ogawa hit Bunker Hill (new).png"
MISSOURI = "USS Missouri Zero Kamikaze.jpg"
CHIRAN = "Chiran high school girls wave kamikaze pilot.jpg"
PUPPY = "72nd Shinbu 1945 Kamikaze.jpg"
SORTIE = "Kamikaze pilot before sortie.jpg"
SCHOOLGIRL = "Kamikaze pilot and school girl.jpg"
TORIHAMA = "Tome Torihama with kamikaze pilots.jpg"
OHKA_SEPT = "Yokosuka MXY-7 Ohka in September 1945.jpg"
OHKA_YONTAN = "Yokosuka MXY-7 at Yontan 1945.jpeg"
OHKA_KONOIKE = "Yokosuka MXY7 Ohka at Konoike airfield 1945.jpg"
LAFFEY = "USS Laffey (DD-724) heavily damaged off Okinawa, 16 April 1945 (NH 78233).jpg"
ESSEX_HIT = "USS Essex (CV-9) is hit by a Kamikaze off the Philippines on 25 November 1944.jpg"
ESSEX_ABOUT = "USS Essex (CV-9) about to be hit by a Kamikaze on 25 November 1944.jpg"
KIDD = "Kamikaze about to crash into USS Kidd (DD-661) off Okinawa, Japan, on 11 April 1945 (NH 75767).jpg"
COLUMBIA = "Kamikaze attacks USS Columbia (CL-56) in Lingayen Gulf on 6 January 1945 (NH 79449).jpg"
LOUISVILLE = "USS Louisville (CA-28) is hit by a kamikaze in Lingayen Gulf on 6 January 1945 (80-G-363217).jpg"
SARATOGA = "USS Saratoga Kamikaze hit 21 February 1945.jpg"
ENTERPRISE = "USS Enterprise (CV-6) is hit by kamikaze - seen from USS Essex (CV-9) on 14 May 1945.jpg"
WDPORTER = "USS William D. Porter (DD-579) sinking after a Kamikaze attack off Okinawa, 10 June 1945.jpg"
AARON_WARD = "Kamikaze damage on USS Aaron Ward (DM-34) in May 1945.jpg"
SPRUANCE = "Ray Spruance.jpg"
MITSCHER = "Admiral Mitscher and Arliegh Burke.jpg"
THACH = "John Thach.jpg"
ARIMA = "Arima Masafumi.jpg"
CABOT = "Japanese plane shot down over USS Cabot (CVL-28) during Battle of the Philippine Sea 1944.jpg"
AIRCOMBAT = "Air combat off the Marianas during Battle of the Philippine Sea 1944.jpg"
JCARRIER = "Japanese carrier under attack during Battle of the Philippine Sea 1944.jpg"
SCROLL = "Mōko Shūrai Ekotoba Mongol Invasion Takezaki Suenaga 2 Page 5-7.jpg"
ABELE = "USS Mannert L. Abele (DD-733) underway c1944.jpg"
BECTON = "RADM Becton.jpg"
DAISAN = "Imperial Japanese Navy kamikaze unit Daisanryoukotai.png"
SEKI_ACADEMY = "Yukio Seki Heigakkou.jpg"
ONISHI3 = "Ōnishi takijirō.png"
ONISHI4 = "TakijiroOnishiPDJapan.jpg"
SHASHIN = "Shashin Shuho No 347.jpg"

EMPEROR_SRC = "EMPEROR HIROHITO · RADIO BROADCAST, 15 AUGUST 1945"

M_LEYTE = {"places": [{"label": "MABALACAT", "lat": 15.2, "lon": 120.6},
                      {"label": "LEYTE GULF", "lat": 10.9, "lon": 125.3, "side": "blue"},
                      {"label": "SAMAR", "lat": 11.8, "lon": 126.3, "side": "blue"}],
           "routes": [[0, 2, "red", 0.2]], "pad": 0.5}
M_OKINAWA = {"places": [{"label": "KYUSHU", "lat": 31.4, "lon": 130.8},
                        {"label": "OKINAWA", "lat": 26.4, "lon": 127.8, "side": "blue"}],
             "routes": [[0, 1, "red", 0.2]], "pad": 0.6}

C = [
 {"title": "", "mode": "action", "sentences": [
  "On 15 August 1945, hours after Japan's surrender is announced, Admiral Matome Ugaki takes off from Kyushu on one last kamikaze attack.",
  "In this war, about 3,800 kamikaze pilots die, and they kill more than 7,000 Allied sailors.",
  "The man who sends out the first of them is Vice Admiral Takijirō Ōnishi.",
  "But are these young men volunteers, or are they ordered to die?",
  "It begins in the Philippines, with one bomb on one fighter plane."],
  "shots": [
   {"s": 1, "film": "fall", "from": 60, "to": 64, "stamp": ["KYUSHU"]},
   {"s": 1, "film": "hit", "from": 50, "to": 56},
   {"s": 2, "file": BH_AFIRE, "note": "3,800 PILOTS"},
   {"s": 2, "film": "bhsmoke", "from": 0, "to": 6},
   {"s": 3, "file": ONISHI, "reveal": [0.72, 0.26], "name": "TAKIJIRŌ ŌNISHI", "role": "FATHER OF THE KAMIKAZE"},
   {"s": 4, "file": DAISAN},
   {"s": 5, "film": "flak", "from": 240, "to": 246}],
  "beats": [{"after": 1, "audio": {"src": "emperor", "from": 193.6, "to": 200.5}, "source": EMPEROR_SRC, "shots": [
   {"dur": 3.5, "file": CIVILIANS, "source": EMPEROR_SRC},
   {"dur": 3.4, "file": UGAKI_D4Y, "source": EMPEROR_SRC}]}]},

 {"title": "The Last Resort", "mode": "people", "stamp": ["JUNE 1944"], "sentences": [
  "But by 1944, Japan's navy has lost most of its best pilots.",
  "The great carrier battles of 1942 have destroyed its veteran aircrews, and new pilots cannot be trained fast enough.",
  "In June 1944, in the Battle of the Philippine Sea, Japan loses over 400 carrier aircraft and their pilots.",
  "American pilots call it the Great Marianas Turkey Shoot.",
  "Then Saipan falls, and American bombers can reach Japan itself.",
  "Captain Motoharu Okamura has a proposal: crash the aircraft into the enemy's ships.",
  "Give him 300 aircraft, he says, and he will turn the tide of the war.",
  "In October 1944, Rear Admiral Masafumi Arima leads an attack on the carrier Franklin himself, and dies.",
  "Japan's propaganda gives him the credit for the first kamikaze attack."],
  "shots": [
   {"s": 1, "file": JCARRIER},
   {"s": 2, "film": "guns", "from": 72, "to": 78},
   {"s": 3, "file": CABOT, "label": "PHILIPPINE SEA · JUNE 1944", "note": "400 AIRCRAFT"},
   {"s": 4, "file": AIRCOMBAT},
   {"s": 5, "film": "guns", "from": 232, "to": 238},
   {"s": 6, "film": "tico", "from": 20, "to": 26},
   {"s": 7, "film": "flak", "from": 196, "to": 202, "note": "300 AIRCRAFT"},
   {"s": 8, "file": ARIMA, "name": "MASAFUMI ARIMA", "role": "REAR ADMIRAL"},
   {"s": 9, "file": ARIMA, "zoom": 1.3, "y": 0.3}]},

 {"title": "Divine Wind", "mode": "people", "stamp": ["MABALACAT"], "sentences": [
  "But when the Americans land at Leyte, Admiral Ōnishi has only 41 aircraft in the Philippines.",
  "On 19 October 1944, at Mabalacat airfield near Manila, he tells his officers there is only one certain way.",
  "Put a 250-kilogram bomb on a Zero, and let it crash into an American carrier.",
  "Commander Asaichi Tamai asks 23 of his student pilots to volunteer.",
  "Every one of them raises both hands.",
  "To lead them, Tamai chooses Lieutenant Yukio Seki.",
  "Seki closes his eyes, lowers his head, and thinks for ten seconds.",
  "Then he says: please do appoint me to the post.",
  "He has been married for less than five months.",
  "The new unit is named the Divine Wind, kamikaze.",
  "It is the name of the typhoons that destroyed the invasion fleets of Kublai Khan in 1274 and 1281.",
  "Ōnishi tells the pilots that their spirit will keep the homeland from ruin, even in defeat."],
  "shots": [
   {"s": 1, "file": ONISHI4},
   {"s": 2, "map": M_LEYTE},
   {"s": 3, "film": "hit", "from": 126, "to": 132, "note": "250 KG BOMB"},
   {"s": 4, "file": SEKI_GROUP, "label": "MABALACAT · OCTOBER 1944"},
   {"s": 5, "file": FAREWELL, "zoom": 1.3, "x": 0.5},
   {"s": 6, "file": SEKI, "name": "YUKIO SEKI", "role": "LIEUTENANT, IMPERIAL JAPANESE NAVY"},
   {"s": 7, "file": SEKI_ACADEMY, "zoom": 1.5, "y": 0.15},
   {"s": 8, "file": SEKI_GROUP, "zoom": 1.35, "x": 0.5},
   {"s": 9, "file": TORIHAMA},
   {"s": 10, "file": SCROLL, "x": 0.85},
   {"s": 11, "file": SCROLL, "zoom": 1.4, "x": 0.25},
   {"s": 12, "file": ONISHI_SEKI}]},

 {"title": "The First Strike", "mode": "action", "stamp": ["LEYTE GULF"], "sentences": [
  "But four times, Seki's unit flies out to Leyte Gulf, and returns to base without an attack.",
  "On 25 October, five Zeros take off, each with one bomb.",
  "They are escorted by the ace Hiroyoshi Nishizawa.",
  "At 10:50, they find the escort carriers of Taffy 3, off Samar.",
  "Seki's plane is hit by anti-aircraft fire, and turns toward the carrier St. Lo.",
  "It crashes into her flight deck.",
  "The bomb explodes on the hangar deck, where aircraft are being refuelled and rearmed.",
  "Then her torpedo and bomb magazine explodes.",
  "St. Lo sinks within half an hour.",
  "Of the 889 men aboard, 113 are killed or missing.",
  "She is the first major warship sunk by a kamikaze attack.",
  "By the next day, seven carriers and 40 other ships have been hit.",
  "The program is expanded at once, and over the next few months, more than 2,000 aircraft make such attacks."],
  "shots": [
   {"s": 1, "film": "flak", "from": 246, "to": 252},
   {"s": 2, "film": "guns", "from": 230, "to": 236},
   {"s": 3, "film": "tico", "from": 26, "to": 32},
   {"s": 4, "film": "flak", "from": 100, "to": 106, "stamp": ["10:50 A.M."]},
   {"s": 5, "film": "hit", "from": 22, "to": 28},
   {"s": 6, "film": "crash", "from": 40, "to": 46, "sfx": "explosion_far"},
   {"s": 7, "film": "crash", "from": 46, "to": 52},
   {"s": 8, "file": STLO, "label": "OFF SAMAR · 25 OCTOBER 1944", "sfx": "explosion_massive"},
   {"s": 9, "file": STLO2},
   {"s": 10, "film": "ling", "from": 54, "to": 60, "note": "113 KILLED OR MISSING"},
   {"s": 11, "film": "ling", "from": 100, "to": 106},
   {"s": 12, "file": ESSEX_ABOUT},
   {"s": 13, "file": ESSEX_HIT, "note": "2,000 AIRCRAFT"}],
  "beats": [
   {"after": 9, "shots": [{"dur": 3.5, "film": "tico", "from": 52, "to": 56, "sfx": "explosion_far"},
                          {"dur": 3.0, "film": "ling", "from": 66, "to": 69, "sfx": "low_rumble"}]}]},

 {"title": "The Volunteers", "mode": "people", "stamp": ["CHIRAN"], "sentences": [
  "But Japan now needs thousands of pilots willing to die.",
  "The commanders claim there are twice as many volunteers as aircraft.",
  "Most of the pilots are unmarried, and their average age is 19.",
  "Their training lasts about thirty days, with beatings as a daily routine.",
  "Their manual tells them never to close their eyes before the crash.",
  "Before the last flight, they share a ceremonial cup of sake or water, and write a death poem.",
  "At Chiran, schoolgirls wave them off with cherry blossom branches.",
  "Lieutenant Seki had told a reporter that he was not going for the Emperor or for the Empire.",
  "Some pilots keep returning to base, and one who comes back nine times is executed.",
  "Some officers refuse to obey the policy.",
  "Decades later, a Japanese newspaper editor calls the pilots sheep at a slaughterhouse.",
  "This is the answer: some volunteer, but many are pushed, by orders and by the pressure of those around them."],
  "shots": [
   {"s": 1, "file": SHASHIN, "label": "SHASHIN SHUHO · NOVEMBER 1944"},
   {"s": 2, "file": PUPPY},
   {"s": 3, "file": PUPPY, "zoom": 1.35, "y": 0.35, "note": "AVERAGE AGE 19"},
   {"s": 4, "file": TORIHAMA, "zoom": 1.3},
   {"s": 5, "file": SCHOOLGIRL},
   {"s": 6, "file": SORTIE, "zoom": 1.3, "x": 0.45},
   {"s": 7, "file": CHIRAN, "label": "CHIRAN · 1945"},
   {"s": 8, "file": ONISHI_SEKI},
   {"s": 9, "film": "fall", "from": 4, "to": 10},
   {"s": 10, "film": "flak", "from": 252, "to": 258},
   {"s": 11, "file": CHIRAN, "zoom": 1.35, "x": 0.4},
   {"s": 12, "file": SCHOOLGIRL, "zoom": 1.3, "x": 0.5}],
  "beats": [
   {"after": 8, "quote": {"text": "I am going because I was ordered to.",
                          "name": "YUKIO SEKI", "role": "LIEUTENANT, KAMIKAZE UNIT LEADER"},
    "shots": [{"dur": 4.0, "file": SEKI, "zoom": 1.2, "y": 0.3}]}]},

 {"title": "The Big Blue Blanket", "mode": "action", "stamp": ["MARCH 1945"], "sentences": [
  "But by March 1945, the U.S. Navy is fighting back.",
  "Commander John Thach designs a defence called the big blue blanket.",
  "Larger fighter patrols fly farther from the carriers, around the clock.",
  "A line of picket destroyers sits at least 50 miles out, to give early radar warning.",
  "Fighters sweep over the Japanese airfields and bomb their runways.",
  "On the ships, the heavy five-inch guns prove the most effective, because even a crippled kamikaze can reach its target.",
  "And new shells with proximity fuzes are about seven times more effective than regular ones.",
  "Still, on 11 March, a kamikaze flies almost 2,500 miles from Japan and hits the carrier Randolph at Ulithi."],
  "shots": [
   {"s": 1, "film": "guns", "from": 78, "to": 84},
   {"s": 2, "file": THACH, "name": "JOHN THACH", "role": "COMMANDER, U.S. NAVY"},
   {"s": 3, "film": "guns", "from": 216, "to": 222},
   {"s": 4, "film": "flak", "from": 92, "to": 98, "note": "50 MILES"},
   {"s": 5, "film": "flak", "from": 52, "to": 58},
   {"s": 6, "film": "guns", "from": 84, "to": 90, "sfx": "machine_gun"},
   {"s": 7, "film": "flak", "from": 192, "to": 198},
   {"s": 8, "file": SARATOGA, "note": "2,500 MILES"}],
  "beats": [
   {"after": 7, "shots": [{"dur": 3.5, "film": "flak", "from": 202, "to": 206, "sfx": "explosion_far"},
                          {"dur": 3.0, "file": LOUISVILLE}]}]},

 {"title": "Cherry Blossom", "mode": "action", "stamp": ["MARCH 21", "1945"], "sentences": [
  "But Japan is already building a weapon made only for suicide: the Ohka, the cherry blossom.",
  "It is a rocket-powered plane with a warhead of 1,200 kilograms, and wings of plywood.",
  "A bomber carries it under its belly, and must come within 23 miles of its target.",
  "In its final dive, it is so fast that gunners can hardly aim at it.",
  "On 21 March 1945, the first Ohka mission ends in disaster.",
  "American fighters shoot down every one of the bombers before they can launch.",
  "The Americans give the Ohka a nickname: baka, the Japanese word for idiot.",
  "On 12 April, an Ohka hits the destroyer Mannert L. Abele, and she breaks in two and sinks.",
  "Of 300 Ohkas ready for Okinawa, only 74 ever attack.",
  "Not one capital ship is ever seriously damaged by them."],
  "shots": [
   {"s": 1, "file": OHKA_YONTAN},
   {"s": 2, "file": OHKA_SEPT, "note": "1,200 KG"},
   {"s": 3, "file": OHKA_KONOIKE},
   {"s": 4, "film": "baka", "from": 36, "to": 42},
   {"s": 5, "film": "burn", "from": 142, "to": 148},
   {"s": 6, "film": "fall", "from": 34, "to": 40},
   {"s": 7, "file": OHKA_YONTAN, "zoom": 1.3, "x": 0.4, "note": "BAKA"},
   {"s": 8, "file": ABELE, "label": "OKINAWA · 12 APRIL 1945"},
   {"s": 9, "film": "baka", "from": 42, "to": 48, "note": "74 OF 300"},
   {"s": 10, "film": "flak", "from": 620, "to": 626}]},

 {"title": "Floating Chrysanthemums", "mode": "action", "stamp": ["OKINAWA"], "sentences": [
  "But the worst is still to come, at Okinawa.",
  "On 6 April 1945, waves of aircraft attack the fleet, in an operation called Kikusui, floating chrysanthemums.",
  "Between April and June, 1,465 kamikaze aircraft fly from Kyushu in these mass attacks.",
  "They strike the picket destroyers first, then the carriers in the middle of the fleet.",
  "On 11 April, a Zero hits the battleship Missouri below her main deck.",
  "Her crew quickly put out the fire, and the damage is only superficial.",
  "Then Captain William Callaghan gives an unexpected order.",
  "The pilot will be buried at sea, under a Japanese flag that the signalmen make themselves.",
  "At Okinawa, the U.S. Navy has more men killed than wounded: 4,907 dead.",
  "Most of them die in kamikaze attacks."],
  "shots": [
   {"s": 1, "film": "flak", "from": 210, "to": 216},
   {"s": 2, "film": "flak", "from": 216, "to": 222, "label": "OKINAWA · 6 APRIL 1945"},
   {"s": 3, "map": M_OKINAWA},
   {"s": 4, "file": KIDD},
   {"s": 5, "file": MISSOURI, "label": "OKINAWA · 11 APRIL 1945", "sfx": "explosion_far"},
   {"s": 6, "film": "burn", "from": 66, "to": 72},
   {"s": 7, "film": "crash", "from": 124, "to": 130},
   {"s": 8, "file": MISSOURI, "zoom": 1.3, "x": 0.45},
   {"s": 9, "file": WDPORTER, "note": "4,907 DEAD"},
   {"s": 10, "film": "ling", "from": 104, "to": 110}],
  "beats": [
   {"after": 4, "shots": [{"dur": 3.5, "film": "flak", "from": 222, "to": 226, "sfx": "explosion_far"},
                          {"dur": 3.0, "film": "burn", "from": 72, "to": 75, "sfx": "low_rumble"}]}]},

 {"title": "The Ship That Would Not Die", "mode": "action", "stamp": ["APRIL 16", "1945"], "sentences": [
  "But the picket destroyers take the heaviest blows.",
  "On 16 April 1945, about 50 Japanese planes attack the destroyer Laffey.",
  "She is on radar picket duty, north of Okinawa.",
  "Wildcats from an escort carrier and Marine Corsairs fight above her.",
  "Six kamikazes crash into her, and four bombs hit her.",
  "An officer asks Captain Frederick Becton if they will have to abandon ship.",
  "A lookout softly adds that first he would have to find a man to fire it.",
  "Laffey survives, with 32 men killed and 71 wounded.",
  "Her crew call her the ship that would not die."],
  "shots": [
   {"s": 1, "file": AARON_WARD},
   {"s": 2, "film": "flak", "from": 226, "to": 232, "label": "NORTH OF OKINAWA · 16 APRIL 1945"},
   {"s": 3, "film": "crash", "from": 82, "to": 88},
   {"s": 4, "film": "guns", "from": 236, "to": 242},
   {"s": 5, "film": "ling", "from": 194, "to": 199, "sfx": "explosion_far", "note": "6 KAMIKAZES"},
   {"s": 6, "file": BECTON, "name": "FREDERICK BECTON", "role": "CAPTAIN, USS LAFFEY"},
   {"s": 7, "film": "guns", "from": 140, "to": 146},
   {"s": 8, "file": LAFFEY, "label": "16 APRIL 1945"},
   {"s": 9, "file": LAFFEY, "zoom": 1.3, "x": 0.5}],
  "beats": [
   {"after": 6, "quote": {"text": "No! I'll never abandon ship as long as a single gun will fire.",
                          "name": "FREDERICK BECTON", "role": "CAPTAIN, USS LAFFEY"},
    "shots": [{"dur": 4.5, "file": BECTON, "zoom": 1.25, "y": 0.3}]}]},

 {"title": "Bunker Hill", "mode": "action", "stamp": ["MAY 11", "1945"], "sentences": [
  "But on 11 May 1945, the kamikazes reach the heart of the fleet.",
  "The carrier Bunker Hill is the flagship of Vice Admiral Marc Mitscher.",
  "The Zero of Lieutenant Seizō Yasunori comes out of low cloud and drops its bomb.",
  "His plane hits the flight deck, where aircraft full of fuel and ammunition are parked.",
  "Thirty seconds later, Ensign Kiyoshi Ogawa dives in near the island.",
  "His bomb reaches the pilots' ready room, where 22 men of one squadron die.",
  "In all, 396 men are killed or missing.",
  "Mitscher is only yards away, and loses fourteen men of his staff.",
  "Three days later, his new flagship Enterprise is hit too.",
  "Admiral Raymond Spruance, whose own flagships are hit twice, writes about the weapon.",
  "Yet the British carriers, with their armoured flight decks, are back in action within hours."],
  "shots": [
   {"s": 1, "film": "bhsmoke", "from": 22, "to": 28},
   {"s": 2, "file": MITSCHER, "name": "MARC MITSCHER", "role": "VICE ADMIRAL, U.S. NAVY"},
   {"s": 3, "file": YASUNORI, "name": "SEIZŌ YASUNORI", "role": "LIEUTENANT"},
   {"s": 4, "file": BH_SECOND, "label": "OFF OKINAWA · 11 MAY 1945", "sfx": "explosion_far"},
   {"s": 5, "file": OGAWA, "name": "KIYOSHI OGAWA", "role": "ENSIGN"},
   {"s": 6, "file": BH_HIT},
   {"s": 7, "file": BH_AFIRE, "note": "396 KILLED OR MISSING"},
   {"s": 8, "file": MITSCHER, "zoom": 1.3, "x": 0.3},
   {"s": 9, "file": ENTERPRISE, "label": "14 MAY 1945"},
   {"s": 10, "file": SPRUANCE, "name": "RAYMOND SPRUANCE", "role": "ADMIRAL, U.S. FIFTH FLEET"},
   {"s": 11, "film": "hit", "from": 176, "to": 182}],
  "beats": [
   {"after": 7, "shots": [{"dur": 3.5, "film": "bhsmoke", "from": 30, "to": 34, "sfx": "low_rumble"},
                          {"dur": 3.0, "film": "ling", "from": 120, "to": 123}]},
   {"after": 10, "quote": {"text": "The suicide plane is a very effective weapon, which we must not underestimate.",
                           "name": "RAYMOND SPRUANCE", "role": "ADMIRAL, U.S. FIFTH FLEET"},
    "shots": [{"dur": 4.5, "film": "bhsmoke", "from": 60, "to": 64.5}]}]},

 {"title": "The Last Flight", "mode": "people", "stamp": ["AUGUST 1945"], "sentences": [
  "But by August 1945, Japan is preparing for an invasion of its home islands.",
  "More than 9,000 aircraft wait there, and over 5,000 are fitted for suicide attacks.",
  "On 15 August, Emperor Hirohito announces the surrender on the radio.",
  "Admiral Ugaki writes a last entry in his diary.",
  "He has no official cease-fire order yet, and he blames himself for the failure of his pilots.",
  "He removes his rank insignia, and takes a short sword given to him by Admiral Yamamoto.",
  "Warrant Officer Akiyoshi Endo, whose place Ugaki has taken, climbs into the same plane.",
  "At 19:24, the last message reports a dive onto an American ship.",
  "But U.S. Navy records show no kamikaze hit that day.",
  "The next day, Admiral Ōnishi commits ritual suicide.",
  "In his note, he apologizes to the roughly 4,000 pilots he sent to their deaths.",
  "He asks the young people of Japan to rebuild their country, and to work for peace among nations.",
  "The kamikazes sink dozens of ships, but not one fleet carrier, battleship or cruiser.",
  "This time, the divine wind cannot save Japan."],
  "shots": [
   {"s": 1, "film": "fall", "from": 46, "to": 52},
   {"s": 2, "file": OHKA_KONOIKE, "zoom": 1.3, "x": 0.5, "note": "9,000 AIRCRAFT"},
   {"s": 3, "file": CIVILIANS, "label": "JAPAN · 15 AUGUST 1945"},
   {"s": 4, "file": UGAKI, "name": "MATOME UGAKI", "role": "VICE ADMIRAL, COMMANDER OF THE 5TH AIR FLEET"},
   {"s": 5, "file": UGAKI, "zoom": 1.3, "y": 0.25},
   {"s": 6, "file": UGAKI_D4Y, "zoom": 1.25, "x": 0.5},
   {"s": 7, "file": UGAKI_FINAL},
   {"s": 8, "film": "fall", "from": 58, "to": 64, "stamp": ["7:24 P.M."]},
   {"s": 9, "film": "flak", "from": 600, "to": 606},
   {"s": 10, "file": ONISHI2, "zoom": 1.2, "y": 0.3},
   {"s": 11, "file": ONISHI, "zoom": 1.3, "y": 0.25, "note": "4,000 PILOTS"},
   {"s": 12, "file": UGAKI_FINAL, "zoom": 1.3, "x": 0.5},
   {"s": 13, "film": "ling", "from": 140, "to": 146},
   {"s": 14, "film": "flak", "from": 626, "to": 632}],
  "beats": [
   {"after": 8, "shots": [{"dur": 3.5, "film": "fall", "from": 52, "to": 56, "sfx": "low_rumble"},
                          {"dur": 3.0, "film": "flak", "from": 606, "to": 609}]}]},
]


def after(ch, prefix, sentence, shot):
    """Insert `sentence` right after the sentence of chapter `ch` that starts with `prefix`; later shots and beats
    move down by one."""
    c = C[ch]
    pos = next(i for i, s in enumerate(c["sentences"]) if s.startswith(prefix)) + 2
    c["sentences"].insert(pos - 1, sentence)
    for s in c["shots"]:
        if s["s"] >= pos:
            s["s"] += 1
    for b in c.get("beats", []):
        if b["after"] >= pos:
            b["after"] += 1
    c["shots"].append({"s": pos, **shot})
    c["shots"].sort(key=lambda s: s["s"])


after(1, "But by 1944", "Before the war, its carrier pilots trained for years in special schools.", {"film": "guns", "from": 240, "to": 246})
after(1, "Then Saipan falls", "Tokyo expects the next blow to fall on the Philippines, between Japan and its oil.", {"film": "flak", "from": 60, "to": 66})
after(2, "He has been married", "His wife, Mariko, had followed him to Yokohama to say goodbye.", {"file": SEKI_ACADEMY})
after(3, "At 10:50", "These ships have just survived an attack by the battleship Yamato and the Japanese Center Force.", {"film": "ling", "from": 220, "to": 226})
after(4, "Before the last flight", "Each wears a belt of a thousand stitches, given to him by his mother.", {"file": FAREWELL, "zoom": 1.4, "x": 0.3})
after(4, "At Chiran", "Many look back for a last sight of Mount Kaimon, the southernmost mountain of mainland Japan, and salute it.", {"film": "fall", "from": 20, "to": 26})
after(6, "A bomber carries it", "Twice, the carriers taking Ohkas to the Philippines are sunk on the way by American submarines.", {"film": "crash", "from": 96, "to": 102})
after(7, "The pilot will be buried", "The crew keep many pieces of his plane, and a sailor's photograph of the attack becomes famous.", {"film": "crash", "from": 130, "to": 136})
after(8, "Wildcats from an escort", "Some of the fighters keep diving at the kamikazes even after their ammunition is gone.", {"film": "hit", "from": 130, "to": 136})
after(10, "Warrant Officer Akiyoshi", "Ten more planes take off with them.", {"film": "fall", "from": 64, "to": 70})
after(10, "The next day", "He refuses the help of a second, and dies over 15 hours, as a penance to the pilots.", {"file": ONISHI3})

STORY = {
 "priority": 10,
 "format": "entire",
 "voice": "andrii",
 "intro_beats": True,
 "topic": "Kamikaze",
 "sources": ["Kamikaze", "Takijirō Ōnishi", "Yukio Seki", "USS St. Lo", "Battle of Okinawa", "USS Bunker Hill (CV-17)",
             "Yokosuka MXY-7 Ohka", "Matome Ugaki", "USS Laffey (DD-724)", "USS Missouri (BB-63)"],
 "title": "The ENTIRE History of the Kamikaze in {N} Minutes",
 "question": "Were the kamikaze pilots heroes, victims, or both?",
 "summary": ("From Admiral Ōnishi's order at Mabalacat and Yukio Seki's attack on the St. Lo in 1944 to the Ohka, "
             "the Laffey, the Bunker Hill and Admiral Ugaki's last flight after the surrender, this is the whole story "
             "of Japan's kamikaze pilots, told with the US Navy's archive film and Emperor Hirohito's own voice."),
 "tags": ["kamikaze", "kamikaze pilots", "Takijiro Onishi", "Yukio Seki", "USS St. Lo", "Battle of Leyte Gulf",
          "Battle of Okinawa", "Ohka", "USS Laffey", "USS Bunker Hill", "USS Missouri", "Matome Ugaki",
          "Pacific War", "WW2 documentary", "World War 2", "history"],
 "pronounce": {"Takijirō Ōnishi": "Tah-kee-jee-roh Oh-nee-shee", "Ōnishi": "Oh-nee-shee", "Matome": "Mah-toh-meh",
               "Ugaki": "Oo-gah-kee", "Seki": "Seh-kee", "Asaichi": "Ah-sah-ee-chee", "Tamai": "Tah-my",
               "Hiroyoshi Nishizawa": "Hee-roh-yoh-shee Nee-shee-zah-wah", "Mabalacat": "Mah-bah-lah-kaht",
               "Motoharu Okamura": "Moh-toh-hah-roo Oh-kah-moo-rah", "Masafumi Arima": "Mah-sah-foo-mee Ah-ree-mah",
               "Kikusui": "Kee-koo-soo-ee", "Kyushu": "Kyoo-shoo", "Seizō Yasunori": "Say-zoh Yah-soo-noh-ree",
               "Kiyoshi Ogawa": "Kee-yoh-shee Oh-gah-wah", "Ohkas": "Oh-kahs", "Ohka": "Oh-kah",
               "Chiran": "Chee-rahn", "Akiyoshi Endo": "Ah-kee-yoh-shee En-doh", "baka": "bah-kah",
               "Abele": "Ay-bel", "Ulithi": "Oo-lee-thee", "Laffey": "Laf-ee", "Samar": "Sah-mar",
               "Mitscher": "Mitch-er", "Thach": "Thatch", "Hirohito": "Hee-roh-hee-toh", "Kublai": "Koo-bly"},
 "films": {
  "crash": {"url": "https://archive.org/download/NPC-69/NPC-69.mov", "mono": True, "crop": "1100:620:90:40",
            "credit": "Japanese Suicide Plane Crashing Into Island Structure of Carrier (1944-45): US Navy / NARA 428-NPC-69 (public domain, via Internet Archive)"},
  "tico": {"url": "https://archive.org/download/NPC-8131/NPC-8131.mov", "mono": True, "crop": "996:560:142:0",
           "credit": "Suicide Dive on USS Ticonderoga (1945): US Navy / NARA 428-NPC-8131 (public domain, via Internet Archive)"},
  "ling": {"url": "https://archive.org/download/NPC-6973/NPC-6973.mov", "mono": True, "crop": "996:560:142:0",
           "credit": "Japanese Suicide Planes Attack BBs and CVLs (6 January 1945): US Navy / NARA 428-NPC-6973 (public domain, via Internet Archive)"},
  "flak": {"url": "https://archive.org/download/NPC-11755/NPC-11755.mov", "mono": True, "crop": "1200:675:40:20",
           "credit": "Task Group Under Attack Off Okinawa (16 April 1945): US Navy / NARA 428-NPC-11755 (public domain, via Internet Archive)"},
  "hit": {"url": "https://archive.org/download/NPC-11705/NPC-11705.mov", "mono": True, "crop": "1200:675:40:20",
          "credit": "CV Hit by Kamikaze (1945): US Navy / NARA 428-NPC-11705 (public domain, via Internet Archive)"},
  "bhsmoke": {"url": "https://archive.org/download/NPC-7969/NPC-7969.mov", "mono": True, "crop": "996:560:142:0",
              "credit": "USS Bunker Hill (CV-17) Afire (1945): US Navy / NARA 428-NPC-7969 (public domain, via Internet Archive)"},
  "guns": {"url": "https://archive.org/download/NPC-11212/NPC-11212.mov", "mono": True, "crop": "1040:585:20:60",
           "credit": "Activity Aboard the USS Essex, USS Bunker Hill Under Attack (21 March 1945): US Navy / NARA 428-NPC-11212 (public domain, via Internet Archive)"},
  "burn": {"url": "https://archive.org/download/NPC-11549/NPC-11549.mov", "mono": True, "crop": "1200:675:40:20",
           "credit": "Japanese Suicide Attack on Task Force, USS Enterprise (1945): US Navy / NARA 428-NPC-11549 (public domain, via Internet Archive)"},
  "baka": {"url": "https://archive.org/download/NPC-7606/NPC-7606.mov", "mono": True, "crop": "996:560:142:0",
           "credit": "Japanese Baka Suicide Bomb, Okinawa (17 April 1945): US Navy / NARA 428-NPC-7606 (public domain, via Internet Archive)"},
  "fall": {"url": "https://archive.org/download/NPC-7818/NPC-7818.mov", "mono": True, "crop": "996:560:142:0",
           "credit": "Japanese Suicide Plane Is Shot Down (17 April 1945): US Navy / NARA 428-NPC-7818 (public domain, via Internet Archive)"}},
 "period_audio": {
  "emperor": {"file": "Imperial Rescript on the Termination of the War.ogg",
              "url": "https://upload.wikimedia.org/wikipedia/commons/4/42/Imperial_Rescript_on_the_Termination_of_the_War.ogg",
              "speaker": "Emperor Hirohito", "date": "AUGUST 1945",
              "credit": "Emperor Hirohito, Imperial Rescript on the Termination of the War, radio broadcast of 15 August 1945 (public domain, Wikimedia Commons)",
              "text": "Enduring the unendurable and suffering what is insufferable."}},
 "pre": [{"dur": 2.8, "film": "crash", "from": 41, "to": 44, "stamp": ["AUGUST 15", "1945"],
          "sfx": "explosion_massive"}],
 "whole": [ONISHI_SEKI, OGAWA, YASUNORI],
 "tone": [SEKI, YASUNORI, MITSCHER, SPRUANCE],   # DDColor paints them pink/green
 "thumb": {"file": STLO},
 "cover": {"file": STLO, "x": 0.5, "y": 0.45, "zoom": 1.0, "color": False,
           "text": ["HISTORY OF", "THE KAMIKAZE", "IN {N} MINUTES"], "key": ["KAMIKAZE"], "sizes": [96, 150, 96],
           "mono": True},
 # Andrii, Nov 24: 2 covers for YouTube's Test & compare against the template (words = facts of the story)
 "thumbs_test": [
  {"style": "photo", "file": PUPPY, "x": 0.5, "y": 0.5, "color": False, "mono": True, "text": ["ORDERED TO DIE?"],
   "key": ["ORDERED"], "sizes": [150], "note": "Seki: 'I am going because I was ordered to.'"},
  {"style": "photo", "file": STLO, "x": 0.5, "y": 0.45, "color": False, "mono": True, "text": ["ONE PLANE", "SANK THIS SHIP"],
   "key": ["ONE"], "sizes": [150, 96], "note": "St. Lo: sunk after one Zero's hit"}],
 "promos": [
  {"id": "kamikaze_missouri", "chapter": 7,
   "sentences": ["A kamikaze crashes into the battleship Missouri.",
                 "Her crew quickly put out the fire.",
                 "Then her captain gives a strange order: a burial at sea for the pilot, under a Japanese flag."],
   "shots": [{"s": 1, "file": MISSOURI}, {"s": 2, "film": "burn", "from": 66, "to": 72},
             {"s": 3, "film": "crash", "from": 124, "to": 130}],
   "top": "A KAMIKAZE|HITS THE MISSOURI", "key": ["KAMIKAZE"],
   "cta": {"kind": "redacted", "line": "THE CAPTAIN ORDERS A", "hidden": "BURIAL AT SEA"}, "end": "WHAT ORDER?",
   "name": "The Kamikaze Pilot the USS Missouri Buried at Sea"},
  {"id": "kamikaze_laffey", "chapter": 8,
   "sentences": ["About 50 Japanese planes attack one American destroyer.",
                 "Six kamikazes crash into her.",
                 "Asked if they must abandon ship, the captain snaps: never."],
   "shots": [{"s": 1, "film": "flak", "from": 226, "to": 232}, {"s": 2, "film": "ling", "from": 194, "to": 199},
             {"s": 3, "file": BECTON}],
   "top": "6 KAMIKAZES|ONE DESTROYER", "key": ["KAMIKAZES"],
   "cta": {"kind": "number", "big": "6", "line": "KAMIKAZE HITS. DOES SHE SINK?"}, "end": "DOES SHE SINK?",
   "name": "The Destroyer That Survived Six Kamikazes"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "kamikaze.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
