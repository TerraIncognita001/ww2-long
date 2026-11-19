"""Dunkirk, Nov 19 (Andrii: 'пиши запас у два сценарії'): a hand story in the full format, like Pearl Harbor (INTRO
with Churchill's 'A tremendous battle is raging in France and Flanders' alone in the silence, chapter stamps, silent
beats, the Ghent 'Vooruit' of 10 May and the Brussels 'Het Algemeen Nieuws' of 30 May 1940, 3 second voices, portraits
with name plates, clock stamps, a two-sided map, the verdict ending, 2 CLIFF promo teasers).
Facts: Wikipedia 'Dunkirk evacuation' (whole) + 'Battle of Dunkirk' + 'Little Ships of Dunkirk'.
Films: Why We Fight 'Divide and Conquer' (1943, US War Department, public domain; the Commons 1920x1080 webm, 4:3
pillarboxed -> crop 1440:810:240:135; its Dunkirk part 2831-2934 s), UfA-Tonwoche Nr. 508 of 30 May 1940 (captured
German newsreel via Internet Archive; 640x480 -> crop 640:360:0:60; bodies at 1485 and 1735-1760: NOT used).
Run: python tools/stories/dunkirk_build.py"""
import collections, json, pathlib

# --- pictures (Wikimedia Commons; PD unless noted, Bundesarchiv = CC BY-SA 3.0 de, credited by longform) ---
BEACH_LINES = "Dunkirk 26-29 May 1940 NYP68075.jpg"
WAITING = "Dunkirk 1940 HU1137.jpg"                 # Royal Ulster Rifles at Bray Dunes: the cover
BEACH2 = "Dunkirk 1940 HU1135.jpg"
WADING = "Dunkirk 26 - 29 May 1940 HU41240.jpg"
MOLE = "Dunkirk 1940 HU1153.jpg"
MOLE_FR = "Dunkirk 1940 HU1150.jpg"
FENELLA = "Fenella at the East Mole, Dunkirk..jpeg"
BOURRASQUE = "Dunkirk 1940 HU2280.jpg"
MONA = "Dunkirk 1940 HU1145.jpg"
LITTLE = "Dunkirk 1940 HU41241.jpg"
DOVER = "Troops evacuated from Dunkirk on a destroyer about to berth at Dover, 31 May 1940. H1637.jpg"
HOME1 = "The British Army in the UK- Evacuation From Dunkirk, May-June 1940 H1661.jpg"
HOME2 = "The British Army in the UK- Evacuation From Dunkirk, May-June 1940 H1668.jpg"
TEA = ("Troops evacuated from Dunkirk enjoying tea and other refreshments at Addison Road station in London, "
       "31 May 1940. H1632.jpg")
BLANKET = "The British Army in the UK- Evacuation From Dunkirk, May-June 1940 H1619.jpg"
TIRED = "The British Army in the UK- Evacuation From Dunkirk, May-June 1940 H1643.jpg"
HOME3 = "The British Army in the UK- Evacuation From Dunkirk, May-June 1940 H1656.jpg"
OIL = "Dunkirk 26-29 May 1940 C1721.jpg"
AERIAL = "Dunkirk and the Retreat From France 1940 C1723.jpg"
OFFSHORE = "Dunkirk and the Retreat From France 1940 C1720.jpg"
AA = "Soldados británicos en Dunkerque en 1940.jpg"
LORRY_PIER = "HU 1860.jpg"
PRISONERS = "Bundesarchiv, Bild 101I-126-0339-19A, Veules-les-Roses, Kolonne alliierter Kriegsgefangener.jpg"
BEF1 = "The British Expeditionary Force (BEF) in France 1939-1940 F4404.jpg"
BEF2 = "The British Expeditionary Force (BEF) in France 1939-1940 F4331.jpg"
BEF3 = "The British Expeditionary Force (BEF) in France 1939-1940 F4451.jpg"
RETREAT1 = "Dunkirk and the Retreat From France 1940 HU104601.jpg"
RETREAT2 = "Dunkirk and the Retreat From France 1940 HU104603.jpg"
GORT = "British Generals 1939-1945 O177.jpg"
GORT2 = "Lord Gort.jpg"
GORT_FR = "The British Army in France 1939 O357.jpg"
GAMELIN = "Maurice Gamelin.jpg"
PETAIN = "Pétain vers 1940.jpg"
BILLOTTE = "Gaston-Henri Billotte (cropped).png"
RAMSAY = "Admiral Sir Bertram Ramsay TR2626.jpg"
TENNANT = "Vice Admiral Tennant 1945 IWM A 29072.jpg"
RUNDSTEDT = "Bundesarchiv Bild 183-L08129, Gerd v. Rundstedt.jpg"
RUND_WEICHS = "Bundesarchiv Bild 101I-056-1643-29A, Frankreich, Generäle v. Rundstedt, v. Weichs.jpg"
MANSTEIN = "Bundesarchiv Bild 183-H01758, Erich v. Manstein.jpg"
GORING = "Herman Goring op Waalhaven, na capitulatie mei 1940 (1).jpg"
LEOPOLD = "Léopold III-1940-revue-01.jpg"
LIGHTOLLER = "CharlesHLightoller.jpg"
TITANIC_OFF = "Titanic surviving officers.jpg"
CHURCHILL = "Winston Churchill As Prime Minister 1940-1945 MH26392.jpg"
CHURCHILL2 = "Winston Churchill As Prime Minister 1940-1945 H2646A.jpg"
HITLER_PARIS = "Hitler in Paris, 23 June 1940.jpg"
HITLER_PARIS2 = "Hitler, Speer y Breker en París, 23 de junio de 1940.jpg"
KING = "King George VI of England, formal photo portrait, circa 1940-1946 - edit.jpg"
CALAIS_PORT = "Bundesarchiv Bild 146-1971-042-08, Calais, zerstörtes Hafenviertel.jpg"
MEUSE = "Bundesarchiv Bild 146-1978-062-24, Floing, Pontonbrücke über die Maas.jpg"
CHAR_B1 = "Bundesarchiv Bild 101I-125-0277-09, Im Westen, zerstörter französischer Panzer Char B1.jpg"
STUKA_PILOTS = "Bundesarchiv Bild 101I-383-0338-03, Frankreich, Piloten bei Lagebesprechung vor Ju 87.jpg"
CALAIS_TANK = "Bundesarchiv Bild 146-1980-132-01, Calais, zerstörter englischer Panzerwagen.jpg"
CALAIS_TRUCKS = "Bundesarchiv Bild 146-1973-050-67, Calais, ausgebrannte englische Fahrzeuge.jpg"
GRENADE = "HMS Grenade (H86) IWM FL 13589.jpg"
DAFFODIL = "StateLibQld 1 169887 Royal Daffodil (ship).jpg"
MAGINOT = ("Troops of 51st Highland Division march over a drawbridge into Fort de Sainghain on the Maginot Line, "
           "3 November 1939. O227.jpg")
MAGINOT2 = ("Soldiers of the 51st Highland Division wearing gasmasks while on duty in a fort on the Maginot Line in "
            "France, 3 November 1939. O229.jpg")
SPITFIRES = ("Supermarine Spitfire Mark Is of No. 610 Squadron based at Biggin Hill, flying in 'vic' formation, "
             "24 July 1940. CH740.jpg")
VOORUIT = 'Voorpagina "Vooruit" (10 Mei 1940).jpg'
NIEUWS = 'Voorpagina "Het Algemeen Nieuws" (30 Mei 1940).jpg'

CH_SRC = "WINSTON CHURCHILL · BBC BROADCAST, 19 MAY 1940"

M_SICKLE = {"places": [{"label": "SEDAN", "lat": 49.70, "lon": 4.94},
                       {"label": "ABBEVILLE", "lat": 50.11, "lon": 1.83},
                       {"label": "DUNKIRK", "lat": 51.03, "lon": 2.37, "side": "blue"},
                       {"label": "DOVER", "lat": 51.13, "lon": 1.31, "side": "blue"}],
            "routes": [[0, 1, "red", 0.2], [2, 3, "blue", 0.15]], "pad": 0.5}

C = [
 {"title": "", "mode": "action", "sentences": [
  "This is Dunkirk, a port in northern France, on May 26, 1940.",
  "Hundreds of thousands of British, French and Belgian soldiers are trapped on its beaches, with the German army closing in.",
  "Only a few miles away, the German tanks have stopped, and they wait.",
  "Then a hastily assembled fleet of over 800 vessels, from destroyers to pleasure yachts, carries 338,226 men across the Channel.",
  "Prime Minister Winston Churchill calls it a miracle of deliverance, and a colossal military disaster.",
  "This is the entire history of Dunkirk."],
  "shots": [
   {"s": 1, "film": "dynamo", "from": 2831, "to": 2833, "label": "DUNKIRK · MAY 1940"},
   {"s": 2, "file": BEACH_LINES},
   {"s": 3, "film": "blitz", "from": 2380, "to": 2386, "sfx": "tank_engine"},
   {"s": 4, "film": "dynamo", "from": 2892.8, "to": 2895.5, "note": "338,226 MEN"},
   {"s": 5, "file": CHURCHILL, "reveal": [0.7, 0.25], "name": "WINSTON CHURCHILL", "role": "PRIME MINISTER"},
   {"s": 6, "film": "dynamo", "from": 2876, "to": 2878}]},

 {"title": "The Phoney War", "mode": "people", "stamp": ["SEPTEMBER", "1939"], "sentences": [
  "In September 1939, after Germany invades Poland, Britain and France declare war on Germany.",
  "The British Expeditionary Force, the BEF, crosses to France to help defend it.",
  "By May 1940, it has ten divisions, under the command of General Lord Gort.",
  "For months, there is almost no fighting at all: the Phoney War.",
  "France puts its trust in the Maginot Line, a chain of fortifications along its border with Germany.",
  "North of the line lies the heavily wooded Ardennes.",
  "General Philippe Pétain declares the forest impenetrable.",
  "The French commander-in-chief, Maurice Gamelin, believes the area is of limited threat.",
  "But the chief of staff of a German army group, Erich von Manstein, has a different plan.",
  "His panzer divisions will attack through the Ardennes, cross the Meuse River, and drive to the English Channel.",
  "It becomes known as the sickle cut.",
  "Hitler approves it after meeting Manstein on February 17."],
  "shots": [
   {"s": 1, "file": BEF1},
   {"s": 2, "file": BEF2},
   {"s": 3, "file": GORT_FR, "name": "LORD GORT", "role": "COMMANDER, BEF"},
   {"s": 4, "file": GORT, "note": "THE PHONEY WAR"},
   {"s": 5, "file": MAGINOT, "label": "MAGINOT LINE · NOVEMBER 1939"},
   {"s": 6, "film": "blitz", "from": 609, "to": 612.5},
   {"s": 7, "file": PETAIN, "name": "PHILIPPE PÉTAIN", "role": "MARSHAL OF FRANCE"},
   {"s": 8, "file": GAMELIN, "name": "MAURICE GAMELIN", "role": "FRENCH COMMANDER-IN-CHIEF"},
   {"s": 9, "file": MANSTEIN, "name": "ERICH VON MANSTEIN", "role": "CHIEF OF STAFF, ARMY GROUP A"},
   {"s": 10, "film": "blitz", "from": 1974, "to": 1980, "sfx": "tank_engine"},
   {"s": 11, "film": "blitz", "from": 1987, "to": 1992, "note": "SICHELSCHNITT"},
   {"s": 12, "file": MANSTEIN, "zoom": 1.3, "y": 0.3}]},

 {"title": "Sickle Cut", "mode": "action", "stamp": ["MAY 10", "1940"], "sentences": [
  "On May 10, 1940, Germany invades Belgium, the Netherlands and France.",
  "The BEF advances into Belgium, to positions along the River Dyle.",
  "But the real blow falls further south, where three panzer corps attack through the Ardennes.",
  "On May 14, they burst out of the forest and advance toward Sedan.",
  "On May 17, Churchill visits Paris, and is astonished: the French have no strategic reserves.",
  "The next day, Gamelin is dismissed, and General Maxime Weygand becomes the Supreme Commander.",
  "On May 19, Gort meets General Gaston Billotte, the overall coordinator of the Allied forces.",
  "Billotte reveals that there are no French troops between the Germans and the sea.",
  "On May 20, the German spearhead reaches the coast.",
  "Gort sees only one way out: evacuation across the Channel, from Dunkirk, the closest good port.",
  "An Allied attack at Arras fails to cut through the German spearhead.",
  "The BEF is trapped, with the remains of the Belgian army and three French armies, against the coast."],
  "shots": [
   {"s": 1, "film": "blitz", "from": 599, "to": 602.5, "sfx": "plane_flyby"},
   {"s": 2, "file": BEF3},
   {"s": 3, "film": "blitz", "from": 1969, "to": 1973.5},
   {"s": 4, "file": MEUSE, "label": "THE MEUSE · MAY 1940"},
   {"s": 5, "file": CHURCHILL2, "note": "NO STRATEGIC RESERVES"},
   {"s": 6, "file": GAMELIN, "zoom": 1.3, "y": 0.3, "note": "DISMISSED"},
   {"s": 7, "file": BILLOTTE, "name": "GASTON BILLOTTE", "role": "COORDINATOR, ALLIED ARMIES"},
   {"s": 8, "file": GORT_FR, "zoom": 1.2, "y": 0.3, "name": "LORD GORT", "role": "COMMANDER, BEF"},
   {"s": 9, "map": M_SICKLE},
   {"s": 10, "file": GORT2},
   {"s": 11, "file": CHAR_B1, "note": "ARRAS"},
   {"s": 12, "file": RETREAT1}],
  "beats": [
   {"after": 1, "source": "VOORUIT, GHENT · 10 MAY 1940",
    "shots": [{"dur": 4.5, "file": VOORUIT, "trim": [0.05, 0.045, 0.04, 0.02], "focus": [0.10, 0.16, 0.89, 0.255],
               "sfx": "typewriter"},
              {"dur": 4.5, "file": VOORUIT, "trim": [0.05, 0.045, 0.04, 0.02], "focus": [0.08, 0.255, 0.92, 0.325]}]},
   {"after": 4, "audio": {"src": "churchill", "from": 21.8, "to": 33.5}, "source": CH_SRC,
    "shots": [{"dur": 4, "film": "blitz", "from": 1571, "to": 1574.5, "sfx": "explosion_far"},
              {"dur": 4, "film": "blitz", "from": 1575, "to": 1578},
              {"dur": 4, "film": "blitz", "from": 1585, "to": 1593}]}]},

 {"title": "The Halt Order", "mode": "people", "stamp": ["CHARLEVILLE"], "sentences": [
  "On May 24, Hitler visits the headquarters of General Gerd von Rundstedt at Charleville.",
  "By now, the Germans have captured the port of Boulogne and surrounded Calais.",
  "German engineers have built five bridges over the Canal Line, and only one British battalion bars the way to Dunkirk.",
  "But Rundstedt has ordered the panzer units to halt.",
  "He is concerned about his flanks, and about supplies for his forward troops.",
  "His tanks have suffered heavy losses, and the marshy ground around Dunkirk is unsuitable for tanks.",
  "Hitler, who knows the marshes of Flanders from the First World War, agrees.",
  "The commander of the Luftwaffe, Hermann Göring, asks for the chance to destroy the forces in Dunkirk.",
  "Hitler gives it to him, and issues Directive 13: the Luftwaffe is to defeat the trapped Allied forces and stop their escape.",
  "Calais, held by the BEF, surrenders on May 26.",
  "Until the evening of that day, the German tanks wait.",
  "At half past three that afternoon, Hitler orders the panzer groups to continue their advance.",
  "Most units take another 16 hours to attack.",
  "Rundstedt later calls the halt one of the great turning points of the war."],
  "shots": [
   {"s": 1, "file": RUNDSTEDT, "name": "GERD VON RUNDSTEDT", "role": "COMMANDER, ARMY GROUP A"},
   {"s": 2, "file": CALAIS_PORT, "label": "CALAIS · 1940"},
   {"s": 3, "film": "blitz", "from": 2344, "to": 2349, "note": "ONE BATTALION"},
   {"s": 4, "file": RUND_WEICHS},
   {"s": 5, "film": "blitz", "from": 2372, "to": 2379},
   {"s": 6, "film": "blitz", "from": 2341, "to": 2343.8, "sfx": "tank_engine"},
   {"s": 7, "file": HITLER_PARIS, "name": "ADOLF HITLER", "role": "FÜHRER"},
   {"s": 8, "file": GORING, "name": "HERMANN GÖRING", "role": "COMMANDER, LUFTWAFFE"},
   {"s": 9, "file": STUKA_PILOTS},
   {"s": 10, "file": CALAIS_TRUCKS, "label": "CALAIS · 1940"},
   {"s": 11, "film": "blitz", "from": 2386, "to": 2394},
   {"s": 12, "film": "blitz", "from": 1981, "to": 1986, "stamp": ["3:30 P.M."]},
   {"s": 13, "film": "blitz", "from": 1987, "to": 1992, "sfx": "tank_engine"},
   {"s": 14, "file": RUNDSTEDT, "zoom": 1.3, "y": 0.3}]},

 {"title": "Operation Dynamo", "mode": "action", "stamp": ["DOVER"], "sentences": [
  "At Dover, Vice Admiral Bertram Ramsay plans the evacuation from the naval headquarters below Dover Castle.",
  "The planning begins on May 20, without informing the French.",
  "Ships begin gathering at Dover.",
  "Ramsay has around a thousand copies of the charts made, and buoys laid around the Goodwin Sands and down to Dunkirk.",
  "The shortest route hugs the French coast, under the fire of the German batteries on shore.",
  "Admiralty officers comb the boatyards for small craft that can carry men from the beaches.",
  "In France, the retreat is chaos: abandoned vehicles block the roads, and a flood of refugees moves the other way.",
  "At home, wartime censorship keeps the full extent of the disaster quiet.",
  "On May 26, King George VI attends a special service at Westminster Abbey, on a national day of prayer.",
  "The Archbishop of Canterbury prays for our soldiers in dire peril in France.",
  "Just before seven that evening, Churchill orders Operation Dynamo to begin.",
  "The plan is to rescue 45,000 men within two days.",
  "On the first day, only 7,669 get away.",
  "On May 27, the Luftwaffe heavily bombs Dunkirk, both the town and the docks.",
  "The water supply is knocked out, and the fires cannot be put out.",
  "An estimated one thousand civilians are killed, a third of the people left in the town.",
  "The bombs destroy the oil tanks and wreck the harbour."],
  "shots": [
   {"s": 1, "file": RAMSAY, "reveal": [0.72, 0.25], "name": "BERTRAM RAMSAY", "role": "VICE ADMIRAL, DOVER"},
   {"s": 2, "file": RAMSAY, "zoom": 1.3, "y": 0.25},
   {"s": 3, "film": "dynamo", "from": 2845, "to": 2846.9, "sfx": "ov/ship_horn"},
   {"s": 4, "film": "dynamo", "from": 2851, "to": 2854},
   {"s": 5, "map": M_SICKLE},
   {"s": 6, "film": "dynamo", "from": 2843, "to": 2844.9},
   {"s": 7, "film": "dynamo", "from": 2906, "to": 2907.9},
   {"s": 8, "file": RETREAT2},
   {"s": 9, "file": KING, "name": "GEORGE VI", "role": "KING OF THE UNITED KINGDOM"},
   {"s": 10, "file": KING, "zoom": 1.3, "y": 0.3, "note": "A DAY OF PRAYER"},
   {"s": 11, "file": CHURCHILL, "zoom": 1.3, "y": 0.3, "note": "OPERATION DYNAMO"},
   {"s": 12, "file": GRENADE},
   {"s": 13, "film": "dynamo", "from": 2909, "to": 2911.9, "note": "7,669 ON DAY ONE"},
   {"s": 14, "film": "blitz", "from": 501, "to": 503.5, "sfx": "plane_vintage"},
   {"s": 15, "file": OIL},
   {"s": 16, "film": "dynamo", "from": 2833, "to": 2836.8},
   {"s": 17, "file": AERIAL}],
  "beats": [
   {"after": 15, "shots": [{"dur": 3.5, "film": "blitz", "from": 2016, "to": 2019, "sfx": "explosion_far"},
                           {"dur": 3.5, "film": "blitz", "from": 519, "to": 524},
                           {"dur": 3.5, "film": "blitz", "from": 530, "to": 534, "sfx": "explosion_battle"},
                           {"dur": 3.5, "film": "blitz", "from": 730, "to": 739}]}]},

 {"title": "The East Mole", "mode": "action", "stamp": ["EAST MOLE"], "sentences": [
  "With the docks wrecked, the senior naval officer, Captain William Tennant, turns to the east mole.",
  "It is a long breakwater of stone and concrete, stretching nearly a mile out to sea.",
  "It was never designed to dock ships, but the ships come alongside anyway.",
  "A destroyer can carry about 900 men per trip.",
  "Almost 200,000 troops will leave Dunkirk this way.",
  "The pier master, James Campbell Clouston, keeps the flow of men moving along the mole into the waiting ships.",
  "On the beaches, most soldiers queue up with their units and patiently await their turn.",
  "Others wade out and wait for hours in shoulder-deep water.",
  "At times, panicky soldiers have to be warned off at gunpoint.",
  "On May 29, 47,310 British troops are rescued, but the Stuka dive bombers take a heavy toll on the shipping.",
  "The British destroyer Grenade is sunk.",
  "The steamer Fenella sinks at the pier with 600 men aboard, but the men are able to get off.",
  "The paddle steamer Crested Eagle suffers a direct hit, catches fire, and sinks.",
  "High above, the RAF fights to protect them, but most of the dogfights take place far from the beaches.",
  "Many soldiers bitterly accuse the airmen of doing nothing to help."],
  "shots": [
   {"s": 1, "file": TENNANT, "name": "WILLIAM TENNANT", "role": "SENIOR NAVAL OFFICER, DUNKIRK"},
   {"s": 2, "file": MOLE, "label": "THE EAST MOLE · DUNKIRK"},
   {"s": 3, "file": MOLE, "zoom": 1.3, "x": 0.4},
   {"s": 4, "film": "dynamo", "from": 2896, "to": 2898.8},
   {"s": 5, "file": MOLE_FR, "note": "200,000 MEN"},
   {"s": 6, "file": WAITING},
   {"s": 7, "file": BEACH2},
   {"s": 8, "file": WADING},
   {"s": 9, "film": "dynamo", "from": 2882.8, "to": 2885},
   {"s": 10, "film": "blitz", "from": 599, "to": 602.5, "sfx": "plane_flyby"},
   {"s": 11, "file": GRENADE, "zoom": 1.3},
   {"s": 12, "file": FENELLA},
   {"s": 13, "film": "dynamo", "from": 2846.2, "to": 2847.6, "sfx": "explosion_far"},
   {"s": 14, "film": "dynamo", "from": 2861, "to": 2866.5, "sfx": "plane_flyby"},
   {"s": 15, "file": AA}],
  "beats": [
   {"after": 13, "shots": [{"dur": 3.5, "film": "dynamo", "from": 2837, "to": 2839.9, "sfx": "explosion_far"},
                           {"dur": 3.5, "file": BOURRASQUE},
                           {"dur": 3.5, "film": "blitz", "from": 2459, "to": 2467, "sfx": "ov/machine_gun"},
                           {"dur": 3.5, "file": MONA, "trim": [0, 0, 0, 0.06]}]}]},

 {"title": "The Little Ships", "mode": "people", "stamp": ["RAMSGATE"], "sentences": [
  "From Ramsgate, a strange fleet sails for Dunkirk: fishing boats, pleasure craft, yachts and lifeboats.",
  "Agents of the Ministry of Shipping scour the Thames for likely vessels, and take them downriver to Sheerness.",
  "Some boats are requisitioned without the owner's knowledge or consent.",
  "Many small craft cross the Channel with civilian crews.",
  "The first of the little ships arrive at Dunkirk on May 28.",
  "The wide sand beaches keep the large vessels far from the shore.",
  "So the little ships ferry the soldiers out to them, again and again.",
  "One of them is the Sundowner, a motor yacht owned by Charles Lightoller, former second officer of the Titanic.",
  "He insists that if anyone is going to take her to Dunkirk, it will be him and his eldest son.",
  "They bring 127 soldiers back to Ramsgate, packed together like sardines.",
  "The paddle steamer Medway Queen makes seven round trips and rescues 7,000 men.",
  "She earns the nickname Heroine of Dunkirk.",
  "The Royal Daffodil evacuates 7,461 more.",
  "Among them is a French army captain, the historian Marc Bloch.",
  "By May 31, nearly four hundred small craft are taking part.",
  "At De Panne and Bray-Dunes, soldiers drive rows of abandoned vehicles onto the beach to make jetties."],
  "shots": [
   {"s": 1, "file": LITTLE, "label": "OFF DUNKIRK · MAY 1940"},
   {"s": 2, "file": HOME2},
   {"s": 3, "film": "dynamo", "from": 2885, "to": 2887.9},
   {"s": 4, "file": LITTLE, "zoom": 1.3, "x": 0.4},
   {"s": 5, "file": OFFSHORE, "label": "DUNKIRK · MAY 1940"},
   {"s": 6, "film": "dynamo", "from": 2843, "to": 2844.9},
   {"s": 7, "film": "dynamo", "from": 2899, "to": 2900.4},
   {"s": 8, "file": LIGHTOLLER, "name": "CHARLES LIGHTOLLER", "role": "FORMER SECOND OFFICER, TITANIC"},
   {"s": 9, "file": TITANIC_OFF, "note": "TITANIC'S OFFICER"},
   {"s": 10, "file": DOVER, "note": "127 SOLDIERS"},
   {"s": 11, "film": "dynamo", "from": 2892.8, "to": 2895, "note": "7 TRIPS"},
   {"s": 12, "file": DOVER, "zoom": 1.3},
   {"s": 13, "file": DAFFODIL},
   {"s": 14, "file": MOLE_FR, "zoom": 1.3},
   {"s": 15, "film": "dynamo", "from": 2908, "to": 2908.9},
   {"s": 16, "file": LORRY_PIER, "label": "DUNKIRK · 1940"}],
  "beats": [
   {"after": 10, "quote": {"text": "From hell to heaven was how the feeling was, you felt like a miracle had happened.",
                          "name": "A BRITISH SOLDIER", "role": "EVACUATED FROM DUNKIRK, 1940"},
    "shots": [{"dur": 3.5, "film": "dynamo", "from": 2901, "to": 2905.8, "sfx": "ov/ocean_waves"},
              {"dur": 3.5, "file": HOME1}]}]},

 {"title": "The Rearguard", "mode": "action", "stamp": ["MAY 28", "1940"], "sentences": [
  "On May 28, 1940, King Leopold III surrenders the Belgian army.",
  "It leaves a gap of 20 miles on Gort's eastern flank, between the British and the sea.",
  "Gort sends three battle-worn divisions into the line to fill it.",
  "Further south, at Lille, 40,000 men of the French First Army fight on against seven German divisions.",
  "When they surrender, the Germans grant them the honours of war.",
  "On May 31, Lord Gort is evacuated with 68,014 men.",
  "Major-General Harold Alexander takes command of the rearguard.",
  "The morning of June 1 is clear, good flying weather.",
  "There are only two and a half good flying days in the whole operation, and this is one of them.",
  "The increasing air attacks stop the evacuation by daylight.",
  "On the night of June 2, the British rearguard leaves.",
  "Captain Tennant signals Ramsay in Dover.",
  "But Churchill insists on the Royal Navy going back for the trapped French soldiers.",
  "On June 4, another 26,175 Frenchmen are carried to England.",
  "That morning, the Germans hoist the swastika over the docks.",
  "Between 30,000 and 40,000 others are left behind and captured."],
  "shots": [
   {"s": 1, "file": LEOPOLD, "name": "LEOPOLD III", "role": "KING OF THE BELGIANS"},
   {"s": 2, "file": RETREAT2, "zoom": 1.3},
   {"s": 3, "file": AA, "zoom": 1.3},
   {"s": 4, "film": "blitz", "from": 1594, "to": 1597.8},
   {"s": 5, "film": "blitz", "from": 1642, "to": 1650},
   {"s": 6, "file": GORT, "zoom": 1.3, "note": "68,014 MEN"},
   {"s": 7, "file": BEACH_LINES, "zoom": 1.25},
   {"s": 8, "film": "dynamo", "from": 2858, "to": 2859.9, "sfx": "plane_flyby"},
   {"s": 9, "film": "blitz", "from": 2016, "to": 2019},
   {"s": 10, "film": "blitz", "from": 504, "to": 509, "sfx": "plane_vintage"},
   {"s": 11, "film": "dynamo", "from": 2878, "to": 2880.9},
   {"s": 12, "film": "dynamo", "from": 2851, "to": 2854.5, "sfx": "ov/morse_code"},
   {"s": 13, "file": CHURCHILL2, "zoom": 1.3, "y": 0.3},
   {"s": 14, "film": "dynamo", "from": 2911.5, "to": 2914.2},
   {"s": 15, "file": CALAIS_PORT, "zoom": 1.25, "stamp": ["10:20 A.M."]},
   {"s": 16, "file": PRISONERS}],
  "beats": [
   {"after": 1, "source": "HET ALGEMEEN NIEUWS, BRUSSELS · 30 MAY 1940",
    "shots": [{"dur": 4.5, "file": NIEUWS, "trim": [0.065, 0.045, 0.078, 0.025], "focus": [0.11, 0.21, 0.88, 0.30],
               "sfx": "typewriter"},
              {"dur": 4.5, "file": NIEUWS, "trim": [0.065, 0.045, 0.078, 0.025],
               "focus": [0.67, 0.295, 0.88, 0.355]}]},
   {"after": 12, "quote": {"text": "Operation completed. Returning to Dover.", "name": "WILLIAM TENNANT",
                          "role": "SIGNAL TO ADMIRAL RAMSAY, 3 JUNE 1940"},
    "shots": [{"dur": 4, "film": "dynamo", "from": 2849, "to": 2850.9, "sfx": "ov/morse_code"}]}]},

 {"title": "Not a Victory", "mode": "people", "stamp": ["JUNE 4", "1940"], "sentences": [
  "On June 4, 1940, Churchill speaks to the House of Commons.",
  "A week earlier, he says, the whole root and core and brain of the British Army seemed about to perish or be captured.",
  "Now 338,226 men are in England, among them 139,997 French, Polish and Belgian troops.",
  "The British press presents it as a disaster turned to triumph, and Churchill has to remind the country of the truth.",
  "During the campaign in France, the BEF loses 68,000 soldiers.",
  "Almost all of its tanks, vehicles and equipment are abandoned in France.",
  "Of the 861 vessels of the evacuation, 243 are sunk.",
  "The army is so short of vehicles that it refurbishes obsolete buses and coaches from British scrapyards.",
  "In the air, the RAF loses 145 aircraft, and the Luftwaffe 156.",
  "On June 5, Hitler declares that the greatest battle in the history of the world has come to an end.",
  "German troops march into Paris on June 14.",
  "France surrenders eight days later."],
  "shots": [
   {"s": 1, "film": "dynamo", "from": 2922, "to": 2924.9},
   {"s": 2, "film": "dynamo", "from": 2919, "to": 2921.9},
   {"s": 3, "file": TEA, "note": "338,226 SAVED"},
   {"s": 4, "file": BLANKET},
   {"s": 5, "file": CALAIS_TANK, "note": "68,000 MEN"},
   {"s": 6, "film": "blitz", "from": 2246, "to": 2252, "note": "445 TANKS"},
   {"s": 7, "file": BOURRASQUE, "zoom": 1.3},
   {"s": 8, "file": CALAIS_TRUCKS, "zoom": 1.3},
   {"s": 9, "file": SPITFIRES, "note": "145 AIRCRAFT"},
   {"s": 10, "file": HITLER_PARIS2, "note": "THE GREATEST BATTLE"},
   {"s": 11, "file": HITLER_PARIS, "zoom": 1.3, "label": "PARIS · JUNE 1940"},
   {"s": 12, "film": "dynamo", "from": 2928, "to": 2934}],
  "beats": [
   {"after": 4, "quote": {"text": "We must be very careful not to assign to this deliverance the attributes of a "
                                  "victory. Wars are not won by evacuations.",
                          "name": "WINSTON CHURCHILL", "role": "HOUSE OF COMMONS, 4 JUNE 1940"},
    "shots": [{"dur": 4, "file": TIRED, "trim": [0, 0, 0, 0.06]}, {"dur": 4, "file": HOME3}]}]},

 {"title": "The Miracle of Dunkirk", "mode": "people", "stamp": ["JUNE 2", "1940"], "sentences": [
  "On June 2, 1940, the Dean of St Paul's, Walter Matthews, is the first to call it the Miracle of Dunkirk.",
  "The British press uses the little ships very effectively.",
  "And the phrase Dunkirk spirit is still used for courage and solidarity in adversity.",
  "On the other side, Hitler believes that once the British troops leave the continent, they will never return.",
  "Manstein calls the halt order one of Hitler's most critical mistakes.",
  "Dunkirk is a great defeat.",
  "And it is a deliverance."],
  "shots": [
   {"s": 1, "file": HOME2, "zoom": 1.3, "label": "ENGLAND · MAY 1940"},
   {"s": 2, "file": OFFSHORE, "zoom": 1.3},
   {"s": 3, "file": HOME1, "zoom": 1.3},
   {"s": 4, "file": HITLER_PARIS2, "zoom": 1.3},
   {"s": 5, "file": RUND_WEICHS, "zoom": 1.3},
   {"s": 6, "film": "dynamo", "from": 2906, "to": 2907.6},
   {"s": 7, "film": "dynamo", "from": 2903, "to": 2905.8}]},
]

STORY = {
 "priority": 9,
 "format": "entire",
 "topic": "Dunkirk evacuation",
 "sources": ["Battle of Dunkirk", "Little Ships of Dunkirk"],
 "title": "The ENTIRE History of Dunkirk in {N} Minutes",
 "question": "Was Hitler's halt order the biggest mistake of the war in the West?",
 "summary": ("In May 1940, the German panzers cut through the Ardennes and trap the British army at Dunkirk. "
             "From the Phoney War and Manstein's sickle cut to Hitler's halt order, the east mole, the little ships "
             "and Churchill's 'Wars are not won by evacuations', this is the whole story of Operation Dynamo, told "
             "with the film of the time, Churchill's own voice and the newspapers of May 1940."),
 "tags": ["Dunkirk", "Dunkirk evacuation", "Operation Dynamo", "Battle of Dunkirk", "Little Ships of Dunkirk",
          "Winston Churchill", "Halt order", "Battle of France", "1940", "BEF", "Lord Gort", "Bertram Ramsay",
          "WW2 documentary", "World War 2"],
 "pronounce": {"Rundstedt": "Roont-shtet", "Billotte": "Bee-yot", "Gamelin": "Gam-lan", "Pétain": "Pay-tan",
               "Lille": "Leel", "De Panne": "Duh Pan", "Bray-Dunes": "Bray-Dune", "Meuse": "Merz",
               "Sedan": "Seh-dahn", "Charleville": "Sharl-veel", "Maginot": "Mah-zhee-no", "Göring": "Gur-ing",
               "Ardennes": "Ar-den", "Lightoller": "Light-oller", "Clouston": "Cloo-ston", "Dyle": "Deel",
               "Manstein": "Mahn-shtine"},
 "films": {
  "dynamo": {"url": "https://upload.wikimedia.org/wikipedia/commons/5/5d/Why_We_Fight-_Divide_and_Conquer.webm",
             "mono": True, "crop": "1440:810:240:135",
             "credit": "Why We Fight: Divide and Conquer (1943), US War Department / Frank Capra (public domain, via Wikimedia Commons)"},
  "blitz": {"url": ("https://archive.org/download/19400530UfATonwocheNr.50842m33s640x480/1940-05-30%20-%20UfA-"
                    "Tonwoche%20Nr.%20508%20%2842m%2033s%2C%20640x480%29.mp4"), "mono": True, "crop": "640:360:0:60",
            "credit": "UfA-Tonwoche Nr. 508, 30 May 1940, German newsreel (via Internet Archive)"}},
 "period_audio": {
  "churchill": {"file": "Winston Churchill - Be Ye Men of Valour.ogg", "speaker": "Winston Churchill",
                "date": "MAY 19, 1940",
                "credit": "Winston Churchill, BBC broadcast 'Be Ye Men of Valour', 19 May 1940 (public domain, via Wikimedia Commons)",
                "text": "A tremendous battle is raging in France and Flanders."}},
 "pre": [
  {"dur": 2.6, "film": "dynamo", "from": 2833.2, "to": 2836.8, "sfx": "explosion_far"},
  {"dur": 2.8, "film": "dynamo", "from": 2837, "to": 2839.9, "stamp": ["MAY 26", "1940"], "sfx": "explosion_massive"},
  {"dur": 3.0, "film": "dynamo", "from": 2876, "to": 2877.9, "stamp": ["DUNKIRK"], "hush": True,
   "audio": {"src": "churchill", "from": 16.4, "to": 21.0}, "source": CH_SRC},
  {"dur": 2.6, "film": "dynamo", "from": 2882.8, "to": 2885, "source": CH_SRC}],
 "whole": [],
 "trims": {WAITING: [0, 0, 0, 0.06], MONA: [0, 0, 0, 0.06], TIRED: [0, 0, 0, 0.06], CALAIS_TANK: [0, 0, 0, 0.065],
           CALAIS_TRUCKS: [0, 0, 0, 0.065], STUKA_PILOTS: [0, 0, 0, 0.065]},
 "thumb": {"file": WAITING},
 "cover": {"file": WAITING, "x": 0.5, "y": 0.4, "zoom": 1.1, "color": False, "trim": [0, 0, 0, 0.06],
           "text": ["HISTORY OF", "DUNKIRK", "IN {N} MINUTES"], "key": ["DUNKIRK"], "sizes": [96, 150, 96],
           "mono": True},
 "promos": [
  {"id": "dunkirk_halt", "chapter": 3,
   "sentences": ["The British army is trapped at Dunkirk, and the German tanks are closing in.",
                 "Only one British battalion bars the way.",
                 "Then Rundstedt gives his order: the panzer units halt."],
   "shots": [{"s": 1, "file": BEACH_LINES}, {"s": 2, "film": "blitz", "from": 2344, "to": 2349},
             {"s": 3, "file": RUNDSTEDT, "name": "GERD VON RUNDSTEDT"}],
   "top": "THE TANKS STOP|AT DUNKIRK", "key": ["DUNKIRK"],
   "cta": {"kind": "redacted", "line": "THE PANZERS", "hidden": "HALT"}, "end": "WHY DID THEY STOP?",
   "name": "Why Hitler's Tanks Stopped at Dunkirk"},
  {"id": "dunkirk_titanic", "chapter": 6,
   "sentences": ["The former second officer of the Titanic takes his own yacht to Dunkirk.",
                 "Off the beaches, soldiers wait for hours in shoulder-deep water.",
                 "Charles Lightoller fills his little yacht: 127 soldiers, packed together like sardines."],
   "shots": [{"s": 1, "file": LIGHTOLLER, "name": "CHARLES LIGHTOLLER"}, {"s": 2, "file": WADING},
             {"s": 3, "film": "dynamo", "from": 2899, "to": 2900.4}],
   "top": "TITANIC'S OFFICER|AT DUNKIRK", "key": ["DUNKIRK"],
   "cta": {"kind": "number", "big": "127", "line": "SOLDIERS ON ONE YACHT. HOW?"}, "end": "HOW MANY DID HE SAVE?",
   "name": "The Titanic Officer Who Sailed to Dunkirk"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "dunkirk.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
uses = collections.Counter(s["file"] for c in C for s in (c["shots"] + [x for b in c.get("beats") or []
                                                                        for x in b["shots"]]) if s.get("file"))
print("photos used > 2 times:", {f: n for f, n in uses.items() if n > 2} or "none")
films = collections.Counter((s["film"], int(s["from"]) // 5) for c in C for s in
                            (c["shots"] + [x for b in c.get("beats") or [] for x in b["shots"]]) if s.get("film"))
print("film moments used > 2 times:", {k: n for k, n in films.items() if n > 2} or "none")
