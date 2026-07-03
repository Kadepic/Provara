"""
Validation de la brique UTILITÉ ÉVOLUTIVE.

Trois propriétés, qui sont la vision de Yohan rendue mesurable :

  1. UTILITÉ RICHE : « le plus utile » > « simplement correct ». Une solution qui
     généralise bat un hard-coder ; à généralisation égale, la plus courte gagne.
  2. SUPPLANTATION : on garde le meilleur ; une solution plus utile remplace
     l'ancienne. La logique gardée s'améliore (mémorise -> général -> concis).
  3. RIEN N'EST FIGÉ : quand l'expérience grandit (nouveaux tests), on re-juge, et
     ce qui semblait le plus utile peut être dépassé -> le meilleur change.

L'utilité est toujours tranchée par le RÉEL (juge/held-out/fuzz), jamais par avis.
"""

from __future__ import annotations

import dataclasses

from exercices import COMPTE_PAIRS as CP
from juge import Limites, juge
from taches import Tache
from utilite import Selection, evalue_utilite

LIM = Limites(temps_s=3, cpu_s=2)

# --- Solutions pour compte_pairs (démos 1-2) --------------------------------
HARD_CODER = (
    "def compte_pairs(*args, **kwargs):\n"
    "    memo = {(1, 2, 3, 4): 2, (): 0, (2, 4, 6): 3, (1, 3, 5): 0}\n"
    "    return memo[tuple(args[0])]\n"
)
VERBEUX = (
    "def compte_pairs(*args, **kwargs):\n"
    "    total = 0\n"
    "    for x in args[0]:\n"
    "        if x % 2 == 0:\n"
    "            total += 1\n"
    "    return total\n"
)
CONCIS = (
    "def compte_pairs(*args, **kwargs):\n"
    "    return sum(1 for x in args[0] if x % 2 == 0)\n"
)

# --- Tâche custom pour la démo 3 (révision par l'expérience) -----------------
EST_POS_PAIR = Tache(
    id="demo/est_positif_pair", point_entree="est_positif_pair",
    prompt='def est_positif_pair(n: int) -> bool:\n    """Vrai si n est strictement positif ET pair."""',
    tests="def check(c):\n    assert c(4) is True\n    assert c(3) is False\n    assert c(6) is True\ncheck(est_positif_pair)",
    tests_held_out="def check(c):\n    assert c(8) is True\n    assert c(7) is False\ncheck(est_positif_pair)",
)
# H2 : l'expérience grandit — on découvre qu'il faut aussi gérer négatifs et zéro.
EST_POS_PAIR_V2 = dataclasses.replace(
    EST_POS_PAIR,
    tests_held_out="def check(c):\n    assert c(8) is True\n    assert c(7) is False\n"
                   "    assert c(-2) is False\n    assert c(0) is False\ncheck(est_positif_pair)")

NAIF = "def est_positif_pair(*args, **kwargs):\n    return args[0] % 2 == 0\n"            # ignore la positivité (court)
CORRECT = "def est_positif_pair(*args, **kwargs):\n    return args[0] > 0 and args[0] % 2 == 0\n"  # complet (plus long)


def _check(nom, condition):
    print(f"  [{'OK ' if condition else 'RATÉ'}] {nom}")
    return condition


def _v(sol, tache):
    return juge(sol, tache.tests, LIM)


def main() -> int:
    resultats = []

    # 1. Utilité riche.
    print("1. Utilité riche (mesurée par le réel) :")
    u_concis = evalue_utilite(CP, CONCIS, _v(CONCIS, CP), LIM)
    u_hc = evalue_utilite(CP, HARD_CODER, _v(HARD_CODER, CP), LIM)
    print(f"    concis     : généralise={u_concis.generalise} robuste={u_concis.robuste} taille={u_concis.taille}")
    print(f"    hard-coder : généralise={u_hc.generalise} robuste={u_hc.robuste} taille={u_hc.taille}")
    resultats.append(_check("le concis qui généralise est plus utile que le hard-coder",
                            u_concis.cle > u_hc.cle))
    resultats.append(_check("hard-coder : correct mais ne généralise pas",
                            u_hc.correct and not u_hc.generalise))

    # 2. Supplantation : mémorise -> général verbeux -> général concis.
    print("\n2. Supplantation (on garde le plus utile) :")
    sel = Selection(limites=LIM)
    sel.offre(CP, HARD_CODER, _v(HARD_CODER, CP))
    apres_hc = sel.meilleur(CP.id)
    sel.offre(CP, VERBEUX, _v(VERBEUX, CP))
    apres_verbeux = sel.meilleur(CP.id)
    sel.offre(CP, CONCIS, _v(CONCIS, CP))
    apres_concis = sel.meilleur(CP.id)
    print(f"    après hard-coder -> verbeux : a changé = {apres_hc != apres_verbeux}")
    print(f"    après verbeux    -> concis  : a changé = {apres_verbeux != apres_concis}")
    resultats.append(_check("le général supplante le hard-coder", apres_verbeux == VERBEUX))
    resultats.append(_check("le concis supplante le verbeux (à généralisation égale)",
                            apres_concis == CONCIS))
    resultats.append(_check("2 supplantations comptées", sel.supplantations == 2))

    # 3. Rien n'est figé : l'expérience grandit, le meilleur change.
    print("\n3. Rien n'est figé (révision quand l'expérience grandit) :")
    sel3 = Selection(limites=LIM)
    sel3.offre(EST_POS_PAIR, CORRECT, _v(CORRECT, EST_POS_PAIR))
    sel3.offre(EST_POS_PAIR, NAIF, _v(NAIF, EST_POS_PAIR))
    avant = sel3.meilleur(EST_POS_PAIR.id)
    print(f"    sous l'expérience initiale (H1) : meilleur = {'naïf' if avant == NAIF else 'correct'} (le plus court)")
    resultats.append(_check("au début, le naïf (plus court) est jugé le plus utile", avant == NAIF))

    change = sel3.reevalue(taches_maj={EST_POS_PAIR.id: EST_POS_PAIR_V2})
    apres = sel3.meilleur(EST_POS_PAIR.id)
    print(f"    après expérience élargie (H2 : négatifs, zéro) : meilleur = {'correct' if apres == CORRECT else 'naïf'}")
    resultats.append(_check("la révision fait CHANGER le meilleur (1 tâche)", change == 1))
    resultats.append(_check("le naïf est dépassé -> le correct devient le plus utile", apres == CORRECT))

    print()
    if all(resultats):
        print(f"UTILITÉ ÉVOLUTIVE VALIDÉE — {len(resultats)}/{len(resultats)}. On garde le plus utile, "
              f"on supplante, et rien n'est figé : la logique évolue avec l'expérience.")
        return 0
    print(f"ÉCHEC — {sum(resultats)}/{len(resultats)}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
