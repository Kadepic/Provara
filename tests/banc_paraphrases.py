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
    # ————— 2e VAGUE (plus dure) : indirectes, soutenu, ellipses, doubles topicalisations, confirmations —————
    ("j'ai oublié qui a écrit 1984", "orwell"),
    ("je ne sais plus quelle est la capitale du Japon", "tokyo"),
    ("je me demande combien d'habitants a la France", "68"),
    ("tu te souviens qui a peint la Joconde ?", "vinci"),
    ("qui est l'auteur du roman intitulé 1984 ?", "orwell"),
    ("en quelle année la bataille de Marignan s'est-elle déroulée ?", "1515"),
    ("où Napoléon Ier a-t-il vu le jour ?", "ajaccio"),
    ("capitale Japon ?", "tokyo"),
    ("auteur 1984 ?", "orwell"),
    ("le Japon, sa capitale, c'est quoi ?", "tokyo"),
    ("et la monnaie, au Japon, c'est quoi ?", "yen"),
    ("la capitale du Japon, c'est bien Tokyo ?", "oui"),
    ("c'est bien Orwell qui a écrit 1984 ?", "oui"),
    ("de la France, quelle est la population ?", "68"),
    ("c'est laquelle, la capitale du Japon ?", "tokyo"),
    ("il a écrit quoi, Orwell ?", "1984"),
    ("elle est où, Tokyo ?", "japon"),
    ("ça se trouve où, Tokyo ?", "japon"),
    ("combien font douze fois huit ?", "96"),
    ("quel âge avait Napoléon Ier à sa mort ?", "52"),
]

# ————— 4e VAGUE : COMBINAISONS ADVERSES (SMS léger + fautes + oral + enrobage EMPILÉS) —————
CAS += [
    ("c ki ki a ecri 1984 ?", "orwell"),
    ("cest koi la capitale du japon", "tokyo"),
    ("kel est la capitale du japon", "tokyo"),
    ("la capitale du japon c koi", "tokyo"),
    ("ou se trouve tokyo", "japon"),
    ("dis moi ou est né napoleon 1er stp", "ajaccio"),
    ("qui a ecrit 1984", "orwell"),
    ("combien fon 12 fois 8", "96"),
    ("QUELLE EST LA CAPITALE DU JAPON", "tokyo"),
    ("quelle est la capitale du japon????", "tokyo"),
    ("la joconde c de qui", "vinci"),
    ("napoleon ier il est né ou", "ajaccio"),
]

# ————— 5e VAGUE : ORDRE DES MOTS VRAIMENT LIBRE (le grand levier parse SVO) —————
CAS += [
    ("du Japon, dis-moi la capitale", "tokyo"),
    ("du Japon la capitale ?", "tokyo"),
    ("la capitale, pour le Japon ?", "tokyo"),
    ("Japon, capitale ?", "tokyo"),
    ("pour le Japon, la monnaie ?", "yen"),
    ("le Japon, sa capitale ?", "tokyo"),
    ("la France, sa population ?", "68"),
    ("Napoléon Ier, sa nationalité ?", "france"),   # nationalite_personne stocke « France »
    ("1984, son auteur ?", "orwell"),
    ("le Japon : monnaie ?", "yen"),
    ("la capitale, c'est quoi, pour le Japon ?", "tokyo"),
    ("dis, la capitale du Japon ?", "tokyo"),
]

# ————— 6e VAGUE : SYNONYMES DE TÊTES DE RELATION (mot proche ≠ tête canonique) —————
CAS += [
    ("quelle est la richesse du Japon ?", "4"),          # richesse -> pib_pays (4435 G$)
    ("quel est le PIB du Japon ?", "4"),
    ("le nombre d'habitants du Japon ?", "123"),         # nombre d'habitants -> population
    ("quelle est la taille de la France ?", "551"),      # taille (pays) -> superficie
    ("quelle est l'étendue de la France ?", "551"),
    ("la superficie de la France ?", "551"),             # canonique (non-régression)
    ("la population du Japon ?", "123"),                 # canonique (non-régression)
]

# ————— 7e VAGUE : PRÉAMBULES CONVERSATIONNELS + TAGS DE FIN + FILLERS (compréhension de phrases longues) —————
CAS += [
    ("j'aimerais beaucoup savoir qui a écrit 1984", "orwell"),
    ("une question qui me trotte : le chat, c'est bien un félin non ?", "félin"),
    ("j'ai une colle pour toi : qui a peint la Joconde ?", "vinci"),
    ("excuse-moi de te déranger mais quelle est la capitale de l'Italie ?", "rome"),
    ("tiens, à propos, le PIB de l'Allemagne c'est combien ?", "pib"),
    ("dis-moi, si tu le sais, quelle est la capitale de l'Australie", "canberra"),
    ("franchement je me demande quelle est la monnaie du Japon", "yen"),
]

# ————— 8e VAGUE : COMPOSITION PROFONDE (enveloppe interrogative + pont ville→pays + élision) —————
CAS += [
    ("sur quel continent se trouve la capitale du Japon ?", "asie"),          # ex-FAUX .exe : répondait « Tokyo »
    ("où est né l'auteur de 1984 ?", "motihari"),                             # créateur -> lieu de naissance (2 sauts)
    ("quand est mort le successeur de Louis XIV ?", "1774"),                  # succession -> année de décès
    ("quelle est la monnaie de la capitale du Japon ?", "yen"),               # capitale -> pont ville→pays -> monnaie
    ("quelle est la monnaie de Tokyo ?", "yen"),                              # pont ville→pays direct
    ("sur quel continent se trouve la capitale du pays le plus peuplé du monde ?", "asie"),  # feuille superlative + 3 sauts
    ("quand a eu lieu la bataille de Hastings ?", "1066"),                    # élision « d'Hastings » (répondait « Battle »)
    ("quelle est la population de la capitale de la France ?", "je m'abstiens"),  # chaîne partielle honnête (Paris sans population_ville)
]

# ————— 3e VAGUE : ANAPHORES INTER-TOURS — (amorce, suite anaphorique, extrait attendu dans la 2e réponse).
# La 2e question n'a AUCUN sens seule (« il est mort quand ? ») : elle mesure la mémoire conversationnelle.
MULTITOURS = [
    ("où est né Napoléon Ier ?", "et dis-moi il est mort quand", "1821"),   # enrobage + anaphore EMPILÉS
    ("où est né Napoléon Ier ?", "il est mort quand ?", "1821"),
    ("où est née Marie Curie ?", "elle est morte quand ?", "1934"),
    ("où est né Napoléon Ier ?", "et il était de quelle nationalité ?", "france"),
    ("quelle est la capitale du Japon ?", "et sa monnaie ?", "yen"),
    ("quelle est la capitale du Japon ?", "et sa population ?", "1"),      # population du Japon (chiffre)
    ("quand a eu lieu la bataille de Marignan ?", "et celle de Waterloo ?", "1815"),
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
    for i, (amorce, suite, attendu) in enumerate(MULTITOURS):
        cid = "para-mt-%d" % i
        try:
            R.repond(mem, cid, amorce, pleine=True)              # pose le contexte (même conversation)
            rep = R.repond(mem, cid, suite, pleine=True) or ""
        except Exception as e:
            rep = "EXCEPTION %r" % e
        if attendu.lower() in rep.lower():
            ok += 1
        else:
            echecs.append(("%s || %s" % (amorce, suite), rep.replace("\n", " ")[:90]))
    total = len(CAS) + len(MULTITOURS)
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
