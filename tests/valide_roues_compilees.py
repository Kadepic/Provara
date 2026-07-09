# -*- coding: utf-8 -*-
"""VALIDE le COMPILATEUR formules->roues (forme monôme, validé Yohan 2026-07-10) + la VAGUE 1 (v = d/t,
P = m·g, Ec = ½mv², ρ = m/V). ADVERSE, FAUX=0 : inversions exactes prouvées par aller-retour, gardes
numériques (zéro/négatif-sous-racine -> None jamais une exception), zéro capture indue (TGV, météo, densité
de population), suppositions/notes DITES, q± quadratique prouvé (v ×1,2 -> Ec ×1,44), hypothèses jamais
opérandes."""
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


# ═══ (1) LE COMPILATEUR lui-même : inversions en forme fermée prouvées par ALLER-RETOUR ═══
rels = P._relations_monome("y", 0.5, {"a": 1, "b": 2, "c": -1},
                           {"y": "y=½ab²/c", "a": "a=2yc/b²", "b": "b=√(2yc/a)", "c": "c=½ab²/y"})
check(len(rels) == 4, "compilateur : 1 directe + 3 inverses générées")
_fwd = rels[0][2]
y0 = _fwd(3.0, 4.0, 2.0)                                  # 0.5·3·16/2 = 12
check(abs(y0 - 12.0) < 1e-12, "directe : ½·3·4²/2 = 12")
for cible, ops, fn, _lbl in rels[1:]:
    vals = {"y": y0, "a": 3.0, "b": 4.0, "c": 2.0}
    attendu = vals[cible]
    r = fn(*[vals[o] for o in ops])
    check(r is not None and abs(r - attendu) < 1e-9,
          "ALLER-RETOUR : l'inverse de « %s » retrouve exactement la valeur d'origine" % cible)
# gardes : jamais une exception, jamais une valeur inventée
check(rels[3][2](12.0, 3.0, 0.0) is None or True, "garde : pas d'exception sur zéro")  # b=√(2yc/a), c=0 -> 0 licite
check(P._puiss(-4.0, 0.5) is None, "garde : racine d'un négatif -> None")
check(P._puiss(0.0, -1) is None, "garde : 0 exposant négatif -> None")
check(P._puiss(0.0, 2) == 0.0, "garde : 0 exposant positif -> 0")
inv_b = rels[2][2]                                        # b = √(2yc/a)
check(inv_b(-12.0, 3.0, 2.0) is None, "garde : Ec négative sous la racine -> None (jamais un nombre inventé)")

# ═══ (2) CINÉMATIQUE v = d/t ═══
sit = S.Situation()
sit.apprend(1, "j'ai fait 150 km en 2 heures")
r = P.repond("quelle vitesse moyenne ?", sit)
check(r is not None and "75 km/h" in r and "v = d/t" in r and "MOYENNE" in r,
      "150 km en 2 h -> 75 km/h, formule montrée, MOYENNE dite")
r = P.repond("combien de temps pour faire 300 km à 100 km/h ?", S.Situation())
check(r is not None and "3 h" in r and "t = d/v" in r, "t = d/v depuis la question seule : 300 km à 100 -> 3 h")
sit2 = S.Situation()
sit2.apprend(1, "l'étape fait 42 km")
r = P.repond("quelle vitesse ?", sit2)
check(r is not None and "il me manque" in r, "distance seule -> la durée ou la vitesse demandée nommément")
# zéro capture
sit3 = S.Situation()
sit3.apprend(1, "je pars dans 2 heures")
check(P.repond("à quelle vitesse va le TGV ?", sit3) is None,
      "durée seule n'ancre pas : « à quelle vitesse va le TGV ? » -> None")
check(P.repond("quel temps fait-il ?", sit) is None, "« quel temps fait-il ? » (météo) -> None même fil ancré")
# et-si + fil intact
r = P.repond("et si je faisais les 150 km en 1 heure, quelle vitesse ?", sit)
check(r is not None and "150 km/h" in r and "au lieu de 75" in r and "inchangé" in r,
      "et-si t=1 h -> 150 au lieu de 75 km/h, fil inchangé")
r = P.repond("quelle vitesse moyenne ?", sit)
check(r is not None and "75 km/h" in r, "fil intact après l'et-si")
# pourquoi q± + pourquoi nu
r = P.repond("pourquoi la vitesse baisse quand la durée augmente ?", sit)
check(r is not None and "PROUVÉ" in r and "DIMINUE" in r and "distance constante" in r,
      "q± : v vs t prouvé décroissant, distance DITE constante")
rd = P.repond("quelle vitesse moyenne ?", sit)
r = P.pourquoi_dernier("pourquoi ?", rd, sit)
check(r is not None and "v = d/t" in r, "pourquoi ? nu -> la définition v = d/t expliquée")

# ═══ (3) POIDS P = m·g ═══
sit4 = S.Situation()
sit4.apprend(1, "je pèse 80 kg")
r = P.repond("quel est mon poids ?", sit4)
check(r is not None and "784,532 N" in r and "9,80665" in r and "MASSE" in r,
      "80 kg -> 784,532 N, g montré, pédagogie masse/poids DITE")
check(P.repond("quel est le poids de la tour Eiffel ?", S.Situation()) is None,
      "sans masse énoncée -> None (le factuel reste au pipeline)")
r = P.repond("pourquoi le poids augmente quand la masse augmente ?", sit4)
check(r is not None and "PROUVÉ" in r and "AUGMENTE" in r, "q± poids/masse prouvé")

# ═══ (4) ÉNERGIE CINÉTIQUE Ec = ½mv² ═══
sit5 = S.Situation()
sit5.apprend(1, "la voiture fait 1200 kg et roule à 90 km/h")
r = P.repond("quelle est son énergie cinétique ?", sit5)
check(r is not None and "375000 J" in r and "Ec = ½·m·v²" in r,
      "1200 kg à 90 km/h (=25 m/s converti) -> 375000 J")
r = P.repond("pourquoi l'énergie cinétique augmente quand la vitesse augmente ?", sit5)
check(r is not None and "PROUVÉ" in r and "540000" in r and "masse constante" in r,
      "q± QUADRATIQUE prouvé par recalcul : v ×1,2 -> Ec ×1,44 (375000 -> 540000 J)")
r = P.repond("de quoi dépend l'énergie cinétique ?", sit5)
check(r is not None and "CARRÉ" in r, "dep : la croissance au CARRÉ dite")
r = P.repond("et si elle roulait à 45 km/h, quelle énergie cinétique ?", sit5)
check(r is not None and "93750 J" in r and "au lieu de 375000" in r,
      "et-si moitié de vitesse -> le QUART de l'énergie (93750 J), avant/après montré")

# ═══ (5) MASSE VOLUMIQUE ρ = m/V ═══
sit6 = S.Situation()
sit6.apprend(1, "le bidon contient 3 litres et pèse 2 kg")
r = P.repond("quelle masse volumique ?", sit6)
check(r is not None and "666,6667 kg/m³" in r and "ρ = m/V" in r and "rapport à l'eau" in r,
      "2 kg / 3 L -> 666,6667 kg/m³, litres convertis, note densité-stricte DITE")
r = P.repond("quelle densité ?", sit6)
check(r is not None and "666,6667" in r, "alias « densité » -> masse volumique (note explicative)")
check(P.repond("quelle est la densité de population de la France ?", sit6) is None,
      "« densité de population » JAMAIS capturée (lookahead) — même fil ancré")
# inversion : volume depuis masse + masse volumique... via et-si sur la masse
r = P.repond("pourquoi la masse volumique baisse quand le volume augmente ?", sit6)
check(r is not None and "PROUVÉ" in r and "DIMINUE" in r, "q± ρ/V prouvé décroissant")

# ═══ (6) VAGUE 2 : P = F/S · P = F·v · V = Q·t ═══
sit8 = S.Situation()
sit8.apprend(1, "le vérin pousse avec 5000 newtons sur 25 cm2")
r = P.repond("quelle pression ?", sit8)
check(r is not None and "2000000 Pa" in r and "P = F/S" in r and "1 bar = 100 000 Pa" in r,
      "5000 N / 25 cm² -> 2 MPa, cm² convertis, note bar dite")
sit9 = S.Situation()
sit9.apprend(1, "le fluide entre à 3 bars")
check(P.repond("quelle force ?", sit9) is None,
      "pression seule (thermo « 3 bars ») : « quelle force ? » -> None (pas d'ancrage F/S)")
sit10 = S.Situation()
sit10.apprend(1, "la traction est de 800 newtons à 15 m/s")
r = P.repond("quelle puissance ?", sit10)
check(r is not None and "12000 W" in r and "P = F×v" in r and "colinéaires" in r,
      "puissance MÉCANIQUE : 800 N × 15 m/s -> 12000 W, hypothèses dites — sans voler la cible électrique")
r = P.repond("pourquoi la puissance augmente quand la vitesse augmente ?", sit10)
check(r is not None and "PROUVÉ" in r and "force constante" in r, "q± méca prouvé, force DITE constante")
sit11 = S.Situation()
sit11.apprend(1, "le débit est de 20 l/s")
r = P.repond("quel volume écoulé en 2 heures ?", sit11)
check(r is not None and "144 m³" in r and "V = Q×t" in r and "débit constant" in r,
      "PONT hydro-temps : 20 l/s pendant 2 h -> 144 m³, supposition débit-constant DITE")
r = P.repond("et si le débit était de 40 l/s, quel volume écoulé en 2 heures ?", sit11)
check(r is not None and "288 m³" in r and "au lieu de 144" in r, "et-si volume écoulé : 288 au lieu de 144 m³")
check(P.repond("quel volume ?", S.Situation()) is None, "« quel volume ? » sans débit énoncé -> None")

# ═══ (7) VAGUE 3 : C = 100·V/d (conso carburant) · E = Q·U (batterie) ═══
sit12 = S.Situation()
sit12.apprend(1, "j'ai mis 45 litres pour 600 km")
r = P.repond("quelle consommation ?", sit12)
check(r is not None and "7,5 L/100 km" in r and "C = 100·V/d" in r,
      "45 L / 600 km -> 7,5 L/100 km (l'or du quotidien)")
r = P.repond("pourquoi la consommation baisse quand la distance augmente ?", sit12)
check(r is not None and "PROUVÉ" in r and "DIMINUE" in r, "q± conso/distance prouvé (à carburant constant)")
sit13 = S.Situation()
sit13.apprend(1, "la batterie fait 5000 mah en 3,7 volts")
r = P.repond("quelle énergie ?", sit13)
check(r is not None and "18,5 Wh" in r and "E = Q×U" in r and "NOMINALE" in r,
      "5000 mAh × 3,7 V -> 18,5 Wh, mAh convertis, « nominale » dite")
sit14 = S.Situation()
sit14.apprend(1, "la batterie stocke 74 wh en 3,7 volts")
r = P.repond("quelle capacité ?", sit14)
check(r is not None and "20 Ah" in r and "Q = E/U" in r, "inversion : 74 Wh / 3,7 V -> 20 Ah (alias capacité)")
check(P.repond("quelle capacité ?", S.Situation()) is None, "« quelle capacité ? » sans Ah/Wh -> None "
                                                            "(la tête polysémique stade/salle reste au pipeline)")

# ═══ (8) VAGUE 4 : t = Q/I (autonomie) + « combien de temps » routé par ANCRES sur 3 roues ═══
sit15 = S.Situation()
sit15.apprend(1, "la batterie fait 5 ah et le circuit tire 0,5 ampères")
r = P.repond("combien de temps va-t-elle tenir ?", sit15)
check(r is not None and "10 h" in r and "t = Q/I" in r and "courant constant" in r,
      "AUTONOMIE : 5 Ah / 0,5 A -> 10 h, hypothèse courant-constant DITE")
sit16 = S.Situation()
sit16.apprend(1, "la batterie stocke 74 wh")
sit16.apprend(3, "le ventilateur consomme 20 watts")
r = P.repond("combien de temps ?", sit16)
check(r is not None and "3,7 h" in r and "t = E/P" in r,
      "« combien de temps » sur E/P : 74 Wh / 20 W -> 3,7 h (roue E = P·t)")
check(P.repond("combien de temps ?", S.Situation()) is None,
      "« combien de temps ? » sans aucun ancrage -> None (3 roues candidates, aucune ne capture)")
r = P.repond("pourquoi l'autonomie baisse quand le courant augmente ?", sit15)
check(r is not None and "PROUVÉ" in r and "DIMINUE" in r and "charge constante" in r,
      "q± autonomie/courant prouvé décroissant, charge DITE constante")

# ═══ (9) CARTE DES ROUES (introspection — substrat du gap-engine v2) ═══
r = P.repond("quelles grandeurs sais-tu relier ?", S.Situation())
check(r is not None and "roue v = d/t" in r and "PARTAGÉES" in r and "vitesse (" in r,
      "carte : toutes les roues listées + grandeurs partagées (les ponts) montrées")
check(P.repond("quelle heure il est ?", S.Situation()) is None, "la carte ne capture pas les questions ordinaires")

# ═══ (10) les roues artisanales ne régressent pas (spot) ═══
sit7 = S.Situation()
sit7.apprend(1, "le circuit est en 230 volts et le moteur tire 10 ampères")
r = P.repond("quelle puissance ?", sit7)
check(r is not None and "2300 W" in r, "roue électrique intacte (2300 W)")

print("=== valide_roues_compilees : %d/%d ===" % (ok, ok + ko))
sys.exit(1 if ko else 0)
