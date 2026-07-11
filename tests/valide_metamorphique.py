"""
VALIDATION — PROPRIÉTÉS MÉTAMORPHIQUES (chantier FORGE atome 6 ; Chen 1998, survey Segura 2016).

Le trou mesuré : le spec par paires ne voit que les entrées étiquetées. Une propriété DÉCLARÉE (exigence du
spec, pas un fait) relie f(T(x)) à f(x) SANS oracle : elle juge des entrées neuves gratuitement. Une
propriété erronée rend le moteur PLUS CONSERVATEUR (refus/frontière), jamais un faux servi : FAUX=0.

Prouve : (1) CATALOGUE sound — permutation/duplication/homogénéité jugent correctement somme/max/len/x[0],
témoin lisible, nom inconnu = ValueError (jamais ignoré en silence), custom accepté, sémantique d'erreur
(f(x) passe mais f(T(x)) erre = violation ; f muet sur x = probe muet) ; (2) TRANCHER — un AMBIGU réel se
résout en INVENTION quand la propriété tue les candidats non conformes (résolution SANS aller-retour
utilisateur), réalisation RE-VÉRIFIÉE ici même (paires + invariance, hors moteur) ; (3) DURCIR — une
propriété insatisfiable par toute réalisation connue -> BRIQUE_MANQUANTE avec témoin, AUCUN code servi ;
(4) EXISTE_DEJA durci — une capacité qui reproduit les paires mais viole l'exigence n'est PLUS un faux
EXISTE_DEJA ; (5) OPT-IN — défaut () = flux inchangé (verdicts historiques intacts) ; (6) COMPOSITION —
proprietes + tours_cegis se cumulent (le fil traverse la récursion CEGIS) ; (7) SERVABLE — câblage
ia.forge_brique(proprietes=) ; (8) DÉTERMINISME — transformations rejouables, deux passes identiques.
"""
from __future__ import annotations

import itertools
import json

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
import metamorphique as MM
import moteur_invention as MI

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _fn(expr):
    ns: dict = {}
    exec(f"def _f(x):\n    return {expr}\n", ns)
    return ns["_f"]


def _reproduit_tout(expr, paires):
    f = _fn(expr)
    for a, o in paires:
        r = f(a)
        if r != o or isinstance(r, bool) != isinstance(o, bool):
            return False
    return True


PROBES = [[9, 4, 1], [7, 5], [8, 3, 2, 1]]

# ── (1) CATALOGUE : chaque relation juge correctement, témoin lisible ────────────────────────────────────
R_PERM = MM.resoud(["invariance_permutation"])
R_DUP = MM.resoud(["invariance_duplication"])
R_HOM = MM.resoud(["homogeneite_double"])
check("catalogue : somme respecte permutation + homogénéité",
      MM.respecte(_fn("sum(x)"), R_PERM + R_HOM, PROBES) == (True, None))
okv, temoin = MM.respecte(_fn("sum(x)"), R_DUP, PROBES)
check("catalogue : somme VIOLE duplication (sum(x+x)=2·sum), témoin (nom, x, tx) lisible",
      not okv and temoin[0] == "invariance_duplication" and temoin[2] == temoin[1] + temoin[1])
check("catalogue : max respecte duplication ; len viole homogénéité",
      MM.respecte(_fn("max(x)"), R_DUP, PROBES)[0] and not MM.respecte(_fn("len(x)"), R_HOM, PROBES)[0])
okv, temoin = MM.respecte(_fn("x[0] + x[1]"), R_PERM, PROBES)
check("catalogue : x[0]+x[1] viole permutation, témoin porte l'entrée transformée",
      not okv and temoin[0] == "invariance_permutation")
try:
    MM.resoud(["propriete_inexistante"])
    check("catalogue : nom inconnu = ValueError (jamais ignoré en silence)", False)
except ValueError:
    check("catalogue : nom inconnu = ValueError (jamais ignoré en silence)", True)
# custom : T réduit la liste -> f=x[2] passe sur x mais ERRE sur T(x) = VIOLATION (l'exigence porte sur T(x)).
CUSTOM = {"nom": "tolere_troncature", "s_applique": lambda x: isinstance(x, list) and len(x) >= 3,
          "transformes": [lambda x: x[:1]], "relie": lambda y, yt: True}
check("custom : accepté, et f(T(x)) qui ERRE = violation (sémantique d'erreur sound)",
      not MM.respecte(_fn("x[2]"), MM.resoud([CUSTOM]), PROBES)[0])
check("custom : f muette sur TOUTES les entrées applicables = respect vacu (aucune affirmation)",
      MM.respecte(_fn("x[9]"), MM.resoud([CUSTOM]), PROBES) == (True, None))

# ── La cible-témoin : « somme des deux plus grands » (invariante par permutation, PAS par duplication).
NOM = "somme_deux_plus_grands"
EX = [([9, 4, 1], 13), ([7, 5], 12)]
HELD = [([8, 3, 2, 1], 11), ([6, 6, 0], 12)]

# ── (5) OPT-IN : défaut = flux inchangé ──────────────────────────────────────────────────────────────────
v0 = MI.examine_cible(NOM, "x", EX, HELD)
check("défaut : la cible-témoin reste AMBIGU (spec par paires sous-déterminé)", v0.statut == MI.AMBIGU)
check("défaut : verdict historique intact (somme_totale -> existe_deja)",
      MI.examine_cible("somme_totale", "x", [([1, 2, 3], 6), ([5], 5)],
                       [([0, 4], 4), ([2, 2], 4)]).statut == MI.EXISTE_DEJA)

# ── (2) TRANCHER : AMBIGU -> INVENTION sans aller-retour utilisateur ─────────────────────────────────────
v1 = MI.examine_cible(NOM, "x", EX, HELD, proprietes=("invariance_permutation",))
check("trancher : l'AMBIGU se résout en INVENTION via la propriété déclarée", v1.statut == MI.INVENTION)
check("trancher : la réalisation reproduit TOUTES les paires (re-vérifié hors moteur)",
      v1.par is not None and _reproduit_tout(v1.par, EX + HELD))
f1 = _fn(v1.par)
check("trancher : la réalisation est RÉELLEMENT invariante par permutation (re-vérifié hors moteur)",
      all(len({f1(list(p)) for p in itertools.permutations(a)}) == 1 for a, _ in EX + HELD))

# ── (8) DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────
v1bis = MI.examine_cible(NOM, "x", EX, HELD, proprietes=("invariance_permutation",))
check("déterminisme : deux passes rendent le même verdict et la même réalisation",
      (v1bis.statut, v1bis.par) == (v1.statut, v1.par))

# ── (3) DURCIR : propriété insatisfiable -> refus honnête avec témoin, aucun code servi ──────────────────
v2 = MI.examine_cible(NOM, "x", EX, HELD,
                      proprietes=("invariance_permutation", "invariance_duplication"))
check("durcir : exigence insatisfiable -> BRIQUE_MANQUANTE, aucun code servi",
      v2.statut == MI.BRIQUE_MANQUANTE and v2.par is None)
check("durcir : la justification porte la propriété violée et un témoin",
      "propriété déclarée" in v2.justification and "témoin" in v2.justification)

# ── (4) EXISTE_DEJA durci : reproduire les paires ne suffit plus si l'exigence est violée ────────────────
EX4, HELD4 = [([5, 1], 5), ([2, 9], 2)], [([7, 3, 0], 7)]
v3 = MI.examine_cible("premier_valeur", "x", EX4, HELD4)
check("existe_deja défaut : x[0] (« premier ») couvre les paires", v3.statut == MI.EXISTE_DEJA)
v4 = MI.examine_cible("premier_valeur", "x", EX4, HELD4, proprietes=("invariance_permutation",))
check("existe_deja durci : la capacité violante n'est PLUS servie (refus honnête)",
      v4.statut != MI.EXISTE_DEJA and v4.par is None)

# ── (6) COMPOSITION : proprietes traverse la récursion CEGIS (atomes 3 + 6 cumulés) ──────────────────────
vc = MI.examine_cible("somme_sup_seuil", "x", [([1, 12], 12), ([2, 12, 1], 12)],
                      [([5, 6, 1], 6), ([5, 6, 7], 13), ([1, 2, 3], 0)],
                      tours_cegis=2, proprietes=("invariance_permutation",))
check("composition : CEGIS + propriété -> INVENTION tracée CEGIS, réalisation invariante",
      vc.statut == MI.INVENTION and "CEGIS" in vc.justification
      and all(len({_fn(vc.par)(list(p)) for p in itertools.permutations(a)}) == 1 for a in ([5, 6, 1], [1, 12])))

# ── (7) SERVABLE : câblage ia.forge_brique(proprietes=) ──────────────────────────────────────────────────
fa = ia.forge_brique(NOM, "x", EX, HELD, proprietes=("invariance_permutation",))
check("forge_brique : trancher servi (invention + code + JSON-sérialisable)",
      fa["statut"] == MI.INVENTION and fa["code"] and isinstance(json.dumps(fa, ensure_ascii=False), str))
fb = ia.forge_brique(NOM + "_dup", "x", EX, HELD,
                     proprietes=("invariance_permutation", "invariance_duplication"))
check("forge_brique : durcir servi (brique_manquante, aucun code)",
      fb["statut"] == MI.BRIQUE_MANQUANTE and fb["code"] is None)

print(f"\n== VALIDE_METAMORPHIQUE : {ok}/{total} ==")
assert ok == total
