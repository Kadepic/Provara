# -*- coding: utf-8 -*-
"""VALIDE le pont HYDRAULIQUE (roue Q = S·v — 2e instance du moteur de roues générique, 2026-07-09 jour).
FAUX=0 : valeurs vérifiées contre calcul indépendant, dérivation MONTRÉE, manquant DEMANDÉ NOMMÉMENT,
hypothèses jamais opérandes, débit MASSIQUE (kg/s) jamais opérande de Q = S·v, vitesse seule n'ancre pas
(une voiture roule aussi), q± prouvé par recalcul 2 points aux données énoncées."""
from __future__ import annotations

import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__)) or "."
sys.path.insert(0, os.path.join(os.path.dirname(_ICI), "src"))

import situation as S
import pont_grandeurs as P

ok = ko = 0


def check(c, label):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print("  FAIL: " + label)


# — S et v énoncés -> Q fermé, dérivation montrée, conversion cm² -> m² —
sit = S.Situation()
sit.apprend(1, "la conduite a une section de 50 cm2 et l'eau s'écoule à 2 m/s")
r = P.repond("quel est le débit ?", sit)
check(r is not None and "0,01 m³/s" in r and "Q = S×v" in r and "0,005 m²" in r,
      "S=50 cm², v=2 m/s -> Q = 0,01 m³/s, chemin Q = S×v montré, cm² convertis")

# — Q et S énoncés -> v ; Q et v -> S (l/s convertis) —
sit2 = S.Situation()
sit2.apprend(1, "le débit est de 20 l/s dans une conduite de 100 cm2")
r = P.repond("quelle est la vitesse de l'eau ?", sit2)
check(r is not None and "2 m/s" in r and "v = Q/S" in r, "Q=20 l/s, S=100 cm² -> v = 2 m/s")
sit3 = S.Situation()
sit3.apprend(1, "le débit vaut 20 l/s et l'eau file à 2 m/s")
r = P.repond("quelle section ?", sit3)
check(r is not None and "0,01 m²" in r and "S = Q/v" in r, "Q=20 l/s, v=2 m/s -> S = 0,01 m²")

# — dernière valeur fait foi (autorité utilisateur) —
sit2.apprend(3, "en fait le débit est de 40 l/s")
r = P.repond("quelle vitesse ?", sit2)
check(r is not None and "4 m/s" in r, "ré-énoncé 20->40 l/s : v recalculée = 4 m/s")

# — manquant -> demandé NOMMÉMENT —
sit4 = S.Situation()
sit4.apprend(1, "la conduite fait 100 cm2 de section")
r = P.repond("quel débit ?", sit4)
check(r is not None and "il me manque" in r and ("m³/s" in r or "vitesse" in r),
      "S seule -> le débit ou la vitesse demandés nommément")

# — débit MASSIQUE (kg/s) : même dimension du fil, PAS la même grandeur -> jamais opérande —
sit5 = S.Situation()
sit5.apprend(1, "le débit est de 5 kg/s dans la conduite de 100 cm2")
r = P.repond("quelle vitesse ?", sit5)
check(r is not None and "il me manque" in r and "≈" not in r.split("il me manque")[0],
      "kg/s massique EXCLU par table d'unités : jamais v = Q/S dessus, manquant demandé")

# — la vitesse seule n'ancre pas (une voiture roule aussi) —
sit6 = S.Situation()
sit6.apprend(1, "la voiture roule à 130 km/h")
check(P.repond("quel débit ?", sit6) is None, "vitesse seule (voiture) -> None, pas d'ancrage hydraulique")
check(P._hydraulique("quelle vitesse ?", S.Situation()) is None, "fil vide -> None (pas d'ancrage)")
sit7 = S.Situation()
sit7.apprend(1, "le fluide chaud entre à 90 degrés et sort à 50 degrés")
check(P.repond("quel débit ?", sit7) is None, "fil thermo sans débit volumique -> None")

# — hypothèse jamais opérande —
sit8 = S.Situation()
sit8.apprend(1, "la section est de 100 cm2")
sit8.apprend(3, "si le débit montait à 40 l/s, ce serait bien")
r = P.repond("quelle vitesse ?", sit8)
check(r is not None and "il me manque" in r, "débit sous « si » = hypothèse -> jamais un opérande")

# — ET-SI hydraulique : simulation avant, avant/après, fil intact —
r = P.repond("et si le débit passait à 40 l/s, quelle vitesse ?", sit2)
check(r is not None and "4 m/s" in r, "et-si sur le fil courant : re-propagé")
sit9 = S.Situation()
sit9.apprend(1, "le débit est de 20 l/s dans une conduite de 100 cm2")
r = P.repond("et si le débit passait à 40 l/s, quelle vitesse ?", sit9)
check(r is not None and "4 m/s" in r and "au lieu de 2 m/s" in r and "inchangé" in r,
      "et-si Q=40 l/s -> v = 4 m/s au lieu de 2, fil réel inchangé")
r2 = P.repond("quelle vitesse ?", sit9)
check(r2 is not None and "2 m/s" in r2, "le fil réel est intact après l'et-si hydraulique")

# — POURQUOI q± : prouvé par recalcul 2 points, constantes = les données ÉNONCÉES —
r = P.repond("de quoi dépend la vitesse ?", sit9)
check(r is not None and "v = Q/S" in r and "racines causales" in r,
      "dep vitesse (dérivée) : roue + racines causales = les données énoncées")
r = P.repond("de quoi dépend le débit ?", sit9)
check(r is not None and "Q = S·v" in r and "RACINE" in r and "directement" in r,
      "dep débit (donnée de l'utilisateur) : dit RACINE causale de SES données, jamais « je ne peux pas »")
r = P.repond("pourquoi la vitesse augmente quand le débit augmente ?", sit9)
check(r is not None and "PROUVÉ" in r and "2,4" in r and "section constante" in r,
      "dir vraie : preuve 2 points (0,02->0,024 m³/s : v 2->2,4 m/s), section DITE constante")
r = P.repond("pourquoi la vitesse baisse quand le débit augmente ?", sit9)
check(r is not None and "Ce n'est pas ce qui se passe" in r and "AUGMENTE" in r,
      "prémisse fausse -> corrigée (elle AUGMENTE), jamais validée")
sit10 = S.Situation()
sit10.apprend(1, "le débit est de 20 l/s et l'eau va à 2 m/s")
r = P.repond("pourquoi le débit baisse quand la vitesse augmente ?", sit10)
check(r is not None and "ne dépend PAS" in r and "indépendantes" in r,
      "cible = donnée de l'utilisateur (Q,v énoncés) : Q indépendant de v DANS SES DONNÉES (de Kleer)")

# — « pourquoi ? » nu sur une réponse hydraulique -> la définition Q = S·v expliquée —
rd = P.repond("quelle vitesse ?", sit9)
r = P.pourquoi_dernier("pourquoi ?", rd, sit9)
check(r is not None and "Q = S·v" in r and "DÉFINITION" in r,
      "pourquoi ? nu sur une réponse hydraulique -> la définition de la roue expliquée")

print("=== valide_pont_hydraulique : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
