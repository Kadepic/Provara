# -*- coding: utf-8 -*-
"""VALIDE le compositeur TÊTE POLYSÉMIQUE (Phase 2 généralisée du TRONC §7/§10, validée Yohan 2026-07-09) :
une tête nominale à plusieurs relations candidates -> toutes TENTÉES contre le store (le lookup réel juge les
lectures), 1 ancrée -> net ; ≥2 même valeur -> concordance DITE ; ≥2 valeurs -> divergence LISTÉE ; 0 -> None.
FAUX=0 : uniquement des lignes réelles de tables vérifiées ; zéro capture des têtes voisines."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "interface"))
os.environ.setdefault("LECTEUR_DATASETS_DIR", os.path.join(os.path.dirname(_ICI), "datasets", "lecteur"))

import repond as R
import tronc as T

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


F = R._cap_tete_polysemique

# — une seule lecture ancrée -> réponse NETTE (le store a jugé : Camp Nou n'est que dans capacite_stade) —
r = F("quelle est la capacité du Camp Nou ?")
check(r is not None and "105 000" in r and "stade" in r and "Camp Nou" in r,
      "capacité du Camp Nou -> 105 000 places (lecture stade, servie nette)")
check(r is not None and "salle" not in r and "réservoir" not in r,
      "les lectures NON ancrées ne polluent pas la réponse nette")

# — lectures multiples, MÊME valeur -> concordance DITE (arènes de Malaga : stade ET salle, 9 032) —
r = F("capacité des arènes de Malaga")
check(r is not None and "9 032" in r and "concordent" in r and "stade" in r and "salle" in r,
      "arènes de Malaga (stade ET salle, même valeur) -> concordance DITE en un seul coup")

# — réservoir : unité m³ (volume, pas des places) —
r = F("quelle est la capacité de l'Akkajaure ?")
check(r is not None and "m³" in r and "5 900 000 000" in r,
      "capacité de l'Akkajaure -> 5 900 000 000 m³ (lecture réservoir, unité juste)")

# — divergence : valeurs DIFFÉRENTES -> les lectures listées, jamais « la première trouvée » (candidats réels
#   synthétiques via compose : la vraie divergence création vit dans la base complète — validée e2e .exe) —
c1 = T.Candidat(intention=T.INTERROGER_FAIT, entites=("Acapulco",), relation="année de création de l'œuvre",
                statut=T.TRANCHE, reponse="Année de création de l'œuvre « Acapulco » : 1978.",
                ancrage="lookup vérifié", confiance=0.9)
c2 = T.Candidat(intention=T.INTERROGER_FAIT, entites=("Acapulco",), relation="année de création de l'organisation",
                statut=T.TRANCHE, reponse="Année de création de l'organisation « Acapulco » : 1520.",
                ancrage="lookup vérifié", confiance=0.9)
r = T.compose(T.Faisceau((c1, c2)), terme="création de Acapulco")
check(r is not None and "1978" in r and "1520" in r and "plusieurs choses" in r,
      "divergence (1978 vs 1520) -> les DEUX lectures servies conditionnellement, invitation à préciser")

# — repli multi-mots : « année de création de X » / « capacité d'accueil de X » routent la même tête —
_p = R._normalise("année de création de la Croix-Rouge")
for _rx, _canon in R._TETE_POLY_PHRASES:
    _p = _rx.sub(_canon, _p)
_m = R._TETE_POLY_RE.match(_p.strip())
check(_m is not None and _m.group(1) == "creation" and "croix" in _m.group(2),
      "« année de création de X » -> replié sur la tête création (regex + phrases)")
check(F("année de création de la Croix-Rouge") is None,
      "tables création absentes de l'échantillon -> None honnête (jamais inventé)")
r = F("capacité d'accueil du Camp Nou")
check(r is not None and "105 000" in r, "« capacité d'accueil » -> replié sur la tête capacité, servie")

# — zéro capture (les voisines ne sont JAMAIS prises) —
for q in ("capacité thermique molaire du cuivre",       # tête composée != capacité nue
          "capacité d'adaptation des plantes",           # concept, pas une entité de table
          "la création du monde",                        # hors tables -> None
          "création de valeur en entreprise",
          "quelle est la capitale de la France ?"):
    check(F(q) is None, "hors périmètre : %r -> None" % q)

# — entité inconnue -> None (cascade inchangée, jamais un voisin deviné) —
check(F("capacité du stade Imaginarium-4242") is None, "entité inconnue -> None")

print("=== valide_tete_polysemique : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
