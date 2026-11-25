"""Goering and his psychiatrist Douglas Kelley, Nov 24 (Andrii: genre 3, trials; Thu 26.11 21:00 London): a hand story
in the NEW FORMAT (CLAUDE.md, Nov 23): voice No. 3, Goering's plea in court ('in the sense of the indictment, not
guilty', 21 November 1945, US Army film ADC-9930, with sound) as a beat after sentence 1, one open question (what did
Kelley find in their minds? answered in 'What He Found' and at the end).
The plan's hook ('the psychiatrist who gave him the poison') is NOT a fact: Kelley had left Nuremberg months before.
Facts: the Wikipedia articles of STORY['sources'] (whole, sources/*.txt). Films: public domain, Internet Archive.
Run: python tools/stories/kelley_build.py"""
import json, pathlib

KELLEY = "Douglas McGlashan Kelley (1912-1958) portrait.webp"
OBIT1 = ("Douglas McGlashan Kelley (1912-1958) obituary in the Berkeley Daily Gazette of Berkeley, California, "
         "page 1.jpg")
OBIT2 = ("Douglas McGlashan Kelley (1912-1958) obituary in the Berkeley Daily Gazette of Berkeley, California, "
         "page 2.jpg")
G_AUG = "Göring Augsburg 1945-beschnitten restored.jpeg"
G_AUG2 = "Göring Augsburg 1945.jpg"
MUGS = "Göring Detention Report mugshots.jpg"
REPORT = "GöringDetentionReport.png"
ASHCAN = "Camp Ashcan prisoners.jpg"
PALACE = "Palace Hotel, Mondorf-les-Bains.JPG"
ANDRUS = "Burton C. Andrus in Nurnberg.jpg"
ANDRUS2 = "Fritzsche, Papen, Schacht with Andrus.jpg"
HESS = "Rudolf Hess at Nuremberg prison.jpg"
RIBB = "Joachim von Ribbentrop in his cell Nuremberg Trials 1945.jpeg"
BLOT = "Rorschach blot 08.jpg"
BLOTS = "Rorschach inkblots.jpg"
CELLS = "German War Crimes Trials. Nuernberg & Dachau - NARA - 292605.jpg"
DOCK2 = "Nuremberg trials 28-1431M original.jpg"
BLOT3, BLOT4 = "Rorschach blot 03.jpg", "Rorschach blot 04.jpg"
PRISON = "Prison used to hold defendants at the Nuremberg trial.jpg"
YARD = "Nazi war criminals and American guards in the exercise yard of Nuremberg prison.jpg"
JACKSON = "Prosecutor Robert Jackson at Nuremberg Trials.jpg"
G_DOCK = "Göring in the dock at the Nuremberg Trials (cropped).jpg"
G_HESS = "Defendants Göring, Dönitz, and Hess conferring Nuremberg Trials.jpeg"
DOCK = "Defendants in the dock at the Nuremberg Trials.jpg"
LUNCH = "Hermann Goering Karl Doenitz Walther Funk Baldur von Schirach and Alfred Rosenberg eat lunch at nuremberg trial.jpg"
G_TRIAL = "Hermann Göring on trial at Nuremberg 1946.jpeg"
G_NEUR = "Goeirng&VonNeurath.jpg"
STREICHER = "StreicherDarkerSharpHLSL.jpg"
BACKROW = "Frick, Streicher, Funk, Papen, Seyß-Inquart, Speer, Neurath.jpg"
G_HESS2 = "Proces Neurenberg. Herman Goering en Rudolf Hess, Bestanddeelnr 901-1886.jpg"
DOCK_UP = "Nuremberg Trials. Looking down on defendants dock, circa 1945-1946. - NARA - 540127.jpg"
PALACE_J = "The Palace of Justice in Nurnberg.jpg"
G_PORT = "Hermann Göring - Röhr (3x4 cropped).jpg"
G_HITLER = "Bundesarchiv Bild 183-1983-0331-500, Hermann Göring und Adolf Hitler bei Truppenbesuch.jpg"
LEY = "Robert Ley (cropped) (2).jpg"
LEY2 = "Bundesarchiv Bild 183-H03909, Tripolis, Ley begrüsst die KdF-Urlauber.jpg"
GUARD = "German War Crimes Trials. Nuernberg & Dachau - NARA - 292606.jpg"
COURT = "German War Crimes Trials. Nuernberg & Dachau - NARA - 292601.jpg"
STAND = "Proces Neurenberg, Bestanddeelnr 901-2017.jpg"

P_SRC = "HERMANN GÖRING IN COURT · 21 NOVEMBER 1945 · 'IN THE SENSE OF THE INDICTMENT, NOT GUILTY'"


def film(s, key, x, n=6, **k):
    return {"s": s, "film": key, "from": x, "to": x + n, **k}


def pic(s, f, **k):
    return {"s": s, "file": f, **k}


def quote(after, text, name, role, *shots):
    return {"after": after, "quote": {"text": text, "name": name, "role": role}, "shots": list(shots)}


C = [
 {"title": "", "mode": "action", "sentences": [
  "On the night of 15 October 1946, in a guarded cell in Nuremberg, Hermann Göring dies of cyanide, two hours before his execution.",
  "Eleven years later, in California, the man who studied him dies of the same poison.",
  "He is Douglas Kelley, the American psychiatrist who was sent to look inside the minds of 22 Nazi leaders.",
  "He was looking for the thing that made them different, so what did he find?",
  "It all begins with a prisoner who is too heavy for the airplane."],
  "shots": [
   film(1, "kl_await", 438.6, 3, stamp=["NUREMBERG"]),
   film(1, "kl_press", 110.5, 5, name="HERMANN GÖRING", role="COMMANDER OF THE LUFTWAFFE"),
   {"s": 2, "file": OBIT1, "trim": [0, 0, 0, 0.795], "card": True},
   pic(3, KELLEY, reveal=[0.62, 0.28], name="DOUGLAS KELLEY", role="U.S. ARMY PSYCHIATRIST"),
   pic(4, BLOT, card=True),
   film(5, "kl_loot", 208.3, 3.5)],
  "beats": [{"after": 1, "audio": {"src": "plea", "from": 0.0, "to": 6.6}, "source": P_SRC, "shots": [
   {"dur": 3.4, "film": "kl_plea", "from": 248, "to": 251.4, "source": P_SRC},
   {"dur": 3.2, "film": "kl_plea", "from": 573, "to": 576.2, "source": P_SRC}]}]},

 {"title": "Too Heavy to Fly", "mode": "people", "stamp": ["9 MAY 1945"], "sentences": [
  "But on 9 May 1945, the second man of the Third Reich is looking for someone to surrender to.",
  "Hermann Göring was the commander of the Luftwaffe, and Hitler's chosen successor.",
  "Then, in the last days, he asked if he should take over, and Hitler threw him out of the party.",
  "Martin Bormann ordered that he be executed if Berlin fell.",
  "So Göring drives to the American lines, to surrender to them and not to the Soviets.",
  "The very next day, American generals sit down with him and ask questions.",
  "Reporters are allowed to ask him too.",
  "Then he has to be flown to a prison camp, and the first airplane cannot lift him.",
  "It is a little Piper, and he weighs 270 pounds.",
  "A bigger airplane takes him to a luxury hotel in Luxembourg."],
  "shots": [
   film(1, "kl_loot", 159, 4, label="GÖRING SURRENDERS · MAY 1945"),
   pic(2, G_PORT, y=0.25),
   pic(3, G_HITLER, x=0.55),
   film(4, "kl_ruins", 221, 5),
   film(5, "kl_loot", 163.2, 4),
   film(6, "kl_loot", 173.6, 3),
   film(6, "kl_press", 48, 4, label="AUGSBURG · MAY 1945"),
   film(7, "kl_press", 33, 4),
   film(7, "kl_press", 102.5, 3),
   film(8, "kl_press", 138, 4),
   pic(9, G_AUG, y=0.2, note="270 POUNDS"),
   pic(10, PALACE, label="PALACE HOTEL · MONDORF")]},

 {"title": "Ashcan", "mode": "people", "stamp": ["MONDORF"], "sentences": [
  "But in Mondorf, in the Palace Hotel, the guests sleep on Army cots.",
  "Around it there is a fence with electric wire, 15 feet high, and towers with machine guns.",
  "The Americans call the place Ashcan, and 86 of the most important Nazis are locked up in it.",
  "The commandant is Colonel Burton Andrus, with a shellacked helmet and a swagger stick.",
  "He takes their razor blades, their neckties and their suspenders, so that nobody can kill himself.",
  "And his most important prisoner is an addict.",
  "Every day, Göring takes drugs equal to three or four grains of morphine.",
  "The doctors take him off it, and put him on a strict diet.",
  "He loses 60 pounds.",
  "What is left is a thinner man with a clear head, and an IQ of 138."],
  "shots": [
   pic(1, ASHCAN, label="CAMP ASHCAN · 1945"),
   film(2, "kl_loot", 22, 4.5),
   pic(3, ASHCAN, zoom=1.8, x=0.5, y=0.85, note="86 PRISONERS"),
   pic(4, ANDRUS, name="BURTON ANDRUS", role="PRISON COMMANDANT"),
   film(5, "kl_loot", 105.6, 2),
   film(5, "kl_loot", 177, 2.5),
   film(6, "kl_press", 117, 2.5),
   film(7, "kl_press", 120, 4),
   pic(8, REPORT, card=True),
   pic(9, MUGS, trim=[0, 0.1, 0.1, 0.15], note="60 POUNDS LOST"),
   pic(10, G_DOCK, y=0.2, note="IQ 138")]},

 {"title": "The Magician", "mode": "people", "stamp": ["AUGUST 1945"], "sentences": [
  "But in August 1945, before anyone can be tried, the Army has to know if these men are sane.",
  "It sends Major Douglas Kelley, a psychiatrist from California.",
  "He has been in Europe treating American soldiers for combat stress.",
  "He is also a magician, and once an officer of the Society of American Magicians.",
  "In San Francisco he taught magic tricks to his patients, to help them get well.",
  "Now he has 22 patients whom he is not allowed to treat.",
  "He has to say who is insane, and who may break down in court.",
  "With the psychologist Gustave Gilbert, he puts ink blots in front of them, and asks what they see.",
  "He gives them IQ tests, and has them write about their lives.",
  "In all, he spends 80 to 90 hours in their company."],
  "shots": [
   film(1, "kl_await", 368, 4, label="NUREMBERG · 1945"),
   pic(2, CELLS, y=0.45, note="MAJOR KELLEY"),
   film(3, "kl_await", 426.2, 2.6),
   pic(4, BLOTS, card=True),
   film(5, "kl_await", 422, 1.4),
   film(5, "kl_await", 445, 2.6),
   pic(6, PRISON, y=0.4, label="NUREMBERG PRISON", note="22 PATIENTS"),
   film(7, "kl_await", 451.1, 1.1),
   film(7, "kl_await", 414, 2),
   pic(8, BLOT, zoom=1.2),
   film(9, "kl_loot", 36, 1.8),
   pic(9, RIBB, y=0.3),
   pic(10, GUARD, y=0.35)]},

 {"title": "Twenty-Two Cells", "mode": "people", "stamp": ["NUREMBERG"], "sentences": [
  "But in Nuremberg, behind every door, there is a man who is hiding something.",
  "On the IQ tests, the banker Hjalmar Schacht has the highest score, 143.",
  "Göring comes third.",
  "Julius Streicher, the publisher of Der Stürmer, is the last, with 106.",
  "In October, Rudolf Hess arrives, once Hitler's deputy.",
  "He brings samples of food, and says that the British have poisoned it.",
  "He also says that he has lost his memory.",
  "They bring in his old secretaries, they show him old newsreels, and he does not react.",
  "Kelley examines him, and gives his opinion.",
  "Hess can be tried, he says.",
  "On 30 November, Hess stands up in court, and tells everyone that it was a trick."],
  "shots": [
   film(1, "kl_await", 457, 2.8),
   film(1, "kl_await", 460.2, 1.6),
   pic(2, ANDRUS2, note="143"),
   film(3, "kl_await", 448.4, 2.4, note="THIRD"),
   pic(4, STREICHER, y=0.2, name="JULIUS STREICHER", role="PUBLISHER OF DER STÜRMER"),
   pic(5, HESS, reveal=[0.6, 0.25], name="RUDOLF HESS", role="HITLER'S DEPUTY UNTIL 1941"),
   film(6, "kl_await", 462, 2),
   film(6, "kl_plea", 214, 4),
   film(7, "kl_plea", 222, 4),
   pic(8, G_HESS2, zoom=1.4, x=0.45, y=0.45),
   film(9, "kl_dec", 44.2, 4),
   film(10, "kl_sent", 372, 4),
   film(11, "kl_sent", 76.5, 4)],
  "beats": [quote(9, "A true psychoneurosis, primarily of the hysterical type, engrafted on a basic paranoid and schizoid personality, with amnesia, partly genuine and partly feigned.",
                  "DOUGLAS KELLEY", "ON RUDOLF HESS", {"dur": 5.5, "film": "kl_sent", "from": 388, "to": 393}, {"dur": 5.5, "film": "kl_sent", "from": 404, "to": 409})]},

 {"title": "The First Suicide", "mode": "people", "stamp": ["24 OCTOBER 1945"], "sentences": [
  "But on 24 October 1945, before the trial has begun, one of the doors is opened too late.",
  "Robert Ley was the head of the German Labour Front, and the man who ran the workers' holidays.",
  "Three days before, he was given the indictment, and it calls him a criminal.",
  "He told Kelley and Gilbert what he thought of it.",
  "Now he is found dead in his cell.",
  "Of all the prisoners, he is the only one whom Kelley had found insane.",
  "Kelley believes that his brain was damaged, perhaps in an airplane crash in 1917.",
  "He sends the brain to Washington, and the doctors there agree with him.",
  "Two years later, they look again, and find nothing clear.",
  "Andrus now has a guard at every door, 24 hours a day.",
  "The prisoners must sleep with their hands outside the blankets.",
  "Even the tables are built to collapse under a man's weight."],
  "shots": [
   film(1, "kl_await", 452.2, 1.1),
   film(1, "kl_await", 465, 1.8),
   pic(2, LEY, y=0.2, name="ROBERT LEY", role="HEAD OF THE GERMAN LABOUR FRONT"),
   film(3, "kl_loot", 30, 4),
   pic(4, LEY2, trim=[0, 0, 0, 0.05]),
   film(5, "kl_await", 437.2, 1.2),
   film(5, "kl_await", 453.8, 1.1),
   pic(6, LEY, zoom=1.4, y=0.2, note="THE ONLY ONE"),
   film(7, "kl_await", 442, 3),
   pic(8, BLOT4),
   film(9, "kl_await", 390, 2.6),
   pic(10, GUARD, zoom=1.4, y=0.3, note="24 HOURS A DAY"),
   film(11, "kl_await", 468, 2.6),
   pic(12, YARD, y=0.5, label="THE EXERCISE YARD")],
  "beats": [quote(4, "Stand us against a wall and shoot us, well and good, you are victors.",
                  "ROBERT LEY", "TO DOUGLAS KELLEY AND GUSTAVE GILBERT",
                  {"dur": 5.5, "film": "kl_await", "from": 446.2, "to": 447.8})]},

 {"title": "The Dock", "mode": "people", "stamp": ["20 NOVEMBER 1945"], "sentences": [
  "But on 20 November 1945, when the trial begins, the sick man from Mondorf has become the leader of the dock.",
  "He wants to read out a long statement, and the judge stops him.",
  "After that he must be silent, so he laughs, shakes his head, and takes notes.",
  "He whispers to the others, and tries to control Hess, who sits beside him.",
  "In the breaks he tells them what to say, until he is put in solitary confinement.",
  "On 29 November, the prosecution shows a film from the liberated concentration camps.",
  "It shocks everyone in the courtroom, even the judges.",
  "Göring says that such films must have been faked.",
  "In one interview he talks with Gilbert about war, and says that the common people never want it.",
  "Gilbert writes it all down."],
  "shots": [
   film(1, "kl_plea", 162.5, 4, label="NUREMBERG · NOVEMBER 1945"),
   pic(1, PALACE_J),
   film(2, "kl_plea", 290, 5),
   film(3, "kl_dec", 45, 4),
   pic(4, G_HESS),
   pic(5, LUNCH, note="NO MORE TALKING"),
   film(6, "kl_plea", 182, 4),
   film(7, "kl_plea", 200, 4),
   pic(8, G_HESS2, zoom=1.6, x=0.6, y=0.45, note="FAKED?"),
   pic(9, G_NEUR, y=0.3),
   pic(10, G_DOCK, zoom=1.3, y=0.2)],
  "beats": [quote(9, "The people can always be brought to the bidding of the leaders. That is easy. All you have to do is tell "
                  "them they are being attacked, and denounce the pacifists for lack of patriotism.",
                  "HERMANN GÖRING", "TO GUSTAVE GILBERT, NUREMBERG",
                  {"dur": 5.5, "film": "kl_press", "from": 122.5, "to": 125.5},
                  {"dur": 5.5, "film": "kl_press", "from": 111, "to": 116})]},

 {"title": "What He Found", "mode": "people", "stamp": ["CALIFORNIA"], "sentences": [
  "But in California, the man who knew them first opens his boxes, because Kelley has gone home.",
  "Another psychiatrist, Leon Goldensohn, has taken his place.",
  "He has brought a strange collection with him.",
  "There are his notes and the tests, and X-rays of Hitler's skull.",
  "There are Göring's capsules, and the food that Hess believed was poisoned.",
  "He writes a book, and calls it 22 Cells in Nuremberg.",
  "People are waiting to read about monsters.",
  "Kelley writes that he has found no special Nazi illness.",
  "In some circumstances, he says, many people would do what they did.",
  "Gilbert writes a book too, Nuremberg Diary, and the two men become rivals."],
  "shots": [
   pic(1, OBIT2, card=True),
   film(2, "kl_await", 399.5, 4),
   film(3, "kl_loot", 97.5, 3.5),
   film(4, "kl_loot", 36.3, 1.6),
   pic(4, BLOTS, zoom=1.0, card=True),
   pic(5, MUGS, zoom=1.2, x=0.8, y=0.4),
   pic(6, DOCK, y=0.5, note="22 CELLS"),
   film(7, "kl_plea", 464.5, 4),
   pic(8, BACKROW, y=0.4, note="NO NAZI ILLNESS"),
   pic(9, DOCK, zoom=1.5, x=0.35, y=0.4),
   pic(10, STAND, y=0.4)],
  "beats": [quote(8, "They were simply creatures of their environment, as all humans are.",
                  "DOUGLAS KELLEY", "22 CELLS IN NUREMBERG", {"dur": 4.8, "file": DOCK2, "zoom": 1.0, "y": 0.4})]},

 {"title": "His Guilt Is Unique", "mode": "people", "stamp": ["MARCH 1946"], "sentences": [
  "But in March 1946, Göring finally gets what he wants, and he is allowed to speak.",
  "He speaks for days, about his loyalty to Hitler, and about himself.",
  "To direct questions he gives long answers, and he has an excuse for everything.",
  "About the camps, he says, he knew nothing.",
  "Then the American prosecutor, Robert Jackson, reads from a piece of paper.",
  "It is the record of a meeting after the pogrom of November 1938, and Göring is planning there to take the property of the Jews.",
  "Then David Maxwell Fyfe shows that he must have known of the killing of 50 airmen, who had escaped from a camp.",
  "He must also have known about the murder of the Hungarian Jews.",
  "The trial lasts 218 days.",
  "Göring is found guilty on all four counts, and the sentence is death by hanging.",
  "He asks to be shot like a soldier, and the court refuses."],
  "shots": [
   pic(1, G_TRIAL, y=0.35),
   film(2, "kl_dec", 33, 4),
   pic(3, G_TRIAL, zoom=1.8, x=0.52, y=0.5),
   film(4, "kl_dec", 20, 5),
   pic(5, JACKSON, name="ROBERT JACKSON", role="AMERICAN CHIEF PROSECUTOR"),
   film(6, "kl_sent", 108.5, 4),
   film(6, "kl_dec", 8, 5),
   film(7, "kl_sent", 132, 5, note="50 AIRMEN"),
   pic(8, COURT, y=0.4),
   film(9, "kl_sent2", 153.6, 5, note="218 DAYS"),
   film(10, "kl_sent2", 176, 5, note="DEATH BY HANGING"),
   film(11, "kl_sent", 188.5, 5)],
  "beats": [quote(10, "His guilt is unique in its enormity. The record discloses no excuses for this man.",
                  "THE TRIBUNAL", "JUDGMENT ON HERMANN GÖRING", {"dur": 6.0, "film": "kl_sent2", "from": 520.5, "to": 526})]},

 {"title": "The Capsule", "mode": "action", "stamp": ["15 OCTOBER 1946"], "sentences": [
  "But on 15 October 1946, with a guard at his door day and night, Göring still has one thing that nobody has found.",
  "It is a capsule of potassium cyanide.",
  "That night, through the door, the guards see that something is wrong.",
  "A doctor is called, and within five minutes the prisoner is dead.",
  "Andrus has lost him, two hours before the gallows.",
  "So where did it come from?",
  "In his last note, Göring writes that he has had it since he became a prisoner.",
  "Another capsule is found in a jar of his hair cream.",
  "Later, people suspect an American officer, Jack Wheelis, because Göring gave him a gold watch, a pen and a cigarette case.",
  "In 2005, a former guard, Herbert Lee Stivers, says that he brought Göring medicine, in a fountain pen, for a girl named Mona.",
  "Nobody knows the truth.",
  "It did not come from his psychiatrist: Kelley had long left.",
  "In America, he calls the death an admirably defiant act."],
  "shots": [
   film(1, "kl_await", 439, 3),
   film(1, "kl_await", 448.2, 2.5),
   film(2, "kl_loot", 175, 1.8, note="CYANIDE"),
   film(3, "kl_await", 450.8, 2),
   film(4, "kl_await", 443, 3),
   film(4, "kl_await", 453.8, 1.1),
   pic(5, ANDRUS, zoom=1.3, y=0.25, note="TWO HOURS"),
   film(6, "kl_press", 126.5, 4),
   pic(7, REPORT, zoom=1.5, x=0.2, y=0.5),
   film(8, "kl_loot", 106, 1.8, note="HAIR CREAM"),
   pic(9, PRISON, zoom=1.4, x=0.4, y=0.5),
   film(9, "kl_await", 426.5, 2.4),
   pic(10, YARD, zoom=1.4, y=0.7),
   film(10, "kl_await", 413.5, 2.4),
   film(11, "kl_press", 144, 2.5),
   film(12, "kl_press", 148, 2.5),
   pic(13, G_AUG2, y=0.2)],
  "beats": [{"after": 4, "shots": [
   {"dur": 3.2, "film": "kl_await", "from": 438.6, "to": 441.4, "sfx": "low_rumble"},
   {"dur": 2.6, "film": "kl_await", "from": 434.2, "to": 436.6}]}]},

 {"title": "New Year's Day", "mode": "people", "stamp": ["BERKELEY"], "sentences": [
  "But in Berkeley, where he is a professor now, Douglas Kelley has a secret at home.",
  "Outside he is a star: he advises the police, the Air Force and San Quentin prison.",
  "He works with lie detectors, and with truth serums that he tries on himself.",
  "Inside, as his family tells later, he drinks, he has fits of anger, and he talks of suicide.",
  "On 1 January 1958, he burns himself while he is cooking, and it all breaks out.",
  "In front of his wife, his father and his three children, he takes a capsule of potassium cyanide.",
  "He is 45 years old.",
  "The newspapers report that the poison came from Nuremberg, and his family does not believe it.",
  "It is one more capsule that nobody can trace.",
  "He had spent 80 hours with the worst men of his time, and come back with an answer that nobody wanted.",
  "He went to Nuremberg to find out what made them different, and he found almost nothing."],
  "shots": [
   pic(1, KELLEY, zoom=1.5, y=0.2),
   pic(2, OBIT2, card=True),
   film(3, "kl_await", 387, 2.6),
   pic(3, BLOT3),
   film(4, "kl_await", 406.5, 4),
   film(5, "kl_loot", 102.5, 2),
   film(5, "kl_await", 430, 3),
   film(6, "kl_loot", 19.3, 2.6),
   film(7, "kl_await", 434.2, 2.2, note="1912 · 1958"),
   pic(8, CELLS, zoom=1.5, x=0.75, y=0.5),
   film(9, "kl_await", 462.3, 1.7),
   pic(10, DOCK_UP, y=0.5),
   pic(11, BACKROW, zoom=1.4, x=0.4, y=0.5),
   film(11, "kl_await", 438.7, 3)],
  "beats": [{"after": 7, "shots": [{"dur": 5.5, "file": OBIT1, "trim": [0, 0, 0, 0.795], "focus": [0.32, 0.005, 1.0, 0.085], "sfx": "typewriter"}]}]},
]

IA = "https://archive.org/download/"
NARA = "(public domain, via Internet Archive)"
STORY = {
 "priority": 10,
 "format": "story",
 "voice": "andrii",
 "intro_beats": True,
 "topic": "Douglas Kelley",
 "sources": ["Douglas Kelley", "Hermann Göring", "Nuremberg trials", "Gustave Gilbert", "Camp Ashcan", "Burton C. Andrus",
             "Robert Ley", "Rudolf Hess", "Nuremberg executions"],
 "title": "Göring and His Psychiatrist: Two Men Who Died of the Same Poison",
 "question": "Kelley found no Nazi illness, only ordinary men. Was he right?",
 "summary": ("In 1945 the U.S. Army sent the psychiatrist Douglas Kelley to look inside the minds of Hermann Göring and 21 "
             "other Nazi leaders. This is the story of the ink blots, the cells, the trial, the capsule nobody found, and "
             "of what happened to the man who studied them."),
 "tags": ["Hermann Göring", "Douglas Kelley", "Nuremberg trials", "Nuremberg", "psychiatrist", "Rorschach test",
          "Rudolf Hess", "Robert Ley", "Gustave Gilbert", "Burton Andrus", "Camp Ashcan", "Robert Jackson",
          "WW2 documentary", "World War 2", "history"],
 "pronounce": {"Göring's": "Gurr-ings", "Göring": "Gurr-ing", "Mondorf": "Mon-dorf", "Ley": "Lie", "Hjalmar Schacht": "Yal-mar Shahkt",
               "Streicher": "Stry-ker", "Gustave": "Goo-stahv", "Goldensohn": "Golden-sone", "Wheelis": "Wee-liss",
               "Stivers": "Sty-vers", "Andrus": "An-druss", "Luftwaffe": "Looft-vah-fuh", "Reich": "Rike",
               "Maxwell Fyfe": "Maxwell Fife", "San Quentin": "San Kwen-tin"},
 "films": {
  "kl_press": {"url": IA + "ADC-4363c/ADC-4363c.mov", "mono": True,
               "credit": "Hermann Göring press conference, Augsburg, 1945: US Army / NARA 111-ADC-4363 " + NARA},
  "kl_plea": {"url": IA + "ADC-9930/ADC-9930.mp4", "mono": True,
              "credit": "Nuremberg Trials, 21 November 1945: US Army / NARA 111-ADC-9930 " + NARA},
  "kl_await": {"url": IA + "ARC-39085/ARC-39085.mp4", "mono": True,
               "credit": "United Newsreel, October 1945: US Office of War Information / NARA ARC 39085 " + NARA},
  "kl_loot": {"url": IA + "1945-06-04_Allies_Sieze_German_Loot_and_Criminals/1945-06-04_Allies_Sieze_German_Loot_and_Criminals.mp4",
              "mono": True, "crop": "616:346:12:62", "credit": "Universal newsreel, 4 June 1945 " + NARA},
  "kl_sent": {"url": IA + "ADC-10005/ADC-10005.mp4", "mono": True,
              "credit": "Sentencing of Nazi Leaders at Nuremberg, 1946: US Army / NARA 111-ADC-10005 " + NARA},
  "kl_sent2": {"url": IA + "ADC-10018/ADC-10018.mp4", "mono": True,
               "credit": "Sentencing of Nazi War Leaders at Nuremberg, 1946: US Army / NARA 111-ADC-10018 " + NARA},
  "kl_dec": {"url": IA + "ADC-5604a/ADC-5604a.mov", "mono": True,
             "credit": "War Crimes Trials, Nuremberg, December 1945: US Army / NARA 111-ADC-5604 " + NARA},
  "kl_ruins": {"url": IA + "ADC-9996/ADC-9996.mp4", "mono": True,
               "credit": "Reich Ruins, September 1945: US Army / NARA 111-ADC-9996 " + NARA}},
 "period_audio": {
  "plea": {"file": "Goering plea Nuremberg 21 November 1945.mp3",   # only from period/ (the judge and the plea, 316-325 s of ADC-9930, the pause between them shortened)
           "url": IA + "ADC-9930/period_excerpt_is_in_the_repo",
           "speaker": "Hermann Göring", "date": "21 NOVEMBER 1945",
           "credit": "Hermann Göring pleads at Nuremberg, 21 November 1945: US Army film / NARA 111-ADC-9930 (public domain)",
           "text": "You must plead guilty or not guilty. Ich bekenne mich im Sinne der Anklage nicht schuldig."}},
 "pre": [{"dur": 2.8, "film": "kl_await", "from": 448.4, "to": 450.9, "stamp": ["OCTOBER 15", "1946"], "sfx": "low_rumble"}],
 "whole": [REPORT],
 "tone": [G_PORT, ANDRUS, KELLEY, LEY, STREICHER, HESS],
 "thumb": {"file": G_HESS2},
 "cover": {"file": G_DOCK, "x": 0.5, "y": 0.0, "zoom": 1.0, "color": False, "mono": True, "sizes": [120, 90],
           "text": ["GÖRING", "ONE POISON, TWO MEN"], "key": ["GÖRING"], "note": "Göring 1946, Kelley 1958: potassium cyanide"},
 "promos": [
  {"id": "kelley_findings", "chapter": 7,
   "sentences": ["A psychiatrist studies 22 Nazi leaders in their cells.",
                 "The whole world wants to know what made them monsters.",
                 "He comes home with the one answer that nobody wants: there was no Nazi illness."],
   "shots": [film(1, "kl_await", 438.7, 2.8), film(2, "kl_dec", 44.2, 4), pic(3, KELLEY, zoom=1.2, y=0.25)],
   "top": "INSIDE THE|NAZI MIND", "key": ["MIND"],
   "cta": {"kind": "redacted", "line": "WHAT HE FOUND WAS", "hidden": "NOTHING"}, "end": "WHAT DID HE FIND?",
   "name": "The Psychiatrist Who Studied 22 Nazi Leaders"},
  {"id": "kelley_capsule", "chapter": 9,
   "sentences": ["Hermann Göring is guarded day and night.",
                 "Two hours before his execution, he is dead.",
                 "In his last note, he says how long he had the poison: since his first day."],
   "shots": [film(1, "kl_await", 448.4, 2.5), film(2, "kl_press", 110.5, 4), film(3, "kl_await", 443, 3)],
   "top": "GÖRING'S|LAST SECRET", "key": ["GÖRING'S"],
   "cta": {"kind": "question"}, "end": "WHERE DID HE GET IT?",
   "name": "Göring's Last Secret at Nuremberg"}],
 "chapters": C,
}

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "kelley.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
