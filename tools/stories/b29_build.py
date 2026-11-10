"""Builds stories/long/b29.json (The Entire War format) from b29_text.py + the shot plan below."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from b29_text import CH

F = lambda film, a, b, **k: {"film": film, "from": a, "to": b, **k}
P = lambda f, **k: {"file": f, **k}
COLOR_FLIGHT = "B-29_Bomber_on_a_long_range_mission_in_late_1945.jpg"
CHENGDU = "B-29_Superfortress_of_the_20th_Bomber_Command_near_Chengdu,_China.jpg"
LEMAY = "Curtis_LeMay_(USAF).jpg"
ARNOLD = "General_of_the_Air_Force_Hap_Arnold.png"
XB29 = "Boeing_XB-29_41-002.jpg"
LINE = "Boeing-Whichata_B-29_Assembly_Line_-_1944.jpg"
WICHITA = "Favored_by_Warm_breezes_and_under_a_blue_Kansas_Sky,_a_vast_crowd_attends_the_delivery_ceremony_on_the_Boeing-Wichita..._-_NARA_-_196890.jpg"
RUINS = "After_Bombing_of_Tokyo_on_March_1945_19450310.jpg"
RUINS2 = "A_view_of_Tokyo_after_an_incendiary_bombing.jpg"
SWEENEY = "Major_Charles_W._Sweeney,_pilot_of_B-29_Bockscar.jpg"
ENOLA = "B-29_Enola_Gay_w_Crews.jpg"
PW = "Boeing_B-29_Superfortress_on_supply_mission_flies_over_Nagasaki,_Japan,_in_September_1945.jpg"
KOREA_BOMBS = "B-29_Dropping_1,000lb_Bombs_Over_Korea_August_1951.jpg"
KOREA = "B-29s_19th_Bomb_Group_over_Korea_1950.jpg"
ODONNELL = "General_Emmett_Rosie_O'Donnell.jpg"
NORTHFIELD = "Northfield-tinian-1945.jpg"
ISELY = "Isely_Field_with_B-29s_in_mid_1945.jpg"
HARD = "497th_Bomb_Group_B-29s_on_Hardstands_Isley_Field_Saipan.jpg"
GROUP = "LeMay,O'Donnel,Arnold,Giles.jpg"
TURRET = "XB-29_or_YB-29_turret_(15942305083).jpg"
OLIVE = "Olive-drab_painted_B-29_superfortress.jpg"
B498 = "Boeing_B-29_Superfortress_of_the_498th_at_Isely_Field,_Saipan,_circa_in_late_1944_(74237464).jpg"
OVER_TOKYO = "B29_Bombing_Tokyo_(25_May_1945).png"
TIBBETS = "Col_Paul_W._Tibbets,_Pilot_Of_B-29_Superfortress_'Enola_Gay'.jpg"
LITTLE_BOY = "Loading_of_the_Little_Boy_nuclear_bomb_into_the_Boeing_B-29_on_Tinian,_Mariana_Island,_5_August_1945_(76048611).jpg"
HIROSHIMA = "Atomic_cloud_over_Hiroshima.jpg"
STALIN = "Joseph_Stalin_1945.jpg"
FDR = "FDR_1944_Color_Portrait.jpg"

MAP = lambda places, routes, **k: {"map": {"places": places, "routes": routes}, **k}
PL = lambda label, lat, lon: {"label": label, "lat": lat, "lon": lon}

SHOTS = [
 # 0 cold open
 {1: [F("tokyo", 935, 939, sfx="plane_flyby"), P(LEMAY, y=0.25)],
  2: [F("birth", 776, 781), F("birth", 700, 705)],
  3: [F("airwar", 545, 550, sfx="explosion_far"), F("airwar", 570, 575)],
  4: [F("airwar", 625, 630), F("airwar", 695, 701, sfx="explosion_massive")],
  5: [P(COLOR_FLIGHT, zoom=1.05)]},
 # 1 The Superbomber
 {1: [F("birth", 310, 316, note="BOEING · 1938")], 2: [P(OLIVE)], 3: [F("birth", 336, 341)],
  4: [F("birth", 866, 871)], 5: [F("birth", 856, 861, note="20,000 POUNDS")], 6: [P(XB29, whole=True)],
  7: [F("birth", 1001, 1006)], 8: [F("birth", 911, 917)], 9: [F("birth", 287, 293)], 10: [F("birth", 976, 981)],
  11: [P(XB29, zoom=1.3, x=0.35, note="XB-29")], 12: [F("birth", 366, 371)], 13: [F("birth", 421, 427)],
  14: [F("birth", 776, 782, note="500 BOMBERS")]},
 # 2 The Most Expensive Weapon
 {1: [F("birth", 441, 447)], 2: [P(LINE, note="FOUR FACTORIES")], 3: [F("birth", 371, 376)],
  4: [F("birth", 787, 792)], 5: [F("birth", 496, 501), F("birth", 856, 860)],
  6: [F("birth", 1186, 1192, note="31,850 FEET")], 7: [F("birth", 726, 731)],
  8: [F("birth", 561, 567), F("birth", 572, 576)], 9: [P(TURRET)], 10: [F("airwar", 420, 426)],
  11: [F("tokyo", 381, 386)], 12: [F("tokyo", 1146, 1150)], 13: [F("airwar", 421, 425)], 14: [F("birth", 801, 807)],
  15: [P(WICHITA, note="THREE BILLION DOLLARS")], 16: [F("tokyo", 151, 157)]},
 # 3 Fire in Seattle
 {1: [F("birth", 816, 821, label="SEATTLE · 21 SEPTEMBER 1942")], 2: [F("birth", 491, 496)],
  3: [F("birth", 496, 501)], 4: [F("birth", 1170, 1174, note="EDMUND T. ALLEN")], 5: [F("birth", 340, 345)],
  6: [F("birth", 506, 511)], 7: [F("tokyo", 851, 856)], 8: [F("birth", 760, 764)], 9: [F("birth", 489, 493)],
  10: [F("tokyo", 966, 972, sfx="plane_flyby")], 11: [F("birth", 665, 671)], 12: [F("birth", 746, 751)],
  13: [F("birth", 702, 708, note="ONLY 15 AIRWORTHY")], 14: [F("tokyo", 1301, 1307, note="BATTLE OF KANSAS")],
  15: [F("birth", 788, 794)]},
 # 4 Over the Hump
 {1: [P(OLIVE, zoom=1.2, x=0.6)], 2: [F("tokyo", 401, 406)], 3: [P(FDR)],
  4: [MAP([PL("INDIA", 22.33, 87.32), PL("CHENGDU", 30.66, 104.07), PL("YAWATA", 33.87, 130.8)], [[0, 1], [1, 2]],
          note="OPERATION MATTERHORN")],
  5: [F("birth", 1056, 1061)], 6: [F("birth", 1186, 1196, note="THE HUMP")], 7: [P(CHENGDU)],
  8: [F("birth", 1136, 1142, sfx="plane_flyby")], 9: [F("birth", 1150, 1155)], 10: [F("tokyo", 1261, 1266)],
  11: [F("birth", 976, 981, note="YAWATA")], 12: [F("tokyo", 1236, 1243, sfx="bomb_drop")],
  13: [F("birth", 1086, 1092)], 14: [F("birth", 1101, 1107)]},
 # 5 Stalin's Copy
 {1: [F("tokyo", 481, 486)], 2: [F("tokyo", 1041, 1047, note="RAMP TRAMP")],
  3: [MAP([PL("MANCHURIA", 41.12, 122.99), PL("VLADIVOSTOK", 43.12, 131.89)], [[0, 1]])],
  4: [F("tokyo", 991, 996)], 5: [P(STALIN)], 6: [F("tokyo", 1061, 1066)], 7: [F("tokyo", 471, 476)],
  8: [P(COLOR_FLIGHT, zoom=1.3, x=0.4)], 9: [P(STALIN, zoom=1.3, y=0.2, note="TUPOLEV")], 10: [F("birth", 336, 341)],
  11: [F("birth", 491, 496)], 12: [F("tokyo", 991, 996, note="TUPOLEV TU-4")], 13: [F("birth", 1001, 1006)],
  14: [F("tokyo", 1046, 1051)]},
 # 6 Islands in Range
 {1: [F("birth", 1186, 1192)],
  2: [MAP([PL("SAIPAN", 15.18, 145.75), PL("TOKYO", 35.68, 139.69)], [[0, 1]], note="1,500 MILES")],
  3: [F("tokyo", 495, 500, sfx="artillery", label="SAIPAN · 15 JUNE 1944")], 4: [F("tokyo", 501, 505)],
  5: [F("tokyo", 520, 525)], 6: [P(NORTHFIELD)], 7: [P(ISELY, note="180 B-29s")], 8: [P(HARD)],
  9: [F("tokyo", 551, 557, sfx="plane_flyby")], 10: [F("tokyo", 1201, 1206)],
  11: [F("tokyo", 966, 972, note="111 B-29s")], 12: [F("tokyo", 822, 827, note="DAUNTLESS DOTTY"), F("tokyo", 926, 931)],
  13: [F("tokyo", 1150, 1155)], 14: [F("tokyo", 1206, 1211)], 15: [F("tokyo", 1136, 1141)]},
 # 7 LeMay's Gamble
 {1: [P(ARNOLD)], 2: [P(LEMAY, note="CURTIS LEMAY")], 3: [F("tokyo", 1121, 1126)], 4: [P(GROUP)],
  5: [F("tokyo", 1061, 1066, note="5,000 FEET")], 6: [F("airwar", 515, 520)], 7: [F("airwar", 420, 425)],
  8: [F("tokyo", 296, 302, sfx="plane_flyby", label="TOKYO · 9 MARCH 1945")], 9: [P(LEMAY, zoom=1.3, y=0.2)],
  10: [F("tokyo", 721, 726)], 11: [F("airwar", 546, 551, sfx="explosion_far"), F("airwar", 571, 576)],
  12: [F("airwar", 556, 561)], 13: [P(RUINS)], 14: [P(RUINS2)], 15: [F("airwar", 601, 607)],
  16: [MAP([PL("TOKYO", 35.68, 139.69), PL("NAGOYA", 35.18, 136.91), PL("OSAKA", 34.69, 135.5)], [])],
  17: [F("airwar", 626, 631)]},
 # 8 Silverplate
 {1: [P(B498)], 2: [P(ENOLA, note="SILVERPLATE")], 3: [F("birth", 911, 917)], 4: [P(LITTLE_BOY)],
  5: [F("tokyo", 852, 856)], 6: [F("tokyo", 1216, 1221)], 7: [P(TIBBETS, note="ENOLA GAY")],
  8: [P(SWEENEY, note="BOCKSCAR")],
  9: [MAP([PL("TINIAN", 15.0, 145.63), PL("HIROSHIMA", 34.39, 132.45), PL("NAGASAKI", 32.75, 129.87),
           PL("OKINAWA", 26.33, 127.8)], [[0, 1], [0, 2], [2, 3]])],
  10: [F("airwar", 705, 710)], 11: [P(OVER_TOKYO, note="OPERATION STARVATION")], 12: [F("airwar", 625, 630)],
  13: [P(PW)]},
 # 9 The Last Missions
 {1: [F("airwar", 721, 726)], 2: [P(GROUP, zoom=1.15)], 3: [F("birth", 801, 807)], 4: [F("airwar", 751, 757)],
  5: [P(KOREA)], 6: [P(KOREA_BOMBS, note="MIG-15")], 7: [P(KOREA, zoom=1.3, x=0.6)], 8: [F("tokyo", 1041, 1046)],
  9: [F("airwar", 791, 796)], 10: [F("birth", 856, 861)], 11: [F("birth", 1031, 1036)],
  12: [F("birth", 788, 793, note="3,970 BUILT")], 13: [P(COLOR_FLIGHT)], 14: [P(ENOLA, zoom=1.25, y=0.2)],
  15: [F("birth", 911, 918)]},
]

chapters = []
for (title, mode, sents), plan in zip(CH, SHOTS):
    assert set(plan) == set(range(1, len(sents) + 1)), (title, sorted(plan), len(sents))
    shots = [{"s": s, **x} for s in sorted(plan) for x in plan[s]]
    chapters.append({"title": title, "mode": mode, "sentences": sents, "shots": shots})

d = {
 "priority": 6, "format": "entire", "topic": "Boeing B-29 Superfortress",
 "sources": ["Operation Meetinghouse", "Air raids on Japan"],
 "title": "The ENTIRE History of the B-29 Superfortress in {N} Minutes",
 "thumb": {"file": COLOR_FLIGHT},
 "cover": {"file": KOREA, "color": False, "x": 0.6, "y": 0.0,
           "note": "A1 (Andrii, Nov 10): black and white, the B-29s under the words, not behind them",
           "variants": [{"file": COLOR_FLIGHT, "y": 0.62, "zoom": 1.1, "note": "one B-29 under the words"}]},
 "question": "Did the B-29 win the war against Japan?",
 "summary": ("The Boeing B-29 Superfortress was the most expensive weapons program of World War II: its $3 billion "
             "cost exceeded the Manhattan Project's. Designed from 1938 as a pressurized long-range 'superbomber' "
             "with remote-controlled turrets, it suffered deadly engine fires and production delays, flew its first "
             "missions from India and China over the Himalayas, then from new bases in the Mariana Islands. From "
             "March 1945 Curtis LeMay sent it low, at night, with incendiaries, against Japanese cities; Silverplate "
             "B-29s Enola Gay and Bockscar dropped the atomic bombs on Hiroshima and Nagasaki. Four interned bombers "
             "became the Soviet Tu-4. B-29s fought again in Korea; 3,970 were built."),
 "tags": ["B-29", "B-29 Superfortress", "Superfortress", "Boeing B-29", "Curtis LeMay", "Enola Gay", "Bockscar",
          "Operation Meetinghouse", "Tokyo firebombing", "air raids on Japan", "Tupolev Tu-4", "Hap Arnold",
          "WW2 bomber", "Pacific War", "Silverplate"],
 "pronounce": {"Chengdu": "Cheng-doo", "Yawata": "Ya-wah-ta", "Tupolev": "Too-po-lev", "Matterhorn": "Matter-horn",
               "Vladivostok": "Vla-di-vos-tok", "LeMay": "Le-May"},
 "films": {
  "birth": {"url": "https://archive.org/download/Birthoft1945/Birthoft1945.mp4", "mono": True,
            "credit": "Birth of the B-29 (1945): US War Department / Army Pictorial Service film (public domain, via Internet Archive)"},
  "tokyo": {"url": "https://archive.org/download/TargetTokyo/TargetTokyo.mp4", "mono": True,
            "credit": "Target Tokyo (1945): Army Air Forces First Motion Picture Unit (public domain, via Internet Archive)"},
  "airwar": {"url": "https://archive.org/download/gov.dod.dimoc.26162/gov.dod.dimoc.26162_512kb.mp4", "mono": True,
             "credit": "The Air Force Story: Air War Against Japan (1953): US Department of Defense, DIMOC 26162 (public domain, via Internet Archive)"},
 },
 "chapters": chapters,
 "clips": [
  {"from": [0, 1], "to": [0, 4], "title": "WHY THE B-29 LOST ITS GUNS", "key": ["B-29"],
   "name": "Why LeMay Ordered the Guns Taken Out of His B-29s"},
  {"from": [5, 1], "to": [5, 8], "title": "STALIN'S B-29", "key": ["B-29"],
   "name": "Four B-29s Landed in the Soviet Union. Stalin Never Gave Them Back"},
 ],
}
pathlib.Path("stories/long/b29.json").write_bytes((json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in chapters for s in c["sentences"])
print("written: chapters", len(chapters), "sentences", sum(len(c["sentences"]) for c in chapters), "words", words)
