"""
VALIDATION — FORME SÉQUENCE×INT×INT (invention_multi) : palier structurel, atome 14 — le ternaire STRUCTURÉ.

Frontière MESURÉE : la tranche à deux bornes a[b:c] et ses agrégats = brique_manquante à l'arité 3 (le
vocabulaire ternaire est scalaire pur). Première FORME DE TYPE à l'arité 3 — même patron que l'arité 2
(registre + générateur + sondes routés par forme, chemin int³ INCHANGÉ). Registre = la tranche (primitive
du langage, comme a[b] et d[k]) ; ops = agrégats ∘ tranche + bornes inversées. Séquence = liste OU chaîne.

Méthode SOUND : labels par fonctions de référence, listes NON TRIÉES, bornes variées (dont bornes au bord),
held-out séparé, re-vérif HORS moteur ; sondes = séquence renversée/triée, bornes ±1, bornes ÉCHANGÉES.

Prouve : (1) TRANCHE AU REGISTRE — a[b:c] reste EXISTE_DEJA (liste ET chaîne) ; (2) FRONTIÈRES FERMÉES —
somme/max/min de tranche deviennent INVENTION ; (3) CORRECT hors moteur ; (4) BORNES — l'ordre des bornes
est discriminé (sonde bornes échangées) ; (5) DÉTERMINISME ; (6) NON-RÉGRESSION — le ternaire scalaire
(mediane3) et le binaire intacts.
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


def _fn3(expr):
    ns: dict = {}
    exec(f"def _f(a, b, c):\n    return {expr}\n", ns)
    return ns["_f"]


# listes NON TRIÉES, bornes variées (dont bord 0 et fin).
T = [(([3, 1, 4, 1, 5], 1, 3),), (([2, 7, 6, 9], 0, 2),), (([9, 8, 5, 3, 2], 2, 5),)]
TH = [(([1, 6, 2, 4, 5, 3], 1, 4),)]
TF = [(([8, 0, 7, 2], 1, 3),)]

CIBLES = [
    ("somme_tranche", lambda x, i, j: sum(x[i:j])),
    ("max_tranche", lambda x, i, j: max(x[i:j])),
    ("min_tranche", lambda x, i, j: min(x[i:j])),
]

realisations = {}
for nom, ref in CIBLES:
    v = IM.examine_cible_multi(nom,
                               [((x, i, j), ref(x, i, j)) for (x, i, j), in T],
                               [((x, i, j), ref(x, i, j)) for (x, i, j), in TH])
    check(f"{nom} : frontière FERMÉE (INVENTION)", v.statut == IM.INVENTION)
    f = _fn3(v.par)
    check(f"{nom} : reproduit paires + sondes fraîches HORS moteur",
          all(f(list(x), i, j) == ref(x, i, j) for (x, i, j), in T + TH + TF))
    realisations[nom] = v.par

# TRANCHE AU REGISTRE : a[b:c] reste EXISTE_DEJA — liste ET chaîne (séquence).
_ref_t = lambda x, i, j: x[i:j]
v = IM.examine_cible_multi("tranche",
                           [((x, i, j), _ref_t(x, i, j)) for (x, i, j), in T],
                           [((x, i, j), _ref_t(x, i, j)) for (x, i, j), in TH])
check("tranche (liste) : reste EXISTE_DEJA (registre : primitive du langage)",
      v.statut == IM.EXISTE_DEJA and v.par == "a[b:c]")
S = [(("banane", 1, 4),), (("mercredi", 2, 5),), (("chat", 0, 2),)]
v = IM.examine_cible_multi("sous_chaine",
                           [((x, i, j), _ref_t(x, i, j)) for (x, i, j), in S],
                           [(("portail", 3, 6), "tai")])
check("sous_chaine (str) : reste EXISTE_DEJA (séquence)", v.statut == IM.EXISTE_DEJA and v.par == "a[b:c]")

# BORNES : l'ordre est réellement une donnée du spec — la somme est bien sur x[i:j], pas x[j:i].
check("bornes : somme_tranche([9,8,5,3,2], 2, 5) = 10 (5+3+2)",
      _fn3(realisations["somme_tranche"])([9, 8, 5, 3, 2], 2, 5) == 10
      and _fn3(realisations["somme_tranche"])([9, 8, 5, 3, 2], 5, 2) == 0)

# DÉTERMINISME.
_ref_0 = CIBLES[0][1]
v2 = IM.examine_cible_multi("somme_tranche",
                            [((x, i, j), _ref_0(x, i, j)) for (x, i, j), in T],
                            [((x, i, j), _ref_0(x, i, j)) for (x, i, j), in TH])
check("déterminisme (somme_tranche : même réalisation aux deux passes)",
      v2.statut == IM.INVENTION and v2.par == realisations["somme_tranche"])

# NON-RÉGRESSION : ternaire scalaire et binaire intacts.
v = IM.examine_cible_multi("mediane3", [((3, 1, 2), 2), ((7, 9, 8), 8), ((5, 0, 4), 4)], [((6, 2, 4), 4)])
check("int³ : mediane3 reste EXISTE_DEJA", v.statut == IM.EXISTE_DEJA)
v = IM.examine_cible_multi("difference", [((7, 2), 5), ((9, 4), 5), ((3, 1), 2)], [((10, 6), 4), ((5, 5), 0)])
check("int×int : difference reste EXISTE_DEJA (a - b)", v.statut == IM.EXISTE_DEJA and v.par == "a - b")

print(f"\nvalide_invention_tranche_ternaire : {ok}/{total}")
assert ok == total
