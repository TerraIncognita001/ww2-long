"""D-Day (Normandy landings), Nov 15: the first hand story in the full new format (INTRO with Roosevelt's D-Day
prayer, chapter stamps, silent beats, a BBC recording and a quoted correspondent, coloured portrait reveals, clock
stamps, two-sided maps, newspapers of 7 June 1944, the verdict ending, 2 promo teasers).
Facts: Wikipedia 'Normandy landings' (the whole article). Run: python tools/stories/dday_build.py"""
import json, pathlib

J = "Into the Jaws of Death 23-0455M edit.jpg"
TEH = "Teheran conference-1943.jpg"
TEH2 = "Allied leaders at the 1943 Tehran Conference.jpg"
IKE = "Dwight D. Eisenhower as General of the Army.jpg"
IKE_PARA = "Eisenhower d-day.jpg"
MONTY = "Field Marshal Sir Bernard Montgomery, 1944 TR2721.jpg"
ROMMEL = "Bundesarchiv Bild 146-1973-012-43, Erwin Rommel.jpg"
PATTON = "George S. Patton 06.jpg"
STAGG = "Operation Overlord (the Normandy Landings)- D-day 6 June 1944- Personalities CH14235.jpg"
DUMMY = "Dummy Vehicles and Equipment USED For Deception during the Second World War H42531.jpg"
TRJR = ("SC 191911 - Brig. Gen. Theodore Roosevelt, Jr., poses before the door to his CP on the day he died from heart "
        "attack while on active service. St. Mere Eglise, France. 12 July, 1944.jpg")
MUL_BUILD = "Construction of Mulberry Harbours, Southampton, April 1944 A25792.jpg"
MUL = "The Mulberry artificial harbour at Arromanches in Normandy, June 1944. A24675.jpg"
MUL2 = "MulberryB - Piers.jpg"
PEG = "Pegasus Bridge, June 1944 B5288.jpg"
GLIDERS = "Operation Deadstick canal bridge gliders.jpg"
PARA_C47 = "US Paratrooper of 101st Airborne Division climbing aboard a C-47.jpg"
SME = "St. Mere Eglise 1944.jpg"
SME2 = "Soldiers in St. Mere-Eglise, France - DPLA - 347058026fca487dcc2ac595deb3cbb8.jpg"
OMAHA_APP = "Infantry landing craft approach Omaha Beach in June 1944.jpg"
OMAHA_SMOKE = "Smoking LCVP off Omaha Beach 6 June 1944.jpg"
OMAHA_WADE = "Troops wade ashore at Omaha Beach from a LCVP landing craft.jpg"
OMAHA_FIRST = "Omaha Beach First Wave.jpg"
PAK = "German 8.8cm Pak 43 at Omaha Beach, Normandy, in June 1944 (26-G-2398).jpg"
UTAH = "Utah Beach Landing.jpg"
UTAH2 = "Normandy Invasion on Utah Beach - DPLA - 1146519af08fec5feedb29d914b999f7.jpg"
UTAH_SHIPS = "Warships bombard targets ashore in support of the D-Day landings on Utah Beach, 6 June 1944.jpg"
E1 = "2nd Infantry Division, E-1 draw, Easy Red sector, Omaha Beach, D+1, June 7, 1944.jpg"
RANGERS = "Rangers-pointe-du-hoc.jpg"
RANGERS2 = "Soldiers at Pointe du Hoc.jpg"
SWORD = "Landing on Queen Red Beach, Sword Area.jpg"
SWORD2 = ("British troops from 3rd Division, some with bicycles, move inland from Sword Beach, Normandy, 6 June 1944. "
          "B5078.jpg")
COMMANDOS = "Royal Marine Commandos attached to 3rd Division move inland from Sword Beach on the Normandy coast, 6 June 1944. B5071.jpg"
JUNO = "Canadian landings at Juno Beach.jpg"
JUNO2 = "Canadian Soldiers Juno Beach Town.jpg"
JUNO3 = ("Follow-up waves of the 9th Canadian Infantry Brigade disembarking with bicycles from landing craft onto 'Nan "
         "White' sector of Juno Beach at Bernieres-sur-Mer, 6 June 1944. A23938.jpg")
GOLD = "The British Army in the Normandy Campaign 1944 B5234.jpg"
SUPPLY = "NormandySupply edit.jpg"
DEDAG = 'Voorpagina "De Dag" 7 Juni 1944 met hoofdnieuws "Invasie in Normandie Begonnen".jpg'
GAZET = ('Voorpagina "De Gazet" 7 Juni 1944 met hoofdnieuws "de Invasie heeft aanvang genomen\' verwijzend naar de '
         'geallieerde landing in Normandië.jpg')
HLN = 'Voorpagina Vlaams dagblad "Het Laatste Nieuws" 7 Juni 1944.jpg'

FDR_SRC = "PRESIDENT ROOSEVELT · RADIO, JUNE 6, 1944"
BYAM_SRC = "GUY BYAM · BBC WAR REPORT, JUNE 1944"
PAPERS = "OCCUPIED BELGIUM · FRONT PAGES, 7 JUNE 1944"

M_CHANNEL = {"places": [{"label": "PORTSMOUTH", "lat": 50.80, "lon": -1.09, "side": "blue"},
                        {"label": "UTAH", "lat": 49.42, "lon": -1.18}, {"label": "OMAHA", "lat": 49.37, "lon": -0.88},
                        {"label": "GOLD", "lat": 49.34, "lon": -0.58}, {"label": "JUNO", "lat": 49.33, "lon": -0.40},
                        {"label": "SWORD", "lat": 49.29, "lon": -0.27}],
             "routes": [[0, 2, "blue", 0.12], [0, 5, "blue", -0.08]], "pad": 0.25}
M_SITES = {"places": [{"label": "PAS-DE-CALAIS", "lat": 50.95, "lon": 1.86}, {"label": "NORMANDY", "lat": 49.18, "lon": -0.37},
                      {"label": "COTENTIN", "lat": 49.64, "lon": -1.62}, {"label": "BRITTANY", "lat": 48.39, "lon": -4.49}],
           "routes": [], "pad": 0.3}
M_GHOST = {"places": [{"label": "KENT", "lat": 51.13, "lon": 1.31, "side": "blue"}, {"label": "CALAIS", "lat": 50.95, "lon": 1.86},
                      {"label": "PORTSMOUTH", "lat": 50.80, "lon": -1.09, "side": "blue"},
                      {"label": "NORMANDY", "lat": 49.30, "lon": -0.60}],
           "routes": [[0, 1, "red", 0.2], [2, 3, "blue", -0.1]], "pad": 0.3}

C = [
 {"title": "", "mode": "action", "sentences": [
  "These are the Normandy landings, the largest seaborne invasion in history.",
  "Nearly 160,000 troops cross the English Channel in a single day.",
  "For two years, the Germans have been fortifying this coast with guns, mines and obstacles.",
  "But on the day of the invasion, their commander, Erwin Rommel, is at home in Germany, for his wife's birthday.",
  "And a whole Allied army, waiting across the Channel, does not even exist.",
  "This is the entire history of D-Day."],
  "shots": [
   {"s": 1, "file": J, "note": "D-DAY"},
   {"s": 2, "film": "news", "from": 336, "to": 342, "note": "160,000 TROOPS"},
   {"s": 3, "film": "news", "from": 68, "to": 74},
   {"s": 3, "film": "news", "from": 100, "to": 106, "sfx": "artillery"},
   {"s": 4, "file": ROMMEL, "reveal": [0.62, 0.2], "name": "ERWIN ROMMEL", "role": "FIELD MARSHAL"},
   {"s": 5, "file": DUMMY, "note": "A FAKE ARMY"},
   {"s": 6, "film": "news", "from": 244, "to": 250}]},
 {"title": "The Second Front", "mode": "people", "stamp": ["TEHRAN", "1943"], "sentences": [
  "In November 1943, at the Tehran Conference, Roosevelt and Churchill promise Stalin a second front in May 1944.",
  "Stalin has been pressing for it since the German Army invaded the Soviet Union in June 1941.",
  "Churchill has held it back, because the Allies do not yet have enough forces for such an attack.",
  "Instead, they fight in North Africa, and then land in Sicily and on the Italian mainland in 1943.",
  "For the return to France, four places are considered: Brittany, the Cotentin Peninsula, Normandy, and the Pas-de-Calais.",
  "The Pas-de-Calais is the closest point to Britain, so the Germans expect the landings there.",
  "Normandy is chosen instead, because a broad landing there threatens the port of Cherbourg, Brittany, and the road to Paris.",
  "Its great drawback is that it has no port, so the Allies decide to bring their own: artificial Mulberry harbours.",
  "General Dwight D. Eisenhower is given command of the whole operation.",
  "General Bernard Montgomery commands all the forces on land.",
  "On 31 December 1943, the two generals see the plan for the first time.",
  "It lands three divisions, and they insist on five, with three more divisions dropped from the air.",
  "The extra landing craft this needs push the invasion back from May to June.",
  "In the end, thirty-nine Allied divisions will fight in the Battle of Normandy, over a million troops."],
  "shots": [
   {"s": 1, "file": TEH, "label": "TEHRAN · NOVEMBER 1943"},
   {"s": 2, "file": TEH2, "x": 0.3},
   {"s": 3, "film": "news", "from": 34, "to": 40},
   {"s": 4, "film": "news", "from": 134, "to": 140},
   {"s": 5, "map": M_SITES},
   {"s": 6, "film": "news", "from": 126, "to": 132},
   {"s": 7, "film": "news", "from": 46, "to": 51},
   {"s": 8, "file": MUL_BUILD, "note": "MULBERRY HARBOURS"},
   {"s": 9, "file": IKE, "name": "DWIGHT D. EISENHOWER", "role": "SUPREME COMMANDER"},
   {"s": 10, "file": MONTY, "name": "BERNARD MONTGOMERY", "role": "COMMANDER, LAND FORCES"},
   {"s": 11, "film": "news", "from": 40, "to": 45},
   {"s": 12, "film": "news", "from": 392, "to": 396, "note": "FIVE DIVISIONS"},
   {"s": 13, "film": "news", "from": 194, "to": 199}]},
 {"title": "Rommel's Wall", "mode": "people", "stamp": ["ATLANTIC WALL"], "sentences": [
  "After British raids on St Nazaire and Dieppe in 1942, Hitler orders a line of fortifications along the Atlantic coast, from Spain to Norway.",
  "He wants 15,000 gun emplacements, manned by 300,000 troops.",
  "Short of concrete and men, most of them are never built.",
  "The men who hold the coast are, on average, six years older than their Allied opponents.",
  "Many are conscripts and volunteers from the Soviet Union, with captured equipment and little transport.",
  "Field Marshal Erwin Rommel is sent to strengthen the coast where the invasion is expected.",
  "He believes Germany's best chance is to stop the invasion on the beaches.",
  "He covers them with wooden stakes, metal tripods, mines and anti-tank obstacles.",
  "On his order, the number of mines along the coast is tripled.",
  "In the meadows behind, booby-trapped stakes wait for airborne landings: Rommel's asparagus.",
  "Rommel wants the tanks stationed close to the coast.",
  "His superiors want them kept back, around Paris and Rouen, until the main landing is known.",
  "Hitler splits them, and keeps four divisions that cannot move without his direct orders.",
  "Above it all, the Allies rule the sky: 9,543 aircraft against the Luftwaffe's 815.",
  "Shortly before the invasion, Rommel reports that in some areas the work is only 18 per cent complete."],
  "shots": [
   {"s": 1, "film": "news", "from": 64, "to": 68},
   {"s": 2, "film": "news", "from": 76, "to": 81, "note": "15,000 EMPLACEMENTS"},
   {"s": 3, "film": "news", "from": 82, "to": 87},
   {"s": 4, "file": ROMMEL, "x": 0.5, "y": 0.2, "zoom": 1.3},
   {"s": 5, "film": "news", "from": 96, "to": 100},
   {"s": 6, "film": "news", "from": 70, "to": 75},
   {"s": 7, "film": "news", "from": 112, "to": 117},
   {"s": 8, "film": "news", "from": 118, "to": 124, "note": "ROMMEL'S ASPARAGUS"},
   {"s": 9, "film": "news", "from": 106, "to": 111, "sfx": "artillery"},
   {"s": 10, "film": "news", "from": 140, "to": 145},
   {"s": 11, "film": "news", "from": 144, "to": 149},
   {"s": 12, "film": "news", "from": 158, "to": 163, "sfx": "plane_flyby", "note": "9,543 AIRCRAFT"}]},
 {"title": "The Ghost Army", "mode": "people", "stamp": ["KENT", "1944"], "sentences": [
  "To keep the Germans watching Calais, the Allies create an army that does not exist.",
  "It is called the First United States Army Group, under Lieutenant General George S. Patton.",
  "Its camps are supposedly in Kent and Sussex, and its radio messages are real, routed there from the true army.",
  "Fake radio traffic also points to an attack on Norway.",
  "Many German radar stations on the French coast are destroyed in the week before the invasion.",
  "On the night itself, dummy paratroopers are dropped over Le Havre and Isigny.",
  "Bombers drop strips of metal foil, which German radar reads as a naval convoy near Le Havre.",
  "The French Resistance waits for coded messages read out on the BBC.",
  "On 5 June, the radio traffic rises, and German intelligence reads it correctly: the invasion is coming.",
  "But after so many false warnings, most German units ignore it.",
  "Patton stays in England until 6 July, and the Germans keep waiting for a second landing at Calais."],
  "shots": [
   {"s": 1, "map": M_GHOST},
   {"s": 2, "file": PATTON, "name": "GEORGE S. PATTON", "role": "LIEUTENANT GENERAL"},
   {"s": 3, "file": DUMMY, "zoom": 1.15},
   {"s": 4, "film": "news", "from": 352, "to": 356},
   {"s": 5, "film": "news", "from": 108, "to": 112},
   {"s": 6, "film": "news", "from": 418, "to": 421, "sfx": "plane_flyby"},
   {"s": 7, "film": "news", "from": 408, "to": 413, "note": "METAL FOIL"},
   {"s": 8, "film": "news", "from": 344, "to": 349},
   {"s": 9, "film": "news", "from": 126, "to": 131},
   {"s": 10, "film": "news", "from": 130, "to": 134}]},
 {"title": "The Forecast", "mode": "people", "stamp": ["4 JUNE", "1944"], "sentences": [
  "On 4 June 1944, high winds and heavy seas make it impossible to launch the landing craft.",
  "Eisenhower has chosen 5 June for the assault.",
  "That evening, Group Captain James Stagg of the Royal Air Force brings him a forecast.",
  "The weather will improve enough to land on 6 June.",
  "The next days with the right tides are two weeks away, from 18 to 20 June.",
  "Waiting would mean recalling men and ships, and the plans might be discovered.",
  "Eisenhower decides that the invasion goes ahead on 6 June.",
  "The Germans read the same sky differently.",
  "Their forecasters in Paris predict two weeks of storms.",
  "Many commanders leave their posts for war games in Rennes, and many men are given leave.",
  "Rommel drives home to Germany, for his wife's birthday.",
  "From 19 to 22 June, a major storm batters the Normandy coast.",
  "On the later date, the landings would have been impossible."],
  "shots": [
   {"s": 1, "film": "news", "from": 254, "to": 259, "sfx": "storm_wind"},
   {"s": 2, "file": IKE, "zoom": 1.2, "y": 0.3},
   {"s": 3, "file": STAGG, "name": "JAMES STAGG", "role": "CHIEF METEOROLOGIST, RAF"},
   {"s": 4, "film": "news", "from": 336, "to": 341},
   {"s": 5, "film": "news", "from": 232, "to": 237},
   {"s": 6, "film": "news", "from": 266, "to": 271},
   {"s": 7, "file": IKE_PARA, "label": "ENGLAND · 5 JUNE 1944"},
   {"s": 8, "film": "news", "from": 126, "to": 130},
   {"s": 9, "film": "dday", "from": 196, "to": 201},
   {"s": 10, "film": "news", "from": 56, "to": 59},
   {"s": 11, "film": "news", "from": 60, "to": 63},
   {"s": 12, "film": "dday", "from": 202, "to": 207, "sfx": "storm_wind"}]},
 {"title": "Night Drop", "mode": "action", "stamp": ["MIDNIGHT"], "sentences": [
  "Shortly after midnight on 6 June, the invasion begins from the air.",
  "In all, 24,000 American, British and Canadian airborne troops are landed behind the beaches.",
  "At 00:16, British gliders land beside two bridges over the Caen canal and the River Orne.",
  "Both bridges are captured quickly, and intact.",
  "One of them is later renamed Pegasus Bridge.",
  "The American paratroopers fly in through a bank of thick cloud.",
  "Only one of their five drop zones is marked correctly.",
  "Many land far from their targets, and some drown in flooded fields.",
  "Within two hours, the 82nd Airborne captures the crossroads at Sainte-Mère-Église.",
  "It is the first town liberated in the invasion.",
  "To the east, a British battalion must destroy the Merville gun battery before 06:00.",
  "Only 160 of its 600 men reach the meeting point, and they attack anyway.",
  "They disable the guns, and find that they are smaller than expected.",
  "After a full day, only about a third of the American paratroopers are under the control of their divisions.",
  "But scattered everywhere, they confuse the Germans.",
  "The German 7th Army hears of the drops at 01:20, but Rundstedt does not at first believe that a major invasion is under way."],
  "shots": [
   {"s": 1, "film": "news", "from": 392, "to": 397, "sfx": "plane_flyby"},
   {"s": 2, "film": "news", "from": 398, "to": 403, "note": "24,000 AIRBORNE TROOPS"},
   {"s": 3, "file": GLIDERS, "stamp": ["00:16"]},
   {"s": 4, "file": PEG},
   {"s": 5, "file": PEG, "zoom": 1.3, "note": "PEGASUS BRIDGE"},
   {"s": 6, "film": "news", "from": 408, "to": 412},
   {"s": 7, "film": "news", "from": 422, "to": 426},
   {"s": 8, "film": "news", "from": 440, "to": 445},
   {"s": 9, "file": SME, "label": "SAINTE-MÈRE-ÉGLISE · 6 JUNE 1944"},
   {"s": 10, "file": SME2},
   {"s": 11, "film": "news", "from": 446, "to": 449},
   {"s": 12, "film": "news", "from": 430, "to": 435}],
  "beats": [
   {"after": 2, "quote": {"text": "This was the first combat jump for every one of them.", "name": "ROBERT BARR",
                          "role": "BBC WAR CORRESPONDENT"},
    "shots": [{"dur": 5, "file": PARA_C47}]},
   {"after": 7, "audio": {"src": "byam", "from": 20.0, "to": 29.3}, "source": BYAM_SRC,
    "shots": [{"dur": 3.5, "film": "news", "from": 432, "to": 437, "sfx": "plane_flyby"},
              {"dur": 3.5, "film": "news", "from": 436, "to": 441},
              {"dur": 3.5, "film": "news", "from": 442, "to": 447}]}]},
 {"title": "Bloody Omaha", "mode": "action", "stamp": ["05:45"], "sentences": [
  "At 05:45, the warships open fire on the coast, while it is still dark.",
  "The American beaches get only about 40 minutes of it before the troops land.",
  "At 06:30, the first Americans come ashore on Utah and Omaha.",
  "On Utah, strong currents push them far to the south of their target.",
  "It turns out to be a better place, with only one strongpoint nearby.",
  "Brigadier General Theodore Roosevelt Jr. decides to start the war from right here.",
  "Utah lands 21,000 troops, at the cost of only 197 casualties.",
  "Omaha is the most heavily defended beach.",
  "Most of the amphibious tanks sent in flood and sink before they reach the shore.",
  "Many landing craft run aground on sandbars, far from the beach.",
  "Afraid of hitting the landing craft, the bombers released their loads too late, and the obstacles still stand.",
  "Men wade 50 to 100 metres in water up to their necks, under fire from the cliffs.",
  "The only ways off the beach are five heavily defended gullies.",
  "At 08:30, the landing of vehicles on Omaha is halted.",
  "By late morning, barely 600 men have reached the higher ground.",
  "By noon, the Germans start to run out of ammunition, and the Americans begin to clear the way off the beach.",
  "The price of Omaha is around two thousand casualties."],
  "shots": [
   {"s": 1, "film": "news", "from": 456, "to": 461, "sfx": "artillery"},
   {"s": 2, "file": UTAH_SHIPS},
   {"s": 3, "map": M_CHANNEL, "stamp": ["06:30"]},
   {"s": 4, "file": UTAH, "label": "UTAH BEACH · 6 JUNE 1944"},
   {"s": 5, "file": UTAH2},
   {"s": 6, "file": TRJR, "name": "THEODORE ROOSEVELT JR.", "role": "BRIGADIER GENERAL"},
   {"s": 7, "film": "dday", "from": 256, "to": 261, "note": "197 CASUALTIES"},
   {"s": 8, "file": OMAHA_APP, "label": "OMAHA BEACH · 6 JUNE 1944"},
   {"s": 9, "film": "news", "from": 496, "to": 501, "note": "THE TANKS SINK"},
   {"s": 10, "file": PAK},
   {"s": 11, "file": J},
   {"s": 12, "file": OMAHA_SMOKE, "stamp": ["08:30"]},
   {"s": 13, "film": "news", "from": 532, "to": 535, "note": "600 MEN"},
   {"s": 14, "file": E1},
   {"s": 15, "file": OMAHA_FIRST}],
  "beats": [
   {"after": 11, "shots": [{"dur": 3, "film": "news", "from": 504, "to": 508, "sfx": "explosion_far"},
                           {"dur": 3, "film": "news", "from": 512, "to": 516},
                           {"dur": 3, "film": "news", "from": 520, "to": 524, "sfx": "explosion_battle"},
                           {"dur": 3, "film": "news", "from": 540, "to": 544},
                           {"dur": 3, "film": "news", "from": 556, "to": 560}]}]},
 {"title": "Cliffs and Beaches", "mode": "action", "stamp": ["POINTE DU HOC"], "sentences": [
  "Between Utah and Omaha rise the cliffs of Pointe du Hoc, with a German gun battery on top.",
  "Two hundred Rangers under Lieutenant Colonel James Rudder climb them with ropes, ladders and grappling hooks.",
  "At the top, they find that the guns have been withdrawn.",
  "They track them down in an orchard, unguarded, and disable them with explosives.",
  "Cut off, they fight off counter-attacks for two days.",
  "By dawn the next day, Rudder has only 90 men able to fight.",
  "To the east, the British and Canadians land on Gold, Juno and Sword.",
  "On Gold, cruisers knock out three of the four guns of the Longues-sur-Mer battery.",
  "Company Sergeant Major Stanley Hollis wins the only Victoria Cross awarded on D-Day.",
  "On Juno, the Canadians clear the fortified seaside towns house by house.",
  "On Sword, Lord Lovat's commandos come ashore to the bagpipes of his piper, Bill Millin.",
  "French commandos under Philippe Kieffer, the first French soldiers to arrive in Normandy, clear the strongpoint at the casino of Riva Bella.",
  "At 16:00, the 21st Panzer Division counter-attacks, and nearly reaches the Channel.",
  "It meets stiff resistance from the British 3rd Division, and is soon recalled."],
  "shots": [
   {"s": 1, "film": "news", "from": 538, "to": 541},
   {"s": 2, "file": RANGERS, "name": "JAMES RUDDER'S RANGERS", "role": "2ND RANGER BATTALION"},
   {"s": 3, "file": RANGERS2},
   {"s": 4, "film": "news", "from": 546, "to": 549, "sfx": "explosion_close"},
   {"s": 5, "film": "news", "from": 548, "to": 552, "note": "90 MEN"},
   {"s": 6, "file": GOLD},
   {"s": 7, "film": "news", "from": 462, "to": 467, "sfx": "artillery"},
   {"s": 8, "file": COMMANDOS},
   {"s": 9, "file": JUNO, "label": "JUNO BEACH · 6 JUNE 1944"},
   {"s": 10, "file": SWORD, "label": "SWORD BEACH · 6 JUNE 1944"},
   {"s": 11, "film": "news", "from": 290, "to": 294, "stamp": ["16:00"], "sfx": "tank_engine"},
   {"s": 12, "file": SWORD2}],
  "beats": [
   {"after": 6, "shots": [{"dur": 3.5, "film": "dday", "from": 312, "to": 318, "sfx": "tank_engine"},
                          {"dur": 3.5, "film": "dday", "from": 346, "to": 352},
                          {"dur": 3.5, "file": JUNO3},
                          {"dur": 3.5, "file": JUNO2}]}]},
 {"title": "The Beachhead", "mode": "people", "stamp": ["7 JUNE", "1944"], "sentences": [
  "By nightfall, the Allies hold a beachhead on each of the five beaches.",
  "Nearly 160,000 troops have crossed the Channel.",
  "It comes at a heavy price.",
  "At least 10,000 Allied soldiers are casualties, and 4,414 of them are confirmed dead.",
  "German losses are estimated in the thousands.",
  "French civilians suffer too, with some 3,000 casualties in the first two days.",
  "Many of the first day's objectives are missed.",
  "Caen, a major objective, will stay in German hands until 21 July.",
  "The five beachheads are not joined until 12 June.",
  "The Mulberry harbours arrive, and by the end of June, 875,000 men have landed.",
  "Rommel's wall is only partly finished, the deception has worked, and the Allies own the sky.",
  "Hitler's aim of throwing the Allies back into the sea is never achieved.",
  "On 30 August 1944, the German forces retreat east across the Seine, marking the close of Operation Overlord.",
  "The liberation of Western Europe has begun."],
  "shots": [
   {"s": 1, "film": "dday", "from": 134, "to": 140},
   {"s": 2, "film": "dday", "from": 298, "to": 304, "note": "160,000 TROOPS"},
   {"s": 3, "film": "dday", "from": 208, "to": 213, "note": "4,414 DEAD"},
   {"s": 4, "film": "dday", "from": 456, "to": 461},
   {"s": 5, "film": "dday", "from": 468, "to": 473},
   {"s": 6, "film": "dday", "from": 474, "to": 479},
   {"s": 7, "map": {"places": [{"label": "CAEN", "lat": 49.18, "lon": -0.37},
                               {"label": "BAYEUX", "lat": 49.28, "lon": -0.70, "side": "blue"},
                               {"label": "CARENTAN", "lat": 49.30, "lon": -1.25, "side": "blue"}],
                    "routes": [[1, 0, "blue", 0.15]], "pad": 0.4}},
   {"s": 8, "film": "dday", "from": 438, "to": 443},
   {"s": 9, "file": MUL, "note": "875,000 MEN"},
   {"s": 10, "file": MUL2},
   {"s": 11, "file": SUPPLY},
   {"s": 12, "film": "dday", "from": 420, "to": 425}],
  "beats": [
   {"after": 2, "source": PAPERS,
    "shots": [{"dur": 4.5, "file": DEDAG, "focus": [0.18, 0.12, 0.73, 0.205], "sfx": "typewriter"},
              {"dur": 4.5, "file": GAZET, "focus": [0.19, 0.16, 0.67, 0.22]},
              {"dur": 4.5, "file": HLN, "focus": [0.02, 0.135, 0.71, 0.19]}]}]},
]

def ins(ci, at, n=1):
    """Sentences inserted at `at` in chapter ci: the shots and beats from there move down by n."""
    for s in C[ci].get("shots") or []:
        if s["s"] >= at:
            s["s"] += n
    for b in C[ci].get("beats") or []:
        if b["after"] >= at:
            b["after"] += n


def add(ci, *shots):
    C[ci]["shots"] = sorted(C[ci]["shots"] + list(shots), key=lambda s: s["s"])


ins(2, 4, 2)                                           # Rommel's Wall: the men of the coast
add(2, {"s": 4, "film": "news", "from": 52, "to": 55}, {"s": 5, "film": "news", "from": 58, "to": 62},
    {"s": 15, "film": "news", "from": 86, "to": 89, "note": "18 PER CENT"})
add(1, {"s": 14, "film": "news", "from": 270, "to": 274, "note": "39 DIVISIONS"})
add(3, {"s": 11, "film": "news", "from": 140, "to": 144})
add(4, {"s": 13, "film": "news", "from": 336, "to": 341})
add(5, {"s": 15, "film": "news", "from": 404, "to": 407})
ins(5, 11, 3)                                          # Night Drop: Merville
add(5, {"s": 11, "film": "news", "from": 414, "to": 418, "label": "MERVILLE · 6 JUNE 1944"},
    {"s": 12, "film": "news", "from": 426, "to": 429, "note": "160 OF 600"},
    {"s": 13, "film": "news", "from": 482, "to": 486, "sfx": "explosion_close"})
ins(6, 10, 1)                                          # Omaha: sandbars
ins(6, 13, 1)                                          # Omaha: the gullies
add(6, {"s": 10, "film": "news", "from": 468, "to": 471}, {"s": 13, "film": "news", "from": 510, "to": 513})
ins(7, 5, 1)                                           # Pointe du Hoc: cut off
ins(7, 12, 1)                                          # Kieffer
add(7, {"s": 5, "file": RANGERS2, "zoom": 1.25}, {"s": 12, "file": SWORD2, "zoom": 1.2})
ins(8, 3, 1)                                           # the price
ins(8, 11, 1)                                          # why it worked
add(8, {"s": 3, "film": "dday", "from": 488, "to": 492}, {"s": 11, "film": "news", "from": 158, "to": 162})

STORY = {
 "priority": 7,
 "format": "entire",
 "topic": "Normandy landings",
 "sources": [],
 "title": "The ENTIRE History of D-Day in {N} Minutes",
 "question": "Could D-Day have failed without the ghost army?",
 "summary": ("On 6 June 1944, the Allies land in Normandy: the largest seaborne invasion in history. "
             "Promised to Stalin in Tehran, planned by Eisenhower and Montgomery, hidden behind a fake army under Patton "
             "and launched on a forecast by James Stagg, it puts nearly 160,000 troops ashore on the first day. "
             "From the airborne drop and Pegasus Bridge to Omaha, Pointe du Hoc and the Mulberry harbours, this is the "
             "whole story, told with archive film, the voices of the time and the newspapers of 7 June 1944."),
 "tags": ["D-Day", "Normandy landings", "Operation Overlord", "Omaha Beach", "Utah Beach", "Pointe du Hoc",
          "Pegasus Bridge", "Eisenhower", "Rommel", "Atlantic Wall", "Operation Fortitude", "WW2 documentary",
          "World War 2", "6 June 1944"],
 "pronounce": {"Sainte-Mère-Église": "Saint Mair Ay-gleez", "Isigny": "Ee-zeen-yee", "Longues-sur-Mer": "Long-sur-Mair",
               "Pointe du Hoc": "Pwant du Hock", "Rouen": "Roo-on"},
 "films": {
  "dday": {"url": "https://archive.org/download/NPC-15746/NPC-15746.mov", "mono": True,
           "credit": "D-Day: Normandy Invasion, 06/06/1944: US Coast Guard / NARA NPC-15746 (public domain, via Internet Archive)"},
  "news": {"url": "https://archive.org/download/ARC-39013/ARC-39013.mp4", "mono": True,
           "credit": "1944 Newsreel 'D-Day!': United News / NARA ARC 39013 (public domain, via Internet Archive)"}},
 "period_audio": {
  "fdr": {"file": "Prayer on D-Day (June 1944).ogg", "speaker": "Franklin D. Roosevelt", "date": "JUNE 6, 1944",
          "credit": "Franklin D. Roosevelt, Prayer on D-Day, radio address, 6 June 1944 (public domain, via Wikimedia Commons)",
          "text": "Our sons, pride of our Nation, this day have set upon a mighty endeavor"},
  "byam": {"file": "Guy Byam - D-Day parachute drop.flac", "speaker": "Guy Byam", "date": "JUNE 1944",
           "credit": "Guy Byam, BBC War Report: the D-Day parachute drop, June 1944 (public domain, via Wikimedia Commons)"}},
 "pre": [
  {"dur": 2.6, "film": "news", "from": 456, "to": 461, "sfx": "explosion_far"},
  {"dur": 2.8, "film": "news", "from": 472, "to": 477, "stamp": ["JUNE 6", "1944"], "sfx": "explosion_massive"},
  {"dur": 3.0, "film": "news", "from": 556, "to": 560, "stamp": ["NORMANDY"], "hush": True,
   "audio": {"src": "fdr", "from": 45.2, "to": 52.75}, "source": FDR_SRC},
  {"dur": 2.6, "film": "news", "from": 504, "to": 508, "source": FDR_SRC},
  {"dur": 2.8, "film": "news", "from": 468, "to": 471, "source": FDR_SRC}],
 "thumb": {"file": J},
 "cover": {"file": J, "x": 0.5, "y": 0.7, "zoom": 1.05, "color": False,
           "text": ["HISTORY OF", "D-DAY", "IN {N} MINUTES"], "key": ["D-DAY"], "sizes": [96, 150, 96], "mono": True},
 "promos": [
  {"id": "dday_weather", "chapter": 4,
   "sentences": ["On 4 June 1944, the sea is too rough to invade.", "A forecaster says the weather will improve, just enough.",
                 "The next chance is two weeks away."],
   "shots": [{"s": 1, "film": "news", "from": 254, "to": 259, "sfx": "storm_wind"},
             {"s": 2, "file": STAGG, "name": "JAMES STAGG"}, {"s": 3, "film": "news", "from": 336, "to": 341}],
   "top": "D-DAY HUNG|ON THE WEATHER", "key": ["D-DAY"], "cta": {"kind": "question"}, "end": "WHAT DID IKE DECIDE?",
   "name": "D-Day Depended on One Weather Forecast"},
  {"id": "dday_ghost", "chapter": 3,
   "sentences": ["To fool the Germans, the Allies create an army that does not exist.", "Its radio messages are real.",
                 "And its commander is a famous American general."],
   "shots": [{"s": 1, "file": DUMMY}, {"s": 2, "film": "news", "from": 344, "to": 349},
             {"s": 3, "map": M_GHOST}],
   "top": "THE D-DAY|GHOST ARMY", "key": ["D-DAY"], "cta": {"kind": "redacted", "line": "ITS COMMANDER:", "hidden": "PATTON"},
   "end": "WHO LED IT?", "name": "The Fake Army That Protected D-Day"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "dday.json"
out.write_text(json.dumps(STORY, ensure_ascii=False, indent=1), encoding="utf-8")
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
