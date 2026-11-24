"""The Sherman tank, Nov 24 (Andrii: 'так, пиши Sherman на п'ятницю'): a hand story in the NEW FORMAT (CLAUDE.md,
Nov 23): voice No. 3 ('andrii', voice pack), the narrator at ~3 s, President Roosevelt's 'we shall produce 45,000
tanks' (State of the Union, 6 January 1942) as a beat right after sentence 1 (the duel at Cologne Cathedral), one open
question (death trap, or the tank that wins the war? answered in 'Did It Burn?' and 'Cologne'), short wordless parts,
names and notes in the stamp look, 2 cliff teasers.
Facts: the Wikipedia articles of STORY['sources'] (whole, sources/*.txt).
Films (public domain, Internet Archive): Universal newsreel 26 March 1945 (Cologne), 111-ADC-1677 (hedgerow cutters),
111-ADC-1672a (Canisy), 111-ADC-1970c (Panther), 111-ADC-3124c (Houffalize), United News ARC-38910 (June 1942),
ARC-38922 (Sept 1942), ARC-38954 (Tunisia), CB-39 (tank modifications), Universal newsreel 20 Dec 1944, NPC-15746 +
ARC-39013 (D-Day), gov.fdr.283 (the speech, FDR Library).
Speech: President Roosevelt, State of the Union, 6 January 1942 (FDR Presidential Library video 283, public domain);
the excerpt 1135-1175 s = period/period_FDR_State_of_the_Union_1942_tanks.mp3.
Run: python tools/stories/sherman_build.py"""
import json, pathlib

PANTHER_K = "Burning German Panzer V Panther in front of Köln Cathedral, 6 March 1945 (342-FH-3A21086-B56707AC).jpg"
M26K = "M26Cologne.jpg"
MCNAIR2 = "Lieutenant general Lesley J. McNair.jpg"
MCNAIR = "Lesley J. McNair Purple Heart 1943 (1).jpg"
MCNAIR_BR = "General Bradley and General McNair.jpg"
PLANT = "US Army Detroit Tank Plant.jpg"
M3A = "M3 tank production LOC fsa.8b00695.jpg"
M3B = "M3 tank production LOC fsa.8e10700.jpg"
ENGINES = "R-975 engines for M-3 tanks.png"
KNOX = "M-4 tank, Ft Knox, Ky.jpg"
LANCERS = "Sherman tanks of 9th Queen's Royal Lancers during the Battle of El Alamein, 5 November 1942. E18972.jpg"
EIGHTH = "Sherman tanks of the Eighth Army move across the desert.jpg"
CREWS = ("Crews climb aboard Sherman tanks of The Queen's Bays (2nd Dragoon Guards), 1st Armoured Division at El Alamein, "
         "24 October 1942. E18376.jpg")
BAYS = ("Sherman II tanks of the Queen's Bays (2nd Dragoon Guards), 2nd Armoured Brigade, moving up to the Alamein line, "
        "24 October 1942. E18380.jpg")
E77 = "The British Army in North Africa 1942 E18377.jpg"
E79 = "The British Army in North Africa 1942 E18379.jpg"
LEE_KASS = "1stArmorDivKasserineTunisia1943.jpg"
TIGER = "Knocked-out German Tiger I tank at Béja, Tunisia, 23 April 1943 (111-SC-171649).jpg"
DEVERS = "General Jacob Devers 1944.jpg"
DD = "DD-Tank.jpg"
DD_OUIS = ("Sherman DD tanks of 'B' Squadron, 13th-18th Royal Hussars support men of No. 4 Army Commando advancing "
           "towards Ouistreham on D-Day, 6 June 1944. MH2011.jpg")
SUPPLY = "NormandySupply edit.jpg"
JAWS = "Into the Jaws of Death 23-0455M edit.jpg"
BRADLEY = "General Omar Bradley and General George C. Marshall.jpg"
IKE_BR = "Eisenhower & Bradley with a member of the French Resistance in Normandy.jpg"
DAMAGED = "Damaged M4, Normandy 1944-06-09.jpg"
FF_BURNED = "Firefly burned out.jpg"
FF_FIELD = "Sherman Firefly in Field.jpg"
FF_NAMUR = "British Sherman Firefly Namur.jpg"
FF = "British Sherman Firefly.jpg"
FF_LOAD = "Loading 17 pounder rounds into Sherman Firefly 1944 IWM B 8793.jpg"
GUEBLING = ("Five damaged German Panzer V Panthers and two U.S. M4A3 Shermans near Guébling, Moselle, France, "
            "25 November 1944 (111-SC-197160).jpg")
ABRAMS_M4 = "M4 Abrams.jpg"
ABRAMS = "Creighton William Abrams Jr. - Cadet Photo.jpg"
PANTHERS_N = "Panthers Knocked-out Normandy.jpg"
KRINKELT = "Two knocked-out German Panzer V Panther tanks in Krinkelt, Belgium, 17 December 1944 (111-SC-198204).jpg"
COBRA = "1944 Cobra King first in Bastogne.jpg"
COBRA2 = "Cobra King, first tank in Bastogne.jpg"
INSIGNIA = "US 761st Tank Battalion - Black Panther.jpg"
IKE3 = "Dwight D. Eisenhower, Omar N. Bradley, and George S. Patton.jpg"
RONSON = "Ronson flame tank Iwo Jima.jpg"
GRABOW = "M4A2 Lend-Lease Tank at Grabow Germany May 1945.jpg"
KOREA = "Korea – Tanks - DPLA - e36f8de727b23f5c10863e84614a4a30 (page 1).jpg"
CARENTAN = "American tank in Carentan.jpg"
COUTANCES = ("SC 192042 - U.S. tanks pass through the wrecked streets of Coutances, France, on their way to the sea "
             "beyond the town. 30 July, 1944.jpg")
DUMP = ("The remains of Sherman tanks and carriers waiting to be broken up at a British vehicle dump in Normandy, "
        "1 August 1944. B8394.jpg")
VETTWEISS = "M26-Pershing-Vettweiss-194503.jpg"
CALLIOPE = "Sherman Arlene III.jpg"

FDR_SRC = "PRESIDENT ROOSEVELT · STATE OF THE UNION, 6 JANUARY 1942"

M_DESERT = {"places": [{"label": "TOBRUK", "lat": 32.08, "lon": 23.96, "side": "red"},
                       {"label": "EL ALAMEIN", "lat": 30.83, "lon": 28.95, "side": "blue"},
                       {"label": "SUEZ CANAL", "lat": 30.4, "lon": 32.4, "side": "blue"}],
            "routes": [[0, 1, "red", 0.15]], "pad": 0.5}
M_BULGE = {"places": [{"label": "ARRACOURT", "lat": 48.73, "lon": 6.53, "side": "blue"},
                      {"label": "BASTOGNE", "lat": 50.0, "lon": 5.72, "side": "red"},
                      {"label": "COLOGNE", "lat": 50.94, "lon": 6.96, "side": "red"}],
           "routes": [[0, 1, "blue", 0.2]], "pad": 0.6}


def film(s, key, x, n=6, **k):
    return {"s": s, "film": key, "from": x, "to": x + n, **k}


def pic(s, f, **k):
    return {"s": s, "file": f, **k}


def beat(after, *shots):
    return {"after": after, "shots": [{"dur": d, "film": f, "from": x, "to": x + d, **({"sfx": s} if s else {})}
                                      for d, f, x, s in shots]}


C = [
 {"title": "", "mode": "action", "sentences": [
  "On 6 March 1945, in front of Cologne Cathedral, a German Panther knocks out an American Sherman, and three of its five crew are killed.",
  "America builds 49,324 of these tanks, more than any other tank it makes in this war.",
  "General Lesley McNair believes the Sherman is good enough, and refuses to send a heavier tank.",
  "So is the Sherman a death trap, or the tank that wins the war?",
  "It begins with a tank that cannot even turn its gun around."],
  "shots": [
   film(1, "sh_cologne", 93, 2.2, stamp=["COLOGNE"]),
   film(1, "sh_cologne", 7, 5),
   film(2, "sh_plant", 440, 6, note="49,324 TANKS"),
   film(2, "sh_plant", 568, 6),
   pic(3, MCNAIR, reveal=[0.72, 0.2], name="LESLEY McNAIR", role="COMMANDER, ARMY GROUND FORCES"),
   film(4, "sh_rhino", 216, 3.5),
   film(5, "sh_plant", 420, 6)],
  "beats": [{"after": 1, "audio": {"src": "fdr", "from": 22.35, "to": 29.6}, "source": FDR_SRC, "shots": [
   {"dur": 4.4, "film": "sh_fdr", "from": 1157.4, "to": 1161.8, "source": FDR_SRC},
   {"dur": 2.85, "film": "sh_plant", "from": 456, "to": 459, "source": FDR_SRC}]}]},

 {"title": "The Gun That Cannot Turn", "mode": "people", "stamp": ["1939"], "sentences": [
  "But in 1939, the U.S. Army has about 400 tanks, and only its 18 M2 Mediums are considered modern.",
  "Two years later, America is arming for a war, and it needs thousands of them.",
  "In Detroit, Chrysler runs the first American plant ever built for the mass production of tanks.",
  "The first tanks roll out before the building is even finished.",
  "They are M3s, with a 75-millimeter gun set in the side of the hull.",
  "It can hardly swing, and it cannot be aimed at anything on the other side of the tank.",
  "The M3 is only a stopgap, until there is a turret for the big gun.",
  "On 18 April 1941, the Armored Force Board looks at five designs, and chooses the simplest.",
  "It is called the T6: the body of the M3, with one new turret on top.",
  "Everything about it is made for the factory: standard parts, easy repairs, and a size that fits on ships.",
  "The prototype is completed on 2 September 1941.",
  "The British name the tank after an American general of the Civil War, William Tecumseh Sherman."],
  "shots": [
   film(1, "sh_plant", 426),
   film(2, "sh_plant", 508),
   pic(3, PLANT, label="DETROIT TANK ARSENAL"),
   pic(4, M3A),
   pic(5, M3B),
   pic(6, LEE_KASS),
   pic(7, ENGINES, trim=[0.04, 0.03, 0.03, 0.08]),
   film(8, "sh_test", 72, note="FIVE DESIGNS"),
   pic(9, KNOX, y=0.45),
   film(10, "sh_plant", 536),
   film(11, "sh_test", 82),
   film(12, "sh_test", 94)]},

 {"title": "Give Us Shermans", "mode": "action", "stamp": ["WASHINGTON"], "sentences": [
  "But on 21 June 1942, Winston Churchill is with Roosevelt in Washington when the news comes: Tobruk has fallen.",
  "Egypt and the Suez Canal are now in danger.",
  "Roosevelt asks what he can do to help, and Churchill answers at once.",
  "America's own divisions have only a few Shermans yet.",
  "More than 300 are shipped to Egypt, and by September they are there.",
  "They are given shields over their tracks, for the desert.",
  "In October 1942, the Second Battle of El Alamein begins.",
  "The Eighth Army has 252 Shermans fit for action.",
  "They meet Panzer Threes and Panzer Fours, and open fire at 2,000 yards.",
  "There are losses on both sides.",
  "But the Sherman's gun and armor give the Allies an edge, and after 13 days, Rommel's army is crushed.",
  "The Americans are sure now: their tank is better than the German ones.",
  "It is true in 1942, and that is the problem."],
  "shots": [
   film(1, "sh_plant", 21.5, 4, label="WASHINGTON · JUNE 1942"),
   {"s": 2, "map": M_DESERT},
   film(3, "sh_plant", 26, 4),
   film(4, "sh_test", 76),
   film(5, "sh_plant", 548, 6, note="300 SHERMANS"),
   pic(6, CREWS),
   pic(7, BAYS, label="EL ALAMEIN · OCTOBER 1942"),
   pic(8, E77, note="252 SHERMANS"),
   pic(9, LANCERS),
   film(10, "sh_tunis", 284, 3),
   pic(11, EIGHTH),
   pic(12, E79),
   film(13, "sh_tunis", 356)],
  "beats": [
   {"after": 3, "quote": {"text": "Give us as many Sherman tanks as you can spare and ship them to the Middle East as quickly as possible.",
                          "name": "WINSTON CHURCHILL", "role": "BRITISH PRIME MINISTER, JUNE 1942"},
    "shots": [{"dur": 7.0, "film": "sh_plant", "from": 30, "to": 35}]},
   beat(10, (3.2, "sh_tunis", 435, "explosion_far"), (3.0, "sh_tunis", 380, "low_rumble"))]},

 {"title": "Sidi Bou Zid", "mode": "action", "stamp": ["TUNISIA"], "sentences": [
  "But in Tunisia, on 14 February 1943, the Americans find out how wrong they are.",
  "At four in the morning, 140 German tanks begin to come through the passes to Sidi Bou Zid, covered by a sandstorm.",
  "On one hill stands Lieutenant Colonel John Waters, the son-in-law of General Patton.",
  "By ten o'clock, his hill is surrounded.",
  "On another hill, Colonel Thomas Drake asks for permission to retreat.",
  "General Fredendall tells him to hold on, and wait for help.",
  "It never arrives.",
  "By 5 p.m., the Americans have lost 44 tanks.",
  "The next day, they counter-attack, over flat, open country.",
  "They are bombed from the air, and then they find themselves between two Panzer divisions.",
  "More than 80 German tanks are waiting, and some of them are Tigers.",
  "Another 46 medium tanks are lost.",
  "America has met the Tiger, and its generals decide that there are too few of them to matter."],
  "shots": [
   film(1, "sh_tunis", 304, 5, label="SIDI BOU ZID · FEBRUARY 1943"),
   film(2, "sh_tunis", 334, 4, stamp=["4:00 A.M."], sfx="explosion_far"),
   film(2, "sh_tunis", 396, 5),
   film(3, "sh_tunis", 516, 4),
   film(4, "sh_tunis", 429, 5),
   film(5, "sh_tunis", 528, 5),
   film(6, "sh_tunis", 308, 5),
   film(7, "sh_tunis", 352, 3),
   film(8, "sh_tunis", 338, 5, note="44 TANKS LOST"),
   film(9, "sh_tunis", 360, 5),
   film(10, "sh_tunis", 444, 4),
   pic(11, TIGER, label="TIGER I · TUNISIA 1943"),
   film(12, "sh_tunis", 388, 5, note="46 MORE"),
   pic(13, TIGER, zoom=1.35, x=0.35, y=0.45)],
  "beats": [beat(8, (3.0, "sh_tunis", 376, "low_rumble"), (3.0, "sh_tunis", 392, None))]},

 {"title": "The Man Who Said No", "mode": "people", "stamp": ["FALL 1943"], "sentences": [
  "But in the fall of 1943, the man at the head of the Army Ground Forces still says the Sherman is enough.",
  "Lesley McNair is an old artilleryman, and he believes in his own plan.",
  "Tanks are there to break through, and to support the infantry.",
  "Enemy tanks are the work of another weapon, the tank destroyer.",
  "General Jacob Devers does not agree.",
  "For the invasion of France, he asks for 250 T26s, a new tank with a 90-millimeter gun.",
  "McNair refuses.",
  "The new tank is not battle worthy, he says, and there is no battle need for it.",
  "He has his reasons: it breaks down, and Europe's bridges are not made for such heavy loads.",
  "Devers goes over his head, to the War Department, and in December 1943 the tanks are ordered.",
  "Still, in April 1944, McNair's command asks for a smaller gun on them.",
  "General George Marshall orders the tanks to Europe as soon as possible.",
  "They will not be there for D-Day."],
  "shots": [
   pic(1, MCNAIR2, label="ARMY GROUND FORCES"),
   pic(2, MCNAIR, zoom=1.5, y=0.15),
   film(3, "sh_test", 100),
   film(4, "sh_rhino", 246, 5),
   pic(5, DEVERS, name="JACOB DEVERS", role="U.S. COMMANDER IN EUROPE, 1943"),
   pic(6, VETTWEISS, note="250 NEW TANKS"),
   pic(7, MCNAIR_BR, x=0.6),
   film(8, "sh_mods", 752, 4),
   film(9, "sh_mods", 774, 4),
   film(10, "sh_plant", 516, 5),
   film(11, "sh_plant", 462, 5),
   pic(12, BRADLEY, x=0.6),
   film(13, "sh_counter", 311, 5)]},

 {"title": "The Tanks That Swim", "mode": "action", "stamp": ["OMAHA BEACH"], "sentences": [
  "But at Omaha Beach, on 6 June 1944, the first Shermans have to swim.",
  "The idea comes from Nicholas Straussler, an engineer born in Hungary.",
  "He wraps the tank in a folding screen of waterproof canvas, and propellers drive it through the water.",
  "It is made for waves of up to one foot.",
  "On D-Day, the waves are up to six feet high.",
  "At 5:40 a.m., one battalion puts 29 of them into the sea, too far from the shore.",
  "The landing craft are drifting, and the tanks must turn their sides to the waves.",
  "The canvas folds, and one after another they go down.",
  "Some crews radio back a warning: do not launch so far out.",
  "27 of the 29 tanks sink.",
  "Two reach the beach, because their commanders know how to sail, and never turn their sides to the waves.",
  "Most of the crews are rescued, but five men are known to have died.",
  "The rest of the Shermans are landed directly on the beach, starting at about 6:40.",
  "On the other four beaches, the swimming tanks have no such problems."],
  "shots": [
   film(1, "news", 535, 2),
   film(1, "news", 496, 2),
   pic(2, DD, note="STRAUSSLER'S TANK"),
   pic(3, DD, zoom=1.35, y=0.65),
   film(4, "news", 506, 3),
   film(5, "news", 499, 4, note="SIX-FOOT WAVES"),
   film(6, "news", 456, 5, stamp=["5:40 A.M."]),
   film(7, "news", 468, 3),
   film(8, "news", 474, 5),
   film(9, "news", 514, 2),
   pic(10, JAWS, label="OMAHA BEACH · 6 JUNE 1944", note="27 OF 29 SINK"),
   film(11, "news", 510, 3),
   film(12, "news", 532, 3),
   pic(13, SUPPLY),
   pic(14, DD_OUIS)],
  "beats": [beat(10, (3.2, "news", 503, "ov/ocean_waves"), (3.0, "news", 516, None))]},

 {"title": "The Sergeant's Idea", "mode": "people", "stamp": ["NORMANDY"], "sentences": [
  "But behind the beaches, Normandy stops the Sherman with something older than any gun: the hedgerow.",
  "It is a thick bank of earth around every field, with hedges on top.",
  "A tank that climbs over it shows its vulnerable underside.",
  "One day, a man from Tennessee asks: why not put saw teeth on the tank, and cut through?",
  "The others laugh, but Sergeant Curtis Culin does not.",
  "He has steel teeth welded to the front of a tank.",
  "The steel is German scrap: it comes from the obstacles on the invasion beaches.",
  "On 14 July, it is shown to General Omar Bradley.",
  "Bradley watches a hedgerow explode, and a Sherman come bursting through.",
  "He forbids anyone to use the teeth until the great attack, Operation Cobra.",
  "By then, 60 percent of the First Army's tanks have them.",
  "On 25 July, as Cobra begins, American bombers drop some of their bombs on their own men.",
  "111 are killed, and among them is the man who said no, Lesley McNair.",
  "Then the Shermans break out of Normandy.",
  "Four months after his invention, Culin loses a leg to a land mine."],
  "shots": [
   film(1, "sh_rhino", 21, 4),
   film(2, "sh_rhino", 3, 4),
   pic(3, CARENTAN),
   film(4, "sh_rhino", 170, 5),
   film(5, "sh_rhino", 78, 6),
   film(6, "sh_rhino", 90, 6, label="NORMANDY · JULY 1944"),
   film(7, "sh_rhino", 123, 6),
   pic(8, IKE_BR, x=0.55, name="OMAR BRADLEY", role="COMMANDER, U.S. FIRST ARMY"),
   film(9, "sh_rhino", 143, 4.5),
   film(10, "sh_rhino", 104, 6, note="SECRET WEAPON"),
   film(11, "sh_rhino", 148, 5),
   film(12, "sh_tunis", 444, 4),
   pic(13, MCNAIR2, zoom=1.3, x=0.7),
   pic(14, COUTANCES, label="COUTANCES · 30 JULY 1944"),
   film(15, "sh_canisy", 111, 3)],
  "beats": [
   {"after": 5, "quote": {"text": "There was a little sergeant. His name was Culin, and he had an idea.",
                          "name": "DWIGHT D. EISENHOWER", "role": "SPEECH OF JANUARY 1961"},
    "shots": [{"dur": 6.0, "file": IKE3, "x": 0.5}]},
   beat(14, (3.2, "sh_rhino", 366, "low_rumble"), (3.0, "sh_rhino", 344, None))]},

 {"title": "Did It Burn?", "mode": "people", "stamp": ["JULY 1944"], "sentences": [
  "But from June to July 1944, British researchers study the wrecks of Normandy, and count.",
  "They examine 40 Shermans, and 33 of them have burned.",
  "That is 82 percent.",
  "A story is told that the tank is called the Ronson, after a cigarette lighter that lights every time.",
  "It is almost certainly made up: the company's slogan is from the 1950s.",
  "And there is a real Ronson, a Sherman with a flamethrower.",
  "The major reason for the fires is the ammunition, stored above the tracks.",
  "Often, after a fire, the fuel tank is found intact.",
  "So the shells are moved to the floor of the hull, inside jackets of water.",
  "Now only 10 to 15 percent of the Shermans burn when they are penetrated.",
  "German tanks burn too: of five Panzer Fours in the same study, four burned.",
  "Yet the losses are terrible.",
  "Belton Cooper, of the Third Armored Division, writes that his division enters Normandy with 232 Shermans.",
  "By the end, 648 are destroyed, and hundreds more are knocked out, repaired, and sent back.",
  "He calls his book Death Traps, and historians still argue with it."],
  "shots": [
   pic(1, DUMP, label="NORMANDY · 1944"),
   pic(2, FF_BURNED, note="33 OF 40 BURNED"),
   pic(3, DAMAGED),
   film(4, "sh_rhino", 152, 2),
   film(4, "sh_rhino", 328, 4),
   film(5, "sh_rhino", 288, 6),
   pic(6, RONSON, label="IWO JIMA · 1945"),
   film(7, "sh_canisy", 72, 4),
   film(8, "sh_panther", 112, 5),
   pic(9, GRABOW),
   film(10, "sh_mods", 783, 5, note="10 TO 15 PERCENT"),
   film(11, "sh_panther", 137, 6),
   pic(12, DUMP, zoom=1.4, x=0.4),
   film(13, "sh_rhino", 290, 3),
   film(13, "sh_rhino", 300, 2.6),
   film(14, "sh_rhino", 114, 6, note="648 DESTROYED"),
   film(15, "sh_canisy", 92, 5)],
  "beats": [beat(14, (3.0, "sh_rhino", 149, "low_rumble"), (3.0, "sh_rhino", 267, None))]},

 {"title": "The Firefly", "mode": "action", "stamp": ["8 AUGUST 1944"], "sentences": [
  "But on 8 August 1944, near Saint-Aignan-de-Cramesnil, in Normandy, one kind of Sherman can stop a Tiger.",
  "It begins with two British officers, Major Brighty and Lieutenant Colonel Witheridge.",
  "They put the British 17-pounder into the Sherman, though the turret is too small for the long recoil of the gun.",
  "The idea is rejected, until Churchill gives it the highest priority.",
  "The gunner of one of these Fireflies is Joe Ekins, a 21-year-old from the shoe factories of Rushden.",
  "He has yet to fire his gun in action.",
  "Then a group of Tigers comes up from the south.",
  "His troop can see three of them.",
  "Ekins fires, and in almost 12 minutes, he destroys all three.",
  "One of them is the tank of Michael Wittmann, the famous German tank commander.",
  "That is the widely accepted version, and some still dispute it.",
  "Ekins then destroys a Panzer Four, before his own tank is hit.",
  "He is made a radio operator, and stays one for the rest of the war.",
  "Then he goes back to the shoe factories."],
  "shots": [
   pic(1, FF_FIELD, label="NORMANDY · AUGUST 1944"),
   pic(2, FF_NAMUR),
   pic(3, FF_LOAD, note="17-POUNDER"),
   pic(4, FF),
   pic(5, FF_NAMUR, zoom=1.35, x=0.65, note="JOE EKINS"),
   pic(6, FF, zoom=1.3),
   film(7, "sh_counter", 92.5, 2),
   film(8, "sh_rhino", 12, 4),
   pic(9, FF_FIELD, zoom=1.5, x=0.4, y=0.6, sfx="explosion_far", note="12 MINUTES"),
   pic(10, PANTHERS_N, note="TIGER 007"),
   film(11, "sh_panther", 150, 5),
   film(12, "news", 541, 2),
   film(12, "sh_panther", 127, 3),
   film(13, "sh_panther", 162, 4),
   pic(14, FF_LOAD, zoom=1.3)],
  "beats": [
   {"after": 12, "quote": {"text": "He might have been a hero to the Germans, but not to me.",
                           "name": "JOE EKINS", "role": "ON MICHAEL WITTMANN"},
    "shots": [{"dur": 5.0, "film": "sh_panther", "from": 142, "to": 146}]}]},

 {"title": "Arracourt", "mode": "action", "stamp": ["ARRACOURT"], "sentences": [
  "But at Arracourt, in September 1944, the Germans send 262 tanks and assault guns into battle.",
  "Many are new Panthers, better than the Sherman in gun and armor.",
  "Their crews have had two weeks of training, and they cannot read maps.",
  "On the morning of the 19th, there is thick fog.",
  "The Panthers come forward blind.",
  "The Shermans slip around them, fire into their weaker sides, and knock out 11.",
  "The 37th Tank Battalion is led by Lieutenant Colonel Creighton Abrams.",
  "Overhead flies Major Charles Carpenter, in a Piper Cub armed with bazookas.",
  "When the fog lifts, he dives on the Panthers, and is credited with two that day.",
  "In a week of fighting, 86 of the German tanks and assault guns are destroyed, and 114 are damaged or broken down.",
  "The combat command in their way loses 25 tanks and seven tank destroyers.",
  "The better tank has lost to the better crews."],
  "shots": [
   film(1, "sh_panther", 188, 4, label="LORRAINE · SEPTEMBER 1944"),
   film(2, "sh_panther", 155, 5),
   pic(3, KRINKELT),
   film(4, "sh_rhino", 345, 3, stamp=["SEPTEMBER 19"]),
   film(5, "sh_panther", 180, 5),
   film(6, "sh_rhino", 301, 2.5, note="11 PANZERS"),
   pic(7, ABRAMS, card=True, name="CREIGHTON ABRAMS", role="COMMANDER, 37TH TANK BATTALION"),
   film(8, "sh_rhino", 377, 4),
   film(9, "sh_panther", 166, 5),
   pic(10, GUEBLING, note="86 DESTROYED"),
   pic(11, ABRAMS_M4),
   pic(12, GUEBLING, zoom=1.5, x=0.7, y=0.55)],
  "beats": [
   {"after": 7, "quote": {"text": "I'm supposed to be the best tank commander in the Army, but I have one peer—Abe Abrams. He's the world champion.",
                          "name": "GEORGE S. PATTON", "role": "ON CREIGHTON ABRAMS"},
    "shots": [{"dur": 8.0, "film": "sh_tunis", "from": 297.3, "to": 301.3}]},
   beat(11, (3.0, "sh_panther", 135, "explosion_far"), (3.0, "sh_panther", 118, "low_rumble"))]},

 {"title": "First in Bastogne", "mode": "action", "stamp": ["BASTOGNE"], "sentences": [
  "But in December 1944, Bastogne is surrounded by the Germans, with the 101st Airborne Division inside.",
  "Abrams and his battalion fight their way toward it.",
  "One of their tanks is a Jumbo, a Sherman with very thick armor, and only 254 of them are made.",
  "The crew call it Cobra King.",
  "On 26 December, at 4:50 in the afternoon, it is the first tank to reach the lines of the defenders.",
  "The siege is over.",
  "In early January, west of the town, the 761st Tank Battalion attacks Tillet.",
  "Its men are Black, and they are not permitted to serve in the same units as white troops.",
  "Their motto is: Come out fighting.",
  "They go in with 11 tanks, and lose nine, but after two days the town is taken.",
  "They are in action for 183 days.",
  "That same month, Eisenhower asks that no more Shermans with the old 75-millimeter gun be sent to Europe.",
  "After the Battle of the Bulge, it is no longer enough."],
  "shots": [
   film(1, "sh_snow", 66, 6),
   {"s": 2, "map": M_BULGE},
   pic(3, COBRA, note="254 JUMBOS"),
   pic(4, COBRA2, zoom=1.3, x=0.55, y=0.45, label="COBRA KING · DECEMBER 1944"),
   film(5, "sh_snow", 42, 5, stamp=["4:50 P.M."]),
   pic(6, COBRA2),
   film(7, "sh_snow", 48, 3, label="TILLET · JANUARY 1945"),
   pic(8, INSIGNIA, card=True),
   pic(9, INSIGNIA, card=True, zoom=1.2),
   film(10, "sh_snow", 60, 3, note="9 OF 11 LOST"),
   film(11, "sh_snow", 29, 5),
   pic(12, IKE3, zoom=1.3),
   film(12, "sh_mods", 746.5, 3),
   film(13, "sh_mods", 762, 4),
   film(13, "sh_snow", 88, 5)],
  "beats": [beat(6, (3.0, "sh_snow", 74, "low_rumble"), (3.0, "sh_snow", 92, None))]},

 {"title": "Cologne", "mode": "action", "stamp": ["6 MARCH 1945"], "sentences": [
  "But on 6 March 1945, the Panther in front of Cologne Cathedral does not know what is in the next street.",
  "It is one of the new tanks that McNair had refused, a Pershing named Eagle 7.",
  "Its gunner is Corporal Clarence Smoyer.",
  "He expects to see the Panther's side, but its gun is already turning toward him.",
  "Smoyer fires on the move, then the tank stops, and he fires twice more.",
  "All three shells go through.",
  "A Signal Corps cameraman, Sergeant Jim Bates, records it all.",
  "But only a small number of Pershings see combat in Europe.",
  "The tank of the Western Allies is still the Sherman.",
  "By 1945, it is not the strongest tank on the battlefield.",
  "But it is reliable, it is quickly repaired, and there are always more of them.",
  "It fights on in Korea, and in other people's wars.",
  "Death trap, or war winner?",
  "To the generals it was a number, and the number was enough, but for the five men inside, it was the only tank they had."],
  "shots": [
   film(1, "sh_cologne", 147, 5),
   pic(2, M26K, label="COLOGNE · 6 MARCH 1945"),
   pic(3, M26K, zoom=1.4, y=0.75),
   film(4, "sh_cologne", 64, 2),
   film(5, "sh_cologne", 42, 4, sfx="explosion_far"),
   film(6, "sh_cologne", 73, 3, note="THREE SHELLS"),
   pic(7, PANTHER_K),
   pic(8, VETTWEISS),
   film(9, "sh_cologne", 8, 4),
   pic(10, CALLIOPE),
   film(11, "sh_mods", 786, 5),
   pic(12, KOREA, trim=[0.06, 0.06, 0.06, 0.06], label="KOREA"),
   film(13, "sh_rhino", 3, 4),
   film(14, "sh_cologne", 33, 3),
   film(14, "sh_cologne", 16.2, 3)],
  "beats": [beat(7, (3.4, "sh_cologne", 75, "explosion_massive"), (2.6, "sh_cologne", 96, None))]},
]

NARA = "(public domain, via Internet Archive)"
IA = "https://archive.org/download/"
STORY = {
 "priority": 10,
 "format": "entire",
 "voice": "andrii",
 "intro_beats": True,
 "topic": "M4 Sherman",
 "sources": ["M4 Sherman", "M3 Lee", "Lesley J. McNair", "Battle of Sidi Bou Zid", "Duplex Drive tank", "Curtis G. Culin",
             "Rhino tank", "Operation Cobra", "Sherman Firefly", "Joe Ekins", "Battle of Arracourt", "Creighton Abrams",
             "Siege of Bastogne", "Battle of the Bulge", "761st Tank Battalion (United States)", "Belton Y. Cooper",
             "M26 Pershing", "Detroit Arsenal (Warren, Michigan)", "Second Battle of El Alamein"],
 "title": "The ENTIRE History of the Sherman Tank in {N} Minutes",
 "question": "The Sherman: death trap, or the tank that won the war?",
 "summary": ("From Detroit and El Alamein to Omaha Beach, the hedgerows, the Firefly, Arracourt, Bastogne and the tank "
             "duel at Cologne Cathedral, this is the whole story of the M4 Sherman, told with archive film and "
             "President Roosevelt's own voice."),
 "tags": ["Sherman tank", "M4 Sherman", "Sherman Firefly", "tank battle", "Battle of Arracourt", "Cobra King",
          "Cologne tank duel", "M26 Pershing", "Panther tank", "Tiger tank", "Creighton Abrams", "Lesley McNair",
          "D-Day", "WW2 documentary", "World War 2", "history"],
 "pronounce": {"Sidi Bou Zid": "Sidi Boo Zeed", "Saint-Aignan-de-Cramesnil": "San Ten-yon duh Krah-meh-neel",
               "Arracourt": "Arra-koor", "Bastogne": "Bas-tone", "Tillet": "Tee-yay", "Ekins": "Eekins",
               "Wittmann": "Vitt-mahn", "Culin": "Kew-lin", "Straussler": "Strowss-ler", "Smoyer": "Smoy-er",
               "McNair's": "Mac-Nair's", "McNair": "Mac-Nair", "Fredendall": "Freh-den-dall", "Devers": "Dee-vers",
               "Witheridge": "With-er-idge", "Tobruk": "Toh-brook"},
 "films": {
  "sh_cologne": {"url": IA + "1945-03-26_Allies_Drive_Across_Rhine_To_Victory/1945-03-26_Allies_Drive_Across_Rhine_To_Victory.mp4",
                 "mono": True, "crop": "590:332:18:75", "credit": "Universal newsreel, 26 March 1945, Allies Drive Across Rhine " + NARA},
  "sh_rhino": {"url": IA + "ADC-1677/111-ADC-1677%20Tanks%20In%20France%20%2B%20Road%20Repair%20Of%20Tanks%20At%20St%20Jean%20De%20Daye%20%2B%20Tanks%20And%20Track%20Vehicles%20On%20Move%20France%20%2B%202ND%20Armored%20DIV%20Advance%20Normandy%20France.mp4",
               "mono": True, "credit": "Tanks in France, 2nd Armored Division (1944): US Army Signal Corps / NARA 111-ADC-1677 " + NARA},
  "sh_canisy": {"url": IA + "ADC-1672a/ADC-1672a.mov", "mono": True,
                "credit": "Canisy, France (1944): US Army Signal Corps / NARA 111-ADC-1672 " + NARA},
  "sh_panther": {"url": IA + "ADC-1970c/ADC-1970c.mov", "mono": True,
                 "credit": "Knocked-out Panther, France (1944): US Army Signal Corps / NARA 111-ADC-1970 " + NARA},
  "sh_snow": {"url": IA + "ADC-3124c/ADC-3124c.mov", "mono": True,
              "credit": "Houffalize, Belgium (January 1945): US Army Signal Corps / NARA 111-ADC-3124 " + NARA},
  "sh_plant": {"url": IA + "ARC-38910/ARC-38910.mov", "mono": True,
               "credit": "United News, June 1942: US Office of War Information / NARA ARC 38910 " + NARA},
  "sh_test": {"url": IA + "ARC-38922/ARC-38922.mov", "mono": True,
              "credit": "United News, September 1942: US Office of War Information / NARA ARC 38922 " + NARA},
  "sh_tunis": {"url": IA + "ARC-38954/ARC-38954.mov", "mono": True,
               "credit": "United News, Tunisia 1943: US Office of War Information / NARA ARC 38954 " + NARA},
  "sh_mods": {"url": IA + "CB-39/CB-39.mp4", "mono": True, "crop": "1180:664:50:28",
              "credit": "Combat Bulletin No. 39 (1945): US Army Signal Corps / NARA 111-CB-39 " + NARA},
  "sh_counter": {"url": IA + "1944-12-20_Allies_Fight_Fierce_Nazi_Counter-Blow/1944-12-20_Allies_Fight_Fierce_Nazi_Counter-Blow.mp4",
                 "mono": True, "crop": "580:326:20:90", "credit": "Universal newsreel, 20 December 1944 " + NARA},
  "sh_fdr": {"url": IA + "gov.fdr.283/gov.fdr.283.ogv", "mono": True, "crop": "240:135:86:50",
             "credit": "President Roosevelt, State of the Union, 6 January 1942: FDR Presidential Library, video 283 " + NARA},
  "news": {"url": IA + "ARC-39013/ARC-39013.mp4", "mono": True,
           "credit": "United News, D-Day (1944): US Office of War Information / NARA ARC 39013 " + NARA}},
 "period_audio": {
  "fdr": {"file": "FDR State of the Union 1942 tanks.mp3",   # only from period/ (the excerpt of IA gov.fdr.283)
          "url": IA + "gov.fdr.283/period_excerpt_is_in_the_repo",
          "speaker": "President Franklin D. Roosevelt", "date": "JANUARY 1942",
          "credit": "President Franklin D. Roosevelt, State of the Union, 6 January 1942 (FDR Presidential Library, video 283, public domain)",
          "text": "In this year, 1942, we shall produce 45,000 tanks."}},
 "pre": [{"dur": 2.8, "film": "sh_cologne", "from": 73, "to": 76, "stamp": ["MARCH 6", "1945"], "sfx": "explosion_massive"}],
 "whole": [ABRAMS],
 "tone": [MCNAIR, MCNAIR2, DEVERS, ABRAMS],
 "thumb": {"file": BAYS},
 "cover": {"file": BAYS, "x": 0.5, "y": 0.28, "zoom": 1.0, "color": False,
           "text": ["HISTORY OF", "THE SHERMAN", "IN {N} MINUTES"], "key": ["SHERMAN"], "sizes": [96, 150, 96],
           "mono": True},
 "promos": [
  {"id": "sherman_swim", "chapter": 5,
   "sentences": ["On D-Day, 29 tanks swim to Omaha Beach.",
                 "They are made for one-foot waves. These are six feet high.",
                 "Only two arrive, because their commanders know one thing: how to sail."],
   "shots": [film(1, "news", 496, 2.5), pic(2, DD), film(3, "news", 499, 5)],
   "top": "THE TANKS|THAT SWAM", "key": ["TANKS"],
   "cta": {"kind": "number", "big": "27", "line": "OF 29 SANK. WHAT SAVED TWO?"}, "end": "WHAT SAVED TWO?",
   "name": "29 Sherman Tanks Tried to Swim to Omaha Beach"},
  {"id": "sherman_ekins", "chapter": 8,
   "sentences": ["A British gunner has never fired his gun in action.",
                 "Then three German Tigers come into his sight.",
                 "He destroys all three, and one belongs to a famous tank commander: Michael Wittmann."],
   "shots": [pic(1, FF_NAMUR), pic(2, TIGER), film(3, "sh_panther", 142, 4)],
   "top": "THREE TIGERS|ONE SHERMAN", "key": ["TIGERS"],
   "cta": {"kind": "redacted", "line": "TIGER 007 BELONGED TO", "hidden": "WITTMANN"}, "end": "WHOSE TANK?",
   "name": "The Sherman Gunner Who Destroyed Three Tigers"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "sherman.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
