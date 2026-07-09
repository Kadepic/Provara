# -*- coding: utf-8 -*-
"""VALIDE interroge_donnees (Route 3 : fichiers INTERROGEABLES) — opérations exactes sur CSV/JSON attachés.
FAUX=0 : chaque agrégat/extraction est EXACT et localisé (ligne réelle, chemin JSON) ; hors périmètre → None
(jamais de capture d'une question générale) ; unités mélangées / texte → refus honnête, jamais un calcul faux."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import interroge_donnees as I

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# ── _nombre : parsing strict des cellules ────────────────────────────────────────────────────────────────────
for s, attendu, unite in [("12,5", 12.5, ""), ("1 234", 1234.0, ""), ("1 234", 1234.0, ""),
                          ("1.234,56", 1234.56, ""), ("45 %", 45.0, "%"), ("2 kg", 2.0, "kg"),
                          ("-3,5", -3.5, ""), ("1.234", 1.234, ""), ("0", 0.0, ""), ("12 €", 12.0, "€")]:
    v, u = I._nombre(s)
    check(v == attendu and u == unite, "nombre %r -> %r %r (obtenu %r %r)" % (s, attendu, unite, v, u))
for s in ("abc", "12-14", "", "  ", "3/4", "v2", "1 23", "12,5,6", None):
    check(I._nombre(s)[0] is None, "nombre %r -> None (jamais deviné)" % (s,))

# ── Tableau : en-tête, agrégats exacts, preuve de localisation ───────────────────────────────────────────────
T = I.Tableau([["nom", "prix", "qte"],
               ["pomme", "1,20", "10"],
               ["poire", "2,50", "4"],
               ["banane", "0,90", "12"],
               ["kiwi", "", "3"]], titre="fruits.csv")
check(T.entete == ["nom", "prix", "qte"] and T.n == 4, "en-tête détecté + 4 lignes de données")

r = I.repond("quel est le max de la colonne prix ?", T)
check(r and "2,5" in r and "poire" in r and "ligne 3" in r, "max prix = 2,5 + preuve (ligne 3, poire) : %r" % r)
r = I.repond("quel est le minimum de prix ?", T)
check(r and "0,9" in r and "banane" in r, "min prix = 0,9 (banane)")
r = I.repond("quel est le prix le plus élevé ?", T)
check(r and "2,5" in r, "formulation « le plus élevé » -> max")
r = I.repond("somme de la colonne qte", T)
check(r and "29" in r, "somme qte = 29 (exact)")
r = I.repond("moyenne de qte ?", T)
check(r and "7,25" in r and "4 valeur" in r, "moyenne qte = 7,25 sur 4 valeurs (kiwi compté : cellule qte pleine)")
r = I.repond("combien de lignes ?", T)
check(r and "4" in r and "hors en-tête" in r, "comptage lignes = 4, en-tête exclu et DIT")
r = I.repond("quelles sont les colonnes ?", T)
check(r and "nom, prix, qte" in r, "liste des colonnes réelles")
r = I.repond("combien de colonnes ?", T)
check(r and "3 colonne" in r, "comptage colonnes = 3")
r = I.repond("max de la colonne 2 ?", T)
check(r and "2,5" in r, "adressage « colonne 2 » (index humain) -> prix")

# extraction ciblée d'une cellule (lookup ligne × colonne)
r = I.repond("quel est le prix de la poire ?", T)
check(r and "2,50" in r and "poire" in r, "cellule : prix de poire = 2,50 (verbatim)")
r = I.repond("quelle est la qte de banane ?", T)
check(r and "12" in r, "cellule : qte de banane = 12")
r = I.repond("quel est le prix du kiwi ?", T)
check(r and "VIDE" in r and "invente" in r, "cellule VIDE -> dit vide, n'invente jamais")

# comptage conditionnel
r = I.repond("combien de lignes ont pomme ?", T)
check(r and "1 ligne" in r and "nom" in r, "comptage conditionnel : 1 ligne porte « pomme » (colonne nommée)")

# ── unités : uniforme = affichée ; mélangées = refus honnête ────────────────────────────────────────────────
TU = I.Tableau([["piece", "masse"], ["a", "2 kg"], ["b", "5 kg"]], titre="masses.csv")
r = I.repond("max de masse ?", TU)
check(r and "5 kg" in r, "unité uniforme affichée : max = 5 kg")
TM = I.Tableau([["piece", "masse"], ["a", "2 kg"], ["b", "500 g"]], titre="mixte.csv")
r = I.repond("max de masse ?", TM)
check(r and ("mélange" in r or "melange" in r) and "5" not in r.split("(")[0].replace("mixte.csv", ""),
      "unités MÉLANGÉES (kg vs g) -> refus honnête, jamais un max faux : %r" % r)

# colonne 100 % texte -> refus honnête d'un agrégat numérique
r = I.repond("max de la colonne nom ?", T)
check(r and "aucun nombre" in r, "agrégat sur colonne texte -> refus honnête")

# ── sans en-tête (données dès la ligne 1) ───────────────────────────────────────────────────────────────────
TS = I.Tableau([["10", "20"], ["30", "5"]], titre="brut.csv")
check(TS.entete == ["colonne 1", "colonne 2"] and TS.n == 2, "pas d'en-tête -> colonnes numérotées, 2 lignes")
r = I.repond("max de la colonne 1 ?", TS)
check(r and "30" in r and "ligne 2" in r, "max colonne 1 = 30 (ligne 2 réelle du fichier)")

# ── ambiguïtés dites, jamais tranchées en silence ───────────────────────────────────────────────────────────
TA = I.Tableau([["prix", "prix unitaire"], ["3", "1"], ["9", "2"]], titre="amb.csv")
r = I.repond("max du prix unitaire ?", TA)
check(r and "2" in r, "colonne la plus LONGUE gagne : « prix unitaire » bat « prix »")
T2 = I.Tableau([["nom", "prix"], ["pomme", "1"], ["pomme", "2"]], titre="doublons.csv")
r = I.repond("quel est le prix de la pomme ?", T2)
check(r and ("plusieurs lignes" in r and "Précise" in r), "lookup ambigu (2 lignes « pomme ») -> demande de précision")

# ── ZÉRO capture indue (pièges : table attachée mais question générale) ─────────────────────────────────────
for q in ("quelle est la capitale de la France ?",
          "quel est le plus grand pays du monde ?",
          "combien de temps dure un match de football ?",
          "raconte-moi une histoire",
          "quelle est la moyenne au bac ?",          # « moyenne » MAIS aucune colonne du fichier ni réf. fichier
          "c'est quoi le total à payer chez le dentiste ?"):
    check(I.repond(q, T) is None, "piège capture : %r -> None" % q)
# agrégat + référence EXPLICITE au fichier mais colonne inconnue -> aide actionnable (pas une invention)
r = I.repond("quel est le max de la colonne tarif dans le fichier ?", T)
check(r and "nom, prix, qte" in r, "colonne inconnue + réf. fichier -> colonnes disponibles listées")
check(I.repond("max de prix ?", None) is None, "aucun document -> None")
check(I.repond("", T) is None, "question vide -> None")
check(I.repond("max de prix ?", I.Tableau([], titre="vide.csv")) is None, "tableau VIDE -> None (rien à dire)")

# ── Arbre (json) : comptages, clés, valeurs — chemins en preuve ─────────────────────────────────────────────
A = I.Arbre({"livres": [{"titre": "Germinal", "prix": 10}, {"titre": "Nana", "prix": 12}],
             "auteur": "Zola", "annee": 1885}, titre="biblio.json")
r = I.repond("combien de livres ?", A)
check(r and "2 élément" in r and "racine.livres" in r, "comptage de clé-liste : 2 (chemin en preuve)")
r = I.repond("quelles sont les clés ?", A)
check(r and "livres" in r and "auteur" in r, "clés réelles listées")
r = I.repond("quel est l'auteur ?", A)
check(r and "Zola" in r and "racine.auteur" in r, "valeur d'une clé unique, verbatim + chemin")
r = I.repond("quel est le prix ?", A)
check(r and "2 fois" in r and "10" in r and "12" in r, "clé multiple -> TOUTES les occurrences, jamais un choix muet")
r = I.repond("quel est le titre ?", A)
check(r and "Germinal" in r and "Nana" in r, "clé « titre » ×2 -> les deux, avec chemins")
AL = I.Arbre([{"id": 1}, {"id": 2}, {"id": 3}], titre="liste.json")
r = I.repond("combien d'éléments contient le fichier ?", AL)
check(r and "3 élément" in r, "liste au sommet : 3 éléments")
r = I.repond("quelles sont les clés ?", AL)
check(r and "id" in r, "liste d'objets -> clés de chaque élément")
for q in ("quelle est la capitale de la France ?", "que penses-tu de la vie ?", "combien font 2 et 2 ?"):
    check(I.repond(q, A) is None, "piège capture JSON : %r -> None" % q)

# pluriel toléré sur les clés (« combien de livre » / clé « livres »)
r = I.repond("combien de livre ?", A)
check(r and "2 élément" in r, "pluriel/singulier tolérés sur la clé")

print("=== valide_interroge_donnees : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
