"""
INGESTION HISTOIRE — événement -> année -> datasets/lecteur/annee.jsonl  (OFFLINE).

SOURCE : dates historiques de RÉFÉRENCE, CERTAINES et NON DISPUTÉES (je suis une source pour le certain).

FAUX=0 — discipline :
  * UNIQUEMENT des événements à date NON CONTESTÉE (année précise consensuelle).
  * On ÉTEND la relation `annee` déjà amorcée dans base_faits SANS recouvrir ses 13 entrées
    (révolution française, premier pas sur la lune, etc. -> NON répétés ici) : aucune contradiction.
  * On ÉCARTE les dates approximatives/disputées (invention de l'imprimerie ~1440, grande peste, etc.).
  * Valeur = année seule (chaîne). Événements à intervalle (guerres) -> on ne met QUE des bornes datées
    distinctes (« début de … », « armistice de … ») pour rester fonctionnel et certain.
  * Clés = libellés FR ; le lecteur normalise (accents/articles) à la lecture.

Usage : python3 ingere_histoire.py    (puis non-reg OFFLINE).
"""
from __future__ import annotations

from ingere_wikidata import publie

# (événement, année) — chacun vérifié certain, AUCUN recouvrement avec base_faits.
_EVENEMENTS = [
    ("prise de la bastille", "1789"),
    ("déclaration des droits de l'homme et du citoyen", "1789"),
    ("proclamation de la première république française", "1792"),
    ("sacre de napoléon", "1804"),
    ("bataille d'austerlitz", "1805"),
    ("bataille de marignan", "1515"),
    ("édit de nantes", "1598"),
    ("révocation de l'édit de nantes", "1685"),
    ("couronnement de charlemagne", "800"),
    ("bataille de hastings", "1066"),
    ("chute de constantinople", "1453"),
    ("chute de l'empire romain d'occident", "476"),
    ("concile de nicée", "325"),
    ("hégire", "622"),
    ("débarquement de normandie", "1944"),
    ("armistice du 11 novembre", "1918"),
    ("traité de versailles", "1919"),
    ("bombardement d'hiroshima", "1945"),
    ("traité de rome", "1957"),
    ("traité de maastricht", "1992"),
    ("mai 68", "1968"),
    ("abolition de la peine de mort en france", "1981"),
    ("indépendance de l'algérie", "1962"),
    ("première coupe du monde de football", "1930"),
    ("révolution d'octobre", "1917"),
    ("révolution américaine", "1775"),
    ("grand incendie de londres", "1666"),
    ("éruption du vésuve (pompéi)", "79"),
    ("assassinat de jules césar", "-44"),
    ("bataille de gergovie", "-52"),
]

SRC = "dates historiques de référence (certaines, non disputées) — extension de la relation annee"


def ingere():
    print(f"== HISTOIRE — événement -> année ({len(_EVENEMENTS)} événements, extension de `annee`) ==")
    publie("annee", "passe", SRC, _EVENEMENTS)


if __name__ == "__main__":
    ingere()
