"""
VALIDE configuration_electronique.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (faits de spectroscopie / valeurs classiques, écrites EN DUR, jamais
recalculées par le module testé) :
  • H Z=1 -> '1s1' ; He Z=2 -> '1s2' ; C Z=6 -> '1s2 2s2 2p2' ; Ne Z=10 -> '1s2 2s2 2p6' (spectroscopie).
  • Fe Z=26 -> [Ar] 3d6 4s2 (6 électrons d — fait mesuré, à la base du magnétisme du fer).
  • EXCEPTIONS mesurées (NIST ASD) : Cr Z=24 -> 3d5 4s1 (PAS 3d4 4s2) ; Cu Z=29 -> 3d10 4s1 ;
    Mo Z=42 -> [Kr] 4d5 5s1 ; Pd Z=46 -> [Kr] 4d10, couche 5s VIDE ; Ag Z=47 -> [Kr] 4d10 5s1 ;
    Au Z=79 -> [Xe] 4f14 5d10 6s1 ; Ac Z=89 -> [Rn] 6d1 7s2 (²D3/2, PAS 5f1 — analogue de La).
  • EXHAUSTIVITÉ du catalogue : la liste NIST ASD COMPLÈTE des anomalies d'Aufbau pour Z<=103 compte
    20 éléments (24, 29, 41, 42, 44, 45, 46, 47, 57, 58, 64, 78, 79, 89, 90, 91, 92, 93, 96, 103) —
    écrite EN DUR ici et comparée à l'ensemble exact des Z où statut(Z) = 'exception mesurée'.
  • INVARIANT FORT : pour tout Z de 1 à 118, la somme des électrons de la chaîne rendue vaut Z — vérifié par
    un SECOND chemin de code : un parseur regex ÉCRIT ICI, dans la gate, qui reparse la chaîne caractère par
    caractère (indépendant de la mécanique interne du module).
  • Gaz rares 10, 18, 36, 54, 86 : couche p externe PLEINE (2p6, 3p6, 4p6, 5p6, 6p6 — sous-couches écrites
    en dur, fait classique ; He exempt).

SOUNDNESS : Z=0, Z=119, Z<0, bool, float (même entier), str, None, NaN, inf -> ValueError, pour CHAQUE
fonction publique. DÉTERMINISME : double appel, égalité exigée.
"""
import math
import re

import configuration_electronique as CE

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def reparse(cfg):
    """SECOND chemin de code (gate, indépendant du module) : '1s2 2s2 2p6' -> [(n, l, count), ...].

    Exige que la chaîne soit EXACTEMENT une suite de blocs n∈1..7, l∈spdf, count≥1 séparés par un espace."""
    morceaux = cfg.split(" ")
    out = []
    for m in morceaux:
        g = re.fullmatch(r"([1-7])([spdf])([1-9]\d*)", m)
        if g is None:
            return None
        out.append((int(g.group(1)), g.group(2), int(g.group(3))))
    return out


CAPACITE = {"s": 2, "p": 6, "d": 10, "f": 14}  # capacités classiques, écrites en dur ici
GAZ_RARE_Z = {"He": 2, "Ne": 10, "Ar": 18, "Kr": 36, "Xe": 54, "Rn": 86}  # Z des gaz rares, en dur

# ── 1) ANCRES : configurations complètes (spectroscopie, écrites en dur) ──
check(CE.configuration(1) == "1s1", "H (Z=1) = 1s1")
check(CE.configuration(2) == "1s2", "He (Z=2) = 1s2")
check(CE.configuration(6) == "1s2 2s2 2p2", "C (Z=6) = 1s2 2s2 2p2")
check(CE.configuration(10) == "1s2 2s2 2p6", "Ne (Z=10) = 1s2 2s2 2p6")
check(CE.configuration(26) == "1s2 2s2 2p6 3s2 3p6 4s2 3d6", "Fe (Z=26) complet, ordre de remplissage")
check(CE.configuration(24) == "1s2 2s2 2p6 3s2 3p6 3d5 4s1", "Cr (Z=24) complet = ...3d5 4s1 (exception)")

# ── 2) ANCRES : notation condensée (NIST ASD, écrites en dur) ──
check(CE.configuration_condensee(26) == "[Ar] 3d6 4s2", "Fe = [Ar] 3d6 4s2")
check(CE.configuration_condensee(24) == "[Ar] 3d5 4s1", "Cr = [Ar] 3d5 4s1 (exception, PAS 3d4 4s2)")
check(CE.configuration_condensee(29) == "[Ar] 3d10 4s1", "Cu = [Ar] 3d10 4s1 (exception)")
check(CE.configuration_condensee(42) == "[Kr] 4d5 5s1", "Mo = [Kr] 4d5 5s1 (exception)")
check(CE.configuration_condensee(46) == "[Kr] 4d10", "Pd = [Kr] 4d10 (exception, aucun 5s)")
check(CE.configuration_condensee(47) == "[Kr] 4d10 5s1", "Ag = [Kr] 4d10 5s1 (exception)")
check(CE.configuration_condensee(79) == "[Xe] 4f14 5d10 6s1", "Au = [Xe] 4f14 5d10 6s1 (exception)")
check(CE.configuration_condensee(58) == "[Xe] 4f1 5d1 6s2", "Ce = [Xe] 4f1 5d1 6s2 (exception)")
check(CE.configuration_condensee(64) == "[Xe] 4f7 5d1 6s2", "Gd = [Xe] 4f7 5d1 6s2 (exception)")
check(CE.configuration_condensee(78) == "[Xe] 4f14 5d9 6s1", "Pt = [Xe] 4f14 5d9 6s1 (exception)")
check(CE.configuration_condensee(90) == "[Rn] 6d2 7s2", "Th = [Rn] 6d2 7s2 (exception, aucun 5f)")
check(CE.configuration_condensee(92) == "[Rn] 5f3 6d1 7s2", "U = [Rn] 5f3 6d1 7s2 (exception)")
check(CE.configuration_condensee(103) == "[Rn] 5f14 7s2 7p1", "Lr = [Rn] 5f14 7s2 7p1 (exception NIST)")
check(CE.configuration_condensee(89) == "[Rn] 6d1 7s2", "Ac = [Rn] 6d1 7s2 (exception NIST, ²D3/2, PAS 5f1)")
check(CE.configuration_condensee(57) == "[Xe] 5d1 6s2", "La = [Xe] 5d1 6s2 (exception, homologue d'Ac)")
# Réguliers rendus par Aufbau MAIS confirmés par la mesure (ancres indépendantes) :
check(CE.configuration_condensee(8) == "[He] 2s2 2p4", "O = [He] 2s2 2p4")
check(CE.configuration_condensee(11) == "[Ne] 3s1", "Na = [Ne] 3s1")
check(CE.configuration_condensee(20) == "[Ar] 4s2", "Ca = [Ar] 4s2")
check(CE.configuration_condensee(74) == "[Xe] 4f14 5d4 6s2", "W = [Xe] 4f14 5d4 6s2 (régulier mesuré)")
check(CE.configuration_condensee(1) == "1s1", "H condensé = 1s1 (pas de gaz rare précédent)")
check(CE.configuration_condensee(2) == "1s2", "He condensé = 1s2 (pas de gaz rare précédent)")

# ── 3) Fe : 6 électrons d (compté par le REPARSE de la gate, pas par le module) ──
fe = reparse(CE.configuration(26))
check(fe is not None and sum(c for (n, l, c) in fe if l == "d") == 6, "Fe : 6 électrons d (reparse)")
pd = reparse(CE.configuration(46))
check(pd is not None and all(n != 5 for (n, l, c) in pd), "Pd : AUCUNE sous-couche n=5 occupée (reparse)")
check("5s" not in CE.configuration(46), "Pd : la chaîne ne contient pas '5s'")
cr = reparse(CE.configuration(24))
check(cr is not None and sum(c for (n, l, c) in cr if (n, l) == (3, "d")) == 5
      and sum(c for (n, l, c) in cr if (n, l) == (4, "s")) == 1, "Cr : 3d5 et 4s1 (reparse)")
au = reparse(CE.configuration(79))
check(au is not None and sum(c for (n, l, c) in au if (n, l) == (5, "d")) == 10
      and sum(c for (n, l, c) in au if (n, l) == (6, "s")) == 1, "Au : 5d10 et 6s1 (reparse)")
ac = reparse(CE.configuration(89))
check(ac is not None and all(l != "f" or n != 5 for (n, l, c) in ac)
      and sum(c for (n, l, c) in ac if (n, l) == (6, "d")) == 1
      and sum(c for (n, l, c) in ac if (n, l) == (7, "s")) == 2,
      "Ac : 6d1 7s2 et AUCUN électron 5f (reparse — le FAUX serait [Rn] 5f1 7s2)")

# ── 4) INVARIANT FORT : somme des électrons = Z pour TOUT Z de 1 à 118 (reparse indépendant) ──
rates_somme = []
rates_capacite = []
for Z in range(1, 119):
    parts = reparse(CE.configuration(Z))
    if parts is None or sum(c for (_n, _l, c) in parts) != Z:
        rates_somme.append(Z)
    elif any(c > CAPACITE[l] for (_n, l, c) in parts) or len({(n, l) for (n, l, _c) in parts}) != len(parts):
        rates_capacite.append(Z)
check(rates_somme == [], f"somme électrons = Z pour Z=1..118 (échecs : {rates_somme})")
check(rates_capacite == [], f"capacités s2/p6/d10/f14 respectées, sous-couches uniques (échecs : {rates_capacite})")

# Même invariant sur la forme CONDENSÉE : Z(gaz rare, table en dur de la gate) + somme de la queue = Z.
rates_cond = []
for Z in range(3, 119):
    cfg = CE.configuration_condensee(Z)
    m = re.fullmatch(r"\[(He|Ne|Ar|Kr|Xe|Rn)\] (.+)", cfg)
    queue = None if m is None else reparse(m.group(2))
    if m is None or queue is None or GAZ_RARE_Z[m.group(1)] + sum(c for (_n, _l, c) in queue) != Z:
        rates_cond.append(Z)
check(rates_cond == [], f"condensé : Z(cœur) + queue = Z pour Z=3..118 (échecs : {rates_cond})")

# ── 5) Gaz rares : couche p externe PLEINE (sous-couches attendues en dur ; He exempt) ──
for (zg, p_pleine) in ((10, "2p6"), (18, "3p6"), (36, "4p6"), (54, "5p6"), (86, "6p6")):
    check(CE.configuration(zg).endswith(" " + p_pleine) or (" " + p_pleine + " ") in (CE.configuration(zg) + " "),
          f"gaz rare Z={zg} : contient {p_pleine}")

# ── 6) STATUT : exception mesurée vs règle d'Aufbau — et EXHAUSTIVITÉ du catalogue ──
# Liste NIST ASD COMPLÈTE des anomalies d'Aufbau (états fondamentaux mesurés) pour Z<=103 : 20 éléments,
# écrite EN DUR (Cr Cu Nb Mo Ru Rh Pd Ag La Ce Gd Pt Au Ac Th Pa U Np Cm Lr). Indépendante du module.
NIST_ANOMALIES = frozenset({24, 29, 41, 42, 44, 45, 46, 47, 57, 58, 64, 78, 79, 89, 90, 91, 92, 93, 96, 103})
check(len(NIST_ANOMALIES) == 20, "la liste NIST des anomalies (Z<=103) compte exactement 20 éléments")
for z_exc in sorted(NIST_ANOMALIES):
    check(CE.statut(z_exc) == "exception mesurée", f"statut(Z={z_exc}) = exception mesurée")
for z_reg in (1, 6, 26, 30, 74, 82, 88, 104, 118):
    check(CE.statut(z_reg) == "règle d'Aufbau", f"statut(Z={z_reg}) = règle d'Aufbau")
# Ensemble EXACT : ni omission (Ac jadis absent) ni excès (aucun régulier catalogué à tort ; rien >= 104).
catalogue = {Z for Z in range(1, 119) if CE.statut(Z) == "exception mesurée"}
check(catalogue == NIST_ANOMALIES,
      f"catalogue d'exceptions = liste NIST exacte (manquants : {sorted(NIST_ANOMALIES - catalogue)}, "
      f"en trop : {sorted(catalogue - NIST_ANOMALIES)})")

# ── 7) VALENCE (convention couche externe = plus grand n occupé, documentée) ──
check(CE.couche_valence(1) == 1 and CE.electrons_valence(1) == 1, "H : couche 1, 1 électron")
check(CE.couche_valence(6) == 2 and CE.electrons_valence(6) == 4, "C : couche 2, 4 électrons (classique)")
check(CE.couche_valence(11) == 3 and CE.electrons_valence(11) == 1, "Na : couche 3, 1 électron (classique)")
check(CE.couche_valence(17) == 3 and CE.electrons_valence(17) == 7, "Cl : couche 3, 7 électrons (classique)")
check(CE.couche_valence(10) == 2 and CE.electrons_valence(10) == 8, "Ne : couche 2, 8 électrons (octet)")
check(CE.couche_valence(26) == 4 and CE.electrons_valence(26) == 2, "Fe : couche 4, 2 électrons (4s2)")
check(CE.couche_valence(46) == 4 and CE.electrons_valence(46) == 18, "Pd : couche externe n=4, 18 électrons")
check(CE.couche_valence(79) == 6 and CE.electrons_valence(79) == 1, "Au : couche 6, 1 électron (6s1)")
check(CE.couche_valence(89) == 7 and CE.electrons_valence(89) == 2, "Ac : couche 7, 2 électrons (7s2)")
# Second chemin : valence recomputée par le REPARSE de la gate, pour tout Z.
rates_val = []
for Z in range(1, 119):
    parts = reparse(CE.configuration(Z))
    n_max = max(n for (n, _l, _c) in parts)
    ev = sum(c for (n, _l, c) in parts if n == n_max)
    if CE.couche_valence(Z) != n_max or CE.electrons_valence(Z) != ev:
        rates_val.append(Z)
check(rates_val == [], f"valence cohérente avec le reparse pour Z=1..118 (échecs : {rates_val})")

# ── 8) BLOC (convention Klechkowski pur / forme Lu-sous-Y, documentée) ──
check(CE.bloc(1) == "s", "H : bloc s")
check(CE.bloc(2) == "s", "He : bloc s (1s2, malgré sa colonne)")
check(CE.bloc(5) == "p", "B : bloc p")
check(CE.bloc(6) == "p", "C : bloc p")
check(CE.bloc(11) == "s", "Na : bloc s")
check(CE.bloc(20) == "s", "Ca : bloc s")
check(CE.bloc(21) == "d", "Sc : bloc d")
check(CE.bloc(26) == "d", "Fe : bloc d")
check(CE.bloc(29) == "d", "Cu : bloc d (même en exception 3d10 4s1)")
check(CE.bloc(30) == "d", "Zn : bloc d")
check(CE.bloc(31) == "p", "Ga : bloc p")
check(CE.bloc(46) == "d", "Pd : bloc d (même sans 5s)")
check(CE.bloc(55) == "s", "Cs : bloc s")
check(CE.bloc(58) == "f", "Ce : bloc f")
check(CE.bloc(71) == "d", "Lu : bloc d (forme Lu sous Y)")
check(CE.bloc(79) == "d", "Au : bloc d")
check(CE.bloc(92) == "f", "U : bloc f")
check(CE.bloc(103) == "d", "Lr : bloc d (forme Lu sous Y)")
check(CE.bloc(118) == "p", "Og : bloc p")
check(all(CE.bloc(Z) in ("s", "p", "d", "f") for Z in range(1, 119)), "bloc ∈ {s,p,d,f} pour Z=1..118")

# ── 9) SOUNDNESS — domaine de Z ──
for fn in (CE.configuration, CE.configuration_condensee, CE.electrons_valence,
           CE.couche_valence, CE.bloc, CE.statut):
    nom = fn.__name__
    check(leve(fn, 0), f"{nom}(0) -> ValueError")
    check(leve(fn, 119), f"{nom}(119) -> ValueError")
    check(leve(fn, -5), f"{nom}(-5) -> ValueError")
    check(leve(fn, True), f"{nom}(True) -> ValueError (bool refusé)")
    check(leve(fn, 26.0), f"{nom}(26.0) -> ValueError (float refusé même entier)")
    check(leve(fn, "26"), f"{nom}('26') -> ValueError")

# ── 10) SOUNDNESS — types pathologiques supplémentaires ──
check(leve(CE.configuration, False), "configuration(False) -> ValueError")
check(leve(CE.configuration, None), "configuration(None) -> ValueError")
check(leve(CE.configuration, math.nan), "configuration(NaN) -> ValueError")
check(leve(CE.configuration, math.inf), "configuration(inf) -> ValueError")
check(leve(CE.configuration, -math.inf), "configuration(-inf) -> ValueError")
check(leve(CE.configuration, 1.5), "configuration(1.5) -> ValueError")
check(leve(CE.configuration, [26]), "configuration([26]) -> ValueError")
check(leve(CE.bloc, math.nan), "bloc(NaN) -> ValueError")
check(leve(CE.electrons_valence, math.inf), "electrons_valence(inf) -> ValueError")
check(leve(CE.statut, None), "statut(None) -> ValueError")

# ── 11) DÉTERMINISME ──
check(CE.configuration(26) == CE.configuration(26), "déterminisme configuration(26)")
check(CE.configuration_condensee(79) == CE.configuration_condensee(79), "déterminisme condensée(79)")
check(CE.electrons_valence(46) == CE.electrons_valence(46), "déterminisme electrons_valence(46)")
check(CE.bloc(57) == CE.bloc(57), "déterminisme bloc(57)")
check(CE.statut(24) == CE.statut(24), "déterminisme statut(24)")

print(f"\n=== valide_configuration_electronique : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
