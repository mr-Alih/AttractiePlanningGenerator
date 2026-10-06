# import modulen
from pathlib import Path
import json
import pprint
from database_wrapper import Database
import random
import openmeteo_requests
import requests_cache
from retry_requests import retry

# WRAPPER voor weather. DIT IS VAN WEATHER MATEOS
# API instellen
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 52.3702,
    "longitude": 5.2141,
    "current": ["temperature_2m", "rain"],
}

responses = openmeteo.weather_api(url, params=params)

response = responses[0]
current = response.Current()

temperatuur = current.Variables(0).Value()
regen = current.Variables(1).Value()

if regen > 0:
    hetweer = "rain"
else:
    hetweer = "goed weer"



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

# Alle attracties
select_query = """
SELECT *
FROM voorziening
WHERE type IN ('achtbaan', 'water', 'draaien', 'familie', 'simulator')
"""
attracties = db.execute_query(select_query)


# Alle horeca
select_query = """
SELECT *
FROM voorziening
WHERE type = 'horeca'
"""
horeca = db.execute_query(select_query)


# Alle winkels
select_query = """
SELECT *
FROM voorziening
WHERE type = 'winkel'
"""
winkels = db.execute_query(select_query)

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
        "temperatuur": round(int(temperatuur), 2), #2 decimalen opsturen!
        "kans_op_regen": hetweer 
    }, 
    "voorzieningen": [], 
    "totale_duur": 0
}
voorkeuren = [v.strip().lower() for v in dagprogramma["bezoekersgegevens"]["voorkeuren_attractietypes"]]
# minor bug fix. lower case omdat hij telkens family en cases niet reageerde
lievelingen = [l.strip() for l in dagprogramma["bezoekersgegevens"]["lievelingsattracties"]]

# temperatuur = temperatuur eerder via mateo
# kijken of het nodig is om binnenattracites te zoeken. 
# temp lager dan 15 is koud, binnen.
# weer slecht door mateo dan yep binnen.
binnen_nodig = (
    dagprogramma["bezoekersgegevens"]["rekening_houden_met_weer"]
    and (temperatuur < 15 or hetweer == "rain")
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
    v = bezoeker["verblijfsduur"]

    # tijd die al vastligt (worst case), dus die mag niet aan attracties opgaan
    # dit zijn de bufferzones ook eigenlijk. die wordt toegevoegd.
    # math eigenlijk maar telkens de helft en defaults
    aantal_horeca = v // 120 if v > 240 else 1
    langste_horeca = max((h["geschatte_wachttijd"] + h["doorlooptijd"] for h in horeca), default=0)
    langste_winkel = max((w["geschatte_wachttijd"] + w["doorlooptijd"] for w in winkels), default=0)
    reserve = aantal_horeca * (langste_horeca + 15 + 5) + langste_winkel + 5
    # moest veel editen want hij ging overschotten
    # slechste case. beetje point system.
    # nooit over tijd. 5 minuten lopen. 
    over = v - reserve

    geschikt = [a for a in attracties if mag_attractie(a)]
    random.shuffle(geschikt)
    geschikt.sort(key=prioriteit)

    # NIEUW: lievelingen 2x in de kandidatenlijst, voor de rest
    favorieten = [a for a in geschikt if a["naam"] in lievelingen]
    rest = [a for a in geschikt if a["naam"] not in lievelingen]
    kandidaten = favorieten + favorieten + rest

    gekozen = []
    for a in geschikt:
        duur = a["geschatte_wachttijd"] + a["doorlooptijd"] + 5   # +5 = worst case lopen
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
with open(f'dagprogramma_bezoeker_{bezoeker["id"]}.json', 'w') as json_bestand_uitvoer:
    json.dump(dagprogramma, json_bestand_uitvoer, indent=4)

# extreme edit. dit komt doordat ik eerste alle stappen heb gepakt.
# nu heb ik alles aan elkaar geplakt met 1 groot BLOCK. 
# extreem fijn edit want ik begrijp precies elk block en kon leren 
# hoe dingen ging reageren.
# chatgpt zei dat ook paar calculation blockken niet werkte

#pip install openmeteo-requests
# pip install requests-cache retry-requests numpy pandas