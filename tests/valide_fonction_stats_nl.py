# -*- coding: utf-8 -*-
"""VALIDE fonction_stats_nl : routeur statistique en langage naturel, FAUX=0.

Vérifie que les intentions statistiques sont reconnues et routées vers la bonne fonction (résultat exact pour
le descriptif, réponse calibrée sinon), et qu'une phrase NON statistique -> None (pas de détournement)."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("LECTEUR_AMORCE_SEULE", "1")
_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import fonction_stats_nl as S

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — descriptif EXACT —
check(S.repond_stats("moyenne de 12, 15, 14, 13, 16, 12").startswith("Moyenne : 13.67"), "moyenne exacte")
check("Médiane : 3.5" in S.repond_stats("médiane de 3, 1, 4, 1, 5, 9, 2, 6"), "médiane exacte")
check("Écart-type" in S.repond_stats("écart-type de 10, 12, 14, 16, 18"), "écart-type")
check("Somme : 20" in S.repond_stats("somme de 2, 4, 6, 8"), "somme exacte")
# GARDE SÉRIE (FAUX vécu 2026-07-08) : « somme des entiers de 1 à 100 » servait « Somme : 101 (sur 2
# valeurs) » — les BORNES prises pour la liste. La série revient à fonction_nl (5050), pas ici.
check(S.repond_stats("somme des entiers de 1 à 100") is None, "somme de série -> None (route dédiée)")
check(S.repond_stats("somme des 100 premiers entiers") is None, "somme des N premiers -> None (route dédiée)")
check("Minimum : 2" in S.repond_stats("min et max de 7, 2, 9, 4"), "min/max")

# — moyenne PONDÉRÉE : les coefficients ne sont JAMAIS moyennés avec les valeurs (bug vécu : 8 au lieu de 13.8) —
check("Moyenne pondérée : 13.8" in S.repond_stats("moyenne pondérée de 12 coefficient 2 et 15 coefficient 3"),
      "pondérée paires coefficient")
check("Moyenne pondérée : 13.8" in S.repond_stats("moyenne de 12 et 15 avec les poids 2 et 3"),
      "pondérée valeurs puis poids")
check("Moyenne pondérée : 11 " in S.repond_stats(
    "quelle est la moyenne pondérée de mes notes : 12 (coefficient 4) et 9 (coefficient 2)"),
      "pondérée notes parenthésées")
r = S.repond_stats("moyenne pondérée de 12 et 15")
check(r and "n'arrive pas à associer" in r, "pondérée sans coefficients -> abstention honnête, jamais 13.5")
check("Moyenne : 80" in S.repond_stats("moyenne des poids 70, 80 et 90"),
      "« poids » physiques -> moyenne simple (pas de détournement)")
check("indéfinie" in S.repond_stats("moyenne pondérée de 10 coefficient 0 et 20 coefficient 0"),
      "somme des coefficients nulle -> indéfinie")

# — calibré (contenu partiel, tolérant) —
r = S.repond_stats("est-ce que 100, 102, 101, 105, 108, 110 est en hausse ?")
check(r and ("monte" in r or "hausse" in r or "pente" in r), "tendance -> hausse")
r = S.repond_stats("j'ai 37 succès sur 100, quel est l'intervalle de confiance ?")
check(r and "0.282" in r and "Wilson" in r, "proportion Wilson 37/100")
r = S.repond_stats("j'ai eu 8 pannes en 5 jours, quel est le taux ?")
check(r and "Taux estimé" in r, "taux Poisson")
r = S.repond_stats("je gagne avec proba 0.55 à une cote de 2, combien parier avec Kelly ?")
check(r and "0.325" in r, "Kelly f*=0.325")
r = S.repond_stats("87 est-il une valeur anormale par rapport à 12, 15, 14, 13, 16 ?")
check(r and "anormale" in r, "anomalie détectée")
r = S.repond_stats("corrélation entre 1,2,3,4,5,6,7,8,9,10,11,12 et 2,4,6,8,10,12,14,16,18,20,22,24")
check(r and ("pente" in r.lower() or "2.0" in r), "corrélation/pente 2 listes")

# — abstention HONNÊTE relayée (échantillon trop petit) —
r = S.repond_stats("compare le groupe 12, 15, 14, 13 et 18, 20, 19, 21")
check(r and ("pr[éeè]f" in r.lower() or "petit" in r or "prononcer" in r), "compare relaie l'abstention honnête")

# — NON-statistique -> None (aucun détournement) —
for q in ["bonjour comment vas-tu ?", "quelle est la capitale de la France ?",
          "conjugue le verbe parler", "raconte-moi une histoire"]:
    check(S.repond_stats(q) is None, "non-stat « %s » -> None" % q)

print("=== valide_fonction_stats_nl : %d/%d ===" % (ok, ok + ko))
sys.exit(0 if ko == 0 else 1)
