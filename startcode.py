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
bezoeker_id = 1 # pas id aan om een andere bezoeker te selecteren


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
# doorlooptijd plus wachtijd en overgebleven duur
duurover = bezoeker["verblijfsduur"]
totaal_tijd = 0

# potje van alle attracties die passen
attr_potje = []

# counter define
counter = 0

# dit in een define voor herroep
# pick een random attractie uit lijst
def Rattr():
    global gek_attractie
    gek_attractie = random.choice(attracties)

    # print(gek_attractie)

Rattr()
# nu gaan we volgorde check alles met define doen!
def voegtoe():
    # lijst bestaat. FORCEFALLBACK
    attr_potje.append(gek_attractie)
    print("TOEGEVOEGD:", gek_attractie["naam"])


# check 1, is leeftijd okay?
def check1():
    if (
        gek_attractie["attractie_min_leeftijd"] is None
        or bezoeker["leeftijd"] >= gek_attractie["attractie_min_leeftijd"]
    ):
        # print("klopt! hij mag", bezoeker["leeftijd"], gek_attractie["attractie_min_leeftijd"])
        check2()
    else:
        # print("nee")
        Rattr()
        check1()


# check 2, is lengte okay?
def check2():
    if (
        gek_attractie["attractie_min_lengte"] is None
        or bezoeker["lengte"] >= gek_attractie["attractie_min_lengte"] 
    ):
        # print("klopt! hij mag")
        check3()
    else:
        # print("nee")
        Rattr()
        check1()

# check 3, is gewicht okay?
def check3():
    if (
        gek_attractie["attractie_max_gewicht"] is None
        or bezoeker["gewicht"] <= gek_attractie["attractie_max_gewicht"] 
    ):
        # print("klopt! hij mag", )
        check4()
    else:
        # print("nee",bezoeker["gewicht"], gek_attractie["attractie_max_gewicht"])
        Rattr()
        check1()

# bekijk het voorwaarde van regenen. dit past toe op check5
def check4():
    global weervoorwaarde

    temperatuur = dagprogramma["weergegevens"]["temperatuur"]
    kans_op_regen = dagprogramma["weergegevens"]["kans_op_regen"]

    if temperatuur >= 15 and kans_op_regen == False:
        # print("jep, het gaat niet regenen")
        weervoorwaarde = "buiten"
    else:
        # print("nee, gaat regenen dus binnenattracties")
        weervoorwaarde = "binnen"

    check5()

# check of gekozen(gek) binnen is en past bij attribuut van weervoorwaarde
def check5():
    if weervoorwaarde == "binnen":
        if gek_attractie["overdekt"] == 1:
            # print("Ja, deze attractie past bij het weer")
            check6()
        else:
            # print("Nee, deze attractie is buiten")
            Rattr()
            check1()
    else:
        # print("geen slecht weer alles mag!")
        check6()

# lievelingsattractie moet 2 maal
def check6():
    # nieuw systeem over lievelingsattractie. moet 2 maal (RETURN)
    if gek_attractie["naam"] in dagprogramma["bezoekersgegevens"]["lievelingsattracties"]:
        # print("Dit is een lievelingsattractie!")
        check7(True)

    else:
        check7()

def check7(lievelings=False):
    global duur
    global duurover
    global counter

    duur = gek_attractie["geschatte_wachttijd"] + gek_attractie["doorlooptijd"]

    # de check past hij in resterende tijd
    if duurover >= duur:
        duurover -= duur
        voegtoe()
        # check of er meer kan of niet
        if duurover <= 0:
            genereer()
        else:
            counter += 1
            Rattr()
            check1()
    else:
        # Is dit de tweede lievelingsattractie?
        if lievelings:

            lievelingen = dagprogramma["bezoekersgegevens"]["lievelingsattracties"]
            # Zoek alle attracties die GEEN lievelingsattractie zijn
            niet_lievelingen = [
                attractie
                for attractie in attr_potje
                if attractie["naam"] not in lievelingen
            ]
            # Als er iets verwijderd kan worden
            if niet_lievelingen:
                te_verwijderen = random.choice(niet_lievelingen)
                attr_potje.remove(te_verwijderen)

                # Tijd van verwijderde attractie teruggeven
                vrijgekomen_tijd = (
                    te_verwijderen["geschatte_wachtijd"]
                    + te_verwijderen["doorlooptijd"]
                )
                duurover += vrijgekomen_tijd
                # print("Verwijderd:", te_verwijderen["naam"])
                # print("Nieuwe resterende tijd:", duurover)
                # Nu opnieuw proberen
                check7(lievelings=True)
            else:
                # print("Geen niet-lievelingsattractie meer om te verwijderen.")
                print(" ")
        else:
            genereer()
        

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
    if aantal_attracties > 0:
        horeca_posities.append(aantal_attracties // 2)

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

            if horeca_teller == 0:
                horeca_keuze = gekozen_horeca
            else:
                if passende_horeca:
                    horeca_keuze = random.choice(passende_horeca)

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

check1()

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open('dagprogramma_bezoeker_x.json', 'w') as json_bestand_uitvoer:
    json.dump(dagprogramma, json_bestand_uitvoer, indent=4)