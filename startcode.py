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

# dit in een define voor herroep
# pick een random attractie uit lijst
def Rattr():
    global gek_attractie

    gek_attractie = random.choice(voorzieningen)

    print(gek_attractie)

Rattr()
# nu gaan we volgorde check alles met define doen!

# check 1, is leeftijd okay?
def check1():
    if (
        gek_attractie["attractie_min_leeftijd"] is None
        or bezoeker["leeftijd"] >= gek_attractie["attractie_min_leeftijd"]
    ):
        print("klopt! hij mag", bezoeker["leeftijd"], gek_attractie["attractie_min_leeftijd"])
        check2()
    else:
        print("nee")


# check 2, is lengte okay?
def check2():
    if (
        gek_attractie["attractie_min_lengte"] is None
        or bezoeker["lengte"] >= gek_attractie["attractie_min_lengte"] 
    ):
        print("klopt! hij mag")
        check3()
    else:
        print("nee")

# check 3, is gewicht okay?
def check3():
    if (
        gek_attractie["attractie_max_gewicht"] is None
        or bezoeker["gewicht"] <= gek_attractie["attractie_max_gewicht"] 
    ):
        print("klopt! hij mag", )
        check4()
    else:
        print("nee",bezoeker["gewicht"], gek_attractie["attractie_max_gewicht"])

# bekijk het voorwaarde van regenen. dit past toe op check5
def check4():
    global weervoorwaarde

    temperatuur = 15
    kans_op_regen = False

    if temperatuur >= 15 and kans_op_regen == False:
        print("jep, het gaat niet regenen")
        weervoorwaarde = "buiten"
    else:
        print("nee, gaat regenen dus binnenattracties")
        weervoorwaarde = "binnen"

    check5()

# check of gekozen(gek) binnen is en past bij attribuut van weervoorwaarde
def check5():
    if weervoorwaarde == "binnen":
        if gek_attractie["overdekt"] == 1:
            print("Ja, deze attractie past bij het weer")
        else:
            print("Nee, deze attractie is buiten")
    else:
        if gek_attractie["overdekt"] == 0:
            print("Ja, deze attractie past bij het weer")
        else:
            print("Nee, deze attractie is binnen")

check1()

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open('dagprogramma_bezoeker_x.json', 'w') as json_bestand_uitvoer:
    json.dump(dagprogramma, json_bestand_uitvoer, indent=4)