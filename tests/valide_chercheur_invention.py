"""
VALIDATION du CHERCHEUR D'INVENTIONS AUTONOME (chercheur_invention.py).

Vérifie : (a) l'inventaire d'un corpus place chaque cible dans le bon statut ; (b) la mesure de VALEUR
par réutilisation fait émerger le composant partagé (« _e * _e ») sur ≥2 cibles ; (c) SOUNDNESS : toute
cible rangée en INVENTION a un code qui reproduit son held-out (jamais de fausse invention dans l'inventaire) ;
(d) l'extraction de composant est correcte (AGG(F for _e in x) -> F ; identité/scalaire -> None).
"""
from __future__ import annotations

from garde_ressources import borne
import moteur_invention as MI
import chercheur_invention as C

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


# --- A) extraction du composant ---------------------------------------------------------------
check("core sum(_e*_e ...) = '_e * _e'", C._transform_core("sum(_e * _e for _e in x)") == "_e * _e")
check("core max(_e*_e ...) = '_e * _e'", C._transform_core("max(_e * _e for _e in x)") == "_e * _e")
check("core (max(x)-min(x)) = None (pas de composant élémentaire)", C._transform_core("(max(x) - min(x))") is None)
check("core sum(x) = None", C._transform_core("sum(x)") is None)

# --- B) inventaire d'un corpus + réutilisation -------------------------------------------------
CORPUS = [
    ("somme_totale", "xs", [([1, 2, 3], 6), ([5], 5)], [([0, 4], 4), ([2, 2], 4)]),                  # existe déjà
    ("somme_carres", "xs", [([1, 2, 3], 14), ([2, 3], 13)], [([5], 25), ([0, 4], 16), ([1, 1], 2)]),  # invention (carré)
    ("max_carres", "xs", [([-3, 2], 9), ([1, 4], 16), ([-1, -5], 25)],
     [([0, 3], 9), ([2, -2], 4), ([-6, 1], 36)]),                                                      # invention (carré)
    ("amplitude", "xs", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
     [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4), ([2, 8], 6)]),                                         # invention (max-min)
    # FRONTIÈRE actuelle = `deep_reverse` (renverser une liste imbriquée à TOUS les niveaux : récursion STRUCTURELLE
    # qui reconstruit l'imbrication, hors du combinateur flatten).
    # (flatten_rec a quitté la frontière le 2026-06-24 après-midi — récursion par auto-application acquise ; rle-DECODE
    # via EXPANSION ; rle-ENCODE via groupby ; produit_cumulatif le 2026-06-23. « Le plafond monte, le benchmark bouge. »)
    ("deep_reverse", "x", [([1, [2, 3], 4], [4, [3, 2], 1]), ([[1, 2], [3, 4]], [[4, 3], [2, 1]])],
     [([1, [2, [3, 4]]], [[[4, 3], 2], 1]), ([5, [6, 7], 8, 9], [9, 8, [7, 6], 5])]),                  # brique manquante (frontière)
]
inv = C.inventorie(CORPUS)
print("\n" + inv.rapport() + "\n")

check("somme_totale -> EXISTE_DEJA", "somme_totale" in inv.par_statut.get(MI.EXISTE_DEJA, []))
check("deep_reverse -> BRIQUE_MANQUANTE", "deep_reverse" in inv.par_statut.get(MI.BRIQUE_MANQUANTE, []))
check("3 inventions trouvées (somme_carres, max_carres, amplitude)",
      set(inv.inventions) == {"somme_carres", "max_carres", "amplitude"})

# --- C) la VALEUR par réutilisation : « _e * _e » émerge sur ≥2 cibles --------------------------
abst = dict((t, set(u)) for t, u in inv.abstractions)
check("abstraction « _e * _e » détectée", "_e * _e" in abst)
check("« _e * _e » réutilisée par somme_carres ET max_carres",
      abst.get("_e * _e") == {"somme_carres", "max_carres"})
check("l'abstraction la plus réutilisée est en tête du classement",
      inv.abstractions and inv.abstractions[0][0] == "_e * _e")

# --- D) SOUNDNESS : toute INVENTION de l'inventaire reproduit son held-out ----------------------
held = {nom: h for nom, sig, ex, h in CORPUS}
sound = all(C.MI._reproduit(C.MI._callable(code, "f"), held[nom]) for nom, code in inv.inventions.items())
check("INVARIANT : chaque invention de l'inventaire reproduit son held-out", sound)

print(f"\nCHERCHEUR_INVENTION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
