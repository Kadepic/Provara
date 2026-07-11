"""
VALIDATION du CAPSTONE RÉCURSIF — phase sommeil (bibliotheque_invention.py).

Vérifie : (a) la promotion fabrique la bonne capacité nommée à partir de l'abstraction réutilisée ;
(b) l'extension est additive et idempotente ; (c) le GAIN épistémique mesuré (INVENTION -> EXISTE_DEJA) ;
(d) la GARDE de non-régression (rien cassé, aucun faux) ; (e) SOUNDNESS : PAS de promotion spurieuse
quand aucune abstraction n'est réutilisée (l'IA n'invente pas une « brique » sans preuve de réutilisation).
"""
from __future__ import annotations

from garde_ressources import borne
import moteur_invention as MI
import chercheur_invention as C
import bibliotheque_invention as B

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


CORPUS = [
    ("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)]),
    ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),
    ("max_carres", "xs", [([-3, 2], 9), ([1, 4], 16), ([-1, -5], 25)], [([0, 3], 9), ([2, -2], 4), ([-6, 1], 36)]),
]
inv = C.inventorie(CORPUS)

# (a) promotion correcte
promo = B.promeut_abstraction(inv)
check("promotion = map du carré", promo == ("map[_e * _e]", "[_e * _e for _e in x]"))
# la capacité promue calcule bien les carrés élément par élément
fmap = MI._callable(promo[1], "f")
check("la capacité promue reproduit le carré élément-par-élément",
      fmap([1, 2, 3]) == [1, 4, 9] and fmap([-2, 5]) == [4, 25])

# (b) extension additive + idempotente
base = MI.EXISTANT
etendue = B.etend_bibliotheque(base, inv)
check("extension ajoute exactement 1 capacité", len(etendue) == len(base) + 1 and promo[0] in etendue)
check("extension idempotente", len(B.etend_bibliotheque(etendue, inv)) == len(etendue))

# (c) GAIN épistémique : liste des carrés passe de INVENTION à EXISTE_DEJA
# Entrées NON triées : distinguent map[carré] de sorted∘map / reverse∘map (sinon AMBIGU, cf. composition 2e niveau).
cibles = [("liste_carres", [([3, 1, 2], [9, 1, 4]), ([2, 5, 1], [4, 25, 1])], [([4, 2], [16, 4]), ([1, 3, 2], [1, 9, 4])])]
vb = MI.examine_cible("liste_carres", "x", cibles[0][1], cibles[0][2], existant=base)
ve = MI.examine_cible("liste_carres", "x", cibles[0][1], cibles[0][2], existant=etendue)
check("liste_carres : INVENTION (base)", vb.statut == MI.INVENTION)
check("liste_carres : EXISTE_DEJA (étendue)", ve.statut == MI.EXISTE_DEJA and ve.proche_de == promo[0])
check("gain_reconnaissance == ['liste_carres']", B.gain_reconnaissance(cibles, base, etendue) == ["liste_carres"])

# (d) GARDE de non-régression sur corpus d'origine + nouvelle cible
corpus_test = [(n, e, h) for n, _s, e, h in CORPUS] + cibles
check("non-régression : rien cassé, aucun faux", B.verifie_non_regression(corpus_test, base, etendue))
# coverage monotone : tout ce qui était EXISTE_DEJA le reste
check("couverture monotone (somme_totale reste EXISTE_DEJA)",
      MI.examine_cible("somme_totale", "x", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4)], existant=etendue).statut == MI.EXISTE_DEJA)

# (e) SOUNDNESS : aucune réutilisation -> AUCUNE promotion (pas de brique fabriquée sans preuve)
inv_sans_reuse = C.inventorie([
    ("amplitude", "xs", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
     [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)]),
])
check("pas d'abstraction réutilisée -> promotion = None", B.promeut_abstraction(inv_sans_reuse) is None)
check("extension sans réutilisation = no-op", B.etend_bibliotheque(base, inv_sans_reuse) == base)

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# ATOME 2 — SOMMEIL GÉNÉRALISÉ : promotion MULTIPLE sous score MDL (DreamCoder), plus seulement le top-1.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════

# (f) LE SCORE MDL est la formule s·(k−1) − k et son SEUIL mord à la bonne place.
#     s = taille (nœuds AST) du map `[F for _e in x]` ; promouvoir ssi le gain de compression est > 0.
s_carre = B._taille("[_e * _e for _e in x]")
check("gain_mdl = s·(k−1) − k (mesuré, non inventé)", B.gain_mdl("_e * _e", 3) == s_carre * 2 - 3)
check("MDL : réutilisée par 2 -> compresse (gain > 0)", B.gain_mdl("_e * _e", 2) > 0)
check("MDL : réutilisée par 1 seule -> NE compresse PAS (gain ≤ 0, le garde-fou mord)",
      B.gain_mdl("_e * _e", 1) <= 0)
check("MDL monotone : plus de réutilisation = plus de gain",
      B.gain_mdl("_e * _e", 4) > B.gain_mdl("_e * _e", 3) > B.gain_mdl("_e * _e", 2))

# (g) PROMOTION MULTIPLE : un inventaire à DEUX abstractions réutilisées -> DEUX capacités promues,
#     triées par gain décroissant (le v0 n'en promouvait qu'UNE). Inventaire construit directement
#     (dataclass) pour un test déterministe, indépendant de ce que la recherche extrait.
inv_multi = C.Inventaire(
    par_statut={}, inventions={},
    abstractions=[("_e + _e", ["a", "b"]), ("_e * _e", ["c", "d", "e"])])
promues = B.promeut_abstractions(inv_multi)
check("les DEUX abstractions réutilisées sont promues (pas seulement le top-1)", len(promues) == 2)
check("tri par gain décroissant : le carré (3 usages) avant le double (2 usages)",
      promues[0][0] == "map[_e * _e]" and promues[1][0] == "map[_e + _e]" and promues[0][2] > promues[1][2])
etendue_multi = B.etend_bibliotheque(MI.EXISTANT, inv_multi)
check("etend_bibliotheque ajoute LES DEUX capacités",
      len(etendue_multi) == len(MI.EXISTANT) + 2
      and "map[_e * _e]" in etendue_multi and "map[_e + _e]" in etendue_multi)
check("promeut_abstraction (compat) rend toujours la plus payante", B.promeut_abstraction(inv_multi) == ("map[_e * _e]", "[_e * _e for _e in x]"))
# chaque capacité promue est CORRECTE (reproduit sa transformation) — jamais une brique fausse en bibliothèque
fplus = MI._callable(etendue_multi["map[_e + _e]"], "f")
check("la 2e capacité promue reproduit bien le doublement élément-par-élément",
      fplus([1, 2, 3]) == [2, 4, 6] and fplus([-4, 5]) == [-8, 10])

print(f"\nBIBLIOTHEQUE_INVENTION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
