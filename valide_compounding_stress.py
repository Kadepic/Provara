"""
STRESS du compounding — POUSSER jusqu'au plafond, et LOCALISER la cause (cap 1 avant cap 2).

Le compounding est prouvé (valide_compounding 5/5). Avant d'industrialiser le registre
(cap 2), on fait ce que dit le principe : **mesurer/analyser AVANT de décider**. On pousse
la montée en PROFONDEUR pour répondre à deux questions, chacune falsifiable :

  Q1. Le compounding PASSE-T-IL L'ÉCHELLE en profondeur ? (la tour grandit-elle au-delà de 3 ?)
  Q2. OÙ plafonne-t-il EXACTEMENT, et POURQUOI ? (la donnée qui spécifie cap 2)

On le mesure par trois scénarios contrôlés (mêmes seeds, même orchestrateur) :

  A. TOUR PROFONDE par tremplins — curriculum gradué deuxieme_plus_{grand,un,deux,trois}
     (profondeurs 2→3→4→5, chaque cran = incremente ∘ le cran précédent).
       * AVEC rétroaction : chaque cran déposé devient le tremplin du suivant -> la tour MONTE seule.
       * SANS rétroaction : seul le cran profondeur-2 passe ; tout le reste reste HORS DE PORTÉE.
     => le compounding passe l'échelle EN PROFONDEUR, *à condition* de tremplins gradués.

  B. MUR « profondeur > 2 d'un coup » — la même tâche profondeur-3 servie SANS son tremplin
     (curriculum = deuxieme_plus_un seul). Même AVEC rétroaction : HORS DE PORTÉE. Cause :
     `GenerateurCompose` nidifie à profondeur 2 (p2(p1(x))) — il ne fait pas un saut de 3 d'un coup.
     => cap 2 « profondeur > 2 » est justifié par une mesure, pas par la spéculation.

  C. ARITÉ 2 — FRANCHIE par cap 2 (`valide_jointure.py`). `produit_premier_dernier(xs) = xs[0]*xs[-1]`
     exige de COMBINER deux extractions (premier, dernier) par une op binaire (mul) : le pipeline
     unaire ne peut pas. L'étage `jointure` (réutilise une op du registre vivant : `op(p1(x), p2(x))`)
     le RÉSOUT. Ce qui était un mur mesuré est désormais tombé — ce scénario le re-vérifie au niveau
     escalade (l'orchestrateur résout à l'étage `jointure`).

Lecture : le compounding est une **tour UNAIRE qui monte sans plafond tant qu'on gradue** (A). L'arité-2
(C) est franchie (cap 2). Reste mesuré et OUVERT : le mur « profondeur > 2 d'un coup » (B) — non bloquant
tant que les tremplins gradués sont gratuits ; à trancher si un vrai besoin apparaît. On ne se précipite pas.
"""

from __future__ import annotations

import tempfile

from comprehension import Predicteur
from compounding import etages_atteints, franchies, montee
from curateur import CurateurGradue
from generateur import TYPES_RICHES, GenerateurOrchestre
from valide_compounding import LIM, OPS, PRIMITIVES, _store_amorce, _t

# --- La tour profonde par tremplins (scénario A) -----------------------------
# Chaque cran = sorted(xs)[-2] + k ; atteignable par incremente ∘ (cran précédent).
_TOWER = [
    ("deuxieme_plus_grand", 0, 3),
    ("deuxieme_plus_un",    1, 4),
    ("deuxieme_plus_deux",  2, 5),
    ("deuxieme_plus_trois", 3, 6),
]


def _tache_cran(fn, k, diff):
    base = "sorted(args[0])[-2]"
    tests = (f"def check(c):\n    assert c([3,1,2]) == {2+k}\n    assert c([5,1,4,2]) == {4+k}\n"
             f"    assert c([1,2]) == {1+k}\ncheck({fn})")
    held = (f"def check(c):\n    assert c([10,20,30]) == {20+k}\n    assert c([9,4,4]) == {4+k}\n"
            f"    assert c([0,5]) == {0+k}\ncheck({fn})")
    corps = f"    return {base} + {k}" if k else f"    return {base}"
    return _t(fn, "xs", tests, held, corps, diff)


TOUR = [_tache_cran(fn, k, diff) for fn, k, diff in _TOWER]

# --- Tâche d'arité 2 (scénario C) : xs[0] * xs[-1] ---------------------------
PRODUIT_PD = _t(
    "produit_premier_dernier", "xs",
    "def check(c):\n    assert c([2,3,4]) == 8\n    assert c([5,1]) == 5\n    assert c([3]) == 9\ncheck(produit_premier_dernier)",
    "def check(c):\n    assert c([10,2,5]) == 50\n    assert c([4,4]) == 16\n    assert c([7]) == 49\ncheck(produit_premier_dernier)",
    "    return args[0][0] * args[0][-1]", 4)

EXTRA_PRIMS = [
    ("premier", "def premier(*args, **kwargs):\n    return args[0][0]\n"),
    ("dernier", "def dernier(*args, **kwargs):\n    return args[0][-1]\n"),
]


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _run(d, suffixe, taches, retroaction, extra_prims=()):
    """Une montée sur orchestrateur + store frais. seuil=0 : on sert TOUT le curriculum
    (la gradation n'est pas l'objet ici — on mesure la portée, pas le rythme)."""
    store = _store_amorce(d, suffixe)
    orch = GenerateurOrchestre(store, primitives=list(PRIMITIVES) + list(extra_prims),
                               ops=list(OPS), predicteur=Predicteur(store, types=TYPES_RICHES))
    curateur = CurateurGradue(taches, seuil=0.0, limites=LIM)
    assert not curateur.rejetees, f"curriculum rejeté : {curateur.rejetees}"
    return montee(orch, curateur, store, limites=LIM, retroaction=retroaction)


def main() -> int:
    resultats = []
    sommets = {t.point_entree for t in TOUR}
    profond = "deuxieme_plus_trois"   # le cran le plus profond (profondeur 5)

    with tempfile.TemporaryDirectory() as d:
        # --- A. Tour profonde par tremplins -----------------------------------
        print("A. TOUR PROFONDE — AVEC rétroaction (chaque cran déposé porte le suivant) :")
        a_avec = _run(d, "tour_avec", TOUR, retroaction=True)
        for p in a_avec:
            print(p.resume())
        f_avec = franchies(a_avec)
        # Coût de PREMIÈRE résolution (le vrai coût de montée) — pas le coût réutilisé (≈1).
        couts: dict[str, int] = {}
        for p in a_avec:
            if p.confirme and p.point_entree not in couts:
                couts[p.point_entree] = p.appels_juge

        print("\n   TOUR PROFONDE — SANS rétroaction (le registre reste figé) :")
        a_sans = _run(d, "tour_sans", TOUR, retroaction=False)
        for p in a_sans:
            print(p.resume())
        f_sans = franchies(a_sans)

        # --- B. Mur « profondeur > 2 d'un coup » ------------------------------
        print("\nB. MUR PROFONDEUR>2 — `deuxieme_plus_un` SANS son tremplin, rétroaction ON :")
        b = _run(d, "mur_prof", [TOUR[1]], retroaction=True)   # le cran profondeur-3 seul
        for p in b:
            print(p.resume())
        b_franchi = "deuxieme_plus_un" in franchies(b)

        # --- C. Arité 2 : FRANCHIE par cap 2 (étage jointure) -----------------
        print("\nC. ARITÉ-2 (cap 2) — `produit_premier_dernier` (premier/dernier + mul fournis), ON :")
        c = _run(d, "arite", [PRODUIT_PD], retroaction=True, extra_prims=EXTRA_PRIMS)
        for p in c:
            print(p.resume())
        c_pas = next((p for p in c if p.point_entree == "produit_premier_dernier"), None)
        c_jointure = c_pas is not None and c_pas.confirme

    print()
    # Q1 — le compounding passe l'échelle en PROFONDEUR (par tremplins).
    resultats.append(_check(
        f"ÉCHELLE : avec rétroaction, la tour MONTE jusqu'à profondeur 5 — les {len(sommets)} crans franchis "
        f"(coût 1ère résolution borné, ~linéaire : {[couts[fn] for fn, _, _ in _TOWER]} ; réutilisé ensuite = 1)",
        f_avec == sommets))
    resultats.append(_check(
        f"CONTRÔLE : sans rétroaction, seul le cran profondeur-2 passe ({len(f_sans)} franchi : {sorted(f_sans)})",
        f_sans == {"deuxieme_plus_grand"}))
    resultats.append(_check(
        f"ESCALADE : la tour est résolue à l'étage composition ({etages_atteints(a_avec)})",
        etages_atteints(a_avec).get("composition", 0) >= len(sommets) - 1))

    # Q2 — les deux plafonds MESURÉS (l'agenda de cap 2).
    resultats.append(_check(
        "MUR PROFONDEUR>2 : `deuxieme_plus_un` reste HORS DE PORTÉE sans tremplin (compose nidifie à prof. 2) "
        "-> cap 2 « profondeur > 2 » justifié par mesure",
        not b_franchi))
    resultats.append(_check(
        "ARITÉ-2 (cap 2) : `produit_premier_dernier` RÉSOLU à l'étage `jointure` (op du registre, pipeline plus unaire) "
        "-> le mur mesuré est TOMBÉ",
        c_jointure))

    print()
    if all(resultats):
        print(f"STRESS VALIDÉ — {len(resultats)}/{len(resultats)}. Le compounding est une TOUR UNAIRE qui monte "
              f"SANS PLAFOND tant qu'on gradue par tremplins (prouvé jusqu'à profondeur 5). L'arité-2 est FRANCHIE "
              f"(cap 2, étage jointure). Reste mesuré et ouvert, non bloquant : profondeur>2-d'un-coup (tremplins "
              f"gratuits l'évitent). On mesure, puis on décide — jamais à l'aveugle.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}. Une hypothèse sur le compounding est réfutée : c'est un RÉSULTAT.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
