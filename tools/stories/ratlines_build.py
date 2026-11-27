"""The Ratlines, Nov 27 (Andrii, Nov 24: genre 3, trials and post-war secrets; Sat 28.11 02:00 London): a hand story in
the NEW FORMAT (CLAUDE.md, Nov 23): voice No. 3, one named person (Adolf Eichmann) from the SS camp to the glass booth,
the period voice = the Universal-International newsreel 'Guilty! Eichmann to Hang' (December 1961, Ed Herlihy: 'A man
who escaped the Nuremberg War Trials by fleeing to South America receives justice'; Andrii, Nov 26: 'так, бери
хроніку'), one open question (how does the man who ran the deportations get a Red Cross passport?).
Facts: the Wikipedia articles of STORY['sources'] (whole, sources/*.txt).
Films (public domain): Universal-International 'Trial of Century' (April 1961, Internet Archive) and 'Guilty! Eichmann
to Hang' (December 1961, Commons, PD-Universal Newsreel); Perón driving, 1953 (Commons, PD Argentina); ADC-9927 and the
1945/46 newsreels of the Kelley story (Nuremberg).
Run: python tools/stories/ratlines_build.py"""
import json, pathlib

IA = "https://archive.org/download/"
FP = "https://commons.wikimedia.org/wiki/Special:FilePath/"

E42 = "Adolf Eichmann, 1942 (cropped).jpg"
E39 = "Adolf Eichmann Zentralstelle Wien 1939.jpg"
ESS = "EichmannSSdoc.jpg"
ERC = "WP Eichmann Passport.jpg"
ERC2 = "Adolf Eichmann Red Cross photo.jpg"
EID = "Eichmann documento identità.jpg"
E60 = "Adolf Eichmann 1960.jpg"
EORDER = "The first imprisonment order of Adolf Eichmann 1960-05-23.jpg"
EJUDGES = "Eichmann voor de rechters, Bestanddeelnr 912-2014.jpg"
ERAMLE = "Adolf Eichman in Ramle Prison1961.jpg"
EYARD = "Flickr - Government Press Office (GPO) - Nazi war criminal Adolf Eichmann walking in yard of his cell in Ramle prison.jpg"
EBOOTH = "Adolf Eichmann at Trial1961.jpg"
ETRIAL = "Eichman Trial1961.jpg"
ESENT = "Adolf Eichmann is sentenced to death at the conclusion of the Eichmann Trial USHMM 65289.jpg"
EASHES = "Eichmann ashes scattered at sea.jpg"
JUDGES = "Eichman Trial judges.jpg"
BACH = "Gavriel Bach at Eichman trial.jpg"
SERVATIUS = "Robert Servatius1961.jpg"
ARENDT = "Arendt in Jerusalem during Adolf Eichmann trial.jpg"
BEITHAAM = "Beit HaAm on Jaffa Road (Derech Yafo), Jerusalem. 1948 (id.15297513).jpg"
APPEAL = "Flickr - Government Press Office (GPO) - The appeal of Nazi war criminal Adolf Eichmann.jpg"
TEAM = "David Ben-Gurion and the participants in the operation to capture Adolf Eichmann.jpg"
MALKIN = "Питер Малкин 1960.jpg"
BG60 = "David Ben-Gurion (D597-087).jpg"
HAREL = "Isser Harel.jpg"
BRITANNIA = "El Al Bristol Britannia and Alouette II.jpg"
HUDAL = "Alois Hudal Santa Maria dell'Anima ca 1940.jpg"
MENGELE56 = "WP Josef Mengele 1956.jpg"
MENGELE_PASS = "Mengele2.jpg"
STANGL = "Franz Paul Stangl.jpg"
BARBIE = "Klaus Barbie in uniform.jpg"
ALTMANN = "Altmann Lima.jpg"
PRIEBKE_RC = "Erich Priebke Red Cross photo.png"
WIESENTHAL = "Simon Wiesenthal (1940-1945).jpg"
PERON_BALC = "Perón y Evita desde el balcón saludan a la multitud.jpg"
PERON_CROWD = "Perón se dirige a la multitud.jpg"
PERON_HORSE = "Perón montado a caballo.jpg"
PERON_RACING = "Juan Domingo Perón en el estadio de Racing Club.jpg"
SKORZENY = "Otto Skorzeny y Peron.jpg"
CORRIENTES = "Avenida Corrientes y Esmeralda 1950.jpg"
ALEM = "Av leandro alem bs as 1950s.jpg"
TROLEBUS = "Trolebus en av las heras y facultad derecho 1950.jpg"
GENOA1 = "Haven van Genua en de omliggende bebouwing vooraan links het schip de Kedmah, Bestanddeelnr 255-0217.jpg"
GENOA2 = "Haven van Genua en de omliggende bebouwing, Bestanddeelnr 255-0216.jpg"
PIUS = "The Infallible (Pope Pius XII) – Sept. 1945.jpg"
POSTERS = "Aanplakbiljetten over de veroordeling van Karl Adolf Eichmann, Bestanddeelnr 255-1849.jpg"
KIOSK = "Joodse jongemannen met keppeltjes staan voor een kiosk en houden een krant met d, Bestanddeelnr 255-1844.jpg"

H_SRC = "ED HERLIHY · UNIVERSAL-INTERNATIONAL NEWS, DECEMBER 1961 · 'GUILTY! EICHMANN TO HANG'"

M_ROUTE = {"places": [{"label": "LÜNEBURG HEATH", "lat": 53.1, "lon": 10.2, "side": "red"},
                      {"label": "GENOA", "lat": 44.41, "lon": 8.93, "side": "red"},
                      {"label": "BUENOS AIRES", "lat": -34.6, "lon": -58.4, "side": "red"}],
           "routes": [[0, 1, "red", 0.1], [1, 2, "red", 0.25]], "pad": 4}
M_FLIGHT = {"places": [{"label": "BUENOS AIRES", "lat": -34.6, "lon": -58.4, "side": "blue"},
                       {"label": "DAKAR", "lat": 14.7, "lon": -17.45, "side": "blue"},
                       {"label": "ISRAEL", "lat": 32.0, "lon": 34.9, "side": "blue"}],
            "routes": [[0, 1, "blue", 0.2], [1, 2, "blue", 0.15]], "pad": 4}


def film(s, key, x, n=4, **k):
    return {"s": s, "film": key, "from": x, "to": x + n, **k}


def pic(s, f, **k):
    return {"s": s, "file": f, **k}


def beat(after, *shots):
    return {"after": after, "shots": [{"dur": d, "film": f, "from": x, "to": x + d, **({"sfx": s} if s else {})}
                                      for d, f, x, s in shots]}


C = [
 {"title": "", "mode": "people", "sentences": [
  "On 11 April 1961, in Jerusalem, the man in the bulletproof glass booth is Adolf Eichmann.",
  "As many as 9,000 Nazi war criminals and their collaborators reportedly escaped to South America.",
  "Eichmann was one of them, and for ten years he lived in Argentina as Ricardo Klement.",
  "So how does the man who ran the deportations of the Jews get a passport from the Red Cross?",
  "It all begins in an American camp, under a false name."],
  "shots": [
   film(1, "rl_trial", 14, 3.5, stamp=["JERUSALEM"]),
   film(1, "rl_trial", 92, 3),
   film(2, "rl_trial", 9, 3, note="9,000 ESCAPED"),
   pic(2, GENOA1, label="GENOA · 1948"),
   pic(3, E42, reveal=[0.62, 0.25], name="ADOLF EICHMANN", role="SS OFFICER"),
   pic(3, EID, card=True, note="RICARDO KLEMENT"),
   film(4, "rl_verdict", 36, 4),
   film(5, "rl_trial", 48, 4)],
  "beats": [{"after": 1, "audio": {"src": "herlihy", "from": 57.05, "to": 66.0}, "source": H_SRC, "shots": [
   {"dur": 5.0, "film": "rl_verdict", "from": 52, "to": 57, "source": H_SRC},
   {"dur": 4.6, "film": "rl_verdict", "from": 65, "to": 69.6, "source": H_SRC}]}]},

 {"title": "Otto Eckmann", "mode": "people", "stamp": ["1945"], "sentences": [
  "But in 1945, when the war ends, Eichmann is captured by the Americans, and they do not know who he is.",
  "He has forged papers in the name of Otto Eckmann.",
  "He is moved through several camps for SS officers.",
  "When he realises that his identity has been discovered, he escapes from a work detail at Cham, in Germany.",
  "Now he is Otto Heninger, and he keeps moving.",
  "He ends up on the Lüneburg Heath, working in the forests.",
  "Later he leases a small plot of land, and he stays there until 1950.",
  "Meanwhile, at Nuremberg, the former commandant of Auschwitz, Rudolf Höss, gives damning evidence about him.",
  "The man they are talking about is living on his small plot of land, under another name."],
  "shots": [
   film(1, "kl_ruins", 221, 4),
   film(2, "kl_await", 420, 4, note="OTTO ECKMANN"),
   film(3, "menace", 72, 4),
   pic(4, E39, card=True, label="EICHMANN'S OFFICE · VIENNA 1939"),
   film(5, "menace", 48, 4, note="OTTO HENINGER"),
   film(6, "kl_await", 409, 3),
   film(7, "kl_ruins", 290, 4),
   film(8, "kl_sent", 40, 4, label="NUREMBERG · 1946"),
   film(9, "kl_await", 377, 4)]},

 {"title": "The Bishop", "mode": "people", "stamp": ["ROME"], "sentences": [
  "But in Rome, there is a bishop who wants to help men like him.",
  "Alois Hudal is an Austrian, the rector of a seminary for German priests, and a Nazi sympathiser.",
  "In December 1944, the Allies let the Vatican send a representative to the German-speaking internees in Italy.",
  "The job goes to Hudal.",
  "He uses it to help wanted war criminals escape.",
  "Among them are Franz Stangl, the commandant of Treblinka, Erich Priebke, and Adolf Eichmann.",
  "The Rome office of the Red Cross gives refugees travel documents, and in South America they are accepted as passports.",
  "Hudal can get the blank forms.",
  "In some cases, the signature of the Red Cross official is forged.",
  "In 1948 he writes to the President of Argentina, Juan Perón, and asks for 5,000 visas."],
  "shots": [
   pic(1, PIUS, label="ROME · 1945"),
   pic(2, HUDAL, card=True, name="ALOIS HUDAL", role="BISHOP, ROME"),
   film(3, "menace", 52, 4),
   film(4, "kl_ruins", 573, 4),
   film(5, "menace", 76, 4),
   pic(6, STANGL, name="FRANZ STANGL", role="COMMANDANT, TREBLINKA"),
   pic(6, PRIEBKE_RC, card=True),
   pic(7, ERC2, card=True),
   film(8, "kl_ruins", 300, 4),
   film(9, "kl_await", 432, 4),
   pic(10, PERON_BALC, note="5,000 VISAS")],
  "beats": [{"after": 5, "quote": {
    "text": "I thank God that He [allowed me] to visit and comfort many victims in their prisons and concentration camps and to help them escape with false identity papers.",
    "name": "ALOIS HUDAL", "role": "BISHOP, IN HIS MEMOIRS"},
   "shots": [{"dur": 5.0, "film": "kl_await", "from": 425, "to": 430}, {"dur": 5.0, "film": "kl_await", "from": 465, "to": 470}]}]},

 {"title": "The Franciscans", "mode": "people", "stamp": ["SAN GIROLAMO"], "sentences": [
  "But Hudal is not the only one: a second network works from San Girolamo, a Croatian seminary in Rome.",
  "It is run by a Croatian priest, Father Krunoslav Draganović.",
  "At first it helps the Croatian Ustaše, and their leader, Ante Pavelić.",
  "When a group is ready, Draganović phones a monsignor in Genoa with the number of berths needed on ships to South America.",
  "It is an open secret in Rome.",
  "In February 1947, an American agent reports that ten members of Pavelić's cabinet live in San Girolamo or in the Vatican itself.",
  "The Americans are using the ratlines too.",
  "Their Counterintelligence Corps shelters Klaus Barbie, the Gestapo chief known as the Butcher of Lyon.",
  "Barbie gives them information, and in 1951 he flees to Bolivia with American help."],
  "shots": [
   film(1, "kl_ruins", 300, 4),
   film(2, "kl_ruins", 104.5, 4, note="KRUNOSLAV DRAGANOVIĆ"),
   film(3, "kl_ruins", 557, 4),
   pic(4, GENOA1, zoom=1.5, x=0.35, y=0.6, label="GENOA"),
   pic(5, PIUS, zoom=1.4, x=0.5, y=0.3),
   film(6, "kl_ruins", 385, 4, note="10 MINISTERS"),
   film(7, "kl_sent", 292, 4),
   pic(8, BARBIE, reveal=[0.6, 0.25], name="KLAUS BARBIE", role="GESTAPO CHIEF, LYON"),
   pic(9, ALTMANN, label="BARBIE AS 'KLAUS ALTMANN'")]},

 {"title": "Perón's Argentina", "mode": "people", "stamp": ["BUENOS AIRES"], "sentences": [
  "But the last stop is Buenos Aires, where Juan Perón is in power.",
  "Already in May 1943, the SS officer Walter Schellenberg made a secret agreement with the Argentine military: Nazis would not be arrested in Argentina.",
  "Perón's immigration commissioner is an avowed anti-Semite, and his intelligence chief is the son of a Nazi supporter.",
  "They help European war criminals on their way to citizenship.",
  "As many as 5,000 escape to Argentina.",
  "Perón will later say that he helped as many Nazi officials as he could.",
  "For him, the Nuremberg trials are a disgrace.",
  "In July 1949, Josef Mengele, the doctor of Auschwitz, sails from Genoa with a passport as Helmut Gregor.",
  "A year later, it is Eichmann's turn."],
  "shots": [
   film(1, "rl_peron", 6, 5, label="JUAN PERÓN · 1953"),
   pic(2, SKORZENY),
   pic(3, PERON_CROWD),
   pic(4, CORRIENTES, label="BUENOS AIRES · 1950S"),
   pic(5, ALEM, note="5,000"),
   pic(6, PERON_HORSE, name="JUAN PERÓN", role="PRESIDENT OF ARGENTINA"),
   pic(7, PERON_RACING),
   pic(8, MENGELE_PASS, card=True, name="JOSEF MENGELE", role="SS DOCTOR, AUSCHWITZ"),
   pic(9, TROLEBUS)]},

 {"title": "Ricardo Klement", "mode": "action", "stamp": ["17 JUNE 1950"], "sentences": [
  "But first he needs papers, and in 1948, through Hudal's organisation, he gets a landing permit for Argentina.",
  "The name on it is Ricardo Klement.",
  "With it, he gets a Red Cross passport.",
  "He crosses Europe, staying in monasteries that serve as safe houses.",
  "On 17 June 1950, he sails from Genoa.",
  "On 14 July, he arrives in Buenos Aires.",
  "He first works for a government contractor in the province of Tucumán.",
  "In 1952, his family joins him.",
  "He holds a series of low-paid jobs, and then he finds work at Mercedes-Benz, where he rises to department head.",
  "The family builds a house at 14 Garibaldi Street, and they move in during 1960.",
  "In 1956, he gives long interviews to a Nazi journalist, Willem Sassen.",
  "He admits that he knew that millions of Jews and others were being killed."],
  "shots": [
   pic(1, ERC, label="RED CROSS PASSPORT · 1950"),
   pic(2, ERC, zoom=1.8, x=0.5, y=0.2, note="RICARDO KLEMENT"),
   pic(3, ERC2, card=True),
   film(4, "kl_ruins", 450, 4),
   pic(5, GENOA2, label="GENOA · 1948"),
   {"s": 6, "map": M_ROUTE},
   pic(7, ALEM, zoom=1.5, x=0.4, y=0.6),
   pic(8, CORRIENTES, zoom=1.5, x=0.6, y=0.5),
   pic(9, EID, card=True, label="HIS ARGENTINE ID"),
   film(10, "rl_peron", 12, 3),
   film(11, "rl_peron", 15, 3),
   pic(12, E60)],
  "beats": [{"after": 11, "quote": {
    "text": "I didn't care about the Jews deported to Auschwitz, whether they lived or died.",
    "name": "ADOLF EICHMANN", "role": "TO WILLEM SASSEN, 1956"},
   "shots": [{"dur": 5.0, "file": E42, "zoom": 1.4, "y": 0.3}]}]},

 {"title": "The Daughter", "mode": "people", "stamp": ["1956"], "sentences": [
  "But in 1956, the daughter of Lothar Hermann, a German Jew in Argentina, begins dating a young man named Klaus Eichmann.",
  "Klaus boasts about his father's Nazi past.",
  "Sylvia Hermann goes to the house, and a man opens the door who says he is Klaus's uncle.",
  "Then Klaus arrives, and calls him: Father.",
  "Lothar Hermann writes to Fritz Bauer, a West German prosecutor.",
  "Bauer does not trust the German police, and in 1957 he tells the head of Mossad, Isser Harel.",
  "When Bauer asks the West German government to request his extradition, it refuses.",
  "The Nazi hunter Simon Wiesenthal has heard the same thing: Eichmann is in Buenos Aires.",
  "There are no recent photos of Eichmann, so Wiesenthal has detectives photograph his brother Otto, who looks like him.",
  "On 1 March 1960, an Israeli interrogator, Zvi Aharoni, arrives in Buenos Aires.",
  "After several weeks, he confirms it.",
  "Argentina has always refused to send Nazis back for trial.",
  "So the Prime Minister of Israel, David Ben-Gurion, decides that Eichmann must be captured."],
  "shots": [
   pic(1, PERON_BALC, zoom=1.5, x=0.5, y=0.5, label="BUENOS AIRES"),
   pic(2, ERAMLE, zoom=1.5, x=0.5, y=0.25),
   film(3, "kl_await", 401, 4),
   pic(4, E60, zoom=1.8, x=0.5, y=0.25, note="FATHER"),
   film(5, "kl_sent", 300, 4),
   pic(6, HAREL, reveal=[0.6, 0.25], name="ISSER HAREL", role="HEAD OF MOSSAD"),
   film(7, "kl_sent", 330, 4),
   pic(8, WIESENTHAL, name="SIMON WIESENTHAL", role="NAZI HUNTER"),
   film(9, "kl_await", 405, 4),
   film(10, "rl_peron", 0, 4, stamp=["1 MARCH 1960"]),
   film(11, "kl_await", 437, 4),
   film(12, "rl_peron", 22, 4),
   pic(13, BG60, reveal=[0.6, 0.25], name="DAVID BEN-GURION", role="PRIME MINISTER OF ISRAEL")]},

 {"title": "Garibaldi Street", "mode": "action", "stamp": ["11 MAY 1960"], "sentences": [
  "But on 11 May 1960, the eight-man team is waiting near Garibaldi Street, in San Fernando.",
  "For days they have watched him come home by bus at the same time every evening.",
  "To be sure, they compared the shape of his ears with the photos in his SS file.",
  "That evening, he is not on his usual bus.",
  "Half an hour later, he gets off another one.",
  "Peter Malkin asks him, in Spanish, if he has a moment.",
  "Eichmann tries to get away, two more agents come, and they wrestle him into a car, under a blanket.",
  "For nine days he is held in a safe house.",
  "Harel also tries to find Josef Mengele, to bring him back on the same flight, but Mengele has already moved.",
  "On 20 May, near midnight, a Mossad anaesthetist sedates him.",
  "The team has made him a fake Israeli passport and an El Al card, in the name of Zeev Zichroni.",
  "The El Al Britannia takes off, refuels in Dakar, and on 22 May it lands in Israel.",
  "The next afternoon, Ben-Gurion tells the Knesset.",
  "Argentina takes the case to the United Nations Security Council, and in June the Council agrees that its sovereignty was violated."],
  "shots": [
   pic(1, TEAM, label="THE CAPTURE TEAM"),
   film(2, "rl_peron", 26, 4),
   pic(3, ESS, zoom=1.4, note="THE EARS"),
   pic(4, TROLEBUS, zoom=1.8, x=0.6, y=0.6),
   film(5, "rl_peron", 18, 3),
   pic(6, MALKIN, reveal=[0.6, 0.25], name="PETER MALKIN", role="MOSSAD AGENT"),
   pic(7, TEAM, zoom=1.5, x=0.5, y=0.4),
   pic(8, EYARD, zoom=1.3, x=0.5, y=0.3),
   pic(9, MENGELE56, zoom=1.3, x=0.5, y=0.4),
   pic(10, BRITANNIA, label="EL AL BRITANNIA"),
   pic(11, BRITANNIA, zoom=1.6, x=0.4, y=0.5, note="ZEEV ZICHRONI"),
   {"s": 12, "map": M_FLIGHT},
   pic(13, EORDER, card=True),
   pic(14, KIOSK, label="TEL AVIV")],
  "beats": [beat(7, (3.0, "rl_peron", 16, None), (3.0, "rl_peron", 28, None))]},

 {"title": "The Glass Booth", "mode": "people", "stamp": ["JERUSALEM"], "sentences": [
  "But it is in Jerusalem that the world finally sees his face, and the trial begins on 11 April 1961.",
  "It is held in a hall called Beit Ha'am, and he sits inside a bulletproof glass booth.",
  "Before the trial, a police officer, Avner Less, questions him every day for months, and the transcripts run to over 3,500 pages.",
  "Less notes that he shows no remorse.",
  "The prosecutor is Gideon Hausner, the Attorney General of Israel.",
  "For 56 days, the prosecution presents its case, with 112 witnesses, many of them Holocaust survivors.",
  "Eichmann says he had no choice: he was only following orders.",
  "Hausner reads out what Eichmann said in 1945, that he would leap into his grave laughing.",
  "Eichmann says he meant enemies of the Reich.",
  "Later, before the judges, he admits that he meant the Jews.",
  "The writer Hannah Arendt watches him, and calls what she sees the banality of evil.",
  "On 15 December 1961, he is sentenced to death.",
  "His appeal fails, and he is hanged a few minutes after midnight, on 1 June 1962.",
  "His last words are reported to be: Long live Germany. Long live Argentina. Long live Austria.",
  "His ashes are scattered in the Mediterranean Sea."],
  "shots": [
   pic(1, BEITHAAM, label="BEIT HA'AM · JERUSALEM"),
   film(2, "rl_trial", 14, 4),
   pic(3, ERAMLE, label="PRISON · 1961"),
   pic(4, EYARD),
   film(5, "rl_trial", 73, 4, label="GIDEON HAUSNER"),
   film(6, "rl_trial", 79, 4, note="112 WITNESSES"),
   film(7, "rl_trial", 32, 4),
   film(8, "rl_verdict", 61, 4),
   film(9, "rl_trial", 83, 4),
   pic(10, JUDGES),
   pic(11, ARENDT, name="HANNAH ARENDT", role="WRITER"),
   film(12, "rl_verdict", 52.5, 3, stamp=["15 DECEMBER 1961"]),
   pic(12, ESENT),
   pic(13, APPEAL),
   film(14, "rl_verdict", 66, 4),
   pic(15, EASHES, card=True)],
  "beats": [beat(10, (3.0, "rl_verdict", 28, None), (3.0, "rl_verdict", 37, None))]},

 {"title": "The Others", "mode": "people", "stamp": ["THE OTHERS"], "sentences": [
  "But for the others, justice is late, or it never comes.",
  "Franz Stangl works at Volkswagen in Brazil until 1967, and he is sentenced to life in 1970.",
  "Klaus Barbie is sent to France in 1983, and dies in prison in Lyon.",
  "Erich Priebke lives in Argentina for almost 50 years, until an American TV team finds him in 1994.",
  "Bishop Hudal is forced to resign in 1952.",
  "Josef Mengele moves to Paraguay, and then to Brazil.",
  "In 1979 he drowns off the coast at Bertioga, and he is buried under a false name.",
  "He is never tried.",
  "Documents released in 2006 show that the CIA and West German intelligence had known for years where Eichmann was.",
  "They did not act.",
  "The ratlines were built so that these men could disappear, and for years, they did."],
  "shots": [
   film(1, "rl_verdict", 5, 3),
   pic(2, STANGL, zoom=1.4, x=0.5, y=0.3, label="FRANZ STANGL"),
   pic(3, ALTMANN, zoom=1.4),
   pic(4, PRIEBKE_RC, zoom=1.3, label="ERICH PRIEBKE AS 'OTTO PAPE'"),
   pic(5, HUDAL, card=True),
   pic(6, MENGELE56, name="JOSEF MENGELE", role="ARGENTINE ID, 1956"),
   pic(7, MENGELE_PASS, zoom=1.5, x=0.5, y=0.5),
   film(8, "rl_verdict", 6, 3, note="NEVER TRIED"),
   pic(9, POSTERS),
   film(10, "kl_sent", 340, 4),
   film(11, "rl_trial", 100, 5)]},
]

STORY = {
 "priority": 10,
 "format": "story",
 "voice": "andrii",
 "intro_beats": True,
 "topic": "Ratlines (World War II)",
 "sources": ["Ratlines (World War II)", "Adolf Eichmann", "Alois Hudal", "Krunoslav Draganović",
             "Adolf Eichmann's capture", "Eichmann trial", "Franz Stangl", "Josef Mengele", "Klaus Barbie",
             "Erich Priebke"],
 "title": "The Ratlines: How Adolf Eichmann Escaped to Argentina, and How He Was Caught",
 "question": "The CIA and West Germany knew where Eichmann was and did nothing. Should they have been held to account?",
 "summary": ("After 1945, thousands of Nazi war criminals escaped to South America along the ratlines, helped by a bishop "
             "in Rome, Croatian priests, forged Red Cross papers and Perón's Argentina. This is the story of Adolf "
             "Eichmann: from an American camp under a false name to Genoa, ten years as Ricardo Klement in Buenos Aires, "
             "the Mossad capture on Garibaldi Street and the glass booth in Jerusalem."),
 "tags": ["Ratlines", "Adolf Eichmann", "Eichmann trial", "Ricardo Klement", "Mossad", "Alois Hudal", "Perón",
          "Josef Mengele", "Klaus Barbie", "Nazi escape", "Argentina", "post-war secrets", "WW2 documentary",
          "World War 2", "history"],
 "pronounce": {"Eichmann": "Ike-man", "Eckmann": "Eck-man", "Heninger": "Hen-ing-er", "Lüneburg": "Loo-neh-burg",
               "Höss": "Hurss", "Hudal": "Hoo-dahl", "Stangl": "Shtang-gle", "Priebke": "Preeb-keh",
               "Draganović": "Dra-gah-no-vitch", "Ustaše": "Oo-sta-sheh", "Pavelić": "Pa-veh-litch",
               "San Girolamo": "San Jee-roh-la-mo", "Perón": "Peh-rone", "Mengele": "Meng-eh-leh",
               "Klement": "Kleh-ment", "Tucumán": "Too-koo-mahn", "Sassen": "Sass-en", "Hermann": "Hair-mahn",
               "Bauer": "Bow-er", "Harel": "Ha-rel", "Aharoni": "A-ha-ro-nee", "Ben-Gurion": "Ben Goo-ree-on",
               "Garibaldi": "Gah-ree-bahl-dee", "Malkin": "Mal-kin", "Zeev Zichroni": "Zeh-ev Zick-ro-nee",
               "Knesset": "Kness-et", "Beit Ha'am": "Bait Ha-ahm", "Hausner": "Howss-ner", "Bertioga": "Bair-tee-oh-ga",
               "Barbie": "Bar-bee", "Cham": "Kahm", "Treblinka": "Treh-blink-a", "Wiesenthal": "Vee-zen-tahl",
               "Mossad": "Mo-sahd", "Reich": "Rike"},
 "films": {
  "rl_trial": {"url": IA + "1961-04-13_Eichmann_trial/1961-04-13_Eichmann_trial.mpeg", "mono": True,
               "crop": "720:405:0:37",
               "credit": "Trial of Century: Eichmann Tried for War Crimes (April 1961): Universal-International News (public domain, via Internet Archive)"},
  "rl_verdict": {"url": FP + "1961-04-13_Tale_Of_Century_-_Eichmann_Tried_For_War_Crimes.ogv", "mono": True,
                 "crop": "392:220:0:28",
                 "credit": "Guilty! Eichmann to Hang (December 1961): Universal-International News / NARA (Wikimedia Commons, public domain)"},
  "rl_peron": {"url": FP + "El_Presidente_de_la_Naci%C3%B3n_Juan_D._Per%C3%B3n_manejando_un_autom%C3%B3vil_INSTITEC_Justicialista_Sport._A%C3%B1o_1953.webm",
               "crop": "477:268:81:96",
               "credit": "President Juan D. Perón driving the Justicialista Sport, 1953 (Wikimedia Commons, public domain in Argentina)"},
  "kl_ruins": {"url": IA + "placeholder", "credit": "see the Kelley story"},
  "kl_sent": {"url": IA + "placeholder", "credit": "see the Kelley story"},
  "kl_await": {"url": IA + "placeholder", "credit": "see the Kelley story"},
  "menace": {"url": IA + "1945-05-17_U-Boat_Menace_Ended/1945-05-17_U-Boat_Menace_Ended.mpeg", "mono": True,
             "crop": "688:344:16:68", "credit": "U-Boat Menace Ended (17 May 1945): Universal Newsreel (public domain, via Internet Archive)"}},
 "period_audio": {
  "herlihy": {"file": "Herlihy Guilty Eichmann to Hang 1961.mp3",
              "url": FP + "1961-04-13_Tale_Of_Century_-_Eichmann_Tried_For_War_Crimes.ogv",
              "speaker": "Ed Herlihy", "date": "DECEMBER 1961",
              "credit": "Guilty! Eichmann to Hang (December 1961), voice Ed Herlihy: Universal-International News / NARA (Wikimedia Commons, public domain)",
              "text": "A man who escaped the Nuremberg War Trials by fleeing to South America receives justice at the hands of the people whom he had aimed to wipe out."}},
 "pre": [{"dur": 2.8, "film": "rl_trial", "from": 31, "to": 34, "stamp": ["APRIL 11", "1961"], "sfx": "cinematic-drum-big"}],
 "whole": [ERC, EID, ESS, EORDER, EASHES, MENGELE_PASS, ERC2, PRIEBKE_RC, HUDAL, E39],
 "tone": [E42, STANGL, BARBIE, HAREL, MALKIN, BG60, WIESENTHAL, MENGELE56, PERON_HORSE],
 "thumb": {"file": EBOOTH},
 "cover": {"file": EBOOTH, "x": 0.5, "y": 0.4, "zoom": 1.0, "color": False, "mono": True, "sizes": [120, 90],
           "text": ["EICHMANN", "THE RED CROSS PASSPORT"], "key": ["EICHMANN"],
           "note": "he left Europe with a Red Cross passport as Ricardo Klement"},
 "promos": [
  {"id": "ratlines_ears", "chapter": 7,
   "sentences": ["Ricardo Klement comes home by the same bus every evening.",
                 "Israeli agents are watching.",
                 "To be sure, they compare one thing with his SS file: the shape of his ears."],
   "shots": [film(1, "rl_peron", 26, 4), pic(2, TEAM), pic(3, ESS, zoom=1.4)],
   "top": "HOW MOSSAD|FOUND EICHMANN", "key": ["EICHMANN"],
   "cta": {"kind": "redacted", "line": "THEY COMPARED HIS", "hidden": "EARS"}, "end": "WHAT DID THEY COMPARE?",
   "name": "How Mossad Made Sure It Was Eichmann"},
  {"id": "ratlines_bishop", "chapter": 2,
   "sentences": ["In 1948, a bishop in Rome writes to the President of Argentina.",
                 "He helps wanted Nazis escape with Red Cross papers.",
                 "And now he asks Juan Perón for one thing: five thousand visas."],
   "shots": [pic(1, HUDAL), pic(2, ERC2, card=True), pic(3, PERON_BALC)],
   "top": "THE BISHOP|OF THE RATLINES", "key": ["RATLINES"],
   "cta": {"kind": "number", "big": "5,000", "line": "VISAS. FOR WHOM?"}, "end": "FOR WHOM?",
   "name": "The Bishop Who Asked Perón for 5,000 Visas"}],
 "chapters": C,
}

# the Kelley story's Nuremberg films (same keys, same files in work/films)
kelley = json.loads((pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "kelley.json").read_text(encoding="utf-8"))
for k in ("kl_ruins", "kl_sent", "kl_await"):
    STORY["films"][k] = kelley["films"][k]

out = pathlib.Path(__file__).resolve().parents[2] / "stories" / "long" / "ratlines.json"
out.write_bytes((json.dumps(STORY, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
words = sum(len(s.split()) for c in C for s in c["sentences"])
print(out, "| chapters", len(C), "| sentences", sum(len(c["sentences"]) for c in C), "| words", words)
