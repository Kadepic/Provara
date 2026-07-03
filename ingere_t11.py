"""
INGESTION T11 — TRANSPORT, VÉHICULES & INFRASTRUCTURE -> datasets/lecteur/*.jsonl (ONLINE QLever, offline ensuite).

Couloir : modèles/véhicules -> constructeur, réseaux -> exploitant. Catégorie `convention` (fait de production /
d'exploitation, comme societe_production_film / developpeur_jeu). FAUX=0 INVIOLABLE :

  - vocabulaire de valeurs OUVERT (constructeurs/exploitants = noms propres d'organisations), donc PAS de test
    d'ensemble fermé : on s'appuie sur (a) `fonctionnel` (publie) qui REJETTE tout libellé d'entité portant >1
    valeur distincte -> tout homonyme / véhicule multi-constructeur part en HORS ; (b) `_paires` qui écarte les
    Q-ID nus et les valeurs <2 caractères ; (c) ANCRES vérité-terrain dans valide_lecteur_t11.py (Titanic ->
    Harland and Wolff, etc.) -> ancrage NON circulaire.

constructeur_vehicule (Q42889 « véhicule ») est GÉNÉRIQUE : via P31/P279* il capte les sous-classes (navires,
aéronefs, automobiles, matériel roulant…). C'est la relation CÉDÉE par T7 — couvre tout le sujet « constructeur ».

Usage : python3 ingere_t11.py sonde   (inspecte sans écrire)   |   python3 ingere_t11.py   (ingère tout).
"""
from __future__ import annotations

import sys

import ingere_qlever as IQ


# (relation, classe_qid, propriété, catégorie, source)
RELATIONS = [
    ("constructeur_vehicule", "Q42889", "P176", "convention",
     "Wikidata/QLever — constructeur (fabricant P176) du véhicule (Q42889 + sous-classes : navire/aéronef/auto/train)"),
    ("exploitant_metro", "Q5503", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du réseau de métro (Q5503)"),
    ("exploitant_aeroport", "Q1248784", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) de l'aéroport (Q1248784) [organisation, distinct de pays_aeroport]"),
    ("exploitant_chemin_fer", "Q22667", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du chemin de fer (Q22667)"),
    ("exploitant_ligne_ferroviaire", "Q728937", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) de la ligne ferroviaire (Q728937)"),
    ("exploitant_tunnel", "Q44377", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du tunnel (Q44377) [ferroviaire/routier/canal -> gestionnaire]"),
    ("exploitant_port", "Q44782", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du port (Q44782) [autorité portuaire / marine / commune]"),
    ("alliance_compagnie_aerienne", "Q46970", "P114", "convention",
     "Wikidata/QLever — alliance (P114) de la compagnie aérienne (Q46970) [Star Alliance/Oneworld/Skyteam…]"),
    ("exploitant_gare", "Q55488", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) de la gare ferroviaire (Q55488) [compagnie ferroviaire / régie transit]"),
    ("constructeur_moteur_avion", "Q743004", "P176", "convention",
     "Wikidata/QLever — constructeur (P176) du moteur d'avion (Q743004) [GE/Pratt&Whitney/Rolls-Royce…, distinct du véhicule]"),
    ("exploitant_funiculaire", "Q142031", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du funiculaire (Q142031)"),
    ("exploitant_telepherique", "Q498002", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du téléphérique (Q498002)"),
    ("exploitant_reseau_tramway", "Q15640053", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du réseau de tramway (Q15640053) [Keolis/Transdev/De Lijn…]"),
    ("classe_navire", "Q11446", "P289", "convention",
     "Wikidata/QLever — classe (P289) du navire (Q11446) [classe Daring/Arleigh Burke/Fletcher… attribut de conception]"),
    ("constructeur_lanceur", "Q697175", "P176", "convention",
     "Wikidata/QLever — constructeur (P176) du lanceur spatial (Q697175) [SpaceX/ULA/ArianeGroup…, distinct du véhicule]"),
    ("exploitant_satellite", "Q26540", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du satellite artificiel (Q26540) [NASA/Roscosmos/ESA/Intelsat/Eutelsat…]"),
    ("constructeur_materiel_roulant", "Q811704", "P176", "convention",
     "Wikidata/QLever — constructeur (P176) de la classe de matériel roulant (Q811704) [Alstom/Siemens/Bombardier/EMD ; classe≠instance]"),
    ("exploitant_vehicule", "Q42889", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du véhicule individuel (Q42889 + sous-classes) [marines/compagnies ; distinct du constructeur]"),
    ("exploitant_phare", "Q39715", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) du phare (Q39715) [Trinity House/Service des phares et balises/garde-côtes]"),
    ("exploitant_ligne_ferry", "Q18984099", "P137", "convention",
     "Wikidata/QLever — exploitant (P137) de la liaison par ferry (Q18984099) [compagnies de traversiers]"),
    ("constructeur_satellite", "Q26540", "P176", "convention",
     "Wikidata/QLever — constructeur (P176) du satellite (Q26540) [Thales Alenia/Airbus DS/Ball/Reshetnev ; distinct de l'exploitant]"),
]

# Lot 2 (exploitants d'infrastructure) — ingéré séparément pour ne pas réécrire le lot 1.
LOT2 = ["exploitant_aeroport", "exploitant_chemin_fer", "exploitant_ligne_ferroviaire"]
# Lot 3 (infrastructures linéaires/portuaires) — ingéré séparément pour ne pas réécrire les lots 1 et 2.
LOT3 = ["exploitant_tunnel", "exploitant_port"]
# Lot 4 (appartenance d'une compagnie aérienne à une alliance) — closed set, ingéré séparément.
LOT4 = ["alliance_compagnie_aerienne"]
# Lot 5 (exploitant de gare ferroviaire) — ingéré séparément.
LOT5 = ["exploitant_gare"]
# Lot 6 (moteurs d'avion + remontées mécaniques / réseaux de tramway) — ingéré séparément.
LOT6 = ["constructeur_moteur_avion", "exploitant_funiculaire", "exploitant_telepherique", "exploitant_reseau_tramway"]
# Lot 7 (classe de conception d'un navire) — ingéré séparément.
LOT7 = ["classe_navire"]
# Lot 8 (constructeur de lanceur spatial) — ingéré séparément.
LOT8 = ["constructeur_lanceur"]
# Lot 9 (exploitant de satellite artificiel) — ingéré séparément.
LOT9 = ["exploitant_satellite"]
# Lot 10 (constructeur de classe de matériel roulant) — ingéré séparément.
LOT10 = ["constructeur_materiel_roulant"]
# Lot 11 (exploitant d'un véhicule individuel) — ingéré séparément.
LOT11 = ["exploitant_vehicule"]
# Lot 12 (exploitant de phare) — ingéré séparément.
LOT12 = ["exploitant_phare"]
# Lot 13 (exploitant de liaison par ferry) — ingéré séparément.
LOT13 = ["exploitant_ligne_ferry"]
# Lot 14 (constructeur de satellite) — ingéré séparément.
LOT14 = ["constructeur_satellite"]


# IDENTIFIANTS transport — pattern « code », fabrique _ingere_x_vers_code, validation STRUCTURELLE (forme du code).
# (relation, classe_qid, propriété, libellé, motif)
CODE_RELATIONS = [
    ("numero_imo_navire",    "Q11446", "P458", "numéro IMO du navire (Q11446)",            r"\d{7}"),
    ("mmsi_navire",          "Q11446", "P587", "MMSI du navire (Q11446)",                  r"\d{9}"),
    ("code_iata_compagnie",  "Q46970", "P229", "code IATA de la compagnie aérienne (Q46970)", r"[A-Z0-9]{2}"),
    ("code_icao_compagnie",  "Q46970", "P230", "code ICAO de la compagnie aérienne (Q46970)", r"[A-Z]{3}"),
    ("callsign_compagnie",   "Q46970", "P432", "indicatif radio de la compagnie aérienne (Q46970)", r"[A-Z0-9][A-Z0-9 '\-]*"),
]
LOT15 = ["numero_imo_navire"]
LOT16 = ["mmsi_navire"]
LOT17 = ["code_iata_compagnie"]
LOT18 = ["code_icao_compagnie"]
LOT19 = ["callsign_compagnie"]


def ingere_codes(seulement=None):
    for rel, cls, prop, lib, motif in CODE_RELATIONS:
        if seulement is not None and rel not in seulement:
            continue
        IQ._ingere_x_vers_code(rel, cls, prop, lib, categorie="convention", motif=motif)


def ingere_tout(seulement=None):
    for rel, cls, prop, cat, src in RELATIONS:
        if seulement is not None and rel not in seulement:
            continue
        IQ._ingere_x_vers_entite(rel, prop, cat, src, classe_qid=cls)


def sonde():
    """Inspecte chaque veine SANS écrire : tire les paires brutes, compte fonctionnel/multi, montre un échantillon."""
    from ingere_wikidata import fonctionnel
    for rel, cls, prop, _cat, _src in RELATIONS:
        q = f"""SELECT ?eLabel ?vLabel WHERE {{
          ?e wdt:P31/wdt:P279* wd:{cls} ; wdt:{prop} ?o .
          ?o rdfs:label ?vLabel . FILTER(lang(?vLabel)="fr")
          ?e rdfs:label ?eLabel . FILTER(lang(?eLabel)="fr")
        }}"""
        rows = IQ._charge_ou_fetch(rel, q)
        paires = IQ._paires(rows, "eLabel", "vLabel")
        fonc, rej = fonctionnel(paires)
        distinctes = len(set(v for _e, v in fonc))
        ech = fonc[:6]
        print(f"  [{rel:22s}] brutes={len(rows):6d} paires={len(paires):6d} fonctionnel={len(fonc):6d} "
              f"multi(HORS)={rej:5d} valeurs_distinctes={distinctes}")
        print("     ex: " + " | ".join(f"{e}->{v}" for e, v in ech))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sonde":
        sonde()
    elif len(sys.argv) > 1 and sys.argv[1] == "lot3":
        ingere_tout(seulement=LOT3)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot4":
        ingere_tout(seulement=LOT4)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot5":
        ingere_tout(seulement=LOT5)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot6":
        ingere_tout(seulement=LOT6)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot7":
        ingere_tout(seulement=LOT7)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot8":
        ingere_tout(seulement=LOT8)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot9":
        ingere_tout(seulement=LOT9)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot10":
        ingere_tout(seulement=LOT10)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot11":
        ingere_tout(seulement=LOT11)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot12":
        ingere_tout(seulement=LOT12)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot13":
        ingere_tout(seulement=LOT13)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot14":
        ingere_tout(seulement=LOT14)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot15":
        ingere_codes(seulement=LOT15)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot16":
        ingere_codes(seulement=LOT16)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot17":
        ingere_codes(seulement=LOT17)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot18":
        ingere_codes(seulement=LOT18)
    elif len(sys.argv) > 1 and sys.argv[1] == "lot19":
        ingere_codes(seulement=LOT19)
    else:
        ingere_tout()
