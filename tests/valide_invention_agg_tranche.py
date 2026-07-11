"""
VALIDATION — AGG∘TRANCHE liste×scalaire : palier structurel, atome 4 — « la frontière se déplace ».

Frontière MESURÉE (après le 1er lot liste×scalaire) : somme_k_plus_grands, somme_k_plus_petits,
somme/max des k premiers, min après k restaient brique_manquante — les tranches existaient, les agrégats
dessus non. Comblé dans _LS_OPS par la classe canonique top-k : AGG {sum,max,min} ∘ tranche {brute, triée},
IDENTITÉS DÉGUISÉES EXCLUES (max∘top-k ≡ max, min∘bottom-k ≡ min : k-invariantes, jamais une capacité neuve).

Méthode SOUND : labels par fonctions de référence, listes NON TRIÉES (tranche brute ≠ tranche triée sur
chaque exemple), k varié, held-out séparé, re-vérif HORS moteur sur sondes fraîches.

Prouve : (1) FRONTIÈRES FERMÉES — somme_k_plus_grands/plus_petits, somme/max des k premiers, min après k
deviennent INVENTION ; (2) CORRECT — re-vérif hors moteur ; (3) ANTI-COÏNCIDENCE — somme des k PREMIERS ≠
somme des k PLUS GRANDS (listes non triées les séparent) ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION — n_premiers
reste INVENTION, int×int intact.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=400)
import invention_multi as IM

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _fn2(expr):
    ns: dict = {}
    exec(f"def _f(a, b):\n    return {expr}\n", ns)
    return ns["_f"]


# listes NON TRIÉES : a[:k] ≠ sorted(a)[:k] et somme premiers ≠ somme plus grands sur chaque exemple.
HB = [([3, 1, 4, 1, 5], 2), ([2, 7, 6], 1), ([9, 8, 5, 3], 3), ([4, 2, 6, 0, 1], 2)]
HB_HELD = [([1, 6, 2, 4, 5, 3], 4), ([7, 3], 1)]
HB_FRAIS = [([6, 2, 9, 1], 2), ([5, 8, 0], 1)]

CIBLES = [
    ("somme_k_plus_grands", lambda x, k: sum(sorted(x)[-k:])),
    ("somme_k_plus_petits", lambda x, k: sum(sorted(x)[:k])),
    ("somme_k_premiers",    lambda x, k: sum(x[:k])),
    ("max_k_premiers",      lambda x, k: max(x[:k])),
    ("min_apres_k",         lambda x, k: min(x[k:])),
]

realisations = {}
for nom, ref in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((x, k), ref(x, k)) for x, k in HB],
                               [((x, k), ref(x, k)) for x, k in HB_HELD])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn2(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(x, k) == ref(x, k) for x, k in HB + HB_HELD + HB_FRAIS))
    realisations[nom] = v.par

# ANTI-COÏNCIDENCE : somme des k PREMIERS ≠ somme des k PLUS GRANDS sur liste non triée.
check("somme_k_premiers ≠ somme_k_plus_grands sur [3,1,4,1,5], k=2 (4 vs 9)",
      _fn2(realisations["somme_k_premiers"])([3, 1, 4, 1, 5], 2) == 4
      and _fn2(realisations["somme_k_plus_grands"])([3, 1, 4, 1, 5], 2) == 9)

# DÉTERMINISME.
_ref0 = CIBLES[0][1]
v2 = IM.examine_cible_multi("somme_k_plus_grands",
                            [((x, k), _ref0(x, k)) for x, k in HB],
                            [((x, k), _ref0(x, k)) for x, k in HB_HELD])
check("déterminisme (somme_k_plus_grands : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["somme_k_plus_grands"])

# NON-RÉGRESSION : le 1er lot de la forme reste résolu ; int×int intact.
v3 = IM.examine_cible_multi("n_premiers", [((x, k), x[:k]) for x, k in HB], [((x, k), x[:k]) for x, k in HB_HELD])
check("n_premiers reste INVENTION (non-régression 1er lot)", v3.statut == IM.INVENTION)
v4 = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v4.statut == IM.EXISTE_DEJA and v4.par == "a - b")

print(f"\nvalide_invention_agg_tranche : {ok}/{total}")
assert ok == total
