# import modulen
from pathlib import Path
import json
import pprint
from database_wrapper import Database
import random

# -----------------------------------------
# Database initialisatie en verbinden
# -----------------------------------------
# parameters voor connectie met de database
db = Database(host="localhost", gebruiker="root", wachtwoord="test", database="attractiepark_casus_a")
# altijd verbinding openen om query's uit te voeren
db.connect()

# -----------------------------------------
# Haal de eigenschappen op van een bezoeker
# -----------------------------------------
bezoeker_id = 2 # pas id aan om een andere bezoeker te selecteren


# SQL-query om alle gegevens van één bezoeker op te halen op basis van het ID.
select_query = f"SELECT * FROM bezoeker WHERE id = {bezoeker_id}"
resultaat = db.execute_query(select_query)

# haal de eerste rij uit het resultaat.
if not resultaat:
    print("Bezoeker niet gevonden")
    exit()
bezoeker = resultaat[0]

# voorbeeld van hoe je bij een eigenschap komt
print(bezoeker['naam']) 

# -----------------------------------------
# Haal alle voorzieningen op
# -----------------------------------------
# pas deze query aan en voeg queries toe om de juiste voorzieningen op te halen
select_query = "SELECT * FROM voorziening"
voorzieningen = db.execute_query(select_query)

attracties = []
horeca = []
winkels = []

for voorziening in voorzieningen:
    if voorziening["type"] in ["achtbaan", "water", "draaien", "familie", "simulator"]:
        attracties.append(voorziening)

    elif voorziening["type"] == "horeca":
        horeca.append(voorziening)

    elif voorziening["type"] == "winkel":
        winkels.append(voorziening)

# print de resultaten van de query op een overzichtelijke manier
# pprint.pp(voorzieningen) 

# altijd verbinding sluiten met de database als je klaar bent
db.close()

# verzamel alle benodigde gegevens in een dictionary
dagprogramma = {
    "bezoekersgegevens": {
        "naam": bezoeker['naam'],
        "verblijfsduur": bezoeker['verblijfsduur'],
        "leeftijd": bezoeker['leeftijd'],
        "lengte": bezoeker['lengte'],
        "gewicht": bezoeker['gewicht'],
        "voorkeuren_attractietypes": bezoeker['voorkeuren_attractietypes'].split(','),
        "lievelingsattracties": bezoeker['lievelingsattracties'].split(','),
        "voorkeuren_eten": bezoeker['voorkeuren_eten'].split(','),
        "rekening_houden_met_weer": bool(bezoeker['rekening_houden_met_weer'])
    },
    "weergegevens": {
        "temperatuur": 20,
        "kans_op_regen": False
    }, 
    "voorzieningen": [], # STAP 2: Hier gaan we zo attracties/horeca toevoegen
    "totale_duur": 0
}
voorkeuren = [v.strip() for v in dagprogramma["bezoekersgegevens"]["voorkeuren_attractietypes"]]
lievelingen = [l.strip() for l in dagprogramma["bezoekersgegevens"]["lievelingsattracties"]]

temperatuur = dagprogramma["weergegevens"]["temperatuur"]
kans_op_regen = dagprogramma["weergegevens"]["kans_op_regen"]
binnen_nodig = (
    dagprogramma["bezoekersgegevens"]["rekening_houden_met_weer"]
    and (temperatuur < 15 or kans_op_regen)
)

def mag_attractie(a):
    # alle checks in 1
    # is attractie bestaand?
    if a["actief"] != 1:
        return False
    # mag deze persoon zijn lengte
    if a["attractie_max_lengte"] is not None and bezoeker["lengte"] > a["attractie_max_lengte"]:
        return False
    # is hij oud genoeg
    if a["attractie_min_leeftijd"] is not None and bezoeker["leeftijd"] < a["attractie_min_leeftijd"]:
        return False
    # min
    if a["attractie_min_lengte"] is not None and bezoeker["lengte"] < a["attractie_min_lengte"]:
        return False
    # is zijn gewicht okay?
    if a["attractie_max_gewicht"] is not None and bezoeker["gewicht"] > a["attractie_max_gewicht"]:
        return False
    # BIJ EERDERE CHECK. WEATHER BINNEN boalean. nodig?
    if binnen_nodig and a["overdekt"] != 1:
        return False
    return True
# beter dan alles herthinken in function. want nu retruned hij opnieuw.

# simepele SWATCH/FLOP voor of hij wel lievelingen heeft en dan direct voorkeuren biedt
def prioriteit(a):
    if a["naam"] in lievelingen:
        return 0
    if a["type"] in voorkeuren:
        return 1
    return 2
# deze had ik geen idee hoe het moest. ik vroeeg een SWATCH maar FLIP werkte beter.
def kies_attracties():
    geschikt = [a for a in attracties if mag_attractie(a)]
    random.shuffle(geschikt)           # eerst husselen
    geschikt.sort(key=prioriteit)      # sort is stabiel: binnen een groep blijft het random
    over = bezoeker["verblijfsduur"]
    gekozen = []
    for a in geschikt:
        duur = a["geschatte_wachttijd"] + a["doorlooptijd"]
        if duur <= over:
            gekozen.append(a)
            over -= duur
    return gekozen
# RATTR function



# geneer
def genereer():
    programma = []

    # dobbellen
    attractie_programma = attr_potje.copy()
    random.shuffle(attractie_programma)

    # horeca zoeken bij voorkeur
    voorkeur_eten = dagprogramma["bezoekersgegevens"]["voorkeuren_eten"]
    passende_horeca = [
        h
        for h in horeca
        if h["productaanbod"] in voorkeur_eten
    ] 
    #dit is puur om een random te pakken.
    # FORCEFALLBACK
    # random
    if not passende_horeca:
        passende_horeca = horeca.copy()

    # einde souvenierwinkel
    if winkels:
        gekozen_winkel = random.choice(winkels)
    else:
        gekozen_winkel = None
        # forcefallback
    # jeyy HET WEKREKRTKITNO

    # horeca positie is eidne
    aantal_attracties = len(attractie_programma)
    horeca_posities = []
    aantal_attracties = len(attractie_programma)
    if aantal_attracties > 0:
        horeca_posities.append(max(1, aantal_attracties // 2))
        # max toegevoegd. fijner

    # FR 11 moet je bij meer dan 4 uur elke activieteit 2 uur . HORECA
    verblijfsduur = bezoeker["verblijfsduur"]
    if verblijfsduur > 240:
        extra_horeca_aantal = verblijfsduur //120
        for i in range (1, extra_horeca_aantal):
            positie = int(aantal_attracties * i / extra_horeca_aantal)
            # breinpein maar hij plaats het in midden.
            if positie not in horeca_posities:
                horeca_posities.append(positie)

    horeca_posities.sort()
    # eindsorting

    # nu maakt hij alles
    horeca_teller = 0

    for i, attractie in enumerate(attractie_programma):

        programma.append({
            "type": "attractie",
            "voorziening": attractie
        })

        # Maximaal 5 minuten lopen
        if i < len(attractie_programma) - 1:
            looptijd = random.randint(0, 5)

            programma.append({
                "type": "lopen",
                "duur": looptijd
            })

        # Horeca op juiste positie
        if (i + 1) in horeca_posities:

            if passende_horeca:
                horeca_keuze = random.choice(passende_horeca)
            else:
                horeca_keuze = None

            programma.append({
                "type": "horeca",
                "voorziening": horeca_keuze
            })

            programma.append({
                "type": "eetpauze",
                "duur": 15
            })

            horeca_teller += 1

    # souvenierwinkel erin
    if gekozen_winkel is not None:
        programma.append({
            "type": "winkel",
            "voorziening": gekozen_winkel
        })

    # laa
    dagprogramma["voorzieningen"] = programma
    print(programma)

attr_potje = kies_attracties()
genereer()

# maak de voorzieningen "plat" zodat de acceptatieomgeving ze snapt
# soort van convertie dat hij doet door 
# alles rewrite. 
schoon = []
totaal = 0
for s in dagprogramma["voorzieningen"]:
    if s["type"] == "lopen":
        totaal += s["duur"]          # telt mee in de tijd, maar komt niet in de JSON
        continue
    if s["type"] == "eetpauze":
        totaal += s["duur"]
        schoon.append(s)
        continue
    v = s["voorziening"]
    totaal += v["geschatte_wachttijd"] + v["doorlooptijd"]
    schoon.append({**v, "type": s["type"]})   # naam, wachttijd enz. direct in het item

dagprogramma["voorzieningen"] = schoon
dagprogramma["totale_duur"] = totaal
# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open('dagprogramma_bezoeker_x.json', 'w') as json_bestand_uitvoer:
    json.dump(dagprogramma, json_bestand_uitvoer, indent=4)

# extreme edit. dit komt doordat ik eerste alle stappen heb gepakt.
# nu heb ik alles aan elkaar geplakt met 1 groot BLOCK. 
# extreem fijn edit want ik begrijp precies elk block en kon leren 
# hoe dingen ging reageren.
# chatgpt zei dat ook paar calculation blockken niet werkte