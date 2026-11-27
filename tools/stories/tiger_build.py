"""The Tiger tank, Nov 27 (genre 1, machines) in the NEW FORMAT (CLAUDE.md, Nov 23): voice No. 3, the Wochenschau 666
narrator (9 June 1943: 'Der Tiger, eine der stärksten Waffen unseres Heeres', Andrii: 'бери диктора для Tiger') as the
speech after sentence 1, one open question (why are so many Tigers abandoned by their own crews?), 2 cliff teasers.
Facts: Wikipedia 'Tiger I', 'Tiger II', 'Michael Wittmann', 'Battle of Villers-Bocage', 'Tiger 131', 'Tigerfibel',
'Ferdinand Porsche', 'Otto Carius', 'Elefant', 'Operation Totalize' (whole, sources/*.txt).
Films: Die Deutsche Wochenschau 659 / 666 / 672 / 674 / 726 / 729 / 736 / 747 (Internet Archive), NARA NPC-16700
(German Weekly Review 1944, PD mark), 111-ADC-1347 (US Signal Corps, Italy 1944: a knocked-out Tiger).
Photos: Bundesarchiv (CC BY-SA 3.0 de, credited), US Signal Corps / NARA (PD), IWM (PD-UKGov, corner mark trimmed),
Polish NAC (PD). Research: work/tiger/research.md.
Run: python tools/stories/tiger_build.py"""
import json, pathlib, collections

IA = "https://archive.org/download/"
BA = "Bundesarchiv Bild "
F01 = BA + "101I-635-3965-05, Panzerfabrik in Deutschland.jpg"
F21 = BA + "101I-635-3965-21, Panzerfabrik in Deutschland.jpg"
F28 = BA + "101I-635-3965-28, Panzerfabrik in Deutschland.jpg"
F34 = BA + "101I-635-3965-34, Panzerfabrik in Deutschland.jpg"
F07 = BA + "101I-635-3966-07, Panzerfabrik in Deutschland.jpg"
RASTEN = BA + "101III-Reprich-012-08, Wolfschanze, Hitler, Ley, Porsche und Göring.jpg"
KASSEL = BA + '146-1972-064-61, Kassel, Verladen eines Panzer VI "Tiger I".jpg'
USDISP = "German Heavy Tank Tiger I (PzKpfw VI) on Display in 1944.jpg"
KT_B8947 = "The British Army in the Normandy Campaign 1944 B8947.jpg"
TURRET45 = "Tiger II tank turret on a flatbed car at the Henschel & Sohn factory at Kassel, Germany, in 1945 (342-FH-3A21714-88032AC).jpg"
FIBEL = "Tigerfibel cover.jpg"
TUN1 = BA + "101I-554-0872-35, Tunesien, Panzer VI (Tiger I).jpg"
TUN2 = BA + "101I-557-1018-28A, Tunesien, Panzer VI (Tiger I), US-Fahrzeug.jpg"
BEJA = "Knocked-out German Tiger I tank at Béja, Tunisia, 23 April 1943 (111-SC-171649).jpg"
FOOT = "SC 171655 - The track of a German Mark VI tank in comparison to a man's foot. Beja, Tunisia. 23 April, 1943. (52272131056).jpg"
NA2640 = "The British Army in Tunisia 1943 NA2640.jpg"
KING = "The British Army in Tunisia 1943 NA3693.jpg"
LONDON = "The British Army in the United Kingdom 1939-45 H34426.jpg"
REPAIR = BA + '101I-022-2922-22, Russland, Reparatur Panzer VI "Tiger I".jpg'
TOW = BA + "101I-022-2926-11A, Russland, Abschleppen eines Tiger I.jpg"
HITS = BA + "101I-022-2935-24, Russland, Treffer an Panzer VI (Tiger I).jpg"
ONTOP = BA + '101I-022-2949-05, Russland, Soldaten auf Panzer VI "Tiger I".jpg'
GUN = BA + "101I-022-2949-22, Russland, Panzerkanone.jpg"
LADOGA = BA + "101I-461-0212-12, Russland, Panzer VI (Tiger I).jpg"
KURSK1 = BA + "101III-Groenert-019-21, Schlacht um Kursk, Panzer VI (Tiger I).jpg"
KURSK2 = BA + "101III-Zschaeckel-206-35, Schlacht um Kursk, Panzer VI (Tiger I).jpg"
LENIN = BA + '146-1981-071-07A, Russland, Panzer VI "Tiger I".jpg'
POWS = "Колонна немецких военнопленных проходит мимо танка «Тигр» на дороге в Белоруссии.jpg"
SOVIET = "Советские танкисты на трофейном немецком танке «Тигр» 502-го тяжелого танкового батальона.jpg"
W_ON = BA + "101I-299-1802-07, Nordfrankreich, Michael Wittmann auf Panzer VI (Tiger I).jpg"
W_ON2 = BA + "101I-299-1802-08, Nordfrankreich, Michael Wittmann auf Panzer VI (Tiger I).jpg"
FRANCE = BA + "101I-299-1805-16, Nordfrankreich, Panzer VI (Tiger I).jpg"
CROMWELL = BA + "101I-494-3376-18A, Villers-Bocage, zerstörter Cromwell-Panzer.jpg"
SHERMAN = BA + "101I-738-0267-28A, Villers-Bocage, zerstörter Sherman-Panzer.jpg"
VB_TIGER = BA + "101I-738-0275-10A, Bei Villers-Bocage, Panzer VI (Tiger I).jpg"
VB_CAMO = BA + "101I-738-0275-09A, Bei Villers-Bocage, getarnter Panzer VI (Tiger I).jpg"
W_HITLER = BA + "146-1989-099-15, Michael Wittmann und Adolf Hitler.jpg"
VB_RUBBLE = "The British Army in Normandy 1944 B8635.jpg"
GOODWOOD = "The Campaign in Normandy 1944 B8032.jpg"
WITTMANN = "Wittmann Michael (2-368).jpg"
BUDAPEST = BA + "101I-680-8282A-16A, Budapest, Panzer VI (Königstiger).jpg"
KT_PAIR = BA + "146-1975-102-14A, Panzer VI (Tiger II, Königstiger).jpg"
MOINET = "Destroyed German Tiger II tank at Moinet, Belgium, 23 January 1945 (111-SC-199473).jpg"
KT_POW = "German Tiger II tank passes American prisoners, 16 December 1944 (111-SC-198241).jpg"
PORSCHE = BA + "183-2005-1017-525, Dr. Ferdinand Porsche.jpg"
RAURAY = "The British Army in Normandy 1944 B6140.jpg"

N_SRC = "DIE DEUTSCHE WOCHENSCHAU · NARRATOR, JUNE 1943"
CROP = "690:388:15:75"                                  # 720x544 Wochenschau: the 4:3 frame without its black edges

M_TUN = {"places": [{"label": "TUNIS", "lat": 36.8, "lon": 10.18, "side": "red"},
                    {"label": "TEBOURBA", "lat": 36.83, "lon": 9.84, "side": "red"},
                    {"label": "BÉJA", "lat": 36.73, "lon": 9.18, "side": "blue"}],
         "routes": [[2, 1, "blue", 0.2]], "pad": 0.6}


def film(s, key, x, n=4, **k):
    return {"s": s, "film": key, "from": x, "to": x + n, **k}


def pic(s, f, **k):
    return {"s": s, "file": f, **k}


def beat(after, *shots):
    return {"after": after, "shots": [{"dur": d, "film": f, "from": x, "to": x + d, **({"sfx": s} if s else {})}
                                      for d, f, x, s in shots]}


C = [
 {"title": "", "mode": "action", "sentences": [
  "On 13 June 1944, at Villers-Bocage in Normandy, a single German tank comes out of cover and attacks a British column.",
  "It is a Tiger, and at the height of its service, almost no Allied gun can get through its front armour.",
  "Its commander is Michael Wittmann, and in Germany he is already a household name.",
  "But if the Tiger is so strong, why do so many of them end up abandoned by their own crews?",
  "It all begins with a shock, in the summer of 1941."],
  "shots": [
   film(1, "tg_726", 1002, 3.4, stamp=["VILLERS-BOCAGE"]),
   film(1, "tg_729", 256, 3),
   film(2, "tg_674", 1204, 4, note="ALMOST NO GUN"),
   film(2, "tg_674", 1259, 3, sfx="tank_gun"),
   pic(3, WITTMANN, reveal=[0.72, 0.3], name="MICHAEL WITTMANN", role="TIGER COMMANDER"),
   pic(4, POWS, x=0.62, y=0.2, label="AN ABANDONED TIGER · 1944"),
   film(5, "tg_700", 552, 3.5)],
  "beats": [{"after": 1, "audio": {"src": "w666", "from": 17.0, "to": 20.7}, "source": N_SRC,
             "shots": [{"dur": 3.7, "film": "tg_666", "from": 907.0, "to": 910.7, "source": N_SRC}]}]},

 {"title": "Copper", "mode": "people", "stamp": ["JUNE 1941"], "sentences": [
  "But in June 1941, when Germany invades the Soviet Union, its tanks meet the Soviet T-34 and the heavy KV-1.",
  "At Henschel, the designer Erwin Aders remembers the shock.",
  "A month earlier, Henschel and Ferdinand Porsche were asked to design a heavy tank of 45 tonnes.",
  "It is to carry an 8.8 centimetre gun, taken from the famous eighty-eight.",
  "The prototypes are due on 20 April 1942, Hitler's 53rd birthday.",
  "By August 1941, the ministry already has a name for the new tank: Tiger.",
  "Porsche is the man behind the Volkswagen, and he has known Hitler for years.",
  "Both prototypes carry the same turret, designed by Krupp, and both are shown to Hitler at Rastenburg.",
  "But Porsche's tank has a petrol-electric drive, and it needs large amounts of copper, which Germany is short of.",
  "Henschel wins.",
  "Expecting the order, Porsche has already built 100 chassis.",
  "Ninety-one of them become a tank destroyer without a turret, the Ferdinand, later called the Elefant."],
  "shots": [
   film(1, "tg_700", 540, 3),
   film(1, "tg_674", 1368, 4, label="A SOVIET TANK · 1943"),
   film(2, "tg_666", 900, 4, label="A GERMAN TANK FACTORY"),
   pic(3, PORSCHE, reveal=[0.75, 0.3], name="FERDINAND PORSCHE", role="ENGINEER"),
   pic(4, GUN, note="8.8 CM"),
   film(5, "tg_666", 912, 4, note="20 APRIL 1942"),
   pic(6, F21, label="THE TIGER"),
   pic(7, PORSCHE, zoom=1.3, y=0.3),
   pic(8, RASTEN, x=0.55, y=0.35, label="RASTENBURG · 1942"),
   pic(9, F34),
   film(10, "tg_666", 916, 3),
   pic(11, F07, trim=[0, 0, 0, 0.06], note="100 CHASSIS"),
   pic(12, RASTEN, zoom=1.5, x=0.5, y=0.35)],
  "beats": [{"after": 2, "quote": {"text": "There was great consternation when it was discovered that the Soviet tanks were superior to anything available to the Heer.",
                                   "name": "ERWIN ADERS", "role": "HENSCHEL DESIGNER"},
             "shots": [{"dur": 4.0, "film": "tg_674", "from": 1352, "to": 1356},
                       {"dur": 4.0, "film": "tg_700", "from": 556, "to": 560}]}]},

 {"title": "Kassel", "mode": "people", "stamp": ["KASSEL"], "sentences": [
  "But when the Tiger goes into production in August 1942, in Kassel, Henschel builds only 25 a month.",
  "A Tiger takes about twice as long to build as any other German tank of the time.",
  "It weighs more than twice as much as a Panzer IV.",
  "Its front armour is 100 millimetres thick, and around the gun it is 200.",
  "It is too heavy for many small bridges, so the first Tigers can drive under water, through a snorkel.",
  "Its road wheels overlap, and to change an inner one, the crew may have to take off up to nine others first.",
  "One Tiger costs the price of almost three Panzer IVs.",
  "The crews get a manual like no other, the Tigerfibel, with comic drawings and humorous poetry.",
  "It claims that each Tiger costs 800,000 Reichsmarks and 300,000 hours of work.",
  "But Hitler cannot wait, and he orders the Tiger into battle months earlier than planned."],
  "shots": [
   pic(1, KASSEL, label="KASSEL · 1942", note="25 A MONTH"),
   pic(2, F01, label="THE HENSCHEL FACTORY"),
   film(2, "tg_666", 904, 3),
   pic(3, FOOT, x=0.55, y=0.45, note="TWICE A PANZER IV"),
   pic(4, HITS, note="100 MM"),
   pic(5, USDISP, trim=[0.04, 0.05, 0.04, 0.05]),
   pic(6, F28, label="TIGER ROAD WHEELS"),
   film(6, "tg_666", 888, 4),
   pic(7, F07, zoom=1.4, x=0.5, y=0.45, trim=[0, 0, 0, 0.06], note="3 PANZER IVS"),
   pic(8, FIBEL, label="THE TIGERFIBEL · 1943"),
   pic(9, FIBEL, zoom=1.5, x=0.75, y=0.65, note="800,000 RM"),
   film(10, "tg_672", 818, 4)]},

 {"title": "Into the Swamp", "mode": "action", "stamp": ["LENINGRAD"], "sentences": [
  "But on 23 September 1942, near Leningrad, the first four Tigers go into action, in swampy forest.",
  "They can only move along roads and tracks, and the defence against them is far easier.",
  "Pushed too hard, the transmission cannot handle the weight, and many break down.",
  "One Tiger gets stuck in the swamp and has to be abandoned.",
  "The Soviets capture it largely intact, and study it to prepare their answer.",
  "But the Tigers that keep going are hard to stop.",
  "Otto Carius will command Tigers on this front, and he remembers their armour.",
  "After the war, he opens a pharmacy, and names it the Tiger Pharmacy."],
  "shots": [
   pic(1, LENIN, label="THE LENINGRAD FRONT"),
   film(1, "tg_659", 440, 3),
   film(2, "tg_674", 1180, 4),
   film(3, "tg_674", 1208, 4),
   pic(4, TOW, label="A TIGER UNDER TOW · 1943"),
   pic(5, SOVIET, label="SOVIET TANKMEN ON A CAPTURED TIGER", note="CAPTURED"),
   film(6, "tg_674", 1216, 2.5),
   film(6, "tg_674", 1276, 4, sfx="tank_gun"),
   pic(7, LADOGA, name="OTTO CARIUS", role="TIGER COMMANDER"),
   pic(8, ONTOP, zoom=1.3, x=0.5, y=0.4)],
  "beats": [{"after": 7, "quote": {"text": "Again and again, we admired the quality of the steel on our tanks. It was hard without being brittle.",
                                   "name": "OTTO CARIUS", "role": "TIGER COMMANDER"},
             "shots": [{"dur": 3.5, "file": HITS, "zoom": 1.3},
                       {"dur": 3.0, "film": "tg_674", "from": 1259, "to": 1262, "sfx": "tank_gun"}]}]},

 {"title": "Tiger 131", "mode": "action", "stamp": ["TUNISIA"], "sentences": [
  "But in Tunisia, on 1 December 1942, three Tigers fight for the first time in Africa, in an olive grove near Tebourba.",
  "Lee tanks hit them from only 80 to 100 metres, and the armour holds.",
  "The first Tiger lost to an Allied gun goes on 20 January 1943, to British anti-tank guns.",
  "On 24 April 1943, at a hill called Point 174, John Oscroft of the Sherwood Foresters is told to hit a Tiger with his anti-tank weapon.",
  "He fires, and the round bounces off.",
  "Then a shot from a Churchill tank jams the Tiger's turret, and the crew abandon it.",
  "It is Tiger 131, and the British repair it with parts from other Tigers.",
  "In Tunis, King George VI and Winston Churchill inspect it.",
  "In England, the tests find that its armour steel is of exceptionally high quality.",
  "In a British trial, its gun scores five hits in a row on a small target, from 1,200 yards.",
  "Britain rushes its new 17-pounder gun to Africa, and later puts it in the Sherman Firefly.",
  "In one fight, a single Firefly destroys three Tigers in 12 minutes."],
  "shots": [
   pic(1, TUN1, label="TUNISIA · 1943"),
   {"s": 1, "map": M_TUN},
   film(2, "tg_659", 916, 4, label="LEE TANKS IN TUNISIA · 1943"),
   film(2, "tg_659", 928, 3, note="80 METRES"),
   pic(3, TUN2),
   pic(3, BEJA, label="BÉJA, TUNISIA · APRIL 1943"),
   pic(4, NA2640, trim=[0, 0, 0.1, 0.1], name="JOHN OSCROFT", role="SHERWOOD FORESTERS"),
   film(5, "tg_659", 872, 3, sfx="explosion_close"),
   pic(6, BEJA, zoom=1.5, x=0.4, y=0.45),
   pic(7, NA2640, zoom=1.4, x=0.45, y=0.5, trim=[0, 0, 0.1, 0.1], note="TIGER 131"),
   pic(8, KING, trim=[0, 0, 0.1, 0.1], label="TUNIS · 1943"),
   pic(9, LONDON, trim=[0, 0, 0.1, 0.1], label="A CAPTURED TIGER IN LONDON · 1943"),
   pic(10, FOOT, zoom=1.5, x=0.4, y=0.5, note="5 HITS IN A ROW"),
   film(11, "tg_726", 1054, 3),
   film(12, "tg_674", 1276, 3.5, note="3 TIGERS · 12 MINUTES")]},

 {"title": "Citadel", "mode": "action", "stamp": ["JULY 1943"], "sentences": [
  "But in July 1943, two Tiger battalions join Operation Citadel, the German attack at Kursk.",
  "Michael Wittmann commands a platoon of four Tigers.",
  "On their first day in battle, his crew is credited with eight tanks and seven anti-tank guns.",
  "At one point, his Tiger survives a collision with a burning T-34.",
  "But the operation fails, and the Germans go back on the defensive.",
  "In the retreat, many broken-down Tigers have to be abandoned, because there is no time to repair them.",
  "To tow one Tiger takes two or three heavy half-tracks, and there are not enough of them.",
  "So crews tow with another Tiger, though it is forbidden, and it often wears out the second one too.",
  "In the second half of 1943, on average only about a third of the Tigers are ready for action.",
  "And the Soviets answer with bigger guns.",
  "Their SU-152 can knock out a Tiger, and it is nicknamed the beast killer."],
  "shots": [
   film(1, "tg_672", 814, 4, stamp=["KURSK"]),
   film(1, "tg_672", 822, 3),
   pic(2, KURSK1, label="KURSK · JULY 1943"),
   pic(2, W_ON, name="MICHAEL WITTMANN", role="PLATOON COMMANDER"),
   film(3, "tg_672", 942, 4, note="8 TANKS · 1 DAY"),
   film(4, "tg_674", 1408, 3, sfx="explosion_close"),
   film(5, "tg_672", 974, 4),
   pic(6, KURSK2),
   pic(6, POWS, zoom=1.4, x=0.7, y=0.2),
   pic(7, TOW, zoom=1.3, x=0.5, y=0.5),
   pic(8, REPAIR, label="REPAIRING A TIGER · 1943"),
   pic(9, ONTOP, note="ONLY 1 IN 3"),
   film(10, "tg_700", 546, 3.5),
   film(11, "tg_700", 584, 4, sfx="explosion_far")],
  "beats": [beat(4, (3.0, "tg_672", 854, "explosion_far"), (3.0, "tg_672", 858, None))]},

 {"title": "Villers-Bocage", "mode": "action", "stamp": ["FEBRUARY 1944"], "sentences": [
  "But on 2 February 1944, Hitler himself gives Wittmann the Oak Leaves to his Knight's Cross.",
  "By then he is credited with 117 tanks, though German tank kills are recorded for the whole unit.",
  "In June 1944 the Allies land in Normandy, and his battalion drives to the front from Beauvais.",
  "There are so many breakdowns on the way that his company has only six of its fourteen Tigers.",
  "On the morning of 13 June, British tanks drive into Villers-Bocage, and the people come out to greet them.",
  "Their lead squadron goes on to a ridge, and the carriers behind it park nose to tail along the road.",
  "Wittmann has no time to gather his company, so he sets off with one tank.",
  "At about 9 o'clock, his Tiger comes out onto the main road.",
  "It knocks out the last tank on the ridge, and a Firefly catches fire and blocks the road.",
  "Then he drives along the column, and the carriers burst into flames.",
  "In the town, the British tanks try to reverse away, but they are too slow.",
  "At the edge of the town, an anti-tank gun finally disables his Tiger.",
  "In less than 15 minutes, up to 14 tanks are destroyed, most or all of them credited to him.",
  "That afternoon, the Tigers that follow him into the town run into a British ambush, and several are lost.",
  "But German propaganda gives all of it to Wittmann, with doctored photographs."],
  "shots": [
   pic(1, W_HITLER, label="THE WOLF'S LAIR · 1944"),
   pic(2, W_ON2, note="117 TANKS"),
   film(3, "tg_729", 198.5, 3.5, label="NORMANDY · 1944"),
   film(3, "tg_729", 252, 3),
   pic(4, FRANCE, note="6 OF 14"),
   pic(5, VB_CAMO, stamp=["8:30 A.M."]),
   film(6, "tg_726", 1012, 4),
   pic(7, W_ON, zoom=1.4, x=0.5, y=0.3),
   pic(8, VB_TIGER, stamp=["9:00 A.M."]),
   film(9, "tg_729", 304, 3, sfx="tank_gun"),
   film(9, "tg_729", 348, 3),
   film(10, "tg_729", 352, 2.5, sfx="explosion_close"),
   pic(11, CROMWELL, label="VILLERS-BOCAGE · JUNE 1944"),
   pic(12, VB_RUBBLE, trim=[0, 0, 0.08, 0.08]),
   film(13, "tg_726", 1084, 4, note="14 TANKS · 15 MINUTES"),
   pic(14, VB_RUBBLE, zoom=1.4, x=0.4, y=0.6, trim=[0, 0, 0.08, 0.08]),
   pic(15, VB_TIGER, zoom=1.4, x=0.4, y=0.5)],
  "beats": [{"after": 7, "quote": {"text": "Instead I had to act quickly, as I had to assume that the enemy had already spotted me and would destroy me where I stood.",
                                   "name": "MICHAEL WITTMANN", "role": "13 JUNE 1944"},
             "shots": [{"dur": 4.0, "film": "tg_729", "from": 256, "to": 260},
                       {"dur": 4.0, "film": "tg_726", "from": 1001.5, "to": 1005.5}]},
            beat(12, (2.5, "tg_729", 364, "explosion_far"), (3.0, "tg_726", 1088, None))]},

 {"title": "The Last Attack", "mode": "action", "stamp": ["8 AUGUST"], "sentences": [
  "But on 8 August 1944, south of Caen, the Allies launch Operation Totalize, and Wittmann leads seven Tigers in a counter-attack.",
  "They cross open ground, towards the high ground.",
  "British tanks wait for them in the woods, and Canadian tanks fire through holes knocked in the walls of a chateau.",
  "Shells go through the upper hull of Wittmann's Tiger and set off the ammunition.",
  "The fire blows off the turret, and none of the crew gets out.",
  "German propaganda says he was killed by fighter-bombers.",
  "After the war, at least four different Allied units are named as the ones that did it.",
  "His crew are buried in an unmarked grave, and only in 1983 is it found.",
  "Today they lie together at the German war cemetery at La Cambe."],
  "shots": [
   film(1, "tg_729", 340, 4, label="NORMANDY · AUGUST 1944"),
   film(1, "tg_729", 560, 4),
   film(2, "tg_729", 368, 4),
   film(3, "tg_726", 1035, 3, sfx="tank_gun"),
   film(4, "tg_726", 1041, 3, sfx="explosion_massive"),
   pic(5, RAURAY, trim=[0, 0, 0.08, 0.08], label="A DESTROYED TIGER · NORMANDY 1944"),
   film(6, "tg_672", 1166, 2.5),
   pic(7, WITTMANN, zoom=1.3, y=0.3, note="4 UNITS"),
   film(8, "tg_729", 372, 4, note="1983"),
   pic(9, W_ON2, zoom=1.3, x=0.5, y=0.3)],
  "beats": [beat(5, (3.0, "tg_729", 352, "explosion_far"), (3.0, "tg_726", 1108, "low_rumble"))]},

 {"title": "The King Tiger", "mode": "action", "stamp": ["JULY 1944"], "sentences": [
  "But in July 1944, a new Tiger reaches Normandy: the Tiger II, which the Allies call the King Tiger.",
  "It weighs almost 70 tonnes, and its front armour is up to 185 millimetres thick.",
  "Its armour is sloped, like the Panther's, and its gun is even longer.",
  "In practice, it hits a target the size of a tank at 1,000 metres every time.",
  "But it has the same engine as the much lighter Tiger I, and it uses a lot of fuel, which Germany is short of.",
  "In its first fight, one of them falls into a bomb crater and cannot be recovered.",
  "In August, in Poland, a few T-34s ambush three of them, and their ammunition explodes.",
  "The Soviets capture three working King Tigers, and at Kubinka they find the steel of lower quality than before.",
  "In October, King Tigers help Otto Skorzeny's men take Budapest, which keeps Hungary on Germany's side.",
  "But in the autumn, five bombing raids destroy 95 percent of the Henschel plant.",
  "Instead of 1,500 King Tigers, only 492 are ever built."],
  "shots": [
   film(1, "tg_736", 726, 4),
   film(1, "tg_736", 732, 3),
   pic(2, KT_PAIR, note="70 TONNES"),
   film(3, "tg_736", 740, 4),
   film(4, "tg_736", 748, 4, note="1,000 METRES"),
   film(5, "tg_736", 744, 3.5),
   pic(6, GOODWOOD, trim=[0, 0, 0.08, 0.08], label="NORMANDY · JULY 1944"),
   film(7, "tg_700", 404, 3.5),
   pic(8, KT_B8947, trim=[0, 0, 0.08, 0.08], label="A CAPTURED KING TIGER"),
   pic(9, BUDAPEST, label="BUDAPEST · OCTOBER 1944"),
   pic(10, TURRET45, label="HENSCHEL, KASSEL · 1945", note="95 PERCENT"),
   film(11, "tg_736", 756, 4, note="ONLY 492")]},

 {"title": "Abandoned", "mode": "action", "stamp": ["ARDENNES"], "sentences": [
  "But in December 1944, in the Ardennes, at least 150 King Tigers go into the German offensive, nearly a third of all ever built.",
  "Most of them are lost.",
  "At La Gleize, the advance of Kampfgruppe Peiper is halted, and one of its King Tigers is abandoned there on 24 December.",
  "In Hungary, one battalion loses 25 King Tigers in 166 days.",
  "Only ten of them are knocked out by Soviet troops.",
  "Thirteen are blown up by their own crews, usually so that they do not fall into enemy hands.",
  "Another battalion loses 45 King Tigers in the east in the last months of the war, most of them destroyed by their own crews after breakdowns or for lack of fuel.",
  "That is the Tiger's real enemy: not the guns, but breakdowns, mud and empty fuel tanks.",
  "In all, only 1,347 Tiger Is and 492 Tiger IIs are built.",
  "Together they destroy at least 8,100 enemy tanks, for the loss of 1,725 Tigers, many of them abandoned or broken down."],
  "shots": [
   film(1, "tg_747", 703, 5),
   film(1, "tg_747", 708, 3, note="150 KING TIGERS"),
   pic(2, KT_POW, label="THE ARDENNES · DECEMBER 1944"),
   pic(3, MOINET, label="BELGIUM · JANUARY 1945"),
   pic(4, BUDAPEST, zoom=1.4, x=0.5, y=0.5, note="25 IN 166 DAYS"),
   film(5, "tg_700", 592, 4),
   pic(6, MOINET, zoom=1.5, x=0.5, y=0.5, note="13 BLOWN UP"),
   pic(7, KT_POW, zoom=1.4, x=0.45, y=0.45),
   film(7, "tg_700", 684.5, 2.5),
   film(8, "tg_adc", 84, 4, label="A KNOCKED-OUT TIGER · ITALY, 1944"),
   film(8, "tg_adc", 92, 4),
   film(9, "tg_736", 760, 4, note="1,839 TIGERS"),
   film(10, "tg_736", 764, 4, note="8,100 TANKS")],
  "beats": [beat(3, (3.0, "tg_747", 580, "low_rumble"), (3.0, "tg_736", 752, None))]},

 {"title": "The Last Tigers", "mode": "people", "stamp": ["1945"], "sentences": [
  "But when the war ends in 1945, very few Tigers survive the scrapping that follows.",
  "In the Soviet Union, dozens of captured Tigers are used as targets, and then melted down.",
  "Tiger 131 goes to the Tank Museum at Bovington, in England, in 1951.",
  "In 1990 the museum takes it apart, and in December 2003 it runs again, with the engine of the museum's King Tiger.",
  "Later it appears in the film Fury, the first real Tiger in a feature film for decades.",
  "In 2025, during maintenance, the crew finds a piece of battle shrapnel still wedged in one of its wheels.",
  "Today, only nine Tiger I tanks survive.",
  "The Tiger was built to break through, and it spent its war on the defensive."],
  "shots": [
   pic(1, TURRET45, zoom=1.3, x=0.5, y=0.5),
   pic(2, SOVIET, zoom=1.3, x=0.5, y=0.5),
   pic(3, LONDON, zoom=1.3, x=0.5, y=0.55, trim=[0, 0, 0.1, 0.1]),
   pic(4, USDISP, zoom=1.3, x=0.5, y=0.5, trim=[0.04, 0.05, 0.04, 0.05]),
   pic(5, KING, zoom=1.4, x=0.35, y=0.5, trim=[0, 0, 0.1, 0.1]),
   film(6, "tg_666", 889, 3),
   pic(7, LADOGA, zoom=1.3, x=0.5, y=0.5, note="ONLY 9"),
   film(8, "tg_674", 1212, 4),
   film(8, "tg_736", 766, 4)]},
]

FILMS = {
 "tg_659": ("19430421DieDeutscheWochenschauNr.65917min46s/1943-04-21%20-%20Die%20Deutsche%20Wochenschau%20Nr.%20659%20%2817min%2046s%29.mp4",
            "640:360:0:60", "Die Deutsche Wochenschau 659 (April 1943)"),
 "tg_666": ("1943-06-09-Die-Deutsche-Wochenschau-666/1943-06-09-DieDeutscheWochenschauNr.66619m52s720x544.mkv", CROP,
            "Die Deutsche Wochenschau 666 (June 1943)"),
 "tg_672": ("1943-07-21-Die-Deutsche-Wochenschau-672/1943-07-21-DieDeutscheWochenschauNr.67223m24s720x544.mkv", CROP,
            "Die Deutsche Wochenschau 672 (July 1943)"),
 "tg_674": ("1943-08-04-Die-Deutsche-Wochenschau-674/1943-08-04-DieDeutscheWochenschauNr.67424m13s720x544.mkv", CROP,
            "Die Deutsche Wochenschau 674 (August 1943)"),
 "tg_726": ("1944-08-03-Die-Deutsche-Wochenschau-726/1944-08-03-DieDeutscheWochenschauNr.72618m45s720x544.mkv", CROP,
            "Die Deutsche Wochenschau 726 (August 1944)"),
 "tg_729": ("1944-08-23-Die-Deutsche-Wochenschau-729/1944-08-23-DieDeutscheWochenschauNr.72912m58s720x544.mkv", CROP,
            "Die Deutsche Wochenschau 729 (August 1944)"),
 "tg_736": ("1944-10-11-Die-Deutsche-Wochenschau-736/1944-10-11-DieDeutscheWochenschauNr.73612m53s720x544.mkv", CROP,
            "Die Deutsche Wochenschau 736 (October 1944)"),
 "tg_747": ("1945-01-04-Die-Deutsche-Wochenschau-747/1945-01-04-DieDeutscheWochenschauNr.74711m54s720x544.mkv", CROP,
            "Die Deutsche Wochenschau 747 (January 1945)"),
}
films = {k: {"url": IA + u, "mono": True, "crop": c,
             "credit": t + " (public domain in the US as seized enemy property, via Internet Archive)"}
         for k, (u, c, t) in FILMS.items()}
films["tg_700"] = {"url": IA + "NPC-16700/GERMAN%20WEEKS%20REVIEW%20ca%201940%20-%20ca%201945.mp4", "mono": True,
                   "credit": "German Weekly Review (1944): NARA 428-NPC-16700 (public domain, via Internet Archive)"}
films["tg_adc"] = {"url": IA + "111-adc-1347/111-adc-1347.mp4", "mono": True, "crop": "720:405:0:37",
                   "credit": "Mark VI tank knocked out, Italy (June 1944): US Army Signal Corps / NARA 111-ADC-1347 (public domain, via Internet Archive)"}

STORY = {
 "priority": 10, "format": "entire", "voice": "andrii", "intro_beats": True,
 "topic": "Tiger I",
 "sources": ["Tiger I", "Tiger II", "Michael Wittmann", "Battle of Villers-Bocage", "Tiger 131", "Tigerfibel",
             "Ferdinand Porsche", "Otto Carius", "Elefant", "Operation Totalize"],
 "title": "The ENTIRE History of the Tiger Tank in {N} Minutes",
 "question": "Was the Tiger the best tank of the war, or a waste of Germany's steel and fuel?",
 "summary": "From Porsche's copper-hungry rival and the Henschel works in Kassel to the swamps of Leningrad, Tiger 131, "
            "Kursk, Michael Wittmann at Villers-Bocage and the King Tigers blown up by their own crews, this is the whole "
            "story of the Tiger tank, told with archive film and the voice of the German newsreel of 1943.",
 "tags": ["Tiger tank", "Tiger I", "King Tiger", "Tiger II", "Michael Wittmann", "Villers-Bocage", "Tiger 131",
          "Panzer", "Kursk", "Ferdinand Porsche", "WW2 tanks", "WW2 history", "world war 2"],
 "pronounce": {"Villers-Bocage": "Vee-lair Bo-cahzh", "Wittmann": "Vit-mun", "Aders": "Ah-ders", "Tigerfibel": "Tee-ger-fee-bel",
               "Tebourba": "Teh-boor-bah", "Oscroft": "Oss-croft", "Kubinka": "Koo-bin-kah", "Skorzeny": "Skor-tsay-nee",
               "Peiper": "Pie-per", "Gleize": "Glayz", "Cambe": "Cahmb", "Kassel": "Kass-el", "Carius": "Kah-ree-us",
               "Henschel": "Hen-shel", "Heer": "Hair", "Rastenburg": "Rass-ten-burg", "Bovington": "Bovv-ing-ton",
               "Totalize": "Toe-tal-ize", "Beauvais": "Bo-vay"},
 "films": films,
 "period_audio": {
  "w666": {"file": "Wochenschau 666 Tiger 1943.mp3",
           "speaker": "Die Deutsche Wochenschau narrator", "date": "JUNE 1943",
           "credit": "Die Deutsche Wochenschau 666 (9 June 1943), narrator (public domain in the US as seized enemy property, via Internet Archive)",
           "text": "Der Tiger, eine der stärksten Waffen unseres Heeres. (The Tiger, one of the strongest weapons of our army.)"}},
 "pre": [{"dur": 2.8, "film": "tg_729", "from": 252, "to": 254.8, "stamp": ["13 JUNE", "1944"], "sfx": "tank_gun"}],
 "whole": [PORSCHE, WITTMANN, FIBEL],
 "tone": [PORSCHE, WITTMANN],
 "trims": {F07: [0, 0, 0, 0.06]},
 "thumb": {"file": KT_POW},
 "cover": {"file": KT_POW, "x": 0.5, "y": 0.0, "zoom": 1.1, "color": False,
           "text": ["HISTORY OF THE", "TIGER TANK", "IN {N} MINUTES"], "key": ["TIGER", "TANK"], "sizes": [96, 150, 96],
           "mono": True},
 "promos": [
  {"id": "tiger_alone", "chapter": 6,
   "sentences": ["A British column drives into a Norman town, and the people cheer.",
                 "A German tank commander has no time to gather his company.",
                 "So he makes his decision: he sets off alone, with one Tiger."],
   "shots": [pic(1, VB_CAMO), film(2, "tg_729", 256, 4), pic(3, W_ON, zoom=1.3, x=0.5, y=0.3)],
   "top": "ONE TIGER|AGAINST A COLUMN", "key": ["TIGER"],
   "cta": {"kind": "number", "big": "15", "line": "MINUTES. WHAT DID ONE TIGER DO?"}, "end": "WHAT DID ONE TIGER DO?",
   "name": "One Tiger Tank Against a Whole British Column"},
  {"id": "tiger_copper", "chapter": 1,
   "sentences": ["Two engineers race to build Hitler a heavy tank by his birthday.",
                 "Both prototypes are shown to Hitler at his headquarters.",
                 "And one design loses because of a single metal: copper."],
   "shots": [pic(1, PORSCHE, zoom=1.2, y=0.3), pic(2, RASTEN, x=0.55, y=0.35), film(3, "tg_666", 912, 4)],
   "top": "WHY PORSCHE LOST|THE TIGER", "key": ["TIGER"],
   "cta": {"kind": "redacted", "line": "PORSCHE LOSES BECAUSE OF", "hidden": "COPPER"}, "end": "WHY DID PORSCHE LOSE?",
   "name": "Why Porsche Lost the Tiger Tank"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "tiger.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
n = collections.Counter(s["file"] for c in C for s in c["shots"] + [x for b in c.get("beats", []) for x in b["shots"]] if s.get("file"))
print("photos used > 2:", {k: v for k, v in n.items() if v > 2})
