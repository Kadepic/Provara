"""Validateur LÉGER du routage NL → sous-systèmes FONCTION (fonction_nl.resout_fonction). FAUX=0.
Aucun chargement du lecteur : ne touche que references/chimie/genetique (légers). <1 s."""
import sys

from base_faits import VERIFIE
from fonction_nl import resout_fonction as F

ok, fails = 0, []


def check(nom, cond):
    global ok
    if cond:
        ok += 1
        print(f"  [OK ] {nom}")
    else:
        fails.append(nom)
        print(f"  [FAIL] {nom}")


def main():
    # —————————————————————— COUVERTURE (la bonne fonction répond, valeur vérifiée) ——————————————————————
    s, v, _ = F("quel est le code morse de SOS")
    check("MORSE : « code morse de SOS » -> ... --- ...", s == VERIFIE and v == "... --- ...")
    s, v, _ = F("morse de A")
    check("MORSE : « morse de A » -> .-", s == VERIFIE and v == ".-")
    s, v, _ = F("que signifie ... --- ... en morse")
    check("MORSE DÉCODE : « ... --- ... » -> SOS", s == VERIFIE and v == "SOS")

    s, v, _ = F("alphabet otan de B")
    check("OTAN : « otan de B » -> Bravo", s == VERIFIE and v == "Bravo")
    s, v, _ = F("nato de R")
    check("OTAN : « nato de R » -> Romeo", s == VERIFIE and v == "Romeo")

    s, v, _ = F("quel chiffre pour la bande rouge d'une résistance")
    check("RÉSISTANCE : bande rouge -> 2", s == VERIFIE and v == "2")
    s, v, _ = F("code couleur résistance violet")
    check("RÉSISTANCE : violet -> 7", s == VERIFIE and v == "7")
    s, v, _ = F("fréquence de la note A4")
    check("NOTE : A4 -> 440.0 Hz", s == VERIFIE and v == "440.0 Hz")
    s, v, _ = F("fréquence de la note La")
    check("NOTE : La (FR->A4) -> 440.0 Hz", s == VERIFIE and v == "440.0 Hz")
    s, v, _ = F("quelle est la fréquence de la note Do")
    check("NOTE : Do (FR->C4) -> ~261 Hz", s == VERIFIE and v.startswith("261") and v.endswith("Hz"))

    s, v, _ = F("masse molaire de H2O")
    check("CHIMIE : masse molaire de H2O -> 18.015 g/mol", s == VERIFIE and v == "18.015 g/mol")
    s, v, _ = F("quelle est la masse molaire du CO2")
    check("CHIMIE : masse molaire de CO2 (verifiee)", s == VERIFIE and v.endswith("g/mol"))
    s, v, _ = F("combien d'atomes dans H2SO4")
    check("CHIMIE : nb atomes H2SO4 -> 7 atomes", s == VERIFIE and v == "7 atomes")
    s, v, _ = F("composition de H2O")
    check("CHIMIE : composition de H2O (H et O)", s == VERIFIE and "H" in v and "O" in v)
    s, v, _ = F("pourcentage massique de O dans H2O")
    check("CHIMIE : %% massique O dans H2O -> 88.81 %", s == VERIFIE and v.startswith("88.81"))

    s, v, _ = F("complément de ATCG")
    check("ADN : complément de ATCG -> TAGC", s == VERIFIE and v == "TAGC")
    s, v, _ = F("complément inverse de ATCG")
    check("ADN : complément inverse de ATCG (verifie)", s == VERIFIE and v is not None)
    s, v, _ = F("transcription de ATCG")
    check("ADN : transcription de ATCG -> AUCG", s == VERIFIE and v == "AUCG")
    s, v, _ = F("traduction de ATGAAA")
    check("ADN : traduction de ATGAAA -> MK", s == VERIFIE and v == "MK")
    s, v, _ = F("quel acide aminé pour le codon ATG")
    check("ADN : codon ATG -> M", s == VERIFIE and v == "M")
    s, v, _ = F("complément de la séquence ATCG")
    check("ADN : repli dernier-token « la séquence ATCG » -> TAGC", s == VERIFIE and v == "TAGC")

    # —————————————————————— PHYSIQUE (formules paramétriques, unités SI) ——————————————————————
    s, v, _ = F("énergie cinétique d'une masse de 2 kg à 10 m/s")
    check("PHYS : énergie cinétique 2 kg, 10 m/s -> 100.0 J", s == VERIFIE and v == "100.0 J")
    s, v, _ = F("poids d'une masse de 5 kg")
    check("PHYS : poids de 5 kg -> 49.0332 N", s == VERIFIE and v == "49.0332 N")
    s, v, _ = F("énergie d'un photon de fréquence 6e14 Hz")
    check("PHYS : énergie photon 6e14 Hz (~e-19 J)", s == VERIFIE and "e-19" in v and v.endswith("J"))
    s, v, _ = F("tension pour une résistance de 10 ohm et un courant de 2 A")
    check("PHYS : loi d'Ohm 10 Ω, 2 A -> 20.0 V", s == VERIFIE and v == "20.0 V")

    # —————————————————————— SOUNDNESS (FAUX=0 : jamais une valeur fausse) ——————————————————————
    # —————————————————————— CONVERSION D'UNITÉS (table fermée, exacte, même dimension) ——————————————————————
    s, v, _ = F("Convertis 5 km en mètres")
    check("CONV : « 5 km en mètres » -> 5000", s == VERIFIE and v.startswith("5000"))
    s, v, _ = F("combien de mètres dans un kilomètre")
    check("CONV : « mètres dans un kilomètre » -> 1000", s == VERIFIE and v.startswith("1000"))
    s, v, _ = F("Combien de secondes dans une heure ?")
    check("CONV : « secondes dans une heure » -> 3600", s == VERIFIE and v.startswith("3600"))
    s, v, _ = F("convertis 2 m en cm")
    check("CONV : « 2 m en cm » -> 200", s == VERIFIE and v.startswith("200"))
    s, v, _ = F("convertir 1 tonne en kg")
    check("CONV : « 1 tonne en kg » -> 1000", s == VERIFIE and v.startswith("1000"))
    s, v, _ = F("convertis 500 mm en m")
    check("CONV : « 500 mm en m » -> 0.5", s == VERIFIE and v.startswith("0.5"))
    s, v, _ = F("combien de minutes dans 2 heures")
    check("CONV : « minutes dans 2 heures » -> 120", s == VERIFIE and v.startswith("120"))

    # —————————————————————— ARITHMÉTIQUE (entiers, résultat EXACT uniquement) ——————————————————————
    s, v, _ = F("Combien font 7 fois 8 ?")
    check("ARITH : « 7 fois 8 » -> 56", s == VERIFIE and v == "56")
    s, v, _ = F("Combien font 2 puissance 10 ?")
    check("ARITH : « 2 puissance 10 » -> 1024", s == VERIFIE and v == "1024")
    s, v, _ = F("Quelle est la racine carrée de 144 ?")
    check("ARITH : « racine carrée de 144 » -> 12", s == VERIFIE and v == "12")
    s, v, _ = F("Combien font 100 divisé par 4 ?")
    check("ARITH : « 100 divisé par 4 » -> 25", s == VERIFIE and v == "25")
    s, v, _ = F("Combien font 12 plus 30 ?")
    check("ARITH : « 12 plus 30 » -> 42", s == VERIFIE and v == "42")

    # RACINE NON PARFAITE (piège MIS À JOUR — décision Yohan 2026-07-09 nuit) : l'ancien piège exigeait HORS ;
    # le produit répond désormais MIEUX — l'irrationalité est DITE et l'approximation MARQUÉE (jamais une
    # décimale présentée comme exacte). Le check garde l'esprit FAUX=0 : les deux mentions sont EXIGÉES.
    s, v, _ = F("Quelle est la racine carrée de 145 ?")
    check("ARITH : « √145 » -> irrationalité DITE + approximation MARQUÉE (jamais une valeur nue)",
          s == VERIFIE and "irrationnel" in v and "approximation" in v and "12.04" in v)

    pieges = [
        "Combien font 100 divisé par 3 ?",  # ARITH division NON exacte -> HORS (jamais un arrondi)
        "Combien font 3.5 fois 2 ?",       # ARITH nombre décimal -> HORS (hors périmètre)
        "qu3ll3 3st l4 l4ngu3 du m3x1qu3 ?",  # ARITH leet : « m3x1qu3 » ne doit PAS matcher « 3x1 » (invariance)
        "l4 c4p1t4l3 d3 l4 fr4nc3",        # ARITH leet : digits collés dans des mots -> jamais un calcul
        "Quel est le pays de D-1-8042-0175 ?",  # ARITH ID hyphéné : « 1-8042 » (tiret collé) n'est PAS une soustraction
        "epreuve de relais 4 x 100 m",     # ARITH « x » nu = séparateur dimension/relais, PAS multiplication (#82)
        "quelle est la dimension de 256 x 202 cm",  # idem : « 256 x 202 » ne doit PAS donner 51712 (hijack #82)
        "producteur de 12 x 5",            # idem : « 12 x 5 » (album) ne doit PAS donner 60
        "Quelle est la date 2020-01-15 ?",      # ARITH date : « 2020-01 » (tiret collé) n'est pas un calcul
        "1/2/2020",                        # ARITH date : « 1/2 » (slash collé) n'est pas une division
        "convertis 5 km en kg",            # CONV inter-dimension (longueur->masse) -> HORS (jamais un nombre faux)
        "convertis 5 km en bananes",       # CONV unité de destination inconnue -> HORS
        "combien de licornes dans un mètre",  # CONV unité source inconnue -> HORS
        "convertis la France en Espagne",  # CONV : aucune unité -> HORS (pas de routage)
        "combien de mots dans un livre",   # CONV : « mots »/« livre » pas des unités de la table -> HORS
        "masse molaire de la lune",        # « lune » n'est pas une formule -> HORS
        "complément de bonjour",           # pas une séquence ADN valide -> HORS
        "code morse de éàç!",              # caractères hors table -> HORS (pas partiel)
        "quel est le nom scientifique de morse",  # HOMONYME #83 : morse=ANIMAL, l'arg EST « morse » -> pas de code Morse
        "c'est quoi un morse",             # idem : « morse » entité, pas une demande de traduction -> HORS
        "que signifie le sigle otan",      # HOMONYME #83 : otan=ORGANISATION, l'arg EST « otan » -> pas d'alphabet radio
        "quelle est la capitale du japon",  # question DATA : NE PAS router ici -> HORS
        "pourquoi le ciel est bleu",
        "sens de la vie",
        "masse molaire de XyZqw",          # formule invalide -> HORS
        "nato de %",                        # symbole hors table -> HORS
        "composition de l'équipe de france",  # « composition » mot courant mais pas une formule -> HORS
        "traduction de bonjour en anglais",   # « traduction » langue, pas une séquence ADN -> HORS
        "combien d'atomes dans la galaxie",   # pas une formule -> HORS
        "codon de la vie",                    # pas un codon ADN -> HORS
        "énergie cinétique d'une masse de 2 kg",        # PHYS : v MANQUANT -> HORS (pas de calcul partiel)
        "énergie cinétique de 2 kg et 3 kg à 10 m/s",   # PHYS : masse AMBIGUË (2 valeurs) -> HORS
        "poids d'une masse de 5 km",                    # PHYS : km n'est pas kg (mauvaise unité) -> HORS
        "la force de l'habitude",                       # PHYS : mot « force » mais aucune mesure -> HORS
        "énergie cinétique d'une voiture rapide",       # PHYS : aucun nombre -> HORS
        "la résistance de la France",                   # RÉSISTANCE : aucune couleur valide -> HORS
        "bonne note en mathématiques",                  # NOTE : pas de contexte fréquence/musique -> HORS
        "fréquence de la note Zorglub",                 # NOTE : note inexistante -> HORS
    ]
    faux = [q for q in pieges if F(q)[0] == VERIFIE]
    check(f"SOUNDNESS : {len(pieges)} pièges restent HORS (FAUX={len(faux)})", not faux)
    if faux:
        print("    pièges qui ont répondu (FAUX) :", faux)

    print(f"\n=== valide_fonction : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
