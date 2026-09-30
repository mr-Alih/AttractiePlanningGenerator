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
        "kans_op_regen": False
    }, 
    "voorzieningen": voorziening["voorziening"], # STAP 2: Hier gaan we zo attracties/horeca toevoegen
    "totale_duur": 0
}
# doorlooptijd plus wachtijd en overgebleven duur
duurover = bezoeker["verblijfsduur"]
totaal_tijd = 0

# potje van alle attracties die passen
attr_potje = []

# dit in een define voor herroep
# pick een random attractie uit lijst
def Rattr():
    global gek_attractie

    gek_attractie = random.choice(attracties)

    print(gek_attractie)

Rattr()
# nu gaan we volgorde check alles met define doen!
def voegtoe():
    if attr_potje:
        # lijst bestaat. FORCEFALLBACK
        attr_potje = gek_attractie


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

    temperatuur = dagprogramma["weergegevens"]["temperatuur"]
    kans_op_regen = dagprogramma["weergegevens"]["kans_op_regen"]

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
            check6()
        else:
            print("Nee, deze attractie is buiten")
    else:
        print("geen slecht weer alles mag!")

# lievelingsattractie moet 2 maal
def check6():
    if bezoeker["lievelingsattracties"] is not None:
        # dus bezoeker heeft lievelingsattractie en nu is die gekozen het wel?
        if gek_attractie["naam"] == bezoeker["lievelingsattracties"]:
            # yep 2 maal
            return()
        else:
            # okay het is niet gelijk dus 1. return
            check7()
    else:
        # direct skippen. return
        check7()

def check7():
    global duur
    global duurover

    duur = gek_attractie["geschatte_wachtijd"] + gek_attractie["doorlooptijd"]

    # de check
    if duurover >= duur:
        duurover = duurover-duur
        # check of er meer kan of niet
        if duurover <= 0:
            # dit is laatste dus direct naar maken
            voegtoe()
            # genereer()
        else:
            counter +=1
            voegtoe()
            # tel op. als we alle attr zijn geweest dan stop + klaar
    # else:
        # niet toevoegen wel genereer
        # genereer()
        



check1()

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open('dagprogramma_bezoeker_x.json', 'w') as json_bestand_uitvoer:
    json.dump(dagprogramma, json_bestand_uitvoer, indent=4)