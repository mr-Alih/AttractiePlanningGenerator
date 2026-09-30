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
db = Database(host="localhost", gebruiker="root", wachtwoord="Hosseine@200", database="attractiepark_casus_a")
# altijd verbinding openen om query's uit te voeren
db.connect()

# -----------------------------------------
# Haal de eigenschappen op van een bezoeker
# -----------------------------------------
bezoeker_id = 1 # pas id aan om een andere bezoeker te selecteren

# aantal attracties
attr = 55

# SQL-query om alle gegevens van één bezoeker op te halen op basis van het ID.
select_query = f"SELECT * FROM bezoeker WHERE id = {bezoeker_id}"
resultaat = db.execute_query(select_query)

# haal de eerste rij uit het resultaat.
bezoeker = resultaat[0]

# voorbeeld van hoe je bij een eigenschap komt
print(bezoeker['naam']) 

# -----------------------------------------
# Haal alle voorzieningen op
# -----------------------------------------
# pas deze query aan en voeg queries toe om de juiste voorzieningen op te halen
select_query = "SELECT * FROM voorziening"
voorzieningen = db.execute_query(select_query)

# print de resultaten van de query op een overzichtelijke manier
pprint.pp(voorzieningen) 

# print de naam van de eerste voorziening
print(voorzieningen[0]["naam"])

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
        "kans_op_regen": 0
    }, 
    "voorzieningen": [], # STAP 2: Hier gaan we zo attracties/horeca toevoegen
    "totale_duur": 0
}

# pick een random attractie uit lijst
random_attractie = random.randint(0, attr)
gek_attractie = voorzieningen[random_attractie]
print(gek_attractie)

# check is waar betekent volgende if anders nieuwe attracit pickken

# check 1, is leeftijd okay?
if bezoeker["leeftijd"] > gek_attractie["attractie_min_leeftijd"]:
    print("klopt! hij mag", bezoeker["leeftijd"], gek_attractie["attractie_min_leeftijd"])
else:
    print("nee")

# check 2, is lengte okay?
if bezoeker["lengte"] > gek_attractie["attractie_min_lengte"]:
    print("klopt! hij mag")
else:
    print("nee")

# check 3, is gewicht okay?
if bezoeker["gewicht"] < gek_attractie["attractie_max_gewicht"] and gek_attractie["attractie_max_gewicht"] is not None:
    print("klopt! hij mag", )
elif gek_attractie["attractie_max_gewicht"] is None:
    print("klopt! hij mag", )
else:
    print("nee",bezoeker["gewicht"], gek_attractie["attractie_max_gewicht"])

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open('dagprogramma_bezoeker_x.json', 'w') as json_bestand_uitvoer:
    json.dump(dagprogramma, json_bestand_uitvoer, indent=4)