# -*- coding: utf-8 -*-
"""BANC DE PARAPHRASES — mesure de la COMPRÉHENSION OUVERTE (fossé de généralisation).

Chaque cas est une reformulation LIBRE (topicalisée, familière, elliptique, inversée…) d'une question dont la
réponse vérifiée est connue. Le banc mesure la proportion comprise par le pipeline COMPLET (`repond`, mode plein).
Contrairement aux gates, ce banc n'exige PAS 100 % : c'est un THERMOMÈTRE — chaque levier de compréhension
(dévoilement, parse SVO, vecteurs, constructions…) doit faire MONTER le score, jamais le faire baisser.
Sortie : score X/N + détail des échecs. Code retour 0 (mesure, pas gate) ; --gate <seuil> pour exiger un plancher.

Usage : LECTEUR_DATASETS_DIR=… python3 tests/banc_paraphrases.py            (base complète recommandée)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "interface"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import repond as R            # noqa: E402
import conversation           # noqa: E402

# (paraphrase, extrait attendu dans la réponse — insensible à la casse). Familles variées, tournures VRAIMENT
# libres : c'est exprès que beaucoup ne matchent aucun patron actuel — le fossé doit être VISIBLE pour se réduire.
CAS = [
    # créateur
    ("1984, c'est de qui ?", "orwell"),
    ("c'est qui l'auteur de 1984 ?", "orwell"),
    ("l'auteur de 1984, c'est qui déjà ?", "orwell"),
    ("de qui est le roman 1984 ?", "orwell"),
    ("qui c'est qui a écrit 1984 ?", "orwell"),
    ("la Joconde, c'est de qui ?", "vinci"),
    ("qui a fait la Joconde ?", "vinci"),
    ("le Boléro, c'est qui le compositeur ?", "ravel"),
    ("c'est qui qui a composé le Boléro ?", "ravel"),
    # capitale / lookup nominal
    ("la capitale du Japon, c'est quoi ?", "tokyo"),
    ("c'est quoi déjà la capitale du Japon ?", "tokyo"),
    ("Japon : capitale ?", "tokyo"),
    ("quelle ville est la capitale du Japon ?", "tokyo"),
    ("tu connais la capitale du Japon ?", "tokyo"),
    # population / quantités
    ("la France, elle a combien d'habitants ?", "68"),
    ("combien de gens vivent en France ?", "68"),
    ("y a combien d'habitants en France ?", "68"),
    # fait personne
    ("il est né où, Napoléon Ier ?", "ajaccio"),
    ("Napoléon Ier, il est né où ?", "ajaccio"),
    ("où c'est que Napoléon Ier est né ?", "ajaccio"),
    # superlatif / comparaison
    ("quel pays d'Afrique a le plus d'habitants ?", "nig"),
    ("le pays le plus peuplé d'Afrique, c'est lequel ?", "nig"),
    ("lequel est le plus peuplé : la France ou l'Allemagne ?", "allemagne"),
    ("entre la France et l'Allemagne, qui a le plus d'habitants ?", "allemagne"),
    # temporel
    ("la bataille de Marignan, c'était quand ?", "1515"),
    ("c'était en quelle année, Marignan ?", "1515"),
    ("elle a duré combien de temps, la guerre de Cent Ans ?", "116"),
    ("après Louis XIV, c'est qui le roi ?", "louis xv"),
    # calcul
    ("ça fait combien, 12 fois 8 ?", "96"),
    ("12 multiplié par 8, ça donne quoi ?", "96"),
    # ontologie / définition
    ("un chat, c'est bien un animal ?", "oui"),
    ("est-ce qu'on peut dire qu'une rose est une fleur ?", "oui"),
    ("ça veut dire quoi, apartheid ?", "régime"),          # définition réelle : « régime politique de séparation… »
    ("apartheid, ça veut dire quoi ?", "régime"),
    # dimension / localisation
    ("quelle est la hauteur du mont Everest ?", "8848"),
    ("Tokyo, c'est dans quel pays ?", "japon"),
    ("dans quel pays se trouve Tokyo ?", "japon"),
    # monnaie
    ("la monnaie qu'on utilise au Japon, c'est quoi ?", "yen"),
    ("on paie avec quoi au Japon ?", "yen"),
    ("avec quelle monnaie paie-t-on au Japon ?", "yen"),
]


def run():
    mem = conversation.MemoireConversation(racine=None)
    ok, echecs = 0, []
    for i, (q, attendu) in enumerate(CAS):
        try:
            rep = R.repond(mem, "para-%d" % i, q, pleine=True) or ""
        except Exception as e:                                # jamais de crash : un échec est un échec mesuré
            rep = "EXCEPTION %r" % e
        if attendu.lower() in rep.lower():
            ok += 1
        else:
            echecs.append((q, rep.replace("\n", " ")[:90]))
    total = len(CAS)
    print("\nPARAPHRASES COMPRISES : %d/%d (%.0f %%)" % (ok, total, 100.0 * ok / total))
    if echecs:
        print("NON COMPRISES :")
        for q, rep in echecs:
            print("  ✗ %s\n      -> %s" % (q, rep))
    if "--gate" in sys.argv:                                  # mode gate optionnel : plancher exigé
        seuil = int(sys.argv[sys.argv.index("--gate") + 1])
        return 0 if ok >= seuil else 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
